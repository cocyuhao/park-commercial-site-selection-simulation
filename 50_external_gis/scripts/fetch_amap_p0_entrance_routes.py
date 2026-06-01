from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"
WORKLIST = ROOT / "70_outputs" / "processed_tables" / "poi_supply_p0_followup_worklist.csv"
OUT_DIR = ROOT / "50_external_gis" / "amap_routes"
RAW_DIR = OUT_DIR / "raw_entrance_nodes"
QUERY_PLAN = OUT_DIR / "p0_entrance_node_query_plan.csv"
NODE_CANDIDATES = OUT_DIR / "amap_p0_entrance_node_candidates.csv"
FETCH_LOG = OUT_DIR / "amap_p0_entrance_node_fetch_log.csv"
ROUTE_RESULTS = OUT_DIR / "amap_p0_entrance_node_route_results.csv"
ROUTE_REVIEW = ROOT / "70_outputs" / "processed_tables" / "poi_supply_p0_entrance_route_review.csv"
REPORT = ROOT / "40_quality_evidence" / "p0_entrance_route_review_report.md"

AMAP_TEXT_ENDPOINT = "https://restapi.amap.com/v5/place/text"
AMAP_WALK_ENDPOINT = "https://restapi.amap.com/v3/direction/walking"


NODE_KEYWORDS = {
    "sample_city_green_heart": [
        ("city_green_heart_p11_parking", "城市绿心森林公园P11停车场", "parking_or_visit_node"),
        ("city_green_heart_south_gate", "城市绿心森林公园南门", "park_gate"),
        ("city_green_heart_west_gate", "城市绿心森林公园西门", "park_gate"),
        ("city_green_heart_green_heart_road", "城市绿心森林公园绿心路入口", "park_gate_or_road_node"),
    ],
    "sample_olympic_forest": [
        ("olympic_south_gate", "奥林匹克森林公园南园南门", "park_gate"),
        ("olympic_south_west_gate", "奥林匹克森林公园南园西门", "park_gate"),
        ("olympic_south_east_gate", "奥林匹克森林公园南园东门", "park_gate"),
        ("olympic_north_gate", "奥林匹克森林公园北园北门", "park_gate"),
        ("olympic_north_east_gate", "奥林匹克森林公园北园东门", "park_gate"),
        ("olympic_north_south_gate", "奥林匹克森林公园北园南门", "park_gate"),
        ("olympic_north_sports_park", "奥林匹克森林公园北园体育园", "park_internal_node"),
        ("olympic_national_tennis_center", "国家网球中心", "nearby_transit_or_visit_node"),
    ],
}

PLAN_FIELDS = ["query_id", "park_id", "park_name", "keyword", "node_kind", "region", "page_size"]
NODE_FIELDS = [
    "run_id",
    "query_id",
    "park_id",
    "park_name",
    "keyword",
    "node_kind",
    "amap_poi_id",
    "node_name",
    "amap_type",
    "address",
    "longitude",
    "latitude",
    "candidate_rank",
    "candidate_status",
    "notes",
]
LOG_FIELDS = [
    "run_id",
    "fetched_at_utc",
    "api_endpoint",
    "query_id",
    "work_item_id",
    "park_id",
    "params_summary",
    "status",
    "info",
    "result_count",
    "raw_file",
]
ROUTE_FIELDS = [
    "run_id",
    "work_item_id",
    "candidate_id",
    "park_id",
    "park_name",
    "poi_name",
    "node_query_id",
    "node_kind",
    "node_name",
    "node_longitude",
    "node_latitude",
    "destination_longitude",
    "destination_latitude",
    "node_to_poi_straight_distance_m",
    "route_status",
    "route_info",
    "walking_distance_m",
    "walking_duration_s",
    "step_count",
    "route_proxy_status",
    "route_confidence",
    "route_notes",
]
REVIEW_EXTRA_FIELDS = [
    "entrance_route_run_id",
    "best_node_kind",
    "best_node_name",
    "best_node_longitude",
    "best_node_latitude",
    "best_node_to_poi_straight_distance_m",
    "best_walking_distance_m",
    "best_walking_duration_s",
    "best_step_count",
    "entrance_route_api_status",
    "entrance_route_api_info",
    "entrance_route_proxy_status",
    "entrance_route_confidence",
    "entrance_route_notes",
    "can_enter_p2_supply_after_entrance_route",
]


