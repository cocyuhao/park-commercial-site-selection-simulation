from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_LEDGER = ROOT / "40_quality_evidence" / "evidence_ledger.csv"
BUSINESS_FILL = ROOT / "70_outputs" / "processed_tables" / "p0_business_field_fill_amap.csv"
ENRICHED_WORKLIST = ROOT / "70_outputs" / "processed_tables" / "poi_supply_p0_followup_worklist_enriched.csv"
FIELD_CHECKLIST = ROOT / "70_outputs" / "processed_tables" / "p0_field_verification_checklist_deepseek.csv"
VERIFICATION_REPORT = ROOT / "40_quality_evidence" / "verification" / "implementation_verification_20260524.md"
P1_DRAFT = ROOT / "40_quality_evidence" / "p1_quality_report_draft_deepseek.md"
OUT_REVIEW = ROOT / "40_quality_evidence" / "deepseek_p1_quality_report_review.csv"
REPORT = ROOT / "40_quality_evidence" / "deepseek_p1_quality_report_review.md"

REVIEW_FIELDS = ["check_id", "status", "severity", "finding", "evidence"]
REQUIRED_HEADINGS = [
    "# P1 质量报告草稿（DeepSeek）",
    "## 当前阶段结论",
    "## 关键数字",
    "## 证据完整度",
    "## 已完成事项",
    "## 主要未闭合缺口",
    "## 主要风险",
    "## P2 前置条件",
    "## 明确不做的结论",
    "## 建议的下一步",
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


def ok(condition: bool) -> str:
    return "pass" if condition else "fail"


def add(rows: list[dict[str, str]], status: str, severity: str, finding: str, evidence: str) -> None:
    rows.append(
        {
            "check_id": f"P1-QUALITY-REVIEW-{len(rows) + 1:03d}",
            "status": status,
            "severity": severity,
            "finding": finding,
            "evidence": evidence,
        }
    )


def parse_verification_totals(text: str) -> tuple[int | None, int | None, int | None]:
    total_match = re.search(r"总检查项：\s*(\d+)", text)
    fail_match = re.search(r"失败项：\s*(\d+)", text)
    warn_match = re.search(r"警告项：\s*(\d+)", text)
    total = int(total_match.group(1)) if total_match else None
    failures = int(fail_match.group(1)) if fail_match else None
    warnings = int(warn_match.group(1)) if warn_match else None
    return total, failures, warnings


def has_numeric_line(text: str, label: str, value: int) -> bool:
    pattern = rf"{re.escape(label)}\s*{value}(?:\b|[，。项条])"
    return re.search(pattern, text) is not None


def main() -> None:
    evidence_rows = read_csv(EVIDENCE_LEDGER)
    business_rows = read_csv(BUSINESS_FILL)
    enriched_rows = read_csv(ENRICHED_WORKLIST)
    checklist_rows = read_csv(FIELD_CHECKLIST)
    verification_text = VERIFICATION_REPORT.read_text(encoding="utf-8-sig", errors="replace")
    total_checks, failures, warnings = parse_verification_totals(verification_text)
    draft = P1_DRAFT.read_text(encoding="utf-8-sig", errors="replace") if P1_DRAFT.exists() else ""

    checked_total = sum(1 for row in evidence_rows if row.get("validation_status") == "checked")
    assumption_total = sum(1 for row in evidence_rows if row.get("evidence_type") == "presentation_assumption")
    heading_missing = [heading for heading in REQUIRED_HEADINGS if heading not in draft]
    banned_patterns = {
        "P2已通过": r"P2已通过|可以进入P2|可直接进入P2",
        "官方入口已确认": r"官方入口已确认|入口已最终确认",
        "空值已复核": r"所有空值已复核|缺失字段已全部复核",
    }
    bad_claims = [name for name, pattern in banned_patterns.items() if re.search(pattern, draft)]

    review: list[dict[str, str]] = []
    add(review, ok(P1_DRAFT.exists() and len(draft.strip()) >= 800), "error", f"draft exists={P1_DRAFT.exists()}, chars={len(draft.strip())}", str(P1_DRAFT))
    add(review, ok(not heading_missing), "error", f"missing headings={heading_missing}", "headings")
    add(review, ok("needs_review" in draft and "当前仍在 P1，尚未进入 P2" in draft), "error", "draft states P1/not P2/needs_review", "current phase statement")
    add(review, ok("空值" in draft and "待核验" in draft and "不再" in draft), "error", "draft keeps null fields as empty or pending review without further chase", "null-field policy")
    add(review, ok(has_numeric_line(draft, "- 证据台账总条数：", len(evidence_rows))), "error", f"evidence total line expected={len(evidence_rows)}", "key numbers")
    add(review, ok(has_numeric_line(draft, "- 已 checked 证据：", checked_total)), "error", f"checked evidence line expected={checked_total}", "key numbers")
    add(review, ok(has_numeric_line(draft, "- presentation_assumption：", assumption_total)), "error", f"presentation assumption line expected={assumption_total}", "key numbers")
    add(review, ok(has_numeric_line(draft, "- P0 经营字段复核记录：", len(business_rows))), "error", f"business fill line expected={len(business_rows)}", "key numbers")
    add(review, ok(has_numeric_line(draft, "- enriched P0 工作项：", len(enriched_rows))), "error", f"enriched worklist line expected={len(enriched_rows)}", "key numbers")
    add(review, ok(has_numeric_line(draft, "- 现场核验检查表：", len(checklist_rows))), "error", f"field checklist line expected={len(checklist_rows)}", "key numbers")
    verification_line_ok = (
        total_checks is not None
        and failures is not None
        and warnings is not None
        and re.search(
            rf"- 最新落实性验证：\s*{total_checks}\s*项通过，失败\s*{failures}，警告\s*{warnings}",
            draft,
        )
        is not None
    )
    add(review, ok(verification_line_ok), "error", f"verification line expected total={total_checks}, failures={failures}, warnings={warnings}", "key numbers")
    add(review, ok(not bad_claims), "error", f"unexpected final claims={bad_claims}", "draft text")
    add(review, "pass", "info", f"draft length={len(draft.strip())}", str(P1_DRAFT))

    write_csv(OUT_REVIEW, review, REVIEW_FIELDS)
    by_status = Counter(row["status"] for row in review)
    REPORT.write_text(
        "\n".join(
            [
                "# DeepSeek P1 质量报告草稿本地复核报告",
                "",
                "## 结论",
                "",
                f"- 复核项状态：{dict(sorted(by_status.items()))}",
                f"- 草稿长度：{len(draft.strip())} 字符。",
                f"- 证据台账总条数：{len(evidence_rows)}。",
                f"- 最新落实性验证：{total_checks} 项通过，失败 {failures}，警告 {warnings}。",
                "",
                "## 口径",
                "",
                "- 本复核只确认 P1 质量报告草稿结构、关键数字和门禁表述可用。",
                "- 不代表 P2 已放行，也不代表入口、授权或缺失经营字段已经最终确认。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    failures_found = [row for row in review if row["status"] == "fail"]
    print(f"wrote p1 quality review rows={len(review)} to {OUT_REVIEW}")
    print(f"wrote review report to {REPORT}")
    print(f"failures={len(failures_found)}")
    if failures_found:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
