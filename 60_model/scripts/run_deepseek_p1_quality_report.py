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

from llm_router import route_for, run_deepseek_task  # noqa: E402  # type: ignore[import-not-found]


EVIDENCE_LEDGER = ROOT / "40_quality_evidence" / "evidence_ledger.csv"
BUSINESS_FILL = ROOT / "70_outputs" / "processed_tables" / "p0_business_field_fill_amap.csv"
ENRICHED_WORKLIST = ROOT / "70_outputs" / "processed_tables" / "poi_supply_p0_followup_worklist_enriched.csv"
FIELD_CHECKLIST = ROOT / "70_outputs" / "processed_tables" / "p0_field_verification_checklist_deepseek.csv"
NODE_REVIEW_QUEUE = ROOT / "50_external_gis" / "amap_routes" / "amap_p0_entrance_node_semantic_review_queue.csv"
QUALITY_REPORT = ROOT / "40_quality_evidence" / "quality_report.md"
P0_AUDIT_JSON = ROOT / "40_quality_evidence" / "p0_data_completeness_audit_final.json"
VERIFICATION_REPORT = ROOT / "40_quality_evidence" / "verification" / "implementation_verification_20260524.md"

OUT_DRAFT = ROOT / "40_quality_evidence" / "p1_quality_report_draft_deepseek.md"
GENERATION_REPORT = ROOT / "40_quality_evidence" / "deepseek_p1_quality_report_generation_report.md"
OUT_DIR = ROOT / "60_model" / "llm_runs"
RAW_JSONL = OUT_DIR / "deepseek_p1_quality_report_raw.jsonl"
PROGRESS_JSON = OUT_DIR / "deepseek_p1_quality_report_progress.json"

DURABLE_CONTEXT_FILES = [
    "progress.md",
    "task_plan.md",
    "findings.md",
    "handoff_next_chat.md",
    "next_chat_prompt.md",
]

REPORT_CONTEXT_FILES = [
    "40_quality_evidence/quality_report.md",
    "40_quality_evidence/second_evidence_ledger_report.md",
    "40_quality_evidence/amap_spatial_precheck_report.md",
    "40_quality_evidence/amap_boundary_filter_report.md",
    "40_quality_evidence/in_park_candidate_review_report.md",
    "40_quality_evidence/p0_in_park_followup_worklist_report.md",
    "40_quality_evidence/p0_route_access_review_report.md",
    "40_quality_evidence/p0_entrance_route_review_report.md",
    "40_quality_evidence/deepseek_p0_detail_query_plan_report.md",
    "40_quality_evidence/deepseek_p0_field_verification_checklist_report.md",
    "40_quality_evidence/deepseek_project_context_sync_report.md",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def clamp(text: Any, limit: int = 4000) -> str:
    value = str(text or "").strip().replace("\r", "\n")
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value[:limit]


def excerpt_text(path: Path, max_chars: int = 1800, mode: str = "head_tail") -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "exists": False}
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    rel_path = str(path.relative_to(ROOT)).replace("\\", "/")
    if len(text) <= max_chars:
        excerpt = text
    elif mode == "tail":
        excerpt = text[-max_chars:]
    else:
        half = max_chars // 2
        excerpt = text[:half] + "\n\n...[middle omitted]...\n\n" + text[-half:]
    return {
        "path": rel_path,
        "exists": True,
        "bytes": path.stat().st_size,
        "excerpt": excerpt,
    }


def summarize_evidence(rows: list[dict[str, str]]) -> dict[str, Any]:
    validation_counts = Counter(row.get("validation_status", "") for row in rows)
    evidence_type_counts = Counter(row.get("evidence_type", "") for row in rows)
    source_counts = Counter(row.get("source_file", "") for row in rows)
    return {
        "total_rows": len(rows),
        "validation_status": dict(sorted(validation_counts.items())),
        "evidence_type": dict(sorted(evidence_type_counts.items())),
        "distinct_source_files": len(source_counts),
    }


def summarize_business_fill(rows: list[dict[str, str]]) -> dict[str, Any]:
    verification_status = Counter(row.get("verification_status", "") for row in rows)
    missing_fields = Counter()
    for row in rows:
        for field in filter(None, (part.strip() for part in row.get("fields_still_missing", "").split(";"))):
            missing_fields[field] += 1
    return {
        "total_rows": len(rows),
        "verification_status": dict(sorted(verification_status.items())),
        "missing_fields": dict(sorted(missing_fields.items())),
    }


def summarize_enriched(rows: list[dict[str, str]]) -> dict[str, Any]:
    enrichment_status = Counter(row.get("enrichment_status", "") for row in rows)
    can_enter = Counter(row.get("can_enter_p2_supply", "") for row in rows)
    blocking = Counter()
    for row in rows:
        for field in filter(None, (part.strip() for part in row.get("blocking_gaps", "").split(";"))):
            blocking[field] += 1
    return {
        "total_rows": len(rows),
        "enrichment_status": dict(sorted(enrichment_status.items())),
        "can_enter_p2_supply": dict(sorted(can_enter.items())),
        "blocking_gaps": dict(sorted(blocking.items())),
    }