def load_local_env(path: Path = ENV_FILE) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def sanitize(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    return value.strip("_") or "item"


def params_summary(params: dict[str, str]) -> str:
    return json.dumps({k: v for k, v in params.items() if k != "key"}, ensure_ascii=False, sort_keys=True)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def request_json(endpoint: str, params: dict[str, str], retries: int = 3) -> dict[str, Any]:
    headers = {"User-Agent": "park-siting-simulation-research/0.1 (P1 entrance route check)"}
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(endpoint, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            payload = response.json()
            return payload if isinstance(payload, dict) else {}
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(1.5 * attempt)
    assert last_exc is not None
    raise RuntimeError(f"request failed after {retries} attempts: {type(last_exc).__name__}") from last_exc


def extract_pois(payload: dict[str, Any]) -> list[dict[str, Any]]:
    pois = payload.get("pois") or []
    if isinstance(pois, list):
        return [item for item in pois if isinstance(item, dict)]
    if isinstance(pois, dict):
        nested = pois.get("poi") or pois.get("pois") or []
        if isinstance(nested, list):
            return [item for item in nested if isinstance(item, dict)]
        if isinstance(nested, dict):
            return [nested]
        if pois.get("id") and pois.get("name"):
            return [pois]
    return []


def split_location(value: str) -> tuple[str, str]:
    if "," not in value:
        return "", ""
    lon, lat = value.split(",", 1)
    return lon.strip(), lat.strip()


def haversine_m(lon1: str, lat1: str, lon2: str, lat2: str) -> float:
    try:
        x1, y1, x2, y2 = map(float, [lon1, lat1, lon2, lat2])
    except ValueError:
        return float("inf")
    radius = 6371000.0
    p1 = math.radians(y1)
    p2 = math.radians(y2)
    dp = math.radians(y2 - y1)
    dl = math.radians(x2 - x1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def route_metrics(payload: dict[str, Any]) -> tuple[str, str, str]:
    route = payload.get("route") or {}
    paths = route.get("paths") or []
    if not paths:
        return "", "", ""
    first_path = paths[0]
    steps = first_path.get("steps") or []
    return str(first_path.get("distance", "")), str(first_path.get("duration", "")), str(len(steps))


def build_query_plan(worklist_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    park_names = {row["park_id"]: row["park_name"] for row in worklist_rows}
    rows: list[dict[str, str]] = []
    for park_id in sorted(park_names):
        for query_id, keyword, node_kind in NODE_KEYWORDS.get(park_id, []):
            rows.append(
                {
                    "query_id": query_id,
                    "park_id": park_id,
                    "park_name": park_names[park_id],
                    "keyword": keyword,
                    "node_kind": node_kind,
                    "region": "北京市",
                    "page_size": "5",
                }
            )
    return rows


def fetch_node_candidates(plan_rows: list[dict[str, str]], key: str, run_id: str, dry_run: bool) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    logs: list[dict[str, str]] = []
    nodes: list[dict[str, str]] = []
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for row in plan_rows:
        params = {
            "key": key,
            "keywords": row["keyword"],
            "region": row["region"],
            "city_limit": "true",
            "page_size": row["page_size"],
            "page_num": "1",
            "show_fields": "business",
        }
        fetched_at = now_utc()
        raw_rel = ""
        if dry_run:
            payload = {"status": "dry_run", "info": "not_requested", "pois": []}
            pois: list[dict[str, Any]] = []
        else:
            payload = request_json(AMAP_TEXT_ENDPOINT, params)
            pois = extract_pois(payload)
            raw_path = RAW_DIR / f"{run_id}_node_{sanitize(row['query_id'])}.json"
            raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            raw_rel = raw_path.relative_to(ROOT).as_posix()
        logs.append(
            {
                "run_id": run_id,
                "fetched_at_utc": fetched_at,
                "api_endpoint": "v5/place/text",
                "query_id": row["query_id"],
                "work_item_id": "",
                "park_id": row["park_id"],
                "params_summary": params_summary(params),
                "status": str(payload.get("status", "")),
                "info": str(payload.get("info", "")),
                "result_count": str(len(pois)),
                "raw_file": raw_rel,
            }
        )
        for index, poi in enumerate(pois, start=1):
            lon, lat = split_location(str(poi.get("location", "")))
            nodes.append(
                {
                    "run_id": run_id,
                    "query_id": row["query_id"],
                    "park_id": row["park_id"],
                    "park_name": row["park_name"],
                    "keyword": row["keyword"],
                    "node_kind": row["node_kind"],
                    "amap_poi_id": str(poi.get("id", "")),
                    "node_name": str(poi.get("name", "")),
                    "amap_type": str(poi.get("type", "")),
                    "address": str(poi.get("address", "")),
                    "longitude": lon,
                    "latitude": lat,
                    "candidate_rank": str(index),
                    "candidate_status": "amap_text_candidate_needs_field_validation",
                    "notes": "高德文本搜索得到的入口/节点候选；可能是门、停车场、场馆或附近访问节点，需现场确认。",
                }
            )
        time.sleep(0.2)
    return nodes, logs


def dedupe_nodes(nodes: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    result: list[dict[str, str]] = []
    for row in nodes:
        key = (row["park_id"], row["amap_poi_id"] or row["node_name"], row["longitude"] + "," + row["latitude"])
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def select_nodes_for_work_item(row: dict[str, str], nodes: list[dict[str, str]], max_nodes: int) -> list[dict[str, str]]:
    park_nodes = [node for node in nodes if node["park_id"] == row["park_id"] and node["longitude"] and node["latitude"]]
    ranked = sorted(
        park_nodes,
        key=lambda node: haversine_m(node["longitude"], node["latitude"], row["longitude"], row["latitude"]),
    )
    return ranked[:max_nodes]


def fetch_routes(
    worklist_rows: list[dict[str, str]],
    nodes: list[dict[str, str]],
    key: str,
    run_id: str,
    dry_run: bool,
    max_nodes_per_work_item: int,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    logs: list[dict[str, str]] = []
    routes: list[dict[str, str]] = []
    for item in worklist_rows:
        selected_nodes = select_nodes_for_work_item(item, nodes, max_nodes_per_work_item)
        destination = f"{item['longitude']},{item['latitude']}"
        for node in selected_nodes:
            origin = f"{node['longitude']},{node['latitude']}"
            params = {"key": key, "origin": origin, "destination": destination, "output": "json"}
            fetched_at = now_utc()
            raw_rel = ""
            if dry_run:
                payload = {"status": "dry_run", "info": "not_requested"}
                distance = duration = step_count = ""
            else:
                payload = request_json(AMAP_WALK_ENDPOINT, params)
                distance, duration, step_count = route_metrics(payload)
                raw_path = RAW_DIR / f"{run_id}_route_{sanitize(item['work_item_id'])}_{sanitize(node['query_id'])}_{sanitize(node['amap_poi_id'] or node['node_name'])}.json"
                raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                raw_rel = raw_path.relative_to(ROOT).as_posix()
            api_status = str(payload.get("status", ""))
            api_info = str(payload.get("info", ""))
            route_ok = api_status == "1" and bool(distance)
            proxy_status = "entrance_or_node_proxy_route_returned_needs_field_validation" if route_ok else "entrance_or_node_route_failed_needs_retry_or_manual_check"
            straight_distance = haversine_m(node["longitude"], node["latitude"], item["longitude"], item["latitude"])
            logs.append(
                {
                    "run_id": run_id,
                    "fetched_at_utc": fetched_at,
                    "api_endpoint": "v3/direction/walking",
                    "query_id": node["query_id"],
                    "work_item_id": item["work_item_id"],
                    "park_id": item["park_id"],
                    "params_summary": params_summary(params),
                    "status": api_status,
                    "info": api_info,
                    "result_count": "1" if route_ok else "0",
                    "raw_file": raw_rel,
                }
            )
            routes.append(
                {
                    "run_id": run_id,
                    "work_item_id": item["work_item_id"],
                    "candidate_id": item["candidate_id"],
                    "park_id": item["park_id"],
                    "park_name": item["park_name"],
                    "poi_name": item["poi_name"],
                    "node_query_id": node["query_id"],
                    "node_kind": node["node_kind"],
                    "node_name": node["node_name"],
                    "node_longitude": node["longitude"],
                    "node_latitude": node["latitude"],
                    "destination_longitude": item["longitude"],
                    "destination_latitude": item["latitude"],
                    "node_to_poi_straight_distance_m": "" if math.isinf(straight_distance) else f"{straight_distance:.1f}",
                    "route_status": api_status,
                    "route_info": api_info,
                    "walking_distance_m": distance,
                    "walking_duration_s": duration,
                    "step_count": step_count,
                    "route_proxy_status": proxy_status,
                    "route_confidence": "medium" if route_ok else "low",
                    "route_notes": "入口/节点来自高德文本搜索，不等于官方入口清单；路径可用于 P1 代理核验，仍需现场或官方节点确认。",
                }
            )
            time.sleep(0.2)
    return routes, logs


def best_route_for_work_item(routes: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in routes:
        grouped[row["work_item_id"]].append(row)
    best: dict[str, dict[str, str]] = {}
    for work_item_id, rows in grouped.items():
        valid = [row for row in rows if row["walking_distance_m"]]
        if valid:
            best[work_item_id] = min(valid, key=lambda row: float(row["walking_distance_m"]))
        elif rows:
            best[work_item_id] = rows[0]
    return best


def build_review(worklist_rows: list[dict[str, str]], routes: list[dict[str, str]]) -> list[dict[str, str]]:
    best_by_id = best_route_for_work_item(routes)
    review_rows: list[dict[str, str]] = []
    for item in worklist_rows:
        route = best_by_id.get(item["work_item_id"], {})
        route_returned = route.get("route_proxy_status") == "entrance_or_node_proxy_route_returned_needs_field_validation"
        review_rows.append(
            {
                **item,
                "entrance_route_run_id": route.get("run_id", ""),
                "best_node_kind": route.get("node_kind", ""),
                "best_node_name": route.get("node_name", ""),
                "best_node_longitude": route.get("node_longitude", ""),
                "best_node_latitude": route.get("node_latitude", ""),
                "best_node_to_poi_straight_distance_m": route.get("node_to_poi_straight_distance_m", ""),
                "best_walking_distance_m": route.get("walking_distance_m", ""),
                "best_walking_duration_s": route.get("walking_duration_s", ""),
                "best_step_count": route.get("step_count", ""),
                "entrance_route_api_status": route.get("route_status", ""),
                "entrance_route_api_info": route.get("route_info", ""),
                "entrance_route_proxy_status": route.get("route_proxy_status", ""),
                "entrance_route_confidence": route.get("route_confidence", ""),
                "entrance_route_notes": route.get("route_notes", ""),
                "can_enter_p2_supply_after_entrance_route": "no",
                "notes": (
                    item.get("notes", "")
                    + " 入口/节点代理路径"
                    + ("已返回；仍需官方/现场入口节点与运营授权。" if route_returned else "未闭合，需重试或现场确认。")
                ),
            }
        )
    return review_rows


def write_report(nodes: list[dict[str, str]], routes: list[dict[str, str]], review_rows: list[dict[str, str]]) -> None:
    node_counts = Counter(row["park_name"] for row in nodes)
    route_counts = Counter(row["route_proxy_status"] for row in routes)
    best_status = Counter(row["entrance_route_proxy_status"] for row in review_rows)
    best_distances = []
    best_durations = []
    for row in review_rows:
        try:
            best_distances.append(float(row["best_walking_distance_m"]))
        except ValueError:
            pass
        try:
            best_durations.append(float(row["best_walking_duration_s"]))
        except ValueError:
            pass
    lines = [
        "# P0 入口/节点代理路径复核报告",
        "",
        "## 结论",
        "",
        f"- 入口/节点候选：{len(nodes)} 条，按公园统计：{dict(sorted(node_counts.items()))}。",
        f"- 路径请求结果：{len(routes)} 条，状态：{dict(sorted(route_counts.items()))}。",
        f"- P0 工作项最佳入口/节点路径：{len(review_rows)} 条，状态：{dict(sorted(best_status.items()))}。",
    ]
    if best_distances:
        lines.append(f"- 最短入口/节点代理步行距离范围：{int(min(best_distances))}-{int(max(best_distances))} 米。")
    if best_durations:
        lines.append(f"- 最短入口/节点代理步行时间范围：{int(min(best_durations))}-{int(max(best_durations))} 秒。")
    lines.extend(
        [
            "",
            "## 口径限制",
            "",
            "- 入口/节点来自高德文本搜索，不是官方入口清单。",
            "- 本结果优于“公园中心点代理路径”，但仍只是 P1 代理核验。",
            "- `can_enter_p2_supply_after_entrance_route` 全部保持 `no`，因为运营授权和现场确认尚未闭合。",
            "- 输出和日志不保存高德 Key。",
            "",
            "## 输出文件",
            "",
            "- `50_external_gis/amap_routes/p0_entrance_node_query_plan.csv`",
            "- `50_external_gis/amap_routes/amap_p0_entrance_node_candidates.csv`",
            "- `50_external_gis/amap_routes/amap_p0_entrance_node_route_results.csv`",
            "- `70_outputs/processed_tables/poi_supply_p0_entrance_route_review.csv`",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-nodes-per-work-item", type=int, default=4)
    args = parser.parse_args()

    load_local_env()
    key = os.environ.get("AMAP_WEB_SERVICE_KEY", "").strip()
    if not key and not args.dry_run:
        raise SystemExit("AMAP_WEB_SERVICE_KEY is not set; rerun with --dry-run or configure .env.")

    worklist_rows = read_csv(WORKLIST)
    plan_rows = build_query_plan(worklist_rows)
    write_csv(QUERY_PLAN, plan_rows, PLAN_FIELDS)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    nodes, node_logs = fetch_node_candidates(plan_rows, key, run_id, args.dry_run)
    nodes = dedupe_nodes(nodes)
    routes, route_logs = fetch_routes(worklist_rows, nodes, key, run_id, args.dry_run, args.max_nodes_per_work_item)
    review_rows = build_review(worklist_rows, routes)
    write_csv(NODE_CANDIDATES, nodes, NODE_FIELDS)
    write_csv(FETCH_LOG, node_logs + route_logs, LOG_FIELDS)
    write_csv(ROUTE_RESULTS, routes, ROUTE_FIELDS)
    write_csv(ROUTE_REVIEW, review_rows, list(worklist_rows[0].keys()) + REVIEW_EXTRA_FIELDS)
    write_report(nodes, routes, review_rows)
    print(f"wrote node query plan rows={len(plan_rows)} to {QUERY_PLAN}")
    print(f"wrote node candidates rows={len(nodes)} to {NODE_CANDIDATES}")
    print(f"wrote entrance route rows={len(routes)} to {ROUTE_RESULTS}")
    print(f"wrote entrance route review rows={len(review_rows)} to {ROUTE_REVIEW}")
    print(f"wrote report to {REPORT}")


if __name__ == "__main__":
    main()
