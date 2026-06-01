from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_CSV = ROOT / "70_outputs" / "processed_tables" / "p0_manual_verification_package_deepseek.csv"
OUT_REVIEW = ROOT / "40_quality_evidence" / "deepseek_p0_verification_package_review.csv"
REPORT = ROOT / "40_quality_evidence" / "deepseek_p0_verification_package_review.md"

P2_GATE = "do_not_enter_p2_until_field_or_official_confirmation"
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


def add(rows: list[dict[str, str]], status: str, severity: str, finding: str, evidence: str) -> None:
    rows.append(
        {
            "check_id": f"DS-P0-PKG-{len(rows) + 1:03d}",
            "status": status,
            "severity": severity,
            "finding": finding,
            "evidence": evidence,
        }
    )


def ok(condition: bool) -> str:
    return "pass" if condition else "fail"


def build_review(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    review: list[dict[str, str]] = []
    statuses = Counter(row.get("output_status", "") for row in rows)
    executors = Counter(row.get("executor", "") for row in rows)
    task_ids = Counter(row.get("llm_task_id", "") for row in rows)
    gates = Counter(row.get("p2_gate_draft", "") for row in rows)
    work_item_ids = {row.get("work_item_id", "") for row in rows}
    empty_summaries = [
        row.get("work_item_id", "")
        for row in rows
        if not row.get("p0_verification_summary_draft", "").strip()
        or not row.get("business_field_followup_draft", "").strip()
        or not row.get("operation_authorization_followup_draft", "").strip()
    ]
    risky_gate_terms = [
        row.get("work_item_id", "")
        for row in rows
        if "可以进入P2" in "".join(row.values()) or "已确认" in "".join(row.values())
    ]

    add(review, ok(len(rows) == 7), "error", f"P0 verification package rows={len(rows)}", str(PACKAGE_CSV))
    add(review, ok(len(work_item_ids) == 7), "error", f"unique work_item_ids={len(work_item_ids)}", "work_item_id")
    add(review, ok(statuses == {"needs_review": len(rows)}), "error", f"output_status counts={dict(statuses)}", "output_status")
    add(review, ok(executors == {"deepseek": len(rows)}), "error", f"executor counts={dict(executors)}", "executor")
    add(review, ok(task_ids == {"LLM-012": len(rows)}), "error", f"llm_task_id counts={dict(task_ids)}", "llm_task_id")
    add(review, ok(gates == {P2_GATE: len(rows)}), "error", f"p2_gate counts={dict(gates)}", "p2_gate_draft")
    add(review, ok(not empty_summaries), "error", f"empty required summaries={empty_summaries}", "summary fields")
    add(review, ok(not risky_gate_terms), "error", f"risky conclusion terms={risky_gate_terms}", "text fields")
    return review


def write_report(review_rows: list[dict[str, str]], package_rows: list[dict[str, str]]) -> None:
    by_status = Counter(row["status"] for row in review_rows)
    by_park = Counter(row.get("park_name", "") for row in package_rows)
    lines = [
        "# DeepSeek P0 人工核验包本地复核报告",
        "",
        "## 结论",
        "",
        f"- 复核项状态：{dict(sorted(by_status.items()))}",
        f"- 核验包按公园分布：{dict(sorted(by_park.items()))}",
        "",
        "## 口径限制",
        "",
        "- 该核验包仍为 `needs_review`，不代表任何事实已经确认。",
        "- 所有 P0 工作项仍不得进入 P2，直到经营字段、真实入口/节点和运营授权闭合。",
        "",
        "## 输出文件",
        "",
        "- `70_outputs/processed_tables/p0_manual_verification_package_deepseek.csv`",
        "- `40_quality_evidence/deepseek_p0_verification_package_review.csv`",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    package_rows = read_csv(PACKAGE_CSV)
    review_rows = build_review(package_rows)
    write_csv(OUT_REVIEW, review_rows, REVIEW_FIELDS)
    write_report(review_rows, package_rows)
    failures = [row for row in review_rows if row["status"] == "fail"]
    print(f"wrote P0 package review rows={len(review_rows)} to {OUT_REVIEW}")
    print(f"wrote report to {REPORT}")
    print(f"failures={len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
