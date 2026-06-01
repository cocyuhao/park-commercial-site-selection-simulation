from __future__ import annotations

from typing import Any


def validate_simulation_request(iterations: int, seed: int) -> list[str]:
    issues: list[str] = []
    if iterations < 1:
        issues.append("iterations 必须大于 0")
    if iterations > 10000:
        issues.append("iterations 当前限制为 10000，避免本地接口被长任务占住")
    if seed < 0:
        issues.append("seed 必须为非负整数")
    return issues


def blocked_gate_warnings(gates: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    for gate in gates:
        if gate.get("required_before_p4_conclusion") == "yes" and gate.get("current_gate_status") not in {"closed", "passed"}:
            warnings.append(f"{gate.get('gate_id')}: {gate.get('calibration_domain')} 未闭合")
    return warnings


def validate_result_rows(rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    required = {
        "park_id",
        "category",
        "candidate_count",
        "inside_osm_polygon_count",
        "missing_business_field_count",
        "blocked_gate_count",
    }
    for index, row in enumerate(rows, start=1):
        missing = [key for key in required if key not in row]
        if missing:
            issues.append(f"result row {index} 缺字段: {', '.join(missing)}")
        if "roi" in row:
            issues.append("当前阶段禁止输出 ROI")
    return issues
