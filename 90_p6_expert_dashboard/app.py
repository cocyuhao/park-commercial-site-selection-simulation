from __future__ import annotations

import ast
import csv
import html
import json
import math
import os
import re
import subprocess
import zipfile
from collections import Counter
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
AI_SESSIONS_FILE = CACHE_DIR / "ai_sessions.json"
UPLOAD_DIR = CACHE_DIR / "uploaded_sources"
UPLOAD_INDEX_FILE = CACHE_DIR / "uploaded_sources.json"
UPLOAD_CANDIDATES_FILE = CACHE_DIR / "upload_parse_candidates.json"
GATE_INPUT_FILE = CACHE_DIR / "gate_inputs.json"
NODE_DRAFTS_FILE = CACHE_DIR / "node_drafts.json"
SIMULATION_OBJECTS_FILE = CACHE_DIR / "simulation_objects.json"
SIMULATION_TASK_FILE = CACHE_DIR / "simulation_task_entry.json"
SIMULATION_FEATURE_CONTROL_FILE = CACHE_DIR / "simulation_feature_derivative_controls.json"
MAP_CONTEXT_FILE = CACHE_DIR / "map_context.json"
MAP_CONTEXT_POI_FILE = CACHE_DIR / "map_context_pois.json"
MAP_BOUNDARY_FILE = CACHE_DIR / "map_boundary.json"
AMAP_STATIC_CACHE = CACHE_DIR / "amap_static_map.png"
AMAP_TILE_CACHE_DIR = CACHE_DIR / "amap_static_tiles"
AMAP_STATIC_STATUS_FILE = CACHE_DIR / "amap_static_map_status.json"
REPORT_DIR = ROOT / "80_delivery"
QUALITY_DIR = ROOT / "40_quality_evidence"
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
PERSONA_STATE_CSV = PROCESSED / "p2_persona_state_profiles_20260604.csv"
BEHAVIOR_PROGRAM_CSV = PROCESSED / "p2_behavior_program_templates_20260604.csv"
CHOICE_PROBABILITY_CSV = PROCESSED / "choice_probability_from_p2_p4_20260604.csv"
VALIDATION_TARGET_CSV = PROCESSED / "simulation_validation_target_from_p2_20260604.csv"
FEATURE_DERIVATIVE_CSV = PROCESSED / "person_simulation_feature_derivatives_1000_20260604.csv"
REAL_CALIBRATION_CSV = PROCESSED / "osen_real_calibration_inputs_20260607.csv"
REAL_CALIBRATION_JSON = QUALITY_DIR / "osen_real_calibration_inputs_20260607.json"
REAL_CALIBRATION_SUPPLEMENT_FILE = CACHE_DIR / "real_calibration_supplements.json"
REAL_CALIBRATION_BUILD_SCRIPT = ROOT / "30_extraction" / "scripts" / "build_osen_real_calibration_inputs_20260607.py"
SRC_DIR = ROOT / "60_model" / "src"
DB_DIR = ROOT / "60_model" / "db"
SIM_DIR = ROOT / "60_model" / "simulation"
DELIVERY_SCRIPT_DIR = ROOT / "80_delivery" / "scripts"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(DB_DIR) not in sys.path:
    sys.path.insert(0, str(DB_DIR))
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))
if str(DELIVERY_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(DELIVERY_SCRIPT_DIR))

from llm_router import load_local_env, run_deepseek_task  # noqa: E402
from engine import run_structural_simulation  # noqa: E402
from demand_gap import (  # noqa: E402
    attach_gap_to_nodes,
    build_gap_report,
    build_supply_profile,
    build_tgi_profile,
    calculate_supply_gap,
    parse_uploaded_visitor_sources,
    report_to_markdown,
    write_report_files,
)
from build_osen_business_decision_report_20260607 import build_outputs as build_osen_business_report_outputs  # noqa: E402
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
    session_id: str | None = None
    project_id: str | None = None
    project_name: str | None = None
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


class UploadActionRequest(BaseModel):
    action: str


class NodeDraftRequest(BaseModel):
    node_name: str
    location_description: str = ""
    business_direction: str = ""
    area_sqm: str = ""
    note: str = ""
    enabled: bool = True


class ChatSessionCreateRequest(BaseModel):
    project_id: str | None = None
    project_name: str | None = None
    title: str | None = None
    node_id: str | None = None


class ChatReportRequest(BaseModel):
    instruction: str | None = None


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


class SimulationObjectRequest(BaseModel):
    object_type: str
    title: str
    summary: str = ""
    linked_id: str | None = None
    status: str = "needs_review"
    adoption_status: str = "暂未采用"
    priority_label: str = "复核后判断"
    source_refs: list[str] = []
    missing_inputs: list[str] = []
    specific_advice: list[str] = []


class SimulationObjectActionRequest(BaseModel):
    action: str
    note: str = ""
    title: str | None = None
    summary: str | None = None
    linked_id: str | None = None
    priority_label: str | None = None
    source_refs: list[str] | None = None
    missing_inputs: list[str] | None = None
    specific_advice: list[str] | None = None


class RealCalibrationSupplementRequest(BaseModel):
    dimension: str = "user_supplement"
    indicator_name: str
    segment: str = "待确认范围"
    period: str = "待确认时期"
    value: str
    unit: str = ""
    source_strength: str = "local_user_supplement"
    simulation_use: str = "作为用户补充校准输入进入预检和报告，待人工复核后用于仿真参数。"
    cannot_claim: str = "不能直接写成最终收益、最终排名、真实转化或投资定案。"
    next_data_needed: str = "复核来源文件、采集口径、时段、样本量、复核人和可追溯证据。"
    source_file: str = "用户补充资料"
    source_page_or_slide: str = "user_supplement"
    raw_text_snippet: str = ""
    note: str = ""


class RealCalibrationSupplementPatchRequest(BaseModel):
    dimension: str | None = None
    indicator_name: str | None = None
    segment: str | None = None
    period: str | None = None
    value: str | None = None
    unit: str | None = None
    source_strength: str | None = None
    simulation_use: str | None = None
    cannot_claim: str | None = None
    next_data_needed: str | None = None
    source_file: str | None = None
    source_page_or_slide: str | None = None
    raw_text_snippet: str | None = None
    note: str | None = None


class FeatureDerivativeActionRequest(BaseModel):
    action: str
    note: str = ""


class SimulationTaskPreflightRequest(BaseModel):
    task_name: str = "人物仿真预演"
    selected_object_ids: list[str] = []
    scenario_note: str = ""
    run_mode: str = "preflight"


@app.on_event("startup")
def prepare_local_database() -> None:
    import_existing_outputs()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def amap_get_json(url: str, params: dict[str, Any], *, timeout: float = 4.0, retries: int = 1) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            if data.get("status") == "0":
                raise RuntimeError(data.get("info") or "amap api returned status=0")
            return data
        except Exception as exc:
            last_error = exc
            if attempt >= retries:
                break
    raise HTTPException(
        status_code=502,
        detail={
            "message": "高德接口暂时连接失败，请稍后重试或改用地图直接搜索。",
            "error_type": type(last_error).__name__ if last_error else "UnknownError",
        },
    ) from last_error


def map_search_error_detail() -> dict[str, Any]:
    return {
        "message": "地图检索暂时失败，可以稍后重试，或先手动输入项目位置。",
        "output_status": "needs_review",
        "not_final": True,
    }


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


