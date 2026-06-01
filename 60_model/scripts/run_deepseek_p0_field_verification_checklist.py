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


ENRICHED_WORKLIST = ROOT / "70_outputs" / "processed_tables" / "poi_supply_p0_followup_worklist_enriched.csv"
NODE_QUEUE = ROOT / "50_external_gis" / "amap_routes" / "amap_p0_entrance_node_semantic_review_queue.csv"
P0_PACKAGE = ROOT / "70_outputs" / "processed_tables" / "p0_manual_verification_package_deepseek.csv"
OUT_CSV = ROOT / "70_outputs" / "processed_tables" / "p0_field_verification_checklist_deepseek.csv"
OUT_DIR = ROOT / "60_model" / "llm_runs"
RAW_JSONL = OUT_DIR / "deepseek_p0_field_verification_checklist_raw.jsonl"
PROGRESS_JSON = OUT_DIR / "deepseek_p0_field_verification_checklist_progress.json"
REPORT = ROOT / "40_quality_evidence" / "deepseek_p0_field_verification_checklist_report.md"

P2_GATE = "do_not_enter_p2_until_field_or_official_confirmation"

FIELDS = [
    "checklist_id",
    "checklist_type",
    "source_id",
    "park_id",
    "park_name",
    "target_name",
    "target_kind",
    "related_poi_or_node",
    "priority",
    "current_known_info",
    "verification_goal_draft",
    "on_site_questions_draft",
    "photo_required_draft",
    "acceptable_evidence_draft",
    "blocking_reason_draft",
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


def clamp(text: Any, limit: int = 500) -> str:
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


def remaining_business_fields(row: dict[str, str]) -> str:
    missing = set(filter(None, row.get("missing_business_fields", "").split(";")))
    if row.get("tel_verified"):
        missing.discard("contact")
    if row.get("opentime_verified"):
        missing.discard("opening_hours")
    if row.get("cost_yuan_verified"):
        missing.discard("cost_yuan")
    return ";".join(sorted(missing))


def work_item_priority(row: dict[str, str]) -> str:
    if row.get("enrichment_status") == "detail_api_called_no_new_data":
        return "P0_business_fields_and_authorization"
    if remaining_business_fields(row):
        return "P1_remaining_business_fields"
    return "P1_authorization_and_route_confirmation"


def build_work_items(rows: list[dict[str, str]], package_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    package_by_id = {row.get("work_item_id", ""): row for row in package_rows}
    items: list[dict[str, str]] = []
    for row in rows:
        package = package_by_id.get(row.get("work_item_id", ""), {})
        known_parts = [
            f"tel={row.get('tel_verified') or '缺失'}",
            f"opentime={row.get('opentime_verified') or '缺失'}",
            f"cost_yuan={row.get('cost_yuan_verified') or '缺失'}",
            f"enrichment_status={row.get('enrichment_status', '')}",
        ]
        items.append(
            {
                "checklist_type": "p0_poi_business_and_authorization",
                "source_id": row.get("work_item_id", ""),
                "park_id": row.get("park_id", ""),
                "park_name": row.get("park_name", ""),
                "target_name": row.get("poi_name", ""),
                "target_kind": row.get("standard_categories", ""),
                "related_poi_or_node": row.get("best_node_name", "") or row.get("address", ""),
                "priority": work_item_priority(row),
                "remaining_business_fields": remaining_business_fields(row),
                "current_known_info": "; ".join(known_parts),
                "draft_context": package.get("fieldwork_questions_draft", ""),
                "blocking_gaps": row.get("blocking_gaps", ""),
            }
        )
    return items


def build_node_items(rows: list[dict[str, str]], work_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    poi_names_by_park: dict[str, list[str]] = {}
    for row in work_rows:
        poi_names_by_park.setdefault(row.get("park_id", ""), []).append(row.get("poi_name", ""))
    items: list[dict[str, str]] = []
    for row in rows:
        if row.get("final_use_gate") == "do_not_use_as_access_node_until_manual_review":
            continue
        checklist_type = (
            "primary_access_node_field_check"
            if row.get("local_rule_priority") == "P0_manual_check_gate_or_entrance"
            else "secondary_parking_or_visit_node_field_check"
        )
        items.append(
            {
                "checklist_type": checklist_type,
                "source_id": row.get("semantic_review_id", ""),
                "park_id": row.get("park_id", ""),
                "park_name": row.get("park_name", ""),
                "target_name": row.get("node_name", ""),
                "target_kind": row.get("semantic_node_type_draft", ""),
                "related_poi_or_node": ";".join(poi_names_by_park.get(row.get("park_id", ""), [])),
                "priority": row.get("local_rule_priority", ""),
                "current_known_info": (
                    f"type={row.get('amap_type', '')}; address={row.get('address', '')}; "
                    f"final_use_gate={row.get('final_use_gate', '')}"
                ),
                "draft_context": row.get("review_instruction", ""),
                "blocking_gaps": "official_or_field_confirmation_required",
            }
        )
    return items


def make_messages(items: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "你是公园商业选址项目的现场核验清单整理助手。"
                "你只能把 P0 供给项和入口/访问节点整理为现场核验 checklist 草稿。"
                "不得确认事实，不得宣称官方入口，不得放行 P2，不得补充外部知识。"
                "只输出 JSON 数组，不输出 Markdown。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请为每个输入项生成一条现场核验 checklist 草稿。\n"
                "输出字段必须为：source_id, verification_goal_draft, on_site_questions_draft, "
                "photo_required_draft, acceptable_evidence_draft, blocking_reason_draft, "
                "p2_gate_draft, output_status。\n"
                f"必须输出 {len(items)} 条，source_id 必须逐一对应输入。"
                f"p2_gate_draft 必须固定为 {P2_GATE}；output_status 必须固定为 needs_review。\n"
                "photo_required_draft 用 yes/no_and_reason。acceptable_evidence_draft 要具体到：照片、官方牌示、现场问询记录、电话记录或园方确认。\n"
                "不要写“已确认”“官方入口已成立”“可进入 P2”等结论。\n"
                "输入 JSON：\n"
                + json.dumps(items, ensure_ascii=False)
            ),
        },
    ]


def normalize_result(item: dict[str, Any]) -> dict[str, str]:
    return {
        "source_id": clamp(item.get("source_id", ""), 100),
        "verification_goal_draft": clamp(item.get("verification_goal_draft", "")),
        "on_site_questions_draft": clamp(item.get("on_site_questions_draft", "")),
        "photo_required_draft": clamp(item.get("photo_required_draft", "yes")),
        "acceptable_evidence_draft": clamp(item.get("acceptable_evidence_draft", "")),
        "blocking_reason_draft": clamp(item.get("blocking_reason_draft", "")),
        "p2_gate_draft": P2_GATE,
        "output_status": "needs_review",
    }


def fallback_result(item: dict[str, str]) -> dict[str, str]:
    return {
        "source_id": item["source_id"],
        "verification_goal_draft": "核验该项是否可作为 P1 后续供给/入口节点输入，且仅记录事实。",
        "on_site_questions_draft": "现场确认目标是否存在、是否开放、是否可到达、是否有经营/管理授权；记录未确认项。",
        "photo_required_draft": "yes: 需要目标、周边导视、入口/节点状态或经营信息照片。",
        "acceptable_evidence_draft": "现场照片、官方牌示、商户/园方问询记录、电话记录或官方公开信息截图。",
        "blocking_reason_draft": item.get("blocking_gaps", "official_or_field_confirmation_required"),
        "p2_gate_draft": P2_GATE,
        "output_status": "needs_review",
    }


def run() -> None:
    task_id = "LLM-015"
    route = route_for(task_id)
    work_rows = read_csv(ENRICHED_WORKLIST)
    node_rows = read_csv(NODE_QUEUE)
    package_rows = read_csv(P0_PACKAGE)
    items = build_work_items(work_rows, package_rows) + build_node_items(node_rows, work_rows)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    content = run_deepseek_task(task_id, make_messages(items), temperature=0.0)
    RAW_JSONL.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "task_id": task_id,
                "task_name": route.task_name,
                "executor": route.default_executor,
                "model": route.model,
                "output_status": route.output_status,
                "input_source_ids": [item["source_id"] for item in items],
                "response_excerpt": content[:5000],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    parsed = extract_json_array(content)
    by_source = {item["source_id"]: item for item in (normalize_result(raw) for raw in parsed) if item["source_id"]}

    out_rows: list[dict[str, str]] = []
    for index, item in enumerate(items, start=1):
        result = by_source.get(item["source_id"], fallback_result(item))
        out_rows.append(
            {
                "checklist_id": f"FIELD-CHECK-{index:03d}",
                "checklist_type": item["checklist_type"],
                "source_id": item["source_id"],
                "park_id": item["park_id"],
                "park_name": item["park_name"],
                "target_name": item["target_name"],
                "target_kind": item["target_kind"],
                "related_poi_or_node": item["related_poi_or_node"],
                "priority": item["priority"],
                "current_known_info": clamp(item["current_known_info"]),
                **{key: result[key] for key in [
                    "verification_goal_draft",
                    "on_site_questions_draft",
                    "photo_required_draft",
                    "acceptable_evidence_draft",
                    "blocking_reason_draft",
                    "p2_gate_draft",
                    "output_status",
                ]},
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
                "node_items": len(items) - len(work_rows),
                "checklist_rows": len(out_rows),
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
    type_counts = Counter(row["checklist_type"] for row in out_rows)
    priority_counts = Counter(row["priority"] for row in out_rows)
    REPORT.write_text(
        "\n".join(
            [
                "# DeepSeek P0 现场核验检查表草稿报告",
                "",
                "## 结论",
                "",
                "- 输出状态：needs_review。",
                f"- P0 供给项核验：{len(work_rows)} 条。",
                f"- 入口/访问节点核验：{len(items) - len(work_rows)} 条。",
                f"- 检查表总行数：{len(out_rows)} 条。",
                f"- 检查类型分布：{dict(sorted(type_counts.items()))}",
                f"- 优先级分布：{dict(sorted(priority_counts.items()))}",
                "",
                "## 口径",
                "",
                "- 本检查表只用于现场/官方核验准备，不确认事实。",
                "- 18 条低置信或不应使用节点未进入主现场核验清单。",
                "- 所有条目仍保持 P2 不放行，直到字段、入口/节点和运营授权闭合。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote field verification checklist rows={len(out_rows)} to {OUT_CSV}")
    print(f"wrote report to {REPORT}")


if __name__ == "__main__":
    run()
