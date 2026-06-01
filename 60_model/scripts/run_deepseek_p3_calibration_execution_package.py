from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "60_model" / "src"))

from llm_router import run_deepseek_task  # noqa: E402  # type: ignore[import-not-found]


TASK_ID = "LLM-023"
OUT_DIR = ROOT / "60_model" / "llm_runs"
RAW_JSONL = OUT_DIR / "deepseek_p3_calibration_execution_package_raw.jsonl"
PROGRESS_JSON = OUT_DIR / "deepseek_p3_calibration_execution_package_progress.json"

INPUTS = {
    "p3_calibration_requirements": ROOT / "70_outputs" / "processed_tables" / "p3_calibration_data_requirements_deepseek.csv",
    "p3_dwg_work_order": ROOT / "70_outputs" / "processed_tables" / "p3_dwg_conversion_work_order_deepseek.csv",
    "p3_mapping": ROOT / "70_outputs" / "processed_tables" / "p3_p2_to_calibration_field_mapping_deepseek.csv",
    "p4_skeleton": ROOT / "70_outputs" / "processed_tables" / "p4_parallel_skeleton_backlog_deepseek.csv",
    "p2_gap_register": ROOT / "70_outputs" / "processed_tables" / "p2_input_gap_register.csv",
}

OUT_EVIDENCE = ROOT / "70_outputs" / "processed_tables" / "p3_calibration_evidence_request_worklist_deepseek.csv"
OUT_ACCEPTANCE = ROOT / "70_outputs" / "processed_tables" / "p3_calibration_acceptance_criteria_deepseek.csv"
OUT_LIMITS = ROOT / "70_outputs" / "processed_tables" / "p3_scenario_assumption_limits_deepseek.csv"
OUT_BLOCKERS = ROOT / "70_outputs" / "processed_tables" / "p3_calibration_blocker_register_deepseek.csv"
OUT_GATE = ROOT / "70_outputs" / "processed_tables" / "p3_calibration_gate_status.csv"
OUT_JSON = ROOT / "40_quality_evidence" / "deepseek_p3_calibration_execution_package.json"
OUT_MD = ROOT / "40_quality_evidence" / "deepseek_p3_calibration_execution_package.md"

COMMON = ["output_status", "executor", "llm_task_id"]
EVIDENCE_FIELDS = [
    "request_id",
    "calibration_domain",
    "target_field",
    "requested_evidence",
    "acceptable_source",
    "validation_rule",
    "p4_dependency",
    "current_status",
    *COMMON,
]
ACCEPTANCE_FIELDS = [
    "criterion_id",
    "calibration_domain",
    "pass_condition",
    "fail_condition",
    "verification_method",
    "blocks_p4_conclusion",
    *COMMON,
]
LIMIT_FIELDS = [
    "assumption_id",
    "calibration_domain",
    "placeholder_policy",
    "allowed_use_before_real_data",
    "forbidden_use",
    "review_status",
    *COMMON,
]
BLOCKER_FIELDS = [
    "blocker_id",
    "calibration_domain",
    "blocker",
    "impact_on_p4",
    "next_action",
    "owner_hint",
    "current_status",
    *COMMON,
]
GATE_FIELDS = [
    "gate_id",
    "calibration_domain",
    "required_before_p4_conclusion",
    "current_gate_status",
    "blocking_reason",
    "source_table",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: str(row.get(field, "")) for field in fields})