def summarize_checklist(rows: list[dict[str, str]]) -> dict[str, Any]:
    checklist_type = Counter(row.get("checklist_type", "") for row in rows)
    output_status = Counter(row.get("output_status", "") for row in rows)
    priority = Counter(row.get("priority", "") for row in rows)
    return {
        "total_rows": len(rows),
        "checklist_type": dict(sorted(checklist_type.items())),
        "output_status": dict(sorted(output_status.items())),
        "priority": dict(sorted(priority.items())),
    }


def summarize_node_queue(rows: list[dict[str, str]]) -> dict[str, Any]:
    local_priority = Counter(row.get("local_rule_priority", "") for row in rows)
    final_gate = Counter(row.get("final_use_gate", "") for row in rows)
    return {
        "total_rows": len(rows),
        "local_rule_priority": dict(sorted(local_priority.items())),
        "final_use_gate": dict(sorted(final_gate.items())),
    }


def summarize_verification_markdown(text: str) -> dict[str, Any]:
    total = re.search(r"总检查项：\s*(\d+)", text)
    failures = re.search(r"失败项：\s*(\d+)", text)
    warnings = re.search(r"警告项：\s*(\d+)", text)
    status_line = re.search(r"状态统计：\s*(\{.*\})", text)
    return {
        "total_checks": int(total.group(1)) if total else None,
        "failures": int(failures.group(1)) if failures else None,
        "warnings": int(warnings.group(1)) if warnings else None,
        "status_summary": status_line.group(1) if status_line else "",
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def strip_markdown_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:markdown)?", "", stripped, flags=re.IGNORECASE).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    return stripped


def build_context() -> dict[str, Any]:
    evidence_rows = read_csv(EVIDENCE_LEDGER)
    business_rows = read_csv(BUSINESS_FILL)
    enriched_rows = read_csv(ENRICHED_WORKLIST)
    checklist_rows = read_csv(FIELD_CHECKLIST)
    node_rows = read_csv(NODE_REVIEW_QUEUE)
    verification_text = VERIFICATION_REPORT.read_text(encoding="utf-8-sig", errors="replace")
    p0_audit = load_json(P0_AUDIT_JSON)

    durable_context = []
    for rel_path in DURABLE_CONTEXT_FILES:
        full = ROOT / rel_path
        mode = "tail" if rel_path in {"progress.md", "findings.md", "handoff_next_chat.md", "next_chat_prompt.md"} else "head_tail"
        durable_context.append(excerpt_text(full, 2500, mode=mode))

    report_context = []
    for rel_path in REPORT_CONTEXT_FILES:
        report_context.append(excerpt_text(ROOT / rel_path, 1600))

    return {
        "project": "公园商业选址仿真与经营决策系统",
        "current_phase": "P1 收口阶段，尚未进入 P2",
        "queue_context": {
            "completed": ["DS-FIRST-001", "DS-FIRST-002", "DS-FIRST-003"],
            "current": "DS-FIRST-004",
            "next": "DS-FIRST-005",
        },
        "user_guardrails": [
            "不要为了缺失经营字段继续循环追补；没有的数据保留为空值，以现有数据继续推进。",
            "DeepSeek 输出只能是 needs_review 草稿，不得直接变成 checked 结论。",
            "入口/节点、运营授权和缺失经营字段未闭合前，不得宣称 P2 已通过。",
        ],
        "evidence_summary": summarize_evidence(evidence_rows),
        "business_fill_summary": summarize_business_fill(business_rows),
        "enriched_worklist_summary": summarize_enriched(enriched_rows),
        "field_checklist_summary": summarize_checklist(checklist_rows),
        "node_review_queue_summary": summarize_node_queue(node_rows),
        "verification_summary": summarize_verification_markdown(verification_text),
        "p0_audit_summary": {
            "overall_verdict": p0_audit.get("overall_verdict"),
            "a2_pdf_tables": p0_audit.get("summary", {}).get("A2_pdf_tables", {}),
            "a6_p0_routes": p0_audit.get("summary", {}).get("A6_p0_routes", {}),
            "gaps_requiring_action": p0_audit.get("gaps_requiring_action", []),
        },
        "durable_context": durable_context,
        "report_context": report_context,
    }


