from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ENRICHED_WORKLIST = ROOT / "70_outputs" / "processed_tables" / "poi_supply_p0_followup_worklist_enriched.csv"
NODE_QUEUE = ROOT / "50_external_gis" / "amap_routes" / "amap_p0_entrance_node_semantic_review_queue.csv"
CHECKLIST = ROOT / "70_outputs" / "processed_tables" / "p0_field_verification_checklist_deepseek.csv"
OUT_REVIEW = ROOT / "40_quality_evidence" / "deepseek_p0_field_verification_checklist_review.csv"
REPORT = ROOT / "40_quality_evidence" / "deepseek_p0_field_verification_checklist_review.md"

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


def ok(condition: bool) -> str:
    return "pass" if condition else "fail"


def add(rows: list[dict[str, str]], status: str, severity: str, finding: str, evidence: str) -> None:
    rows.append(
        {
            "check_id": f"FIELD-CHECK-REVIEW-{len(rows) + 1:03d}",
            "status": status,
            "severity": severity,
            "finding": finding,
            "evidence": evidence,
        }
    )


def main() -> None:
    work_rows = read_csv(ENRICHED_WORKLIST)
    node_rows = read_csv(NODE_QUEUE)
    checklist_rows = read_csv(CHECKLIST)
    expected_node_ids = {
        row.get("semantic_review_id", "")
        for row in node_rows
        if row.get("final_use_gate") != "do_not_use_as_access_node_until_manual_review"
    }
    excluded_node_ids = {
        row.get("semantic_review_id", "")
        for row in node_rows
        if row.get("final_use_gate") == "do_not_use_as_access_node_until_manual_review"
    }
    expected_source_ids = {row.get("work_item_id", "") for row in work_rows} | expected_node_ids
    checklist_source_ids = {row.get("source_id", "") for row in checklist_rows}
    statuses = Counter(row.get("output_status", "") for row in checklist_rows)
    gates = Counter(row.get("p2_gate_draft", "") for row in checklist_rows)
    executors = Counter(row.get("executor", "") for row in checklist_rows)
    task_ids = Counter(row.get("llm_task_id", "") for row in checklist_rows)
    type_counts = Counter(row.get("checklist_type", "") for row in checklist_rows)
    priority_counts = Counter(row.get("priority", "") for row in checklist_rows)
    excluded_present = sorted(checklist_source_ids & excluded_node_ids)
    missing_core_text = [
        row.get("checklist_id", "")
        for row in checklist_rows
        if not row.get("verification_goal_draft") or not row.get("on_site_questions_draft") or not row.get("acceptable_evidence_draft")
    ]
    explicit_bad_claims = [
        row.get("checklist_id", "")
        for row in checklist_rows
        if row.get("output_status") == "checked" or "P2通过" in "".join(row.values()) or "官方入口已确认" in "".join(row.values())
    ]

    review: list[dict[str, str]] = []
    add(review, ok(len(checklist_rows) == 34), "error", f"checklist rows={len(checklist_rows)}, expected=34", str(CHECKLIST))
    add(review, ok(checklist_source_ids == expected_source_ids), "error", f"source ids match expected={checklist_source_ids == expected_source_ids}", "source_id")
    add(review, ok(statuses == {"needs_review": len(checklist_rows)}), "error", f"output_status distribution={dict(statuses)}", "output_status")
    add(review, ok(gates == {P2_GATE: len(checklist_rows)}), "error", f"p2 gate distribution={dict(gates)}", "p2_gate_draft")
    add(review, ok(executors == {"deepseek": len(checklist_rows)}), "error", f"executor distribution={dict(executors)}", "executor")
    add(review, ok(task_ids == {"LLM-015": len(checklist_rows)}), "error", f"task id distribution={dict(task_ids)}", "llm_task_id")
    add(review, ok(not excluded_present), "error", f"excluded low-confidence nodes present={excluded_present}", "source_id")
    add(review, ok(not missing_core_text), "error", f"missing core checklist text rows={missing_core_text}", "verification fields")
    add(review, ok(not explicit_bad_claims), "error", f"explicit checked/P2 claims={explicit_bad_claims}", "checklist text")
    add(review, "pass", "info", f"checklist type distribution={dict(type_counts)}", "checklist_type")
    add(review, "pass", "info", f"priority distribution={dict(priority_counts)}", "priority")

    write_csv(OUT_REVIEW, review, REVIEW_FIELDS)
    by_status = Counter(row["status"] for row in review)
    REPORT.write_text(
        "\n".join(
            [
                "# DeepSeek P0 现场核验检查表本地复核报告",
                "",
                "## 结论",
                "",
                f"- 复核项状态：{dict(sorted(by_status.items()))}",
                f"- 检查类型分布：{dict(sorted(type_counts.items()))}",
                f"- 输出状态分布：{dict(sorted(statuses.items()))}",
                "",
                "## 口径",
                "",
                "- 本复核只确认现场核验检查表结构和门禁字段可用。",
                "- 不代表任何入口、经营字段或运营授权已经确认。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    failures = [row for row in review if row["status"] == "fail"]
    print(f"wrote field verification checklist review rows={len(review)} to {OUT_REVIEW}")
    print(f"wrote report to {REPORT}")
    print(f"failures={len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
