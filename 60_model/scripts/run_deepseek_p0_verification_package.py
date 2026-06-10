from __future__ import annotations

import argparse
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


P0_REVIEW_CSV = ROOT / "70_outputs" / "processed_tables" / "poi_supply_p0_entrance_route_review.csv"
NODE_QUEUE_CSV = ROOT / "50_external_gis" / "amap_routes" / "amap_p0_entrance_node_semantic_review_queue.csv"
OUT_CSV = ROOT / "70_outputs" / "processed_tables" / "p0_manual_verification_package_deepseek.csv"
OUT_DIR = ROOT / "60_model" / "llm_runs"
RAW_JSONL = OUT_DIR / "deepseek_p0_verification_package_raw.jsonl"
PROGRESS_JSON = OUT_DIR / "deepseek_p0_verification_package_progress.json"
REPORT = ROOT / "40_quality_evidence" / "deepseek_p0_verification_package_report.md"


FIELDS = [
    "work_item_id",
    "park_id",
    "park_name",
    "poi_name",
    "standard_categories",
    "missing_business_fields_draft",
    "p0_verification_summary_draft",
    "business_field_followup_draft",
    "entrance_node_followup_draft",
    "operation_authorization_followup_draft",
    "fieldwork_questions_draft",
    "p2_gate_draft",
    "p1_next_action_draft",
    "output_status",
    "executor",
    "model",
    "review_gate",
    "llm_task_id",
    "run_id",
]

P2_GATE = "do_not_enter_p2_until_field_or_official_confirmation"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def clamp(text: Any, limit: int = 360) -> str:
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


def build_node_context(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    by_park: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        if row.get("final_use_gate") == "do_not_use_as_access_node_until_manual_review":
            continue
        by_park.setdefault(row.get("park_id", ""), []).append(
            {
                "node_candidate_id": row.get("node_candidate_id", ""),
                "node_name": row.get("node_name", ""),
                "local_rule_priority": row.get("local_rule_priority", ""),
                "final_use_gate": row.get("final_use_gate", ""),
                "review_instruction": row.get("review_instruction", ""),
            }
        )
    for park_id, items in by_park.items():
        by_park[park_id] = items[:8]
    return by_park


def compact_work_item(row: dict[str, str], node_context: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    return {
        "work_item_id": row.get("work_item_id", ""),
        "park_id": row.get("park_id", ""),
        "park_name": row.get("park_name", ""),
        "poi_name": row.get("poi_name", ""),
        "standard_categories": row.get("standard_categories", ""),
        "address": row.get("address", ""),
        "field_review_priority": row.get("field_review_priority", ""),
        "source_strength_status": row.get("source_strength_status", ""),
        "missing_business_fields": row.get("missing_business_fields", ""),
        "opening_hours_status": row.get("opening_hours_status", ""),
        "contact_status": row.get("contact_status", ""),
        "spend_status": row.get("spend_status", ""),
        "pdf_seed_match_status": row.get("pdf_seed_match_status", ""),
        "pdf_seed_poi_names": row.get("pdf_seed_poi_names", ""),
        "best_node_kind": row.get("best_node_kind", ""),
        "best_node_name": row.get("best_node_name", ""),
        "best_walking_distance_m": row.get("best_walking_distance_m", ""),
        "best_walking_duration_s": row.get("best_walking_duration_s", ""),
        "entrance_route_proxy_status": row.get("entrance_route_proxy_status", ""),
        "can_enter_p2_supply_after_entrance_route": row.get("can_enter_p2_supply_after_entrance_route", ""),
        "operation_authorization_status": row.get("operation_authorization_status", ""),
        "candidate_access_nodes_same_park": node_context.get(row.get("park_id", ""), []),
    }


def make_messages(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "你是公园商业选址项目的低成本 P1 核验包整理助手。"
                "你只能整理人工/官方核验动作，不能确认事实，不能给 checked，不能允许进入 P2。"
                "不要补充外部知识，不要编造营业时间、电话、价格、授权状态或官方入口。"
                "只输出 JSON 数组，不输出 Markdown。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请根据输入的 P0 园内候选工作项，生成逐项人工/官方核验包草稿。\n"
                "每个输入必须输出一条；字段必须为：work_item_id, missing_business_fields_draft, "
                "p0_verification_summary_draft, business_field_followup_draft, entrance_node_followup_draft, "
                "operation_authorization_followup_draft, fieldwork_questions_draft, p2_gate_draft, "
                "p1_next_action_draft, output_status。\n"
                f"p2_gate_draft 必须固定为 {P2_GATE}。\n"
                "output_status 必须固定为 needs_review。\n"
                "核验包要具体、可执行，但只能说“需要核验/确认”，不能说“已确认”。\n"
                "重点覆盖：缺失经营字段、最佳入口/节点仍是代理、运营授权、PDF 种子同名回查、现场问题。\n"
                "输入 JSON：\n"
                + json.dumps(items, ensure_ascii=False)
            ),
        },
    ]


