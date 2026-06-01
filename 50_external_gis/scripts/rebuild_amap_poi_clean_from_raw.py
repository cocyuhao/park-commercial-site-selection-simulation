from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FETCH_LOG = ROOT / "50_external_gis" / "amap_poi" / "amap_fetch_log.csv"
QUERY_PLAN = ROOT / "50_external_gis" / "amap_poi" / "amap_poi_query_plan.csv"
CLEAN_OUTPUT = ROOT / "50_external_gis" / "amap_poi" / "amap_poi_clean.csv"
SUPPLY_OUTPUT = ROOT / "70_outputs" / "processed_tables" / "poi_supply_base_amap.csv"


CLEAN_FIELDS = [
    "run_id",
    "fetched_at",
    "query_id",
    "park_id",
    "park_name",
    "commercial_category",
    "amap_keyword",
    "radius_m",
    "amap_poi_id",
    "poi_name",
    "amap_type",
    "amap_typecode",
    "address",
    "business_area",
    "longitude",
    "latitude",
    "distance_m",
    "rating",
    "cost_yuan",
    "opentime_today",
    "opentime_week",
    "tel",
    "source_kind",
    "validation_status",
    "confidence",
    "notes",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CLEAN_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def extract_pois(payload: dict) -> list[dict]:
    pois = payload.get("pois") or []
    if isinstance(pois, list):
        return [poi for poi in pois if isinstance(poi, dict)]
    if isinstance(pois, dict):
        nested = pois.get("poi") or pois.get("pois") or []
        if isinstance(nested, list):
            return [poi for poi in nested if isinstance(poi, dict)]
        if isinstance(nested, dict):
            return [nested]
        if all(key in pois for key in ("name", "id")):
            return [pois]
    return []


def business_value(poi: dict, *keys: str) -> str:
    for key in keys:
        value = poi.get(key)
        if isinstance(value, str):
            return value
    business = poi.get("business")
    if isinstance(business, dict):
        for key in keys:
            value = business.get(key)
            if isinstance(value, str):
                return value
    return ""


def location_parts(poi: dict) -> tuple[str, str]:
    location = str(poi.get("location") or "")
    if "," not in location:
        return "", ""
    longitude, latitude = location.split(",", 1)
    return longitude.strip(), latitude.strip()


def main() -> None:
    logs = read_csv(FETCH_LOG)
    plan_by_query_id = {row["query_id"]: row for row in read_csv(QUERY_PLAN)}
    rows: list[dict[str, str]] = []

    for log in logs:
        if log.get("api_endpoint") != "v5/place/around":
            continue
        if log.get("status") != "1" or not log.get("raw_file"):
            continue
        plan = plan_by_query_id.get(log["query_id"])
        if not plan:
            continue
        raw_path = ROOT / log["raw_file"]
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        for poi in extract_pois(payload):
            longitude, latitude = location_parts(poi)
            rows.append(
                {
                    "run_id": log["run_id"],
                    "fetched_at": log["fetched_at"],
                    "query_id": log["query_id"],
                    "park_id": plan["park_id"],
                    "park_name": plan["park_name"],
                    "commercial_category": plan["commercial_category"],
                    "amap_keyword": plan["amap_keywords"],
                    "radius_m": plan["radius_m"],
                    "amap_poi_id": str(poi.get("id", "")),
                    "poi_name": str(poi.get("name", "")),
                    "amap_type": str(poi.get("type", "")),
                    "amap_typecode": str(poi.get("typecode", "")),
                    "address": str(poi.get("address", "")),
                    "business_area": business_value(poi, "business_area", "businessarea"),
                    "longitude": longitude,
                    "latitude": latitude,
                    "distance_m": str(poi.get("distance", "")),
                    "rating": business_value(poi, "rating"),
                    "cost_yuan": business_value(poi, "cost"),
                    "opentime_today": business_value(poi, "opentime_today"),
                    "opentime_week": business_value(poi, "opentime_week"),
                    "tel": business_value(poi, "tel"),
                    "source_kind": "amap_poi_around",
                    "validation_status": "api_returned_needs_boundary_filter",
                    "confidence": "medium",
                    "notes": "Amap POI around result; boundary filtering and field validation still required.",
                }
            )

    write_csv(CLEAN_OUTPUT, rows)
    write_csv(SUPPLY_OUTPUT, rows)
    print(f"rebuilt {len(rows)} POI rows from raw Amap responses")
    print(f"wrote {CLEAN_OUTPUT}")
    print(f"wrote {SUPPLY_OUTPUT}")


if __name__ == "__main__":
    main()
