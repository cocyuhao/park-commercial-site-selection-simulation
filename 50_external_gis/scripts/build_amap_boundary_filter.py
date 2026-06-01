from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOUNDARIES = ROOT / "50_external_gis" / "boundaries" / "osm_park_boundaries.geojson"
PRECHECK = ROOT / "70_outputs" / "processed_tables" / "poi_supply_candidates_amap_spatial_precheck.csv"
OUT_CSV = ROOT / "70_outputs" / "processed_tables" / "poi_supply_candidates_amap_boundary_filter.csv"
REPORT = ROOT / "40_quality_evidence" / "amap_boundary_filter_report.md"


EXTRA_FIELDS = [
    "wgs84_longitude",
    "wgs84_latitude",
    "boundary_source",
    "boundary_osm_type",
    "boundary_osm_id",
    "boundary_filter_status",
    "p1_boundary_supply_status",
    "boundary_filter_confidence",
    "boundary_filter_notes",
]


X_PI = math.pi * 3000.0 / 180.0
PI = math.pi
A = 6378245.0
EE = 0.00669342162296594323


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def to_float(value: str) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def out_of_china(lon: float, lat: float) -> bool:
    return lon < 72.004 or lon > 137.8347 or lat < 0.8293 or lat > 55.8271


def transform_lat(lon: float, lat: float) -> float:
    ret = -100.0 + 2.0 * lon + 3.0 * lat + 0.2 * lat * lat + 0.1 * lon * lat + 0.2 * math.sqrt(abs(lon))
    ret += (20.0 * math.sin(6.0 * lon * PI) + 20.0 * math.sin(2.0 * lon * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * PI) + 40.0 * math.sin(lat / 3.0 * PI)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * PI) + 320 * math.sin(lat * PI / 30.0)) * 2.0 / 3.0
    return ret


def transform_lon(lon: float, lat: float) -> float:
    ret = 300.0 + lon + 2.0 * lat + 0.1 * lon * lon + 0.1 * lon * lat + 0.1 * math.sqrt(abs(lon))
    ret += (20.0 * math.sin(6.0 * lon * PI) + 20.0 * math.sin(2.0 * lon * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lon * PI) + 40.0 * math.sin(lon / 3.0 * PI)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lon / 12.0 * PI) + 300.0 * math.sin(lon / 30.0 * PI)) * 2.0 / 3.0
    return ret


def gcj02_to_wgs84(lon: float, lat: float) -> tuple[float, float]:
    if out_of_china(lon, lat):
        return lon, lat
    dlat = transform_lat(lon - 105.0, lat - 35.0)
    dlon = transform_lon(lon - 105.0, lat - 35.0)
    radlat = lat / 180.0 * PI
    magic = math.sin(radlat)
    magic = 1 - EE * magic * magic
    sqrt_magic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((A * (1 - EE)) / (magic * sqrt_magic) * PI)
    dlon = (dlon * 180.0) / (A / sqrt_magic * math.cos(radlat) * PI)
    mg_lat = lat + dlat
    mg_lon = lon + dlon
    return lon * 2 - mg_lon, lat * 2 - mg_lat


def point_in_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    inside = False
    if len(ring) < 3:
        return False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        intersects = ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def point_in_polygon(lon: float, lat: float, polygon: list[list[list[float]]]) -> bool:
    if not polygon:
        return False
    if not point_in_ring(lon, lat, polygon[0]):
        return False
    for hole in polygon[1:]:
        if point_in_ring(lon, lat, hole):
            return False
    return True


def point_in_geometry(lon: float, lat: float, geometry: dict) -> bool:
    geo_type = geometry.get("type")
    coords = geometry.get("coordinates") or []
    if geo_type == "Polygon":
        return point_in_polygon(lon, lat, coords)
    if geo_type == "MultiPolygon":
        return any(point_in_polygon(lon, lat, polygon) for polygon in coords)
    return False


def load_boundaries() -> dict[str, dict]:
    data = json.loads(BOUNDARIES.read_text(encoding="utf-8-sig"))
    boundaries: dict[str, dict] = {}
    for feature in data.get("features", []):
        park_id = feature.get("properties", {}).get("park_id")
        if park_id:
            boundaries[park_id] = feature
    return boundaries


