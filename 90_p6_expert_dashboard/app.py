from __future__ import annotations

import ast
import csv
import html
import json
import math
import os
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx

import sys


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "90_p6_expert_dashboard"
STATIC_DIR = APP_DIR / "static"
CACHE_DIR = APP_DIR / "cache"
CACHE_FILE = CACHE_DIR / "deepseek_ai_reviews.json"
FEEDBACK_FILE = CACHE_DIR / "expert_feedback.json"
UPLOAD_DIR = CACHE_DIR / "uploaded_sources"
UPLOAD_INDEX_FILE = CACHE_DIR / "uploaded_sources.json"
UPLOAD_CANDIDATES_FILE = CACHE_DIR / "upload_parse_candidates.json"
GATE_INPUT_FILE = CACHE_DIR / "gate_inputs.json"
MAP_CONTEXT_FILE = CACHE_DIR / "map_context.json"
MAP_CONTEXT_POI_FILE = CACHE_DIR / "map_context_pois.json"
MAP_BOUNDARY_FILE = CACHE_DIR / "map_boundary.json"
AMAP_STATIC_CACHE = CACHE_DIR / "amap_static_map.png"
AMAP_TILE_CACHE_DIR = CACHE_DIR / "amap_static_tiles"
AMAP_STATIC_STATUS_FILE = CACHE_DIR / "amap_static_map_status.json"
KNOWN_OSM_BOUNDARY_FILE = ROOT / "50_external_gis" / "boundaries" / "osm_park_boundaries.geojson"
MAP_KEYWORD_ALIASES = {
    "aosen": "北京奥森",
    "as": "北京奥森",
    "osen": "北京奥森",
    "db": "东坝公园",
    "dongba": "东坝公园",
    "cygy": "北京朝阳公园",
    "chaoyang": "北京朝阳公园",
    "yhy": "颐和园",
    "yiheyuan": "颐和园",
}
PROCESSED = ROOT / "70_outputs" / "processed_tables"
SRC_DIR = ROOT / "60_model" / "src"
DB_DIR = ROOT / "60_model" / "db"
SIM_DIR = ROOT / "60_model" / "simulation"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(DB_DIR) not in sys.path:
    sys.path.insert(0, str(DB_DIR))
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

from llm_router import load_local_env, run_deepseek_task  # noqa: E402
from engine import run_structural_simulation  # noqa: E402
from store import (  # noqa: E402
    complete_job,
    create_job,
    get_job,
    get_results,
    import_existing_outputs,
    list_calibration_gates,
    list_gate_inputs,
    list_jobs,
    list_poi_candidates,
    list_runtime_uploads,
    list_upload_candidates,
    upsert_gate_input,
    upsert_runtime_upload,
    upsert_upload_candidate,
)


