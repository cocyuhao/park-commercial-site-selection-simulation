from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FILES = {
    "personas": (ROOT / "70_outputs" / "processed_tables" / "p2_persona_parameter_prototype.csv", 6),
    "triggers": (ROOT / "70_outputs" / "processed_tables" / "p2_demand_trigger_matrix.csv", 12),
    "formula": (ROOT / "70_outputs" / "processed_tables" / "p2_supply_gap_scoring_formula.csv", 8),
    "scores": (ROOT / "70_outputs" / "processed_tables" / "p2_candidate_method_readiness_scores.csv", 6),
    "api": (ROOT / "70_outputs" / "processed_tables" / "p2_postman_api_contract_draft.csv", 8),
}
REPORT = ROOT / "40_quality_evidence" / "p2_method_prototype_report.md"
OUT_CSV = ROOT / "40_quality_evidence" / "p2_method_prototype_review.csv"
OUT_MD = ROOT / "40_quality_evidence" / "p2_method_prototype_review.md"

FIELDS = ["check_id", "status", "severity", "finding", "evidence"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def add(rows: list[dict[str, str]], status: str, severity: str, finding: str, evidence: str) -> None:
    rows.append(
        {
            "check_id": f"P2-METHOD-REVIEW-{len(rows) + 1:03d}",
            "status": status,
            "severity": severity,
            "finding": finding,
            "evidence": evidence,
        }
    )


def ok(condition: bool) -> str:
    return "pass" if condition else "fail"


def main() -> None:
    rows: list[dict[str, str]] = []
    data: dict[str, list[dict[str, str]]] = {}
    for name, (path, expected) in FILES.items():
        table = read_csv(path)
        data[name] = table
        add(rows, ok(len(table) == expected), "error", f"{name} rows={len(table)}, expected={expected}", str(path))
        statuses = Counter(row.get("output_status", "") for row in table)
        add(rows, ok(statuses == {"needs_review": len(table)}), "error", f"{name} output statuses={dict(statuses)}", str(path))

    persona_weight = sum(float(row.get("prototype_weight", "0") or 0) for row in data["personas"])
    add(rows, ok(abs(persona_weight - 1.0) < 0.0001), "error", f"persona prototype weights sum={persona_weight}", str(FILES["personas"][0]))

    formula_weight = sum(float(row.get("prototype_weight", "0") or 0) for row in data["formula"])
    add(rows, ok(abs(formula_weight - 0.90) < 0.0001), "error", f"formula prototype weights include risk penalty and sum={formula_weight}", str(FILES["formula"][0]))

    score_boundaries = Counter(row.get("score_use_boundary", "") for row in data["scores"])
    add(
        rows,
        ok(score_boundaries == {"ranking_method_draft_not_final_site_selection": len(data["scores"])}),
        "error",
        f"score use boundaries={dict(score_boundaries)}",
        str(FILES["scores"][0]),
    )

    score_text = "\n".join(row.get("blocking_gaps", "") for row in data["scores"])
    for keyword in ["geometry", "visitor_flow", "conversion_rate", "revenue_cost", "operation_authorization", "model_gate"]:
        add(rows, ok(keyword in score_text), "error", f"score blocking gaps include {keyword}", str(FILES["scores"][0]))

    api_key_policy = Counter(row.get("auth_or_key_policy", "") for row in data["api"])
    add(rows, ok("no_real_key_in_collection" in api_key_policy), "error", f"api key policy={dict(api_key_policy)}", str(FILES["api"][0]))

    report_text = REPORT.read_text(encoding="utf-8-sig")
    for keyword in ["P2 方法原型", "不是 P3", "不是 P4", "pending_conversion", "needs_review"]:
        add(rows, ok(keyword in report_text), "error", f"report includes {keyword}", str(REPORT))

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    failures = [row for row in rows if row["status"] != "pass"]
    OUT_MD.write_text(
        "\n".join(
            [
                "# P2 方法原型本地复核报告",
                "",
                f"- 检查项：{len(rows)}",
                f"- 失败项：{len(failures)}",
                "",
                "## 结论",
                "",
                "- P2 方法原型产物结构完整。",
                "- 所有输出保持 `needs_review`。",
                "- 候选评分不是最终选址排序，不替代 P3/P4 真实校准和完整仿真。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"wrote p2 method review rows={len(rows)} to {OUT_CSV}")
    print(f"wrote review report to {OUT_MD}")
    print(f"failures={len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
