from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "60_model" / "src"))

from llm_router import route_for, run_deepseek_task  # noqa: E402


WORKLIST = ROOT / "70_outputs" / "processed_tables" / "poi_supply_p0_followup_worklist.csv"
OUT_CSV = ROOT / "50_external_gis" / "amap_poi" / "amap_p0_detail_query_plan_deepseek.csv"
OUT_DIR = ROOT / "60_model" / "llm_runs"
RAW_JSONL = OUT_DIR / "deepseek_p0_detail_query_plan_raw.jsonl"
PROGRESS_JSON = OUT_DIR / "deepseek_p0_detail_query_plan_progress.json"
REPORT = ROOT / "40_quality_evidence" / "deepseek_p0_detail_query_plan_report.md"

AMAP_DETAIL_ENDPOINT = "https://restapi.amap.com/v5/place/detail"
P2_GATE = "do_not_enter_p2_until_field_or_official_confirmation"

FIELDS = [
    "work_item_id",
    "candidate_id",
    "park_id",
    "park_name",
    "poi_name",
    "amap_poi_id",
    "address",
    "missing_business_fields",
    "query_priority",
    "query_mode_draft",
    "amap_endpoint_draft",
    "amap_detail_poi_id",
    "show_fields_draft",
    "local_update_fields_draft",
    "keyword_fallback_draft",
    "fallback_strategy_draft",
    "manual_review_notes_draft",
    "p2_gate_draft",
    "output_status",
    "executor",
    "model",
    "review_gate",
    "llm_task_id",
    "run_id",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def clamp(text: Any, limit: int = 400) -> str:
    value = str(text or "").strip().replace("\r", " ").replace("\n", " ")
    value = re.sub(r"\s+", " ", value)
    return value[:limit]


def extract_json_array(text: str) -> list[dict[str, Any]]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped, flags=re.IGNORECASE).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    start = stripped.find("[")
    end = stripped.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("DeepSeek response does not contain a JSON array")
    payload = json.loads(stripped[start : end + 1])
    if not isinstance(payload, list):
        raise ValueError("DeepSeek response JSON is not a list")
    return payload


def compact_item(row: dict[str, str]) -> dict[str, str]:
    return {
        "work_item_id": row.get("work_item_id", ""),
        "candidate_id": row.get("candidate_id", ""),
        "park_id": row.get("park_id", ""),
        "park_name": row.get("park_name", ""),
        "poi_name": row.get("poi_name", ""),
        "amap_poi_id": row.get("amap_poi_id", ""),
        "address": row.get("address", ""),
        "longitude": row.get("longitude", ""),
        "latitude": row.get("latitude", ""),
        "standard_categories": row.get("standard_categories", ""),
        "missing_business_fields": row.get("missing_business_fields", ""),
        "opening_hours_status": row.get("opening_hours_status", ""),
        "contact_status": row.get("contact_status", ""),
        "spend_status": row.get("spend_status", ""),
        "source_strength_status": row.get("source_strength_status", ""),
        "operation_authorization_status": row.get("operation_authorization_status", ""),
        "can_enter_p2_supply": row.get("can_enter_p2_supply", ""),
        "next_action": row.get("next_action", ""),
    }


def query_priority(row: dict[str, str]) -> str:
    missing = row.get("missing_business_fields", "")
    if "opening_hours" in missing or "contact" in missing:
        return "P0_detail_api_high"
    if "cost_yuan" in missing:
        return "P1_cost_or_business_field"
    return "P2_confirm_only"


def make_messages(items: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "你是公园商业选址项目的 DeepSeek-first P1 执行助手。"
                "你只生成高德 POI 详情查询计划和补字段策略草稿，不调用 API，不确认事实。"
                "不得编造营业时间、电话、人均消费、授权状态或入口结论。"
                "只输出 JSON 数组，不输出 Markdown。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请为每个 P0 工作项生成高德详情查询计划草稿。\n"
                "每个输入必须输出一条；字段必须为：work_item_id, query_mode_draft, "
                "show_fields_draft, local_update_fields_draft, keyword_fallback_draft, "
                "fallback_strategy_draft, manual_review_notes_draft, p2_gate_draft, output_status。\n"
                "query_mode_draft 优先使用 detail_by_amap_poi_id；如果缺少 id 才写 keyword_text_fallback。\n"
                "show_fields_draft 建议只写 business。local_update_fields_draft 只能来自输入的 missing_business_fields。\n"
                f"p2_gate_draft 必须固定为 {P2_GATE}。output_status 必须固定为 needs_review。\n"
                "计划要服务于后续本地 Python 调用高德 ID 搜索接口；不要把草稿当成事实。\n"
                "输入 JSON：\n"
                + json.dumps(items, ensure_ascii=False)
            ),
        },
    ]


