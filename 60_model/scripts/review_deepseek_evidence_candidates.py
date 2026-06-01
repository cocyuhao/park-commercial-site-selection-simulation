from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
QUEUE_CSV = ROOT / "30_extraction" / "tables" / "pdf_table_review_queue.csv"
CANDIDATES_CSV = ROOT / "30_extraction" / "tables" / "pdf_table_evidence_candidates_deepseek.csv"
OUT_QUEUE = ROOT / "30_extraction" / "tables" / "pdf_evidence_candidate_review_queue.csv"
OUT_REVIEW = ROOT / "40_quality_evidence" / "deepseek_evidence_candidates_review.csv"
REPORT = ROOT / "40_quality_evidence" / "deepseek_evidence_candidates_review.md"


ALLOWED_CANDIDATE_TYPES = {
    "visitor_flow",
    "time_peak",
    "poi_hot_visit",
    "commercial_supply",
    "consumption_spending",
    "revenue_finance",
    "supply_gap",
    "other",
}

QUEUE_FIELDS = [
    "candidate_review_id",
    "candidate_id",
    "table_id",
    "source_file",
    "page",
    "topic_draft",
    "candidate_type",
    "metric_name_draft",
    "subject_draft",
    "value_draft",
    "unit_draft",
    "source_row_text_draft",
    "extraction_confidence",
    "candidate_review_priority",
    "ledger_entry_status",
    "review_instruction",
    "output_status",
]

