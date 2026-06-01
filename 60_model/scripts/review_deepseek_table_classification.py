from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SUMMARY = ROOT / "30_extraction" / "tables" / "pdf_native_tables_summary.csv"
DEEPSEEK_CSV = ROOT / "30_extraction" / "tables" / "pdf_table_topic_draft_deepseek.csv"
OUT_QUEUE = ROOT / "30_extraction" / "tables" / "pdf_table_review_queue.csv"
OUT_REVIEW = ROOT / "40_quality_evidence" / "deepseek_table_classification_review.csv"
REPORT = ROOT / "40_quality_evidence" / "deepseek_table_classification_review.md"


ALLOWED_TOPICS = {
    "visitor_flow",
    "time_peak",
    "demographic_profile",
    "origin_residence_work",
    "tgi_preference",
    "poi_hot_visit",
    "consumption_spending",
    "commercial_supply",
    "revenue_finance",
    "supply_gap",
    "empty_or_visual_noise",
    "other",
}

P0_TOPICS = {"poi_hot_visit", "consumption_spending", "visitor_flow", "time_peak", "commercial_supply"}
P1_TOPICS = {"tgi_preference", "demographic_profile", "origin_residence_work", "revenue_finance", "supply_gap"}

QUEUE_FIELDS = [
    "review_queue_id",
    "table_id",
    "source_file",
    "page",
    "table_index",
    "row_count",
    "column_count",
    "topic_draft",
    "topic_confidence",
    "sampling_priority",
    "evidence_candidate_status",
    "review_gate",
    "output_status",
    "reason_draft",
    "evidence_keywords_draft",
    "sample",
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


def priority(topic: str, confidence: str) -> str:
    if topic in P0_TOPICS:
        return "P0_second_evidence_candidate"
    if topic in P1_TOPICS:
        return "P1_context_or_followup_candidate"
    if topic == "empty_or_visual_noise":
        return "P3_skip_or_low_value"
    return "P2_low_priority_review"


def candidate_status(topic: str) -> str:
    if topic in P0_TOPICS:
        return "candidate_for_second_evidence_review"
    if topic in P1_TOPICS:
        return "context_candidate_needs_sampling"
    if topic == "empty_or_visual_noise":
        return "not_evidence_noise_or_empty"
    return "unclear_needs_sampling"


def build_queue(summary_rows: list[dict[str, str]], draft_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    summary_by_id = {row["table_id"]: row for row in summary_rows}
    queue_rows: list[dict[str, str]] = []
    for row in draft_rows:
        table_id = row["table_id"]
        summary = summary_by_id.get(table_id, {})
        topic = row.get("topic_draft", "")
        queue_rows.append(
            {
                "review_queue_id": f"TBL-REVIEW-{len(queue_rows) + 1:04d}",
                "table_id": table_id,
                "source_file": row.get("source_file", ""),
                "page": row.get("page", ""),
                "table_index": row.get("table_index", ""),
                "row_count": row.get("row_count", ""),
                "column_count": row.get("column_count", ""),
                "topic_draft": topic,
                "topic_confidence": row.get("topic_confidence", ""),
                "sampling_priority": priority(topic, row.get("topic_confidence", "")),
                "evidence_candidate_status": candidate_status(topic),
                "review_gate": row.get("review_gate", ""),
                "output_status": row.get("output_status", ""),
                "reason_draft": row.get("reason_draft", ""),
                "evidence_keywords_draft": row.get("evidence_keywords_draft", ""),
                "sample": summary.get("sample", ""),
            }
        )
    priority_order = {
        "P0_second_evidence_candidate": 0,
        "P1_context_or_followup_candidate": 1,
        "P2_low_priority_review": 2,
        "P3_skip_or_low_value": 3,
    }
    return sorted(
        queue_rows,
        key=lambda row: (
            priority_order.get(row["sampling_priority"], 9),
            row["source_file"],
            int(row["page"] or 0),
            row["table_id"],
        ),
    )


def add_review(rows: list[dict[str, str]], status: str, severity: str, finding: str, evidence: str) -> None:
    rows.append(
        {
            "check_id": f"DSTBL-{len(rows) + 1:03d}",
            "status": status,
            "severity": severity,
            "finding": finding,
            "evidence": evidence,
        }
    )


def build_review(summary_rows: list[dict[str, str]], draft_rows: list[dict[str, str]], queue_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    review_rows: list[dict[str, str]] = []
    summary_ids = {row["table_id"] for row in summary_rows}
    draft_ids = {row["table_id"] for row in draft_rows}
    topics = Counter(row.get("topic_draft", "") for row in draft_rows)
    statuses = Counter(row.get("output_status", "") for row in draft_rows)
    invalid_topics = sorted(topic for topic in topics if topic not in ALLOWED_TOPICS)
    missing = sorted(summary_ids - draft_ids)
    extra = sorted(draft_ids - summary_ids)
    p0_count = sum(1 for row in queue_rows if row["sampling_priority"] == "P0_second_evidence_candidate")

    add_review(review_rows, "pass" if len(summary_rows) == 329 else "fail", "error", f"source summary rows={len(summary_rows)}", "30_extraction/tables/pdf_native_tables_summary.csv")
    add_review(review_rows, "pass" if len(draft_rows) == 329 else "fail", "error", f"DeepSeek draft rows={len(draft_rows)}", "30_extraction/tables/pdf_table_topic_draft_deepseek.csv")
    add_review(review_rows, "pass" if not missing else "fail", "error", f"missing table ids={missing[:20]}", "table_id coverage")
    add_review(review_rows, "pass" if not extra else "fail", "error", f"extra table ids={extra[:20]}", "table_id coverage")
    add_review(review_rows, "pass" if not invalid_topics else "fail", "error", f"invalid topics={invalid_topics}", "topic_draft")
    add_review(review_rows, "pass" if statuses == {"draft": len(draft_rows)} else "fail", "error", f"output_status counts={dict(statuses)}", "output_status")
    add_review(review_rows, "pass", "info", f"topic distribution={dict(sorted(topics.items()))}", "topic_draft")
    add_review(review_rows, "pass", "info", f"P0 second evidence candidate tables={p0_count}", "pdf_table_review_queue.csv")
    return review_rows


def write_report(review_rows: list[dict[str, str]], queue_rows: list[dict[str, str]]) -> None:
    by_status = Counter(row["status"] for row in review_rows)
    by_priority = Counter(row["sampling_priority"] for row in queue_rows)
    by_candidate = Counter(row["evidence_candidate_status"] for row in queue_rows)
    by_topic = Counter(row["topic_draft"] for row in queue_rows)
    p0_examples = [
        f"{row['table_id']} p{row['page']} {row['topic_draft']}"
        for row in queue_rows
        if row["sampling_priority"] == "P0_second_evidence_candidate"
    ][:20]

    lines = [
        "# DeepSeek 表格分类本地复核报告",
        "",
        "## 结论",
        "",
        f"- 复核项状态：{dict(sorted(by_status.items()))}",
        f"- 复核队列优先级：{dict(sorted(by_priority.items()))}",
        f"- 证据候选状态：{dict(sorted(by_candidate.items()))}",
        f"- 主题分布：{dict(sorted(by_topic.items()))}",
        "",
        "## P0 复核样例",
        "",
    ]
    for item in p0_examples:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## 口径限制",
            "",
            "- DeepSeek 分类只能作为 `draft`；本地复核只检查结构完整性和复核优先级。",
            "- `P0_second_evidence_candidate` 代表优先复核，不代表已经入账或真实。",
            "- 第二批入账仍需回到 `pdf_native_tables.jsonl` 和 PDF 原文确认字段、单位、页码、口径。",
            "",
            "## 输出文件",
            "",
            "- `30_extraction/tables/pdf_table_review_queue.csv`",
            "- `40_quality_evidence/deepseek_table_classification_review.csv`",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    summary_rows = read_csv(SUMMARY)
    draft_rows = read_csv(DEEPSEEK_CSV)
    queue_rows = build_queue(summary_rows, draft_rows)
    review_rows = build_review(summary_rows, draft_rows, queue_rows)
    write_csv(OUT_QUEUE, queue_rows, QUEUE_FIELDS)
    write_csv(OUT_REVIEW, review_rows, REVIEW_FIELDS)
    write_report(review_rows, queue_rows)
    failures = [row for row in review_rows if row["status"] == "fail"]
    print(f"wrote review queue rows={len(queue_rows)} to {OUT_QUEUE}")
    print(f"wrote review report to {REPORT}")
    print(f"failures={len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
