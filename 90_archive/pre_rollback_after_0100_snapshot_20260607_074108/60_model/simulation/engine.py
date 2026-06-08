from __future__ import annotations

import random
from collections import defaultdict
from typing import Any

from validators import blocked_gate_warnings, validate_result_rows, validate_simulation_request


BUSINESS_FIELD_LABELS = {
    "cost_yuan": "人均消费/成本字段",
    "opentime_today": "营业时间",
    "tel": "联系电话",
}

ACTION_CATEGORY_HINTS = {
    "饮水机": ["convenience_retail", "sports_supply"],
    "直饮水": ["convenience_retail", "sports_supply"],
    "自动售卖机": ["convenience_retail", "cold_drink", "sports_supply"],
    "移动补给": ["convenience_retail", "cold_drink", "fast_food"],
    "咖啡": ["coffee", "cold_drink", "tea_drink"],
    "冷饮": ["coffee", "cold_drink", "tea_drink"],
    "茶饮": ["tea_drink", "cold_drink"],
    "轻食": ["fast_food", "restaurant", "tea_drink"],
    "儿童": ["convenience_retail", "fast_food", "cultural_creative"],
    "亲子": ["convenience_retail", "fast_food", "cultural_creative"],
    "文创": ["cultural_creative"],
    "运动": ["sports_supply", "yoga_pilates"],
    "瑜伽": ["yoga_pilates", "sports_supply"],
    "夜间": ["night_dining_bar", "restaurant", "convenience_retail"],
    "避雨": ["convenience_retail", "restaurant", "coffee", "tea_drink"],
    "遮阴": ["convenience_retail", "restaurant", "coffee", "tea_drink"],
    "卫生间": ["convenience_retail"],
    "排队": ["fast_food", "restaurant", "coffee", "tea_drink", "cold_drink"],
}


CALIBRATION_LAYER_LABELS = {
    "official_macro_boundary": "官方宏观边界",
    "local_bigdata_profile": "本地大数据画像",
    "local_device_price_proxy": "设备价格代理",
    "local_poi_price_signal": "竞品价格线索",
    "local_poi_demand_signal": "本地需求热度线索",
    "plan_assumption_needs_review": "方案假设待复核",
    "local_user_supplement": "用户补充校准输入",
}


def split_categories(value: Any) -> list[str]:
    categories = [item.strip() for item in str(value or "").split(";") if item.strip()]
    return categories or ["unknown"]


