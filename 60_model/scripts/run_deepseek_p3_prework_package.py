from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "60_model" / "src"))

from llm_router import route_for, run_deepseek_task  # noqa: E402  # type: ignore[import-not-found]


TASK_ID = "LLM-022"
OUT_DIR = ROOT / "60_model" / "llm_runs"
RAW_JSONL = OUT_DIR / "deepseek_p3_prework_package_raw.jsonl"
PROGRESS_JSON = OUT_DIR / "deepseek_p3_prework_package_progress.json"

TASK_PLAN = ROOT / "task_plan.md"
FINDINGS = ROOT / "findings.md"
SOURCE_CATALOG = ROOT / "40_quality_evidence" / "p2_real_site_source_catalog.csv"
GAP_REGISTER = ROOT / "70_outputs" / "processed_tables" / "p2_input_gap_register.csv"
DWG_WORKLIST = ROOT / "70_outputs" / "processed_tables" / "p2_dwg_conversion_worklist_deepseek.csv"
P2_PERSONAS = ROOT / "70_outputs" / "processed_tables" / "p2_persona_parameter_prototype.csv"
P2_TRIGGERS = ROOT / "70_outputs" / "processed_tables" / "p2_demand_trigger_matrix.csv"
P2_FORMULA = ROOT / "70_outputs" / "processed_tables" / "p2_supply_gap_scoring_formula.csv"
P2_API = ROOT / "70_outputs" / "processed_tables" / "p2_postman_api_contract_draft.csv"

OUT_ROUTE = ROOT / "70_outputs" / "processed_tables" / "p3_p4_route_decision_deepseek.csv"
OUT_DWG = ROOT / "70_outputs" / "processed_tables" / "p3_dwg_conversion_work_order_deepseek.csv"
OUT_CALIBRATION = ROOT / "70_outputs" / "processed_tables" / "p3_calibration_data_requirements_deepseek.csv"
OUT_MAPPING = ROOT / "70_outputs" / "processed_tables" / "p3_p2_to_calibration_field_mapping_deepseek.csv"
OUT_P4 = ROOT / "70_outputs" / "processed_tables" / "p4_parallel_skeleton_backlog_deepseek.csv"
OUT_JSON = ROOT / "40_quality_evidence" / "deepseek_p3_prework_package.json"
OUT_MD = ROOT / "40_quality_evidence" / "deepseek_p3_prework_package.md"


ROUTE_FIELDS = [
    "decision_id",
    "route_option",
    "recommendation",
    "rationale",
    "p3_gate",
    "p4_allowed_parallel_work",
    "forbidden_before_p3_closed",
    "output_status",
    "executor",
    "llm_task_id",
]
DWG_FIELDS = [
    "work_id",
    "source_id",
    "dwg_file",
    "objective",
    "acceptable_output",
    "required_metadata",
    "current_status",
    "blocker",
    "output_status",
    "executor",
    "llm_task_id",
]
CALIBRATION_FIELDS = [
    "req_id",
    "domain",
    "field_name",
    "description",
    "acceptable_source",
    "required_before_p4_conclusion",
    "current_value_policy",
    "output_status",
    "executor",
    "llm_task_id",
]
MAPPING_FIELDS = [
    "map_id",
    "p2_source_table",
    "p2_field_or_metric",
    "p3_calibration_field",
    "transformation_rule",
    "calibration_status",
    "output_status",
    "executor",
    "llm_task_id",
]
P4_FIELDS = [
    "item_id",
    "component",
    "preparation_task",
    "can_start_before_p3_closed",
    "must_not_do_before_p3_closed",
    "verification_hint",
    "output_status",
    "executor",
    "llm_task_id",
]


def read_text(path: Path, limit: int = 6000) -> str:
    return path.read_text(encoding="utf-8-sig")[:limit]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: str(row.get(field, "")) for field in fields})


def strip_fence(value: str) -> str:
    text = value.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()
    return text