app = FastAPI(title="P6 Expert Decision Dashboard", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class AIRequest(BaseModel):
    mode: str
    node_id: str | None = None


class ChatRequest(BaseModel):
    node_id: str | None = None
    message: str
    position_note: str | None = None
    upload_refs: list[dict[str, Any]] = []
    history: list[dict[str, str]] = []


class ExpertFeedback(BaseModel):
    node_id: str
    comment: str
    expert_name: str | None = None
    position_note: str | None = None
    data_hint: str | None = None


class GateInput(BaseModel):
    calibration_domain: str
    note: str = ""
    owner: str | None = None
    due_date: str | None = None
    source_hint: str | None = None


class ConfirmCandidateRequest(BaseModel):
    reviewer_note: str = ""


class MapContextRequest(BaseModel):
    keyword: str
    longitude: str | None = None
    latitude: str | None = None
    matched_name: str | None = None
    address: str | None = None
    radius_m: int = 1200


class SimulationJobRequest(BaseModel):
    scenario_name: str = "structural_dry_run"
    seed: int = 20260601
    iterations: int = 100


@app.on_event("startup")
def prepare_local_database() -> None:
    import_existing_outputs()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def parse_list(value: str | None) -> list[str]:
    if not value:
        return []
    text = value.strip()
    if not text:
        return []
    try:
        parsed = ast.literal_eval(text)
    except (SyntaxError, ValueError):
        return [item.strip() for item in text.replace("；", ";").split(";") if item.strip()]
    if isinstance(parsed, list):
        return [str(item) for item in parsed if str(item).strip()]
    return [str(parsed)]


def normalize_row(row: dict[str, str]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in row.items():
        normalized[key] = "" if value is None else value
    return normalized


def review_meta(
    *,
    source_hint: str = "",
    evidence_hint: str = "",
    status_label: str = "待复核 / 非最终",
) -> dict[str, Any]:
    return {
        "output_status": "needs_review",
        "not_final": True,
        "status_label": status_label,
        "source_hint": source_hint,
        "evidence_hint": evidence_hint,
    }


def is_osen_context(context: dict[str, Any]) -> bool:
    text = f"{context.get('keyword', '')}{context.get('matched_name', '')}"
    return "奥森" in text or "奥林匹克森林" in text


def blocked_gate_count(gates: list[dict[str, Any]]) -> int:
    return sum(
        1
        for gate in gates
        if gate.get("required_before_p4_conclusion") == "yes"
        and gate.get("current_gate_status") not in {"closed", "passed"}
    )


def node_missing_fields(node: dict[str, Any], gates: list[dict[str, Any]]) -> list[str]:
    fields: list[str] = []
    for item in node.get("data_requests", []):
        value = item.get("missing_input") or item.get("calibration_domain")
        if value and value not in fields:
            fields.append(str(value))
    for gate in gates:
        if gate.get("required_before_p4_conclusion") == "yes" and gate.get("current_gate_status") not in {"closed", "passed"}:
            domain = str(gate.get("calibration_domain") or "")
            if domain and domain not in fields:
                fields.append(domain)
    return fields


def backend_draft_score(
    node: dict[str, Any],
    *,
    gates: list[dict[str, Any]],
    amap_supply: list[dict[str, Any]],
    map_boundary: dict[str, Any] | None,
    estimated_boundary: dict[str, Any] | None,
    map_context: dict[str, Any],
) -> dict[str, Any]:
    if not is_osen_context(map_context):
        return {
            "discussion_score_draft": 0,
            "score_status": "external_preview_only",
            "score_label": "外部预览",
            "score_explanation": "当前地图不是奥森项目上下文，只返回地图/POI/边界预览，不套用奥森节点评分。",
            "score_inputs": {
                "project_context": "external",
                "base_score": node.get("discussion_score", ""),
            },
        }
    base = safe_float(node.get("discussion_score")) or 50.0
    gate_count = blocked_gate_count(gates)
    missing_fields = node_missing_fields(node, gates)
    boundary_status = (map_boundary or estimated_boundary or {}).get("boundary_status", "estimated_range_needs_review")
    poi_count = len(amap_supply)
    penalty = min(30, gate_count * 5) + min(18, len(missing_fields) * 2)
    if poi_count < 20:
        penalty += 6
    if "estimated" in str(boundary_status):
        penalty += 8
    score = max(0, min(100, round(base - penalty)))
    return {
        "discussion_score_draft": score,
        "score_status": "needs_review_not_final",
        "score_label": f"{score} 分 · 待复核",
        "score_explanation": "后端草案分仅用于讨论，已按 P3 gate、缺失字段、POI 数量和边界状态扣分；不是最终排序。",
        "score_inputs": {
            "project_context": "osen",
            "base_score": base,
            "blocked_gate_count": gate_count,
            "missing_required_fields": missing_fields,
            "poi_context_count": poi_count,
            "boundary_status": boundary_status,
            "penalty": penalty,
        },
    }


def enrich_gate(row: dict[str, Any]) -> dict[str, Any]:
    status = row.get("current_gate_status", "")
    label = "已闭合" if status in {"closed", "passed"} else "待补资料 / 待复核"
    return {
        **row,
        **review_meta(
            source_hint=row.get("source_table", "p3_calibration_gate_status.csv"),
            evidence_hint=row.get("blocking_reason", ""),
            status_label=label,
        ),
    }


def enrich_poi(row: dict[str, Any]) -> dict[str, Any]:
    boundary = str(row.get("boundary_filter_status", ""))
    label = "公开边界内候选 / 待复核" if boundary == "inside_osm_polygon" else "周边或边界未确认 / 待复核"
    return {
        **row,
        **review_meta(
            source_hint=row.get("source_path", "poi_supply_candidates_amap_boundary_filter.csv"),
            evidence_hint=row.get("supply_use_status", "do_not_use_as_in_park_supply_yet"),
            status_label=label,
        ),
    }


def load_dashboard() -> dict[str, Any]:
    nodes = read_csv_rows(PROCESSED / "p2_project_node_candidates.csv")
    priorities = read_csv_rows(PROCESSED / "p4_feedback_node_priority_draft_deepseek.csv")
    scenarios = read_csv_rows(PROCESSED / "p4_feedback_scenario_matrix_draft_deepseek.csv")
    requests = read_csv_rows(PROCESSED / "p4_feedback_data_request_to_partner_deepseek.csv")
    gates = read_csv_rows(PROCESSED / "p3_calibration_gate_status.csv")
    assumptions = read_csv_rows(PROCESSED / "p2_business_scene_assumption_pool.csv")
    gaps = read_csv_rows(PROCESSED / "p2_input_gap_register.csv")
    amap_supply = load_amap_supply()
    map_context = load_map_context()
    map_boundary = load_map_boundary_for_context(map_context) or load_known_osm_boundary(map_context)
    if map_boundary and not load_map_boundary_for_context(map_context):
        save_map_boundary(map_boundary)
    estimated_boundary = estimated_boundary_from_points(amap_supply, map_context) if not map_boundary else None
    map_bounds = boundary_bounds(map_boundary or estimated_boundary) if (map_boundary or estimated_boundary) else poi_bounds(amap_supply, map_context)
    boundary_polygon = boundary_points(map_boundary) if map_boundary else boundary_polygon_from_bounds(map_bounds)
    if estimated_boundary and not map_boundary:
        boundary_polygon = boundary_points(estimated_boundary)

    priority_by_id = {row.get("node_id", ""): row for row in priorities}
    request_by_node: dict[str, list[dict[str, Any]]] = {}
    scenario_by_node: dict[str, list[dict[str, Any]]] = {}
    assumption_by_project: dict[str, list[dict[str, Any]]] = {}

    for row in requests:
        request_by_node.setdefault(row.get("node_id", ""), []).append(normalize_row(row))
    for row in scenarios:
        scenario_by_node.setdefault(row.get("node_id", ""), []).append(normalize_row(row))
    for row in assumptions:
        assumption_by_project.setdefault(row.get("source_project_name", ""), []).append(normalize_row(row))

    merged_nodes: list[dict[str, Any]] = []
    for index, row in enumerate(nodes):
        node_id = row.get("node_id", "")
        priority = priority_by_id.get(node_id, {})
        source_project_name = row.get("source_project_name", "")
        base_node = {
            **normalize_row(row),
            "area_sqm": priority.get("area_sqm") or row.get("area_sqm") or "",
            "business_direction": parse_list(priority.get("business_direction") or row.get("candidate_business_formats")),
            "candidate_business_formats": parse_list(row.get("candidate_business_formats")),
            "discussion_score": priority.get("discussion_score", ""),
            "feedback_priority": priority.get("feedback_priority", "discussion_only"),
            "score_reason": priority.get("score_reason", ""),
            "placeholder_inputs_used": priority.get("placeholder_inputs_used", ""),
            "must_collect_before_final": priority.get("must_collect_before_final", ""),
            "use_boundary": priority.get("use_boundary", "feedback_draft_not_final_ranking"),
            "output_status": priority.get("output_status") or row.get("output_status") or "needs_review",
            "data_requests": request_by_node.get(node_id, []),
            "feedback_scenarios": scenario_by_node.get(node_id, []),
            "assumption_refs": assumption_by_project.get(source_project_name, []),
            "schematic_position": {
                "x": 18 + (index % 3) * 30,
                "y": 28 + (index // 3) * 34,
            },
        }
        score_payload = backend_draft_score(
            base_node,
            gates=gates,
            amap_supply=amap_supply,
            map_boundary=map_boundary,
            estimated_boundary=estimated_boundary,
            map_context=map_context,
        )
        missing_fields = node_missing_fields(base_node, gates)
        merged_nodes.append(
            {
                **base_node,
                **review_meta(
                    source_hint="p2_project_node_candidates.csv; p4_feedback_node_priority_draft_deepseek.csv",
                    evidence_hint="P4 feedback draft; not final ranking",
                    status_label="反馈草案 / 待复核",
                ),
                **score_payload,
                "missing_required_fields": missing_fields,
                "next_data_needed": [
                    "补齐 P3 gate 真实来源",
                    "确认 DWG/DXF/GeoJSON/SVG/PDF 可信几何导出",
                    "补齐真实客流、转化率、收益成本和运营授权",
                ],
            }
        )

    return {
        "meta": {
            "project_name": "奥森公园商业选址仿真 P6 原型",
            "phase": "P6 expert dashboard prototype",
            "data_status": "feedback_draft / needs_review / not_final",
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "source_tables": [
                "p2_project_node_candidates.csv",
                "p4_feedback_node_priority_draft_deepseek.csv",
                "p4_feedback_scenario_matrix_draft_deepseek.csv",
                "p4_feedback_data_request_to_partner_deepseek.csv",
                "p3_calibration_gate_status.csv",
            ],
        },
        "nodes": merged_nodes,
        "p4_feedback": {
            "node_priority": [normalize_row(row) for row in priorities],
            "scenario_matrix": [normalize_row(row) for row in scenarios],
            "data_requests": [normalize_row(row) for row in requests],
        },
        "p3_gates": [enrich_gate(normalize_row(row)) for row in gates],
        "p2_gaps": [normalize_row(row) for row in gaps],
        "amap": {
            "status": amap_status(amap_supply),
            "supply_points": amap_supply,
            "static_map_url": "/api/amap/static-map",
            "map_context": map_context,
            "map_bounds": map_bounds,
            "boundary_polygon": boundary_polygon,
            "boundary_status": (map_boundary or estimated_boundary or {}).get("boundary_status", "estimated_range_needs_review"),
            "boundary_source": (map_boundary or estimated_boundary or {}).get("source", "computed_from_visible_points"),
            "context_nodes": build_context_nodes(merged_nodes, map_context),
        },
        "uploads": load_upload_index(),
        "upload_candidates": load_upload_candidates(),
        "gate_inputs": load_gate_inputs(),
    }


def load_amap_supply(limit: int = 60) -> list[dict[str, Any]]:
    context_pois = load_map_context_pois()
    if context_pois:
        return context_pois[:limit]
    rows = read_csv_rows(PROCESSED / "poi_supply_candidates_amap_boundary_filter.csv")
    olympic = [row for row in rows if row.get("park_id") == "sample_olympic_forest"]
    preferred = sorted(
        olympic,
        key=lambda row: (
            0 if row.get("boundary_filter_status") == "inside_osm_polygon" else 1,
            float(row.get("computed_center_distance_m") or row.get("min_distance_m") or 999999),
        ),
    )
    points: list[dict[str, Any]] = []
    for row in preferred[:limit]:
        lon = row.get("longitude")
        lat = row.get("latitude")
        if not lon or not lat:
            continue
        points.append(
            {
                "candidate_id": row.get("candidate_id", ""),
                "poi_name": row.get("poi_name", ""),
                "category": row.get("standard_categories", ""),
                "amap_keywords": row.get("amap_keywords", ""),
                "longitude": lon,
                "latitude": lat,
                "rating": row.get("rating", ""),
                "cost_yuan": row.get("cost_yuan", ""),
                "distance_m": row.get("computed_center_distance_m") or row.get("min_distance_m") or "",
                "boundary_filter_status": row.get("boundary_filter_status", ""),
                "supply_use_status": row.get("supply_use_status", ""),
                "output_status": "needs_review",
            }
        )
    return points


def load_map_context_pois() -> list[dict[str, Any]]:
    if MAP_CONTEXT_POI_FILE.exists():
        try:
            data = json.loads(MAP_CONTEXT_POI_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            return []
    return []


def save_map_context_pois(rows: list[dict[str, Any]]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    MAP_CONTEXT_POI_FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_amap_around_pois(lon: str, lat: str, key: str, limit: int = 50) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    keywords = "咖啡|餐饮|便利店|书店|亲子|文创|茶饮"
    with httpx.Client(timeout=10.0) as client:
        for page in range(1, 3):
            params = {
                "key": key,
                "location": f"{lon},{lat}",
                "keywords": keywords,
                "radius": "3500",
                "offset": "25",
                "page": str(page),
                "extensions": "base",
            }
            response = client.get("https://restapi.amap.com/v3/place/around", params=params)
            response.raise_for_status()
            payload = response.json()
            for poi in payload.get("pois") or []:
                location = poi.get("location", "")
                if "," not in location:
                    continue
                p_lon, p_lat = location.split(",", 1)
                collected.append(
                    {
                        "candidate_id": poi.get("id", ""),
                        "poi_name": poi.get("name", ""),
                        "category": poi.get("type", ""),
                        "amap_keywords": keywords,
                        "longitude": p_lon,
                        "latitude": p_lat,
                        "rating": "",
                        "cost_yuan": "",
                        "distance_m": poi.get("distance", ""),
                        "boundary_filter_status": "amap_around_current_context",
                        "supply_use_status": "needs_review_context_poi",
                        "output_status": "needs_review",
                    }
                )
                if len(collected) >= limit:
                    return collected
    return collected


def build_context_nodes(base_nodes: list[dict[str, Any]], context: dict[str, Any]) -> list[dict[str, Any]]:
    context_text = f"{context.get('keyword', '')}{context.get('matched_name', '')}"
    if "奥森" not in context_text and "奥林匹克森林" not in context_text:
        return []
    boundary = load_map_boundary_for_context(context) or load_known_osm_boundary(context) or estimated_boundary_from_points(load_map_context_pois(), context)
    bounds = boundary_bounds(boundary) if boundary else map_bounds_from_context(context)
    lon_span = bounds["max_lon"] - bounds["min_lon"]
    lat_span = bounds["max_lat"] - bounds["min_lat"]
    layout = [
        (-0.30, -0.18), (0.18, -0.28), (-0.02, 0.02),
        (-0.26, 0.26), (0.24, 0.20), (0.00, 0.34),
    ]
    nodes: list[dict[str, Any]] = []
    for index, node in enumerate(base_nodes):
        dx, dy = layout[index % len(layout)]
        lon = float(context.get("longitude") or 116.391365) + dx * lon_span
        lat = float(context.get("latitude") or 40.016194) + dy * lat_span
        nodes.append(
            {
                "node_id": node.get("node_id"),
                "node_name": f"{context.get('matched_name') or context.get('keyword') or '当前地点'}候选点 {index + 1}",
                "source_node_name": node.get("node_name"),
                "longitude": f"{lon:.6f}",
                "latitude": f"{lat:.6f}",
                "discussion_score": str(node.get("discussion_score") or ""),
                "area_sqm": "待测",
                "primary_positioning": "基于当前地图上下文生成的待复核候选点，需上传图纸/现场资料后确认。",
                "review_status": "待人工确认",
                "source": "context_layout_not_dwg",
                "output_status": "needs_review",
            }
        )
    return nodes


def amap_status(points: list[dict[str, Any]]) -> dict[str, Any]:
    load_local_env()
    has_key = bool(os.environ.get("AMAP_WEB_SERVICE_KEY"))
    return {
        "web_service_key_available": has_key,
        "key_location": ".env_or_environment" if has_key else "missing",
        "frontend_key_exposed": False,
        "source": "amap_web_service_static_map_proxy_and_existing_poi_csv",
        "point_count": len(points),
        "output_status": "needs_review",
    }


def save_amap_static_status(status: dict[str, Any]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    AMAP_STATIC_STATUS_FILE.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")


def load_amap_static_status() -> dict[str, Any]:
    if not AMAP_STATIC_STATUS_FILE.exists():
        return {
            "status": "not_checked_in_this_session",
            "output_status": "needs_review",
            "frontend_key_exposed": False,
        }
    try:
        return json.loads(AMAP_STATIC_STATUS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "status": "status_file_unreadable",
            "output_status": "needs_review",
            "frontend_key_exposed": False,
        }


def amap_center() -> tuple[str, str]:
    context = load_map_context()
    if context.get("longitude") and context.get("latitude"):
        return str(context["longitude"]), str(context["latitude"])
    rows = read_csv_rows(PROCESSED / "poi_supply_candidates_amap_boundary_filter.csv")
    for row in rows:
        if row.get("park_id") == "sample_olympic_forest" and row.get("center_longitude") and row.get("center_latitude"):
            return row["center_longitude"], row["center_latitude"]
    return "116.392159", "40.018635"


def normalize_zoom(value: Any, fallback: str = "15") -> str:
    zoom = safe_float(value)
    if zoom is None:
        zoom = safe_float(fallback) or 15
    return str(int(max(3, min(20, round(zoom)))))


def load_map_context() -> dict[str, Any]:
    if MAP_CONTEXT_FILE.exists():
        try:
            data = json.loads(MAP_CONTEXT_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
    return {
        "keyword": "北京奥林匹克森林公园",
        "longitude": "",
        "latitude": "",
        "radius_m": 1200,
        "source": "default_project_context",
        "output_status": "needs_review",
        "not_final": True,
    }


def save_map_context(row: dict[str, Any]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    MAP_CONTEXT_FILE.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def context_boundary_key(context: dict[str, Any]) -> str:
    keyword = str(context.get("keyword") or "").strip()
    matched = str(context.get("matched_name") or "").strip()
    lon = str(context.get("longitude") or "").strip()
    lat = str(context.get("latitude") or "").strip()
    return "|".join([keyword, matched, lon, lat])


def load_map_boundary_for_context(context: dict[str, Any]) -> dict[str, Any] | None:
    if not MAP_BOUNDARY_FILE.exists():
        return None
    try:
        data = json.loads(MAP_BOUNDARY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or data.get("context_key") != context_boundary_key(context):
        return None
    if not boundary_points(data):
        return None
    return data


def save_map_boundary(row: dict[str, Any] | None) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if row is None:
        MAP_BOUNDARY_FILE.write_text(json.dumps({}, ensure_ascii=False, indent=2), encoding="utf-8")
        return
    MAP_BOUNDARY_FILE.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")


def boundary_points(boundary: dict[str, Any] | None) -> list[dict[str, str]]:
    if not boundary:
        return []
    points = boundary.get("points_gcj02") or boundary.get("points") or []
    clean: list[dict[str, str]] = []
    for point in points:
        lon = safe_float(point.get("longitude") if isinstance(point, dict) else None)
        lat = safe_float(point.get("latitude") if isinstance(point, dict) else None)
        if lon is not None and lat is not None:
            clean.append({"longitude": f"{lon:.6f}", "latitude": f"{lat:.6f}"})
    return clean


def boundary_bounds(boundary: dict[str, Any]) -> dict[str, float]:
    points = boundary_points(boundary)
    lons = [float(point["longitude"]) for point in points]
    lats = [float(point["latitude"]) for point in points]
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)
    lon_pad = max((max_lon - min_lon) * 0.08, 0.0015)
    lat_pad = max((max_lat - min_lat) * 0.08, 0.0015)
    return {
        "min_lon": min_lon - lon_pad,
        "max_lon": max_lon + lon_pad,
        "min_lat": min_lat - lat_pad,
        "max_lat": max_lat + lat_pad,
    }


def static_zoom_for_bounds(bounds: dict[str, float]) -> str:
    lon_span = max(bounds["max_lon"] - bounds["min_lon"], 0.001)
    lat_span = max(bounds["max_lat"] - bounds["min_lat"], 0.001)
    span = max(lon_span, lat_span)
    if span > 0.09:
        return "12"
    if span > 0.045:
        return "13"
    if span > 0.022:
        return "14"
    if span > 0.011:
        return "15"
    return "16"


def convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    unique = sorted(set(points))
    if len(unique) <= 1:
        return unique

    def cross(origin: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
        return (a[0] - origin[0]) * (b[1] - origin[1]) - (a[1] - origin[1]) * (b[0] - origin[0])

    lower: list[tuple[float, float]] = []
    for point in unique:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper: list[tuple[float, float]] = []
    for point in reversed(unique):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]


def estimated_boundary_from_points(points: list[dict[str, Any]], context: dict[str, Any]) -> dict[str, Any] | None:
    coords: list[tuple[float, float]] = []
    center_lon = safe_float(context.get("longitude"))
    center_lat = safe_float(context.get("latitude"))
    if center_lon is not None and center_lat is not None:
        coords.append((center_lon, center_lat))
    for point in points:
        lon = safe_float(point.get("longitude"))
        lat = safe_float(point.get("latitude"))
        if lon is not None and lat is not None:
            coords.append((lon, lat))
    if len(coords) < 3:
        return None
    hull = convex_hull(coords)
    if len(hull) < 3:
        return None
    centroid_lon = sum(lon for lon, _ in hull) / len(hull)
    centroid_lat = sum(lat for _, lat in hull) / len(hull)
    expanded = []
    for lon, lat in hull:
        expanded.append((centroid_lon + (lon - centroid_lon) * 1.06, centroid_lat + (lat - centroid_lat) * 1.06))
    if expanded[0] != expanded[-1]:
        expanded.append(expanded[0])
    return {
        "context_key": context_boundary_key(context),
        "keyword": context.get("keyword", ""),
        "matched_name": context.get("matched_name", ""),
        "source": "AMap around POI convex hull",
        "source_detail": "Used only when no public polygon is available; this is a discussion envelope, not a park redline.",
        "boundary_status": "estimated_context_hull_needs_review",
        "coordinate_note": "GCJ-02 POI hull; not official boundary and not DWG geometry.",
        "output_status": "needs_review",
        "not_final": True,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "points_gcj02": [{"longitude": f"{lon:.6f}", "latitude": f"{lat:.6f}"} for lon, lat in expanded],
    }


def polygon_area_rough(ring: list[list[float]]) -> float:
    if len(ring) < 3:
        return 0.0
    area = 0.0
    for index, current in enumerate(ring):
        nxt = ring[(index + 1) % len(ring)]
        area += current[0] * nxt[1] - nxt[0] * current[1]
    return abs(area) / 2


def extract_largest_ring(geometry: dict[str, Any]) -> list[list[float]]:
    geom_type = geometry.get("type")
    coordinates = geometry.get("coordinates") or []
    rings: list[list[list[float]]] = []
    if geom_type == "Polygon":
        rings = [coordinates[0]] if coordinates else []
    elif geom_type == "MultiPolygon":
        rings = [polygon[0] for polygon in coordinates if polygon]
    candidates: list[list[list[float]]] = []
    for ring in rings:
        clean = []
        for point in ring:
            if isinstance(point, list) and len(point) >= 2:
                lon = safe_float(point[0])
                lat = safe_float(point[1])
                if lon is not None and lat is not None:
                    clean.append([lon, lat])
        if len(clean) >= 4:
            candidates.append(clean)
    if not candidates:
        return []
    return max(candidates, key=polygon_area_rough)


def downsample_ring(ring: list[list[float]], max_points: int = 180) -> list[list[float]]:
    if len(ring) <= max_points:
        return ring
    step = math.ceil(len(ring) / max_points)
    sampled = ring[::step]
    if sampled and sampled[0] != sampled[-1]:
        sampled.append(sampled[0])
    return sampled


def out_of_china(lon: float, lat: float) -> bool:
    return lon < 72.004 or lon > 137.8347 or lat < 0.8293 or lat > 55.8271


def transform_lat(x: float, y: float) -> float:
    ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(y / 12.0 * math.pi) + 320 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
    return ret


def transform_lon(x: float, y: float) -> float:
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
    return ret


def wgs84_to_gcj02(lon: float, lat: float) -> tuple[float, float]:
    if out_of_china(lon, lat):
        return lon, lat
    a = 6378245.0
    ee = 0.00669342162296594323
    dlat = transform_lat(lon - 105.0, lat - 35.0)
    dlon = transform_lon(lon - 105.0, lat - 35.0)
    radlat = lat / 180.0 * math.pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrt_magic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrt_magic) * math.pi)
    dlon = (dlon * 180.0) / (a / sqrt_magic * math.cos(radlat) * math.pi)
    return lon + dlon, lat + dlat


def boundary_from_ring(
    *,
    ring: list[list[float]],
    context: dict[str, Any],
    source: str,
    source_detail: str = "",
    boundary_status: str = "public_polygon_needs_review",
) -> dict[str, Any]:
    sampled = downsample_ring(ring)
    points_gcj02 = []
    for lon, lat in sampled:
        gcj_lon, gcj_lat = wgs84_to_gcj02(float(lon), float(lat))
        points_gcj02.append({"longitude": f"{gcj_lon:.6f}", "latitude": f"{gcj_lat:.6f}"})
    return {
        "context_key": context_boundary_key(context),
        "keyword": context.get("keyword", ""),
        "matched_name": context.get("matched_name", ""),
        "source": source,
        "source_detail": source_detail,
        "boundary_status": boundary_status,
        "coordinate_note": "OSM WGS84 polygon converted to GCJ-02 for AMap visual alignment; not an official redline.",
        "output_status": "needs_review",
        "not_final": True,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "points_gcj02": points_gcj02,
    }


def load_known_osm_boundary(context: dict[str, Any]) -> dict[str, Any] | None:
    if not KNOWN_OSM_BOUNDARY_FILE.exists():
        return None
    try:
        data = json.loads(KNOWN_OSM_BOUNDARY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    keyword = str(context.get("keyword") or "")
    matched = str(context.get("matched_name") or "")
    wanted = keyword + matched
    best: dict[str, Any] | None = None
    best_score = 0
    for feature in data.get("features") or []:
        props = feature.get("properties") or {}
        park_name = str(props.get("park_name") or "")
        park_id = str(props.get("park_id") or "")
        score = 0
        if park_name and (park_name in wanted or keyword in park_name or matched in park_name):
            score += 10
        if "奥森" in wanted and park_id == "sample_olympic_forest":
            score += 9
        if "奥林匹克森林" in wanted and park_id == "sample_olympic_forest":
            score += 9
        if "城市绿心" in wanted and park_id == "sample_city_green_heart":
            score += 9
        if score > best_score:
            best = feature
            best_score = score
    if not best:
        return None
    ring = extract_largest_ring(best.get("geometry") or {})
    if not ring:
        return None
    props = best.get("properties") or {}
    return boundary_from_ring(
        ring=ring,
        context=context,
        source="OpenStreetMap cached polygon",
        source_detail=str(props.get("source_url") or props.get("osm_id") or ""),
        boundary_status="cached_public_polygon_needs_review",
    )


def fetch_osm_boundary_for_context(context: dict[str, Any]) -> dict[str, Any] | None:
    base_name = str(context.get("matched_name") or context.get("keyword") or "").strip()
    keyword = str(context.get("keyword") or "").strip()
    address = str(context.get("address") or "").strip()
    queries = []
    for query in [
        f"{base_name} 北京",
        f"{keyword} 北京",
        base_name,
        keyword,
        f"{base_name} {address}",
    ]:
        query = query.strip()
        if query and query not in queries:
            queries.append(query)
    if not queries:
        return None
    headers = {"User-Agent": "p6-expert-dashboard/0.1 needs_review boundary lookup"}
    best_ring: list[list[float]] = []
    best_detail = ""
    best_area = 0.0
    try:
        with httpx.Client(timeout=12.0, headers=headers) as client:
            for query in queries:
                params = {
                    "format": "json",
                    "polygon_geojson": "1",
                    "limit": "5",
                    "q": query,
                }
                response = client.get("https://nominatim.openstreetmap.org/search", params=params)
                response.raise_for_status()
                results = response.json()
                for item in results if isinstance(results, list) else []:
                    geometry = item.get("geojson") or {}
                    ring = extract_largest_ring(geometry)
                    area = polygon_area_rough(ring)
                    if ring and area > best_area:
                        best_ring = ring
                        best_area = area
                        best_detail = str(item.get("display_name") or item.get("osm_id") or "")
                if best_ring:
                    break
    except Exception:
        return None
    if not best_ring:
        return None
    return boundary_from_ring(
        ring=best_ring,
        context=context,
        source="OpenStreetMap Nominatim live polygon",
        source_detail=best_detail,
        boundary_status="live_public_polygon_needs_review",
    )


def refresh_map_boundary(context: dict[str, Any]) -> dict[str, Any] | None:
    boundary = load_known_osm_boundary(context) or fetch_osm_boundary_for_context(context)
    save_map_boundary(boundary)
    return boundary


def map_bounds_from_context(context: dict[str, Any]) -> dict[str, float]:
    lon = float(context.get("longitude") or 116.391365)
    lat = float(context.get("latitude") or 40.016194)
    radius_m = float(context.get("radius_m") or 1200)
    lat_delta = max(radius_m / 111_000, 0.006)
    lon_delta = max(radius_m / (111_000 * max(0.2, abs(__import__("math").cos(__import__("math").radians(lat))))), 0.006)
    return {
        "min_lon": lon - lon_delta,
        "max_lon": lon + lon_delta,
        "min_lat": lat - lat_delta,
        "max_lat": lat + lat_delta,
    }


def poi_bounds(points: list[dict[str, Any]], context: dict[str, Any]) -> dict[str, float]:
    lons = [lon for p in points if (lon := safe_float(p.get("longitude"))) is not None]
    lats = [lat for p in points if (lat := safe_float(p.get("latitude"))) is not None]
    if len(lons) >= 3 and len(lats) >= 3:
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)
        lon_pad = max((max_lon - min_lon) * 0.15, 0.002)
        lat_pad = max((max_lat - min_lat) * 0.15, 0.002)
        return {
            "min_lon": min_lon - lon_pad,
            "max_lon": max_lon + lon_pad,
            "min_lat": min_lat - lat_pad,
            "max_lat": max_lat + lat_pad,
        }
    return map_bounds_from_context(context)


def boundary_polygon_from_bounds(bounds: dict[str, float]) -> list[dict[str, str]]:
    min_lon = bounds["min_lon"]
    max_lon = bounds["max_lon"]
    min_lat = bounds["min_lat"]
    max_lat = bounds["max_lat"]
    mid_lon = (min_lon + max_lon) / 2
    mid_lat = (min_lat + max_lat) / 2
    return [
        {"longitude": f"{min_lon:.6f}", "latitude": f"{mid_lat + (max_lat-min_lat)*0.34:.6f}"},
        {"longitude": f"{mid_lon - (max_lon-min_lon)*0.12:.6f}", "latitude": f"{max_lat:.6f}"},
        {"longitude": f"{max_lon:.6f}", "latitude": f"{mid_lat + (max_lat-min_lat)*0.22:.6f}"},
        {"longitude": f"{max_lon - (max_lon-min_lon)*0.08:.6f}", "latitude": f"{min_lat:.6f}"},
        {"longitude": f"{mid_lon - (max_lon-min_lon)*0.34:.6f}", "latitude": f"{min_lat + (max_lat-min_lat)*0.08:.6f}"},
        {"longitude": f"{min_lon:.6f}", "latitude": f"{mid_lat + (max_lat-min_lat)*0.34:.6f}"},
    ]


def load_cache() -> dict[str, Any]:
    if not CACHE_FILE.exists():
        return {}
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def load_feedback() -> list[dict[str, Any]]:
    if not FEEDBACK_FILE.exists():
        return []
    try:
        data = json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def save_feedback(rows: list[dict[str, Any]]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    FEEDBACK_FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def load_upload_index() -> list[dict[str, Any]]:
    built_in = []
    cad_dir = ROOT / "CAD图及其计划"
    if cad_dir.exists():
        for item in sorted(cad_dir.iterdir()):
            if item.is_file():
                built_in.append(
                    {
                        "upload_id": f"BUILTIN-{item.stem[:24]}",
                        "filename": item.name,
                        "source_type": "existing_project_material",
                        "category": guess_upload_category(item.name),
                        "size_bytes": item.stat().st_size,
                        "stored_path": str(item.relative_to(ROOT)),
                        "review_status": "待解析",
                        "created_at": datetime.fromtimestamp(item.stat().st_mtime).isoformat(timespec="seconds"),
                        "note": "来自 CAD图及其计划，仍需在网页流程中选择/解析/复核。",
                    }
                )
    uploaded = []
    if UPLOAD_INDEX_FILE.exists():
        try:
            data = json.loads(UPLOAD_INDEX_FILE.read_text(encoding="utf-8"))
            uploaded = data if isinstance(data, list) else []
        except json.JSONDecodeError:
            uploaded = []
    return built_in + uploaded


def save_upload_index(rows: list[dict[str, Any]]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    uploaded_only = [row for row in rows if not str(row.get("upload_id", "")).startswith("BUILTIN-")]
    UPLOAD_INDEX_FILE.write_text(json.dumps(uploaded_only, ensure_ascii=False, indent=2), encoding="utf-8")
    for row in uploaded_only:
        upsert_runtime_upload(row)


def guess_upload_category(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in {".dwg", ".dxf"}:
        return "CAD / 图纸"
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
        return "现场图片 / 位置图"
    if suffix in {".csv", ".xlsx", ".xls"}:
        return "数据表"
    if suffix in {".pdf", ".docx", ".doc", ".pptx", ".ppt"}:
        return "方案文件"
    return "其他资料"


def load_gate_inputs() -> list[dict[str, Any]]:
    if not GATE_INPUT_FILE.exists():
        return []
    try:
        data = json.loads(GATE_INPUT_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def save_gate_inputs(rows: list[dict[str, Any]]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    GATE_INPUT_FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    for row in rows:
        upsert_gate_input(row)


def load_upload_candidates() -> list[dict[str, Any]]:
    if not UPLOAD_CANDIDATES_FILE.exists():
        return []
    try:
        data = json.loads(UPLOAD_CANDIDATES_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def save_upload_candidates(rows: list[dict[str, Any]]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_CANDIDATES_FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    for row in rows:
        upsert_upload_candidate(row)


def find_upload(upload_id: str) -> dict[str, Any]:
    for row in load_upload_index():
        if row.get("upload_id") == upload_id:
            return row
    raise HTTPException(status_code=404, detail="upload not found")


def resolve_project_path(stored_path: str) -> Path:
    path = (ROOT / stored_path).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="stored path outside project") from exc
    return path


def extract_source_preview(path: Path, limit: int = 5000) -> str:
    suffix = path.suffix.lower()
    try:
        if suffix == ".pdf":
            import fitz  # type: ignore

            doc = fitz.open(path)
            parts = [page.get_text("text") for page in doc[: min(len(doc), 6)]]
            return "\n".join(parts)[:limit]
        if suffix in {".docx", ".pptx", ".xlsx"}:
            return extract_zip_text(path, limit)
        if suffix in {".csv", ".txt", ".md", ".json"}:
            return path.read_text(encoding="utf-8", errors="ignore")[:limit]
        if suffix in {".dwg", ".dxf"}:
            return (
                f"文件类型：{suffix.upper()}；文件大小：{path.stat().st_size} bytes。"
                "当前网页只登记图纸资料，不能直接生成 DWG 坐标、面积、图层或动线结论。"
            )
        if suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
            return f"图片资料：{path.name}；文件大小：{path.stat().st_size} bytes。需由专家说明图片位置和用途。"
    except Exception as exc:
        return f"资料预览失败：{type(exc).__name__}。仍可作为待复核上传资料登记。"
    return f"资料：{path.name}；文件大小：{path.stat().st_size} bytes。"


def extract_zip_text(path: Path, limit: int) -> str:
    chunks: list[str] = []
    with zipfile.ZipFile(path) as zf:
        names = [
            name
            for name in zf.namelist()
            if name.endswith(".xml") and any(part in name for part in ["word/", "ppt/slides/", "xl/sharedStrings", "xl/worksheets/"])
        ]
        for name in names[:24]:
            raw = zf.read(name).decode("utf-8", errors="ignore")
            text = re.sub(r"<[^>]+>", " ", raw)
            text = html.unescape(re.sub(r"\s+", " ", text)).strip()
            if text:
                chunks.append(text)
            if sum(len(item) for item in chunks) >= limit:
                break
    return "\n".join(chunks)[:limit]


def local_parse_candidate(upload: dict[str, Any], preview: str) -> dict[str, Any]:
    filename = upload.get("filename", "")
    category = upload.get("category", "")
    related_gates: list[str] = []
    text = f"{filename} {category} {preview}".lower()
    gate_keywords = {
        "geometry": ["dwg", "dxf", "cad", "图纸", "建筑", "平面", "geometry"],
        "visitor_flow": ["客流", "人次", "游客", "票务", "visitor"],
        "conversion_rate": ["转化", "消费", "购买", "conversion"],
        "revenue_cost": ["租金", "成本", "收入", "分成", "revenue", "cost"],
        "operation_authorization": ["授权", "审批", "消防", "运营", "authorization"],
    }
    for gate, keywords in gate_keywords.items():
        if any(keyword in text for keyword in keywords):
            related_gates.append(gate)
    if upload.get("target_gate") and upload["target_gate"] not in related_gates:
        related_gates.insert(0, upload["target_gate"])
    if not related_gates:
        related_gates = ["model_gate"]
    return {
        "candidate_type": "资料解析候选",
        "summary": f"{filename} 可进入待复核资料池；建议先关联 {', '.join(related_gates)}。",
        "related_nodes": [],
        "related_gates": related_gates,
        "suggested_actions": [
            "人工确认资料对应的园区、节点或缺口",
            "AI 只生成待复核候选，不自动写入最终结论",
            "如为 DWG/CAD，需另行转换为可信 DXF/GeoJSON/SVG/PDF 后再做几何判断",
        ],
    }


def save_cache(cache: dict[str, Any]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def node_context(payload: dict[str, Any], node_id: str | None) -> dict[str, Any]:
    node = next((item for item in payload["nodes"] if item.get("node_id") == node_id), None)
    if not node and payload["nodes"]:
        node = payload["nodes"][0]
    if not node:
        raise HTTPException(status_code=404, detail="node not found")
    feedback = [row for row in load_feedback() if row.get("node_id") == node.get("node_id")]
    return {
        "node": node,
        "p3_gates": payload["p3_gates"],
        "p2_gaps": payload["p2_gaps"],
        "expert_feedback": feedback[-8:],
    }


def make_prompt(payload: dict[str, Any], mode: str, node_id: str | None) -> str:
    nodes = payload["nodes"]
    selected = next((node for node in nodes if node.get("node_id") == node_id), None)
    gates = payload["p3_gates"]
    common_boundary = (
        "你是公园商业选址专家驾驶舱的 DeepSeek AI 草稿助手。"
        "只能输出 needs_review / not_final 的反馈草案解释。"
        "不得输出最终推荐、最终排序、收益预测、坐标、面积推断、DWG 几何结论或 checked 证据。"
        "必须说明为什么当前只是 feedback draft，并列出缺失数据。"
    )
    if mode == "priority":
        compact_nodes = [
            {
                "node_id": node.get("node_id"),
                "node_name": node.get("node_name"),
                "area_sqm": node.get("area_sqm"),
                "discussion_score": node.get("discussion_score"),
                "must_collect_before_final": node.get("must_collect_before_final"),
                "use_boundary": node.get("use_boundary"),
                "output_status": node.get("output_status"),
            }
            for node in nodes
        ]
        return (
            f"{common_boundary}\n"
            "请用中文解释多个节点的讨论优先级，只能叫讨论优先级，不能叫最终排名。\n"
            "输出 JSON，字段为 output_status, boundary_notice, priority_discussion, missing_data, partner_questions。\n"
            f"节点草案：{json.dumps(compact_nodes, ensure_ascii=False)}\n"
            f"P3 gate：{json.dumps(gates, ensure_ascii=False)}"
        )
    if not selected:
        raise HTTPException(status_code=404, detail="node_id not found")
    return (
        f"{common_boundary}\n"
        "请对当前节点做方案解释，并给合作方提问清单。"
        "输出 JSON，字段为 output_status, node_explanation, why_feedback_draft, missing_data, partner_questions, discussion_priority_note。\n"
        f"当前节点：{json.dumps(selected, ensure_ascii=False)}\n"
        f"P3 gate：{json.dumps(gates, ensure_ascii=False)}"
    )


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/dashboard")
def dashboard() -> dict[str, Any]:
    payload = load_dashboard()
    payload["expert_feedback"] = load_feedback()
    payload["api_contract"] = {
        **review_meta(
            source_hint="backend_response_schema_v2",
            evidence_hint="All conclusions remain needs_review / not_final",
            status_label="接口字段已统一 / 待前端逐步切换",
        ),
        "machine_status_field": "output_status",
        "human_status_field": "status_label",
        "score_field": "discussion_score_draft",
    }
    return payload


@app.get("/api/uploads")
def uploads() -> dict[str, Any]:
    items = load_upload_index()
    return {
        **review_meta(source_hint="uploaded_sources.json + runtime_uploads", status_label="资料池 / 待解析"),
        "count": len(items),
        "db_runtime_count": len(list_runtime_uploads()),
        "items": items,
        "accepted_categories": ["CAD / 图纸", "现场图片 / 位置图", "数据表", "方案文件", "其他资料"],
    }


@app.post("/api/uploads")
async def upload_source(
    file: UploadFile = File(...),
    category: str = Form("auto"),
    note: str = Form(""),
    target_gate: str = Form(""),
) -> dict[str, Any]:
    filename = Path(file.filename or "upload.bin").name
    if not filename:
        raise HTTPException(status_code=400, detail="filename is required")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(ch if ch.isalnum() or ch in ".-_()[] " else "_" for ch in filename)
    upload_id = f"UP-{stamp}-{len(load_upload_index()) + 1:03d}"
    target_dir = UPLOAD_DIR / stamp
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / safe_name
    content = await file.read()
    target_path.write_bytes(content)
    row = {
        "upload_id": upload_id,
        "filename": filename,
        "source_type": "web_upload",
        "category": guess_upload_category(filename) if category == "auto" else category,
        "size_bytes": len(content),
        "stored_path": str(target_path.relative_to(ROOT)),
        "review_status": "待 AI 解析",
        "target_gate": target_gate,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "note": note,
        "output_status": "needs_review",
        "not_final": True,
    }
    rows = load_upload_index()
    rows.append(row)
    save_upload_index(rows)
    return row


@app.post("/api/gate-inputs")
def save_gate_input(payload: GateInput) -> dict[str, Any]:
    rows = load_gate_inputs()
    row = {
        "input_id": f"GI-{len(rows) + 1:04d}",
        "calibration_domain": payload.calibration_domain,
        "note": payload.note,
        "owner": payload.owner or "",
        "due_date": payload.due_date or "",
        "source_hint": payload.source_hint or "",
        "output_status": "needs_review",
        "not_final": True,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    rows.append(row)
    save_gate_inputs(rows)
    return row


@app.get("/api/upload-candidates")
def upload_candidates() -> dict[str, Any]:
    items = load_upload_candidates()
    return {
        **review_meta(source_hint="upload_parse_candidates.json + upload_candidates", status_label="解析候选 / 待人工确认"),
        "count": len(items),
        "db_candidate_count": len(list_upload_candidates()),
        "items": items,
    }


@app.post("/api/uploads/{upload_id}/parse")
def parse_upload(upload_id: str) -> dict[str, Any]:
    upload = find_upload(upload_id)
    path = resolve_project_path(upload.get("stored_path", ""))
    if not path.exists():
        raise HTTPException(status_code=404, detail="stored file not found")
    preview = extract_source_preview(path)
    local_candidate = local_parse_candidate(upload, preview)
    nodes = [
        {"node_id": node.get("node_id"), "node_name": node.get("node_name"), "primary_positioning": node.get("primary_positioning")}
        for node in load_dashboard()["nodes"]
    ]
    prompt = (
        "你是 P6 专家网页的资料解析草稿助手。"
        "请把上传资料解析成待复核候选，不能输出最终推荐、最终排序、收益预测或 DWG 几何结论。"
        "输出 JSON：candidate_type, summary, related_nodes, related_gates, suggested_actions。"
        f"\n上传资料：{json.dumps(upload, ensure_ascii=False)}"
        f"\n资料预览：{preview[:3500]}"
        f"\n可选节点：{json.dumps(nodes, ensure_ascii=False)}"
    )
    generated_by = "local_rules"
    parsed = local_candidate
    try:
        content = run_deepseek_task(
            "LLM-026",
            [
                {"role": "system", "content": "你只输出 needs_review 的资料解析候选 JSON，不得升级为最终结论。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
        )
        parsed_json = json.loads(content)
        if isinstance(parsed_json, dict):
            parsed = {**local_candidate, **parsed_json}
            generated_by = "deepseek"
    except Exception as exc:
        parsed = {**local_candidate, "parse_warning": f"{type(exc).__name__}: {exc}"}
    rows = load_upload_candidates()
    existing_index = next((i for i, row in enumerate(rows) if row.get("upload_id") == upload_id), None)
    candidate = {
        "candidate_id": f"UC-{len(rows) + 1:04d}" if existing_index is None else rows[existing_index].get("candidate_id"),
        "upload_id": upload_id,
        "filename": upload.get("filename", ""),
        "category": upload.get("category", ""),
        "source_excerpt": preview[:900],
        "review_status": "待人工确认",
        "output_status": "needs_review",
        "not_final": True,
        "generated_by": generated_by,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        **parsed,
    }
    if existing_index is None:
        rows.append(candidate)
    else:
        rows[existing_index] = candidate
    save_upload_candidates(rows)
    return candidate


@app.post("/api/upload-candidates/{candidate_id}/confirm")
def confirm_upload_candidate(candidate_id: str, payload: ConfirmCandidateRequest) -> dict[str, Any]:
    candidates = load_upload_candidates()
    candidate = next((row for row in candidates if row.get("candidate_id") == candidate_id), None)
    if not candidate:
        raise HTTPException(status_code=404, detail="candidate not found")
    candidate["review_status"] = "已确认入池"
    candidate["reviewer_note"] = payload.reviewer_note
    candidate["confirmed_at"] = datetime.now().isoformat(timespec="seconds")
    candidate["output_status"] = "needs_review"
    candidate["not_final"] = True
    save_upload_candidates(candidates)

    gate_inputs = load_gate_inputs()
    for gate in candidate.get("related_gates", []) or ["model_gate"]:
        gate_inputs.append(
            {
                "input_id": f"GI-{len(gate_inputs) + 1:04d}",
                "calibration_domain": gate,
                "note": f"已确认资料入池：{candidate.get('filename')}。{payload.reviewer_note}".strip(),
                "owner": "网页确认",
                "due_date": "",
                "source_hint": candidate.get("upload_id", ""),
                "output_status": "needs_review",
                "not_final": True,
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
    save_gate_inputs(gate_inputs)

    uploads = load_upload_index()
    for row in uploads:
        if row.get("upload_id") == candidate.get("upload_id"):
            row["review_status"] = "已确认入池"
    save_upload_index(uploads)
    return candidate


@app.get("/api/amap/status")
def amap_proxy_status() -> dict[str, Any]:
    points = load_amap_supply()
    return {**amap_status(points), "static_map": load_amap_static_status(), "map_context": load_map_context()}


@app.post("/api/amap/context")
def update_amap_context(payload: MapContextRequest) -> dict[str, Any]:
    keyword = payload.keyword.strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="keyword is required")
    normalized_keyword = MAP_KEYWORD_ALIASES.get(keyword.lower(), keyword)
    load_local_env()
    key = os.environ.get("AMAP_WEB_SERVICE_KEY")
    if not key:
        raise HTTPException(status_code=400, detail="AMAP_WEB_SERVICE_KEY missing")
    if payload.longitude and payload.latitude:
        lon, lat = payload.longitude, payload.latitude
        poi = {"name": payload.matched_name or normalized_keyword, "address": payload.address or ""}
    else:
        params = {"key": key, "keywords": normalized_keyword, "city": "全国", "offset": "1", "page": "1", "extensions": "base"}
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get("https://restapi.amap.com/v3/place/text", params=params)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"amap place search failed: {type(exc).__name__}") from exc
        pois = data.get("pois") or []
        if not pois:
            suggestions = amap_input_tips(keyword, key)
            if suggestions:
                raise HTTPException(status_code=404, detail={"message": "amap returned no poi", "suggestions": suggestions})
            raise HTTPException(status_code=404, detail="amap returned no poi")
        poi = pois[0]
        location = poi.get("location", "")
        if "," not in location:
            raise HTTPException(status_code=502, detail="amap poi has no location")
        lon, lat = location.split(",", 1)
    context = {
        "keyword": keyword,
        "matched_name": poi.get("name", ""),
        "address": poi.get("address", ""),
        "longitude": lon,
        "latitude": lat,
        "radius_m": max(300, min(8000, int(payload.radius_m or 1200))),
        "source": "amap_web_service_place_text",
        "output_status": "needs_review",
        "not_final": True,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    save_map_context(context)
    try:
        save_map_context_pois(fetch_amap_around_pois(lon, lat, key))
    except Exception:
        save_map_context_pois([])
    refresh_map_boundary(context)
    if AMAP_STATIC_CACHE.exists():
        AMAP_STATIC_CACHE.unlink()
    save_amap_static_status(
        {
            "status": "context_updated_pending_static_map_refresh",
            "detail": f"地图目标已更新为：{context['matched_name'] or keyword}；刷新地图后重新请求高德静态图。",
            "output_status": "needs_review",
            "frontend_key_exposed": False,
            "checked_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    return context


def amap_input_tips(keyword: str, key: str) -> list[dict[str, Any]]:
    if not keyword.strip():
        return []
    raw_keyword = keyword.strip()
    normalized_keyword = MAP_KEYWORD_ALIASES.get(raw_keyword.lower(), raw_keyword)
    preferred_name = {
        "aosen": "奥林匹克森林公园",
        "as": "奥林匹克森林公园",
        "osen": "奥林匹克森林公园",
        "cygy": "朝阳公园",
        "chaoyang": "朝阳公园",
    }.get(raw_keyword.lower(), normalized_keyword)
    data: dict[str, Any] = {}
    exact_pois: list[dict[str, Any]] = []
    try:
        with httpx.Client(timeout=8.0) as client:
            response = client.get(
                "https://restapi.amap.com/v3/assistant/inputtips",
                params={"key": key, "keywords": normalized_keyword, "city": "全国", "datatype": "all"},
            )
            response.raise_for_status()
            data = response.json()
            place_keywords = [normalized_keyword]
            if preferred_name and preferred_name != normalized_keyword:
                place_keywords.append(preferred_name)
            for place_keyword in place_keywords:
                place_response = client.get(
                    "https://restapi.amap.com/v3/place/text",
                    params={
                        "key": key,
                        "keywords": place_keyword,
                        "city": "全国",
                        "offset": "3",
                        "page": "1",
                        "extensions": "base",
                    },
                )
                place_response.raise_for_status()
                exact_pois.extend(place_response.json().get("pois") or [])
    except Exception:
        if not data:
            return []
    tips = []
    def append_tip(name: str, district: str, address: str, location: str) -> None:
        lon, lat = ("", "")
        if isinstance(location, str) and "," in location:
            lon, lat = location.split(",", 1)
        tips.append(
            {
                "name": name,
                "district": district,
                "address": address,
                "longitude": lon,
                "latitude": lat,
                "output_status": "needs_review",
            }
        )

    for poi in exact_pois:
        append_tip(
            str(poi.get("name") or ""),
            str(poi.get("adname") or poi.get("pname") or ""),
            str(poi.get("address") or ""),
            str(poi.get("location") or ""),
        )
    for tip in data.get("tips") or []:
        append_tip(
            str(tip.get("name") or ""),
            str(tip.get("district") or ""),
            str(tip.get("address") or ""),
            str(tip.get("location") or ""),
        )
    def tip_rank(tip: dict[str, Any]) -> tuple[int, str]:
        name = str(tip.get("name") or "")
        district = str(tip.get("district") or "")
        score = 0
        if preferred_name and preferred_name in name:
            score -= 10
        if "北京市" in district:
            score -= 3
        if name == preferred_name:
            score -= 4
        if any(token in name for token in ("酒店", "停车场", "地铁站", "店", "安保队", "水电")):
            score += 5
        score += min(len(name), 40) // 10
        return score, name

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for tip in sorted([tip for tip in tips if tip.get("name")], key=tip_rank):
        key_tuple = (str(tip.get("name") or ""), str(tip.get("district") or ""), str(tip.get("address") or ""))
        if key_tuple in seen:
            continue
        seen.add(key_tuple)
        deduped.append(tip)
        if len(deduped) >= 8:
            break
    return deduped


@app.get("/api/amap/tips")
def amap_tips(q: str = "") -> dict[str, Any]:
    load_local_env()
    key = os.environ.get("AMAP_WEB_SERVICE_KEY")
    if not key:
        return {"output_status": "needs_review", "items": []}
    return {"output_status": "needs_review", "items": amap_input_tips(q, key)}


@app.get("/api/integration/status")
def integration_status() -> dict[str, Any]:
    payload = load_dashboard()
    points = load_amap_supply()
    deepseek_cache = load_cache()
    return {
        "output_status": "needs_review",
        "not_final": True,
        "items": [
            {
                "name": "P2/P4 节点与反馈 CSV",
                "kind": "local_csv",
                "status": "connected",
                "detail": f"已读取 {len(payload['nodes'])} 个节点、{len(payload['p4_feedback']['data_requests'])} 条合作方数据请求。",
            },
            {
                "name": "P3 gate CSV",
                "kind": "local_csv",
                "status": "connected",
                "detail": f"已读取 {len(payload['p3_gates'])} 个 gate；仅表示当前阻塞状态，不表示通过。",
            },
            {
                "name": "DeepSeek 后端代理",
                "kind": "backend_ai",
                "status": "configured" if os.environ.get("DEEPSEEK_API_KEY") else "missing_key",
                "detail": f"前端不接触 Key；已缓存 {len(deepseek_cache)} 条 AI 草稿，所有输出 needs_review / not_final。",
            },
            {
                "name": "AMap POI 历史抓取表",
                "kind": "local_csv_from_amap",
                "status": "connected",
                "detail": f"已读取 {len(points)} 条用于地图 POI 示意的候选点；不是最终园内供给结论。",
            },
            {
                "name": "AMap 静态地图后端代理",
                "kind": "backend_map",
                "status": load_amap_static_status().get("status", "not_checked_in_this_session"),
                "detail": load_amap_static_status().get("detail", "尚未在本会话检查静态图返回；失败时显示本地示意底图。"),
            },
        ],
    }


@app.get("/api/data/poi-candidates")
def api_poi_candidates(limit: int = 200) -> dict[str, Any]:
    import_existing_outputs()
    rows = [enrich_poi(row) for row in list_poi_candidates(limit=limit)]
    return {
        **review_meta(source_hint="SQLite poi_candidates", status_label="POI 候选 / 待复核"),
        "count": len(rows),
        "items": rows,
    }


@app.get("/api/data/gates")
def api_calibration_gates() -> dict[str, Any]:
    import_existing_outputs()
    rows = [enrich_gate(row) for row in list_calibration_gates()]
    return {
        **review_meta(source_hint="SQLite calibration_gates", status_label="P3 闸门 / 待闭合"),
        "count": len(rows),
        "items": rows,
    }


@app.get("/api/simulation/jobs")
def api_simulation_jobs() -> dict[str, Any]:
    items = list_jobs()
    return {
        **review_meta(source_hint="SQLite simulation_jobs", status_label="仿真任务 / 非最终"),
        "count": len(items),
        "items": items,
    }


@app.post("/api/simulation/jobs")
def api_create_simulation_job(request: SimulationJobRequest) -> dict[str, Any]:
    import_existing_outputs()
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    job_id = f"SIM-{stamp}-{abs(request.seed) % 100000:05d}"
    request_row = request.model_dump()
    create_job(job_id, request.scenario_name, request.seed, request.iterations, request_row)
    try:
        results = run_structural_simulation(
            list_poi_candidates(limit=10000),
            list_calibration_gates(),
            seed=request.seed,
            iterations=request.iterations,
        )
        complete_job(job_id, results)
    except Exception as exc:
        complete_job(job_id, [], status="failed", error_message=f"{type(exc).__name__}: {exc}")
        raise HTTPException(status_code=400, detail=f"simulation failed: {type(exc).__name__}: {exc}") from exc
    job = get_job(job_id)
    return {
        **review_meta(source_hint="SQLite simulation_jobs + simulation_results", status_label="干跑完成 / 待复核"),
        "job": job,
        "result_count": len(get_results(job_id)),
    }


@app.get("/api/simulation/jobs/{job_id}")
def api_get_simulation_job(job_id: str) -> dict[str, Any]:
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="simulation job not found")
    return {
        **review_meta(source_hint="SQLite simulation_jobs", status_label="仿真任务 / 非最终"),
        "job": job,
    }


@app.get("/api/simulation/jobs/{job_id}/results")
def api_get_simulation_results(job_id: str) -> dict[str, Any]:
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="simulation job not found")
    return {
        **review_meta(source_hint="SQLite simulation_results", status_label="干跑结果 / 待复核"),
        "job": job,
        "count": len(get_results(job_id)),
        "items": get_results(job_id),
    }


@app.get("/api/simulation/jobs/{job_id}/export")
def api_export_simulation_results(job_id: str, format: str = "json") -> Response:
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="simulation job not found")
    results = get_results(job_id)
    if format == "csv":
        fields = [
            "result_id",
            "job_id",
            "park_id",
            "category",
            "group_context",
            "boundary_filter_status",
            "source_hint",
            "candidate_count",
            "inside_osm_polygon_count",
            "missing_business_field_count",
            "blocked_gate_count",
            "why_blocked",
            "missing_required_fields",
            "next_data_needed",
            "output_status",
            "not_final",
            "status_label",
        ]
        lines = [",".join(fields)]
        for row in results:
            lines.append(",".join(json.dumps(row.get(field, ""), ensure_ascii=False) for field in fields))
        return Response(
            content="\n".join(lines) + "\n",
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{job_id}_results.csv"'},
        )
    return Response(
        content=json.dumps({"job": job, "items": results}, ensure_ascii=False, indent=2),
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{job_id}_results.json"'},
    )


@app.get("/api/amap/static-map")
def amap_static_map(lon: str | None = None, lat: str | None = None, zoom: str | None = None) -> Response:
    load_local_env()
    key = os.environ.get("AMAP_WEB_SERVICE_KEY")
    points = load_amap_supply()
    if not key:
        save_amap_static_status(
            {
                "status": "missing_key",
                "detail": "未检测到 AMAP_WEB_SERVICE_KEY，显示本地 POI 坐标示意。",
                "output_status": "needs_review",
                "frontend_key_exposed": False,
                "checked_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
        return Response(
            content=render_fallback_map_svg(points, "未检测到高德 Key，显示本地 POI 坐标示意"),
            media_type="image/svg+xml",
            headers={"Cache-Control": "no-store"},
        )
    context = load_map_context()
    default_lon, default_lat = amap_center()
    lon = lon or default_lon
    lat = lat or default_lat
    boundary = load_map_boundary_for_context(context) or load_known_osm_boundary(context)
    bounds = boundary_bounds(boundary) if boundary else poi_bounds(points, context)
    zoom_value = normalize_zoom(zoom, static_zoom_for_bounds(bounds))
    cache_key = re.sub(r"[^0-9A-Za-z_.-]", "_", f"{lon}_{lat}_{zoom_value}")
    tile_cache = AMAP_TILE_CACHE_DIR / f"{cache_key}.png"
    if tile_cache.exists():
        return Response(content=tile_cache.read_bytes(), media_type="image/png", headers={"Cache-Control": "no-store"})
    params = {
        "location": f"{lon},{lat}",
        "zoom": zoom_value,
        "size": "760*470",
        "scale": "2",
        "traffic": "0",
        "key": key,
    }
    try:
        with httpx.Client(timeout=8.0) as client:
            response = client.get("https://restapi.amap.com/v3/staticmap", params=params)
            response.raise_for_status()
    except Exception as exc:
        save_amap_static_status(
            {
                "status": "request_error",
                "detail": f"高德静态图请求异常：{type(exc).__name__}，显示本地 POI 坐标示意。",
                "output_status": "needs_review",
                "frontend_key_exposed": False,
                "checked_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
        if AMAP_STATIC_CACHE.exists():
            return Response(
                content=AMAP_STATIC_CACHE.read_bytes(),
                media_type="image/png",
                headers={"Cache-Control": "no-store"},
            )
        return Response(
            content=render_fallback_map_svg(points, f"高德静态图暂不可达：{type(exc).__name__}，显示本地 POI 坐标示意"),
            media_type="image/svg+xml",
            headers={"Cache-Control": "no-store"},
        )
    content_type = response.headers.get("content-type", "")
    if "image" not in content_type.lower():
        note = "高德静态图未返回图片，显示本地 POI 坐标示意"
        detail = note
        try:
            payload = response.json()
            info = payload.get("info") or payload.get("infocode")
            if info:
                note = f"高德静态图未返回图片：{info}，显示本地 POI 坐标示意"
                detail = f"高德返回非图片响应：{info}；前端继续使用本地示意底图。"
        except ValueError:
            pass
        save_amap_static_status(
            {
                "status": "non_image_response",
                "detail": detail,
                "output_status": "needs_review",
                "frontend_key_exposed": False,
                "checked_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
        return Response(
            content=render_fallback_map_svg(points, note),
            media_type="image/svg+xml",
            headers={"Cache-Control": "no-store"},
        )
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    AMAP_TILE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    AMAP_STATIC_CACHE.write_bytes(response.content)
    tile_cache.write_bytes(response.content)
    save_amap_static_status(
        {
            "status": "connected_image",
            "detail": "高德静态地图返回图片，已通过后端代理缓存；前端未暴露 Key。",
            "output_status": "needs_review",
            "frontend_key_exposed": False,
            "checked_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    return Response(content=response.content, media_type=content_type, headers={"Cache-Control": "no-store"})


def render_fallback_map_svg(points: list[dict[str, Any]], note: str) -> str:
    valid = []
    for point in points:
        try:
            valid.append(
                {
                    "lon": float(point.get("longitude", "")),
                    "lat": float(point.get("latitude", "")),
                    "inside": point.get("boundary_filter_status") == "inside_osm_polygon",
                }
            )
        except ValueError:
            continue
    if valid:
        min_lon = min(item["lon"] for item in valid)
        max_lon = max(item["lon"] for item in valid)
        min_lat = min(item["lat"] for item in valid)
        max_lat = max(item["lat"] for item in valid)
    else:
        min_lon, max_lon, min_lat, max_lat = 116.37, 116.41, 40.00, 40.04
    lon_span = max(max_lon - min_lon, 0.01)
    lat_span = max(max_lat - min_lat, 0.01)
    dots = []
    for item in valid[:60]:
        x = 52 + ((item["lon"] - min_lon) / lon_span) * 656
        y = 410 - ((item["lat"] - min_lat) / lat_span) * 338
        color = "#0f8f82" if item["inside"] else "#f5a623"
        dots.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.8" fill="{color}" stroke="#fff" '
            f'stroke-width="1.8" opacity="0.9" />'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="760" height="470" viewBox="0 0 760 470">
  <defs>
    <linearGradient id="land" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#e3efeb"/>
      <stop offset="1" stop-color="#f5f8f5"/>
    </linearGradient>
    <linearGradient id="lake" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#bdddd9"/>
      <stop offset="1" stop-color="#e3f0ed"/>
    </linearGradient>
    <pattern id="grid" width="38" height="38" patternUnits="userSpaceOnUse">
      <path d="M 38 0 L 0 0 0 38" fill="none" stroke="#c9dad6" stroke-width="1"/>
    </pattern>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#15443f" flood-opacity=".14"/>
    </filter>
  </defs>
  <rect width="760" height="470" fill="url(#land)"/>
  <rect width="760" height="470" fill="url(#grid)" opacity="0.32"/>
  <path d="M55,98 C170,44 297,48 424,74 C540,98 642,76 738,38" fill="none" stroke="#d7dfdc" stroke-width="24" opacity="0.7"/>
  <path d="M49,101 C169,55 295,57 420,84 C535,108 642,86 738,51" fill="none" stroke="#fff" stroke-width="8" opacity="0.88"/>
  <path d="M35,362 C138,291 238,262 360,255 C495,247 593,207 735,116" fill="none" stroke="#d4dfdc" stroke-width="24" opacity="0.72"/>
  <path d="M35,362 C138,291 238,262 360,255 C495,247 593,207 735,116" fill="none" stroke="#fff" stroke-width="8" opacity="0.9"/>
  <path d="M132,318 C178,214 270,180 355,218 C446,259 512,176 632,202 C710,219 726,306 660,357 C572,426 456,363 358,379 C244,397 154,384 132,318Z" fill="url(#lake)" stroke="#9fc9c3" stroke-width="2.5" opacity="0.9"/>
  <path d="M190,146 C232,116 298,116 355,141 C412,166 470,151 520,128" fill="none" stroke="#c4d7d2" stroke-width="10" opacity=".65"/>
  <path d="M192,147 C238,124 298,124 351,148 C407,172 469,158 520,134" fill="none" stroke="#fff" stroke-width="4" opacity=".9"/>
  <path d="M456,420 C470,335 510,278 580,238 C625,213 662,181 702,138" fill="none" stroke="#c4d7d2" stroke-width="10" opacity=".55"/>
  <path d="M456,420 C470,335 510,278 580,238 C625,213 662,181 702,138" fill="none" stroke="#fff" stroke-width="4" opacity=".8"/>
  <g opacity=".28">
    <circle cx="106" cy="185" r="40" fill="#79b68b"/>
    <circle cx="92" cy="238" r="25" fill="#79b68b"/>
    <circle cx="640" cy="308" r="34" fill="#79b68b"/>
    <circle cx="612" cy="356" r="24" fill="#79b68b"/>
    <circle cx="307" cy="112" r="28" fill="#79b68b"/>
  </g>
  <g filter="url(#shadow)">
  {''.join(dots)}
  </g>
</svg>"""


@app.post("/api/ai/review")
def ai_review(request: AIRequest) -> dict[str, Any]:
    mode = request.mode if request.mode in {"node", "priority"} else "node"
    cache_key = f"{mode}:{request.node_id or 'all'}"
    cache = load_cache()
    if cache_key in cache:
        return {**cache[cache_key], "cached": True}

    payload = load_dashboard()
    prompt = make_prompt(payload, mode, request.node_id)
    try:
        content = run_deepseek_task(
            "LLM-026",
            [
                {"role": "system", "content": "You return concise valid JSON only. Keep all conclusions not_final."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
        )
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = {"output_status": "needs_review", "raw_text": content}
        parsed.setdefault("output_status", "needs_review")
        parsed["not_final"] = True
        parsed["generated_by"] = "deepseek"
    except Exception as exc:
        parsed = {
            "output_status": "needs_review",
            "not_final": True,
            "generated_by": "local_fallback",
            "error": f"{type(exc).__name__}: {exc}",
            "why_feedback_draft": "DeepSeek 调用不可用或超时；当前仍只能使用本地 CSV 的 feedback draft 数据。",
            "missing_data": ["真实客流", "转化率", "收益成本", "运营授权", "DWG 可信转换产物"],
        }
    cache[cache_key] = parsed
    save_cache(cache)
    return {**parsed, "cached": False}


@app.post("/api/ai/chat")
def ai_chat(request: ChatRequest) -> dict[str, Any]:
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    payload = load_dashboard()
    context = node_context(payload, request.node_id)
    prompt = (
        "你是公园商业选址专家驾驶舱里的 DeepSeek 对话助手，像网页版对话一样连续协助专家。"
        "你可以读取当前节点、专家意见、位置/图片文字说明、P3 gate 和 P4 feedback draft。"
        "你的任务是：解释当前方案、追问缺失数据、把专家意见转为模型修改建议、提示哪些字段需要补数。"
        "硬边界：所有输出只能是 needs_review / not_final；不得给最终推荐、最终排序、收益预测、坐标、面积推断、DWG几何结论或 checked 证据。"
        "如果用户提到未来会给图或位置资料，只能说明应如何登记、如何进入待复核假设池。"
        "请用中文回答，简洁但可操作，最后给出 3-6 条下一步提问或待补数据。"
        f"\n当前上下文：{json.dumps(context, ensure_ascii=False)}"
        f"\n位置/图片文字说明：{request.position_note or ''}"
        f"\n本轮上传/关联资料：{json.dumps(request.upload_refs, ensure_ascii=False)}"
        f"\n历史对话：{json.dumps(request.history[-8:], ensure_ascii=False)}"
        f"\n专家/用户本轮输入：{message}"
    )
    try:
        content = run_deepseek_task(
            "LLM-026",
            [
                {"role": "system", "content": "你只输出 needs_review/not_final 的专家对话草稿，不得升级为最终结论。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.15,
        )
        return {
            "output_status": "needs_review",
            "not_final": True,
            "generated_by": "deepseek",
            "message": content,
        }
    except Exception as exc:
        return {
            "output_status": "needs_review",
            "not_final": True,
            "generated_by": "local_fallback",
            "message": (
                "DeepSeek 当前不可用或超时。当前意见仍可先登记为专家反馈，"
                "但不能进入 checked/final。下一步请补充：真实客流、转化率、收益成本、运营授权、DWG可信转换产物。"
            ),
            "error": f"{type(exc).__name__}: {exc}",
        }


@app.post("/api/expert-feedback")
def save_expert_feedback(feedback: ExpertFeedback) -> dict[str, Any]:
    if not feedback.comment.strip():
        raise HTTPException(status_code=400, detail="comment is required")
    rows = load_feedback()
    row = {
        "feedback_id": f"FB-{len(rows) + 1:04d}",
        "node_id": feedback.node_id,
        "expert_name": feedback.expert_name or "专家",
        "comment": feedback.comment,
        "position_note": feedback.position_note or "",
        "data_hint": feedback.data_hint or "",
        "output_status": "needs_review",
        "not_final": True,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    rows.append(row)
    save_feedback(rows)
    return row
