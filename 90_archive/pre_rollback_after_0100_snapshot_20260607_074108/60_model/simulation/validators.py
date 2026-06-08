from __future__ import annotations

from typing import Any


def validate_simulation_request(iterations: int, seed: int) -> list[str]:
    issues: list[str] = []
    if iterations < 1:
        issues.append("iterations must be greater than 0")
    if iterations > 10000:
        issues.append("iterations is capped at 10000 for the local dry-run API")
    if seed < 0:
        issues.append("seed must be a non-negative integer")
    return issues


def blocked_gate_warnings(gates: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    for gate in gates:
        if gate.get("required_before_p4_conclusion") == "yes" and gate.get("current_gate_status") not in {"closed", "passed"}:
            warnings.append(f"{gate.get('gate_id')}: {gate.get('calibration_domain')} not closed")
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
        "why_blocked",
        "missing_required_fields",
        "next_data_needed",
        "feature_scene_count",
        "matched_feature_scene_count",
        "feature_scene_context",
        "scenario_pressure",
        "accuracy_context",
        "calibration_constraints",
    }
    for index, row in enumerate(rows, start=1):
        missing = [key for key in required if key not in row]
        if missing:
            issues.append(f"result row {index} missing fields: {', '.join(missing)}")
        if "roi" in row:
            issues.append("current dry-run must not output ROI")
        if row.get("output_status") not in {None, "needs_review"}:
            issues.append(f"result row {index} output_status must stay needs_review")
        if not isinstance(row.get("feature_scene_context", []), list):
            issues.append(f"result row {index} feature_scene_context must be a list")
        if not isinstance(row.get("scenario_pressure", {}), dict):
            issues.append(f"result row {index} scenario_pressure must be a dict")
        if not isinstance(row.get("accuracy_context", {}), dict):
            issues.append(f"result row {index} accuracy_context must be a dict")
        if not isinstance(row.get("calibration_constraints", []), list):
            issues.append(f"result row {index} calibration_constraints must be a list")
    return issues
