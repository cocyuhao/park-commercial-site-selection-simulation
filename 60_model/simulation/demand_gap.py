from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
LOCATION_REFERENCE_STATUSES = {"location_reference_only", "external" + "_preview_only"}

BUSINESS_TYPES = [
    "精品咖啡",
    "快餐小吃",
    "亲子餐饮",
    "文创零售",
    "夜间餐酒",
    "运动补给",
    "便利零售",
    "健康休闲",
]

POI_CATEGORY_KEYWORDS = {
    "精品咖啡": ["咖啡", "coffee", "星巴克", "瑞幸", "manner", "costa"],
    "快餐小吃": ["餐饮", "小吃", "快餐", "简餐", "麦当劳", "肯德基", "美食"],
    "亲子餐饮": ["亲子", "儿童", "家庭", "母婴"],
    "文创零售": ["文创", "纪念品", "书店", "零售", "礼品", "文化"],
    "夜间餐酒": ["酒吧", "精酿", "夜市", "餐酒", "演艺"],
    "运动补给": ["运动", "骑行", "跑步", "健身", "轻食", "补给"],
    "便利零售": ["便利", "超市", "自动售货", "饮用水", "商店"],
    "健康休闲": ["瑜伽", "普拉提", "康复", "健康", "理疗"],
}

SEGMENT_TO_TGI = {
    "亲子餐饮": ["亲子", "儿童", "家庭", "母婴"],
    "运动补给": ["运动", "跑步", "骑行", "户外", "赛事"],
    "精品咖啡": ["白领", "办公", "商务", "咖啡", "青年", "休闲"],
    "夜间餐酒": ["夜间", "夜游", "演艺", "音乐", "露营"],
    "文创零售": ["文创", "文化", "展览", "研学", "游客"],
    "便利零售": ["通勤", "补给", "便利", "游客", "高峰"],
    "快餐小吃": ["午餐", "晚餐", "简餐", "餐饮", "停留"],
    "健康休闲": ["银发", "瑜伽", "普拉提", "康养", "健康"],
}


