from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_CSV = ROOT / "70_outputs" / "processed_tables" / "person_simulation_feature_derivatives_1000_20260604.csv"
OUT_JSON = ROOT / "40_quality_evidence" / "person_simulation_feature_derivatives_generation_20260607.json"

FIELDNAMES = [
    "derivative_id",
    "persona_id",
    "persona_name",
    "persona_core_need",
    "income_segment_id",
    "income_segment_name",
    "income_price_band",
    "income_sensitivity_note",
    "income_evidence_hint",
    "time_band_id",
    "time_band_name",
    "time_range",
    "weather_id",
    "weather_name",
    "weather_effect",
    "node_context_id",
    "node_context_name",
    "node_role",
    "demand_trigger_id",
    "demand_trigger_name",
    "candidate_supply_action_id",
    "candidate_supply_action_name",
    "priority_label",
    "user_control_needed",
    "data_needed",
    "deepseek_role",
    "why_it_matters",
]

PERSONAS = [
    {
        "id": "runner",
        "name": "晨练/跑步人群",
        "core": "目标是快速补水、低负担补给和路线不中断；收入敏感度中等，更在意距离、排队和运动后即时性。",
    },
    {
        "id": "parent_family",
        "name": "亲子家庭",
        "core": "目标是安全停留、儿童照护、轻食和休息；收入跨度较大，价格透明、卫生和便利性比单价更重要。",
    },
    {
        "id": "silver_senior",
        "name": "银发慢游人群",
        "core": "目标是舒适步行、座椅、厕所、饮水和低风险消费；收入/养老金差异会影响价格容忍和消费频次。",
    },
    {
        "id": "office_lunch",
        "name": "周边白领/午间客群",
        "core": "目标是在有限时间内完成咖啡、轻食、社交或短暂放松；收入水平相对稳定，时间成本高于小额价差。",
    },
    {
        "id": "tourist_photo",
        "name": "外地游客/拍照客群",
        "core": "目标是景观停留、路线指引、特色消费和纪念性体验；收入与旅游预算影响文创和特色产品接受度。",
    },
    {
        "id": "culture_visitor",
        "name": "文化研学/活动客群",
        "core": "目标是活动前后聚集、讲解、文创、补给和秩序；团体预算、活动票务和组织方安排会改变消费决策。",
    },
    {
        "id": "cyclist",
        "name": "骑行/装备人群",
        "core": "目标是路线衔接、快速补给、临时维修和安全停靠；收入敏感度不一，但对专业服务和时间效率有明确需求。",
    },
    {
        "id": "night_event",
        "name": "夜间活动/社交人群",
        "core": "目标是照明安全、夜间补给、社交停留和离园便利；收入、同行关系和夜间营业时间共同影响消费。",
    },
]

INCOME_SEGMENTS = [
    {
        "id": "public_basic",
        "name": "基础预算/公共服务优先",
        "price_band": "0-30元即时补给或免费基础服务",
        "sensitivity": "价格敏感度高，优先判断是否应做公益性饮水、座椅、卫生间、导视和低价透明补给。",
        "evidence": "本地资料含餐饮消费水平、城市/全国消费水平和居住社区房价表；基础预算段不可被高消费均值覆盖。",
    },
    {
        "id": "value_family",
        "name": "稳健家庭预算",
        "price_band": "31-100元亲子轻食/饮品/休息配套",
        "sensitivity": "关注卫生、安全、排队、儿童友好和明码标价，价格不一定最低，但必须让家庭觉得可控。",
        "evidence": "奥森与对照公园资料均出现51-100元、101-150元餐饮价格带和已育/亲子相关人群特征。",
    },
    {
        "id": "urban_mid",
        "name": "城市中等消费",
        "price_band": "51-150元咖啡、茶饮、轻食与短停留服务",
        "sensitivity": "能接受便利溢价，但会比较园内外价格、距离和排队；适合做标准化轻资产试点。",
        "evidence": "奥森PDF出现城市消费水平v2中/次高/高和餐饮消费水平分布，需与周边商圈级收入复核。",
    },
    {
        "id": "quality_high",
        "name": "品质导向/高消费潜力",
        "price_band": "101-300元精品咖啡、文创、夜间餐酒或运动健康体验",
        "sensitivity": "更在意品质、品牌、景观和体验完整度；价格可以更高，但必须有场景溢价和服务承接。",
        "evidence": "奥森资料含全国消费水平v2高占比、餐饮高客单价和酒店消费水平线索；仍需真实交易校准。",
    },
    {
        "id": "business_event",
        "name": "商务活动/团体预算",
        "price_band": "300元以上活动、包场、课程或联名产品",
        "sensitivity": "由组织方预算、活动档期、服务容量和审批许可决定，不宜用普通游客客单价直接外推。",
        "evidence": "老板方法资料强调宏观校准、行动约束和真实验证；团体/活动收入必须单列，不与散客消费混算。",
    },
]