def parse_json_object(value: str) -> dict[str, Any]:
    text = strip_fence(value)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            sliced = text[start : end + 1]
            cleaned_slice = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", sliced)
            return json.loads(cleaned_slice)
        raise


def normalize_rows(rows: Any, size: int, fallbacks: list[dict[str, str]]) -> list[dict[str, Any]]:
    clean = [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
    clean.extend(fallbacks)
    return clean[:size]


def mark(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for row in rows:
        row["output_status"] = "needs_review"
        row["executor"] = "deepseek"
        row["llm_task_id"] = TASK_ID
    return rows


def make_messages(context: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "你是公园商业选址仿真项目的P3前置工作包整理助手。"
                "必须坚持：P2只是方法原型；P3真实校准是P4完整仿真的硬前置；"
                "P4只能并行准备代码骨架、API契约、Postman回归集合、接口占位和场景配置模板。"
                "在P3关键输入未闭合前，不得输出、暗示或排序任何P4完整仿真结论。"
                "所有输出必须是needs_review草稿，DeepSeek不能写checked证据。"
                "DWG必须保持pending_conversion，除非已有可信DXF/GeoJSON/SVG/PDF导出，但当前上下文没有。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请基于以下上下文，生成严格JSON，不要Markdown围栏。输出结构：\n"
                "{\n"
                "  \"summary\": \"简短结论\",\n"
                "  \"route_decision\": [exactly 3 objects],\n"
                "  \"dwg_conversion_work_order\": [exactly 8 objects],\n"
                "  \"calibration_data_requirements\": [exactly 16 objects],\n"
                "  \"p2_to_calibration_mapping\": [exactly 16 objects],\n"
                "  \"p4_parallel_skeleton_backlog\": [exactly 12 objects],\n"
                "  \"output_status\": \"needs_review\"\n"
                "}\n"
                "字段名请按这些CSV字段语义返回：route_option/recommendation/rationale/p3_gate/"
                "p4_allowed_parallel_work/forbidden_before_p3_closed；source_id/dwg_file/objective/"
                "acceptable_output/required_metadata/current_status/blocker；domain/field_name/"
                "description/acceptable_source/required_before_p4_conclusion/current_value_policy；"
                "p2_source_table/p2_field_or_metric/p3_calibration_field/transformation_rule/calibration_status；"
                "component/preparation_task/can_start_before_p3_closed/must_not_do_before_p3_closed/verification_hint。\n\n"
                + json.dumps(context, ensure_ascii=False)
            ),
        },
    ]


def fallback_route() -> list[dict[str, str]]:
    return [
        {
            "route_option": "strict_sequence",
            "recommendation": "P3_is_hard_gate_for_P4_conclusions",
            "rationale": "真实校准参数、DWG转换、客流、转化率、收益成本和运营授权决定仿真可信度。",
            "p3_gate": "all_core_calibration_domains_closed_or_explicitly_marked_as_scenario_assumption",
            "p4_allowed_parallel_work": "none_except_documenting_future_interfaces",
            "forbidden_before_p3_closed": "full_agent_gis_simulation_conclusion",
        },
        {
            "route_option": "parallel_preparation",
            "recommendation": "recommended",
            "rationale": "P3作为结论硬前置，同时允许P4准备代码/API/测试/配置骨架，减少后续等待。",
            "p3_gate": "geometry visitor_flow conversion_rate revenue_cost operation_authorization",
            "p4_allowed_parallel_work": "code_skeleton api_contract postman_regression_placeholder scenario_config_template",
            "forbidden_before_p3_closed": "ranking revenue forecast route weight or final site selection",
        },
        {
            "route_option": "premature_full_p4",
            "recommendation": "rejected",
            "rationale": "会把P2方法原型误写成完整仿真，污染后续选址结论。",
            "p3_gate": "not_satisfied",
            "p4_allowed_parallel_work": "none",
            "forbidden_before_p3_closed": "any_complete_simulation_result",
        },
    ]


