from __future__ import annotations

import argparse
import csv
import json
import os
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[2]
WORKLIST = ROOT / "70_outputs" / "processed_tables" / "poi_supply_p0_followup_worklist.csv"
FETCH_LOG = ROOT / "50_external_gis" / "amap_poi" / "amap_fetch_log.csv"
OUT_DIR = ROOT / "50_external_gis" / "amap_routes"
RAW_DIR = OUT_DIR / "raw"
ROUTE_LOG = OUT_DIR / "amap_p0_route_fetch_log.csv"
ROUTE_RESULTS = OUT_DIR / "amap_p0_route_results.csv"
ROUTE_REVIEW = ROOT / "70_outputs" / "processed_tables" / "poi_supply_p0_route_access_review.csv"
REPORT = ROOT / "40_quality_evidence" / "p0_route_access_review_report.md"


LOG_FIELDS = [
    "run_id",
    "fetched_at_utc",
    "work_item_id",
    "park_id",
    "poi_name",
    "api_endpoint",
    "params_summary",
    "status",
    "info",
    "raw_file",
]

RESULT_FIELDS = [
    "run_id",
    "work_item_id",
    "review_id",
    "candidate_id",
    "park_id",
    "park_name",
    "poi_name",
    "origin_kind",
    "origin_longitude",
    "origin_latitude",
    "destination_longitude",
    "destination_latitude",
    "route_status",
    "route_info",
    "walking_distance_m",
    "walking_duration_s",
    "step_count",
    "route_access_status",
    "route_confidence",
    "route_notes",
]

