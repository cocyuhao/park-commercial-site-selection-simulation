from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "70_outputs" / "processed_tables" / "p3_calibration_evidence_request_worklist_deepseek.csv"
ACCEPTANCE = ROOT / "70_outputs" / "processed_tables" / "p3_calibration_acceptance_criteria_deepseek.csv"
LIMITS = ROOT / "70_outputs" / "processed_tables" / "p3_scenario_assumption_limits_deepseek.csv"
BLOCKERS = ROOT / "70_outputs" / "processed_tables" / "p3_calibration_blocker_register_deepseek.csv"
GATE = ROOT / "70_outputs" / "processed_tables" / "p3_calibration_gate_status.csv"
SUMMARY = ROOT / "40_quality_evidence" / "deepseek_p3_calibration_execution_package.json"
OUT_CSV = ROOT / "40_quality_evidence" / "deepseek_p3_calibration_execution_package_review.csv"
OUT_MD = ROOT / "40_quality_evidence" / "deepseek_p3_calibration_execution_package_review.md"

FIELDS = ["check_id", "status", "severity", "finding", "evidence"]
CORE_DOMAINS = {"geometry", "visitor_flow", "conversion_rate", "revenue_cost", "operation_authorization", "model_gate"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def add(rows: list[dict[str, str]], condition: bool, severity: str, finding: str, evidence: Path) -> None:
    rows.append(
        {
            "check_id": f"P3-CALIB-REVIEW-{len(rows) + 1:03d}",
            "status": "pass" if condition else "fail",
            "severity": severity,
            "finding": finding,
            "evidence": str(evidence.relative_to(ROOT)).replace("\\", "/"),
        }
    )


def check_common(rows: list[dict[str, str]], name: str, table: list[dict[str, str]], path: Path) -> None:
    statuses = Counter(row.get("output_status", "") for row in table)
    executors = Counter(row.get("executor", "") for row in table)
    task_ids = Counter(row.get("llm_task_id", "") for row in table)
    add(rows, statuses == {"needs_review": len(table)}, "error", f"{name} statuses={dict(statuses)}", path)
    add(rows, executors == {"deepseek": len(table)}, "error", f"{name} executors={dict(executors)}", path)
    add(rows, task_ids == {"LLM-023": len(table)}, "error", f"{name} task ids={dict(task_ids)}", path)


def main() -> None:
    rows: list[dict[str, str]] = []
    evidence = read_csv(EVIDENCE)
    acceptance = read_csv(ACCEPTANCE)
    limits = read_csv(LIMITS)
    blockers = read_csv(BLOCKERS)
    gate = read_csv(GATE)
    summary = json.loads(SUMMARY.read_text(encoding="utf-8-sig"))

    add(rows, len(evidence) == 24, "error", f"evidence request rows={len(evidence)}", EVIDENCE)
    add(rows, len(acceptance) == 18, "error", f"acceptance rows={len(acceptance)}", ACCEPTANCE)
    add(rows, len(limits) == 12, "error", f"assumption limit rows={len(limits)}", LIMITS)
    add(rows, len(blockers) == 12, "error", f"blocker rows={len(blockers)}", BLOCKERS)
    add(rows, len(gate) == 6, "error", f"gate rows={len(gate)}", GATE)

    for name, table, path in [
        ("evidence", evidence, EVIDENCE),
        ("acceptance", acceptance, ACCEPTANCE),
        ("limits", limits, LIMITS),
        ("blockers", blockers, BLOCKERS),
    ]:
        check_common(rows, name, table, path)

    for name, table, path in [
        ("evidence", evidence, EVIDENCE),
        ("acceptance", acceptance, ACCEPTANCE),
        ("limits", limits, LIMITS),
        ("blockers", blockers, BLOCKERS),
        ("gate", gate, GATE),
    ]:
        domains = {row.get("calibration_domain", "") for row in table}
        add(rows, CORE_DOMAINS <= domains, "error", f"{name} covers core domains missing={sorted(CORE_DOMAINS - domains)}", path)

    evidence_statuses = {row.get("current_status", "") for row in evidence}
    add(rows, evidence_statuses <= {"pending_collection", "pending_conversion", "blocked_until_source_received", "needs_review"}, "error", f"evidence statuses={sorted(evidence_statuses)}", EVIDENCE)
    add(rows, any(row.get("calibration_domain") == "geometry" and row.get("current_status") == "pending_conversion" for row in evidence), "error", "geometry evidence remains pending_conversion", EVIDENCE)
    add(rows, all(row.get("blocks_p4_conclusion") == "yes" for row in acceptance), "error", "acceptance criteria block P4 conclusion", ACCEPTANCE)
    limit_text = "\n".join(" ".join(row.values()) for row in limits)
    forbidden_tokens = ["完整仿真结论", "最终排序", "收益预测", "坐标面积"]
    add(rows, all(token in limit_text for token in forbidden_tokens), "error", "scenario limits forbid premature P4 outputs", LIMITS)
    blocker_statuses = Counter(row.get("current_status", "") for row in blockers)
    add(rows, blocker_statuses == {"blocked_until_source_received": len(blockers)}, "error", f"blocker statuses={dict(blocker_statuses)}", BLOCKERS)
    gate_statuses = {row.get("current_gate_status", "") for row in gate}
    add(rows, "closed" not in gate_statuses and "passed" not in gate_statuses, "error", f"P3 gates are not falsely closed statuses={sorted(gate_statuses)}", GATE)
    add(rows, all(row.get("required_before_p4_conclusion") == "yes" for row in gate), "error", "all P3 gates required before P4 conclusion", GATE)
    add(rows, summary.get("output_status") == "needs_review", "error", f"summary output_status={summary.get('output_status')}", SUMMARY)
    add(rows, summary.get("executor") == "deepseek", "error", f"summary executor={summary.get('executor')}", SUMMARY)
    add(rows, summary.get("llm_task_id") == "LLM-023", "error", f"summary task={summary.get('llm_task_id')}", SUMMARY)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    failures = [row for row in rows if row["status"] != "pass"]
    OUT_MD.write_text(
        "\n".join(
            [
                "# DeepSeek P3 calibration execution package review",
                "",
                f"- checks: {len(rows)}",
                f"- failures: {len(failures)}",
                "- conclusion: P3 calibration execution package is structurally ready, but P3 real calibration gates remain open until trusted sources are received.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote P3 calibration execution review rows={len(rows)} to {OUT_CSV}")
    print(f"failures={len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
