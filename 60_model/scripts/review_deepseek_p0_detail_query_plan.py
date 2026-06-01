from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKLIST = ROOT / "70_outputs" / "processed_tables" / "poi_supply_p0_followup_worklist.csv"
PLAN = ROOT / "50_external_gis" / "amap_poi" / "amap_p0_detail_query_plan_deepseek.csv"
OUT_REVIEW = ROOT / "40_quality_evidence" / "deepseek_p0_detail_query_plan_review.csv"
REPORT = ROOT / "40_quality_evidence" / "deepseek_p0_detail_query_plan_review.md"

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
            "check_id": f"P0-DETAIL-{len(rows) + 1:03d}",
            "status": status,
            "severity": severity,
            "finding": finding,
            "evidence": evidence,
        }
    )


def main() -> None:
    work_rows = read_csv(WORKLIST)
    plan_rows = read_csv(PLAN)
    work_ids = {row.get("work_item_id", "") for row in work_rows}
    plan_ids = {row.get("work_item_id", "") for row in plan_rows}
    statuses = Counter(row.get("output_status", "") for row in plan_rows)
    gates = Counter(row.get("p2_gate_draft", "") for row in plan_rows)
    task_ids = Counter(row.get("llm_task_id", "") for row in plan_rows)
    executors = Counter(row.get("executor", "") for row in plan_rows)
    endpoints = Counter(row.get("amap_endpoint_draft", "") for row in plan_rows)
    query_modes = Counter(row.get("query_mode_draft", "") for row in plan_rows)
    priority_counts = Counter(row.get("query_priority", "") for row in plan_rows)
    missing_ids = [row.get("work_item_id", "") for row in plan_rows if not row.get("amap_detail_poi_id")]
    unexpected_claims = [
        row.get("work_item_id", "")
        for row in plan_rows
        if row.get("output_status") == "checked"
        or row.get("p2_gate_draft") != P2_GATE
        or "进入P2" in "".join(row.values())
    ]

    review: list[dict[str, str]] = []
    add(review, ok(len(plan_rows) == len(work_rows) == 7), "error", f"plan rows={len(plan_rows)}, worklist rows={len(work_rows)}", str(PLAN))
    add(review, ok(plan_ids == work_ids), "error", f"plan ids match worklist={plan_ids == work_ids}", "work_item_id")
    add(review, ok(statuses == {"needs_review": len(plan_rows)}), "error", f"output_status distribution={dict(statuses)}", "output_status")
    add(review, ok(gates == {P2_GATE: len(plan_rows)}), "error", f"p2 gate distribution={dict(gates)}", "p2_gate_draft")
    add(review, ok(task_ids == {"LLM-014": len(plan_rows)}), "error", f"task id distribution={dict(task_ids)}", "llm_task_id")
    add(review, ok(executors == {"deepseek": len(plan_rows)}), "error", f"executor distribution={dict(executors)}", "executor")
    add(review, ok(not missing_ids), "error", f"missing amap_detail_poi_id rows={missing_ids}", "amap_detail_poi_id")
    add(review, ok(not unexpected_claims), "error", f"unexpected checked/P2 claims={unexpected_claims}", "plan text")
    add(review, "pass", "info", f"endpoint distribution={dict(endpoints)}", "amap_endpoint_draft")
    add(review, "pass", "info", f"query mode distribution={dict(query_modes)}", "query_mode_draft")
    add(review, "pass", "info", f"query priority distribution={dict(priority_counts)}", "query_priority")

    write_csv(OUT_REVIEW, review, REVIEW_FIELDS)
    by_status = Counter(row["status"] for row in review)
    REPORT.write_text(
        "\n".join(
            [
                "# DeepSeek P0 高德详情查询计划本地复核报告",
                "",
                "## 结论",
                "",
                f"- 复核项状态：{dict(sorted(by_status.items()))}",
                f"- 输出状态分布：{dict(sorted(statuses.items()))}",
                f"- P2 门禁分布：{dict(sorted(gates.items()))}",
                "",
                "## 口径",
                "",
                "- 本复核只确认查询计划草稿结构可用。",
                "- 不代表高德详情 API 已调用，也不代表经营字段已确认。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    failures = [row for row in review if row["status"] == "fail"]
    print(f"wrote P0 Amap detail query plan review rows={len(review)} to {OUT_REVIEW}")
    print(f"wrote report to {REPORT}")
    print(f"failures={len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