REVIEW_EXTRA_FIELDS = [
    "route_run_id",
    "origin_kind",
    "origin_longitude",
    "origin_latitude",
    "walking_distance_m",
    "walking_duration_s",
    "step_count",
    "route_api_status",
    "route_api_info",
    "route_access_status_after_api",
    "route_access_confidence",
    "route_access_notes",
    "can_enter_p2_supply_after_route",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_params(params_summary: str) -> dict[str, str]:
    try:
        return {str(k): str(v) for k, v in json.loads(params_summary or "{}").items()}
    except json.JSONDecodeError:
        return {}


def load_park_centers() -> dict[str, str]:
    centers: dict[str, str] = {}
    for row in read_csv(FETCH_LOG):
        if row.get("api_endpoint") != "v5/place/around":
            continue
        params = parse_params(row.get("params_summary", ""))
        location = params.get("location", "")
        if "," in location:
            centers.setdefault(row.get("park_id", ""), location)
    return centers


def request_json(url: str, params: dict[str, str]) -> dict:
    headers = {"User-Agent": "park-siting-simulation-research/0.1 (P1 route access check)"}
    last_exc: Exception | None = None
    for attempt in range(1, 4):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < 3:
                time.sleep(1.5 * attempt)
    assert last_exc is not None
    raise last_exc


def route_metrics(data: dict) -> tuple[str, str, str]:
    route = data.get("route") or {}
    paths = route.get("paths") or []
    if not paths:
        return "", "", ""
    path = paths[0]
    steps = path.get("steps") or []
    return str(path.get("distance", "")), str(path.get("duration", "")), str(len(steps))


def fetch_routes(worklist_rows: list[dict[str, str]], key: str, dry_run: bool) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    centers = load_park_centers()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    logs: list[dict[str, str]] = []
    results: list[dict[str, str]] = []
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    endpoint = "https://restapi.amap.com/v3/direction/walking"

    for row in worklist_rows:
        origin = centers.get(row.get("park_id", ""), "")
        destination = f"{row.get('longitude', '')},{row.get('latitude', '')}"
        params = {
            "key": key,
            "origin": origin,
            "destination": destination,
            "output": "json",
        }
        params_summary = {
            "origin": origin,
            "destination": destination,
            "output": "json",
        }
        fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        raw_rel = ""
        status = ""
        info = ""
        distance = ""
        duration = ""
        step_count = ""
        if dry_run:
            status = "dry_run"
            info = "not_requested"
        else:
            data = request_json(endpoint, params)
            status = str(data.get("status", ""))
            info = str(data.get("info", ""))
            distance, duration, step_count = route_metrics(data)
            raw_path = RAW_DIR / f"{run_id}_{row['work_item_id']}.json"
            raw_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            raw_rel = raw_path.relative_to(ROOT).as_posix()

        route_ok = status == "1" and bool(distance)
        if route_ok:
            route_access_status = "amap_center_proxy_route_returned_needs_entrance_validation"
            route_confidence = "medium"
            notes = "高德步行路径已返回；origin 为公园中心点代理，不是入口/节点，仍需真实入口或现场可达性核验。"
        elif dry_run:
            route_access_status = "dry_run_not_verified"
            route_confidence = "low"
            notes = "dry-run 未调用高德路径接口。"
        else:
            route_access_status = "amap_route_failed_needs_retry_or_manual_check"
            route_confidence = "low"
            notes = "高德路径接口未返回可用步行路径，需重试或人工核验。"

        logs.append(
            {
                "run_id": run_id,
                "fetched_at_utc": fetched_at,
                "work_item_id": row.get("work_item_id", ""),
                "park_id": row.get("park_id", ""),
                "poi_name": row.get("poi_name", ""),
                "api_endpoint": "v3/direction/walking",
                "params_summary": json.dumps(params_summary, ensure_ascii=False, sort_keys=True),
                "status": status,
                "info": info,
                "raw_file": raw_rel,
            }
        )
        results.append(
            {
                "run_id": run_id,
                "work_item_id": row.get("work_item_id", ""),
                "review_id": row.get("review_id", ""),
                "candidate_id": row.get("candidate_id", ""),
                "park_id": row.get("park_id", ""),
                "park_name": row.get("park_name", ""),
                "poi_name": row.get("poi_name", ""),
                "origin_kind": "amap_park_center_proxy",
                "origin_longitude": origin.split(",", 1)[0] if "," in origin else "",
                "origin_latitude": origin.split(",", 1)[1] if "," in origin else "",
                "destination_longitude": row.get("longitude", ""),
                "destination_latitude": row.get("latitude", ""),
                "route_status": status,
                "route_info": info,
                "walking_distance_m": distance,
                "walking_duration_s": duration,
                "step_count": step_count,
                "route_access_status": route_access_status,
                "route_confidence": route_confidence,
                "route_notes": notes,
            }
        )
    return logs, results


def build_route_review(worklist_rows: list[dict[str, str]], route_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    route_by_work_item = {row["work_item_id"]: row for row in route_rows}
    review_rows: list[dict[str, str]] = []
    for row in worklist_rows:
        route = route_by_work_item.get(row["work_item_id"], {})
        route_returned = route.get("route_access_status") == "amap_center_proxy_route_returned_needs_entrance_validation"
        review_rows.append(
            {
                **row,
                "route_run_id": route.get("run_id", ""),
                "origin_kind": route.get("origin_kind", ""),
                "origin_longitude": route.get("origin_longitude", ""),
                "origin_latitude": route.get("origin_latitude", ""),
                "walking_distance_m": route.get("walking_distance_m", ""),
                "walking_duration_s": route.get("walking_duration_s", ""),
                "step_count": route.get("step_count", ""),
                "route_api_status": route.get("route_status", ""),
                "route_api_info": route.get("route_info", ""),
                "route_access_status_after_api": route.get("route_access_status", ""),
                "route_access_confidence": route.get("route_confidence", ""),
                "route_access_notes": route.get("route_notes", ""),
                "can_enter_p2_supply_after_route": "no",
                "notes": (
                    row.get("notes", "")
                    + " 路径结果仅为中心点代理；"
                    + ("已返回步行路径，但仍需真实入口/节点和运营授权。" if route_returned else "路径未闭合。")
                ),
            }
        )
    return review_rows


def write_report(route_rows: list[dict[str, str]], review_rows: list[dict[str, str]]) -> None:
    status_counts = Counter(row["route_access_status"] for row in route_rows)
    api_counts = Counter(row["route_status"] for row in route_rows)
    by_park = Counter(row["park_name"] for row in route_rows)
    distances = []
    durations = []
    for row in route_rows:
        try:
            distances.append(float(row["walking_distance_m"]))
        except (TypeError, ValueError):
            pass
        try:
            durations.append(float(row["walking_duration_s"]))
        except (TypeError, ValueError):
            pass
    lines = [
        "# P0 园内候选路径可达复核报告",
        "",
        "## 结论",
        "",
        f"- P0 路径核验项：{len(route_rows)} 条。",
        f"- 高德 API 状态：{dict(sorted(api_counts.items()))}",
        f"- 路径可达状态：{dict(sorted(status_counts.items()))}",
        f"- 按公园统计：{dict(sorted(by_park.items()))}",
    ]
    if distances:
        lines.append(f"- 步行距离范围：{int(min(distances))}-{int(max(distances))} 米。")
    if durations:
        lines.append(f"- 步行时间范围：{int(min(durations))}-{int(max(durations))} 秒。")
    lines.extend(
        [
            "",
            "## 口径限制",
            "",
            "- origin 使用高德公园中心点代理，不是真实入口、停车场、地铁站或游线节点。",
            "- 路径结果只用于 P1 可达性初筛；进入 P2 前仍需真实入口/节点路径或现场核验。",
            "- 所有记录 `can_enter_p2_supply_after_route` 仍为 `no`，因为运营授权和入口口径尚未闭合。",
            "- 日志和原始返回不包含高德 Key。",
            "",
            "## 输出文件",
            "",
            "- `50_external_gis/amap_routes/amap_p0_route_fetch_log.csv`",
            "- `50_external_gis/amap_routes/amap_p0_route_results.csv`",
            "- `70_outputs/processed_tables/poi_supply_p0_route_access_review.csv`",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    key = os.environ.get("AMAP_WEB_SERVICE_KEY", "").strip()
    if not key and not args.dry_run:
        raise SystemExit("AMAP_WEB_SERVICE_KEY is not set; rerun with --dry-run or set the env var.")

    worklist_rows = read_csv(WORKLIST)
    logs, route_rows = fetch_routes(worklist_rows, key, args.dry_run)
    review_rows = build_route_review(worklist_rows, route_rows)
    write_csv(ROUTE_LOG, logs, LOG_FIELDS)
    write_csv(ROUTE_RESULTS, route_rows, RESULT_FIELDS)
    write_csv(ROUTE_REVIEW, review_rows, list(worklist_rows[0].keys()) + REVIEW_EXTRA_FIELDS)
    write_report(route_rows, review_rows)
    print(f"wrote {len(route_rows)} P0 route result rows to {ROUTE_RESULTS}")
    print(f"wrote route review rows to {ROUTE_REVIEW}")
    print(f"wrote report to {REPORT}")


if __name__ == "__main__":
    main()
