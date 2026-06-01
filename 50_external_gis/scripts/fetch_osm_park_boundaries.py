from __future__ import annotations

import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "50_external_gis" / "boundaries"
RAW_DIR = OUT_DIR / "osm_raw"
OUT_GEOJSON = OUT_DIR / "osm_park_boundaries.geojson"
OUT_LOG = OUT_DIR / "osm_park_boundary_fetch_log.csv"
REPORT = ROOT / "40_quality_evidence" / "osm_boundary_report.md"


PARK_QUERIES = [
    {
        "park_id": "sample_city_green_heart",
        "park_name": "城市绿心森林公园",
        "query": "北京城市绿心森林公园",
    },
    {
        "park_id": "sample_olympic_forest",
        "park_name": "奥林匹克森林公园",
        "query": "北京奥林匹克森林公园",
    },
]


LOG_FIELDS = [
    "fetched_at_utc",
    "park_id",
    "park_name",
    "query",
    "http_status",
    "result_count",
    "selected_osm_type",
    "selected_osm_id",
    "selected_geojson_type",
    "selected_display_name",
    "raw_file",
    "source_url",
]


def fetch_boundary(query: str) -> tuple[list[dict], str, int]:
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "format": "json",
        "polygon_geojson": "1",
        "limit": "5",
        "q": query,
    }
    headers = {
        "User-Agent": "park-siting-simulation-research/0.1 (P1 boundary evidence; local project)",
    }
    last_exc: Exception | None = None
    for attempt in range(1, 4):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json(), response.url, response.status_code
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < 3:
                time.sleep(1.5 * attempt)
    assert last_exc is not None
    raise last_exc


def select_polygon(results: list[dict]) -> dict | None:
    for item in results:
        geojson = item.get("geojson") or {}
        if geojson.get("type") in {"Polygon", "MultiPolygon"}:
            return item
    return None


def write_outputs(features: list[dict], log_rows: list[dict[str, str]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    feature_collection = {
        "type": "FeatureCollection",
        "name": "osm_park_boundaries",
        "metadata": {
            "source": "OpenStreetMap via Nominatim",
            "license_note": "OpenStreetMap data is available under ODbL; keep attribution when reused.",
            "coordinate_reference_system": "WGS84 lon/lat",
        },
        "features": features,
    }
    OUT_GEOJSON.write_text(json.dumps(feature_collection, ensure_ascii=False, indent=2), encoding="utf-8")

    with OUT_LOG.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        writer.writeheader()
        writer.writerows(log_rows)

    lines = [
        "# OSM 公园边界抓取报告",
        "",
        "## 结论",
        "",
        f"- 已保存边界 feature：{len(features)} 个。",
        f"- 输出 GeoJSON：`{OUT_GEOJSON.relative_to(ROOT).as_posix()}`。",
        f"- 抓取日志：`{OUT_LOG.relative_to(ROOT).as_posix()}`。",
        "",
        "## 边界来源",
        "",
        "- 来源：OpenStreetMap via Nominatim。",
        "- 坐标系：WGS84 lon/lat。",
        "- 许可提示：OpenStreetMap 数据使用 ODbL；后续报告或交付若复用边界，需要保留 OSM attribution。",
        "- 口径限制：OSM 边界不是官方规划红线，P1 阶段只作为公开地图边界核验材料。",
        "",
        "## 明细",
        "",
    ]
    for row in log_rows:
        lines.append(
            f"- {row['park_name']}：results={row['result_count']}，selected={row['selected_osm_type']}/{row['selected_osm_id']}，geojson={row['selected_geojson_type']}。"
        )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    features: list[dict] = []
    log_rows: list[dict[str, str]] = []

    for item in PARK_QUERIES:
        results, source_url, http_status = fetch_boundary(item["query"])
        raw_file = RAW_DIR / f"nominatim_{item['park_id']}.json"
        raw_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        selected = select_polygon(results)
        selected_geojson = selected.get("geojson") if selected else None
        if selected and selected_geojson:
            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "park_id": item["park_id"],
                        "park_name": item["park_name"],
                        "source": "OpenStreetMap via Nominatim",
                        "source_url": source_url,
                        "osm_type": selected.get("osm_type", ""),
                        "osm_id": str(selected.get("osm_id", "")),
                        "osm_class": selected.get("class", ""),
                        "osm_place_type": selected.get("type", ""),
                        "display_name": selected.get("display_name", ""),
                        "fetched_at_utc": fetched_at,
                    },
                    "geometry": selected_geojson,
                }
            )

        log_rows.append(
            {
                "fetched_at_utc": fetched_at,
                "park_id": item["park_id"],
                "park_name": item["park_name"],
                "query": item["query"],
                "http_status": str(http_status),
                "result_count": str(len(results)),
                "selected_osm_type": selected.get("osm_type", "") if selected else "",
                "selected_osm_id": str(selected.get("osm_id", "")) if selected else "",
                "selected_geojson_type": selected_geojson.get("type", "") if selected_geojson else "",
                "selected_display_name": selected.get("display_name", "") if selected else "",
                "raw_file": raw_file.relative_to(ROOT).as_posix(),
                "source_url": source_url,
            }
        )

    write_outputs(features, log_rows)
    print(f"wrote {len(features)} OSM boundary features to {OUT_GEOJSON}")
    print(f"wrote fetch log to {OUT_LOG}")
    print(f"wrote report to {REPORT}")


if __name__ == "__main__":
    main()