def fallback_dwg() -> list[dict[str, str]]:
    return [
        {
            "source_id": "P2SRC-003",
            "dwg_file": "奥森北园(字体放大)-改造建筑示意_t5.dwg",
            "objective": "convert_north_dwg_to_readable_dxf_or_geojson",
            "acceptable_output": "DXF;GeoJSON;SVG;PDF_export_with_manifest",
            "required_metadata": "tool_name;tool_version;command_or_manual_steps;file_hash;crs_if_any;layer_list",
            "current_status": "pending_conversion",
            "blocker": "no_trusted_converted_output_yet",
        },
        {
            "source_id": "P2SRC-004",
            "dwg_file": "奥森南园（字体放大）-改造建筑示意_t5.dwg",
            "objective": "convert_south_dwg_to_readable_dxf_or_geojson",
            "acceptable_output": "DXF;GeoJSON;SVG;PDF_export_with_manifest",
            "required_metadata": "tool_name;tool_version;command_or_manual_steps;file_hash;crs_if_any;layer_list",
            "current_status": "pending_conversion",
            "blocker": "no_trusted_converted_output_yet",
        },
        {
            "source_id": "P2SRC-003",
            "dwg_file": "north_dwg",
            "objective": "extract_candidate_building_or_project_node_layers_after_conversion",
            "acceptable_output": "polygon_or_label_table_after_conversion",
            "required_metadata": "layer_name_mapping;object_count;manual_review_note",
            "current_status": "pending_conversion",
            "blocker": "DWG_geometry_not_parsed",
        },
        {
            "source_id": "P2SRC-004",
            "dwg_file": "south_dwg",
            "objective": "extract_south_project_node_proxy_after_conversion",
            "acceptable_output": "polygon_or_label_table_after_conversion",
            "required_metadata": "layer_name_mapping;object_count;manual_review_note",
            "current_status": "pending_conversion",
            "blocker": "DWG_geometry_not_parsed",
        },
        {
            "source_id": "P2SRC-003;P2SRC-004",
            "dwg_file": "both_dwg",
            "objective": "define_common_export_schema",
            "acceptable_output": "shared_schema_csv",
            "required_metadata": "field_dictionary;status_values;geometry_type",
            "current_status": "pending_conversion",
            "blocker": "no_common_export_schema_until_conversion",
        },
        {
            "source_id": "P2SRC-003;P2SRC-004",
            "dwg_file": "both_dwg",
            "objective": "record_conversion_quality_gate",
            "acceptable_output": "conversion_quality_report",
            "required_metadata": "row_count;empty_layer_count;unreadable_object_count;reviewer",
            "current_status": "pending_conversion",
            "blocker": "no_conversion_report_yet",
        },
        {
            "source_id": "P2SRC-003",
            "dwg_file": "north_dwg",
            "objective": "compare_pdf_proxy_labels_to_converted_layers",
            "acceptable_output": "label_to_layer_mapping_table",
            "required_metadata": "matched_label;unmatched_label;confidence",
            "current_status": "pending_conversion",
            "blocker": "pdf_proxy_is_not_geometry",
        },
        {
            "source_id": "P2SRC-004",
            "dwg_file": "south_dwg",
            "objective": "create_south_proxy_equivalent_if_no_pdf_exists",
            "acceptable_output": "converted_label_or_manual_export_table",
            "required_metadata": "source_method;manual_export_boundary;quality_status",
            "current_status": "pending_conversion",
            "blocker": "south_pdf_proxy_missing",
        },
    ]