TIME_BANDS = [
    ("early_morning", "清晨", "05:30-08:30", "晨练和入园高峰，补水、厕所、短停留需求更强。"),
    ("forenoon", "上午", "09:00-11:30", "亲子、慢游和观景逐步增加，导视和轻补给更重要。"),
    ("lunch_noon", "午间", "11:30-14:00", "周边白领、轻食、咖啡和遮阴休息需求上升。"),
    ("afternoon", "下午", "14:00-17:30", "亲子、拍照、活动客流增加，座椅和活动配套重要。"),
    ("evening", "傍晚", "18:00-21:30", "社交、夜跑、离园和夜间照明/营业策略成为约束。"),
    ("holiday_peak", "周末/节假日高峰", "10:00-19:30", "人流密度、排队、亲子照护和补货压力集中。"),
]

WEATHERS = [
    ("comfortable", "舒适天气", "停留时间延长，特色消费和慢游转化更容易发生。"),
    ("hot", "高温暴晒", "补水、遮阴、冷饮和缩短排队是关键，热风险提高。"),
    ("rain", "降雨", "避雨、路线缩短、临时遮蔽和室内/半室内服务更重要。"),
    ("cold_windy", "寒冷大风", "热饮、避风、短停留和关闭策略更重要。"),
    ("poor_air", "空气质量较差", "运动客流下降，短线游和室内替代活动需要单独判断。"),
]

NODE_CONTEXTS = [
    ("entry", "入口/闸口", "客流导入与第一补给点，适合低决策成本服务。"),
    ("main_path", "主环路/主路径", "连续通过和分流位置，适合可快速获取的补给。"),
    ("lakefront", "湖边/景观停留区", "停留和拍照更强，适合轻量休憩与特色消费。"),
    ("activity_node", "活动/展陈节点", "活动前后聚集，适合活动配套、导视和秩序维护。"),
    ("service_gap_node", "服务缺口节点", "现有设施不足或距离较远，适合先做小规模试点。"),
    ("exit", "离园出口/换乘口", "离园前补给、打包和路线信息更重要。"),
]

DEMAND_TRIGGERS = [
    ("thirst", "口渴/补水", "高频即时需求，需要距离近、排队短、价格清楚。"),
    ("hunger", "轻食/能量补给", "和停留时间、同行、收入水平、客单价直接相关。"),
    ("fatigue", "疲劳/休息", "受年龄、步行距离、天气和座椅密度影响。"),
    ("toilet", "卫生间/基础服务", "决定停留能否继续，亲子和银发客群更敏感。"),
    ("childcare", "亲子照护", "与安全、卫生、排队和儿童活动半径相关。"),
    ("wayfinding", "导视/问询", "路线不确定会降低停留和消费转化。"),
    ("social_stay", "社交/等待", "情侣、朋友和活动客群需要可停留空间。"),
    ("weather_shelter", "避暑/避雨/避风", "天气触发强，决定服务是否应季节性启用。"),
    ("price_compare", "价格/收入匹配", "收入水平和预算敏感度会决定是否接受咖啡、文创或轻食。"),
    ("night_safety", "夜间安全/离园", "照明、营业关闭、路线清晰和换乘便利是主要约束。"),
]

ACTIONS = {
    "thirst": [
        ("water_machine", "饮水机/直饮水点"),
        ("vending_machine", "自动售卖机"),
        ("mobile_cart", "移动补给车"),
    ],
    "hunger": [
        ("tea_lightfood", "茶饮轻食"),
        ("coffee_kiosk", "咖啡/冷饮小站"),
        ("vending_machine", "自动售卖机"),
    ],
    "fatigue": [
        ("rest_seating", "遮阴座椅/休息点"),
        ("shade_canopy", "遮阴棚/临时遮蔽"),
        ("no_action_review", "暂不新增，仅观察复核"),
    ],
    "toilet": [
        ("toilet_upgrade", "卫生间与排队改善"),
        ("info_service", "导视问询"),
        ("queue_manager", "排队组织与提示"),
    ],
    "childcare": [
        ("parent_room", "亲子照护点"),
        ("tea_lightfood", "儿童友好轻食"),
        ("rest_seating", "安全休息点"),
    ],
    "wayfinding": [
        ("info_service", "导视问询"),
        ("route_marker", "路线标识/节点牌"),
        ("digital_notice", "电子提示屏"),
    ],
    "social_stay": [
        ("rest_seating", "社交停留座椅"),
        ("coffee_kiosk", "咖啡/冷饮小站"),
        ("event_kiosk", "活动配套摊位"),
    ],
    "weather_shelter": [
        ("shade_canopy", "遮阴避雨设施"),
        ("tea_lightfood", "季节饮品轻食"),
        ("temporary_shelter", "临时避雨/避风点"),
    ],
    "price_compare": [
        ("value_menu", "平价套餐/价格带设计"),
        ("premium_culture_product", "特色文创/高客单产品"),
        ("no_action_review", "暂不新增，仅观察复核"),
    ],
    "night_safety": [
        ("night_lighting", "夜间照明与安全提示"),
        ("late_vending", "夜间售卖/补给"),
        ("closing_rule", "营业关闭与补货规则"),
    ],
}


