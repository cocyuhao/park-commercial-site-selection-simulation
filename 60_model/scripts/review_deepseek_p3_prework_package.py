from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROUTE = ROOT / "70_outputs" / "processed_tables" / "p3_p4_route_decision_deepseek.csv"
DWG = ROOT / "70_outputs" / "processed_tables" / "p3_dwg_conversion_work_order_deepseek.csv"
CALIBRATION = ROOT / "70_outputs" / "processed_tables" / "p3_calibration_data_requirements_deepseek.csv"
MAPPING = ROOT / "70_outputs" / "processed_tables" / "p3_p2_to_calibration_field_mapping_deepseek.csv"
P4 = ROOT / "70_outputs" / "processed_tables" / "p4_parallel_skeleton_backlog_deepseek.csv"
SUMMARY = ROOT / "40_quality_evidence" / "deepseek_p3_prework_package.json"
OUT_CSV = ROOT / "40_quality_evidence" / "deepseek_p3_prework_package_review.csv"
OUT_MD = ROOT / "40_quality_evidence" / "deepseek_p3_prework_package_review.md"

FIELDS = ["check_id", "status", "severity", "finding", "evidence"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def add(rows: list[dict[str, str]], condition: bool, severity: str, finding: str, evidence: Path) -> None:
    rows.append(
        {
            "check_id": f"P3-PREWORK-REVIEW-{len(rows) + 1:03d}",
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
    add(rows, statuses == {"needs_review": len(table)}, "error", f"{name} output statuses={dict(statuses)}", path)
    add(rows, executors == {"deepseek": len(table)}, "error", f"{name} executors={dict(executors)}", path)
    add(rows, task_ids == {"LLM-022": len(table)}, "error", f"{name} task ids={dict(task_ids)}", path)


def main() -> None:
    rows: list[dict[str, str]] = []
    route = read_csv(ROUTE)
    dwg = read_csv(DWG)
    calibration = read_csv(CALIBRATION)
    mapping = read_csv(MAPPING)
    p4 = read_csv(P4)
    summary = json.loads(SUMMARY.read_text(encoding="utf-8-sig"))

    add(rows, len(route) == 3, "error", f"route decision rows={len(route)}", ROUTE)
    add(rows, len(dwg) == 8, "error", f"DWG work rows={len(dwg)}", DWG)
    add(rows, len(calibration) == 16, "error", f"calibration rows={len(calibration)}", CALIBRATION)
    add(rows, len(mapping) == 16, "error", f"mapping rows={len(mapping)}", MAPPING)
    add(rows, len(p4) == 12, "error", f"P4 skeleton rows={len(p4)}", P4)

    for name, table, path in [
        ("route", route, ROUTE),
        ("dwg", dwg, DWG),
        ("calibration", calibration, CALIBRATION),
        ("mapping", mapping, MAPPING),
        ("p4", p4, P4),
    ]:
        check_common(rows, name, table, path)

    route_text = "\n".join(" ".join(row.values()) for row in route)
    route_lower = route_text.lower()
    route_has_recommendation = any((row.get("recommendation") or "").strip() for row in route)
    route_has_parallel_prep = "P3" in route_text and "P4" in route_text and any(
        token in route_lower
        for token in [
            "代码骨架",
            "接口占位",
            "code skeleton",
            "api contract",
            "postman",
            "interface stub",
            "parallel",
        ]
    )
    add(rows, route_has_recommendation and route_has_parallel_prep, "error", "route explicitly recommends P3 hard gate with P4 parallel preparation", ROUTE)
    add(rows, any(token in route_text for token in ["完整", "仿真运行", "结论输出", "候选点排序", "full simulation"]), "error", "route names forbidden simulation/conclusion before P3 closure", ROUTE)

    add(rows, all(row.get("current_status") == "pending_conversion" for row in dwg), "error", "all DWG work items remain pending_conversion", DWG)
    dwg_text = "\n".join(" ".join(row.values()) for row in dwg)
    for forbidden in ["coordinates_extracted", "area_calculated", "layer_parsed", "geometry_checked"]:
        add(rows, forbidden not in dwg_text, "error", f"DWG work order has no false precision token: {forbidden}", DWG)

    domains = {row.get("domain", "") for row in calibration}
    required_domains = {"geometry", "visitor_flow", "conversion_rate", "revenue_cost", "operation_authorization", "model_gate"}
    joined_calibration = "\n".join(" ".join(row.values()) for row in calibration).lower()
    domain_aliases = {
        "geometry": ["geometry", "geojson", "dwg", "spatial_access"],
        "visitor_flow": ["visitor_flow", "visitor_behavior", "visitor_count", "persona_mix"],
        "conversion_rate": ["conversion_rate", "consumption", "transaction", "trigger_calibration"],
        "revenue_cost": ["revenue_cost", "rent", "opex", "capex"],
        "operation_authorization": ["operation_authorization", "lease", "regulatory", "policy", "permission"],
        "model_gate": ["model_gate", "p4_release_gate"],
    }
    missing_domains = [domain for domain, aliases in domain_aliases.items() if not any(alias in joined_calibration for alias in aliases)]
    add(rows, not missing_domains, "error", f"calibration domains cover core gates missing={missing_domains}; raw={sorted(domains)}", CALIBRATION)
    required_flags = Counter(row.get("required_before_p4_conclusion", "") for row in calibration)
    add(rows, required_flags.get("yes", 0) >= 12, "error", f"calibration required-before-P4 counts={dict(required_flags)}", CALIBRATION)

    mapping_text = "\n".join(" ".join(row.values()) for row in mapping)
    mapping_alias_groups = [
        ("project nodes", ["p2_project_node_candidates.csv", "p2_nodes", "candidate"]),
        ("personas", ["p2_persona_parameter_prototype.csv", "p2_personas", "persona"]),
        ("formula", ["p2_supply_gap_scoring_formula.csv", "p2_formula", "demand_fit_score"]),
        ("gap register", ["p2_input_gap_register.csv", "p2_gap_register", "gap"]),
    ]
    for label, aliases in mapping_alias_groups:
        add(rows, any(alias.lower() in mapping_text.lower() for alias in aliases), "error", f"mapping references {label}", MAPPING)

    add(rows, all(row.get("can_start_before_p3_closed") == "yes" for row in p4), "error", "P4 backlog only contains parallel preparation tasks", P4)
    p4_text = "\n".join(" ".join(row.values()) for row in p4)
    add(rows, all(row.get("must_not_do_before_p3_closed", "") for row in p4), "error", "P4 backlog has explicit must-not boundary for every item", P4)
    boundary_hits = sum(
        1
        for token in ["结论", "排序", "收益", "坐标", "面积", "完整仿真", "真实数据", "真实参数", "calibrated", "final", "ranking", "forecast"]
        if token.lower() in p4_text.lower()
    )
    add(rows, boundary_hits >= 4, "error", f"P4 backlog boundary vocabulary hits={boundary_hits}", P4)

    add(rows, summary.get("output_status") == "needs_review", "error", f"summary output_status={summary.get('output_status')}", SUMMARY)
    add(rows, summary.get("executor") == "deepseek", "error", f"summary executor={summary.get('executor')}", SUMMARY)
    add(rows, summary.get("llm_task_id") == "LLM-022", "error", f"summary task={summary.get('llm_task_id')}", SUMMARY)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    failures = [row for row in rows if row["status"] != "pass"]
    OUT_MD.write_text(
        "\n".join(
            [
                "# DeepSeek P3前置工作包复核",
                "",
                f"- 检查项：{len(rows)}",
                f"- 失败项：{len(failures)}",
                "",
                "## 结论",
                "",
                "- P3/P4路线、DWG转换工作单、校准数据需求、P2到P3映射、P4并行骨架清单均已通过本地结构复核。",
                "- 当前仍是needs_review前置包，不是P4完整仿真结论。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote p3 prework review rows={len(rows)} to {OUT_CSV}")
    print(f"wrote review report to {OUT_MD}")
    print(f"failures={len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
