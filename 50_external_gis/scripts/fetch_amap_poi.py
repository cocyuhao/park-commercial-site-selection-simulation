from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[2]
QUERY_PLAN = ROOT / "50_external_gis" / "amap_poi" / "amap_poi_query_plan.csv"
RAW_DIR = ROOT / "50_external_gis" / "amap_poi" / "raw"
FETCH_LOG = ROOT / "50_external_gis" / "amap_poi" / "amap_fetch_log.csv"
CLEAN_OUTPUT = ROOT / "50_external_gis" / "amap_poi" / "amap_poi_clean.csv"
SUPPLY_OUTPUT = ROOT / "70_outputs" / "processed_tables" / "poi_supply_base_amap.csv"

AMAP_TEXT_ENDPOINT = "https://restapi.amap.com/v5/place/text"
AMAP_AROUND_ENDPOINT = "https://restapi.amap.com/v5/place/around"

LOG_FIELDS = [
    "run_id",
    "fetched_at",
    "query_id",
    "park_id",
    "api_endpoint",
    "params_summary",
    "status",
    "info",
    "result_count",
    "raw_file",
]

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


def load_query_plan(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sanitize_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    return value.strip("_") or "item"


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def params_summary(params: dict[str, str]) -> str:
    safe = {key: value for key, value in params.items() if key != "key"}
    return json.dumps(safe, ensure_ascii=False, sort_keys=True)


def fetch_json(
    endpoint: str,
    params: dict[str, str],
    timeout: int = 20,
    retries: int = 3,
    backoff_seconds: float = 1.0,
) -> dict:
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(
                endpoint,
                params=params,
                timeout=timeout,
                headers={"User-Agent": "park-simulation-poi-audit/1.0"},
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(backoff_seconds * attempt)
    raise RuntimeError(f"request failed after {retries} attempts: {type(last_exc).__name__}") from None


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists()
    with path.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def get_location(poi: dict) -> tuple[str, str]:
    location = str(poi.get("location") or "")
    if "," not in location:
        return "", ""
    lon, lat = location.split(",", 1)
    return lon.strip(), lat.strip()


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


def get_business_area(poi: dict) -> str:
    return get_business_value(poi, "business_area", "businessarea")


def get_business_value(poi: dict, *keys: str) -> str:
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


def request_center(
    *,
    key: str,
    run_id: str,
    row: dict[str, str],
    fetched_at: str,
) -> tuple[str, list[dict[str, str]]]:
    params = {
        "key": key,
        "keywords": row["center_address"],
        "region": row["city"],
        "city_limit": "true",
        "show_fields": "business",
        "page_size": "1",
        "page_num": "1",
    }
    payload = fetch_json(AMAP_TEXT_ENDPOINT, params)
    raw_file = RAW_DIR / f"{run_id}_center_{sanitize_name(row['park_id'])}.json"
    write_json(raw_file, payload)

    pois = extract_pois(payload)
    location = ""
    if pois:
        location = str(pois[0].get("location") or "")

    log = {
        "run_id": run_id,
        "fetched_at": fetched_at,
        "query_id": f"center_{row['park_id']}",
        "park_id": row["park_id"],
        "api_endpoint": "v5/place/text",
        "params_summary": params_summary(params),
        "status": str(payload.get("status", "")),
        "info": str(payload.get("info", "")),
        "result_count": str(len(pois)),
        "raw_file": str(raw_file.relative_to(ROOT)),
    }
    return location, [log]


def request_around(
    *,
    key: str,
    run_id: str,
    row: dict[str, str],
    location: str,
    fetched_at: str,
    page_size: int,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    params = {
        "key": key,
        "keywords": row["amap_keywords"],
        "location": location,
        "radius": row["radius_m"],
        "region": row["city"],
        "show_fields": "business",
        "page_size": str(page_size),
        "page_num": "1",
    }
    if row.get("amap_types"):
        params["types"] = row["amap_types"]

    payload = fetch_json(AMAP_AROUND_ENDPOINT, params)
    raw_file = RAW_DIR / f"{run_id}_{sanitize_name(row['query_id'])}.json"
    write_json(raw_file, payload)

    pois = extract_pois(payload)
    log = {
        "run_id": run_id,
        "fetched_at": fetched_at,
        "query_id": row["query_id"],
        "park_id": row["park_id"],
        "api_endpoint": "v5/place/around",
        "params_summary": params_summary(params),
        "status": str(payload.get("status", "")),
        "info": str(payload.get("info", "")),
        "result_count": str(len(pois)),
        "raw_file": str(raw_file.relative_to(ROOT)),
    }

    clean_rows: list[dict[str, str]] = []
    for poi in pois:
        lon, lat = get_location(poi)
        clean_rows.append(
            {
                "run_id": run_id,
                "fetched_at": fetched_at,
                "query_id": row["query_id"],
                "park_id": row["park_id"],
                "park_name": row["park_name"],
                "commercial_category": row["commercial_category"],
                "amap_keyword": row["amap_keywords"],
                "radius_m": row["radius_m"],
                "amap_poi_id": str(poi.get("id", "")),
                "poi_name": str(poi.get("name", "")),
                "amap_type": str(poi.get("type", "")),
                "amap_typecode": str(poi.get("typecode", "")),
                "address": str(poi.get("address", "")),
                "business_area": get_business_area(poi),
                "longitude": lon,
                "latitude": lat,
                "distance_m": str(poi.get("distance", "")),
                "rating": get_business_value(poi, "rating"),
                "cost_yuan": get_business_value(poi, "cost"),
                "opentime_today": get_business_value(poi, "opentime_today"),
                "opentime_week": get_business_value(poi, "opentime_week"),
                "tel": get_business_value(poi, "tel"),
                "source_kind": "amap_poi_around",
                "validation_status": "api_returned_needs_boundary_filter",
                "confidence": "medium",
                "notes": "Amap POI around result; boundary filtering and field validation still required.",
            }
        )

    return clean_rows, [log]


def run_fetch(plan_rows: list[dict[str, str]], page_size: int, sleep_seconds: float) -> None:
    key = os.environ.get("AMAP_WEB_SERVICE_KEY")
    if not key:
        raise SystemExit("AMAP_WEB_SERVICE_KEY is not set; run with --dry-run or set it in the environment.")

    run_id = datetime.now().strftime("%Y%m%dT%H%M%S")
    fetched_at = now_utc()
    center_cache: dict[str, str] = {}
    logs: list[dict[str, str]] = []
    clean_rows: list[dict[str, str]] = []

    for row in plan_rows:
        if row["park_id"] not in center_cache:
            try:
                location, center_logs = request_center(key=key, run_id=run_id, row=row, fetched_at=fetched_at)
                center_cache[row["park_id"]] = location
                logs.extend(center_logs)
            except Exception as exc:
                center_cache[row["park_id"]] = ""
                logs.append(
                    {
                        "run_id": run_id,
                        "fetched_at": fetched_at,
                        "query_id": f"center_{row['park_id']}",
                        "park_id": row["park_id"],
                        "api_endpoint": "v5/place/text",
                        "params_summary": json.dumps(
                            {
                                "keywords": row["center_address"],
                                "region": row["city"],
                                "city_limit": "true",
                                "show_fields": "business",
                                "page_size": "1",
                                "page_num": "1",
                            },
                            ensure_ascii=False,
                            sort_keys=True,
                        ),
                        "status": "error",
                        "info": str(exc),
                        "result_count": "0",
                        "raw_file": "",
                    }
                )
            time.sleep(sleep_seconds)

        location = center_cache[row["park_id"]]
        if not location:
            logs.append(
                {
                    "run_id": run_id,
                    "fetched_at": fetched_at,
                    "query_id": row["query_id"],
                    "park_id": row["park_id"],
                    "api_endpoint": "v5/place/around",
                    "params_summary": json.dumps({"reason": "missing center location"}, ensure_ascii=False),
                    "status": "skipped",
                    "info": "missing center location",
                    "result_count": "0",
                    "raw_file": "",
                }
            )
            continue

        try:
            rows, around_logs = request_around(
                key=key,
                run_id=run_id,
                row=row,
                location=location,
                fetched_at=fetched_at,
                page_size=page_size,
            )
            clean_rows.extend(rows)
            logs.extend(around_logs)
        except Exception as exc:
            logs.append(
                {
                    "run_id": run_id,
                    "fetched_at": fetched_at,
                    "query_id": row["query_id"],
                    "park_id": row["park_id"],
                    "api_endpoint": "v5/place/around",
                    "params_summary": json.dumps(
                        {
                            "keywords": row["amap_keywords"],
                            "location": location,
                            "radius": row["radius_m"],
                            "region": row["city"],
                            "show_fields": "business",
                            "page_size": str(page_size),
                            "page_num": "1",
                            "types": row.get("amap_types", ""),
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                    "status": "error",
                    "info": str(exc),
                    "result_count": "0",
                    "raw_file": "",
                }
            )
        time.sleep(sleep_seconds)

    append_csv(FETCH_LOG, LOG_FIELDS, logs)
    write_csv(CLEAN_OUTPUT, CLEAN_FIELDS, clean_rows)
    write_csv(SUPPLY_OUTPUT, CLEAN_FIELDS, clean_rows)
    print(f"wrote {len(clean_rows)} POI rows to {CLEAN_OUTPUT}")
    print(f"wrote {len(logs)} log rows to {FETCH_LOG}")


def dry_run(plan_rows: list[dict[str, str]]) -> None:
    parks = sorted({row["park_id"] for row in plan_rows})
    categories = sorted({row["commercial_category"] for row in plan_rows})
    print(f"query_plan_rows={len(plan_rows)}")
    print(f"parks={len(parks)}")
    print(f"categories={len(categories)}")
    print("dry_run_only=true")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query-plan", type=Path, default=QUERY_PLAN)
    parser.add_argument("--page-size", type=int, default=25)
    parser.add_argument("--sleep-seconds", type=float, default=0.2)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    plan_rows = load_query_plan(args.query_plan)
    if args.dry_run:
        dry_run(plan_rows)
        return

    try:
        run_fetch(plan_rows, args.page_size, args.sleep_seconds)
    except Exception as exc:
        print(f"amap fetch failed: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
