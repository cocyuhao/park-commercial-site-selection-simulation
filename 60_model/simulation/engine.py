from __future__ import annotations

import random
from collections import defaultdict
from typing import Any

from validators import blocked_gate_warnings, validate_result_rows, validate_simulation_request


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
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in poi_candidates:
        categories = [item.strip() for item in str(row.get("standard_categories", "")).split(";") if item.strip()]
        if not categories:
            categories = ["unknown"]
        for category in categories:
            groups[(str(row.get("park_id", "")), category)].append(row)

    rng = random.Random(seed)
    results: list[dict[str, Any]] = []
    sample_size = max(1, min(iterations, 20))
    for (park_id, category), rows in sorted(groups.items()):
        sampled = [rng.choice(rows).get("candidate_id", "") for _ in range(sample_size)]
        missing_business_fields = [
            row
            for row in rows
            if not row.get("opentime_today") or not row.get("tel") or row.get("cost_yuan") is None
        ]
        inside_count = sum(1 for row in rows if row.get("boundary_filter_status") == "inside_osm_polygon")
        warnings = list(gate_warnings)
        if inside_count < len(rows):
            warnings.append("存在 OSM polygon 外候选，不能直接当园内供给")
        if missing_business_fields:
            warnings.append("存在经营字段缺失，需高德 detail 或现场补齐")
        results.append(
            {
                "park_id": park_id,
                "category": category,
                "candidate_count": len(rows),
                "inside_osm_polygon_count": inside_count,
                "missing_business_field_count": len(missing_business_fields),
                "blocked_gate_count": blocked_gate_count,
                "sampled_candidate_ids": sampled,
                "warnings": warnings,
            }
        )
    result_issues = validate_result_rows(results)
    if result_issues:
        raise ValueError("; ".join(result_issues))
    return results
