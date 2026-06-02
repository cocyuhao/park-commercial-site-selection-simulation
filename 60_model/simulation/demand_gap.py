from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


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
        priority = "优先补齐" if gap_index >= 0.25 else "可优化" if gap_index >= 0.08 else "暂不优先"
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
        if isinstance(score, (int, float)) and node.get("score_status") != "external_preview_only":
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
        return "未匹配到可计算缺口，先补客流/TGI资料和当前地图 POI。"
    if gap_match.get("priority") == "优先补齐":
        return f"建议优先补充{gap_match.get('business_type')}，并用现场约束复核面积、可达性和运营授权。"
    if gap_match.get("priority") == "可优化":
        return f"{gap_match.get('business_type')}有一定缺口，可作为组合业态或轻量试点。"
    return f"{gap_match.get('business_type')}暂不作为主要缺口，避免过早增加供给。"


def build_gap_report(nodes: list[dict[str, Any]], gap: dict[str, Any], uploads: list[dict[str, Any]]) -> dict[str, Any]:
    node_items = []
    for node in nodes:
        gap_match = node.get("supply_gap_match") or {}
        node_items.append(
            {
                "node_id": node.get("node_id", ""),
                "node_name": node.get("node_name", ""),
                "score": node.get("discussion_score_draft", ""),
                "matched_gap": gap_match,
                "improvement": improvement_for_gap(gap_match),
                "output_status": "needs_review",
                "not_final": True,
            }
        )
    return {
        "report_id": f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "title": "供需缺口与节点改进报告",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "output_status": "needs_review",
        "not_final": True,
        "source_upload_count": len(uploads),
        "gap_status": gap.get("status", ""),
        "summary": gap.get("message", ""),
        "top_gaps": gap.get("items", [])[:5],
        "nodes": node_items,
    }


def report_to_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['title']}",
        "",
        f"- 生成时间：{report['generated_at']}",
        "- 状态：needs_review / not_final",
        f"- 来源上传资料数：{report['source_upload_count']}",
        f"- 摘要：{report['summary']}",
        "",
        "## 主要供需缺口",
    ]
    for item in report.get("top_gaps", []):
        lines.append(
            f"- {item['business_type']}：TGI {item['tgi']}，POI {item['poi_count']}，缺口指数 {item['gap_index']}，{item['priority']}"
        )
    lines.extend(["", "## 节点改进建议"])
    for node in report.get("nodes", []):
        gap = node.get("matched_gap") or {}
        lines.append(f"- {node['node_id']} {node['node_name']}：{gap.get('business_type', '未匹配缺口')}；{node['improvement']}")
    lines.extend(["", "## 边界", "本报告只用于待复核讨论，不能作为最终推荐、最终排序或收益预测。"])
    return "\n".join(lines) + "\n"


def write_report_files(report: dict[str, Any], out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    base = out_dir / "site_selection_gap_report_latest"
    json_path = base.with_suffix(".json")
    md_path = base.with_suffix(".md")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(report_to_markdown(report), encoding="utf-8")
    return {"json": str(json_path), "md": str(md_path)}