def filter_rows(rows: list[dict[str, str]], boundaries: dict[str, dict]) -> list[dict[str, str]]:
    output_rows: list[dict[str, str]] = []
    for row in rows:
        lon = to_float(row.get("longitude", ""))
        lat = to_float(row.get("latitude", ""))
        feature = boundaries.get(row.get("park_id", ""))
        extra = {
            "wgs84_longitude": "",
            "wgs84_latitude": "",
            "boundary_source": "",
            "boundary_osm_type": "",
            "boundary_osm_id": "",
            "boundary_filter_status": "boundary_missing_or_invalid",
            "p1_boundary_supply_status": "needs_boundary_or_field_verification",
            "boundary_filter_confidence": "low",
            "boundary_filter_notes": "缺少可用边界或坐标。",
        }
        if lon is not None and lat is not None:
            wgs_lon, wgs_lat = gcj02_to_wgs84(lon, lat)
            extra["wgs84_longitude"] = f"{wgs_lon:.8f}"
            extra["wgs84_latitude"] = f"{wgs_lat:.8f}"
            if feature:
                props = feature.get("properties", {})
                inside = point_in_geometry(wgs_lon, wgs_lat, feature.get("geometry", {}))
                extra.update(
                    {
                        "boundary_source": props.get("source", "OpenStreetMap via Nominatim"),
                        "boundary_osm_type": props.get("osm_type", ""),
                        "boundary_osm_id": props.get("osm_id", ""),
                        "boundary_filter_status": "inside_osm_polygon" if inside else "outside_osm_polygon",
                        "p1_boundary_supply_status": "boundary_filtered_in_park_candidate_needs_field_review"
                        if inside
                        else "boundary_filtered_surrounding_supply_candidate",
                        "boundary_filter_confidence": "medium",
                        "boundary_filter_notes": "高德 GCJ-02 坐标已近似转 WGS84 后与 OSM polygon 判断；OSM 非官方红线，仍需现场/运营状态复核。",
                    }
                )
        output_rows.append({**row, **extra})
    return output_rows


def write_report(rows: list[dict[str, str]]) -> None:
    by_boundary = Counter(row["boundary_filter_status"] for row in rows)
    by_supply = Counter(row["p1_boundary_supply_status"] for row in rows)
    by_park = defaultdict(Counter)
    by_category_inside = defaultdict(Counter)
    for row in rows:
        by_park[row["park_name"]][row["boundary_filter_status"]] += 1
        if row["boundary_filter_status"] == "inside_osm_polygon":
            for category in row.get("standard_categories", "").split(";"):
                if category:
                    by_category_inside[row["park_name"]][category] += 1

    lines = [
        "# 高德候选 POI 边界过滤报告",
        "",
        "## 结论",
        "",
        f"- 输入候选：{len(rows)} 条。",
        f"- OSM polygon 边界状态：{dict(sorted(by_boundary.items()))}",
        f"- P1 供给使用状态：{dict(sorted(by_supply.items()))}",
        "",
        "## 按公园统计",
        "",
    ]
    for park_name, counter in sorted(by_park.items()):
        lines.append(f"- {park_name}：{dict(sorted(counter.items()))}")

    lines.extend(["", "## OSM polygon 内候选按业态统计", ""])
    for park_name, counter in sorted(by_category_inside.items()):
        lines.append(f"- {park_name}：{dict(sorted(counter.items()))}")
    if not by_category_inside:
        lines.append("- 无。")

    lines.extend(
        [
            "",
            "## 口径限制",
            "",
            "- 高德 POI 坐标默认为 GCJ-02，本脚本近似转换为 WGS84 后与 OSM polygon 做点在面内判断。",
            "- OSM 边界来自公开地图，不是官方规划红线；P1 可用于候选过滤和复核优先级，不作为最终经营结论。",
            "- `inside_osm_polygon` 只表示公开地图 polygon 内候选，仍需现场营业状态、入口/路径可达和运营授权核验。",
            "- `outside_osm_polygon` 可作为周边竞品/外溢供给候选，不应直接计入园内供给。",
            "",
            "## 输出文件",
            "",
            "- `70_outputs/processed_tables/poi_supply_candidates_amap_boundary_filter.csv`",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = read_csv(PRECHECK)
    boundaries = load_boundaries()
    output_rows = filter_rows(rows, boundaries)
    fields = list(rows[0].keys()) + EXTRA_FIELDS if rows else EXTRA_FIELDS
    write_csv(output_rows, fields)
    write_report(output_rows)
    print(f"wrote {len(output_rows)} boundary filter rows to {OUT_CSV}")
    print(f"wrote report to {REPORT}")


if __name__ == "__main__":
    main()