REVIEW_FIELDS = ["check_id", "status", "severity", "finding", "evidence"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def review_priority(row: dict[str, str]) -> str:
    candidate_type = row.get("candidate_type", "")
    metric = row.get("metric_name_draft", "")
    unit = row.get("unit_draft", "")
    if candidate_type in {"visitor_flow", "time_peak"}:
        return "P0_flow_or_peak_numeric_check"
    if candidate_type == "consumption_spending" and ("消费" in metric or unit in {"元", "次", "%"}):
        return "P0_spending_numeric_check"
    if candidate_type == "poi_hot_visit" and row.get("value_draft"):
        return "P1_poi_hot_visit_row_check"
    if candidate_type == "commercial_supply":
        return "P1_supply_context_check"
    if candidate_type in {"revenue_finance", "supply_gap"}:
        return "P1_business_assumption_check"
    return "P2_low_priority_or_no_candidate"


def review_instruction(row: dict[str, str]) -> str:
    candidate_type = row.get("candidate_type", "")
    if candidate_type == "poi_hot_visit":
        return "回查 PDF 表格行，确认 POI 名称、指数、人均消费是否逐格对应；热门到访不等于完整供给。"
    if candidate_type in {"visitor_flow", "time_peak"}:
        return "回查 PDF 页和表头，确认人次/小时/日期/人群口径，再决定是否入账。"
    if candidate_type == "consumption_spending":
        return "回查单位、金额或频次口径，避免把全市大盘和目标客群混用。"
    if candidate_type == "commercial_supply":
        return "仅作为供给线索，必须结合高德/现场/边界核验后才能作为供给数量。"
    return "抽样回查原表，确认是否有可入账指标；不能由 DeepSeek 直接入账。"


def build_queue(candidate_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in candidate_rows:
        priority = review_priority(row)
        rows.append(
            {
                "candidate_review_id": f"EV-REVIEW-{len(rows) + 1:04d}",
                "candidate_id": row.get("candidate_id", ""),
                "table_id": row.get("table_id", ""),
                "source_file": row.get("source_file", ""),
                "page": row.get("page", ""),
                "topic_draft": row.get("topic_draft", ""),
                "candidate_type": row.get("candidate_type", ""),
                "metric_name_draft": row.get("metric_name_draft", ""),
                "subject_draft": row.get("subject_draft", ""),
                "value_draft": row.get("value_draft", ""),
                "unit_draft": row.get("unit_draft", ""),
                "source_row_text_draft": row.get("source_row_text_draft", ""),
                "extraction_confidence": row.get("extraction_confidence", ""),
                "candidate_review_priority": priority,
                "ledger_entry_status": "needs_pdf_row_check_before_ledger",
                "review_instruction": review_instruction(row),
                "output_status": row.get("output_status", ""),
            }
        )
    priority_order = {
        "P0_flow_or_peak_numeric_check": 0,
        "P0_spending_numeric_check": 1,
        "P1_poi_hot_visit_row_check": 2,
        "P1_supply_context_check": 3,
        "P1_business_assumption_check": 4,
        "P2_low_priority_or_no_candidate": 5,
    }
    return sorted(
        rows,
        key=lambda row: (
            priority_order.get(row["candidate_review_priority"], 9),
            row["source_file"],
            int(row["page"] or 0),
            row["table_id"],
            row["candidate_id"],
        ),
    )


def add_review(rows: list[dict[str, str]], status: str, severity: str, finding: str, evidence: str) -> None:
    rows.append(
        {
            "check_id": f"DSEV-{len(rows) + 1:03d}",
            "status": status,
            "severity": severity,
            "finding": finding,
            "evidence": evidence,
        }
    )


def build_review(p0_table_ids: set[str], candidate_rows: list[dict[str, str]], queue_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    review_rows: list[dict[str, str]] = []
    candidate_table_ids = {row.get("table_id", "") for row in candidate_rows}
    statuses = Counter(row.get("output_status", "") for row in candidate_rows)
    executors = Counter(row.get("executor", "") for row in candidate_rows)
    task_ids = Counter(row.get("llm_task_id", "") for row in candidate_rows)
    candidate_types = Counter(row.get("candidate_type", "") for row in candidate_rows)
    invalid_types = sorted(candidate_type for candidate_type in candidate_types if candidate_type not in ALLOWED_CANDIDATE_TYPES)
    empty_values = [row.get("candidate_id", "") for row in candidate_rows if not row.get("value_draft") and row.get("metric_name_draft") != "no_candidate"]
    missing_tables = sorted(p0_table_ids - candidate_table_ids)
    extra_tables = sorted(candidate_table_ids - p0_table_ids)
    checked_pollution = [row.get("candidate_id", "") for row in candidate_rows if row.get("output_status") == "checked"]
    queue_priorities = Counter(row.get("candidate_review_priority", "") for row in queue_rows)

    add_review(review_rows, "pass" if len(p0_table_ids) == 63 else "fail", "error", f"P0 source tables={len(p0_table_ids)}", "30_extraction/tables/pdf_table_review_queue.csv")
    add_review(review_rows, "pass" if len(candidate_rows) == 592 else "fail", "error", f"DeepSeek evidence candidates rows={len(candidate_rows)}", "30_extraction/tables/pdf_table_evidence_candidates_deepseek.csv")
    add_review(review_rows, "pass" if not missing_tables else "fail", "error", f"missing P0 table ids={missing_tables[:20]}", "table_id coverage")
    add_review(review_rows, "pass" if not extra_tables else "fail", "error", f"extra table ids={extra_tables[:20]}", "table_id coverage")
    add_review(review_rows, "pass" if statuses == {"needs_review": len(candidate_rows)} else "fail", "error", f"output_status counts={dict(statuses)}", "output_status")
    add_review(review_rows, "pass" if executors == {"deepseek": len(candidate_rows)} else "fail", "error", f"executor counts={dict(executors)}", "executor")
    add_review(review_rows, "pass" if task_ids == {"LLM-003": len(candidate_rows)} else "fail", "error", f"llm_task_id counts={dict(task_ids)}", "llm_task_id")
    add_review(review_rows, "pass" if not invalid_types else "fail", "error", f"invalid candidate types={invalid_types}", "candidate_type")
    add_review(review_rows, "pass" if not checked_pollution else "fail", "error", f"checked pollution={checked_pollution[:20]}", "output_status")
    add_review(review_rows, "pass" if len(empty_values) <= 10 else "fail", "warning", f"empty value rows={len(empty_values)}", "value_draft")
    add_review(review_rows, "pass", "info", f"candidate type distribution={dict(sorted(candidate_types.items()))}", "candidate_type")
    add_review(review_rows, "pass", "info", f"review priority distribution={dict(sorted(queue_priorities.items()))}", "pdf_evidence_candidate_review_queue.csv")
    return review_rows


def write_report(review_rows: list[dict[str, str]], queue_rows: list[dict[str, str]]) -> None:
    by_status = Counter(row["status"] for row in review_rows)
    by_priority = Counter(row["candidate_review_priority"] for row in queue_rows)
    by_type = Counter(row["candidate_type"] for row in queue_rows)
    examples = [
        f"{row['candidate_id']} {row['table_id']} p{row['page']} {row['candidate_type']} {row['metric_name_draft']} {row['subject_draft']}={row['value_draft']}{row['unit_draft']}"
        for row in queue_rows
        if row["candidate_review_priority"].startswith("P0_")
    ][:20]
    lines = [
        "# DeepSeek 证据候选本地复核报告",
        "",
        "## 结论",
        "",
        f"- 复核项状态：{dict(sorted(by_status.items()))}",
        f"- 候选复核优先级：{dict(sorted(by_priority.items()))}",
        f"- 候选类型：{dict(sorted(by_type.items()))}",
        "",
        "## P0 回查样例",
        "",
    ]
    for item in examples:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## 口径限制",
            "",
            "- DeepSeek 证据候选仍为 `needs_review`，不是已核验证据。",
            "- `pdf_evidence_candidate_review_queue.csv` 只是回查排序，不代表可直接入账。",
            "- 进入 `evidence_ledger.csv` 前必须确认 PDF 原表、页码、单位、主体和重复项。",
            "",
            "## 输出文件",
            "",
            "- `30_extraction/tables/pdf_evidence_candidate_review_queue.csv`",
            "- `40_quality_evidence/deepseek_evidence_candidates_review.csv`",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    p0_rows = [row for row in read_csv(QUEUE_CSV) if row.get("sampling_priority") == "P0_second_evidence_candidate"]
    p0_table_ids = {row["table_id"] for row in p0_rows}
    candidate_rows = read_csv(CANDIDATES_CSV)
    queue_rows = build_queue(candidate_rows)
    review_rows = build_review(p0_table_ids, candidate_rows, queue_rows)
    write_csv(OUT_QUEUE, queue_rows, QUEUE_FIELDS)
    write_csv(OUT_REVIEW, review_rows, REVIEW_FIELDS)
    write_report(review_rows, queue_rows)
    failures = [row for row in review_rows if row["status"] == "fail"]
    print(f"wrote evidence candidate review queue rows={len(queue_rows)} to {OUT_QUEUE}")
    print(f"wrote review report to {REPORT}")
    print(f"failures={len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