def normalize_result(item: dict[str, Any]) -> dict[str, str]:
    return {
        "work_item_id": clamp(item.get("work_item_id", ""), 80),
        "missing_business_fields_draft": clamp(item.get("missing_business_fields_draft", "")),
        "p0_verification_summary_draft": clamp(item.get("p0_verification_summary_draft", "")),
        "business_field_followup_draft": clamp(item.get("business_field_followup_draft", "")),
        "entrance_node_followup_draft": clamp(item.get("entrance_node_followup_draft", "")),
        "operation_authorization_followup_draft": clamp(item.get("operation_authorization_followup_draft", "")),
        "fieldwork_questions_draft": clamp(item.get("fieldwork_questions_draft", "")),
        "p2_gate_draft": P2_GATE,
        "p1_next_action_draft": clamp(item.get("p1_next_action_draft", "")),
        "output_status": "needs_review",
    }


def fallback_result(row: dict[str, str]) -> dict[str, str]:
    missing = row.get("missing_business_fields", "")
    return {
        "work_item_id": row.get("work_item_id", ""),
        "missing_business_fields_draft": missing,
        "p0_verification_summary_draft": "DeepSeek 未返回该项；按保守口径保留为人工核验。",
        "business_field_followup_draft": f"复核缺失经营字段：{missing or '无明确缺失字段'}。",
        "entrance_node_followup_draft": "入口/节点路径仅为代理结果，需现场或官方确认。",
        "operation_authorization_followup_draft": "确认是否属于园方可运营或可授权资产。",
        "fieldwork_questions_draft": "现场核验营业状态、入口可达、授权关系和经营字段。",
        "p2_gate_draft": P2_GATE,
        "p1_next_action_draft": "保守列入人工核验队列。",
        "output_status": "needs_review",
    }


def run() -> None:
    task_id = "LLM-012"
    route = route_for(task_id)
    p0_rows = read_csv(P0_REVIEW_CSV)
    node_rows = read_csv(NODE_QUEUE_CSV)
    node_context = build_node_context(node_rows)
    compact_items = [compact_work_item(row, node_context) for row in p0_rows]
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    content = run_deepseek_task(task_id, make_messages(compact_items), temperature=0.0)
    raw_record = {
        "run_id": run_id,
        "task_id": task_id,
        "task_name": route.task_name,
        "executor": route.default_executor,
        "model": route.model,
        "output_status": route.output_status,
        "input_work_item_ids": [row.get("work_item_id", "") for row in p0_rows],
        "response_excerpt": content[:4000],
    }
    RAW_JSONL.write_text(json.dumps(raw_record, ensure_ascii=False) + "\n", encoding="utf-8")

    parsed = extract_json_array(content)
    by_id = {item["work_item_id"]: item for item in (normalize_result(raw) for raw in parsed) if item["work_item_id"]}

    out_rows: list[dict[str, str]] = []
    for row in p0_rows:
        work_item_id = row.get("work_item_id", "")
        result = by_id.get(work_item_id, fallback_result(row))
        out_rows.append(
            {
                "work_item_id": work_item_id,
                "park_id": row.get("park_id", ""),
                "park_name": row.get("park_name", ""),
                "poi_name": row.get("poi_name", ""),
                "standard_categories": row.get("standard_categories", ""),
                **result,
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
                "work_items": len(p0_rows),
                "package_rows": len(out_rows),
                "remaining_rows": len(p0_rows) - len(out_rows),
                "raw_chunks": 1,
                "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    status_counts = Counter(row["output_status"] for row in out_rows)
    gate_counts = Counter(row["p2_gate_draft"] for row in out_rows)
    REPORT.write_text(
        "\n".join(
            [
                "# DeepSeek P0 人工核验包草稿报告",
                "",
                "## 结论",
                "",
                f"- 输入 P0 工作项：{len(p0_rows)} 条。",
                f"- 输出核验包：{len(out_rows)} 条。",
                f"- 输出状态：{dict(sorted(status_counts.items()))}",
                f"- P2 门禁：{dict(sorted(gate_counts.items()))}",
                "",
                "## 口径限制",
                "",
                "- 本结果只整理人工/官方核验动作，不能作为事实确认。",
                "- 不得把本草稿写成官方入口、正式营业字段、运营授权或 P2 供给结论。",
                "- 进入 P2 前仍需现场/官方入口、经营字段和运营授权闭合。",
                "",
                "## 输出文件",
                "",
                "- `70_outputs/processed_tables/p0_manual_verification_package_deepseek.csv`",
                "- `60_model/llm_runs/deepseek_p0_verification_package_raw.jsonl`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(out_rows)} P0 verification package rows to {OUT_CSV}")
    print(f"wrote report to {REPORT}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    run()


if __name__ == "__main__":
    main()