def fallback_calibration() -> list[dict[str, str]]:
    domains = [
        ("geometry", "converted_geometry_file", "可信DXF/GeoJSON/SVG/PDF导出及manifest", "DWG conversion output", "yes", "empty_until_conversion"),
        ("geometry", "node_area_or_footprint", "候选节点面积或轮廓", "converted geometry or official drawing", "yes", "empty_until_conversion"),
        ("geometry", "path_network_or_access_nodes", "入口、停车、主路径与节点关系", "converted geometry;Amap routes;field check", "yes", "empty_until_verified"),
        ("visitor_flow", "daily_flow_by_segment", "分人群/时间段真实或可解释客流", "official data;ticketing;manual count;operator log", "yes", "empty_until_provided"),
        ("visitor_flow", "peak_hour_flow", "峰值小时客流", "official data;sensor;manual count", "yes", "empty_until_provided"),
        ("visitor_flow", "persona_mix", "亲子、运动、白领、老人、游客、夜间人群比例", "survey;operator observation;sample report", "yes", "scenario_only_if_missing"),
        ("conversion_rate", "format_conversion_rate", "各业态转化率", "operator data;benchmark;field survey", "yes", "scenario_assumption_only"),
        ("conversion_rate", "queue_abandon_rate", "排队/拥挤导致放弃率", "observation;benchmark", "no", "scenario_assumption_only"),
        ("revenue_cost", "average_ticket_or_spend", "客单价/人均消费", "operator data;Amap cost;survey;ledger", "yes", "empty_or_benchmark_labeled"),
        ("revenue_cost", "rent_or_revenue_share", "租金、保底、抽成规则", "operator authorization;contract draft", "yes", "empty_until_authorized"),
        ("revenue_cost", "renovation_cost", "改造投入", "budget;BOQ;operator estimate", "yes", "empty_until_provided"),
        ("revenue_cost", "operating_cost", "人工、能耗、维护成本", "operator estimate;benchmark", "yes", "scenario_assumption_only"),
        ("operation_authorization", "allowed_business_formats", "允许经营业态清单", "operator or official policy", "yes", "empty_until_authorized"),
        ("operation_authorization", "night_operation_permission", "夜间演出/餐饮运营授权", "operator or official policy", "yes", "empty_until_authorized"),
        ("operation_authorization", "construction_constraints", "施工、消防、市政、文保等约束", "operator;drawing note;official rule", "yes", "empty_until_authorized"),
        ("model_gate", "p4_release_gate", "P4完整仿真放行门禁", "local verification script", "yes", "blocked_until_core_fields_closed"),
    ]
    return [
        {
            "domain": d,
            "field_name": f,
            "description": desc,
            "acceptable_source": src,
            "required_before_p4_conclusion": req,
            "current_value_policy": policy,
        }
        for d, f, desc, src, req, policy in domains
    ]