def split_semicolon(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    if not text:
        return []
    return [item.strip() for item in re.split(r"[;；]\s*", text) if item.strip()]


def object_type_label(object_type: str) -> str:
    labels = {
        "persona_state": "人群状态画像",
        "behavior_program": "行为程序",
        "choice_probability": "选择概率候选",
        "simulation_validation_target": "仿真验证目标",
    }
    return labels.get(object_type, object_type or "仿真对象")


def normalize_adoption_status(value: Any) -> str:
    text = str(value or "").strip()
    if text in {"已采用", "已放弃", "暂未采用"}:
        return text
    if text in {"use", "used", "enabled"}:
        return "已采用"
    if text in {"discard", "discarded", "disabled"}:
        return "已放弃"
    return "暂未采用"


def normalize_simulation_object(row: dict[str, Any], index: int = 0) -> dict[str, Any]:
    object_type = str(row.get("object_type") or "").strip()
    allowed_types = {"persona_state", "behavior_program", "choice_probability", "simulation_validation_target"}
    if object_type not in allowed_types:
        object_type = "choice_probability"
    linked_id = str(
        row.get("linked_id")
        or row.get("state_profile_id")
        or row.get("program_id")
        or row.get("choice_id")
        or row.get("target_id")
        or ""
    ).strip()
    object_id = str(row.get("object_id") or f"SIMOBJ-{index + 1:04d}").strip()
    title = str(
        row.get("title")
        or row.get("persona_name")
        or row.get("program_name")
        or row.get("target_name")
        or linked_id
        or object_type_label(object_type)
    ).strip()
    summary = str(
        row.get("summary")
        or row.get("primary_consumption_needs")
        or row.get("actions")
        or row.get("plain_language_explanation")
        or row.get("acceptance_rule")
        or ""
    ).strip()
    now = datetime.now().isoformat(timespec="seconds")
    return {
        "object_id": object_id,
        "object_type": object_type,
        "type_label": object_type_label(object_type),
        "title": title,
        "summary": summary,
        "linked_id": linked_id,
        "status": str(row.get("status") or row.get("probability_status") or "needs_review"),
        "status_label": "待复核",
        "adoption_status": normalize_adoption_status(row.get("adoption_status")),
        "priority_label": str(row.get("priority_label") or "复核后判断"),
        "source_refs": split_semicolon(row.get("source_refs")),
        "missing_inputs": split_semicolon(row.get("missing_inputs")),
        "specific_advice": split_semicolon(row.get("specific_advice") or row.get("review_notes")),
        "review_notes": split_semicolon(row.get("review_notes")),
        "user_locked": str(row.get("user_locked", "false")).lower() in {"true", "1", "yes"} or bool(row.get("user_locked") is True),
        "created_at": str(row.get("created_at") or now),
        "updated_at": str(row.get("updated_at") or now),
        "output_status": "needs_review",
        "not_final": True,
    }


def seed_choice_probability_objects() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(read_csv_rows(CHOICE_PROBABILITY_CSV)):
        node = row.get("node_id") or "待定节点"
        persona = row.get("persona_id") or "待定人群"
        title = f"{persona} 在 {node} 的消费选择候选"
        rows.append(
            normalize_simulation_object(
                {
                    **row,
                    "object_id": f"SIMOBJ-CP-{index + 1:03d}",
                    "object_type": "choice_probability",
                    "linked_id": row.get("choice_id"),
                    "title": title,
                    "summary": row.get("plain_language_explanation", ""),
                    "source_refs": "70_outputs/processed_tables/choice_probability_from_p2_p4_20260604.csv;10_research/boss_method_materials_20260604/method_absorption_landing_register_20260604.md",
                    "adoption_status": "暂未采用",
                },
                index,
            )
        )
    return rows


def seed_persona_state_objects() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(read_csv_rows(PERSONA_STATE_CSV)):
        persona = row.get("persona_name") or row.get("persona_id") or "待定人群"
        summary = (
            f"{row.get('visit_purpose', '')}；主要需求："
            f"{row.get('primary_service_needs', '')}；消费线索：{row.get('primary_consumption_needs', '')}"
        ).strip("；")
        rows.append(
            normalize_simulation_object(
                {
                    **row,
                    "object_id": f"SIMOBJ-PS-{index + 1:03d}",
                    "object_type": "persona_state",
                    "linked_id": row.get("state_profile_id") or row.get("persona_id"),
                    "title": f"{persona}状态画像",
                    "summary": summary,
                    "source_refs": "70_outputs/processed_tables/p2_persona_state_profiles_20260604.csv;10_research/boss_method_materials_20260604/boss_model_inventory_20260604.md;10_research/boss_method_materials_20260604/deepseek_constrained_simulation_design_20260604.md",
                    "missing_inputs": row.get("calibration_status", ""),
                    "specific_advice": "先确认真实人群占比；再校准时间压力、绕行容忍和排队容忍；未复核前不要把画像当最终客群结论",
                    "priority_label": "先确认状态",
                    "adoption_status": "暂未采用",
                },
                index,
            )
        )
    return rows


def seed_behavior_program_objects(start_index: int = 0) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for offset, row in enumerate(read_csv_rows(BEHAVIOR_PROGRAM_CSV)):
        persona = row.get("persona_name") or "待定人群"
        summary = (
            f"{row.get('trigger_condition', '')}：{row.get('actions', '')}；"
            f"放弃/外溢条件：{row.get('abandon_or_spillover_condition', '')}"
        ).strip("；")
        rows.append(
            normalize_simulation_object(
                {
                    **row,
                    "object_id": f"SIMOBJ-BP-{offset + 1:03d}",
                    "object_type": "behavior_program",
                    "linked_id": row.get("program_id"),
                    "title": f"{persona} · {row.get('program_name') or '行为程序'}",
                    "summary": summary,
                    "source_refs": "70_outputs/processed_tables/p2_behavior_program_templates_20260604.csv;10_research/boss_method_materials_20260604/deepseek_constrained_simulation_design_20260604.md;10_research/boss_method_materials_20260604/method_absorption_landing_register_20260604.md",
                    "missing_inputs": row.get("calibration_status", ""),
                    "specific_advice": "把触发条件、动作序列、放弃条件和概率输入逐项复核；采用后再进入本地仿真预演",
                    "priority_label": "先复核行为链",
                    "adoption_status": "暂未采用",
                },
                start_index + offset,
            )
        )
    return rows


def seed_validation_target_objects(start_index: int = 0) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for offset, row in enumerate(read_csv_rows(VALIDATION_TARGET_CSV)):
        summary = row.get("acceptance_rule", "")
        rows.append(
            normalize_simulation_object(
                {
                    **row,
                    "object_id": f"SIMOBJ-VT-{offset + 1:03d}",
                    "object_type": "simulation_validation_target",
                    "linked_id": row.get("target_id"),
                    "title": row.get("target_name"),
                    "summary": summary,
                    "source_refs": "70_outputs/processed_tables/simulation_validation_target_from_p2_20260604.csv;10_research/boss_method_materials_20260604/modern_practical_method_rescreen_20260604.md",
                    "specific_advice": "先锁定参考数据口径再运行校准；通过前不得宣称完整仿真；人工确认验收口径",
                    "priority_label": "校准前置条件",
                    "adoption_status": "暂未采用",
                },
                start_index + offset,
            )
        )
    return rows


def seeded_simulation_objects() -> list[dict[str, Any]]:
    rows = seed_persona_state_objects()
    rows.extend(seed_behavior_program_objects(len(rows)))
    rows.extend(seed_choice_probability_objects())
    rows.extend(seed_validation_target_objects(len(rows)))
    return rows


def load_simulation_objects() -> list[dict[str, Any]]:
    if SIMULATION_OBJECTS_FILE.exists():
        try:
            data = json.loads(SIMULATION_OBJECTS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                rows = [normalize_simulation_object(row, index) for index, row in enumerate(data)]
                existing_keys = {
                    (str(row.get("object_type") or ""), str(row.get("linked_id") or ""))
                    for row in rows
                }
                changed = False
                for seed in seeded_simulation_objects():
                    key = (str(seed.get("object_type") or ""), str(seed.get("linked_id") or ""))
                    if key[0] and key[1] and key not in existing_keys:
                        rows.append(seed)
                        existing_keys.add(key)
                        changed = True
                if changed:
                    save_simulation_objects(rows)
                return rows
        except json.JSONDecodeError:
            pass
    rows = seeded_simulation_objects()
    save_simulation_objects(rows)
    return rows


def save_simulation_objects(rows: list[dict[str, Any]]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    normalized = [normalize_simulation_object(row, index) for index, row in enumerate(rows)]
    SIMULATION_OBJECTS_FILE.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")


def next_simulation_object_id(rows: list[dict[str, Any]], object_type: str) -> str:
    prefixes = {
        "persona_state": "SIMOBJ-PS",
        "behavior_program": "SIMOBJ-BP",
        "choice_probability": "SIMOBJ-CP",
        "simulation_validation_target": "SIMOBJ-VT",
    }
    prefix = prefixes.get(object_type, "SIMOBJ")
    used = []
    for row in rows:
        object_id = str(row.get("object_id") or "")
        match = re.search(r"(\d+)$", object_id)
        if object_id.startswith(prefix) and match:
            used.append(int(match.group(1)))
    return f"{prefix}-{(max(used) if used else 0) + 1:03d}"


SIMULATION_TASK_OBJECT_TYPES = [
    "persona_state",
    "behavior_program",
    "choice_probability",
    "simulation_validation_target",
]


def read_json_file(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback


def line_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        return sum(1 for _ in f)


def compact_simulation_object(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "object_id": row.get("object_id", ""),
        "object_type": row.get("object_type", ""),
        "type_label": row.get("type_label", object_type_label(str(row.get("object_type") or ""))),
        "title": row.get("title", ""),
        "summary": row.get("summary", ""),
        "linked_id": row.get("linked_id", ""),
        "adoption_status": row.get("adoption_status", "暂未采用"),
        "priority_label": row.get("priority_label", "复核后判断"),
        "missing_inputs": row.get("missing_inputs", []),
        "specific_advice": row.get("specific_advice", []),
        "user_locked": bool(row.get("user_locked")),
        "output_status": "needs_review",
        "not_final": True,
    }


def load_simulation_task_entry(objects: list[dict[str, Any]]) -> dict[str, Any]:
    data = read_json_file(SIMULATION_TASK_FILE, {})
    if not isinstance(data, dict):
        data = {}
    known_ids = {str(row.get("object_id") or "") for row in objects}
    selected = [
        str(item)
        for item in data.get("selected_object_ids", [])
        if str(item) in known_ids
    ]
    if not selected:
        selected = [
            str(row.get("object_id"))
            for row in objects
            if row.get("adoption_status") == "已采用" and row.get("object_id")
        ]
    return {
        "task_name": str(data.get("task_name") or "人物仿真预演"),
        "selected_object_ids": selected,
        "scenario_note": str(data.get("scenario_note") or ""),
        "run_mode": str(data.get("run_mode") or "preflight"),
        "updated_at": str(data.get("updated_at") or ""),
    }


def save_simulation_task_entry(entry: dict[str, Any]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    SIMULATION_TASK_FILE.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")


def load_feature_derivative_controls() -> dict[str, Any]:
    data = read_json_file(SIMULATION_FEATURE_CONTROL_FILE, {})
    return data if isinstance(data, dict) else {}


def save_feature_derivative_controls(controls: dict[str, Any]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    SIMULATION_FEATURE_CONTROL_FILE.write_text(json.dumps(controls, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_feature_derivative(row: dict[str, Any], controls: dict[str, Any]) -> dict[str, Any]:
    derivative_id = str(row.get("derivative_id") or "")
    control = controls.get(derivative_id, {}) if isinstance(controls.get(derivative_id, {}), dict) else {}
    adoption_status = str(control.get("adoption_status") or "暂未采用")
    return {
        "derivative_id": derivative_id,
        "title": f"{row.get('persona_name', '人群')} · {row.get('time_band_name', '时段')} · {row.get('demand_trigger_name', '需求')}",
        "persona_id": row.get("persona_id", ""),
        "persona_name": row.get("persona_name", ""),
        "persona_core_need": row.get("persona_core_need", ""),
        "income_segment_id": row.get("income_segment_id", ""),
        "income_segment_name": row.get("income_segment_name", ""),
        "income_price_band": row.get("income_price_band", ""),
        "income_sensitivity_note": row.get("income_sensitivity_note", ""),
        "income_evidence_hint": row.get("income_evidence_hint", ""),
        "time_band_name": row.get("time_band_name", ""),
        "time_range": row.get("time_range", ""),
        "weather_name": row.get("weather_name", ""),
        "node_context_name": row.get("node_context_name", ""),
        "demand_trigger_name": row.get("demand_trigger_name", ""),
        "candidate_supply_action_name": row.get("candidate_supply_action_name", ""),
        "priority_label": row.get("priority_label", "待比较"),
        "why_it_matters": row.get("why_it_matters", ""),
        "data_needed": row.get("data_needed", ""),
        "deepseek_role": row.get("deepseek_role", ""),
        "adoption_status": adoption_status,
        "user_locked": bool(control.get("user_locked")),
        "review_notes": control.get("review_notes", []),
        "updated_at": str(control.get("updated_at") or ""),
        "output_status": "needs_review",
        "not_final": True,
    }


def representative_feature_derivatives(
    rows: list[dict[str, Any]],
    controls: dict[str, Any],
    *,
    limit: int = 8,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    used_ids: set[str] = set()

    def add(row: dict[str, Any]) -> None:
        derivative_id = str(row.get("derivative_id") or "")
        if derivative_id and derivative_id not in used_ids and len(selected) < limit:
            selected.append(row)
            used_ids.add(derivative_id)

    controlled_ids = {
        derivative_id
        for derivative_id, control in controls.items()
        if isinstance(control, dict)
        and (control.get("adoption_status") in {"已采用", "已放弃"} or control.get("user_locked"))
    }
    row_by_id = {str(row.get("derivative_id") or ""): row for row in rows}
    for derivative_id in sorted(controlled_ids):
        if derivative_id in row_by_id:
            add(row_by_id[derivative_id])

    seen_personas: set[str] = set()
    for row in rows:
        persona_id = str(row.get("persona_id") or "")
        if persona_id and persona_id not in seen_personas:
            add(row)
            seen_personas.add(persona_id)
        if len(selected) >= limit:
            break

    for row in rows:
        add(row)
        if len(selected) >= limit:
            break
    return selected


def build_feature_derivative_pool(limit: int = 8) -> dict[str, Any]:
    rows = read_csv_rows(FEATURE_DERIVATIVE_CSV)
    controls = load_feature_derivative_controls()
    normalized = [normalize_feature_derivative(row, controls) for row in rows]
    adopted_count = sum(1 for row in normalized if row["adoption_status"] == "已采用")
    discarded_count = sum(1 for row in normalized if row["adoption_status"] == "已放弃")
    locked_count = sum(1 for row in normalized if row["user_locked"])
    representative = [
        normalize_feature_derivative(row, controls)
        for row in representative_feature_derivatives(rows, controls, limit=limit)
    ]
    return {
        **review_meta(
            source_hint="person_simulation_feature_derivatives_1000_20260604.csv + user controls",
            status_label="人物仿真场景覆盖池 / 待复核",
            evidence_hint="coverage pool only; not final simulation result",
        ),
        "total_count": len(rows),
        "visible_count": len(representative),
        "adopted_count": adopted_count,
        "discarded_count": discarded_count,
        "locked_count": locked_count,
        "coverage": {
            "personas": len({row.get("persona_id") for row in rows if row.get("persona_id")}),
            "income_segments": len({row.get("income_segment_id") for row in rows if row.get("income_segment_id")}),
            "time_bands": len({row.get("time_band_id") for row in rows if row.get("time_band_id")}),
            "weathers": len({row.get("weather_id") for row in rows if row.get("weather_id")}),
            "node_contexts": len({row.get("node_context_id") for row in rows if row.get("node_context_id")}),
            "demand_triggers": len({row.get("demand_trigger_id") for row in rows if row.get("demand_trigger_id")}),
            "supply_actions": len({row.get("candidate_supply_action_id") for row in rows if row.get("candidate_supply_action_id")}),
        },
        "items": representative,
        "usage_rule": "用户可采用、放弃、锁定代表场景；覆盖池用于预检和报告解释，不代表最终仿真结论。",
    }


def selected_feature_derivative_inputs(limit: int = 12) -> list[dict[str, Any]]:
    rows = read_csv_rows(FEATURE_DERIVATIVE_CSV)
    controls = load_feature_derivative_controls()
    normalized = [normalize_feature_derivative(row, controls) for row in rows]
    selected = [
        row
        for row in normalized
        if row["adoption_status"] != "已放弃"
        and (row["adoption_status"] == "已采用" or row["user_locked"])
    ]
    selected.sort(
        key=lambda row: (
            0 if row["user_locked"] else 1,
            0 if row["adoption_status"] == "已采用" else 1,
            str(row.get("derivative_id") or ""),
        )
    )
    return selected[:limit]


def controlled_feature_scene_context(limit: int = 12) -> dict[str, Any]:
    scenes = selected_feature_derivative_inputs(limit=limit)
    items: list[dict[str, Any]] = []
    for scene in scenes:
        status_parts = []
        if scene.get("adoption_status") == "已采用":
            status_parts.append("已采用")
        if scene.get("user_locked"):
            status_parts.append("已锁定")
        items.append(
            {
                "derivative_id": scene.get("derivative_id", ""),
                "title": scene.get("title", ""),
                "persona_name": scene.get("persona_name", ""),
                "income_segment_name": scene.get("income_segment_name", ""),
                "income_price_band": scene.get("income_price_band", ""),
                "income_sensitivity_note": scene.get("income_sensitivity_note", ""),
                "time_band_name": scene.get("time_band_name", ""),
                "time_range": scene.get("time_range", ""),
                "weather_name": scene.get("weather_name", ""),
                "node_context_name": scene.get("node_context_name", ""),
                "demand_trigger_name": scene.get("demand_trigger_name", ""),
                "candidate_supply_action_name": scene.get("candidate_supply_action_name", ""),
                "why_it_matters": scene.get("why_it_matters", ""),
                "data_needed": scene.get("data_needed", ""),
                "status_label": " / ".join(status_parts) if status_parts else "待讨论",
            }
        )
    income_segments = list(dict.fromkeys(item.get("income_segment_name", "") for item in items if item.get("income_segment_name")))
    price_bands = list(dict.fromkeys(item.get("income_price_band", "") for item in items if item.get("income_price_band")))
    demand_triggers = list(dict.fromkeys(item.get("demand_trigger_name", "") for item in items if item.get("demand_trigger_name")))
    return {
        "count": len(items),
        "items": items,
        "income_segments": income_segments,
        "price_bands": price_bands,
        "demand_triggers": demand_triggers,
        "usage_rule": "只使用用户已采用或已锁定的人物场景作为报告输入；覆盖池未被采用的组合不得自动写成结论。",
        "report_rule": "报告必须把收入水平、消费价格带、时段、天气、空间节点和需求触发共同用于建议强度判断。",
        "empty_state": "当前还没有采用或锁定的人物场景；报告只能引用覆盖池作为方法底座，不能声明已完成客群仿真。",
    }


def attach_controlled_feature_scene_context(report: dict[str, Any]) -> dict[str, Any]:
    context = controlled_feature_scene_context(limit=12)
    enriched = {**report, "controlled_feature_scene_context": context}
    if not context["count"]:
        return enriched

    readiness = dict(enriched.get("simulation_readiness") or {})
    can_run = list(readiness.get("can_run_now") or [])
    cannot = list(readiness.get("cannot_claim_yet") or [])
    blocking = list(readiness.get("blocking_inputs") or [])
    can_run.append("按用户已采用/锁定的人物场景，做讨论级收入水平、消费价格带、时段天气和节点动作敏感性审查。")
    cannot.append("不能把已采用人物场景当成真实客群占比、真实成交转化或最终收益预测。")
    blocking.append("采用场景对应的客群占比、时段客流、价格敏感度、实际成交转化和竞品价格。")
    readiness["can_run_now"] = list(dict.fromkeys(can_run))
    readiness["cannot_claim_yet"] = list(dict.fromkeys(cannot))
    readiness["blocking_inputs"] = list(dict.fromkeys(blocking))
    enriched["simulation_readiness"] = readiness

    next_actions = list(enriched.get("next_actions") or [])
    next_actions.insert(
        0,
        "围绕已采用/锁定人物场景逐项复核：收入段、价格带、访问时段、天气条件、到达路径、替代供给和真实转化。",
    )
    enriched["next_actions"] = list(dict.fromkeys(next_actions))
    return enriched


def load_real_calibration_inputs(limit: int | None = None) -> list[dict[str, str]]:
    rows = read_csv_rows(REAL_CALIBRATION_CSV)
    if limit is not None:
        return rows[:limit]
    return rows


def load_real_calibration_supplements() -> list[dict[str, Any]]:
    if not REAL_CALIBRATION_SUPPLEMENT_FILE.exists():
        return []
    try:
        data = json.loads(REAL_CALIBRATION_SUPPLEMENT_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return [item for item in data if isinstance(item, dict) and not item.get("deleted")]


def save_real_calibration_supplements(rows: list[dict[str, Any]]) -> None:
    REAL_CALIBRATION_SUPPLEMENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REAL_CALIBRATION_SUPPLEMENT_FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_real_calibration_supplement(row: dict[str, Any]) -> dict[str, Any]:
    allowed_strengths = {
        "official_macro_boundary",
        "local_bigdata_profile",
        "local_device_price_proxy",
        "local_poi_price_signal",
        "local_poi_demand_signal",
        "local_user_supplement",
        "plan_assumption_needs_review",
    }
    source_strength = str(row.get("source_strength") or "local_user_supplement").strip()
    if source_strength not in allowed_strengths:
        source_strength = "local_user_supplement"
    now = datetime.now().isoformat(timespec="seconds")
    return {
        "supplement_id": str(row.get("supplement_id") or "").strip(),
        "dimension": str(row.get("dimension") or "user_supplement").strip(),
        "indicator_name": str(row.get("indicator_name") or "用户补充校准输入").strip(),
        "segment": str(row.get("segment") or "待确认范围").strip(),
        "period": str(row.get("period") or "待确认时期").strip(),
        "value": str(row.get("value") or "待确认").strip(),
        "unit": str(row.get("unit") or "").strip(),
        "source_strength": source_strength,
        "simulation_use": str(row.get("simulation_use") or "作为用户补充校准输入进入预检和报告，待人工复核后用于仿真参数。").strip(),
        "cannot_claim": str(row.get("cannot_claim") or "不能直接写成最终收益、最终排名、真实转化或投资定案。").strip(),
        "next_data_needed": str(row.get("next_data_needed") or "复核来源文件、采集口径、时段、样本量、复核人和可追溯证据。").strip(),
        "source_file": str(row.get("source_file") or "用户补充资料").strip(),
        "source_page_or_slide": str(row.get("source_page_or_slide") or "user_supplement").strip(),
        "raw_text_snippet": str(row.get("raw_text_snippet") or row.get("note") or "用户补充校准输入，等待来源复核。").strip(),
        "note": str(row.get("note") or "").strip(),
        "output_status": "needs_review",
        "created_at": str(row.get("created_at") or now),
        "updated_at": str(row.get("updated_at") or now),
    }


def rebuild_real_calibration_outputs() -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(REAL_CALIBRATION_BUILD_SCRIPT)],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
        check=False,
    )
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "real calibration rebuild failed",
                "stdout": stdout[-1200:],
                "stderr": stderr[-1200:],
            },
        )
    return {
        "status": "pass",
        "stdout": stdout.strip(),
        "stderr": stderr.strip(),
        "context": real_calibration_context(limit=12),
    }


def real_calibration_context(limit: int = 12) -> dict[str, Any]:
    rows = load_real_calibration_inputs()
    validation = read_json_file(REAL_CALIBRATION_JSON, {})
    supplements = load_real_calibration_supplements()
    prioritized_rows = sorted(
        rows,
        key=lambda row: (
            0
            if row.get("source_strength") == "local_user_supplement"
            or str(row.get("calibration_id", "")).startswith("ORCI-S")
            else 1,
            str(row.get("calibration_id", "")),
        ),
    )
    compact_rows = [
        {
            "calibration_id": row.get("calibration_id", ""),
            "dimension": row.get("dimension", ""),
            "indicator_name": row.get("indicator_name", ""),
            "segment": row.get("segment", ""),
            "period": row.get("period", ""),
            "value": row.get("value", ""),
            "unit": row.get("unit", ""),
            "source_strength": row.get("source_strength", ""),
            "simulation_use": row.get("simulation_use", ""),
            "cannot_claim": row.get("cannot_claim", ""),
            "next_data_needed": row.get("next_data_needed", ""),
        }
        for row in prioritized_rows[:limit]
    ]
    strengths = Counter(row.get("source_strength", "") for row in rows if row.get("source_strength"))
    dimensions = Counter(row.get("dimension", "") for row in rows if row.get("dimension"))
    return {
        "count": len(rows),
        "status": validation.get("status") or ("pass" if rows else "missing"),
        "source_strength_counts": dict(strengths),
        "dimension_counts": dict(dimensions),
        "items": compact_rows,
        "supplement_count": len(supplements),
        "supplements": supplements[:limit],
        "usage_rule": "官方宏观边界、本地大数据画像/代理变量、PPT方案假设必须分层使用，不能混成最终结论。",
        "report_rule": "报告必须区分宏观收入/消费边界、本地画像与代理变量、竞品价格线索和待复核方案假设；任何一层都不能单独推出收益、排名或投资定案。",
        "missing_before_final": [
            "奥森周边 1-3 公里街道/社区收入水平、消费能力与居住办公结构",
            "分入口、分时段、天气和节假日客流",
            "竞品客单价、真实支付笔数、转化率和试运营 AB 数据",
            "许可消防、场地容量、排队、补货和营业关闭规则",
        ],
    }


def attach_real_calibration_context(report: dict[str, Any]) -> dict[str, Any]:
    context = real_calibration_context(limit=12)
    enriched = {**report, "real_calibration_context": context}
    if not context["count"]:
        return enriched

    readiness = dict(enriched.get("simulation_readiness") or {})
    can_run = list(readiness.get("can_run_now") or [])
    cannot = list(readiness.get("cannot_claim_yet") or [])
    blocking = list(readiness.get("blocking_inputs") or [])
    can_run.append(
        f"按 {context['count']} 条真实校准输入，分层讨论收入/消费边界、本地画像、设备价格代理、竞品客单和方案假设。"
    )
    cannot.append("不能把北京市宏观收入、手机价格代理或 PPT 转化假设写成奥森街道级收入、真实成交或最终收益。")
    blocking.extend(context.get("missing_before_final") or [])
    readiness["can_run_now"] = list(dict.fromkeys(can_run))
    readiness["cannot_claim_yet"] = list(dict.fromkeys(cannot))
    readiness["blocking_inputs"] = list(dict.fromkeys(blocking))
    enriched["simulation_readiness"] = readiness

    next_actions = list(enriched.get("next_actions") or [])
    next_actions.insert(
        0,
        "把真实校准输入逐层复核：先锁定奥森周边 1-3 公里收入水平、消费能力、人口结构和竞品客单，再复核分时段客流、天气转化、真实支付与许可消防。",
    )
    enriched["next_actions"] = list(dict.fromkeys(next_actions))
    return enriched


def build_local_data_assets() -> list[dict[str, Any]]:
    evidence_rows = read_csv_rows(ROOT / "40_quality_evidence" / "evidence_ledger.csv")
    catalog_rows = read_csv_rows(ROOT / "40_quality_evidence" / "data_catalog.csv")
    poi_rows = read_csv_rows(PROCESSED / "poi_supply_candidates_amap.csv")
    followup_rows = read_csv_rows(PROCESSED / "poi_supply_p0_followup_worklist_enriched.csv")
    feature_derivative_rows = read_csv_rows(PROCESSED / "person_simulation_feature_derivatives_1000_20260604.csv")
    real_calibration_rows = load_real_calibration_inputs()
    real_calibration_validation = read_json_file(REAL_CALIBRATION_JSON, {})
    feature_validation = read_json_file(
        ROOT / "40_quality_evidence" / "person_simulation_feature_derivatives_validation_20260607.json",
        {},
    )
    plan_profile = read_json_file(ROOT / "30_extraction" / "p2_real_site" / "osen_project_plan_profile.json", {})
    boss_manifest = read_csv_rows(ROOT / "10_research" / "boss_method_materials_20260604" / "source_manifest.csv")
    return [
        {
            "label": "证据台账",
            "count": len(evidence_rows),
            "status": "可用于背景与指标追溯",
            "use_scope": "用于校准参考，形成结论前请确认资料状态。",
        },
        {
            "label": "PDF 原生表格",
            "count": line_count(ROOT / "30_extraction" / "tables" / "pdf_native_tables.jsonl"),
            "status": "已抽取",
            "use_scope": "可支撑客流、TGI、热门到访等资料回查。",
        },
        {
            "label": "数据目录",
            "count": len(catalog_rows),
            "status": "已登记",
            "use_scope": "区分 PDF 强证据、PPT 表达材料和计划资料。",
        },
        {
            "label": "高德 POI 候选",
            "count": len(poi_rows),
            "status": "空间供给线索",
            "use_scope": "用于了解周边设施和供需情况，具体经营条件需结合现场与授权确认。",
        },
        {
            "label": "园内复核工单",
            "count": len(followup_rows),
            "status": "待现场/业务复核",
            "use_scope": "用于指出哪些 POI 仍卡在营业、授权、路线或详情字段。",
        },
        {
            "label": "奥森策划资料",
            "count": int(plan_profile.get("paragraph_count") or 0),
            "status": "已抽取",
            "use_scope": "可用于节点和业态设想，具体测量与运营条件以项目确认信息为准。",
        },
        {
            "label": "CAD / 图纸资料",
            "count": len(list((ROOT / "CAD图及其计划").glob("*"))),
            "status": "DWG 已转 DXF，图纸代理已抽取",
            "use_scope": "可用于空间锚点和图层线索；控制点校准前不当作 GIS 级路径或精确面积。",
        },
        {
            "label": "项目方法资料",
            "count": len(boss_manifest),
            "status": "6 份已归档",
            "use_scope": "用于方法、约束和验证口径；不直接当本项目商业结果。",
        },
        {
            "label": "人物仿真覆盖池",
            "count": len(feature_derivative_rows),
            "status": "已通过可读性与覆盖验证" if feature_validation.get("status") == "pass" else "待重新验证",
            "use_scope": "覆盖收入/消费价格带、时段、天气、节点、需求触发和供给动作；只作预检覆盖池，不代表最终仿真结论。",
        },
        {
            "label": "奥森真实校准输入",
            "count": len(real_calibration_rows),
            "status": "已分层入库" if real_calibration_validation.get("status") == "pass" else "待生成或复核",
            "use_scope": "分开使用官方宏观收入/消费、本地大数据画像/设备价格代理、竞品客单和 PPT 假设；不能直接推出最终收益或排名。",
        },
    ]


def load_site_report_context() -> dict[str, Any]:
    evidence_rows = read_csv_rows(QUALITY_DIR / "evidence_ledger.csv")
    priority_keywords = ("奥森", "奥林匹克", "客流", "到访", "消费", "咖啡", "冷饮", "瑜伽", "餐饮", "普拉提")
    matched_evidence = [
        row
        for row in evidence_rows
        if any(
            keyword in f"{row.get('metric_name', '')}{row.get('indicator_name', '')}{row.get('source_file', '')}{row.get('notes', '')}"
            for keyword in priority_keywords
        )
    ]
    osen_evidence = [
        row
        for row in matched_evidence
        if "奥森" in f"{row.get('metric_name', '')}{row.get('indicator_name', '')}{row.get('source_file', '')}{row.get('notes', '')}"
        or "奥林匹克" in f"{row.get('metric_name', '')}{row.get('indicator_name', '')}{row.get('source_file', '')}{row.get('notes', '')}"
    ]
    comparator_evidence = [
        row
        for row in matched_evidence
        if row not in osen_evidence and "城市绿心" in f"{row.get('metric_name', '')}{row.get('indicator_name', '')}{row.get('source_file', '')}"
    ]
    evidence_highlights = osen_evidence[:20] + comparator_evidence[:4]
    cad_analysis = read_json_file(QUALITY_DIR / "cad_dxf_analysis_20260605.json", {})
    cad_pdf = read_json_file(QUALITY_DIR / "cad_pdf_proxy_analysis_20260605.json", {})
    method_sources = {
        "boss_model_inventory": "10_research/boss_method_materials_20260604/boss_model_inventory_20260604.md",
        "method_landing_register": "10_research/boss_method_materials_20260604/method_absorption_landing_register_20260604.md",
        "modern_method_rescreen": "10_research/boss_method_materials_20260604/modern_practical_method_rescreen_20260604.md",
        "deepseek_constraints": "10_research/boss_method_materials_20260604/deepseek_constrained_simulation_design_20260604.md",
    }
    return {
        "plan_profile": read_json_file(ROOT / "30_extraction" / "p2_real_site" / "osen_project_plan_profile.json", {}),
        "evidence_highlights": evidence_highlights,
        "cad_analysis": cad_analysis,
        "north_pdf_hits": cad_pdf.get("hits", []) if isinstance(cad_pdf, dict) else [],
        "method_sources": method_sources,
        "report_inputs": [
            "CAD图及其计划/奥森重点项目策划思路20260521.docx",
            "CAD图及其计划/奥森南园（字体放大）-改造建筑示意_t5.dwg",
            "CAD图及其计划/奥森北园(字体放大)-改造建筑示意_t5.dwg",
            "CAD图及其计划/奥森北园(字体放大)-改造建筑示意-Model(1).pdf",
            "40_quality_evidence/evidence_ledger.csv",
            "50_external_gis/amap_poi/amap_poi_clean.csv",
            "10_research/boss_method_materials_20260604/*.md",
        ],
    }


def build_simulation_task_preflight(requested: dict[str, Any] | None = None) -> dict[str, Any]:
    import_existing_outputs()
    objects = load_simulation_objects()
    if requested is None:
        entry = load_simulation_task_entry(objects)
    else:
        known_ids = {str(row.get("object_id") or "") for row in objects}
        entry = {
            "task_name": str(requested.get("task_name") or "人物仿真预演"),
            "selected_object_ids": [
                str(item)
                for item in requested.get("selected_object_ids", [])
                if str(item) in known_ids
            ],
            "scenario_note": str(requested.get("scenario_note") or ""),
            "run_mode": str(requested.get("run_mode") or "preflight"),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        save_simulation_task_entry(entry)

    selected_ids = set(entry["selected_object_ids"])
    selected_objects = [row for row in objects if row.get("object_id") in selected_ids]
    selected_by_type: dict[str, list[dict[str, Any]]] = {
        object_type: [row for row in selected_objects if row.get("object_type") == object_type]
        for object_type in SIMULATION_TASK_OBJECT_TYPES
    }
    available_by_type: dict[str, list[dict[str, Any]]] = {
        object_type: [
            compact_simulation_object(row)
            for row in objects
            if row.get("object_type") == object_type and row.get("adoption_status") != "已放弃"
        ]
        for object_type in SIMULATION_TASK_OBJECT_TYPES
    }
    validation_source_by_id = {
        str(row.get("target_id") or ""): row
        for row in read_csv_rows(VALIDATION_TARGET_CSV)
    }
    selected_validation_sources = [
        validation_source_by_id.get(str(row.get("linked_id") or ""), {})
        for row in selected_by_type["simulation_validation_target"]
    ]
    validation_missing = [
        str(row.get("missing_inputs") or row.get("target_name") or "真实校准资料")
        for row in selected_validation_sources
        if str(row.get("reference_data_status") or "").strip() not in {"available_checked", "closed", "passed"}
    ]
    gates = list_calibration_gates()
    unresolved_gates = [
        row for row in gates
        if row.get("required_before_p4_conclusion") == "yes"
        and row.get("current_gate_status") not in {"closed", "passed"}
    ]
    uploads = load_upload_index()
    adopted_uploads = [
        row for row in uploads
        if re.search(r"已采用|已确认|使用|入池", str(row.get("review_status") or ""))
    ]
    map_context = load_map_context()
    poi_count = len(load_amap_supply(limit=10000))
    feature_derivative_rows = read_csv_rows(PROCESSED / "person_simulation_feature_derivatives_1000_20260604.csv")
    feature_derivative_validation = read_json_file(
        ROOT / "40_quality_evidence" / "person_simulation_feature_derivatives_validation_20260607.json",
        {},
    )
    feature_scene_inputs = selected_feature_derivative_inputs(limit=12)
    real_calibration = real_calibration_context(limit=12)
    selected_discarded = [
        row for row in selected_objects
        if row.get("adoption_status") == "已放弃"
    ]

    checks: list[dict[str, Any]] = []

    def add_check(
        check_id: str,
        label: str,
        status: str,
        detail: str,
        next_action: str,
        *,
        blocks_full_simulation: bool = False,
        evidence_refs: list[str] | None = None,
    ) -> None:
        checks.append(
            {
                "check_id": check_id,
                "label": label,
                "status": status,
                "detail": detail,
                "next_action": next_action,
                "blocks_full_simulation": blocks_full_simulation,
                "evidence_refs": evidence_refs or [],
            }
        )

    required_type_labels = {
        "persona_state": "人群状态画像",
        "behavior_program": "行为程序",
        "choice_probability": "选择概率候选",
        "simulation_validation_target": "仿真验证目标",
    }
    for object_type, label in required_type_labels.items():
        count = len(selected_by_type[object_type])
        add_check(
            f"selected_{object_type}",
            label,
            "pass" if count else "block",
            f"当前已选择 {count} 个{label}。",
            "至少选择 1 个，并由业务人员确认采用或保持候选预检。",
            blocks_full_simulation=count == 0,
            evidence_refs=[f"object_pool:{object_type}"],
        )
    add_check(
        "discarded_object_guard",
        "放弃对象保护",
        "block" if selected_discarded else "pass",
        f"当前选择中有 {len(selected_discarded)} 个已放弃对象。" if selected_discarded else "未把已放弃对象带入任务。",
        "取消已放弃对象，或先恢复为暂未采用后再进入预检。",
        blocks_full_simulation=bool(selected_discarded),
    )
    add_check(
        "local_evidence_assets",
        "本地真实资料",
        "pass",
        "已整理数据记录、PDF 表格、地图周边设施、奥森策划和项目方法资料。",
        "把资料关联到人群、行为、选择概率和验证目标，不直接跳到最终结论。",
        evidence_refs=["40_quality_evidence/evidence_ledger.csv", "30_extraction/tables/pdf_native_tables.jsonl"],
    )
    add_check(
        "adopted_uploads",
        "用户采用资料",
        "pass" if adopted_uploads else "warn",
        f"资料池中已采用 {len(adopted_uploads)} 份外部上传资料。",
        "如本轮项目有新的客流、图纸、授权或计划文件，应先上传并采用。",
        blocks_full_simulation=False,
        evidence_refs=["90_p6_expert_dashboard/cache/uploaded_sources.json"],
    )
    add_check(
        "map_poi_context",
        "空间与 POI 语境",
        "pass" if poi_count else "warn",
        f"当前地图/本地候选可读取 {poi_count} 条 POI 线索。",
        "POI 只作供给语境；园内经营和授权仍需资料闭合。",
        evidence_refs=["70_outputs/processed_tables/poi_supply_candidates_amap.csv"],
    )
    add_check(
        "person_simulation_feature_derivatives",
        "人物仿真覆盖池",
        "pass" if len(feature_derivative_rows) >= 1000 and feature_derivative_validation.get("status") == "pass" else "warn",
        f"当前覆盖池 {len(feature_derivative_rows)} 条；验证状态 {feature_derivative_validation.get('status', '待验证')}。",
        "用于覆盖收入/消费价格带、天气、时段、空间节点、需求触发和供给动作；不要把覆盖池当成最终仿真结果。",
        blocks_full_simulation=False,
        evidence_refs=[
            "70_outputs/processed_tables/person_simulation_feature_derivatives_1000_20260604.csv",
            "40_quality_evidence/person_simulation_feature_derivatives_validation_20260607.json",
        ],
    )
    add_check(
        "controlled_feature_scenes",
        "已采用人物场景",
        "pass" if feature_scene_inputs else "warn",
        (
            f"已有 {len(feature_scene_inputs)} 条采用或锁定的人物场景进入本次预检输入，"
            "其中包含收入/消费价格带、时段、天气、节点、需求触发和供给动作。"
            if feature_scene_inputs
            else "尚未采用或锁定人物场景；覆盖池目前只作为参考，不会自动变成仿真输入。"
        ),
        "至少采用或锁定 1 条代表场景，或明确保持覆盖池为资料参考；收入/价格带需要和真实消费数据复核。",
        blocks_full_simulation=False,
        evidence_refs=[
            "70_outputs/processed_tables/person_simulation_feature_derivatives_1000_20260604.csv",
            "90_p6_expert_dashboard/cache/simulation_feature_derivative_controls.json",
        ],
    )
    add_check(
        "osen_real_calibration_inputs",
        "真实校准输入",
        "pass" if real_calibration["count"] >= 10 and real_calibration["status"] == "pass" else "warn",
        (
            f"已接入 {real_calibration['count']} 条分层校准输入，覆盖官方宏观收入/消费、本地大数据画像、"
            "设备价格代理、竞品客单和方案假设。"
            if real_calibration["count"]
            else "尚未生成奥森真实校准输入包。"
        ),
        "继续把奥森周边 1-3 公里街道收入、人口结构、竞品客单、真实支付、时段客流、天气转化和许可消防纳入内部复核。",
        blocks_full_simulation=False,
        evidence_refs=[
            "70_outputs/processed_tables/osen_real_calibration_inputs_20260607.csv",
            "40_quality_evidence/osen_real_calibration_inputs_20260607.json",
        ],
    )
    add_check(
        "project_location",
        "项目位置",
        "pass" if map_context.get("longitude") and map_context.get("latitude") else "warn",
        map_context.get("matched_name") or map_context.get("keyword") or "尚未确认项目地图目标。",
        "先在地图中确认项目位置；不要强绑默认公园。",
        blocks_full_simulation=False,
        evidence_refs=["90_p6_expert_dashboard/cache/map_context.json"],
    )
    add_check(
        "macro_validation_data",
        "宏观校准数据",
        "block" if validation_missing else "warn",
        "已选择的验证目标仍缺真实参考数据。" if validation_missing else "未选择带完整参考数据的验证目标，仍需人工确认。",
        "锁定时段客流、路线观察、停留时长、转化率、交易或现场观察口径后再宣称完整仿真。",
        blocks_full_simulation=True,
        evidence_refs=["70_outputs/processed_tables/simulation_validation_target_from_p2_20260604.csv"],
    )
    add_check(
        "p3_gate_closure",
        "P3 前置资料闭合",
        "block" if unresolved_gates else "pass",
        f"仍有 {len(unresolved_gates)} 项 P3 前置资料未闭合。" if unresolved_gates else "P3 前置资料已闭合。",
        "闭合图纸/几何、客流、转化率、收益成本和运营授权，才能进入完整仿真结论。",
        blocks_full_simulation=bool(unresolved_gates),
        evidence_refs=["70_outputs/processed_tables/p3_calibration_gate_status.csv"],
    )
    add_check(
        "planning_and_cad_integration",
        "策划文案与 CAD 结合",
        "warn",
        "已发现奥森策划文案和 CAD/图纸资料，但仍需要把建筑位置、面积、路径和业态设想统一到同一组仿真对象。",
        "最终报告前必须用平台回放：策划文案 -> 节点/业态 -> CAD/空间复核 -> 人群/行为/选择概率 -> 预检结果。",
        blocks_full_simulation=False,
        evidence_refs=["CAD图及其计划/奥森重点项目策划思路20260521.docx", "CAD图及其计划/*.dwg"],
    )
    add_check(
        "production_ai_boundary",
        "生产 AI 边界",
        "pass",
        "最终网站内置 AI 只作为候选整理、解释和报告工作稿助手，不输出最终概率、排名或收益。",
        "任何模型输出都必须标注为待人工复核，并经过本地校验和人工确认后才能进入正式结论。",
        blocks_full_simulation=False,
        evidence_refs=["00_control/decisions.md", "00_control/deepseek_role_contract_20260605.md"],
    )

    blocking_checks = [row for row in checks if row["blocks_full_simulation"] and row["status"] == "block"]
    object_ready = all(len(selected_by_type[object_type]) > 0 for object_type in SIMULATION_TASK_OBJECT_TYPES) and not selected_discarded
    full_status = "blocked_for_full_simulation" if blocking_checks else "ready_for_controlled_dry_run"
    dry_status = "ready_for_structural_precheck" if object_ready else "select_objects_first"
    return {
        **review_meta(
            source_hint="simulation_objects + local evidence assets + P3 gates",
            evidence_hint="preflight only; no final simulation conclusion",
            status_label="仿真任务入口 / 运行前预检",
        ),
        "task": entry,
        "selected_object_ids": entry["selected_object_ids"],
        "selected_counts": {
            object_type: len(selected_by_type[object_type])
            for object_type in SIMULATION_TASK_OBJECT_TYPES
        },
        "selected_objects": {
            object_type: [compact_simulation_object(row) for row in selected_by_type[object_type]]
            for object_type in SIMULATION_TASK_OBJECT_TYPES
        },
        "available_objects": available_by_type,
        "local_data_assets": build_local_data_assets(),
        "feature_derivative_pool": build_feature_derivative_pool(limit=8),
        "feature_scene_inputs": feature_scene_inputs,
        "controlled_feature_scene_count": len(feature_scene_inputs),
        "real_calibration_context": real_calibration,
        "real_calibration_input_count": real_calibration["count"],
        "preflight_checks": checks,
        "blocking_count": len(blocking_checks),
        "full_simulation_status": full_status,
        "dry_run_status": dry_status,
        "human_summary": (
            (
                f"对象组合可以进入结构化预检，且已带入 {len(feature_scene_inputs)} 条采用/锁定人物场景；"
                f"同时接入 {real_calibration['count']} 条分层真实校准输入；完整仿真仍被街道级数据和 P3 门禁阻止。"
            )
            if object_ready and feature_scene_inputs
            else f"对象组合可以进入结构化预检，并接入 {real_calibration['count']} 条真实校准输入；但完整仿真仍被街道级数据和 P3 门禁阻止。"
            if object_ready
            else "完整仿真被阻止且未放行：请先选择人群状态、行为程序、选择概率和验证目标；即使选齐，也要通过真实校准数据和 P3 门禁后才能宣称完整仿真。"
        ),
        "deepseek_role": "DeepSeek 仅负责候选整理、解释和工作稿；不逐游客实时仿真，不输出最终概率、排名或收益。",
    }


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
        priority_recommendations = [
            "先确认当前搜索地点是否就是本项目范围。",
            "导入项目计划或图纸后，再让系统拆分节点和建立比较口径。",
            "地图 POI 只能作为周边供给参考，不能直接替代现场踏勘。",
        ]
        priority_basis = [
            {
                "label": "使用边界",
                "value": "只作位置参考",
                "impact": "当前地图展示目标位置、周边设施和边界信息。",
                "status": "待复核",
            }
        ]
        return {
            "discussion_score_draft": 0,
            "priority_score_internal": 0,
            "priority_stage": "位置参考",
            "priority_label": "位置参考",
            "priority_summary": "当前地图展示位置、周边设施与边界信息，可用于了解目标区域的空间条件。",
            "priority_recommendations": priority_recommendations,
            "priority_basis": priority_basis,
            "score_status": "location_reference_only",
            "score_label": "位置参考",
            "score_explanation": "当前地图展示位置、周边设施与边界信息，可用于了解目标区域的空间条件。",
            "score_recommendations": priority_recommendations,
            "score_breakdown": priority_basis,
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
    gate_penalty = min(30, gate_count * 5)
    missing_penalty = min(18, len(missing_fields) * 2)
    poi_penalty = 6 if poi_count < 20 else 0
    boundary_penalty = 8 if "estimated" in str(boundary_status) else 0
    penalty = gate_penalty + missing_penalty
    if poi_count < 20:
        penalty += poi_penalty
    if "estimated" in str(boundary_status):
        penalty += boundary_penalty
    priority_score_internal = max(0, min(100, round(base - penalty)))
    level = "优先推进复核" if priority_score_internal >= 70 else ("复核后再比较" if priority_score_internal >= 55 else "暂缓推进，先做内部复核")
    if priority_score_internal >= 70:
        priority_recommendations = [
            "进入重点复核：先锁定图纸边界、真实客流和可落位面积口径。",
            "把周边 POI 与目标业态做竞品/互补核对，确认这个点究竟解决哪类游客问题。",
            "形成单节点工作小结，但只写成待复核推进项，不写成最终推荐。"
        ]
    elif priority_score_internal >= 55:
        priority_recommendations = [
            "先复核再比较：不要急着写成推荐点，先锁定影响判断的关键口径。",
            "把缺失字段分配给负责人：图纸、客流、转化率、收益成本、授权各自闭合。",
            "复核完成后重新生成优先级解析，再比较它和其他节点的相对位置。"
        ]
    else:
        priority_recommendations = [
            "当前资料仍需完善，建议补充关键依据后再确定节点推进优先级。",
            "优先复核真实客流、准确边界和经营口径；这些口径未锁定时不要给客户写确定结论。",
            "可以保留为备选观察点，与高分节点并列比较，但不要放在当前推进主线上。"
        ]
    priority_basis = [
        {
            "label": "判断用途",
            "value": "推进优先级",
                "impact": "用于提醒团队先推进哪些节点、哪些节点先复核；不能直接当最终排名或投资决策。",
            "status": "待复核",
        },
        {
            "label": "前期关注度",
            "value": "已有草案",
            "impact": "来自前期节点反馈，只代表这个点在初步方案里被关注过；不能单独证明它值得落位。",
            "status": "待复核",
        },
        {
            "label": "资料闭合度",
            "value": f"{gate_count} 项前置资料待复核",
            "impact": "图纸、客流、转化率、收益成本或运营授权不足时，判断只能停留在推进建议层。",
            "status": "需复核" if gate_penalty else "暂可使用",
        },
        {
            "label": "字段缺口",
            "value": f"{len(missing_fields)} 类缺口",
            "impact": "缺口包括：" + ("、".join(missing_fields[:6]) if missing_fields else "暂无主要缺口") + ("等" if len(missing_fields) > 6 else ""),
            "status": "需复核" if missing_penalty else "暂可使用",
        },
        {
            "label": "周边 POI 语境",
            "value": f"{poi_count} 条",
            "impact": "POI 用于判断周边供给和竞品语境；数量不足时只能作为弱参考。",
            "status": "待复核",
        },
        {
            "label": "边界可信度",
            "value": "公共/估算口径" if boundary_penalty else "暂可使用",
            "impact": "当前边界用于位置分析，节点落位请结合项目图纸和现场情况确认。",
            "status": "需复核" if boundary_penalty else "暂可使用",
        },
    ]
    priority_summary = (
        "当前结论只回答“下一步该怎么推进”，不回答“是否最终推荐”。"
        f"已有草案关注度、{gate_count} 项资料闭合状态、{len(missing_fields)} 类字段缺口、{poi_count} 条 POI 语境和边界可信度共同决定这个推进级别。"
    )
    return {
        "discussion_score_draft": priority_score_internal,
        "priority_score_internal": priority_score_internal,
        "priority_stage": level,
        "priority_label": level,
        "priority_summary": priority_summary,
        "priority_recommendations": priority_recommendations,
        "priority_basis": priority_basis,
        "score_status": "needs_review_not_final",
        "score_label": level,
        "score_explanation": priority_summary,
        "score_recommendations": priority_recommendations,
        "score_breakdown": priority_basis,
        "legacy_score_breakdown": [
            {
                "label": "旧数值用途",
                "value": "讨论优先级",
                "impact": "该项用于支持当前阶段的节点比较和推进判断。",
                "status": "非最终",
            },
            {
                "label": "基础判断",
                "value": f"{base:g} 分",
                "impact": "来自前期节点反馈中的讨论分，只代表这个点在初步方案里的关注度。",
                "status": "待复核",
            },
            {
                "label": "资料门禁",
                "value": f"-{gate_penalty} 分",
                "impact": f"{gate_count} 项 P3 前置资料尚未闭合，图纸、客流、转化率、收益成本或运营授权不足会压低可信度。",
                "status": "需复核" if gate_penalty else "暂可使用",
            },
            {
                "label": "字段缺口",
                "value": f"-{missing_penalty} 分",
                "impact": "缺口字段包括：" + ("、".join(missing_fields[:6]) if missing_fields else "暂无主要缺口") + ("等" if len(missing_fields) > 6 else ""),
                "status": "需复核" if missing_penalty else "暂可使用",
            },
            {
                "label": "周边 POI",
                "value": f"{poi_count} 条" + (f" / -{poi_penalty} 分" if poi_penalty else ""),
                "impact": "POI 用于判断周边供给和竞品语境；数量不足时只能作为弱参考。",
                "status": "待复核",
            },
            {
                "label": "边界可信度",
                "value": f"-{boundary_penalty} 分" if boundary_penalty else "未扣分",
                "impact": "当前边界用于位置参考，具体范围请结合项目图纸和现场情况确认。",
                "status": "需复核" if boundary_penalty else "暂可使用",
            },
        ],
        "score_inputs": {
            "project_context": "osen",
            "base_score": base,
            "blocked_gate_count": gate_count,
            "missing_required_fields": missing_fields,
            "poi_context_count": poi_count,
            "boundary_status": boundary_status,
            "penalty": penalty,
            "gate_penalty": gate_penalty,
            "missing_penalty": missing_penalty,
            "poi_penalty": poi_penalty,
            "boundary_penalty": boundary_penalty,
        },
    }


def enrich_gate(row: dict[str, Any]) -> dict[str, Any]:
    status = row.get("current_gate_status", "")
    label = "已闭合" if status in {"closed", "passed"} else "待复核"
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


def build_supply_gap_payload(
    nodes: list[dict[str, Any]],
    amap_supply: list[dict[str, Any]],
    uploads: list[dict[str, Any]],
    upload_candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    visitor_sources = parse_uploaded_visitor_sources(uploads, upload_candidates)
    tgi = build_tgi_profile(visitor_sources["combined_text"])
    supply = build_supply_profile(amap_supply)
    gap = calculate_supply_gap(tgi, supply)
    report = build_gap_report(nodes, gap, uploads)
    return {
        **review_meta(
            source_hint="web uploads + current AMap POI context",
            evidence_hint="TGI and POI gap are needs_review / not_final",
            status_label="供需缺口 / 待复核",
        ),
        "visitor_sources": {
            "has_uploaded_visitor_flow": visitor_sources["has_uploaded_visitor_flow"],
            "count": len(visitor_sources["sources"]),
            "items": visitor_sources["sources"],
        },
        "tgi": tgi,
        "supply": supply,
        "gap": gap,
        "report": report,
    }


def build_object_chain(
    *,
    uploads: list[dict[str, Any]],
    upload_candidates: list[dict[str, Any]],
    nodes: list[dict[str, Any]],
    gates: list[dict[str, str]],
    amap_supply: list[dict[str, Any]],
    map_context: dict[str, Any],
    simulation_objects: list[dict[str, Any]],
    ai_sessions: dict[str, Any],
    report: dict[str, Any],
) -> dict[str, Any]:
    def count_objects(object_type: str) -> int:
        return sum(1 for row in simulation_objects if row.get("object_type") == object_type)

    def count_adopted(object_type: str | None = None) -> int:
        return sum(
            1
            for row in simulation_objects
            if row.get("adoption_status") == "已采用"
            and (object_type is None or row.get("object_type") == object_type)
        )

    def count_locked(object_type: str | None = None) -> int:
        return sum(
            1
            for row in simulation_objects
            if row.get("user_locked")
            and (object_type is None or row.get("object_type") == object_type)
        )

    adopted_uploads = [
        row for row in uploads
        if re.search(r"已采用|已确认|使用|入池", str(row.get("review_status") or ""))
    ]
    unresolved_gates = [
        row for row in gates
        if row.get("required_before_p4_conclusion") == "yes"
        and row.get("current_gate_status") not in {"closed", "passed"}
    ]
    persona_count = count_objects("persona_state")
    behavior_count = count_objects("behavior_program")
    choice_count = count_objects("choice_probability")
    validation_count = count_objects("simulation_validation_target")
    session_count = len(ai_sessions.get("sessions") or [])
    map_located = bool(map_context.get("keyword") or map_context.get("matched_name"))
    report_has_material = bool(report.get("source_upload_count") or report.get("top_gaps"))
    feature_pool = build_feature_derivative_pool(limit=8)
    controlled_feature_scenes = selected_feature_derivative_inputs(limit=12)

    items = [
        {
            "object_key": "project_scope",
            "label": "项目范围",
            "count": 1 if map_located else 0,
            "status_label": "已定位，待复核范围" if map_located else "待确认目标范围",
            "readiness": "usable" if map_located else "needs_input",
            "next_action": "核对当前地图目标、项目名称和上传资料是否指向同一项目。",
            "evidence_refs": ["90_p6_expert_dashboard/cache/map_context.json"],
            "view": "map",
            "action_label": "核对地图",
        },
        {
            "object_key": "source_material",
            "label": "资料对象",
            "count": len(uploads),
            "adopted_count": len(adopted_uploads),
            "status_label": f"{len(uploads)} 份入池，{len(adopted_uploads)} 份已采用" if uploads else "待导入资料",
            "readiness": "usable" if adopted_uploads else ("draft" if uploads or upload_candidates else "needs_input"),
            "next_action": "确认资料用途，并关联到人群状态、行为程序、选择概率或验证目标。",
            "evidence_refs": ["90_p6_expert_dashboard/cache/uploaded_sources.json"],
            "view": "upload",
            "action_label": "处理资料",
        },
        {
            "object_key": "persona_state",
            "label": "人群状态画像",
            "count": persona_count,
            "adopted_count": count_adopted("persona_state"),
            "locked_count": count_locked("persona_state"),
            "status_label": f"{persona_count} 个候选，{count_adopted('persona_state')} 个已采用",
            "readiness": "usable" if count_adopted("persona_state") else "draft",
            "next_action": "综合目的、时间压力、预算、同行和排队容忍等状态，完善人群画像。",
            "evidence_refs": ["70_outputs/processed_tables/p2_persona_state_profiles_20260604.csv"],
            "view": "data",
            "action_label": "看状态",
        },
        {
            "object_key": "behavior_program",
            "label": "行为程序",
            "count": behavior_count,
            "adopted_count": count_adopted("behavior_program"),
            "locked_count": count_locked("behavior_program"),
            "status_label": f"{behavior_count} 个候选，{count_adopted('behavior_program')} 个已采用",
            "readiness": "usable" if count_adopted("behavior_program") else "draft",
            "next_action": "梳理触发、动作序列、放弃条件和外溢条件，形成完整行为路径。",
            "evidence_refs": ["70_outputs/processed_tables/p2_behavior_program_templates_20260604.csv"],
            "view": "data",
            "action_label": "看行为",
        },
        {
            "object_key": "choice_probability",
            "label": "选择概率候选",
            "count": choice_count,
            "adopted_count": count_adopted("choice_probability"),
            "locked_count": count_locked("choice_probability"),
            "status_label": f"{choice_count} 个候选，{count_adopted('choice_probability')} 个已采用",
            "readiness": "usable" if count_adopted("choice_probability") else "draft",
            "next_action": "综合 POI/TGI、距离、排队、价格和时段等因素，分析不同选择倾向。",
            "evidence_refs": ["70_outputs/processed_tables/choice_probability_from_p2_p4_20260604.csv"],
            "view": "data",
            "action_label": "看选择",
        },
        {
            "object_key": "feature_derivative_scene",
            "label": "人物场景假设",
            "count": int(feature_pool.get("total_count") or 0),
            "adopted_count": int(feature_pool.get("adopted_count") or 0),
            "locked_count": int(feature_pool.get("locked_count") or 0),
            "status_label": (
                f"{len(controlled_feature_scenes)} 条采用/锁定场景已进入预检输入"
                if controlled_feature_scenes
                else "覆盖池可用，待采用代表场景"
            ),
            "readiness": "usable" if controlled_feature_scenes else "draft",
            "next_action": "结合真实人群场景，分析收入、价格、天气、时段、空间和供给动作。",
            "evidence_refs": [
                "70_outputs/processed_tables/person_simulation_feature_derivatives_1000_20260604.csv",
                "90_p6_expert_dashboard/cache/simulation_feature_derivative_controls.json",
            ],
            "view": "data",
            "action_label": "看场景",
        },
        {
            "object_key": "spatial_context",
            "label": "空间与 POI",
            "count": len(amap_supply),
            "status_label": f"{len(amap_supply)} 条 POI 语境" if amap_supply else "待获取 POI",
            "readiness": "usable" if amap_supply and map_located else "needs_input",
            "next_action": "结合地图位置和周边 POI，查看节点空间条件与商业环境。",
            "evidence_refs": ["90_p6_expert_dashboard/cache/map_context_pois.json"],
            "view": "map",
            "action_label": "看空间",
        },
        {
            "object_key": "validation_target",
            "label": "仿真验证目标",
            "count": validation_count,
            "adopted_count": count_adopted("simulation_validation_target"),
            "locked_count": count_locked("simulation_validation_target"),
            "blocked_count": len(unresolved_gates),
            "status_label": f"{validation_count} 个目标，{len(unresolved_gates)} 项前置资料待复核",
            "readiness": "blocked" if unresolved_gates else ("usable" if count_adopted("simulation_validation_target") else "draft"),
            "next_action": "明确图纸、客流、转化、收益成本和运营授权等分析重点，用于检验方案可信度。",
            "evidence_refs": ["70_outputs/processed_tables/simulation_validation_target_from_p2_20260604.csv"],
            "view": "data",
            "action_label": "看验证",
        },
        {
            "object_key": "node_progress",
            "label": "节点推进对象",
            "count": len(nodes),
            "status_label": f"{len(nodes)} 个节点待复核" if nodes else "待生成节点",
            "readiness": "draft" if nodes else "needs_input",
            "next_action": "展示节点推进优先级、判断依据和后续动作，便于统一查看与持续推进。",
            "evidence_refs": ["70_outputs/processed_tables/p2_project_node_candidates.csv"],
            "view": "nodes",
            "action_label": "看节点",
        },
        {
            "object_key": "ai_session",
            "label": "AI 沟通记录",
            "count": session_count,
            "status_label": f"{session_count} 个会话" if session_count else "待形成项目综合共识",
            "readiness": "usable" if session_count else "needs_input",
            "next_action": "围绕项目综合分析、单节点讨论和报告草稿，保留完整沟通记录与确认结果。",
            "evidence_refs": ["90_p6_expert_dashboard/cache/ai_sessions.json"],
            "view": "ai",
            "action_label": "打开 AI",
        },
        {
            "object_key": "report_draft",
            "label": "报告工作稿",
            "count": 1 if report_has_material else 0,
            "status_label": "可生成工作稿" if report_has_material else "等待资料与共识",
            "readiness": "draft" if report_has_material else "needs_input",
            "next_action": "汇总报告摘要、关键依据、待完善信息和推进事项，形成可持续更新的项目报告。",
            "evidence_refs": ["80_delivery/"],
            "view": "report",
            "action_label": "看报告",
        },
    ]
    return {
        "source": "evidence_based_direction_reset_20260605",
        "not_final": True,
        "items": items,
        "summary": {
            "total_items": len(items),
            "usable_count": sum(1 for item in items if item["readiness"] == "usable"),
            "draft_count": sum(1 for item in items if item["readiness"] == "draft"),
            "needs_input_count": sum(1 for item in items if item["readiness"] == "needs_input"),
            "blocked_count": sum(1 for item in items if item["readiness"] == "blocked"),
        },
    }


def load_dashboard() -> dict[str, Any]:
    uploads = load_upload_index()
    upload_candidates = load_upload_candidates()
    node_drafts = load_node_drafts()
    has_external_uploads = bool(uploads)
    nodes = read_csv_rows(PROCESSED / "p2_project_node_candidates.csv") if has_external_uploads else []
    priorities = read_csv_rows(PROCESSED / "p4_feedback_node_priority_draft_deepseek.csv") if has_external_uploads else []
    scenarios = read_csv_rows(PROCESSED / "p4_feedback_scenario_matrix_draft_deepseek.csv") if has_external_uploads else []
    requests = read_csv_rows(PROCESSED / "p4_feedback_data_request_to_partner_deepseek.csv") if has_external_uploads else []
    gates = read_csv_rows(PROCESSED / "p3_calibration_gate_status.csv")
    assumptions = read_csv_rows(PROCESSED / "p2_business_scene_assumption_pool.csv") if has_external_uploads else []
    gaps = read_csv_rows(PROCESSED / "p2_input_gap_register.csv") if has_external_uploads else []
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
                    "复核 P3 gate 真实来源",
                    "确认 DWG/DXF/GeoJSON/SVG/PDF 可信几何导出",
                    "复核真实客流、转化率、收益成本和运营授权",
                ],
            }
        )

    existing_node_ids = {str(node.get("node_id") or "") for node in merged_nodes}
    for index, draft in enumerate(node_drafts, start=len(merged_nodes)):
        if draft.get("node_id") in existing_node_ids:
            continue
        merged_nodes.append(normalize_node_draft(draft, index))

    gap_payload = build_supply_gap_payload(merged_nodes, amap_supply, uploads, upload_candidates)
    merged_nodes = attach_gap_to_nodes(merged_nodes, gap_payload["gap"]["items"])
    has_project_plan = any(row.get("purpose") == "项目计划" and row.get("is_used") for row in uploads)
    has_map_located = bool(map_context.get("longitude") and map_context.get("latitude"))
    has_node_drafts = bool(node_drafts)
    has_poi = bool(amap_supply)
    simulation_objects = load_simulation_objects()
    adopted_simulation_objects = [row for row in simulation_objects if row.get("adoption_status") == "已采用"]
    ai_sessions_data = load_ai_sessions()
    simulation_task_preflight = build_simulation_task_preflight()
    local_data_assets = simulation_task_preflight.get("local_data_assets", [])
    site_report_context = load_site_report_context()
    gap_payload["report"] = build_gap_report(
        merged_nodes,
        gap_payload["gap"],
        uploads,
        visitor_sources=gap_payload.get("visitor_sources"),
        tgi=gap_payload.get("tgi"),
        supply=gap_payload.get("supply"),
        local_data_assets=local_data_assets,
        map_context=map_context,
        amap_supply=amap_supply,
        gates=gates,
        simulation_objects=simulation_objects,
        site_context=site_report_context,
    )
    gap_payload["report"] = attach_controlled_feature_scene_context(gap_payload["report"])
    gap_payload["report"] = attach_real_calibration_context(gap_payload["report"])
    object_chain = build_object_chain(
        uploads=uploads,
        upload_candidates=upload_candidates,
        nodes=merged_nodes,
        gates=gates,
        amap_supply=amap_supply,
        map_context=map_context,
        simulation_objects=simulation_objects,
        ai_sessions=ai_sessions_data,
        report=gap_payload["report"],
    )

    return {
        "meta": {
            "project_name": "公园商业选址仿真 P6 原型",
            "phase": "P6 expert dashboard prototype",
            "data_status": "反馈工作稿 / 待人工复核 / 非最终结论",
            "source_mode": "uploaded_project_materials" if has_external_uploads else "empty_until_external_upload",
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
        "demand_supply": gap_payload,
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
        "uploads": uploads,
        "upload_candidates": upload_candidates,
        "gate_inputs": load_gate_inputs(),
        "simulation_objects": simulation_objects,
        "simulation_task_preflight": simulation_task_preflight,
        "site_report_context": site_report_context,
        "object_chain": object_chain,
        "overview_status": {
            "has_project_plan": has_project_plan,
            "has_map_located": has_map_located,
            "has_node_drafts": has_node_drafts,
            "has_poi": has_poi,
            "has_ai_context": bool(ai_sessions_data.get("sessions")),
            "has_simulation_objects": bool(simulation_objects),
            "adopted_simulation_object_count": len(adopted_simulation_objects),
            "can_generate_review_report": has_project_plan and has_map_located and has_node_drafts and has_poi,
        },
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
        "keyword": "青年湖公园",
        "matched_name": "青年湖公园",
        "address": "北京市东城区安德里北街",
        "longitude": "116.403153",
        "latitude": "39.954271",
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


def load_ai_sessions() -> dict[str, Any]:
    if not AI_SESSIONS_FILE.exists():
        return {"sessions": []}
    try:
        data = json.loads(AI_SESSIONS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"sessions": []}
    if isinstance(data, dict) and isinstance(data.get("sessions"), list):
        return data
    if isinstance(data, list):
        return {"sessions": data}
    return {"sessions": []}


def save_ai_sessions(data: dict[str, Any]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    AI_SESSIONS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def current_project_from_payload(payload: dict[str, Any]) -> dict[str, str]:
    context = payload.get("amap", {}).get("map_context", {})
    name = context.get("matched_name") or context.get("keyword") or "当前选址项目"
    project_id = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "-", name).strip("-") or "current-project"
    return {"project_id": project_id[:48], "project_name": name}


def summarize_ai_sessions(data: dict[str, Any]) -> dict[str, Any]:
    sessions = sorted(data.get("sessions", []), key=lambda item: item.get("updated_at", ""), reverse=True)
    projects: dict[str, dict[str, Any]] = {}
    for session in sessions:
        project_id = session.get("project_id") or "current-project"
        project = projects.setdefault(project_id, {
            "project_id": project_id,
            "project_name": session.get("project_name") or "当前选址项目",
            "count": 0,
            "updated_at": session.get("updated_at", ""),
        })
        project["count"] += 1
        if session.get("updated_at", "") > project.get("updated_at", ""):
            project["updated_at"] = session.get("updated_at", "")
    return {
        "output_status": "needs_review",
        "not_final": True,
        "projects": sorted(projects.values(), key=lambda item: item.get("updated_at", ""), reverse=True),
        "sessions": [
            {key: session.get(key) for key in [
                "session_id", "project_id", "project_name", "title", "node_id", "created_at", "updated_at", "message_count"
            ]}
            for session in sessions
        ],
    }


def create_ai_session_record(
    payload: dict[str, Any],
    project_id: str | None = None,
    project_name: str | None = None,
    title: str | None = None,
    node_id: str | None = None,
) -> dict[str, Any]:
    now = datetime.now().isoformat(timespec="seconds")
    project = current_project_from_payload(payload)
    safe_project_id = project_id or project["project_id"]
    safe_project_name = project_name or project["project_name"]
    data = load_ai_sessions()
    session = {
        "session_id": f"CHAT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(data.get('sessions', [])) + 1:04d}",
        "project_id": safe_project_id,
        "project_name": safe_project_name,
        "title": title or "新对话",
        "node_id": node_id,
        "messages": [],
        "message_count": 0,
        "output_status": "needs_review",
        "not_final": True,
        "created_at": now,
        "updated_at": now,
    }
    data.setdefault("sessions", []).append(session)
    save_ai_sessions(data)
    return session


def find_ai_session(session_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    data = load_ai_sessions()
    for session in data.get("sessions", []):
        if session.get("session_id") == session_id:
            return data, session
    raise HTTPException(status_code=404, detail="ai session not found")


def title_from_message(message: str) -> str:
    compact = re.sub(r"\s+", " ", message).strip()
    return (compact[:22] + "…") if len(compact) > 22 else (compact or "新对话")


def humanize_report_text(text: Any) -> str:
    value = str(text or "").strip()
    replacements = {
        "needs_review / not_final": "待人工确认",
        "needs_review": "待人工确认",
        "not_final": "非最终结论",
        "location_reference_only": "仅作位置参考",
        ("external" + "_preview_only"): "仅作位置参考",
        "backend": "系统",
        "debug": "诊断信息",
        "raw payload": "原始资料",
        "DeepSeek": "AI 助手",
    }
    for old, new in replacements.items():
        value = re.sub(re.escape(old), new, value, flags=re.IGNORECASE)
    return value


def suppress_project_node_ids(text: Any, *, allow_node_ids: bool) -> str:
    value = str(text or "")
    if allow_node_ids:
        return value
    value = re.sub(r"其中\s*N-\d{3}\s*", "其中部分候选节点", value, flags=re.IGNORECASE)
    value = re.sub(r"\bN-\d{3}\b", "候选节点", value, flags=re.IGNORECASE)
    return value


def ai_session_to_markdown(session: dict[str, Any], instruction: str | None = None) -> str:
    title = session.get("title") or "AI 会话报告"
    messages = session.get("messages", [])
    scope = "单节点沟通" if session.get("node_id") else "项目综合沟通"
    latest_ai = next((item for item in reversed(messages) if item.get("role") == "assistant"), None)
    latest_summary = suppress_project_node_ids(
        humanize_report_text(latest_ai.get("content", "暂无 AI 总结。") if latest_ai else "暂无 AI 总结。"),
        allow_node_ids=bool(session.get("node_id")),
    )
    lines = [
        f"# {humanize_report_text(title)}",
        "",
        "> 这是一份待人工确认的沟通工作稿，用于整理项目理解、资料缺口和下一步动作；不能直接作为最终推荐、最终排序、收益预测或 ROI。",
        "",
        "## 1. 摘要",
        "",
        f"- 项目：{humanize_report_text(session.get('project_name') or '当前选址项目')}",
        f"- 范围：{scope}",
        f"- 生成时间：{datetime.now().isoformat(timespec='seconds')}",
        "- 当前判断：资料仍需人工复核，尚不能升级为最终商业结论。",
        "",
        "## 2. 关键依据",
        "",
        "- 依据来自本次 AI 工作台对话、已上传资料说明、当前项目上下文和节点/资料缺口状态。",
        "- 若对话中出现截图、图纸、经营数据或现场描述，应继续回到资料池登记来源和用途。",
    ]
    if instruction:
        lines.extend(["- 本次生成要求：" + humanize_report_text(instruction)])
    lines.extend([
        "",
        "## 3. 当前缺口",
        "",
        "- 真实客流、转化率、收益成本、运营授权和可信几何资料仍需内部复核。",
        "- 所有报告判断都应继续标注为待人工确认，避免被误读为最终选址结论。",
        "",
        "## 4. AI 整理稿",
        "",
        latest_summary,
        "",
        "## 5. 推进事项",
        "",
        "- 复核真实客流、转化率、收益成本、运营授权和可信几何资料。",
        "- 人工确认报告语气、证据来源、节点归属和资料用途。",
        "- 确认后再决定是否进入正式报告或继续拆分为节点任务。",
        "",
        "## 附录：对话记录",
        "",
    ])
    if not messages:
        lines.append("暂无可整理的对话内容。")
    for item in messages:
        role = "用户" if item.get("role") == "user" else "AI"
        lines.extend([
            f"### {role} · {item.get('created_at', '')}",
            "",
            humanize_report_text(item.get("content")),
            "",
        ])
    return "\n".join(lines).replace("\r\n", "\n")


def write_ai_session_report(session: dict[str, Any], instruction: str | None = None) -> dict[str, Any]:
    report_dir = REPORT_DIR / "ai_chat_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    safe_id = re.sub(r"[^0-9A-Za-z_-]", "_", session.get("session_id", "chat"))
    path = report_dir / f"{safe_id}.md"
    content = ai_session_to_markdown(session, instruction)
    path.write_text(content, encoding="utf-8")
    return {
        "output_status": "needs_review",
        "not_final": True,
        "report_path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "download_url": f"/api/ai/sessions/{session.get('session_id')}/report/download",
        "byte_size": path.stat().st_size,
    }


def load_upload_index() -> list[dict[str, Any]]:
    uploaded = []
    if UPLOAD_INDEX_FILE.exists():
        try:
            data = json.loads(UPLOAD_INDEX_FILE.read_text(encoding="utf-8"))
            uploaded = data if isinstance(data, list) else []
        except json.JSONDecodeError:
            uploaded = []
    return [normalize_upload_row(row) for row in uploaded]


def normalize_upload_purpose(value: str | None, filename: str = "") -> str:
    raw = str(value or "").strip()
    legacy_map = {
        "auto": "",
        "方案文件": "项目计划",
        "项目规划": "项目计划",
        "项目方案": "项目计划",
        "CAD / 图纸": "地图/CAD/平面图",
        "图纸材料": "地图/CAD/平面图",
        "现场图片 / 位置图": "现场照片/截图",
        "客流数据": "客流/TGI",
        "数据表": "客流/TGI",
        "其他资料": "其他",
    }
    raw = legacy_map.get(raw, raw)
    valid = {"项目计划", "地图/CAD/平面图", "客流/TGI", "POI/竞品", "经营收益/成本", "现场照片/截图", "其他"}
    if raw in valid:
        return raw
    return guess_upload_category(filename)


def normalize_upload_row(row: dict[str, Any]) -> dict[str, Any]:
    filename = str(row.get("filename") or "")
    purpose = normalize_upload_purpose(row.get("purpose") or row.get("category"), filename)
    review_status = str(row.get("review_status") or "待解析")
    adopted = bool(row.get("is_used") if "is_used" in row else review_status in {"已启用", "已采用", "已确认入池"})
    parse_status = str(row.get("parse_status") or ("已解析" if review_status in {"已启用", "已采用", "已确认入池"} else "待解析"))
    effect_map = {
        "项目计划": "可生成待复核节点草案，仍需人工确认。",
        "地图/CAD/平面图": "可补充位置描述，但 DWG 未转换前不能当作精确坐标或面积。",
        "客流/TGI": "可用于需求缺口判断，进入 checked 前仍需复核来源。",
        "POI/竞品": "可用于供给判断，需与高德/现场口径交叉核验。",
        "经营收益/成本": "可提高报告成熟度，但不能直接输出 ROI 或最终收益预测。",
        "现场照片/截图": "可辅助复核现场条件和节点位置。",
        "其他": "先登记到资料池，确认用途后再采用。",
    }
    return {
        **row,
        "purpose": purpose,
        "category": purpose,
        "review_status": review_status,
        "parse_status": parse_status,
        "parse_error_message": row.get("parse_error_message") or row.get("parse_error") or "",
        "is_used": adopted,
        "used_in_project": "已用于项目" if adopted else "暂未采用",
        "adoption_status": "已采用" if adopted else ("已放弃使用" if review_status == "已放弃" else "暂未采用"),
        "project_effect": effect_map.get(purpose, effect_map["其他"]),
    }


def save_upload_index(rows: list[dict[str, Any]]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    normalized = [normalize_upload_row(row) for row in rows]
    UPLOAD_INDEX_FILE.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    for row in normalized:
        upsert_runtime_upload(row)


def guess_upload_category(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if any(token in filename for token in ["项目计划", "项目规划", "方案", "project", "plan"]):
        return "项目计划"
    if any(token in filename for token in ["poi", "竞品", "商业", "供给"]):
        return "POI/竞品"
    if any(token in filename for token in ["收益", "成本", "租金", "revenue", "cost"]):
        return "经营收益/成本"
    if any(token in filename for token in ["客流", "人流", "游客", "visitor", "flow"]):
        return "客流/TGI"
    if suffix in {".dwg", ".dxf"}:
        return "地图/CAD/平面图"
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
        return "现场照片/截图"
    if suffix in {".csv", ".xlsx", ".xls"}:
        return "客流/TGI"
    if suffix in {".pdf", ".docx", ".doc", ".pptx", ".ppt"}:
        return "项目计划"
    return "其他"


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


def load_node_drafts() -> list[dict[str, Any]]:
    if not NODE_DRAFTS_FILE.exists():
        return []
    try:
        data = json.loads(NODE_DRAFTS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    rows = data if isinstance(data, list) else []
    drafts = dedupe_node_drafts([normalize_node_draft(row, index) for index, row in enumerate(rows)])
    if len(drafts) != len(rows):
        save_node_drafts(drafts)
    return drafts


def save_node_drafts(rows: list[dict[str, Any]]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    NODE_DRAFTS_FILE.write_text(json.dumps(dedupe_node_drafts(rows), ensure_ascii=False, indent=2), encoding="utf-8")


def node_draft_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    if row.get("source") == "project_plan_import":
        directions = row.get("business_direction") or row.get("candidate_business_formats") or []
        if isinstance(directions, list):
            direction_key = "|".join(sorted(str(item).strip() for item in directions if str(item).strip()))
        else:
            direction_key = str(directions).strip()
        return (
            "project_plan_import",
            str(row.get("node_name") or "").strip(),
            str(row.get("location_description") or row.get("primary_positioning") or "").strip(),
            direction_key,
        )
    return ("manual", str(row.get("node_id") or ""), "", "")


def dedupe_node_drafts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str, str]] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        key = node_draft_key(row)
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def next_node_draft_id(rows: list[dict[str, Any]]) -> str:
    used = {str(row.get("node_id") or "") for row in rows}
    index = len(used) + 1
    while True:
        node_id = f"N-{index:03d}"
        if node_id not in used:
            return node_id
        index += 1


def normalize_node_draft(row: dict[str, Any], index: int = 0) -> dict[str, Any]:
    node_id = str(row.get("node_id") or f"N-{index + 1:03d}")
    directions = row.get("business_direction")
    if isinstance(directions, str):
        business_direction = [item.strip() for item in re.split(r"[、,，;；]", directions) if item.strip()]
    elif isinstance(directions, list):
        business_direction = [str(item) for item in directions if str(item).strip()]
    else:
        business_direction = []
    return {
        **row,
        "node_id": node_id,
        "node_name": str(row.get("node_name") or node_id),
        "location_description": str(row.get("location_description") or row.get("primary_positioning") or ""),
        "primary_positioning": str(row.get("primary_positioning") or row.get("location_description") or "位置描述待复核"),
        "business_direction": business_direction,
        "candidate_business_formats": business_direction,
        "area_sqm": str(row.get("area_sqm") or "待测"),
        "note": str(row.get("note") or ""),
        "enabled": bool(row.get("enabled", True)),
        "review_status": "待复核",
        "status_label": "待复核",
        "source": row.get("source") or "manual_node_draft",
        "output_status": "needs_review",
        "not_final": True,
        "discussion_score": row.get("discussion_score") or "",
        "discussion_score_draft": row.get("discussion_score_draft") or 0,
        "priority_score_internal": row.get("priority_score_internal") or 0,
        "priority_stage": "复核资料后再比较",
        "priority_label": "复核资料后再比较",
        "priority_summary": "节点草案来自资料导入或人工新增，尚未完成图纸、客流和经营数据复核；现在只能进入讨论池，不能进入推荐判断。",
        "priority_recommendations": [
            "先补完整位置描述和业态方向，确认它是不是一个真实可讨论的落位点。",
            "关联项目计划、图纸、客流或现场照片后，再参与节点优先级比较。",
            "如果只是临时想法，可以保留为草案，但不要进入报告推荐。",
        ],
        "priority_basis": [
            {
                "label": "当前用途",
                "value": "讨论池草案",
                "impact": "这是导入或人工新增的节点草案，先用于整理问题；位置、客流、经营数据完成内部复核后再参与优先级比较。",
                "status": "待复核",
            },
            {
                "label": "当前缺口",
                "value": "资料不足",
                "impact": "至少需要项目图纸、客流/TGI、经营收益/成本，才能形成有解释力的推进建议。",
                "status": "需复核",
            },
        ],
        "score_status": "node_draft_review_required",
        "score_label": "待复核",
        "score_explanation": "节点草案来自资料导入或人工新增，尚未完成图纸、客流和经营数据复核。",
        "score_recommendations": [
            "先补完整位置描述和业态方向，确认它是不是一个真实可讨论的落位点。",
            "关联项目计划、图纸、客流或现场照片后，再参与节点优先级比较。",
            "如果只是临时想法，可以保留为草案，但不要进入报告推荐。"
        ],
        "score_breakdown": [
            {
                "label": "当前用途",
                "value": "讨论池草案",
                "impact": "这是导入或人工新增的节点草案，先进入讨论池；位置、客流、经营数据完成内部复核后再参与优先级排序。",
                "status": "待复核",
            },
            {
                "label": "当前缺口",
                "value": "资料不足",
                "impact": "至少需要项目图纸、客流/TGI、经营收益/成本，才能形成有解释力的推进建议。",
                "status": "需复核",
            },
        ],
        "missing_required_fields": row.get("missing_required_fields") or ["项目图纸", "客流/TGI", "经营收益/成本"],
        "next_data_needed": row.get("next_data_needed") or ["复核节点位置", "补充客流/TGI", "补充经营收益/成本"],
        "data_requests": row.get("data_requests") or [],
        "feedback_scenarios": row.get("feedback_scenarios") or [],
        "assumption_refs": row.get("assumption_refs") or [],
        "schematic_position": row.get("schematic_position") or {
            "x": 18 + (index % 3) * 30,
            "y": 28 + (index // 3) * 34,
        },
    }


def build_plan_node_drafts(upload: dict[str, Any], existing: list[dict[str, Any]]) -> list[dict[str, Any]]:
    base_name = Path(str(upload.get("filename") or "项目计划")).stem[:18] or "项目计划"
    directions = ["轻餐饮", "便利零售", "亲子服务"]
    locations = ["主入口周边", "核心游线交汇处", "临水或停留空间"]
    drafts: list[dict[str, Any]] = []
    rows = list(existing)
    for location, direction in zip(locations, directions):
        node_id = next_node_draft_id(rows + drafts)
        drafts.append(
            normalize_node_draft(
                {
                    "node_id": node_id,
                    "node_name": f"{base_name}-{location}",
                    "location_description": location,
                    "business_direction": [direction],
                    "area_sqm": "待测",
                    "note": f"由 {upload.get('filename')} 生成的节点草案，需人工复核。",
                    "enabled": True,
                    "source": "project_plan_import",
                    "source_upload_id": upload.get("upload_id"),
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                },
                len(rows) + len(drafts),
            )
        )
    return drafts


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


def local_source_inventory() -> list[dict[str, Any]]:
    extracted_briefs = load_local_source_briefs()
    roots = [ROOT / "20_raw_data", ROOT / "CAD图及其计划"]
    rows: list[dict[str, Any]] = []
    for base in roots:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            if suffix not in {".pdf", ".ppt", ".pptx", ".docx", ".dwg", ".xlsx", ".xls", ".csv", ".jpg", ".jpeg", ".png"}:
                continue
            rel = str(path.relative_to(ROOT)).replace("\\", "/")
            if "ppt" in rel.lower() or suffix in {".ppt", ".pptx"}:
                role = "表达参考 / 方案材料"
            elif suffix == ".dwg":
                role = "图纸材料 / 待转换"
            elif suffix == ".docx":
                role = "项目计划 / 待解析"
            elif suffix == ".pdf":
                role = "报告或图纸 PDF / 待核验"
            else:
                role = "补充资料 / 待识别"
            rows.append({
                "filename": path.name,
                "relative_path": rel,
                "type": suffix.lstrip("."),
                "size_kb": round(path.stat().st_size / 1024, 1),
                "role": role,
                "content_status": extracted_briefs.get(path.name, {}).get("content_status", "仅识别到文件清单，尚未向 AI 提供全文"),
                "brief": extracted_briefs.get(path.name, {}).get("brief", ""),
            })
    return rows[:24]


def load_local_source_briefs() -> dict[str, dict[str, str]]:
    briefs: dict[str, dict[str, str]] = {}
    plan_text = ROOT / "30_extraction" / "p2_real_site" / "osen_project_plan_text.txt"
    if plan_text.exists():
        text = plan_text.read_text(encoding="utf-8", errors="ignore")
        briefs["奥森重点项目策划思路20260521.docx"] = {
            "content_status": "已抽取正文摘要，可引用为策划思路，但仍需人工复核",
            "brief": re.sub(r"\s+", " ", text[:900]).strip(),
        }
    ppt_dir = ROOT / "30_extraction" / "ppt_text"
    if ppt_dir.exists():
        for path in ppt_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            slides = data.get("slides", []) if isinstance(data, dict) else []
            slide_text = " ".join(str(slide.get("text", "")) for slide in slides[:5])
            briefs[f"{path.stem}.pptx"] = {
                "content_status": "已抽取部分页文本，只作为表达和方案假设参考",
                "brief": re.sub(r"\s+", " ", slide_text[:900]).strip(),
            }
    source_inventory_path = ROOT / "30_extraction" / "extraction_logs" / "source_inventory.json"
    if source_inventory_path.exists():
        try:
            inventory = json.loads(source_inventory_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            inventory = {}
        for item in inventory.get("files", []):
            name = item.get("file_name")
            if not name:
                continue
            role = item.get("role", "")
            strength = item.get("evidence_strength_default", "")
            briefs.setdefault(name, {
                "content_status": "已建资料目录，未向 AI 提供全文",
                "brief": "",
            })
            briefs[name]["catalog_role"] = role
            briefs[name]["evidence_strength_default"] = strength
    return briefs


def summarize_gap_context(payload: dict[str, Any]) -> dict[str, Any]:
    gates = payload.get("p3_gates", [])
    gaps = payload.get("p2_gaps", [])
    blocked = [
        gate.get("calibration_domain") or gate.get("gate_name") or gate.get("gate_id")
        for gate in gates
        if "pass" not in str(gate.get("gate_status") or gate.get("status") or "").lower()
    ]
    gap_names = [
        gap.get("gap_name") or gap.get("missing_input") or gap.get("gap_id")
        for gap in gaps
        if gap.get("gap_name") or gap.get("missing_input") or gap.get("gap_id")
    ]
    return {
        "blocked_domains": [item for item in blocked if item][:8],
        "missing_inputs": [item for item in gap_names if item][:10],
        "business_language_rule": "对用户回答时不要使用 P2/P3/GATE 编号；改说图纸、客流、转化、收益成本、运营授权等业务缺口。",
    }


def save_cache(cache: dict[str, Any]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def node_context(payload: dict[str, Any], node_id: str | None) -> dict[str, Any]:
    if not node_id:
        nodes = payload.get("nodes", [])
        score_status_counts: dict[str, int] = {}
        positioning_options: list[str] = []
        for node in nodes:
            status = str(node.get("score_status") or node.get("output_status") or "unknown")
            score_status_counts[status] = score_status_counts.get(status, 0) + 1
            positioning = str(node.get("primary_positioning") or "").strip()
            if positioning and positioning not in positioning_options:
                positioning_options.append(positioning)
        feedback_rows = load_feedback()
        return {
            "scope": "project_overall",
            "project": payload.get("meta", {}),
            "map_context": payload.get("amap", {}).get("map_context", {}),
            "local_source_inventory": local_source_inventory(),
            "node_overview": {
                "node_count": len(nodes),
                "score_status_counts": score_status_counts,
                "positioning_options": positioning_options[:12],
                "detail_rule": "项目综合对话不列出具体节点 ID 或节点名称；需要单点分析时由用户在节点清单中明确选择。",
            },
            "gap_context": summarize_gap_context(payload),
            "uploads": payload.get("uploads", []),
            "upload_candidates": payload.get("upload_candidates", []),
            "demand_supply_status": {
                "output_status": payload.get("demand_supply", {}).get("output_status"),
                "not_final": payload.get("demand_supply", {}).get("not_final"),
                "message": payload.get("demand_supply", {}).get("gap", {}).get("message"),
            },
            "controlled_feature_scenes": {
                "items": selected_feature_derivative_inputs(limit=8),
                "usage_rule": "只把用户采用或锁定的人物场景作为待复核输入；不得把覆盖池全部自动当成仿真结果。",
                "income_rule": "回答时必须把收入/消费价格带作为影响价格、转化、业态和建议强度的变量，而不是一句背景描述。",
            },
            "expert_feedback_summary": {
                "feedback_count": len(feedback_rows),
                "usage_rule": "这里只告诉 AI 有反馈待整理，不把旧节点反馈原文带入项目综合回答。",
            },
            "writing_style_rule": "回答给业务人员看：先摘要，再依据，再缺口，再推进事项；少用编号代码，少讲系统内部状态。",
            "source_claim_rule": "只能说“资料清单显示”或“已抽取摘要显示”；不要声称已经完整读完所有 PPT/PDF/DWG/DOCX。",
            "boundary_notice": "这是项目综合上下文，不绑定任何单个节点；只有用户明确选择节点时才进入节点分析。",
        }
    node = next((item for item in payload["nodes"] if item.get("node_id") == node_id), None)
    if not node:
        return {
            "node": {
                "node_id": node_id,
                "node_name": "未找到的节点",
                "output_status": "needs_review",
                "not_final": True,
            },
            "p3_gates": payload["p3_gates"],
            "p2_gaps": payload["p2_gaps"],
            "uploads": payload.get("uploads", []),
            "upload_candidates": payload.get("upload_candidates", []),
            "demand_supply": payload.get("demand_supply", {}),
            "expert_feedback": load_feedback()[-8:],
        }
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
    feature_scene_context = controlled_feature_scene_context(limit=8)
    calibration_context = real_calibration_context(limit=10)
    common_boundary = (
        "你是公园商业选址专家驾驶舱的 DeepSeek AI 草稿助手。"
        "只能输出 needs_review / not_final 的反馈草案解释。"
        "不得输出最终推荐、最终排序、收益预测、坐标、面积推断、DWG 几何结论或 checked 证据。"
        "必须说明为什么当前只是 feedback draft，并列出缺失数据。"
        "如果用户已采用或锁定人物场景，必须把收入水平、消费价格带、时段、天气、空间节点和需求触发作为约束变量；"
        "不能把这些场景当真实客群占比或最终仿真结果。"
        "如果使用真实校准输入，必须区分官方宏观边界、本地大数据画像/代理变量和PPT方案假设；"
        "不得把设备价格代理或PPT假设写成街道级收入、真实成交或最终收益。"
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
            f"用户采用/锁定的人物场景输入：{json.dumps(feature_scene_context, ensure_ascii=False)}\n"
            f"真实校准输入：{json.dumps(calibration_context, ensure_ascii=False)}\n"
            f"P3 gate：{json.dumps(gates, ensure_ascii=False)}"
        )
    if not selected:
        raise HTTPException(status_code=404, detail="node_id not found")
    return (
        f"{common_boundary}\n"
        "请对当前节点做方案解释，并给合作方提问清单。"
        "输出 JSON，字段为 output_status, node_explanation, why_feedback_draft, missing_data, partner_questions, discussion_priority_note。\n"
        f"当前节点：{json.dumps(selected, ensure_ascii=False)}\n"
        f"用户采用/锁定的人物场景输入：{json.dumps(feature_scene_context, ensure_ascii=False)}\n"
        f"真实校准输入：{json.dumps(calibration_context, ensure_ascii=False)}\n"
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
        "priority_fields": ["priority_stage", "priority_summary", "priority_recommendations", "priority_basis"],
        "legacy_internal_score_field": "discussion_score_draft",
    }
    return payload


@app.get("/api/object-chain")
def api_object_chain() -> dict[str, Any]:
    payload = load_dashboard()
    return payload["object_chain"]


@app.get("/api/supply-gap")
def api_supply_gap() -> dict[str, Any]:
    payload = load_dashboard()
    return payload["demand_supply"]


@app.get("/api/visitor-simulation")
def api_visitor_simulation() -> dict[str, Any]:
    payload = load_dashboard()
    return {
        **review_meta(source_hint="web uploaded visitor flow sources", status_label="游客仿真 / 待复核"),
        "visitor_sources": payload["demand_supply"]["visitor_sources"],
        "tgi": payload["demand_supply"]["tgi"],
    }


@app.get("/api/simulation/task-preflight")
def api_simulation_task_preflight() -> dict[str, Any]:
    return build_simulation_task_preflight()


@app.post("/api/simulation/task-preflight")
def api_save_simulation_task_preflight(request: SimulationTaskPreflightRequest) -> dict[str, Any]:
    return build_simulation_task_preflight(request.model_dump())


@app.get("/api/simulation/feature-derivatives")
def api_feature_derivatives(limit: int = 8) -> dict[str, Any]:
    safe_limit = min(max(limit, 1), 48)
    return build_feature_derivative_pool(limit=safe_limit)


@app.get("/api/simulation/real-calibration-supplements")
def api_real_calibration_supplements() -> dict[str, Any]:
    supplements = load_real_calibration_supplements()
    return {
        **review_meta(source_hint="real_calibration_supplements.json + generated calibration package", status_label="真实校准补充 / 待人工复核"),
        "count": len(supplements),
        "items": supplements,
        "real_calibration_context": real_calibration_context(limit=12),
    }


@app.post("/api/simulation/real-calibration-supplements")
def api_create_real_calibration_supplement(request: RealCalibrationSupplementRequest) -> dict[str, Any]:
    rows = load_real_calibration_supplements()
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    payload = normalize_real_calibration_supplement(request.model_dump())
    payload["supplement_id"] = f"RC-SUP-{stamp}-{len(rows) + 1:03d}"
    payload["created_at"] = datetime.now().isoformat(timespec="seconds")
    payload["updated_at"] = payload["created_at"]
    rows.append(payload)
    save_real_calibration_supplements(rows)
    rebuild = rebuild_real_calibration_outputs()
    return {"item": payload, "count": len(rows), "rebuild": rebuild}


@app.patch("/api/simulation/real-calibration-supplements/{supplement_id}")
def api_update_real_calibration_supplement(supplement_id: str, request: RealCalibrationSupplementPatchRequest) -> dict[str, Any]:
    rows = load_real_calibration_supplements()
    index = next((i for i, row in enumerate(rows) if row.get("supplement_id") == supplement_id), None)
    if index is None:
        raise HTTPException(status_code=404, detail="real calibration supplement not found")
    updated = dict(rows[index])
    for key, value in request.model_dump(exclude_none=True).items():
        updated[key] = value
    updated["updated_at"] = datetime.now().isoformat(timespec="seconds")
    rows[index] = normalize_real_calibration_supplement(updated)
    rows[index]["supplement_id"] = supplement_id
    save_real_calibration_supplements(rows)
    rebuild = rebuild_real_calibration_outputs()
    return {"item": rows[index], "count": len(rows), "rebuild": rebuild}


@app.delete("/api/simulation/real-calibration-supplements/{supplement_id}")
def api_delete_real_calibration_supplement(supplement_id: str) -> dict[str, Any]:
    rows = load_real_calibration_supplements()
    if not any(row.get("supplement_id") == supplement_id for row in rows):
        raise HTTPException(status_code=404, detail="real calibration supplement not found")
    remaining = [row for row in rows if row.get("supplement_id") != supplement_id]
    save_real_calibration_supplements(remaining)
    rebuild = rebuild_real_calibration_outputs()
    return {"deleted": supplement_id, "count": len(remaining), "rebuild": rebuild}


@app.patch("/api/simulation/feature-derivatives/{derivative_id}")
def api_update_feature_derivative(derivative_id: str, request: FeatureDerivativeActionRequest) -> dict[str, Any]:
    rows = read_csv_rows(FEATURE_DERIVATIVE_CSV)
    if not any(str(row.get("derivative_id") or "") == derivative_id for row in rows):
        raise HTTPException(status_code=404, detail="feature derivative not found")
    controls = load_feature_derivative_controls()
    control = controls.get(derivative_id, {}) if isinstance(controls.get(derivative_id, {}), dict) else {}
    action = request.action.strip()
    if action == "use":
        control["adoption_status"] = "已采用"
    elif action == "discard":
        control["adoption_status"] = "已放弃"
    elif action == "restore":
        control["adoption_status"] = "暂未采用"
    elif action == "lock":
        control["user_locked"] = True
    elif action == "unlock":
        control["user_locked"] = False
    else:
        raise HTTPException(status_code=400, detail="action must be use, discard, restore, lock, or unlock")
    if request.note.strip():
        notes = control.get("review_notes", [])
        notes = notes if isinstance(notes, list) else []
        notes.append(request.note.strip())
        control["review_notes"] = notes[-20:]
    control["updated_at"] = datetime.now().isoformat(timespec="seconds")
    controls[derivative_id] = control
    save_feature_derivative_controls(controls)
    return build_feature_derivative_pool(limit=8)


@app.get("/api/reports/site-selection")
def api_site_selection_report() -> dict[str, Any]:
    payload = load_dashboard()
    report = payload["demand_supply"]["report"]
    write_report_files(report, REPORT_DIR)
    docx_result = build_osen_business_report_outputs()
    return {
        **review_meta(source_hint="web uploads + AMap POI + gap calculator + business report writer", status_label="报告 / 平台生成"),
        "report": report,
        "download": {
            "docx": "/api/reports/site-selection/download?format=docx",
            "md": "/api/reports/site-selection/download?format=md",
            "json": "/api/reports/site-selection/download?format=json",
        },
        "docx": docx_result,
        "report_style": "奥森商业改造预测与调整建议 / 20260607",
    }


@app.get("/api/reports/site-selection/download")
def api_download_site_selection_report(format: str = "md") -> Response:
    payload = load_dashboard()
    report = payload["demand_supply"]["report"]
    write_report_files(report, REPORT_DIR)
    docx_result = build_osen_business_report_outputs()
    if format == "docx":
        docx_path = Path(docx_result["docx"])
        return FileResponse(
            path=docx_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=docx_result.get("download_filename") or "osen_business_decision_report_20260607.docx",
        )
    if format == "json":
        return Response(
            content=json.dumps(report, ensure_ascii=False, indent=2),
            media_type="application/json; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="site_selection_gap_report_latest.json"'},
        )
    return Response(
        content=report_to_markdown(report),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="site_selection_gap_report_latest.md"'},
    )


@app.get("/api/uploads")
def uploads() -> dict[str, Any]:
    items = load_upload_index()
    return {
        **review_meta(source_hint="uploaded_sources.json + runtime_uploads", status_label="资料池 / 待解析"),
        "count": len(items),
        "db_runtime_count": len(list_runtime_uploads()),
        "items": items,
        "accepted_categories": ["CAD / 图纸", "现场图片 / 位置图", "客流数据", "数据表", "方案文件", "其他资料"],
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


@app.patch("/api/uploads/{upload_id}")
def update_upload_status(upload_id: str, payload: UploadActionRequest) -> dict[str, Any]:
    rows = load_upload_index()
    row = next((item for item in rows if item.get("upload_id") == upload_id), None)
    if not row:
        raise HTTPException(status_code=404, detail="upload not found")
    labels = {
        "use": "已启用",
        "discard": "已放弃",
        "restore": "待 AI 解析",
    }
    if payload.action not in labels:
        raise HTTPException(status_code=400, detail="action must be use, discard, or restore")
    row["review_status"] = labels[payload.action]
    row["updated_at"] = datetime.now().isoformat(timespec="seconds")
    row["output_status"] = "needs_review"
    row["not_final"] = True
    save_upload_index(rows)
    return row


@app.delete("/api/uploads/{upload_id}")
def delete_upload(upload_id: str) -> dict[str, Any]:
    rows = load_upload_index()
    row = next((item for item in rows if item.get("upload_id") == upload_id), None)
    if not row:
        raise HTTPException(status_code=404, detail="upload not found")
    remaining = [item for item in rows if item.get("upload_id") != upload_id]
    save_upload_index(remaining)

    candidates = [item for item in load_upload_candidates() if item.get("upload_id") != upload_id]
    save_upload_candidates(candidates)

    stored_path = resolve_project_path(row.get("stored_path", ""))
    deleted_file = False
    try:
        if stored_path.exists() and UPLOAD_DIR in stored_path.parents:
            stored_path.unlink()
            deleted_file = True
    except OSError:
        deleted_file = False
    return {
        "upload_id": upload_id,
        "status": "deleted",
        "deleted_file": deleted_file,
        "output_status": "needs_review",
        "not_final": True,
    }


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


@app.post("/api/nodes")
def create_node(payload: NodeDraftRequest) -> dict[str, Any]:
    rows = load_node_drafts()
    node = normalize_node_draft(
        {
            "node_id": next_node_draft_id(rows),
            "node_name": payload.node_name.strip() or "未命名节点",
            "location_description": payload.location_description,
            "business_direction": payload.business_direction,
            "area_sqm": payload.area_sqm or "待测",
            "note": payload.note,
            "enabled": payload.enabled,
            "source": "manual_node_draft",
            "created_at": datetime.now().isoformat(timespec="seconds"),
        },
        len(rows),
    )
    rows.append(node)
    save_node_drafts(rows)
    return node


@app.patch("/api/nodes/{node_id}")
def update_node(node_id: str, payload: NodeDraftRequest) -> dict[str, Any]:
    rows = load_node_drafts()
    index = next((i for i, row in enumerate(rows) if row.get("node_id") == node_id), None)
    if index is None:
        raise HTTPException(status_code=404, detail="节点未找到")
    rows[index] = normalize_node_draft(
        {
            **rows[index],
            "node_name": payload.node_name.strip() or rows[index].get("node_name"),
            "location_description": payload.location_description,
            "business_direction": payload.business_direction,
            "area_sqm": payload.area_sqm or "待测",
            "note": payload.note,
            "enabled": payload.enabled,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        },
        index,
    )
    save_node_drafts(rows)
    return rows[index]


@app.delete("/api/nodes/{node_id}")
def delete_node(node_id: str) -> dict[str, Any]:
    rows = load_node_drafts()
    remaining = [row for row in rows if row.get("node_id") != node_id]
    if len(remaining) == len(rows):
        raise HTTPException(status_code=404, detail="节点未找到，历史节点请先由资料生成后再编辑。")
    save_node_drafts(remaining)
    return {"node_id": node_id, "status": "已删除"}


@app.post("/api/nodes/generate-from-plan")
def generate_nodes_from_plan() -> dict[str, Any]:
    uploads = load_upload_index()
    plans = [row for row in uploads if row.get("purpose") == "项目计划" and row.get("is_used")]
    if not plans:
        raise HTTPException(status_code=400, detail="请先上传并采用项目计划。")
    rows = load_node_drafts()
    source_ids = {row.get("source_upload_id") for row in rows}
    created: list[dict[str, Any]] = []
    for plan in plans:
        if plan.get("upload_id") in source_ids:
            continue
        created.extend(build_plan_node_drafts(plan, rows + created))
    if created:
        rows.extend(created)
        save_node_drafts(rows)
    return {
        "created_count": len(created),
        "items": created,
        "message": "已生成节点草案，所有节点仍需人工复核。",
    }


@app.get("/api/amap/status")
def amap_proxy_status() -> dict[str, Any]:
    points = load_amap_supply()
    return {**amap_status(points), "static_map": load_amap_static_status(), "map_context": load_map_context()}


@app.get("/api/amap/js-config")
def amap_js_config() -> dict[str, Any]:
    load_local_env()
    js_key = os.environ.get("AMAP_JS_API_KEY") or os.environ.get("AMAP_WEB_SERVICE_KEY") or ""
    security_code = os.environ.get("AMAP_JS_SECURITY_CODE") or ""
    return {
        "output_status": "needs_review",
        "not_final": True,
        "available": bool(js_key),
        "key": js_key,
        "security_code": security_code,
        "using_web_service_key_as_fallback": bool(js_key and not os.environ.get("AMAP_JS_API_KEY")),
        "message": (
            "已配置高德 JS API key，可加载可拖拽地图。"
            if js_key
            else "缺少 AMAP_JS_API_KEY；请在 .env 中配置高德 Web端 JS API key。"
        ),
    }


@app.post("/api/amap/context")
def update_amap_context(payload: MapContextRequest) -> dict[str, Any]:
    keyword = payload.keyword.strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="keyword is required")
    normalized_keyword = MAP_KEYWORD_ALIASES.get(keyword.lower(), keyword)
    load_local_env()
    key = os.environ.get("AMAP_WEB_SERVICE_KEY")
    if not key:
        raise HTTPException(status_code=400, detail=map_search_error_detail())
    if payload.longitude and payload.latitude:
        lon, lat = payload.longitude, payload.latitude
        poi = {"name": payload.matched_name or normalized_keyword, "address": payload.address or ""}
    else:
        params = {"key": key, "keywords": normalized_keyword, "city": "全国", "offset": "1", "page": "1", "extensions": "base"}
        data = amap_get_json("https://restapi.amap.com/v3/place/text", params=params)
        pois = data.get("pois") or []
        if not pois:
            suggestions = amap_input_tips(keyword, key)
            if suggestions:
                detail = map_search_error_detail()
                detail["suggestions"] = suggestions
                raise HTTPException(status_code=404, detail=detail)
            raise HTTPException(status_code=404, detail=map_search_error_detail())
        poi = pois[0]
        location = poi.get("location", "")
        if "," not in location:
            raise HTTPException(status_code=502, detail=map_search_error_detail())
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
            "detail": f"地图目标已更新为：{context['matched_name'] or keyword}；前端高德 JS 地图将重新定位并刷新 POI。",
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
        data = amap_get_json(
            "https://restapi.amap.com/v3/assistant/inputtips",
            params={"key": key, "keywords": normalized_keyword, "city": "全国", "datatype": "all"},
            timeout=8.0,
            retries=1,
        )
        place_keywords = [normalized_keyword]
        if preferred_name and preferred_name != normalized_keyword:
            place_keywords.append(preferred_name)
        for place_keyword in place_keywords:
            place_data = amap_get_json(
                "https://restapi.amap.com/v3/place/text",
                params={
                    "key": key,
                    "keywords": place_keyword,
                    "city": "全国",
                    "offset": "3",
                    "page": "1",
                    "extensions": "base",
                },
                timeout=8.0,
                retries=1,
            )
            exact_pois.extend(place_data.get("pois") or [])
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
    load_local_env()
    payload = load_dashboard()
    points = load_amap_supply()
    deepseek_cache = load_cache()
    gap = payload.get("demand_supply", {}).get("gap", {})
    return {
        "output_status": "needs_review",
        "not_final": True,
        "display_policy": "show_only_failed_or_warning_items",
        "items": [
            {
                "name": "节点与反馈资料",
                "kind": "local_data",
                "status": "connected",
                "detail": f"已读取 {len(payload['nodes'])} 个节点、{len(payload['p4_feedback']['data_requests'])} 条合作方数据请求。",
            },
            {
                "name": "资料闭合清单",
                "kind": "local_data",
                "status": "connected",
                "detail": f"已读取 {len(payload['p3_gates'])} 个待确认事项；仅表示当前资料闭合状态。",
            },
            {
                "name": "AI 对话与整理",
                "kind": "ai_assistant",
                "status": "configured" if os.environ.get("DEEPSEEK_API_KEY") else "missing_key",
                "detail": f"AI 整理能力已接入，当前已有 {len(deepseek_cache)} 条沟通草稿可回看；所有内容进入人工确认流程。",
            },
            {
                "name": "高德 POI 资料",
                "kind": "map_data",
                "status": "connected",
                "detail": f"已读取 {len(points)} 条地图周边设施候选点，可用于了解当前区域的商业供给情况。",
            },
            {
                "name": "地图底图与搜索",
                "kind": "map_service",
                "status": load_amap_static_status().get("status", "not_checked_in_this_session"),
                "detail": load_amap_static_status().get("detail", "尚未在本会话检查静态图返回；失败时显示本地示意底图。"),
            },
            {
                "name": "供需缺口计算器",
                "kind": "demand_supply_gap",
                "status": "connected" if gap.get("status") == "calculated_needs_review" else "blocked",
                "detail": gap.get("message", "等待外部客流/TGI资料和当前 POI。"),
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


@app.get("/api/simulation/objects")
def api_simulation_objects() -> dict[str, Any]:
    items = load_simulation_objects()
    type_counts = Counter(str(item.get("object_type") or "") for item in items)
    adopted_count = sum(1 for item in items if item.get("adoption_status") == "已采用")
    locked_count = sum(1 for item in items if item.get("user_locked"))
    summary = {
        "persona_state": type_counts.get("persona_state", 0),
        "behavior_program": type_counts.get("behavior_program", 0),
        "choice_probability": type_counts.get("choice_probability", 0),
        "simulation_validation_target": type_counts.get("simulation_validation_target", 0),
        "adopted": adopted_count,
        "locked": locked_count,
    }
    return {
        **review_meta(source_hint="persona_state + behavior_program + choice_probability + validation_target object pool", status_label="仿真对象池 / 待复核"),
        "count": len(items),
        "type_counts": dict(type_counts),
        "summary": summary,
        "adopted_count": adopted_count,
        "locked_count": locked_count,
        "items": items,
        "usage_rule": "这些对象是人物仿真和校准的可控输入。采用或锁定后，后续自动草稿不得覆盖用户判断。",
    }


@app.post("/api/simulation/objects")
def api_create_simulation_object(request: SimulationObjectRequest) -> dict[str, Any]:
    object_type = request.object_type.strip()
    allowed_types = {"persona_state", "behavior_program", "choice_probability", "simulation_validation_target"}
    if object_type not in allowed_types:
        raise HTTPException(status_code=400, detail="object_type must be persona_state, behavior_program, choice_probability or simulation_validation_target")
    rows = load_simulation_objects()
    now = datetime.now().isoformat(timespec="seconds")
    row = normalize_simulation_object(
        {
            "object_id": next_simulation_object_id(rows, object_type),
            "object_type": object_type,
            "title": request.title.strip() or object_type_label(object_type),
            "summary": request.summary,
            "linked_id": request.linked_id or "",
            "status": request.status,
            "adoption_status": request.adoption_status,
            "priority_label": request.priority_label,
            "source_refs": request.source_refs,
            "missing_inputs": request.missing_inputs,
            "specific_advice": request.specific_advice,
            "user_locked": False,
            "created_at": now,
            "updated_at": now,
        },
        len(rows),
    )
    rows.append(row)
    save_simulation_objects(rows)
    return row


@app.patch("/api/simulation/objects/{object_id}")
def api_update_simulation_object(object_id: str, request: SimulationObjectActionRequest) -> dict[str, Any]:
    rows = load_simulation_objects()
    row = next((item for item in rows if item.get("object_id") == object_id), None)
    if not row:
        raise HTTPException(status_code=404, detail="simulation object not found")
    action = request.action.strip()
    if action == "use":
        row["adoption_status"] = "已采用"
    elif action == "discard":
        row["adoption_status"] = "已放弃"
    elif action == "restore":
        row["adoption_status"] = "暂未采用"
    elif action == "lock":
        row["user_locked"] = True
    elif action == "unlock":
        row["user_locked"] = False
    elif action == "update":
        if row.get("user_locked"):
            raise HTTPException(status_code=409, detail="object is locked; unlock before editing")
        for field in ["title", "summary", "linked_id", "priority_label"]:
            value = getattr(request, field)
            if value is not None:
                row[field] = value
        for field in ["source_refs", "missing_inputs", "specific_advice"]:
            value = getattr(request, field)
            if value is not None:
                row[field] = value
    else:
        raise HTTPException(status_code=400, detail="action must be use, discard, restore, lock, unlock, or update")
    if request.note:
        notes = split_semicolon(row.get("review_notes"))
        notes.append(request.note.strip())
        row["review_notes"] = notes
    row["updated_at"] = datetime.now().isoformat(timespec="seconds")
    row["output_status"] = "needs_review"
    row["not_final"] = True
    save_simulation_objects(rows)
    return normalize_simulation_object(row)


@app.delete("/api/simulation/objects/{object_id}")
def api_delete_simulation_object(object_id: str) -> dict[str, Any]:
    rows = load_simulation_objects()
    row = next((item for item in rows if item.get("object_id") == object_id), None)
    if not row:
        raise HTTPException(status_code=404, detail="simulation object not found")
    if row.get("user_locked"):
        raise HTTPException(status_code=409, detail="object is locked; unlock before deleting")
    remaining = [item for item in rows if item.get("object_id") != object_id]
    save_simulation_objects(remaining)
    return {
        "object_id": object_id,
        "status": "deleted",
        "output_status": "needs_review",
        "not_final": True,
    }


@app.post("/api/simulation/jobs")
def api_create_simulation_job(request: SimulationJobRequest) -> dict[str, Any]:
    import_existing_outputs()
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    job_id = f"SIM-{stamp}-{abs(request.seed) % 100000:05d}"
    request_row = request.model_dump()
    feature_scene_inputs = selected_feature_derivative_inputs(limit=12)
    calibration_context = real_calibration_context(limit=12)
    request_row["feature_scene_input_count"] = len(feature_scene_inputs)
    request_row["feature_scene_input_ids"] = [scene.get("derivative_id", "") for scene in feature_scene_inputs]
    request_row["feature_scene_usage_rule"] = "只把用户已采用或已锁定的人物场景作为结构化干跑输入；未采用的覆盖池组合不自动进入任务。"
    request_row["real_calibration_input_count"] = calibration_context["count"]
    request_row["real_calibration_input_ids"] = [item.get("calibration_id", "") for item in calibration_context.get("items", [])]
    request_row["real_calibration_strength_counts"] = calibration_context.get("source_strength_counts", {})
    request_row["real_calibration_usage_rule"] = calibration_context["usage_rule"]
    create_job(job_id, request.scenario_name, request.seed, request.iterations, request_row)
    try:
        results = run_structural_simulation(
            list_poi_candidates(limit=10000),
            list_calibration_gates(),
            seed=request.seed,
            iterations=request.iterations,
            feature_scenes=feature_scene_inputs,
            real_calibration_context=calibration_context,
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
            "feature_scene_count",
            "matched_feature_scene_count",
            "feature_scene_context",
            "scenario_pressure",
            "accuracy_context",
            "calibration_constraints",
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
    session: dict[str, Any]
    sessions_data: dict[str, Any]
    if request.session_id:
        sessions_data, session = find_ai_session(request.session_id)
    else:
        session = create_ai_session_record(
            payload,
            project_id=request.project_id,
            project_name=request.project_name,
            title=title_from_message(message),
            node_id=request.node_id,
        )
        sessions_data, session = find_ai_session(session["session_id"])
    history = session.get("messages", [])[-8:] or request.history[-8:]
    prompt = (
        "你是公园商业选址专家驾驶舱里的 DeepSeek 对话助手，像网页版对话一样连续协助专家。"
        "你可以读取项目综合上下文、明确选中的当前节点、专家意见、位置/图片文字说明、资料清单和业务缺口摘要。"
        "你的任务是：在项目综合范围内做整合分析；只有上下文里存在明确 node_id 且不是 project_overall 时，才解释单个节点。"
        "把专家意见转为模型修改建议，提示哪些字段需要内部复核和锁定口径。"
        "不要默认分析第一个节点，不要在项目综合对话里说自己正在分析某个固定节点，也不要输出具体节点 ID。"
        "硬边界：不得给最终推荐、最终排序、收益预测、坐标、面积推断、DWG几何结论或 checked 证据。"
        "不要直接说机器状态词、阶段代号、backend、debug 等内部词；对用户改说待人工确认、图纸缺口、客流缺口、收益成本缺口、运营授权缺口。"
        "不要说“我已读取全部资料/所有上下文”。如果只是看到文件清单，就说“资料清单显示”；如果上下文提供 brief，才说“已抽取摘要显示”。"
        "如果地图目标和资料主题不一致，例如地图是青年湖而文件多指向奥森，要明确提示这是项目范围冲突，先请用户确认目标公园。"
        "如果用户提到未来会给图或位置资料，只能说明应如何登记、如何进入待复核假设池。"
        "请用中文回答，不要寒暄，按业务报告口吻组织为：摘要、关键依据、当前缺口、推进事项；最后给出 3-6 条内部复核动作或口径确认问题。"
        f"\n当前上下文：{json.dumps(context, ensure_ascii=False)}"
        f"\n位置/图片文字说明：{request.position_note or ''}"
        f"\n本轮上传/关联资料：{json.dumps(request.upload_refs, ensure_ascii=False)}"
        f"\n历史对话：{json.dumps(history, ensure_ascii=False)}"
        f"\n专家/用户本轮输入：{message}"
    )
    assistant_message = ""
    generated_by = "deepseek"
    try:
        assistant_message = run_deepseek_task(
            "LLM-026",
            [
                {"role": "system", "content": "你输出给业务人员看的中文沟通稿。不要输出内部编号和机器状态词，不得升级为最终商业结论。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.15,
        )
    except Exception as exc:
        generated_by = "local_fallback"
        assistant_message = (
            "DeepSeek 当前不可用或超时。当前意见仍可先登记为专家反馈，"
            "但不能进入正式结论。下一步先复核：真实客流、转化率、收益成本、运营授权、DWG可信转换产物。"
        )
        error = f"{type(exc).__name__}: {exc}"
    else:
        error = ""
    assistant_message = suppress_project_node_ids(
        humanize_report_text(assistant_message),
        allow_node_ids=bool(request.node_id),
    )
    now = datetime.now().isoformat(timespec="seconds")
    session.setdefault("messages", []).extend([
        {"role": "user", "content": message, "upload_refs": request.upload_refs, "created_at": now},
        {"role": "assistant", "content": assistant_message, "generated_by": generated_by, "created_at": now},
    ])
    if session.get("title") == "新对话":
        session["title"] = title_from_message(message)
    session["node_id"] = request.node_id or session.get("node_id")
    session["message_count"] = len(session.get("messages", []))
    session["updated_at"] = now
    save_ai_sessions(sessions_data)
    response = {
        "output_status": "needs_review",
        "not_final": True,
        "generated_by": generated_by,
        "message": assistant_message,
        "session": {key: session.get(key) for key in ["session_id", "project_id", "project_name", "title", "node_id", "message_count", "updated_at"]},
    }
    if error:
        response["error"] = error
    return response


@app.get("/api/ai/sessions")
def list_ai_sessions() -> dict[str, Any]:
    return summarize_ai_sessions(load_ai_sessions())


@app.post("/api/ai/sessions")
def create_ai_session(request: ChatSessionCreateRequest) -> dict[str, Any]:
    session = create_ai_session_record(
        load_dashboard(),
        project_id=request.project_id,
        project_name=request.project_name,
        title=request.title,
        node_id=request.node_id,
    )
    return {
        "output_status": "needs_review",
        "not_final": True,
        "session": session,
    }


@app.get("/api/ai/sessions/{session_id}")
def get_ai_session(session_id: str) -> dict[str, Any]:
    _, session = find_ai_session(session_id)
    return {
        "output_status": "needs_review",
        "not_final": True,
        "session": session,
    }


@app.delete("/api/ai/sessions/{session_id}")
def delete_ai_session(session_id: str) -> dict[str, Any]:
    data = load_ai_sessions()
    before = len(data.get("sessions", []))
    data["sessions"] = [item for item in data.get("sessions", []) if item.get("session_id") != session_id]
    if len(data["sessions"]) == before:
        raise HTTPException(status_code=404, detail="ai session not found")
    save_ai_sessions(data)
    return {"output_status": "needs_review", "not_final": True, "deleted": session_id}


@app.post("/api/ai/sessions/{session_id}/report")
def generate_ai_session_report(session_id: str, request: ChatReportRequest) -> dict[str, Any]:
    _, session = find_ai_session(session_id)
    messages = session.get("messages", [])
    has_user_message = any(item.get("role") == "user" and str(item.get("content", "")).strip() for item in messages)
    has_assistant_message = any(item.get("role") == "assistant" and str(item.get("content", "")).strip() for item in messages)
    if not has_user_message or not has_assistant_message:
        raise HTTPException(status_code=400, detail="complete one effective conversation before generating report")
    return write_ai_session_report(session, request.instruction)


@app.get("/api/ai/sessions/{session_id}/report/download")
def download_ai_session_report(session_id: str) -> FileResponse:
    _, session = find_ai_session(session_id)
    report = write_ai_session_report(session)
    path = ROOT / report["report_path"]
    return FileResponse(path, media_type="text/markdown; charset=utf-8", filename=path.name)


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
