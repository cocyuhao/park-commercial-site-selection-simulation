from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUDIT_JSON = ROOT / "40_quality_evidence" / "deepseek_p2_completion_readiness_audit.json"
AUDIT_CSV = ROOT / "40_quality_evidence" / "deepseek_p2_completion_readiness_audit_checks.csv"
OUT_CSV = ROOT / "40_quality_evidence" / "deepseek_p2_completion_readiness_audit_review.csv"
OUT_MD = ROOT / "40_quality_evidence" / "deepseek_p2_completion_readiness_audit_review.md"

FIELDS = ["check_id", "status", "severity", "finding", "evidence"]


def add(rows: list[dict[str, str]], status: str, severity: str, finding: str, evidence: str) -> None:
    rows.append(
        {
            "check_id": f"P2-READY-REVIEW-{len(rows) + 1:03d}",
            "status": status,
            "severity": severity,
            "finding": finding,
            "evidence": evidence,
        }
    )


def ok(condition: bool) -> str:
    return "pass" if condition else "fail"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    rows: list[dict[str, str]] = []
    audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8-sig"))
    audit_rows = read_csv(AUDIT_CSV)

    add(rows, ok(audit.get("output_status") == "needs_review"), "error", f"output_status={audit.get('output_status')}", str(AUDIT_JSON))
    add(rows, ok(audit.get("executor") == "deepseek"), "error", f"executor={audit.get('executor')}", str(AUDIT_JSON))
    add(rows, ok(audit.get("llm_task_id") == "LLM-019"), "error", f"llm_task_id={audit.get('llm_task_id')}", str(AUDIT_JSON))
    add(rows, ok(audit.get("can_close_p2_method_prototype") is True), "error", "P2 method prototype can close", str(AUDIT_JSON))
    add(rows, ok(audit.get("cannot_claim_full_simulation") is True), "error", "full simulation is not claimed", str(AUDIT_JSON))

    source = audit.get("source_reading_assessment", {})
    add(rows, ok(source.get("docx_studied") is True), "error", f"docx_studied={source.get('docx_studied')}", str(AUDIT_JSON))
    add(rows, ok(source.get("pdf_studied") is True), "error", f"pdf_studied={source.get('pdf_studied')}", str(AUDIT_JSON))
    add(rows, ok(source.get("dwg_geometry_parsed") is False), "error", f"dwg_geometry_parsed={source.get('dwg_geometry_parsed')}", str(AUDIT_JSON))

    for key, expected in [
        ("prototype_ready_items", 8),
        ("blocking_gaps_for_real_calibration", 8),
        ("recommended_p2_outputs", 6),
        ("handoff_risks", 5),
    ]:
        add(rows, ok(isinstance(audit.get(key), list) and len(audit[key]) == expected), "error", f"{key} rows={len(audit.get(key, []))}, expected={expected}", str(AUDIT_JSON))

    by_type: dict[str, int] = {}
    for row in audit_rows:
        by_type[row.get("audit_type", "")] = by_type.get(row.get("audit_type", ""), 0) + 1
    add(rows, ok(len(audit_rows) == 27), "error", f"audit csv rows={len(audit_rows)}", str(AUDIT_CSV))
    add(rows, ok(by_type.get("blocking_gaps_for_real_calibration") == 8), "error", f"blocking gap csv rows={by_type}", str(AUDIT_CSV))

    text = json.dumps(audit, ensure_ascii=False)
    for keyword in ["DWG", "PPT", "客流", "转化率", "收益", "成本", "运营授权"]:
        add(rows, ok(keyword in text), "error", f"keyword covered: {keyword}", str(AUDIT_JSON))

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    failures = [row for row in rows if row["status"] != "pass"]
    OUT_MD.write_text(
        "\n".join(
            [
                "# DeepSeek P2 完成度审计本地复核报告",
                "",
                f"- 检查项：{len(rows)}",
                f"- 失败项：{len(failures)}",
                "",
                "## 结论",
                "",
                "- P2 可以按方法原型闭环。",
                "- 不得声称完整仿真或真实校准已经完成。",
                "- DOCX/PDF 已进入审计，DWG 几何仍未解析。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"wrote p2 readiness review rows={len(rows)} to {OUT_CSV}")
    print(f"wrote review report to {OUT_MD}")
    print(f"failures={len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