def make_messages(context: dict[str, Any]) -> list[dict[str, str]]:
    evidence_total = context["evidence_summary"]["total_rows"]
    checked_total = context["evidence_summary"]["validation_status"].get("checked", 0)
    assumption_total = context["evidence_summary"]["evidence_type"].get("presentation_assumption", 0)
    business_total = context["business_fill_summary"]["total_rows"]
    enriched_total = context["enriched_worklist_summary"]["total_rows"]
    checklist_total = context["field_checklist_summary"]["total_rows"]
    verification_total = context["verification_summary"].get("total_checks")
    verification_failures = context["verification_summary"].get("failures")
    verification_warnings = context["verification_summary"].get("warnings")
    return [
        {
            "role": "system",
            "content": (
                "你是本项目的 P1 质量报告草稿助手。"
                "你只能基于提供的结构化事实和上下文生成 Markdown 草稿。"
                "不得编造新数字，不得把待核验项写成已确认事实，不得宣称 P2 已通过。"
                "遇到缺失字段时，必须明确写成空值或待核验，不得要求在本稿里继续追补。"
                "只输出 Markdown 正文，不输出代码块。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请生成一份 `needs_review` 的 P1 质量报告草稿。\n"
                "必须使用以下标题结构，标题文字必须完全一致：\n"
                "# P1 质量报告草稿（DeepSeek）\n"
                "## 当前阶段结论\n"
                "## 关键数字\n"
                "## 证据完整度\n"
                "## 已完成事项\n"
                "## 主要未闭合缺口\n"
                "## 主要风险\n"
                "## P2 前置条件\n"
                "## 明确不做的结论\n"
                "## 建议的下一步\n\n"
                "在 `## 关键数字` 下，必须逐行出现以下标签，并保持数值与上下文完全一致：\n"
                f"- 证据台账总条数：{evidence_total}\n"
                f"- 已 checked 证据：{checked_total}\n"
                f"- presentation_assumption：{assumption_total}\n"
                f"- P0 经营字段复核记录：{business_total}\n"
                f"- enriched P0 工作项：{enriched_total}\n"
                f"- 现场核验检查表：{checklist_total}\n"
                f"- 最新落实性验证：{verification_total} 项通过，失败 {verification_failures}，警告 {verification_warnings}\n\n"
                "内容约束：\n"
                "1. 开头必须明确写出：当前仍在 P1，尚未进入 P2，本稿状态为 needs_review。\n"
                "2. 必须明确写出：缺失经营字段在本稿中按空值/待核验处理，不再为本段反复追补。\n"
                "3. 必须同时覆盖证据链、P0 经营字段、入口/节点、运营授权、路径代理和验证门禁。\n"
                "4. `## 明确不做的结论` 里必须写明不把代理路径、未核验入口、未核验授权和空值复核假设当成最终事实。\n"
                "5. 不要输出表格。使用简洁段落和项目符号。\n\n"
                "上下文 JSON：\n"
                + json.dumps(context, ensure_ascii=False)
            ),
        },
    ]


def run() -> None:
    task_id = "LLM-016"
    route = route_for(task_id)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    context = build_context()
    content = run_deepseek_task(task_id, make_messages(context), temperature=0.0)
    draft = strip_markdown_fence(content)

    OUT_DRAFT.write_text(draft.strip() + "\n", encoding="utf-8")
    RAW_JSONL.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "task_id": task_id,
                "task_name": route.task_name,
                "executor": route.default_executor,
                "model": route.model,
                "output_status": route.output_status,
                "input_paths": [
                    str(EVIDENCE_LEDGER.relative_to(ROOT)).replace("\\", "/"),
                    str(BUSINESS_FILL.relative_to(ROOT)).replace("\\", "/"),
                    str(ENRICHED_WORKLIST.relative_to(ROOT)).replace("\\", "/"),
                    str(FIELD_CHECKLIST.relative_to(ROOT)).replace("\\", "/"),
                    str(QUALITY_REPORT.relative_to(ROOT)).replace("\\", "/"),
                    str(P0_AUDIT_JSON.relative_to(ROOT)).replace("\\", "/"),
                    str(VERIFICATION_REPORT.relative_to(ROOT)).replace("\\", "/"),
                ],
                "response_excerpt": draft[:5000],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    PROGRESS_JSON.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "evidence_rows": context["evidence_summary"]["total_rows"],
                "business_fill_rows": context["business_fill_summary"]["total_rows"],
                "enriched_work_rows": context["enriched_worklist_summary"]["total_rows"],
                "field_checklist_rows": context["field_checklist_summary"]["total_rows"],
                "verification_checks": context["verification_summary"].get("total_checks"),
                "output_status": route.output_status,
                "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    GENERATION_REPORT.write_text(
        "\n".join(
            [
                "# DeepSeek P1 质量报告草稿生成报告",
                "",
                "## 结论",
                "",
                "- 输出状态：needs_review。",
                f"- 证据台账总条数：{context['evidence_summary']['total_rows']}。",
                f"- P0 经营字段复核记录：{context['business_fill_summary']['total_rows']} 条。",
                f"- enriched P0 工作项：{context['enriched_worklist_summary']['total_rows']} 条。",
                f"- 现场核验检查表：{context['field_checklist_summary']['total_rows']} 条。",
                f"- 最新落实性验证：{context['verification_summary'].get('total_checks')} 项通过，失败 {context['verification_summary'].get('failures')}，警告 {context['verification_summary'].get('warnings')}。",
                "",
                "## 口径",
                "",
                "- 本次只基于现有数据生成 P1 质量报告草稿，不继续追补空值。",
                "- 草稿不得被视为 P2 放行结论，入口/节点、运营授权和缺失经营字段仍是未闭合事项。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote draft to {OUT_DRAFT}")
    print(f"wrote generation report to {GENERATION_REPORT}")


if __name__ == "__main__":
    run()
