from __future__ import annotations

import random
from collections import defaultdict
from typing import Any

from validators import blocked_gate_warnings, validate_result_rows, validate_simulation_request


BUSINESS_FIELD_LABELS = {
    "cost_yuan": "人均消费/成本字段",
    "opentime_today": "营业时间",
    "tel": "联系电话",
}


def split_categories(value: Any) -> list[str]:
    categories = [item.strip() for item in str(value or "").split(";") if item.strip()]
    return categories or ["unknown"]


def missing_business_fields(row: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if row.get("cost_yuan") is None or str(row.get("cost_yuan", "")).strip() == "":
        missing.append("cost_yuan")
    if not str(row.get("opentime_today", "")).strip():
        missing.append("opentime_today")
    if not str(row.get("tel", "")).strip():
        missing.append("tel")
    return missing


def source_hint_for(rows: list[dict[str, Any]]) -> str:
    source_paths = sorted({str(row.get("source_path") or "") for row in rows if row.get("source_path")})
    if source_paths:
        return "; ".join(source_paths[:3])
    statuses = sorted({str(row.get("supply_use_status") or "") for row in rows if row.get("supply_use_status")})
    return "; ".join(statuses[:3]) or "poi_candidates_import"


def next_data_needed(
    missing_fields: set[str],
    inside_count: int,
    total_count: int,
    blocked_gate_count: int,
) -> list[str]:
    needs: list[str] = []
    if blocked_gate_count:
        needs.append("补齐 P3 gate: geometry / visitor_flow / conversion_rate / revenue_cost / operation_authorization / model_gate")
    if inside_count < total_count:
        needs.append("用可信边界或现场资料确认候选是否在园内")
    for field in sorted(missing_fields):
        needs.append(f"补齐经营字段: {BUSINESS_FIELD_LABELS.get(field, field)}")
    if not needs:
        needs.append("人工复核来源、授权与现场可达性后再进入下一步模型")
    return needs


def run_structural_simulation(
    poi_candidates: list[dict[str, Any]],
    calibration_gates: list[dict[str, Any]],
    seed: int,
    iterations: int,
) -> list[dict[str, Any]]:
    issues = validate_simulation_request(iterations, seed)
    if issues:
        raise ValueError("; ".join(issues))

    gate_warnings = blocked_gate_warnings(calibration_gates)
    blocked_gate_count = len(gate_warnings)
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in poi_candidates:
        boundary_status = str(row.get("boundary_filter_status") or "boundary_unknown")
        for category in split_categories(row.get("standard_categories")):
            groups[(str(row.get("park_id", "")), category, boundary_status)].append(row)

    rng = random.Random(seed)
    results: list[dict[str, Any]] = []
    sample_size = max(1, min(iterations, 20))
    for (park_id, category, boundary_status), rows in sorted(groups.items()):
        sampled = [rng.choice(rows).get("candidate_id", "") for _ in range(sample_size)]
        missing_by_row = [missing_business_fields(row) for row in rows]
        missing_field_names = {field for fields in missing_by_row for field in fields}
        missing_row_count = sum(1 for fields in missing_by_row if fields)
        inside_count = sum(1 for row in rows if row.get("boundary_filter_status") == "inside_osm_polygon")
        why_blocked = list(gate_warnings)
        warnings = list(gate_warnings)
        if inside_count < len(rows):
            msg = "candidate group includes records outside or not confirmed by OSM/public boundary"
            why_blocked.append(msg)
            warnings.append(msg)
        if missing_field_names:
            msg = "candidate group has missing business fields"
            why_blocked.append(msg)
            warnings.append(msg)
        results.append(
            {
                "park_id": park_id,
                "category": category,
                "group_context": f"{park_id} / {category} / {boundary_status}",
                "boundary_filter_status": boundary_status,
                "source_hint": source_hint_for(rows),
                "candidate_count": len(rows),
                "inside_osm_polygon_count": inside_count,
                "missing_business_field_count": missing_row_count,
                "blocked_gate_count": blocked_gate_count,
                "why_blocked": why_blocked,
                "missing_required_fields": sorted(missing_field_names),
                "next_data_needed": next_data_needed(missing_field_names, inside_count, len(rows), blocked_gate_count),
                "sampled_candidate_ids": sampled,
                "warnings": warnings,
                "output_status": "needs_review",
                "not_final": True,
                "status_label": "待复核 / 非最终",
            }
        )
    result_issues = validate_result_rows(results)
    if result_issues:
        raise ValueError("; ".join(result_issues))
    return results