def parse_uploaded_visitor_sources(uploads: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    candidate_by_upload = {row.get("upload_id"): row for row in candidates}
    selected: list[dict[str, Any]] = []
    for upload in uploads:
        text = f"{upload.get('category', '')} {upload.get('target_gate', '')} {upload.get('note', '')} {upload.get('filename', '')}"
        if "visitor_flow" in text or "客流" in text or "人流" in text or "游客" in text:
            candidate = candidate_by_upload.get(upload.get("upload_id"), {})
            selected.append(
                {
                    "upload_id": upload.get("upload_id", ""),
                    "filename": upload.get("filename", ""),
                    "note": upload.get("note", ""),
                    "source_excerpt": candidate.get("source_excerpt", ""),
                    "review_status": upload.get("review_status", ""),
                }
            )
    return {
        "has_uploaded_visitor_flow": bool(selected),
        "sources": selected,
        "combined_text": "\n".join(
            f"{row.get('filename', '')}\n{row.get('note', '')}\n{row.get('source_excerpt', '')}"
            for row in selected
        ),
    }


def parse_flow_numbers(text: str) -> dict[str, Any]:
    normalized = []
    for match in re.finditer(r"(\d+(?:\.\d+)?)\s*(万人次|人次/小时|人/小时|人次|游客|客流)", text):
        value = float(match.group(1))
        unit = match.group(2)
        normalized.append(value * 10000 if "万" in unit else value)
    return {
        "observed_values": normalized[:24],
        "peak_flow": max(normalized) if normalized else None,
        "sample_count": len(normalized),
    }


def extract_segment_weights(text: str) -> dict[str, float]:
    weights: dict[str, float] = {}
    for category, keywords in SEGMENT_TO_TGI.items():
        for keyword in keywords:
            pattern = rf"{re.escape(keyword)}[^0-9%％]{{0,16}}(\d+(?:\.\d+)?)\s*[%％]"
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                weights[category] = max(weights.get(category, 0.0), float(match.group(1)) / 100)
        if category not in weights and any(keyword.lower() in text.lower() for keyword in keywords):
            weights[category] = 0.1
    return weights


def extract_explicit_tgi(text: str, category: str) -> float | None:
    aliases = [category, *POI_CATEGORY_KEYWORDS.get(category, [])]
    for alias in aliases:
        pattern = rf"{re.escape(alias)}[^0-9]{{0,12}}(?:TGI|tgi)[^0-9]{{0,8}}(\d+(?:\.\d+)?)"
        match = re.search(pattern, text)
        if match:
            value = float(match.group(1))
            if 20 <= value <= 300:
                return round(value, 2)
            raise ValueError(f"TGI value out of allowed range for {category}: {value}")
    return None


def build_tgi_profile(visitor_text: str) -> dict[str, Any]:
    flow = parse_flow_numbers(visitor_text)
    segment_weights = extract_segment_weights(visitor_text)
    if not flow["sample_count"] and not segment_weights:
        return {
            "status": "missing_visitor_flow_upload",
            "tgi_profile": {},
            "demand_profile": {},
            "flow": flow,
            "message": "未读取到外部上传的客流/TGI资料，不能计算游客需求。",
        }
    tgi_profile: dict[str, float] = {}
    for category in BUSINESS_TYPES:
        try:
            explicit = extract_explicit_tgi(visitor_text, category)
        except ValueError as exc:
            return {
                "status": "invalid_uploaded_tgi",
                "tgi_profile": {},
                "demand_profile": {},
                "flow": flow,
                "message": str(exc),
            }
        if explicit is not None:
            tgi_profile[category] = explicit
            continue
        weight = segment_weights.get(category, 0.0)
        flow_lift = min((flow["peak_flow"] or 0) / 10000, 0.6)
        tgi_profile[category] = round(100 + 100 * weight + 20 * flow_lift, 2)
    demand_profile = {category: round(value / 100, 4) for category, value in tgi_profile.items()}
    return {
        "status": "calculated_from_uploaded_sources",
        "tgi_profile": tgi_profile,
        "demand_profile": demand_profile,
        "flow": flow,
        "segment_weights": segment_weights,
        "message": "已按外部上传资料生成待复核 TGI。",
    }


def classify_poi_category(poi: dict[str, Any]) -> str | None:
    text = f"{poi.get('poi_name', '')} {poi.get('category', '')} {poi.get('amap_keywords', '')}".lower()
    for category, keywords in POI_CATEGORY_KEYWORDS.items():
        if any(keyword.lower() in text for keyword in keywords):
            return category
    return None


def build_supply_profile(pois: list[dict[str, Any]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    evidence: dict[str, list[str]] = defaultdict(list)
    for poi in pois:
        category = classify_poi_category(poi)
        if not category:
            continue
        counts[category] += 1
        if len(evidence[category]) < 6:
            evidence[category].append(str(poi.get("poi_name") or poi.get("candidate_id") or "POI"))
    if not counts:
        return {
            "status": "missing_amap_poi",
            "supply_profile": {},
            "poi_counts": {},
            "poi_evidence": {},
            "message": "没有可分类的高德 POI，不能计算供给。",
        }
    average = sum(counts.values()) / max(len(BUSINESS_TYPES), 1)
    supply_profile = {category: round(counts.get(category, 0) / max(average, 1), 4) for category in BUSINESS_TYPES}
    return {
        "status": "calculated_from_amap_poi",
        "supply_profile": supply_profile,
        "poi_counts": dict(counts),
        "poi_evidence": dict(evidence),
        "message": "已按当前地图上下文高德 POI 生成待复核供给画像。",
    }


def calculate_supply_gap(tgi_result: dict[str, Any], supply_result: dict[str, Any]) -> dict[str, Any]:
    if not tgi_result.get("demand_profile") or not supply_result.get("supply_profile"):
        return {
            "status": "blocked_until_uploaded_visitor_flow_and_poi_ready",
            "items": [],
            "message": "缺少外部客流/TGI资料或高德 POI，供需缺口暂不能计算。",
        }
    demand = tgi_result["demand_profile"]
    supply = supply_result["supply_profile"]
    items = []
    for category in BUSINESS_TYPES:
        demand_score = float(demand.get(category, 0.0))
        supply_score = float(supply.get(category, 0.0))
        denominator = abs(demand_score) + abs(supply_score)
        gap_index = 0.0 if denominator == 0 else (demand_score - supply_score) / denominator
        priority = "优先校准" if gap_index >= 0.25 else "可优化" if gap_index >= 0.08 else "暂不优先"
        items.append(
            {
                "business_type": category,
                "tgi": tgi_result["tgi_profile"].get(category, ""),
                "demand_score": round(demand_score, 4),
                "supply_score": round(supply_score, 4),
                "gap_score": round(demand_score - supply_score, 4),
                "gap_index": round(gap_index, 4),
                "priority": priority,
                "poi_count": supply_result.get("poi_counts", {}).get(category, 0),
                "poi_examples": supply_result.get("poi_evidence", {}).get(category, []),
                "output_status": "needs_review",
                "not_final": True,
            }
        )
    return {
        "status": "calculated_needs_review",
        "items": sorted(items, key=lambda item: (item["gap_index"], item["gap_score"]), reverse=True),
        "message": "缺口指数=(需求-供给)/(需求+供给)，仅作节点讨论依据。",
    }


def attach_gap_to_nodes(nodes: list[dict[str, Any]], gap_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gap_by_type = {item["business_type"]: item for item in gap_items}
    enriched = []
    for node in nodes:
        directions = node.get("business_direction") or node.get("candidate_business_formats") or []
        matched = []
        for direction in directions:
            direction_text = str(direction)
            for category in BUSINESS_TYPES:
                if category in direction_text or any(keyword in direction_text for keyword in POI_CATEGORY_KEYWORDS[category]):
                    if category in gap_by_type:
                        matched.append(gap_by_type[category])
        best_gap = max(matched, key=lambda item: item["gap_index"], default=None)
        gap_bonus = max(-12, min(12, round(best_gap["gap_index"] * 20))) if best_gap else 0
        score = node.get("discussion_score_draft")
        if isinstance(score, (int, float)) and node.get("score_status") not in LOCATION_REFERENCE_STATUSES:
            new_score = max(0, min(100, int(score) + gap_bonus))
            node = {**node, "discussion_score_draft": new_score, "score_label": f"{new_score} 分 · 待复核"}
        enriched.append(
            {
                **node,
                "supply_gap_match": best_gap or {},
                "supply_gap_items": matched[:4],
                "score_explanation": (
                    f"{node.get('score_explanation', '')} 供需缺口已作为草案加减分依据。"
                    if best_gap
                    else node.get("score_explanation", "")
                ),
            }
        )
    return enriched


def improvement_for_gap(gap_match: dict[str, Any]) -> str:
    if not gap_match:
        return "未匹配到可计算缺口，先复核客流/TGI资料和当前地图 POI。"
    if gap_match.get("priority") == "优先校准":
        return f"建议优先校准{gap_match.get('business_type')}，并用现场约束复核面积、可达性和运营授权。"
    if gap_match.get("priority") == "可优化":
        return f"{gap_match.get('business_type')}有一定缺口，可作为组合业态或轻量试点。"
    return f"{gap_match.get('business_type')}暂不作为主要缺口，避免过早增加供给。"


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "；".join(_as_text(item) for item in value if _as_text(item))
    if isinstance(value, dict):
        return "；".join(f"{key}: {_as_text(val)}" for key, val in value.items() if _as_text(val))
    return str(value).strip()


def _first_nonempty(*values: Any) -> str:
    for value in values:
        text = _as_text(value)
        if text:
            return text
    return ""


def _business_tags(node: dict[str, Any]) -> list[str]:
    raw = node.get("business_direction") or node.get("candidate_business_formats") or []
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw.replace("'", '"'))
            raw = parsed if isinstance(parsed, list) else [raw]
        except json.JSONDecodeError:
            raw = re.split(r"[;；,，\n]", raw)
    tags: list[str] = []
    for item in raw:
        text = str(item)
        for category, keywords in POI_CATEGORY_KEYWORDS.items():
            if category in text or any(keyword in text for keyword in keywords):
                if category not in tags:
                    tags.append(category)
        if len(tags) >= 4:
            break
    return tags


def _priority_stage(node: dict[str, Any], index: int) -> str:
    name = f"{node.get('node_name', '')}{node.get('primary_positioning', '')}"
    missing = _as_text(node.get("missing_required_fields") or node.get("must_collect_before_final"))
    if "地下" in name or "5417" in _as_text(node.get("area_sqm")):
        return "重资产条件型：先做可行性和运营招商，不宜直接定案"
    if any(word in name for word in ("露天剧场", "桃花源", "白房子")):
        return "低改造试点型：适合先做轻量运营测试"
    if any(word in name for word in ("廉洁", "2A03", "中医", "国医", "疗愈")):
        return "资质依赖型：产品可讨论，落地取决于授权和专业背书"
    if "Live House" in name or "音乐" in name:
        return "双方案筛选型：优先验证低风险方案，再保留夜间内容"
    if missing:
        return "复核后推进型：先锁定关键输入，再进入比较"
    return f"讨论顺序 {index + 1}：保持为工作稿"


def _node_recommendation(node: dict[str, Any]) -> str:
    name = str(node.get("node_name") or "")
    positioning = str(node.get("primary_positioning") or "")
    formats = _as_text(node.get("business_direction") or node.get("candidate_business_formats"))
    if "桃花源" in name or "白房子" in name:
        return "建议把它定位成“花海旁的轻餐与预约活动据点”，先跑咖啡茶饮、轻食、摄影/生日/小型团建预约；阳光房、木平台和灯光可以作为体验增强，但要先确认审批、消防、外摆和厨房排烟边界。"
    if "廉洁" in name or "展馆" in name or "疗愈" in positioning:
        return "建议从“健康展厅+检测体验+轻康养课程+营养茶吧”起步，不直接重押高价医疗设备。医学检测、专家背书、疗程包和客户追踪可以做成高客单产品，但必须由有资质机构承接，并把医疗表述、责任边界和长期复购先谈清楚。"
    if "12#" in name or "西分区" in name:
        return "两个方案里，北冰洋/义利国潮轻餐和文创体验更适合先验证，因为白天客群、亲子和公园调性更稳。Live House 可保留为周末小型演出或联名活动，不宜先作为主经营假设，除非夜间开放、噪声、演出审批和酒水牌照都能闭合。"
    if "地下" in name or "预埋" in name:
        return "这是最大体量空间，不能用一个业态一次性吃满。建议先拆成“运动户外折扣/快闪+地上咖啡文创引流+亲子托管/体验”的可招商模块；沉浸式 RPG 作为备选主题，只有消防、疏散、空调、层高、停车和 IP 合作确认后再进入深方案。"
    if "露天剧场" in name:
        return "建议把露天剧场做成“湖畔烘焙咖啡+草坪活动”的季节型运营场，而不是固定大店。用移动外摆、市集、亲子工坊和小型音乐活动测试停留与转化，冬季再切换灯光节/庙会/热饮；篝火、萌宠、帐篷等必须以政策许可为前提。"
    if "2A03" in name or "国医" in positioning or "中医" in formats:
        return "建议把国医国学中心从“医疗诊疗综合体”降一档到“中医文化体验+康复理疗课程+茶饮文创+专家预约”的组合。诊疗、针灸、药房必须有机构资质和运营授权；没有资质前，只能做文化与健康生活方式体验。"
    return improvement_for_gap(node.get("supply_gap_match") or {})


def _load_expert_knowledge_summary() -> dict[str, Any]:
    path = ROOT / "10_research" / "expert_implementation_knowledge_20260607" / "expert_implementation_summary.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _expert_review_basis() -> dict[str, Any]:
    summary = _load_expert_knowledge_summary()
    dimensions = summary.get("real_world_review_dimensions") or [
        ["政策与公园适配", "是否符合公园定位、生态与公共服务边界。"],
        ["目标人群", "亲子、运动、银发、白领、游客等群体是否分别有需求触发和支付能力。"],
        ["周边人口与收入", "周边居住、办公、学校、游客来源、收入层级和客单价承受力是否支撑该业态。"],
        ["时间天气与季节", "工作日/周末、早中晚、淡旺季和天气是否改变停留与消费。"],
        ["运营财务与许可", "招商、成本、消防、食品、演出、医疗、外摆和夜间许可是否闭合。"],
    ]
    official_sources = summary.get("official_real_world_sources") or []
    return {
        "generated_at": summary.get("generated_at", ""),
        "query_total": summary.get("query_total", 0),
        "completed_query_count": summary.get("completed_query_count", 0),
        "raw_count": summary.get("raw_count", 0),
        "unique_count": summary.get("unique_count", 0),
        "screened_count": summary.get("screened_count", 0),
        "topic_group_count": summary.get("topic_group_count", 0),
        "dimensions": dimensions,
        "official_sources": official_sources,
        "beijing_context": BEIJING_REAL_WORLD_CONTEXT,
        "required_local_inputs": REAL_WORLD_HARD_INPUTS,
        "use_boundary": "研究底座用于约束评审维度和证据门槛，不把论文数量、官方条文或全市均值直接写成项目收益结论。",
    }


def _node_case(node: dict[str, Any]) -> str:
    text = f"{node.get('node_name', '')}{node.get('primary_positioning', '')}{_as_text(node.get('business_direction') or node.get('candidate_business_formats'))}"
    if "桃花源" in text or "白房子" in text:
        return "taohuayuan"
    if "廉洁" in text or "展馆" in text or "疗愈" in text:
        return "lianjie"
    if "12#" in text or "西分区" in text or "Live House" in text:
        return "west_zone"
    if "地下" in text or "预埋" in text:
        return "underground"
    if "露天剧场" in text:
        return "theater"
    if "2A03" in text or "国医" in text or "中医" in text:
        return "guoyi"
    return "general"


def _node_segment_profile(node: dict[str, Any], tags: list[str]) -> dict[str, list[str]]:
    case = _node_case(node)
    common_income = [
        "北京全市收入与消费数据说明：城市居民有服务消费和文娱消费基础，但本节点不能直接用全市均值定价。",
        "定价必须回到奥森周边居住/办公/游客来源的收入分层、家庭结构和价格敏感度；缺街道级数据时只能做价格带假设。",
    ]
    profiles = {
        "taohuayuan": {
            "target_segments": ["亲子家庭", "周末游客", "花海打卡人群", "摄影/生日/团建预约客"],
            "demand_triggers": ["花海与湖景带来的停留", "拍照与社交分享", "小型聚会需要轻餐和遮阴休息", "亲子活动需要低门槛体验"],
            "income_and_price_band": [
                *common_income,
                "更适合中低客单高频消费和预约活动加价，不宜一开始做高门槛套餐或重厨房。",
            ],
        },
        "lianjie": {
            "target_segments": ["康养关注人群", "银发与亚健康白领", "企业团建/健康讲座", "文化展陈游客"],
            "demand_triggers": ["健康筛查好奇心", "低强度休闲课程", "展馆参观后的停留转化", "企业/社区活动预约"],
            "income_and_price_band": [
                *common_income,
                "康养体验可承接中高客单，但诊疗、检测和疗程包必须依赖资质机构、复购路径和真实支付意愿。",
            ],
        },
        "west_zone": {
            "target_segments": ["年轻白领", "亲子家庭", "国潮消费人群", "活动/演出观众"],
            "demand_triggers": ["轻餐补给", "国潮品牌打卡", "周末活动前后消费", "夜间内容带来的停留延长"],
            "income_and_price_band": [
                *common_income,
                "先验证国潮轻餐、文创和亲子消费；Live House 与酒水高客单依赖夜间开放、噪声审批和周边接受度。",
            ],
        },
        "underground": {
            "target_segments": ["运动户外人群", "亲子体验家庭", "快闪品牌客", "团建/主题活动客"],
            "demand_triggers": ["大体量空间可承接目的性消费", "南门入口流量", "极端天气下的室内替代", "运动与亲子活动的模块化招商"],
            "income_and_price_band": [
                *common_income,
                "大体量空间不能靠单一业态回收；必须用分区招商、分阶段 CAPEX 和真实转化率验证客单价承受力。",
            ],
        },
        "theater": {
            "target_segments": ["周末家庭", "草坪活动人群", "轻音乐/市集游客", "跑步骑行补给客"],
            "demand_triggers": ["湖畔和草坪停留", "季节性市集", "演出/活动前后补给", "天气好时的户外消费冲动"],
            "income_and_price_band": [
                *common_income,
                "应以轻量、季节型、中低客单为主；高价活动要先验证天气、噪声、审批和游客付费意愿。",
            ],
        },
        "guoyi": {
            "target_segments": ["文化研学客", "银发/康复需求人群", "亲子国学体验", "预约制健康课程客"],
            "demand_triggers": ["国医文化好奇心", "低门槛理疗/茶饮体验", "专家预约与课程", "研学和家庭陪伴需求"],
            "income_and_price_band": [
                *common_income,
                "文化体验和茶饮可先做低风险价格带；医疗诊疗、药房和针灸类高客单必须有资质和责任边界。",
            ],
        },
        "general": {
            "target_segments": ["公园游客", "周边居民", "运动休闲人群", "家庭游客"],
            "demand_triggers": ["停留延长", "补给", "休闲活动", "预约制服务"],
            "income_and_price_band": [*common_income, "先按低改造试点验证支付意愿，再进入标准运营。"],
        },
    }
    profile = profiles.get(case, profiles["general"])
    if tags and "business_tags" not in profile:
        profile = {**profile, "business_tags": tags}
    return profile


def _node_time_weather(case: str) -> list[str]:
    defaults = [
        "工作日与周末要拆开看；周末亲子和游客高峰不能替代工作日经营能力。",
        "高温、降雨、寒冷、大风和空气质量会改变户外停留，遮阴、避雨、取暖和室内替代空间要进入方案。",
    ]
    extra = {
        "taohuayuan": ["春秋花期和晴天最强；雨天/冬季需靠预约活动和室内轻餐保底。"],
        "lianjie": ["更适合全天候预约制课程和讲座，天气影响小于户外点位，但医生/专家排班会影响履约。"],
        "west_zone": ["夜间与活动日是关键变量；如夜间开放或噪声审批不成立，Live House 只能降级为白天活动组件。"],
        "underground": ["可作为极端天气下的室内承接空间，但空调、通风、疏散和后勤成本会直接改变收益模型。"],
        "theater": ["天气是第一变量；户外演出、市集和草坪活动必须有雨备、风控和季节切换方案。"],
        "guoyi": ["可做全天候预约制，但银发/康复人群对无障碍、温度、休息和路线距离更敏感。"],
    }
    return defaults + extra.get(case, [])


def _node_options(case: str) -> list[dict[str, Any]]:
    option_sets = {
        "taohuayuan": [
            {
                "name": "低改造试点",
                "what_to_do": "咖啡茶饮、轻食、移动外摆、摄影/生日/团建预约，先验证停留和预约转化。",
                "best_for": "花期、周末、亲子和打卡人群。",
                "prerequisites": ["外摆边界", "食品简单制售许可", "垃圾/保洁", "小活动审批"],
                "risks": ["季节波动", "雨天转化下降", "厨房排烟和后勤不足"],
                "evidence_to_validate": ["花期与非花期客流", "预约转化率", "客单价", "投诉记录"],
            },
            {
                "name": "标准运营",
                "what_to_do": "固定轻餐店+预约活动包+亲子工坊，形成稳定菜单、活动日历和会员复购。",
                "best_for": "客流稳定、审批清晰、周边家庭消费力确认后。",
                "prerequisites": ["可经营面积", "给排水/电力", "人员排班", "供应链"],
                "risks": ["固定成本上升", "淡季空置", "活动运营难度"],
                "evidence_to_validate": ["月度坪效", "活动满班率", "复购率", "天气敏感性"],
            },
            {
                "name": "重资产/暂缓条件",
                "what_to_do": "阳光房、木平台、灯光和婚礼级场景只作为二期，先不进入首轮 CAPEX。",
                "best_for": "审批、消防、结构和高客单预约被证明后。",
                "prerequisites": ["结构/消防审批", "噪声和活动管理", "投资回收模型"],
                "risks": ["一次性投入过高", "审批周期长", "公共空间商业化舆情"],
                "evidence_to_validate": ["高客单订单量", "社区接受度", "审批意见", "回收期"],
            },
        ],
        "lianjie": [
            {
                "name": "低改造试点",
                "what_to_do": "健康展陈、茶饮、轻检测体验、公益讲座和企业健康活动预约。",
                "best_for": "先把展馆流量转化为停留和咨询。",
                "prerequisites": ["健康表述边界", "合作机构背书", "体验设备安全"],
                "risks": ["医疗化表述越界", "体验转化弱", "专家资源不稳定"],
                "evidence_to_validate": ["咨询转化率", "课程报名", "客单价承受力", "合规审核"],
            },
            {
                "name": "标准运营",
                "what_to_do": "健康生活方式中心：检测体验、理疗课程、营养茶吧、会员跟踪和团体活动。",
                "best_for": "周边中高收入白领/银发需求明确后。",
                "prerequisites": ["资质方运营", "数据隐私", "服务 SOP", "复购体系"],
                "risks": ["资质责任不清", "高客单复购不足", "投诉和责任风险"],
                "evidence_to_validate": ["有效会员数", "复购周期", "投诉率", "合作机构资质"],
            },
            {
                "name": "重资产/暂缓条件",
                "what_to_do": "高端医疗设备、疗程包和诊疗服务暂缓，除非机构资质、责任边界和收益模型闭合。",
                "best_for": "有明确运营主体和医疗资质时。",
                "prerequisites": ["医疗/检测资质", "责任保险", "设备投入测算"],
                "risks": ["政策和责任风险高", "设备闲置", "公共空间调性冲突"],
                "evidence_to_validate": ["资质许可", "设备利用率", "单客毛利", "风险评审"],
            },
        ],
        "west_zone": [
            {
                "name": "低改造试点",
                "what_to_do": "北冰洋/义利国潮轻餐、文创快闪、亲子体验和周末小演出。",
                "best_for": "白天稳定游客和亲子客。",
                "prerequisites": ["品牌联名条件", "食品许可", "活动审批"],
                "risks": ["同质化", "快闪后劲不足", "品牌合作不稳定"],
                "evidence_to_validate": ["客单价", "连带购买率", "活动客流", "品牌合作成本"],
            },
            {
                "name": "标准运营",
                "what_to_do": "轻餐+文创+活动日历，形成白天消费主线，夜间仅做低噪声活动。",
                "best_for": "需要稳态运营和亲子/白领混合客群。",
                "prerequisites": ["持续品牌供给", "运营排期", "周边客群收入分层"],
                "risks": ["活动运营成本", "淡季弱化", "价格带不匹配"],
                "evidence_to_validate": ["分时段销售", "家庭客占比", "复购率", "淡旺季差异"],
            },
            {
                "name": "重资产/暂缓条件",
                "what_to_do": "Live House、酒水和夜间演出暂不作为主方案，先保留为审批通过后的可选组件。",
                "best_for": "夜间开放、演出资质、噪声和居民接受度全部闭合后。",
                "prerequisites": ["演出许可", "酒水/食品许可", "安保疏散", "噪声控制"],
                "risks": ["审批难", "投诉风险", "夜间客流不确定", "安全成本高"],
                "evidence_to_validate": ["夜间客流", "噪声监测", "审批意见", "安保成本"],
            },
        ],
        "underground": [
            {
                "name": "低改造试点",
                "what_to_do": "地上引流点+地下局部快闪，先测试运动户外折扣、亲子体验和主题活动。",
                "best_for": "验证大体量空间是否能被目的性消费激活。",
                "prerequisites": ["消防疏散核验", "基础照明/导视", "短租招商"],
                "risks": ["地下可见性弱", "导流不足", "安全和维护成本高"],
                "evidence_to_validate": ["进店率", "停留时长", "导视效果", "安全巡检"],
            },
            {
                "name": "标准运营",
                "what_to_do": "拆成运动户外、亲子体验、快闪市集和配套轻餐模块，分区招商分期投入。",
                "best_for": "空间条件和客流验证后，避免单一业态吃满空间。",
                "prerequisites": ["空调通风", "给排水/电力", "货运后勤", "招商分成模型"],
                "risks": ["CAPEX 高", "招商周期长", "运营管理复杂"],
                "evidence_to_validate": ["模块坪效", "招商报价", "运营成本", "客流承载"],
            },
            {
                "name": "重资产/暂缓条件",
                "what_to_do": "沉浸式 RPG、IP 主题馆和大设备项目仅在消防、层高、IP、停车和回收期成立后推进。",
                "best_for": "具备强 IP、强招商主体和明确目的性客流时。",
                "prerequisites": ["消防/结构", "IP 合作", "停车与排队", "完整财务模型"],
                "risks": ["投资不可逆", "主题衰减", "维护成本高", "人群密度风险"],
                "evidence_to_validate": ["目的性购票率", "IP 授权成本", "回收期", "高峰疏散"],
            },
        ],
        "theater": [
            {
                "name": "低改造试点",
                "what_to_do": "移动咖啡/烘焙、草坪市集、亲子工坊和小型音乐活动。",
                "best_for": "晴天周末和活动日。",
                "prerequisites": ["临时摊位审批", "用电安全", "垃圾保洁", "雨备方案"],
                "risks": ["天气敏感", "噪声投诉", "人群聚集"],
                "evidence_to_validate": ["天气-销售关系", "活动客流", "投诉记录", "保洁成本"],
            },
            {
                "name": "标准运营",
                "what_to_do": "季节性活动日历+固定轻补给点，春秋主打草坪活动，冬季转热饮/灯光/庙会。",
                "best_for": "有稳定活动运营团队时。",
                "prerequisites": ["活动排期", "安保方案", "食品许可", "季节切换方案"],
                "risks": ["活动组织成本", "淡季弱", "许可边界变化"],
                "evidence_to_validate": ["活动满场率", "补给转化率", "季节收入曲线", "安保成本"],
            },
            {
                "name": "重资产/暂缓条件",
                "what_to_do": "篝火、帐篷、萌宠和大型夜间活动暂缓，先完成安全、消防、生态和舆情评审。",
                "best_for": "政策明确允许且居民/游客接受度较高时。",
                "prerequisites": ["用火/搭建审批", "噪声控制", "生态影响评估"],
                "risks": ["安全风险高", "舆情敏感", "季节不可控"],
                "evidence_to_validate": ["审批意见", "试运营投诉", "安全演练", "生态影响"],
            },
        ],
        "guoyi": [
            {
                "name": "低改造试点",
                "what_to_do": "国医文化体验、茶饮文创、香囊/节气课、低风险康养课程。",
                "best_for": "亲子研学、银发和文化游客。",
                "prerequisites": ["文化体验边界", "课程师资", "食品/文创许可"],
                "risks": ["内容浅", "复购弱", "医疗表述越界"],
                "evidence_to_validate": ["课程报名", "文创转化", "客群年龄结构", "合规文案"],
            },
            {
                "name": "标准运营",
                "what_to_do": "中医文化+康复理疗课程+专家预约+健康茶饮，诊疗动作由资质方承接。",
                "best_for": "有稳定资质合作方和预约需求后。",
                "prerequisites": ["医疗/康复资质", "隐私和责任边界", "预约系统"],
                "risks": ["责任风险", "专家排班不稳定", "高客单转化难"],
                "evidence_to_validate": ["预约率", "复购率", "资质文件", "投诉/退费"],
            },
            {
                "name": "重资产/暂缓条件",
                "what_to_do": "诊疗综合体、药房和针灸治疗不作为首轮项目，除非监管和运营主体完全闭合。",
                "best_for": "具备完整医疗机构合作与监管许可时。",
                "prerequisites": ["医疗机构许可", "药品/器械管理", "责任保险", "专业人员资质"],
                "risks": ["合规不可控", "公共空间定位冲突", "成本和责任高"],
                "evidence_to_validate": ["许可文件", "专业人员排班", "单位经济模型", "监管意见"],
            },
        ],
    }
    return option_sets.get(case, [
        {
            "name": "低改造试点",
            "what_to_do": "先用轻量业态和预约活动验证需求。",
            "best_for": "资料不足但有明确讨论价值的节点。",
            "prerequisites": ["客流", "转化率", "基本许可"],
            "risks": ["需求不稳", "价格带不清"],
            "evidence_to_validate": ["试运营销售", "客群结构", "投诉记录"],
        },
        {
            "name": "标准运营",
            "what_to_do": "在客流、收入、转化和许可确认后做固定运营。",
            "best_for": "可经营面积和持续需求明确的节点。",
            "prerequisites": ["财务模型", "工程条件", "运营主体"],
            "risks": ["固定成本", "淡旺季"],
            "evidence_to_validate": ["坪效", "复购率", "淡旺季差异"],
        },
        {
            "name": "重资产/暂缓条件",
            "what_to_do": "高投入方案暂缓到审批、资金和回收期闭合后。",
            "best_for": "有强客流和强招商主体的节点。",
            "prerequisites": ["审批", "投资测算", "安全评审"],
            "risks": ["投资不可逆", "审批不确定"],
            "evidence_to_validate": ["回收期", "审批意见", "敏感性分析"],
        },
    ])


def _implementation_review(node: dict[str, Any], index: int) -> dict[str, Any]:
    tags = _business_tags(node)
    case = _node_case(node)
    profile = _node_segment_profile(node, tags)
    required_inputs = _human_required_inputs(node.get("missing_required_fields") or node.get("must_collect_before_final", ""))
    local_context = [
        "奥森周边 1-3 公里常住人口、办公人口、学校/场馆客流和游客来源已列为内部复核变量。",
        "朝阳/奥森周边街道级收入、消费层级、租金和品牌可承受客单价只作约束条件，不在本稿写成最终定值。",
        "节点周边同类供给、竞品价格、停车/地铁导流和居民投诉历史进入下一轮地图与现场复核口径。",
    ]
    options = _node_options(case)
    recommended = {
        "taohuayuan": "先选低改造试点，把轻餐、摄影和预约活动跑出客流-转化-客单价曲线，再决定是否做阳光房和固定场景。",
        "lianjie": "先选健康生活方式试点，诊疗/检测/疗程包只在资质方和责任边界闭合后进入二期。",
        "west_zone": "先选国潮轻餐与文创标准化试点，Live House 暂降为活动组件。",
        "underground": "先做分区小样和招商测试，不能用一个重资产主题一次性吃满地下空间。",
        "theater": "先做季节型移动补给和活动日历，天气与审批验证后再扩大。",
        "guoyi": "先做中医文化体验与课程，医疗服务必须由资质主体承接后再讨论。",
        "general": "先做低改造试点，真实客流、收入层级和许可完成内部复核后再升级。",
    }.get(case, "先做低改造试点，真实客流、收入层级和许可完成内部复核后再升级。")
    return {
        "target_segments": profile.get("target_segments", []),
        "demand_triggers": profile.get("demand_triggers", []),
        "income_and_price_band": profile.get("income_and_price_band", []),
        "time_weather": _node_time_weather(case),
        "surrounding_context_needed": local_context,
        "location_fit": [
            "先确认入口距离、可见性、绕行距离和导视；如果路线弱，优先做移动/预约/活动型产品。",
            "CAD/DXF 只能证明图纸锚点存在；进入路径级仿真前必须做控制点校准。",
            "园内公共空间属性要求商业服务服从游客体验、生态和秩序，不宜只按租金最大化设计。",
        ],
        "options": options,
        "recommended_path": recommended,
        "why_this_is_preferred": [
            "先低投入验证可以暴露真实客群、收入水平、天气影响和许可难点，避免一次性重资产误判。",
            "公园商业的核心不是单点高分，而是不同节点在时间、天气和客群上的互补。",
            "当前资料足以生成修正建议；最终投资和收益仍需走定案复核。",
        ],
        "must_verify_before_commitment": list(dict.fromkeys(required_inputs + [
            "周边人口与收入分层",
            "价格带与客单价承受力",
            "天气/季节敏感性",
            "现场审批和居民/游客接受度",
        ])),
        "risk_controls": [
            "把医疗、演出、酒水、外摆和夜间活动放入许可清单，不在文案里提前承诺。",
            "用试运营数据复核转化率、客单价和复购，而不是用 AI 草稿或旧分数代替。",
            "每个重资产方案必须有可退出的分期路径和敏感性分析。",
        ],
        "evidence_that_changes_decision": [
            "周边收入和消费层级显著低于高客单假设时，降级为低客单高频产品。",
            "恶劣天气或淡季导致户外停留大幅下降时，户外节点必须有雨备/冬季替代。",
            "审批、消防、医疗、演出或居民投诉风险无法闭合时，相关业态降级或暂缓。",
            "试运营显示高转化和稳定复购时，才进入标准运营或二期改造。",
        ],
        "simulation_inputs": [
            "分入口分时段客流",
            "人群状态和同行关系",
            "收入/支付能力分层",
            "天气与季节场景",
            "路线距离和可见性",
            "同类 POI 价格与供给",
            "转化率、客单价、成本和审批状态",
        ],
    }


REQUIRED_INPUT_LABELS = {
    "geometry": "图纸坐标、面积和路径校准",
    "visitor_flow": "分入口、分时段真实客流",
    "conversion_rate": "各业态到店/到场转化率",
    "revenue_cost": "租金、分成、装修、人工和运营成本",
    "operation_authorization": "消防、结构、食品、医疗/演出等经营授权",
    "model_gate": "仿真验收口径和人工复核标准",
    "真实客流": "真实客流",
    "转化率": "转化率",
    "客单价": "客单价",
    "租金/分成": "租金/分成",
    "装修/人工/运营成本": "装修、人工和运营成本",
    "运营授权": "运营授权",
}

BEIJING_REAL_WORLD_CONTEXT = {
    "source_urls": [
        "https://tjj.beijing.gov.cn/zxfbu/202601/t20260121_4451962.html",
        "https://tjj.beijing.gov.cn/zxfbu/202601/t20260121_4451977.html",
        "https://tjj.beijing.gov.cn/zxfbu/202601/t20260121_4452019.html",
    ],
    "verified_at": "2026-06-07",
    "items": [
        "国家统计局北京调查总队披露：2025 年北京居民人均可支配收入 89090 元，城镇居民 96292 元。",
        "同源资料披露：2025 年北京居民人均消费支出 50667 元，城镇居民 54122 元。",
        "服务性消费支出 30052 元，占居民消费支出 59.3%；教育文化娱乐支出 4838 元，同比增长 6.5%。",
    ],
    "use_boundary": "这些是全市上位消费能力边界，不能替代奥森周边街道、社区、办公和游客来源的收入分层。",
}

REAL_WORLD_HARD_INPUTS = [
    "周边 1-3 公里居住人口、办公人口、学校/场馆客群和游客来源结构。",
    "周边收入水平、消费层级、家庭/亲子/银发/白领的客单价承受区间。",
    "工作日、周末、节假日、早中晚、活动前后和季节淡旺季的客流分布。",
    "高温、降雨、寒冷、风、空气质量、遮阴、避雨和取暖条件。",
    "入口可达、绕行距离、停车、地铁公交、无障碍、导视和夜间照明。",
    "食品、演出、医疗、外摆、酒水、夜间、临时市集和活动审批边界。",
    "租金/分成、CAPEX、OPEX、人力、设备、库存、客单价、转化率和回收期。",
    "新闻舆情、居民投诉、游客接受度、价格敏感度和公园公共性边界。",
]


def _human_required_inputs(value: Any) -> list[str]:
    raw = re.split(r"[;；,，\n]+", _as_text(value))
    labels: list[str] = []
    for item in raw:
        clean = item.strip()
        if not clean:
            continue
        labels.append(REQUIRED_INPUT_LABELS.get(clean, clean))
    deduped: list[str] = []
    for label in labels:
        if label and label not in deduped:
            deduped.append(label)
    return deduped


def _human_gate_block(row: dict[str, Any], cad_ready: bool = False) -> str | None:
    domain = str(row.get("calibration_domain") or row.get("gate_id") or "").strip()
    if domain == "geometry":
        if cad_ready:
            return "图纸与空间：南北园 DWG 已完成 DXF 转换；下一步补控制点校准、可经营面积和路径复核。"
        return "图纸与空间：需完成 DWG/DXF 转换、控制点校准、可经营面积和路径复核。"
    if domain == "visitor_flow":
        return "客流：需补分入口、分时段、工作日/周末/节假日的真实客流。"
    if domain == "conversion_rate":
        return "转化：需补各业态从路过、停留到购买/预约的转化率。"
    if domain == "revenue_cost":
        return "财务：需补租金、分成、装修、人工、设备、库存和运营成本。"
    if domain == "operation_authorization":
        return "授权：需补消防、结构、食品、医疗/演出、外摆和夜间运营许可边界。"
    if domain == "model_gate":
        return "仿真验收：需确定真实数据、校准指标、人工复核标准和版本验收口径。"
    reason = _first_nonempty(row.get("blocking_reason"), row.get("current_gate_status"))
    if reason:
        return reason
    return None


def _evidence_line(item: dict[str, Any]) -> str:
    metric = _first_nonempty(item.get("metric_name"), item.get("indicator_name"), item.get("name"))
    value = _first_nonempty(item.get("value"))
    unit = _first_nonempty(item.get("unit"))
    source = _first_nonempty(item.get("source_file"))
    source_name = Path(source).name if source else "证据台账"
    if "奥林匹克森林公园区域大数据分析报告" in source_name or "奥林匹克森林公园区域大数据分析报告" in source:
        source_name = "奥森区域大数据分析报告"
    elif "城市绿心公园区域大数据分析报告" in source_name or "城市绿心公园区域大数据分析报告" in source:
        source_name = "城市绿心区域大数据分析报告"
    metric_id = _first_nonempty(item.get("metric_id"), item.get("evidence_id"))
    suffix = f"（{metric_id}）" if metric_id else ""
    if value or unit:
        return f"{metric}{suffix}：{value}{unit}，来源 {source_name}"
    return f"{metric}{suffix}，来源 {source_name}"


def _calibration_layer_label(value: Any) -> str:
    labels = {
        "official_macro_boundary": "官方宏观边界",
        "local_bigdata_profile": "本地大数据画像",
        "local_device_price_proxy": "设备价格代理",
        "local_poi_price_signal": "竞品价格线索",
        "local_poi_demand_signal": "本地需求热度线索",
        "plan_assumption_needs_review": "方案假设待复核",
        "local_user_supplement": "用户补充校准输入",
    }
    return labels.get(str(value or ""), str(value or "待分层"))


def _summarize_assets(local_data_assets: list[dict[str, Any]] | None) -> list[str]:
    lines = []
    for asset in local_data_assets or []:
        label = _first_nonempty(asset.get("label"))
        count = _first_nonempty(asset.get("count"))
        status = _first_nonempty(asset.get("status"))
        scope = _first_nonempty(asset.get("use_scope"))
        if label:
            lines.append(f"{label}：{count}；{status}；{scope}")
    return lines


def _cad_summary(site_context: dict[str, Any] | None) -> dict[str, Any]:
    cad = (site_context or {}).get("cad_analysis") or {}
    results = cad.get("results") if isinstance(cad, dict) else []
    rows = []
    anchors = []
    for result in results or []:
        hit_count = len(result.get("keyword_hits") or [])
        rows.append(
            {
                "cad_id": result.get("cad_id", ""),
                "source_dwg": result.get("source_dwg", ""),
                "dxf_path": result.get("dxf_path", ""),
                "dxf_bytes": result.get("dxf_bytes", 0),
                "entity_type_count": len(result.get("entity_counts") or {}),
                "keyword_hit_count": hit_count,
                "bounds": result.get("bounds", {}),
            }
        )
        for hit in (result.get("keyword_hits") or [])[:12]:
            anchors.append(
                {
                    "cad_id": result.get("cad_id", ""),
                    "label": hit.get("text", ""),
                    "keyword": hit.get("keyword", ""),
                    "layer": hit.get("layer", ""),
                    "x": hit.get("x"),
                    "y": hit.get("y"),
                }
            )
    north_pdf_hits = (site_context or {}).get("north_pdf_hits") or []
    return {
        "converted_drawings": rows,
        "keyword_anchors": anchors,
        "north_pdf_hits": north_pdf_hits,
        "boundary_note": (
            "DWG 已转 DXF 并可抽图层、实体和标签；但 CAD 坐标仍需控制点/坐标系确认后才能升级为 GIS 路径或精确面积结论。"
        ),
    }


def build_gap_report(
    nodes: list[dict[str, Any]],
    gap: dict[str, Any],
    uploads: list[dict[str, Any]],
    *,
    visitor_sources: dict[str, Any] | None = None,
    tgi: dict[str, Any] | None = None,
    supply: dict[str, Any] | None = None,
    local_data_assets: list[dict[str, Any]] | None = None,
    map_context: dict[str, Any] | None = None,
    amap_supply: list[dict[str, Any]] | None = None,
    gates: list[dict[str, Any]] | None = None,
    simulation_objects: list[dict[str, Any]] | None = None,
    site_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    expert_basis = _expert_review_basis()
    node_items = []
    for index, node in enumerate(nodes):
        gap_match = node.get("supply_gap_match") or {}
        implementation_review = _implementation_review(node, index)
        node_items.append(
            {
                "node_id": node.get("node_id", ""),
                "node_name": node.get("node_name", ""),
                "area_sqm": node.get("area_sqm", ""),
                "positioning": node.get("primary_positioning", ""),
                "business_tags": _business_tags(node),
                "priority_stage": _priority_stage(node, index),
                "matched_gap": gap_match,
                "improvement": _node_recommendation(node),
                "implementation_review": implementation_review,
                "required_inputs": _human_required_inputs(
                    node.get("missing_required_fields") or node.get("must_collect_before_final", "")
                ),
                "output_status": "needs_review",
                "not_final": True,
            }
        )
    evidence_highlights = (site_context or {}).get("evidence_highlights") or []
    plan_profile = (site_context or {}).get("plan_profile") or {}
    project_titles = [node.get("node_name", "") for node in nodes if node.get("node_name")]
    cad = _cad_summary(site_context)
    cad_ready = bool(cad.get("converted_drawings"))
    gate_blocks = [item for item in (_human_gate_block(row, cad_ready=cad_ready) for row in gates or []) if item][:8]
    supply_counts = (supply or {}).get("poi_counts") or {}
    poi_count = len(amap_supply or [])
    object_counts = Counter(str(row.get("object_type") or "未分类") for row in simulation_objects or [])
    executive_summary = [
        "本稿按奥森重点项目策划书、南北园 CAD/DWG、北园图纸 PDF、已有客流/消费画像和高德 POI 线索生成，定位为“可讨论的综合工作稿”，不是最终投资或收益结论。",
        f"原计划不是单点方案，而是 {len(nodes)} 个项目节点的组合：{ '、'.join(project_titles[:6]) }。报告按节点条件、业态逻辑和落地风险合并判断，不再用单一分数替代建议。",
        "已能较稳地判断：咖啡/冷饮、轻餐、运动康养、亲子活动和季节性户外内容有明确讨论价值；重设备医疗、夜间演出、大体量地下空间和诊疗类项目必须先过收入客群、资质、消防、运营和转化率门槛。",
        "CAD 已完成南北园 DWG 到 DXF 的转换并抽取图纸标签；南园图纸已命中南入口、露天剧场、廉洁馆、2A03 等锚点。下一步需要把 CAD 坐标用控制点校准到 GIS，才能做路径级仿真和精确面积复核。",
        "北京市 2025 年收入与消费数据可以作为上位消费能力边界；但奥森周边街道级人口、收入、住宅/办公/学校结构和游客来源尚未闭合，不能据此直接定高客单或收益。",
    ]
    current_judgements = [
        "先把项目拆成“低改造试点、资质依赖、重资产条件型”三类推进，比直接排名更可信。",
        "先验证高频轻消费、预约活动和价格带，再扩展大体量、重设备和夜间项目，可以降低一次性招商和工程风险。",
        "POI/TGI 与客流只能说明需求和供给语境，不能直接推出收入；报告中的收益、转化和回收期只能在真实参数完成内部复核后计算。",
    ]
    revision_advice = [
        "建立南门综合簇：以南门地下预埋空间为重资产承接，以露天剧场做轻量活动和烘焙咖啡试点，以 2A03/廉洁馆承接康养与文化预约服务。",
        "建立北园轻活动点：桃花源白房子先做花海打卡、轻餐和预约小活动，不先背负复杂餐饮厨房和大规模活动运营。",
        "把“疗愈/国医/检测”统一降级为先验证的健康生活方式产品；涉及诊疗、检测、药房、针灸等服务，必须由资质方负责并写入合作边界。",
        "把 Live House 从主方案改为可选内容组件；更成熟的首选是国潮轻餐、文创、亲子体验和周末小型演出。",
        "用 CAD 控制点、入口客流、转化率、客单价、租金/分成、运营成本和审批资料作为下一轮仿真的硬输入，不让 AI 或旧分数替代真实参数。",
    ]
    method_trace = [
        {
            "source": "老板资料：DLR/FLR/SSR 与 Agent Bank 方法",
            "used_for": "把旧节点分数降级为“理由先行、再映射优先级”，报告不再用裸分数替代建议。",
            "report_sections": ["六个项目节点的综合判断与修改建议", "现阶段判断"],
            "boundary": "不把市场研究案例里的准确率或评分方法当成本项目承诺。",
        },
        {
            "source": "老板资料 / ROTE：行为程序与有限状态机",
            "used_for": "把公园消费解释为状态、触发、动作、放弃和外溢，而不是让 AI 临场编游客故事。",
            "report_sections": ["综合修改意见", "仿真与定案边界"],
            "boundary": "当前没有真实轨迹和停留数据，不宣称已完成贝叶斯权重更新或完整行为仿真。",
        },
        {
            "source": "老板资料 / HumanLM：潜在状态优先",
            "used_for": "节点建议先区分亲子、运动、康养、文化、夜间等动机和状态，再给运营建议。",
            "report_sections": ["原计划理解", "六个项目节点的综合判断与修改建议"],
            "boundary": "不把“写得像人”当模拟成功；必须保留真实用户状态和数据校准缺口。",
        },
        {
            "source": "老板资料 / 高清社区仿真：GIS/BIM + RL + LLM + 双重奖励",
            "used_for": "把 CAD/GIS、宏观客流、微观状态-行为一致性作为进入完整仿真的前置条件。",
            "report_sections": ["关键依据", "仿真与定案边界"],
            "boundary": "当前不训练 PPO、不做 Unreal 复刻；只落成校准门槛和可复跑对象链。",
        },
        {
            "source": "现代论文：MobiVerse / CAMS / CitySim 等 LLM 城市移动仿真",
            "used_for": "采用“轻量规则/领域生成器先生成活动链，模型只做上下文修正和解释”的结构。",
            "report_sections": ["方法依据", "仿真与定案边界"],
            "boundary": "不逐游客调用模型；不让模型直接输出最终商业结论。",
        },
        {
            "source": "商业选址方法：Huff / Logit / Gravity / POI-TGI 缺口",
            "used_for": "把咖啡、冷饮、餐饮、运动康养等判断放在需求偏好、供给、距离和承接能力的共同语境里。",
            "report_sections": ["关键依据", "供需缺口草案"],
            "boundary": "POI/TGI 是相关性和供需语境，不是因果，也不是收益预测。",
        },
        {
            "source": "真实世界实施知识底座：近年研究筛选 + 官方实践约束 + 北京收入消费数据",
            "used_for": "把目标人群、收入水平、时间天气、周边人口、工程消防、许可、财务、舆情和仿真校准作为每个节点的硬评审维度。",
            "report_sections": ["专家评审底座", "节点实施评审", "当前推进事项"],
            "boundary": "研究和全市统计只提供约束框架；街道级收入、客群、价格和试运营结果仍需内部复核。",
        },
        {
            "source": "CAD 工具链：ODA File Converter 27.1.0 + LibreDWG 0.13.4 + DXF 流式解析",
            "used_for": "把用户给的南北园 DWG 转成 DXF，抽取实体、图层、标签锚点和图纸代理证据。",
            "report_sections": ["关键依据", "CAD / 图纸处理"],
            "boundary": "DXF 坐标未做控制点校准前，不能直接当高德/OSM 地理坐标或精确路径仿真。",
        },
    ]
    return {
        "report_id": f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "title": "奥森商业改造综合评估与修正建议工作稿",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "output_status": "needs_review",
        "not_final": True,
        "source_upload_count": len(uploads),
        "gap_status": gap.get("status", ""),
        "summary": "；".join(executive_summary[:2]),
        "executive_summary": executive_summary,
        "method_basis": [
            "资料证据先行：策划书、CAD、PDF、POI、证据台账分层使用，PPT/策划表述不能直接当最终事实。",
            "空间选址逻辑采用“距离/可达/吸引力/竞争供给”的商业分析思想；Huff/Logit/Gravity 只作为概率因子，不单独给最终结论。",
            "人物仿真采用“人群状态、行为程序、选择概率、验证目标”对象链；模型只能生成候选和表达草稿，最终判断由证据和人工复核收口。",
            "实施评审采用十五类真实世界维度：政策、公园适配、目标人群、周边人口与收入、时间天气、地理可达、工程消防、许可、运营、财务、品牌、维护、舆情和仿真校准。",
        ],
        "method_trace": method_trace,
        "expert_review_basis": expert_basis,
        "source_foundation": {
            "assets": _summarize_assets(local_data_assets),
            "plan_profile": {
                "paragraph_count": plan_profile.get("paragraph_count", ""),
                "table_count": plan_profile.get("table_count", ""),
                "keyword_counts": plan_profile.get("keyword_counts", {}),
                "limitations": plan_profile.get("limitations", []),
            },
            "cad": cad,
            "map_context": {
                "name": (map_context or {}).get("name") or (map_context or {}).get("keyword") or "",
                "longitude": (map_context or {}).get("longitude", ""),
                "latitude": (map_context or {}).get("latitude", ""),
                "poi_count": poi_count,
                "supply_counts": supply_counts,
            },
            "evidence_highlights": [_evidence_line(item) for item in evidence_highlights[:18]],
        },
        "original_plan_reading": [
            "策划书把奥森商业机会拆为六类空间：花海轻活动点、健康疗愈展馆、西分区复合消费、南门地下大体量、南门露天草坪活动、2A03 国医国学中心。",
            "这些项目的共同方向是“公园停留时间变长后，把自然游憩转化为轻餐、活动、康养、文创和预约服务”。关键不是单点好坏，而是节点之间是否形成可运营的南北分工。",
            "原计划中部分案例和财务假设具有启发性，但还缺少客流分配、转化率、客单价、成本、审批和经营授权，不能直接写成最终收益预测。",
        ],
        "current_judgements": current_judgements,
        "revision_advice": revision_advice,
        "simulation_readiness": {
            "can_run_now": [
                "按策划书节点生成讨论级报告和修改建议。",
                "按 CAD 标签建立南园项目锚点清单。",
                "按证据台账识别咖啡、冷饮、瑜伽、餐饮消费和到访峰值等需求线索。",
            ],
            "cannot_claim_yet": [
                "不能声明最终节点排序、最终 ROI、最终收益或完整人群仿真结果。",
                "不能把 DXF 图纸坐标直接当高德/OSM 地理坐标；必须先做控制点校准。",
                "不能把模型草稿、PPT 假设或热门 POI 表直接当经营事实。",
                "不能用北京市全市收入均值替代奥森周边街道级收入、客群来源和价格敏感度。",
            ],
            "blocking_inputs": list(dict.fromkeys(gate_blocks + REAL_WORLD_HARD_INPUTS[:6])),
            "simulation_object_counts": dict(object_counts),
        },
        "top_gaps": gap.get("items", [])[:5],
        "nodes": node_items,
        "next_actions": [
            "用南门、露天剧场、2A03、廉洁馆等 CAD 锚点做一次图纸到地图的控制点校准，输出可复核 GeoJSON。",
            "对六个节点分别复核客流入口、停留时长、转化率、客单价、租金/分成、装修和运营成本。",
            "补奥森周边 1-3 公里人口、收入水平、居住/办公/学校结构、游客来源和竞品价格，校准各业态价格带。",
            "把南门簇先做成小规模试运营方案：咖啡/烘焙、草坪活动、运动户外快闪和健康课程，观察停留与消费转化。",
            "把重资产业态拆成招商模块和审批清单，未通过消防、结构、医疗/演出/食品等许可前不进入定案。",
            "在网站里把本报告作为项目综合会话的底稿，让用户继续追问并生成下一版报告。",
        ],
    }


def report_to_markdown(report: dict[str, Any]) -> str:
    lines = [f"# {report['title']}", "", f"生成时间：{report['generated_at']}", ""]
    lines.extend(["## 1. 摘要：现在能确认什么", ""])
    for item in report.get("executive_summary", []):
        lines.append(f"- {item}")
    lines.extend(["", "## 2. 关键依据：来自哪些资料", ""])
    foundation = report.get("source_foundation") or {}
    for item in foundation.get("evidence_highlights", []):
        lines.append(f"- {item}")
    if not foundation.get("evidence_highlights"):
        lines.append("- 当前证据台账未提供可展示指标，报告只能保留为资料结构稿。")
    lines.extend(["", "### CAD / 图纸处理", ""])
    cad = foundation.get("cad") or {}
    for drawing in cad.get("converted_drawings", []):
        size_mb = round(float(drawing.get("dxf_bytes") or 0) / 1024 / 1024, 1)
        lines.append(
            f"- {drawing.get('cad_id')}：{drawing.get('source_dwg')} 已转 DXF（约 {size_mb} MB），实体类型 {drawing.get('entity_type_count')} 类，关键词锚点 {drawing.get('keyword_hit_count')} 个。"
        )
    for anchor in cad.get("keyword_anchors", [])[:10]:
        lines.append(f"  - {anchor.get('label')}：图层 {anchor.get('layer')}，坐标 {anchor.get('x')}, {anchor.get('y')}")
    for hit in cad.get("north_pdf_hits", [])[:6]:
        lines.append(f"  - 北园 PDF 文字命中：{hit.get('text')}")
    if cad.get("boundary_note"):
        lines.append(f"- 图纸边界：{cad['boundary_note']}")
    lines.extend(["", "## 3. 方法说明", ""])
    lines.append("本稿采用“资料分层、空间校准、需求-供给对照、行为状态约束、人工复核收口”的方法。也就是说，策划书用于理解意图，CAD/图纸用于识别空间锚点，客流和消费画像用于判断需求语境，POI 用于判断供给语境；凡是缺少真实转化、成本、审批和坐标校准的内容，只能写成修正建议，不能写成最终收益或最终排序。")
    expert = report.get("expert_review_basis") or {}
    if expert:
        lines.extend(["", "## 4. 专家评审底座", ""])
        screened = expert.get("screened_count") or 0
        completed = expert.get("completed_query_count") or 0
        query_total = expert.get("query_total") or 0
        if screened:
            lines.append(f"- 已完成 {completed}/{query_total} 组主题检索，高相关研究候选 {screened} 条；这些资料只用于约束评审维度，不直接写成项目结论。")
        beijing = expert.get("beijing_context") or {}
        for item in beijing.get("items", []):
            lines.append(f"- {item}")
        if beijing.get("use_boundary"):
            lines.append(f"- 使用边界：{beijing['use_boundary']}")
        dimensions = expert.get("dimensions") or []
        if dimensions:
            lines.append("- 本稿把以下维度作为节点硬评审口径：" + "、".join(str(row[0]) for row in dimensions[:15] if row))
    calibration_context = report.get("real_calibration_context") or {}
    lines.extend(["", "## 5. 真实校准输入与使用边界", ""])
    if calibration_context.get("count"):
        lines.append(
            f"- 已接入 {calibration_context.get('count')} 条真实校准输入，用于约束收入/消费边界、本地画像、设备价格代理、竞品价格和方案假设。"
        )
        strengths = calibration_context.get("source_strength_counts") or {}
        if strengths:
            layer_summary = [
                f"{_calibration_layer_label(layer)} {count} 条"
                for layer, count in strengths.items()
                if count
            ]
            if layer_summary:
                lines.append("- 分层数量：" + "；".join(layer_summary))
        if calibration_context.get("report_rule"):
            lines.append(f"- 使用规则：{calibration_context['report_rule']}")
        rows = calibration_context.get("items") or []
        if rows:
            lines.append("")
            lines.append("| 输入编号 | 分层 | 指标 | 数值 | 进入仿真的用法 | 不能直接宣称 |")
            lines.append("|---|---|---|---|---|---|")
            for item in rows[:10]:
                value = f"{item.get('value', '')}{item.get('unit', '')}"
                lines.append(
                    "| {cid} | {layer} | {name} | {value} | {use} | {cannot} |".format(
                        cid=item.get("calibration_id", ""),
                        layer=_calibration_layer_label(item.get("source_strength")),
                        name=item.get("indicator_name", ""),
                        value=value,
                        use=item.get("simulation_use", ""),
                        cannot=item.get("cannot_claim", ""),
                    )
                )
        missing = calibration_context.get("missing_before_final") or []
        if missing:
            lines.append("")
            lines.append("- 进入定案前内部复核项：" + "；".join(missing[:6]))
    else:
        lines.append("- 当前还没有可复跑真实校准输入；报告只能保留为方法工作稿，不能进入收益或排名判断。")
    feature_context = report.get("controlled_feature_scene_context") or {}
    lines.extend(["", "## 6. 人物场景输入与收入价格带", ""])
    if feature_context.get("count"):
        lines.append(
            f"- 已采用/锁定 {feature_context.get('count')} 条人物场景进入本轮报告输入；这些场景只用于讨论级敏感性审查，不代表真实客群占比。"
        )
        if feature_context.get("income_segments"):
            lines.append(f"- 收入段覆盖：{'、'.join(feature_context.get('income_segments', [])[:8])}")
        if feature_context.get("price_bands"):
            lines.append(f"- 消费价格带：{'、'.join(feature_context.get('price_bands', [])[:8])}")
        lines.append("")
        lines.append("| 场景编号 | 场景 | 收入/价格带 | 时段/天气/空间 | 建议动作 | 复核证据 |")
        lines.append("|---|---|---|---|---|---|")
        for item in feature_context.get("items", [])[:8]:
            lines.append(
                "| {scene_id} | {title} | {income} / {price} | {time}；{weather}；{space} | {action} | {data} |".format(
                    scene_id=item.get("derivative_id", ""),
                    title=item.get("title", ""),
                    income=item.get("income_segment_name", ""),
                    price=item.get("income_price_band", ""),
                    time=item.get("time_band_name", ""),
                    weather=item.get("weather_name", ""),
                    space=item.get("node_context_name", ""),
                    action=item.get("candidate_supply_action_name", ""),
                    data=item.get("data_needed", ""),
                )
            )
    else:
        lines.append(f"- {feature_context.get('empty_state') or '当前还没有采用或锁定的人物场景；报告只引用覆盖池作为方法底座。'}")
    if feature_context.get("report_rule"):
        lines.append(f"- 使用规则：{feature_context['report_rule']}")
    lines.extend(["", "## 7. 原计划理解", ""])
    for item in report.get("original_plan_reading", []):
        lines.append(f"- {item}")
    lines.extend(["", "## 8. 六个项目节点的综合判断与修改建议", ""])
    for node in report.get("nodes", []):
        tags = "、".join(node.get("business_tags") or []) or "业态标签待复核"
        area = f"{node.get('area_sqm')}㎡" if node.get("area_sqm") else "面积待复核"
        review = node.get("implementation_review") or {}
        lines.extend(
            [
                f"### {node.get('node_id')} {node.get('node_name')}（{area}）",
                "",
                f"- 推进类型：{node.get('priority_stage')}",
                f"- 业态方向：{tags}",
                f"- 原计划要点：{node.get('positioning') or '策划书未提供完整定位。'}",
                f"- 修正建议：{node.get('improvement')}",
            ]
        )
        if review:
            lines.append(f"- 服务对象：{'；'.join(review.get('target_segments') or [])}")
            lines.append(f"- 需求触发：{'；'.join(review.get('demand_triggers') or [])}")
            lines.append(f"- 收入与价格带：{'；'.join(review.get('income_and_price_band') or [])}")
            lines.append(f"- 推荐路径：{review.get('recommended_path')}")
            lines.append("")
            lines.append("| 方案 | 怎么做 | 适用条件 | 先决条件 | 主要风险 | 需要验证 |")
            lines.append("|---|---|---|---|---|---|")
            for option in review.get("options", [])[:3]:
                lines.append(
                    "| {name} | {what} | {best} | {pre} | {risk} | {ev} |".format(
                        name=option.get("name", ""),
                        what=option.get("what_to_do", ""),
                        best=option.get("best_for", ""),
                        pre="；".join(option.get("prerequisites", [])[:3]),
                        risk="；".join(option.get("risks", [])[:3]),
                        ev="；".join(option.get("evidence_to_validate", [])[:3]),
                    )
                )
            lines.append("")
            for title, key in [
                ("时间/天气", "time_weather"),
                ("周边复核口径", "surrounding_context_needed"),
                ("风险控制", "risk_controls"),
                ("会改变判断的证据", "evidence_that_changes_decision"),
            ]:
                values = review.get(key) or []
                if values:
                    lines.append(f"- {title}：{'；'.join(values[:4])}")
        required = node.get("required_inputs") or []
        if required:
            lines.append(f"- 进入定案前需要：{'；'.join(required)}")
        lines.append("")
    lines.extend(["## 9. 现阶段判断", ""])
    for item in report.get("current_judgements", []):
        lines.append(f"- {item}")
    lines.extend(["", "## 10. 综合修改意见", ""])
    for item in report.get("revision_advice", []):
        lines.append(f"- {item}")
    lines.extend(["", "## 11. 仿真与定案边界", ""])
    readiness = report.get("simulation_readiness") or {}
    lines.append("现在可以做：")
    for item in readiness.get("can_run_now", []):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("现在不能宣称：")
    for item in readiness.get("cannot_claim_yet", []):
        lines.append(f"- {item}")
    if readiness.get("blocking_inputs"):
        lines.extend(["", "定案前内部复核项："])
        for item in readiness.get("blocking_inputs", []):
            lines.append(f"- {item}")
    lines.extend(["", "## 12. 当前推进事项", ""])
    for item in report.get("next_actions", []):
        lines.append(f"- {item}")
    lines.extend(["", "## 附录：供需缺口草案", ""])
    if report.get("top_gaps"):
        for item in report.get("top_gaps", []):
            lines.append(
                f"- {item['business_type']}：TGI {item['tgi']}，POI {item['poi_count']}，缺口指数 {item['gap_index']}，{item['priority']}"
            )
    else:
        lines.append("- 当前供需缺口排序仍等待客流/TGI/POI 口径闭合；本报告先给出节点级修改建议。")
    lines.extend(["", "## 使用边界", ""])
    lines.append("本稿用于内部研判、方案修正和定案前复核。进入客户正式汇报前，应完成 CAD 控制点校准、现场/运营复核、财务参数复核和人工审阅。")
    return "\n".join(lines) + "\n"


def write_report_files(report: dict[str, Any], out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    base = out_dir / "site_selection_gap_report_latest"
    json_path = base.with_suffix(".json")
    md_path = base.with_suffix(".md")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(report_to_markdown(report), encoding="utf-8")
    return {"json": str(json_path), "md": str(md_path)}
