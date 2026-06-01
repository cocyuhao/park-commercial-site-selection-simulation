from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
IN_PARK_REVIEW = ROOT / "70_outputs" / "processed_tables" / "poi_supply_in_park_candidate_review.csv"
BOUNDARIES = ROOT / "50_external_gis" / "boundaries" / "osm_park_boundaries.geojson"
ROUTE_RESULTS = ROOT / "50_external_gis" / "amap_routes" / "amap_p0_route_results.csv"
OUT_CSV = ROOT / "70_outputs" / "processed_tables" / "poi_supply_p0_followup_worklist.csv"
REPORT = ROOT / "40_quality_evidence" / "p0_in_park_followup_worklist_report.md"


FIELDS = [
    "work_item_id",
    "review_id",
    "candidate_id",
    "park_id",
    "park_name",
    "poi_name",
    "standard_categories",
    "amap_poi_id",
    "address",
    "longitude",
    "latitude",
    "wgs84_longitude",
    "wgs84_latitude",
    "min_distance_m",
    "approx_distance_to_osm_boundary_m",
    "field_review_priority",
    "source_strength_status",
    "business_info_status",
    "opening_hours_status",
    "contact_status",
    "spend_status",
    "pdf_seed_match_status",
    "pdf_seed_poi_names",
    "missing_business_fields",
    "route_access_status",
    "operation_authorization_status",
    "amap_route_api_status",
    "amap_detail_api_status",
    "manual_fieldwork_status",
    "blocking_gaps",
    "next_action",
    "can_enter_p2_supply",
    "notes",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_csv_if_exists(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return read_csv(path)


def write_csv(rows: list[dict[str, str]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def to_float(value: str) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    radius_m = 6_371_000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_m * c


def point_to_segment_distance_m(
    lon: float, lat: float, lon1: float, lat1: float, lon2: float, lat2: float
) -> float:
    mean_lat = math.radians((lat + lat1 + lat2) / 3)
    meters_per_deg_lat = 111_320.0
    meters_per_deg_lon = 111_320.0 * math.cos(mean_lat)
    px, py = lon * meters_per_deg_lon, lat * meters_per_deg_lat
    ax, ay = lon1 * meters_per_deg_lon, lat1 * meters_per_deg_lat
    bx, by = lon2 * meters_per_deg_lon, lat2 * meters_per_deg_lat
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy)


def iter_rings(geometry: dict) -> list[list[list[float]]]:
    geo_type = geometry.get("type")
    coords = geometry.get("coordinates") or []
    if geo_type == "Polygon":
        return coords
    if geo_type == "MultiPolygon":
        rings: list[list[list[float]]] = []
        for polygon in coords:
            rings.extend(polygon)
        return rings
    return []


def load_boundaries() -> dict[str, dict]:
    data = json.loads(BOUNDARIES.read_text(encoding="utf-8-sig"))
    return {
        feature.get("properties", {}).get("park_id", ""): feature.get("geometry", {})
        for feature in data.get("features", [])
        if feature.get("properties", {}).get("park_id")
    }


def distance_to_boundary_m(row: dict[str, str], boundaries: dict[str, dict]) -> str:
    lon = to_float(row.get("wgs84_longitude", ""))
    lat = to_float(row.get("wgs84_latitude", ""))
    geometry = boundaries.get(row.get("park_id", ""))
    if lon is None or lat is None or not geometry:
        return ""
    distances: list[float] = []
    for ring in iter_rings(geometry):
        for idx in range(1, len(ring)):
            lon1, lat1 = ring[idx - 1][0], ring[idx - 1][1]
            lon2, lat2 = ring[idx][0], ring[idx][1]
            distances.append(point_to_segment_distance_m(lon, lat, lon1, lat1, lon2, lat2))
    if not distances:
        return ""
    return f"{min(distances):.1f}"


def missing_fields(row: dict[str, str]) -> list[str]:
    missing = []
    if row.get("opening_hours_status") != "has_opening_hours":
        missing.append("opening_hours")
    if row.get("contact_status") != "has_contact":
        missing.append("contact")
    if row.get("spend_status") != "has_cost_yuan":
        missing.append("cost_yuan")
    return missing


def blocking_gaps(row: dict[str, str], missing: list[str]) -> list[str]:
    gaps = list(missing)
    if row.get("route_access_status") == "needs_entrance_or_route_api_verification":
        gaps.append("real_entrance_or_node_route_access")
    if row.get("operation_authorization_status") == "needs_operator_or_field_confirmation":
        gaps.append("operation_authorization")
    return gaps


def next_action(row: dict[str, str], missing: list[str]) -> str:
    actions = []
    if missing:
        actions.append("补齐高德 detail 或现场经营字段：" + ",".join(missing))
    if row.get("pdf_seed_match_status") == "matched_pdf_seed":
        actions.append("回查 PDF 种子名称并确认是否同一商户")
    actions.append("补入口/节点步行路线或现场可达性")
    actions.append("确认是否属于园方可运营/可授权资产")
    return "；".join(actions)


def route_status_for(row: dict[str, str], route_by_work_item: dict[str, dict[str, str]]) -> str:
    route = route_by_work_item.get(row.get("review_id", ""))
    if route and route.get("route_access_status") == "amap_center_proxy_route_returned_needs_entrance_validation":
        return "center_proxy_route_returned_needs_real_entrance_validation"
    return "blocked_until_AMAP_WEB_SERVICE_KEY_available"


def build_rows(review_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    boundaries = load_boundaries()
    route_by_review = {
        row.get("review_id", ""): row
        for row in read_csv_if_exists(ROUTE_RESULTS)
        if row.get("review_id")
    }
    p0_rows = [row for row in review_rows if row.get("field_review_priority", "").startswith("P0")]
    output_rows = []
    for row in p0_rows:
        missing = missing_fields(row)
        gaps = blocking_gaps(row, missing)
        route_api_status = route_status_for(row, route_by_review)
        output_rows.append(
            {
                "work_item_id": f"P0-INPARK-{len(output_rows) + 1:03d}",
                "review_id": row.get("review_id", ""),
                "candidate_id": row.get("candidate_id", ""),
                "park_id": row.get("park_id", ""),
                "park_name": row.get("park_name", ""),
                "poi_name": row.get("poi_name", ""),
                "standard_categories": row.get("standard_categories", ""),
                "amap_poi_id": row.get("amap_poi_id", ""),
                "address": row.get("address", ""),
                "longitude": row.get("longitude", ""),
                "latitude": row.get("latitude", ""),
                "wgs84_longitude": row.get("wgs84_longitude", ""),
                "wgs84_latitude": row.get("wgs84_latitude", ""),
                "min_distance_m": row.get("min_distance_m", ""),
                "approx_distance_to_osm_boundary_m": distance_to_boundary_m(row, boundaries),
                "field_review_priority": row.get("field_review_priority", ""),
                "source_strength_status": row.get("source_strength_status", ""),
                "business_info_status": row.get("business_info_status", ""),
                "opening_hours_status": row.get("opening_hours_status", ""),
                "contact_status": row.get("contact_status", ""),
                "spend_status": row.get("spend_status", ""),
                "pdf_seed_match_status": row.get("pdf_seed_match_status", ""),
                "pdf_seed_poi_names": row.get("pdf_seed_poi_names", ""),
                "missing_business_fields": ";".join(missing),
                "route_access_status": row.get("route_access_status", ""),
                "operation_authorization_status": row.get("operation_authorization_status", ""),
                "amap_route_api_status": route_api_status,
                "amap_detail_api_status": "blocked_until_AMAP_WEB_SERVICE_KEY_available" if missing else "not_required_for_current_business_fields",
                "manual_fieldwork_status": "not_started",
                "blocking_gaps": ";".join(gaps),
                "next_action": next_action(row, missing),
                "can_enter_p2_supply": "no",
                "notes": "P0 园内候选复核工作单；补齐阻塞缺口前不得进入 P2 供给数量。",
            }
        )
    return output_rows


def write_report(rows: list[dict[str, str]]) -> None:
    by_park = Counter(row["park_name"] for row in rows)
    by_priority = Counter(row["field_review_priority"] for row in rows)
    by_source = Counter(row["source_strength_status"] for row in rows)
    missing_counter: Counter[str] = Counter()
    for row in rows:
        for item in row["missing_business_fields"].split(";"):
            if item:
                missing_counter[item] += 1
    route_blocked = sum(1 for row in rows if row["amap_route_api_status"].startswith("blocked"))
    route_proxy_returned = sum(1 for row in rows if row["amap_route_api_status"].startswith("center_proxy_route_returned"))
    detail_blocked = sum(1 for row in rows if row["amap_detail_api_status"].startswith("blocked"))

    lines = [
        "# P0 园内候选复核工作单报告",
        "",
        "## 结论",
        "",
        f"- P0 工作项：{len(rows)} 条。",
        f"- 按公园统计：{dict(sorted(by_park.items()))}",
        f"- 复核优先级：{dict(sorted(by_priority.items()))}",
        f"- 来源强度：{dict(sorted(by_source.items()))}",
        f"- 缺失经营字段：{dict(sorted(missing_counter.items())) if missing_counter else '无'}",
        f"- 高德中心点代理路径已返回：{route_proxy_returned}/{len(rows)}。",
        f"- 高德路径 API 阻塞项：{route_blocked}/{len(rows)}。",
        f"- 高德 detail/API 或现场补字段项：{detail_blocked}/{len(rows)}。",
        "",
        "## 口径限制",
        "",
        "- 本工作单只用于 P1 复核排队，不是最终园内供给清单。",
        "- 高德路径如已返回，也只是公园中心点代理路线；真实入口/节点路线仍未闭合。",
        "- 当前环境未确认 `AMAP_WEB_SERVICE_KEY` 时，detail 补字段仍需等待后续接口或现场核验。",
        "- `approx_distance_to_osm_boundary_m` 是基于 OSM polygon 的近似几何距离，不是步行距离。",
        "- 所有工作项 `can_enter_p2_supply` 均为 `no`，直到路径可达、实际营业和运营授权闭合。",
        "",
        "## 输出文件",
        "",
        "- `70_outputs/processed_tables/poi_supply_p0_followup_worklist.csv`",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows(read_csv(IN_PARK_REVIEW))
    write_csv(rows)
    write_report(rows)
    print(f"wrote {len(rows)} P0 follow-up worklist rows to {OUT_CSV}")
    print(f"wrote report to {REPORT}")


if __name__ == "__main__":
    main()