def parse_json_object(value: str) -> dict[str, Any]:
    text = value.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def mark(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for row in rows:
        row["output_status"] = "needs_review"
        row["executor"] = "deepseek"
        row["llm_task_id"] = TASK_ID
    return rows


def pad(rows: list[dict[str, Any]], size: int, factory: Any) -> list[dict[str, Any]]:
    clean = [row for row in rows if isinstance(row, dict)]
    while len(clean) < size:
        clean.append(factory(len(clean) + 1))
    return clean[:size]


def make_messages(context: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "你是公园商业选址仿真项目的P3真实校准执行包整理助手。"
                "必须大量利用已有P2/P3表，但不得伪造真实客流、转化率、收益成本、运营授权或DWG几何。"
                "所有输出只能是needs_review。P3未闭合前，P4只能准备骨架/API/测试/配置，不能出完整仿真结论。"
                "DWG没有可信DXF/GeoJSON/SVG/PDF导出前，状态必须保持pending_conversion。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请输出严格JSON，不要Markdown。结构如下：\n"
                "{\n"
                "  \"summary\": \"一句话说明P3当前只能形成校准执行包，不能形成完整仿真结论\",\n"
                "  \"evidence_request_worklist\": [24 objects],\n"
                "  \"acceptance_criteria\": [18 objects],\n"
                "  \"scenario_assumption_limits\": [12 objects],\n"
                "  \"blocker_register\": [12 objects],\n"
                "  \"output_status\": \"needs_review\"\n"
                "}\n"
                "字段必须贴合CSV字段：evidence_request_worklist 使用 request_id/calibration_domain/target_field/"
                "requested_evidence/acceptable_source/validation_rule/p4_dependency/current_status；"
                "acceptance_criteria 使用 criterion_id/calibration_domain/pass_condition/fail_condition/"
                "verification_method/blocks_p4_conclusion；scenario_assumption_limits 使用 assumption_id/"
                "calibration_domain/placeholder_policy/allowed_use_before_real_data/forbidden_use/review_status；"
                "blocker_register 使用 blocker_id/calibration_domain/blocker/impact_on_p4/next_action/owner_hint/current_status。\n"
                "核心域必须覆盖 geometry, visitor_flow, conversion_rate, revenue_cost, operation_authorization, model_gate。"
                "current_status 只能使用 pending_collection, pending_conversion, blocked_until_source_received, needs_review。"
                "blocks_p4_conclusion 对核心门禁应为 yes。\n"
                + json.dumps(context, ensure_ascii=False)
            ),
        },
    ]