def fallback_mapping() -> list[dict[str, str]]:
    rows = [
        ("p2_project_node_candidates.csv", "node_name", "candidate_node_id_or_name", "retain_as_candidate_label_only", "needs_p3_validation"),
        ("p2_project_node_candidates.csv", "area_sqm", "node_area_or_footprint", "use_only_if_source_explicit_else_empty", "needs_geometry_or_document_validation"),
        ("p2_spatial_label_candidates.csv", "label_text", "path_network_or_access_nodes", "label_to_node_hint_only", "pending_dwg_conversion"),
        ("p2_business_scene_assumption_pool.csv", "business_format", "allowed_business_formats", "map_to_authorization_check_item", "needs_operator_confirmation"),
        ("p2_business_scene_assumption_pool.csv", "scenario_assumption", "scenario_config_template", "keep_as_needs_review_scenario", "scenario_only"),
        ("p2_persona_parameter_prototype.csv", "prototype_weight", "persona_mix", "replace_with_real_mix_or_mark_scenario", "needs_real_flow"),
        ("p2_demand_trigger_matrix.csv", "prototype_multiplier", "trigger_multiplier", "calibrate_from_behavior_or_keep_scenario", "needs_real_behavior"),
        ("p2_supply_gap_scoring_formula.csv", "demand_fit_score", "formula_weight_demand_fit", "calibrate_weight_after_P3", "needs_review"),
        ("p2_supply_gap_scoring_formula.csv", "spatial_access_score", "formula_weight_spatial_access", "blocked_until_geometry_and_routes", "pending_geometry"),
        ("p2_supply_gap_scoring_formula.csv", "revenue_potential_score", "formula_weight_revenue", "blocked_until_revenue_cost", "pending_revenue_cost"),
        ("p2_candidate_method_readiness_scores.csv", "method_readiness_score_prototype", "baseline_score_preview", "do_not_use_as_final_ranking", "prototype_only"),
        ("p2_postman_api_contract_draft.csv", "path", "api_contract_endpoint", "can_prepare_placeholder_tests", "parallel_allowed"),
        ("p2_input_gap_register.csv", "geometry", "converted_geometry_file", "must_close_before_full_simulation", "blocking"),
        ("p2_input_gap_register.csv", "visitor_flow", "daily_flow_by_segment", "must_close_or_mark_scenario", "blocking"),
        ("p2_input_gap_register.csv", "conversion_rate", "format_conversion_rate", "must_close_or_mark_scenario", "blocking"),
        ("p2_input_gap_register.csv", "operation_authorization", "allowed_business_formats", "must_close_before_site_recommendation", "blocking"),
    ]
    return [
        {
            "p2_source_table": a,
            "p2_field_or_metric": b,
            "p3_calibration_field": c,
            "transformation_rule": d,
            "calibration_status": e,
        }
        for a, b, c, d, e in rows
    ]


def fallback_p4() -> list[dict[str, str]]:
    rows = [
        ("model_api", "create FastAPI placeholder endpoints from p2_postman_api_contract_draft", "yes", "do not return ranked site conclusions", "unit test endpoint shape"),
        ("postman", "create collection skeleton with variable names only", "yes", "do not store real keys or real conclusions", "collection schema check"),
        ("scenario_config", "define conservative/base/optimistic config template", "yes", "do not fill real calibrated parameters", "empty value gate"),
        ("simulation_interface", "define input/output dataclasses for agents and GIS", "yes", "do not run full simulation", "python import and schema tests"),
        ("geometry_adapter", "create adapter interface for future DXF/GeoJSON", "yes", "do not invent coordinates or area", "fixture with empty geometry"),
        ("route_adapter", "create Amap route adapter placeholder", "yes", "do not claim route weights calibrated", "mock response tests"),
        ("revenue_module", "create revenue formula placeholder", "yes", "do not forecast revenue", "requires explicit scenario flag"),
        ("calibration_loader", "load p3_calibration_data_requirements as schema", "yes", "do not auto-fill missing fields", "missing value tests"),
        ("quality_gate", "add P4 release gate design", "yes", "do not mark gate passed", "expected blocked status"),
        ("report_stub", "create draft summary template", "yes", "do not write final recommendation", "contains needs_review labels"),
        ("monte_carlo", "prepare random seed and output contract", "yes", "do not sample until parameters exist", "seed reproducibility test"),
        ("frontend_future", "list future dashboard data contract only", "yes", "do not build P6 website now", "contract file exists"),
    ]
    return [
        {
            "component": c,
            "preparation_task": t,
            "can_start_before_p3_closed": can,
            "must_not_do_before_p3_closed": no,
            "verification_hint": hint,
        }
        for c, t, can, no, hint in rows
    ]


def assign_ids(rows: list[dict[str, Any]], prefix: str, field: str) -> list[dict[str, Any]]:
    for index, row in enumerate(rows, start=1):
        row[field] = f"{prefix}-{index:03d}"
    return rows