def normalize_result(item: dict[str, Any]) -> dict[str, str]:
    return {
        "work_item_id": clamp(item.get("work_item_id", ""), 80),
        "query_mode_draft": clamp(item.get("query_mode_draft", "detail_by_amap_poi_id"), 80),
        "show_fields_draft": "business",
        "local_update_fields_draft": clamp(item.get("local_update_fields_draft", "")),
        "keyword_fallback_draft": clamp(item.get("keyword_fallback_draft", "")),
        "fallback_strategy_draft": clamp(item.get("fallback_strategy_draft", "")),
        "manual_review_notes_draft": clamp(item.get("manual_review_notes_draft", "")),
        "p2_gate_draft": P2_GATE,
        "output_status": "needs_review",
    }


def fallback_result(row: dict[str, str]) -> dict[str, str]:
    missing = row.get("missing_business_fields", "")
    return {
        "work_item_id": row.get("work_item_id", ""),
        "query_mode_draft": "detail_by_amap_poi_id" if row.get("amap_poi_id") else "keyword_text_fallback",
        "show_fields_draft": "business",
        "local_update_fields_draft": missing,
        "keyword_fallback_draft": f"{row.get('park_name', '')} {row.get('poi_name', '')}".strip(),
        "fallback_strategy_draft": "若 ID 查询无结果或字段仍缺失，回退到文本搜索/现场核验，不直接补事实。",
        "manual_review_notes_draft": "高德详情返回后仍需人工确认经营字段和运营授权；未闭合前不得进入 P2。",
        "p2_gate_draft": P2_GATE,
        "output_status": "needs_review",
    }


def run() -> None:
    task_id = "LLM-014"
    route = route_for(task_id)
    work_rows = read_csv(WORKLIST)
    compact_items = [compact_item(row) for row in work_rows]
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    content = run_deepseek_task(task_id, make_messages(compact_items), temperature=0.0)
    RAW_JSONL.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "task_id": task_id,
                "task_name": route.task_name,
                "executor": route.default_executor,
                "model": route.model,
                "output_status": route.output_status,
                "input_work_item_ids": [row.get("work_item_id", "") for row in work_rows],
                "response_excerpt": content[:5000],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    parsed = extract_json_array(content)
    by_id = {item["work_item_id"]: item for item in (normalize_result(raw) for raw in parsed) if item["work_item_id"]}

    out_rows: list[dict[str, str]] = []
    for row in work_rows:
        result = by_id.get(row.get("work_item_id", ""), fallback_result(row))
        missing = row.get("missing_business_fields", "")
        local_update_fields = result.get("local_update_fields_draft") or missing
        out_rows.append(
            {
                "work_item_id": row.get("work_item_id", ""),
                "candidate_id": row.get("candidate_id", ""),
                "park_id": row.get("park_id", ""),
                "park_name": row.get("park_name", ""),
                "poi_name": row.get("poi_name", ""),
                "amap_poi_id": row.get("amap_poi_id", ""),
                "address": row.get("address", ""),
                "missing_business_fields": missing,
                "query_priority": query_priority(row),
                "query_mode_draft": "detail_by_amap_poi_id" if row.get("amap_poi_id") else "keyword_text_fallback",
                "amap_endpoint_draft": AMAP_DETAIL_ENDPOINT,
                "amap_detail_poi_id": row.get("amap_poi_id", ""),
                "show_fields_draft": "business",
                "local_update_fields_draft": clamp(local_update_fields),
                "keyword_fallback_draft": result.get("keyword_fallback_draft") or fallback_result(row)["keyword_fallback_draft"],
                "fallback_strategy_draft": result.get("fallback_strategy_draft") or fallback_result(row)["fallback_strategy_draft"],
                "manual_review_notes_draft": result.get("manual_review_notes_draft") or fallback_result(row)["manual_review_notes_draft"],
                "p2_gate_draft": P2_GATE,
                "output_status": "needs_review",
                "executor": route.default_executor,
                "model": route.model,
                "review_gate": route.review_gate,
                "llm_task_id": task_id,
                "run_id": run_id,
            }
        )

    write_csv(OUT_CSV, out_rows, FIELDS)
    PROGRESS_JSON.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "work_items": len(work_rows),
                "plan_rows": len(out_rows),
                "remaining_rows": len(work_rows) - len(out_rows),
                "raw_chunks": 1,
                "output_status": "needs_review",
                "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    REPORT.write_text(
        "\n".join(
            [
                "# DeepSeek P0 高德详情查询计划草稿报告",
                "",
                "## 结论",
                "",
                "- 输出状态：needs_review。",
                f"- P0 工作项：{len(work_rows)} 条。",
                f"- 查询计划：{len(out_rows)} 条。",
                f"- 查询优先级分布：{dict(sorted(Counter(row['query_priority'] for row in out_rows).items()))}",
                "",
                "## 口径",
                "",
                "- 本报告只生成高德详情查询计划草稿，不调用 API，不确认经营字段事实。",
                "- 下一步由本地 Python 读取 `.env` / `AMAP_WEB_SERVICE_KEY` 执行详情 API，并保留 P1 草稿状态。",
                "- 所有 P0 项仍保持不进入 P2，直到经营字段、入口/节点和运营授权闭合。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote P0 Amap detail query plan rows={len(out_rows)} to {OUT_CSV}")
    print(f"wrote report to {REPORT}")


if __name__ == "__main__":
    run()