def fallback_row(prefix: str, idx: int, domain: str) -> dict[str, str]:
    return {
        "request_id": f"P3-EVID-{idx:03d}",
        "calibration_domain": domain,
        "target_field": f"{domain}_source_field",
        "requested_evidence": f"{domain}真实校准来源或明确缺失证明",
        "acceptable_source": "官方/运营方/现场/DWG可信导出/可复核原始表",
        "validation_rule": "必须有来源、日期、字段口径和复核状态；不得由PPT或P2原型默认回填",
        "p4_dependency": "blocks_p4_conclusion",
        "current_status": "pending_collection" if domain != "geometry" else "pending_conversion",
    }


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    domains = ["geometry", "visitor_flow", "conversion_rate", "revenue_cost", "operation_authorization", "model_gate"]
    evidence = pad(payload.get("evidence_request_worklist", []), 24, lambda i: fallback_row("P3-EVID", i, domains[(i - 1) % len(domains)]))
    acceptance = pad(
        payload.get("acceptance_criteria", []),
        18,
        lambda i: {
            "criterion_id": f"P3-ACCEPT-{i:03d}",
            "calibration_domain": domains[(i - 1) % len(domains)],
            "pass_condition": "存在可复核来源并通过字段口径检查",
            "fail_condition": "缺少来源或仅有P2原型/DeepSeek/PPT假设",
            "verification_method": "本地脚本检查行数、字段、状态、来源类型和人工复核标记",
            "blocks_p4_conclusion": "yes",
        },
    )
    limits = pad(
        payload.get("scenario_assumption_limits", []),
        12,
        lambda i: {
            "assumption_id": f"P3-LIMIT-{i:03d}",
            "calibration_domain": domains[(i - 1) % len(domains)],
            "placeholder_policy": "允许保留空值或显式scenario_assumption，不允许冒充真实校准参数",
            "allowed_use_before_real_data": "schema/API/mock测试",
            "forbidden_use": "完整仿真结论、最终排序、收益预测、坐标面积推断",
            "review_status": "needs_review",
        },
    )
    blockers = pad(
        payload.get("blocker_register", []),
        12,
        lambda i: {
            "blocker_id": f"P3-BLOCK-{i:03d}",
            "calibration_domain": domains[(i - 1) % len(domains)],
            "blocker": "真实校准来源未闭合",
            "impact_on_p4": "blocks_p4_conclusion",
            "next_action": "收集来源并通过本地门禁复核",
            "owner_hint": "user_or_field_or_operator",
            "current_status": "blocked_until_source_received",
        },
    )
    for rows in [evidence, acceptance, limits, blockers]:
        mark(rows)
    allowed_status = {"pending_collection", "pending_conversion", "blocked_until_source_received", "needs_review"}
    for row in evidence:
        if row.get("calibration_domain") == "geometry":
            row["current_status"] = "pending_conversion"
        elif row.get("current_status") not in allowed_status:
            row["current_status"] = "pending_collection"
    for row in blockers:
        row["current_status"] = "blocked_until_source_received"
    for row in acceptance:
        row["blocks_p4_conclusion"] = "yes"
    core_domains = ["geometry", "visitor_flow", "conversion_rate", "revenue_cost", "operation_authorization", "model_gate"]
    for idx, domain in enumerate(core_domains):
        if idx < len(acceptance):
            acceptance[idx]["calibration_domain"] = domain
        if idx < len(limits):
            limits[idx]["calibration_domain"] = domain
        if idx < len(blockers):
            blockers[idx]["calibration_domain"] = domain
    forbidden_tokens = ["完整仿真结论", "最终排序", "收益预测", "坐标面积"]
    for row in limits:
        forbidden = str(row.get("forbidden_use", ""))
        missing_tokens = [token for token in forbidden_tokens if token not in forbidden]
        if missing_tokens:
            row["forbidden_use"] = forbidden + "；不得用于" + "、".join(missing_tokens)
    return {
        "summary": payload.get("summary", "P3当前形成真实校准执行包，等待真实来源和DWG可信转换；不能形成P4完整仿真结论。"),
        "evidence_request_worklist": evidence,
        "acceptance_criteria": acceptance,
        "scenario_assumption_limits": limits,
        "blocker_register": blockers,
        "output_status": "needs_review",
        "executor": "deepseek",
        "llm_task_id": TASK_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def build_gate_status(evidence: list[dict[str, Any]], blockers: list[dict[str, Any]]) -> list[dict[str, str]]:
    domains = ["geometry", "visitor_flow", "conversion_rate", "revenue_cost", "operation_authorization", "model_gate"]
    rows = []
    for idx, domain in enumerate(domains, start=1):
        ev = [row for row in evidence if row.get("calibration_domain") == domain]
        bl = [row for row in blockers if row.get("calibration_domain") == domain]
        status = "pending_conversion" if domain == "geometry" else "blocked_until_source_received"
        reason = "; ".join(sorted({row.get("blocker", "") for row in bl if row.get("blocker")}))
        if not reason:
            reason = "真实校准来源未闭合"
        rows.append(
            {
                "gate_id": f"P3-GATE-{idx:03d}",
                "calibration_domain": domain,
                "required_before_p4_conclusion": "yes",
                "current_gate_status": status,
                "blocking_reason": reason,
                "source_table": "p3_calibration_evidence_request_worklist_deepseek.csv",
            }
        )
    return rows


def main() -> None:
    context = {name: read_csv(path) for name, path in INPUTS.items()}
    messages = make_messages(context)
    content = run_deepseek_task(TASK_ID, messages, temperature=0.1)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_JSONL.write_text(json.dumps({"task_id": TASK_ID, "response": content}, ensure_ascii=False) + "\n", encoding="utf-8")
    payload = normalize_payload(parse_json_object(content))

    write_csv(OUT_EVIDENCE, EVIDENCE_FIELDS, payload["evidence_request_worklist"])
    write_csv(OUT_ACCEPTANCE, ACCEPTANCE_FIELDS, payload["acceptance_criteria"])
    write_csv(OUT_LIMITS, LIMIT_FIELDS, payload["scenario_assumption_limits"])
    write_csv(OUT_BLOCKERS, BLOCKER_FIELDS, payload["blocker_register"])
    gate_rows = build_gate_status(payload["evidence_request_worklist"], payload["blocker_register"])
    write_csv(OUT_GATE, GATE_FIELDS, gate_rows)

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(
        "\n".join(
            [
                "# DeepSeek P3 calibration execution package",
                "",
                f"- output_status: {payload['output_status']}",
                f"- evidence_request_worklist rows: {len(payload['evidence_request_worklist'])}",
                f"- acceptance_criteria rows: {len(payload['acceptance_criteria'])}",
                f"- scenario_assumption_limits rows: {len(payload['scenario_assumption_limits'])}",
                f"- blocker_register rows: {len(payload['blocker_register'])}",
                "- boundary: needs_review only; P3 calibration gates remain open until real sources and trusted DWG conversion are received.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    PROGRESS_JSON.write_text(
        json.dumps(
            {
                "task_id": TASK_ID,
                "output_status": "needs_review",
                "evidence_rows": len(payload["evidence_request_worklist"]),
                "acceptance_rows": len(payload["acceptance_criteria"]),
                "limit_rows": len(payload["scenario_assumption_limits"]),
                "blocker_rows": len(payload["blocker_register"]),
                "gate_rows": len(gate_rows),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"{OUT_EVIDENCE.name} rows={len(payload['evidence_request_worklist'])}")
    print(f"{OUT_ACCEPTANCE.name} rows={len(payload['acceptance_criteria'])}")
    print(f"{OUT_LIMITS.name} rows={len(payload['scenario_assumption_limits'])}")
    print(f"{OUT_BLOCKERS.name} rows={len(payload['blocker_register'])}")
    print(f"{OUT_GATE.name} rows={len(gate_rows)}")


if __name__ == "__main__":
    main()