def ensure_mapping_core_coverage(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    text = "\n".join(" ".join(str(value) for value in row.values()) for row in rows).lower()
    core_fallbacks = fallback_mapping()
    required = [
        ("project_node", ["p2_project_node_candidates.csv", "p2_nodes", "candidate"], core_fallbacks[0]),
        ("persona", ["p2_persona_parameter_prototype.csv", "p2_personas", "persona"], core_fallbacks[5]),
        ("formula", ["p2_supply_gap_scoring_formula.csv", "p2_formula", "demand_fit_score"], core_fallbacks[7]),
        ("gap_register", ["p2_input_gap_register.csv", "p2_gap_register", "gap"], core_fallbacks[12]),
    ]
    patched = list(rows)
    for _, aliases, fallback in required:
        if any(alias.lower() in text for alias in aliases):
            continue
        patched[-1] = fallback
        text += "\n" + " ".join(str(value) for value in fallback.values()).lower()
    return patched[:16]


def ensure_calibration_core_coverage(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    patched = list(rows)
    for row in patched:
        value = str(row.get("required_before_p4_conclusion", "")).strip().lower()
        if value in {"true", "1", "required", "yes", "y", "是", "必需", "必须"}:
            row["required_before_p4_conclusion"] = "yes"
        elif value in {"false", "0", "optional", "no", "n", "否", "可选"}:
            row["required_before_p4_conclusion"] = "no"
    text = "\n".join(" ".join(str(value) for value in row.values()) for row in patched).lower()
    core_fallbacks = fallback_calibration()
    required = [
        ("geometry", ["geometry", "geojson", "dwg", "spatial_access"], core_fallbacks[0]),
        ("visitor_flow", ["visitor_flow", "visitor_behavior", "visitor_count", "persona_mix"], core_fallbacks[3]),
        ("conversion_rate", ["conversion_rate", "consumption", "transaction", "trigger_calibration"], core_fallbacks[6]),
        ("revenue_cost", ["revenue_cost", "rent", "opex", "capex"], core_fallbacks[8]),
        ("operation_authorization", ["operation_authorization", "lease", "regulatory", "policy", "permission"], core_fallbacks[12]),
        ("model_gate", ["model_gate", "p4_release_gate"], core_fallbacks[15]),
    ]
    for _, aliases, fallback in required:
        if any(alias.lower() in text for alias in aliases):
            continue
        fallback = dict(fallback)
        fallback["required_before_p4_conclusion"] = "yes"
        patched[-1] = fallback
        text += "\n" + " ".join(str(value) for value in fallback.values()).lower()
    return patched[:16]


def enforce_route_boundaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for row in rows:
        forbidden = str(row.get("forbidden_before_p3_closed", "")).strip()
        boundary = "P3未闭合前不得运行完整仿真结论、候选点排序、财务收益预测、坐标面积推断或最终选址建议"
        if not forbidden:
            row["forbidden_before_p3_closed"] = boundary
        elif "完整仿真" not in forbidden and "仿真运行" not in forbidden:
            row["forbidden_before_p3_closed"] = f"{forbidden}; {boundary}"
    return rows


def enforce_p4_boundaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    boundary = "不得输出完整仿真结论、最终推荐、候选点排序、收益预测、坐标面积或真实校准参数"
    for row in rows:
        current = str(row.get("must_not_do_before_p3_closed", "")).strip()
        if not current:
            row["must_not_do_before_p3_closed"] = boundary
        elif "完整仿真" not in current and "最终" not in current and "排序" not in current:
            row["must_not_do_before_p3_closed"] = f"{current}; {boundary}"
    return rows


def main() -> None:
    route = route_for(TASK_ID)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    context = {
        "task_plan_excerpt": read_text(TASK_PLAN),
        "findings_excerpt": read_text(FINDINGS),
        "source_catalog": read_csv(SOURCE_CATALOG),
        "p2_gap_register": read_csv(GAP_REGISTER),
        "p2_dwg_worklist": read_csv(DWG_WORKLIST),
        "p2_personas": read_csv(P2_PERSONAS),
        "p2_triggers": read_csv(P2_TRIGGERS),
        "p2_formula": read_csv(P2_FORMULA),
        "p2_api_contract": read_csv(P2_API),
        "hard_boundary": (
            "P3 calibration is required before P4 conclusions. P4 can only prepare skeleton/API/tests/config. "
            "DWG stays pending_conversion; no coordinates, area, layers, route, movement, or north-south geometry conclusion."
        ),
    }
    response = run_deepseek_task(TASK_ID, make_messages(context), temperature=0.0)
    RAW_JSONL.write_text(
        json.dumps({"run_id": run_id, "task_id": TASK_ID, "model": route.model, "response_excerpt": response[:5000]}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    parsed = parse_json_object(response)

    route_rows = assign_ids(enforce_route_boundaries(normalize_rows(parsed.get("route_decision"), 3, fallback_route())), "P3P4-ROUTE", "decision_id")
    dwg_rows = assign_ids(normalize_rows(parsed.get("dwg_conversion_work_order"), 8, fallback_dwg()), "P3-DWG-WORK", "work_id")
    calibration_rows = assign_ids(ensure_calibration_core_coverage(normalize_rows(parsed.get("calibration_data_requirements"), 16, fallback_calibration())), "P3-CALIB", "req_id")
    mapping_rows = assign_ids(ensure_mapping_core_coverage(normalize_rows(parsed.get("p2_to_calibration_mapping"), 16, fallback_mapping())), "P3-MAP", "map_id")
    p4_rows = assign_ids(enforce_p4_boundaries(normalize_rows(parsed.get("p4_parallel_skeleton_backlog"), 12, fallback_p4())), "P4-SKEL", "item_id")

    for row in dwg_rows:
        row["current_status"] = "pending_conversion"
    for row in p4_rows:
        row["can_start_before_p3_closed"] = "yes"

    write_csv(OUT_ROUTE, ROUTE_FIELDS, mark(route_rows))
    write_csv(OUT_DWG, DWG_FIELDS, mark(dwg_rows))
    write_csv(OUT_CALIBRATION, CALIBRATION_FIELDS, mark(calibration_rows))
    write_csv(OUT_MAPPING, MAPPING_FIELDS, mark(mapping_rows))
    write_csv(OUT_P4, P4_FIELDS, mark(p4_rows))

    summary = {
        "summary": parsed.get("summary") or "P3 is the hard prerequisite for P4 conclusions; P4 skeleton can proceed in parallel.",
        "route_rows": len(route_rows),
        "dwg_work_rows": len(dwg_rows),
        "calibration_rows": len(calibration_rows),
        "mapping_rows": len(mapping_rows),
        "p4_skeleton_rows": len(p4_rows),
        "output_status": "needs_review",
        "executor": "deepseek",
        "llm_task_id": TASK_ID,
        "model": route.model,
        "run_id": run_id,
    }
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(
        "\n".join(
            [
                "# DeepSeek P3前置工作包",
                "",
                "- 路线结论：P3是真实校准硬前置；P4可并行准备代码/API/测试/配置骨架。",
                "- 禁止事项：P3关键输入未闭合前，不运行或宣称P4完整仿真结论。",
                f"- 路线判断：{len(route_rows)} 行",
                f"- DWG转换工作单：{len(dwg_rows)} 行",
                f"- 校准数据需求：{len(calibration_rows)} 行",
                f"- P2到P3字段映射：{len(mapping_rows)} 行",
                f"- P4并行骨架清单：{len(p4_rows)} 行",
                "- 输出状态：needs_review",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    PROGRESS_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"p3_p4_route_decision_deepseek.csv rows={len(route_rows)}")
    print(f"p3_dwg_conversion_work_order_deepseek.csv rows={len(dwg_rows)}")
    print(f"p3_calibration_data_requirements_deepseek.csv rows={len(calibration_rows)}")
    print(f"p3_p2_to_calibration_field_mapping_deepseek.csv rows={len(mapping_rows)}")
    print(f"p4_parallel_skeleton_backlog_deepseek.csv rows={len(p4_rows)}")


if __name__ == "__main__":
    main()