def priority_for(trigger_id: str, weather_id: str, node_id: str, action_id: str) -> str:
    if action_id == "no_action_review":
        return "P3 保留观察：先补真实数据，不直接投资"
    if trigger_id in {"toilet", "childcare", "night_safety"}:
        return "P1 先核实：影响停留、安全或基础服务"
    if weather_id in {"hot", "rain"} and trigger_id in {"thirst", "weather_shelter", "fatigue"}:
        return "P1 季节性试点：天气触发强，需现场校准"
    if node_id in {"entry", "service_gap_node", "exit"}:
        return "P2 方案比较：适合小规模 A/B 试点"
    return "P2 可纳入方案比较：需结合客流和转化率复核"


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    per_persona = 150
    for persona_index, persona in enumerate(PERSONAS):
        for local_index in range(per_persona):
            time = TIME_BANDS[(local_index + persona_index) % len(TIME_BANDS)]
            income = INCOME_SEGMENTS[(local_index // 5 + persona_index * 2) % len(INCOME_SEGMENTS)]
            weather = WEATHERS[(local_index // 2 + persona_index) % len(WEATHERS)]
            node = NODE_CONTEXTS[(local_index // 3 + persona_index) % len(NODE_CONTEXTS)]
            trigger = DEMAND_TRIGGERS[(local_index // 4 + persona_index) % len(DEMAND_TRIGGERS)]
            action_options = ACTIONS[trigger[0]]
            action = action_options[(local_index + persona_index) % len(action_options)]
            derivative_id = f"PSD-{len(rows) + 1:04d}"
            priority = priority_for(trigger[0], weather[0], node[0], action[0])
            user_control = (
                "用户可编辑人群权重、收入/预算假设、消费价格带、时段、天气、节点和供给动作；"
                "可采用、放弃、删除、锁定本条假设，并要求 DeepSeek 只解释待复核理由。"
            )
            data_needed = (
                "真实客流、时段分布、天气/节假日记录、周边人口与收入水平、消费支出、客单价、"
                "转化率、竞品 POI、步行距离、排队时长、库存/补货、营业关闭时间、现场观察和用户访谈。"
            )
            deepseek_role = (
                "DeepSeek 只能生成候选说明、资料缺口和报告草稿；不得决定最终概率、最终排名、"
                "最终收益或自动覆盖用户锁定对象，所有输出保持待复核。"
            )
            why = (
                f"{persona['name']}在{time[1]}、{weather[1]}、{node[1]}遇到“{trigger[1]}”时，"
                f"若收入/消费口径按“{income['name']}（{income['price_band']}）”处理，"
                f"建议优先评估“{action[1]}”。判断必须结合收入/预算、同行关系、路径成本、"
                "供给真实性和运营承接能力，输出应是可执行修改建议而不是裸分。"
            )
            rows.append(
                {
                    "derivative_id": derivative_id,
                    "persona_id": persona["id"],
                    "persona_name": persona["name"],
                    "persona_core_need": persona["core"],
                    "income_segment_id": income["id"],
                    "income_segment_name": income["name"],
                    "income_price_band": income["price_band"],
                    "income_sensitivity_note": income["sensitivity"],
                    "income_evidence_hint": income["evidence"],
                    "time_band_id": time[0],
                    "time_band_name": time[1],
                    "time_range": time[2],
                    "weather_id": weather[0],
                    "weather_name": weather[1],
                    "weather_effect": weather[2],
                    "node_context_id": node[0],
                    "node_context_name": node[1],
                    "node_role": node[2],
                    "demand_trigger_id": trigger[0],
                    "demand_trigger_name": trigger[1],
                    "candidate_supply_action_id": action[0],
                    "candidate_supply_action_name": action[1],
                    "priority_label": priority,
                    "user_control_needed": user_control,
                    "data_needed": data_needed,
                    "deepseek_role": deepseek_role,
                    "why_it_matters": why,
                }
            )
    return rows


def summarize(rows: list[dict[str, str]]) -> dict[str, object]:
    keys = [
        "persona_id",
        "income_segment_id",
        "time_band_id",
        "weather_id",
        "node_context_id",
        "demand_trigger_id",
        "candidate_supply_action_id",
    ]
    coverage = {key: len({row[key] for row in rows}) for key in keys}
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "generated",
        "output_csv": str(OUT_CSV.relative_to(ROOT)).replace("\\", "/"),
        "row_count": len(rows),
        "coverage": coverage,
        "design_boundary": (
            "This is a deterministic coverage pool for person-simulation scenarios. "
            "It is not a final simulation result and does not claim ROI or final ranking."
        ),
    }


def main() -> None:
    rows = build_rows()
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    summary = summarize(rows)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_CSV.relative_to(ROOT)} rows={len(rows)}")
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