def missing_business_fields(row: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if row.get("cost_yuan") is None or str(row.get("cost_yuan", "")).strip() == "":
        missing.append("cost_yuan")
    if not str(row.get("opentime_today", "")).strip():
        missing.append("opentime_today")
    if not str(row.get("tel", "")).strip():
        missing.append("tel")
    return missing


def source_hint_for(rows: list[dict[str, Any]]) -> str:
    source_paths = sorted({str(row.get("source_path") or "") for row in rows if row.get("source_path")})
    if source_paths:
        return "; ".join(source_paths[:3])
    statuses = sorted({str(row.get("supply_use_status") or "") for row in rows if row.get("supply_use_status")})
    return "; ".join(statuses[:3]) or "poi_candidates_import"


def next_data_needed(
    missing_fields: set[str],
    inside_count: int,
    total_count: int,
    blocked_gate_count: int,
    scene_pressure: dict[str, Any] | None = None,
) -> list[str]:
    needs: list[str] = []
    if blocked_gate_count:
        needs.append("补齐 P3 gate: geometry / visitor_flow / conversion_rate / revenue_cost / operation_authorization / model_gate")
    if inside_count < total_count:
        needs.append("用可信边界或现场资料确认候选是否在园内")
    for field in sorted(missing_fields):
        needs.append(f"补齐经营字段: {BUSINESS_FIELD_LABELS.get(field, field)}")
    if scene_pressure and scene_pressure.get("matched_scene_count"):
        needs.append("补齐采用人物场景对应的客群占比、分时段客流、价格敏感度、真实成交转化和竞品价格")
        if scene_pressure.get("operation_rules"):
            needs.append("复核场景动作对应的营业关闭、补货、排队和天气应对规则")
    if not needs:
        needs.append("人工复核来源、授权与现场可达性后再进入下一步模型")
    return needs


def scene_category_hints(scene: dict[str, Any]) -> set[str]:
    text = " ".join(
        str(scene.get(key) or "")
        for key in [
            "candidate_supply_action_name",
            "demand_trigger_name",
            "persona_name",
            "node_context_name",
        ]
    )
    hints: set[str] = set()
    for keyword, categories in ACTION_CATEGORY_HINTS.items():
        if keyword in text:
            hints.update(categories)
    return hints


def match_feature_scenes(category: str, scenes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    category_parts = set(split_categories(category))
    matched: list[dict[str, Any]] = []
    for scene in scenes:
        hints = scene_category_hints(scene)
        if not hints:
            continue
        if category_parts & hints:
            matched.append(scene)
    return matched


def compact_scene(scene: dict[str, Any]) -> dict[str, Any]:
    return {
        "derivative_id": scene.get("derivative_id", ""),
        "title": scene.get("title", ""),
        "persona_name": scene.get("persona_name", ""),
        "income_segment_name": scene.get("income_segment_name", ""),
        "income_price_band": scene.get("income_price_band", ""),
        "time_band_name": scene.get("time_band_name", ""),
        "time_range": scene.get("time_range", ""),
        "weather_name": scene.get("weather_name", ""),
        "node_context_name": scene.get("node_context_name", ""),
        "demand_trigger_name": scene.get("demand_trigger_name", ""),
        "candidate_supply_action_name": scene.get("candidate_supply_action_name", ""),
        "data_needed": scene.get("data_needed", ""),
    }


def scene_pressure_summary(matched_scenes: list[dict[str, Any]], total_scene_count: int) -> dict[str, Any]:
    compacted = [compact_scene(scene) for scene in matched_scenes[:6]]
    income_segments = list(dict.fromkeys(row["income_segment_name"] for row in compacted if row["income_segment_name"]))
    price_bands = list(dict.fromkeys(row["income_price_band"] for row in compacted if row["income_price_band"]))
    time_bands = list(dict.fromkeys(row["time_band_name"] for row in compacted if row["time_band_name"]))
    weathers = list(dict.fromkeys(row["weather_name"] for row in compacted if row["weather_name"]))
    demand_triggers = list(dict.fromkeys(row["demand_trigger_name"] for row in compacted if row["demand_trigger_name"]))
    operation_rules = list(dict.fromkeys(row["candidate_supply_action_name"] for row in compacted if row["candidate_supply_action_name"]))
    if not compacted:
        return {
            "total_feature_scene_count": total_scene_count,
            "matched_scene_count": 0,
            "matched_scenes": [],
            "income_segments": [],
            "price_bands": [],
            "time_bands": [],
            "weathers": [],
            "demand_triggers": [],
            "operation_rules": [],
            "business_reading": "当前 POI 组暂未匹配到用户已采用/锁定的人物场景；仅按 POI 和资料门禁做结构化检查。",
        }
    return {
        "total_feature_scene_count": total_scene_count,
        "matched_scene_count": len(matched_scenes),
        "matched_scenes": compacted,
        "income_segments": income_segments,
        "price_bands": price_bands,
        "time_bands": time_bands,
        "weathers": weathers,
        "demand_triggers": demand_triggers,
        "operation_rules": operation_rules,
        "business_reading": (
            "该 POI/供给组已被采用人物场景命中；干跑只说明哪些收入/价格/时段/天气变量需要校准，"
            "不能直接推出真实成交或收益。"
        ),
    }


def calibration_layer_label(value: Any) -> str:
    return CALIBRATION_LAYER_LABELS.get(str(value or ""), str(value or "待分层"))


def compact_calibration_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "calibration_id": item.get("calibration_id", ""),
        "layer": calibration_layer_label(item.get("source_strength")),
        "indicator_name": item.get("indicator_name", ""),
        "segment": item.get("segment", ""),
        "period": item.get("period", ""),
        "value": item.get("value", ""),
        "simulation_use": item.get("simulation_use", ""),
        "cannot_claim": item.get("cannot_claim", ""),
        "next_data_needed": item.get("next_data_needed", ""),
    }


def category_accuracy_focus(category: str) -> list[str]:
    parts = set(split_categories(category))
    focus = ["周边收入/消费能力", "分时段客流", "真实转化率", "空间可达与边界", "竞品价格"]
    if parts & {"coffee", "tea_drink", "cold_drink", "fast_food", "restaurant"}:
        focus.extend(["客单价区间", "排队等待", "补货与营业时间"])
    if parts & {"sports_supply", "yoga_pilates"}:
        focus.extend(["运动后即时需求", "早晚高峰差异", "天气触发"])
    if parts & {"cultural_creative"}:
        focus.extend(["停留时长", "活动档期", "纪念性消费"])
    if parts & {"night_dining_bar"}:
        focus.extend(["夜间安全", "照明与关闭规则", "离园交通"])
    return list(dict.fromkeys(focus))


def build_accuracy_context(
    category: str,
    scene_pressure: dict[str, Any],
    calibration_context: dict[str, Any] | None,
    missing_fields: set[str],
    inside_count: int,
    total_count: int,
    blocked_gate_count: int,
) -> dict[str, Any]:
    calibration_context = calibration_context or {}
    items = [compact_calibration_item(item) for item in (calibration_context.get("items") or [])[:8]]
    layer_counts = {
        calibration_layer_label(layer): count
        for layer, count in (calibration_context.get("source_strength_counts") or {}).items()
    }
    matched_scene_count = int(scene_pressure.get("matched_scene_count") or 0)
    focus = category_accuracy_focus(category)
    if scene_pressure.get("weathers"):
        focus.append("天气转化")
    if scene_pressure.get("time_bands"):
        focus.append("时段营业策略")
    if scene_pressure.get("operation_rules"):
        focus.append("供给动作与运维容量")
    focus = list(dict.fromkeys(focus))

    constraints: list[dict[str, Any]] = [
        {
            "name": "收入与消费能力",
            "status": "has_macro_boundary_needs_local_calibration"
            if layer_counts.get("官方宏观边界")
            else "missing",
            "how_to_use": "只能约束价格带和支付能力讨论，不能直接当奥森周边街道收入或真实成交。",
            "next_data_needed": "补奥森周边 1-3 公里街道/社区收入、居住办公结构、游客来源和真实支付客单。",
        },
        {
            "name": "竞品价格与供给",
            "status": "has_poi_price_signal_needs_verification"
            if layer_counts.get("竞品价格线索")
            else "missing",
            "how_to_use": "用于判断咖啡、轻食、亲子、运动补给等价格带是否离谱，不能直接替代园内经营客单。",
            "next_data_needed": "补竞品真实客单、距离、营业时间、排队、评分、复购和淡旺季差异。",
        },
        {
            "name": "时段与天气转化",
            "status": "needs_observed_flow_and_weather"
            if matched_scene_count
            else "not_triggered_by_selected_scene",
            "how_to_use": "用于决定清晨、午间、傍晚、雨热冷风等场景下是否启用供给、补货或关闭。",
            "next_data_needed": "补分入口分时段客流、天气、节假日、活动日、停留时长和转化率。",
        },
        {
            "name": "空间边界与可达",
            "status": "partly_confirmed" if inside_count == total_count else "needs_boundary_review",
            "how_to_use": "只判断当前 POI 组是否能进入空间讨论，不替代 CAD/GIS 控制点和路线测算。",
            "next_data_needed": "补 CAD 控制点、可经营面积、入口路径、步行距离、照明、排队空间和消防限制。",
        },
        {
            "name": "经营字段与运维",
            "status": "missing_fields" if missing_fields else "field_level_ready_for_review",
            "how_to_use": "用于识别电话、营业时间、成本/客单等经营字段缺口，不能推出收益。",
            "next_data_needed": "补营业时间、关闭规则、补货频率、库存、人员、排队容量、收益成本和授权。",
        },
    ]
    readiness_label = "准确性待校准"
    if blocked_gate_count:
        readiness_label = "关键门禁未闭合"
    elif matched_scene_count and calibration_context.get("count"):
        readiness_label = "可做结构化预检"

    return {
        "readiness_label": readiness_label,
        "calibration_input_count": calibration_context.get("count", 0),
        "calibration_layers": layer_counts,
        "category_accuracy_focus": focus,
        "calibration_evidence": items,
        "constraints": constraints,
        "missing_before_claim": list(dict.fromkeys(calibration_context.get("missing_before_final") or [])),
        "deepseek_boundary": "DeepSeek 只能补充候选解释、缺口和草稿，不得给最终概率、最终排名、最终收益或覆盖用户锁定对象。",
        "human_review_question": "这些输入是否足以解释该业态在这个时间、天气、空间节点下为什么有人来、为什么停留、为什么消费或为什么放弃？",
    }


def run_structural_simulation(
    poi_candidates: list[dict[str, Any]],
    calibration_gates: list[dict[str, Any]],
    seed: int,
    iterations: int,
    feature_scenes: list[dict[str, Any]] | None = None,
    real_calibration_context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    issues = validate_simulation_request(iterations, seed)
    if issues:
        raise ValueError("; ".join(issues))

    feature_scenes = feature_scenes or []
    gate_warnings = blocked_gate_warnings(calibration_gates)
    blocked_gate_count = len(gate_warnings)
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in poi_candidates:
        boundary_status = str(row.get("boundary_filter_status") or "boundary_unknown")
        for category in split_categories(row.get("standard_categories")):
            groups[(str(row.get("park_id", "")), category, boundary_status)].append(row)

    rng = random.Random(seed)
    results: list[dict[str, Any]] = []
    sample_size = max(1, min(iterations, 20))
    for (park_id, category, boundary_status), rows in sorted(groups.items()):
        sampled = [rng.choice(rows).get("candidate_id", "") for _ in range(sample_size)]
        missing_by_row = [missing_business_fields(row) for row in rows]
        missing_field_names = {field for fields in missing_by_row for field in fields}
        missing_row_count = sum(1 for fields in missing_by_row if fields)
        inside_count = sum(1 for row in rows if row.get("boundary_filter_status") == "inside_osm_polygon")
        matched_scenes = match_feature_scenes(category, feature_scenes)
        scene_pressure = scene_pressure_summary(matched_scenes, len(feature_scenes))
        accuracy_context = build_accuracy_context(
            category,
            scene_pressure,
            real_calibration_context,
            missing_field_names,
            inside_count,
            len(rows),
            blocked_gate_count,
        )
        why_blocked = list(gate_warnings)
        warnings = list(gate_warnings)
        if feature_scenes:
            warnings.append("user-controlled feature scenes are used as needs_review dry-run inputs, not final population shares")
        if inside_count < len(rows):
            msg = "candidate group includes records outside or not confirmed by OSM/public boundary"
            why_blocked.append(msg)
            warnings.append(msg)
        if missing_field_names:
            msg = "candidate group has missing business fields"
            why_blocked.append(msg)
            warnings.append(msg)
        if matched_scenes:
            warnings.append("feature-scene pressure requires real flow, conversion, price and weather calibration")
        results.append(
            {
                "park_id": park_id,
                "category": category,
                "group_context": f"{park_id} / {category} / {boundary_status}",
                "boundary_filter_status": boundary_status,
                "source_hint": source_hint_for(rows),
                "candidate_count": len(rows),
                "inside_osm_polygon_count": inside_count,
                "missing_business_field_count": missing_row_count,
                "blocked_gate_count": blocked_gate_count,
                "why_blocked": why_blocked,
                "missing_required_fields": sorted(missing_field_names),
                "next_data_needed": next_data_needed(
                    missing_field_names,
                    inside_count,
                    len(rows),
                    blocked_gate_count,
                    scene_pressure,
                ),
                "sampled_candidate_ids": sampled,
                "feature_scene_context": scene_pressure.get("matched_scenes", []),
                "scenario_pressure": scene_pressure,
                "accuracy_context": accuracy_context,
                "calibration_constraints": accuracy_context.get("constraints", []),
                "feature_scene_count": len(feature_scenes),
                "matched_feature_scene_count": int(scene_pressure.get("matched_scene_count", 0)),
                "warnings": warnings,
                "output_status": "needs_review",
                "not_final": True,
                "status_label": "待复核 / 非最终",
            }
        )
    result_issues = validate_result_rows(results)
    if result_issues:
        raise ValueError("; ".join(result_issues))
    return results
