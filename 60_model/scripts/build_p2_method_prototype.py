from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NODES = ROOT / "70_outputs" / "processed_tables" / "p2_project_node_candidates.csv"
ASSUMPTIONS = ROOT / "70_outputs" / "processed_tables" / "p2_business_scene_assumption_pool.csv"
GAPS = ROOT / "70_outputs" / "processed_tables" / "p2_input_gap_register.csv"

OUT_PERSONAS = ROOT / "70_outputs" / "processed_tables" / "p2_persona_parameter_prototype.csv"
OUT_TRIGGERS = ROOT / "70_outputs" / "processed_tables" / "p2_demand_trigger_matrix.csv"
OUT_FORMULA = ROOT / "70_outputs" / "processed_tables" / "p2_supply_gap_scoring_formula.csv"
OUT_SCORES = ROOT / "70_outputs" / "processed_tables" / "p2_candidate_method_readiness_scores.csv"
OUT_API = ROOT / "70_outputs" / "processed_tables" / "p2_postman_api_contract_draft.csv"
REPORT = ROOT / "40_quality_evidence" / "p2_method_prototype_report.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def build_personas() -> list[dict[str, object]]:
    base = [
        ("P2-PER-001", "亲子家庭", 0.18, "轻餐、游乐、亲子活动、遮阴休息", "P1 需求画像 + P2 场景假设", "needs_real_visitor_mix"),
        ("P2-PER-002", "运动健身人群", 0.16, "补给、运动装备、康复理疗、淋浴/储物线索", "P1 TGI/运动空间标签 + P2 运动设施", "needs_real_visitor_mix"),
        ("P2-PER-003", "周边白领与社交人群", 0.15, "咖啡、烘焙、早午餐、轻社交", "P1 消费偏好 + DOCX 业态假设", "needs_real_visitor_mix"),
        ("P2-PER-004", "老人康养人群", 0.14, "中医、康复、国学、安静休憩", "DOCX 中医国学康养假设", "needs_real_visitor_mix"),
        ("P2-PER-005", "外地游客与文化参观人群", 0.17, "展陈、纪念、文化体验、导览", "DOCX 廉洁主题展馆和文化项目", "needs_real_visitor_mix"),
        ("P2-PER-006", "夜间活动与演艺人群", 0.20, "露天剧场、夜间轻餐、活动补给", "DOCX 南门露天剧场假设", "needs_policy_and_flow_confirmation"),
    ]
    return [
        {
            "persona_id": pid,
            "persona_name": name,
            "prototype_weight": weight,
            "key_needs": needs,
            "source_basis": basis,
            "calibration_status": status,
            "output_status": "needs_review",
            "p2_use": "method_prototype_parameter_not_real_calibration",
        }
        for pid, name, weight, needs, basis, status in base
    ]


def build_triggers() -> list[dict[str, object]]:
    base = [
        ("P2-TRG-001", "亲子家庭", "周末/节假日", "亲子活动与轻餐需求上升", 1.25),
        ("P2-TRG-002", "亲子家庭", "儿童疲劳/等待", "休息、饮品、游乐消费触发", 1.15),
        ("P2-TRG-003", "运动健身人群", "运动后30分钟", "补给、康复、装备需求上升", 1.30),
        ("P2-TRG-004", "运动健身人群", "赛事/活动", "快速补给与品牌装备需求上升", 1.20),
        ("P2-TRG-005", "周边白领与社交人群", "午间/下午茶", "咖啡、烘焙、早午餐需求上升", 1.25),
        ("P2-TRG-006", "周边白领与社交人群", "社交约见", "环境型餐饮和轻社交需求上升", 1.15),
        ("P2-TRG-007", "老人康养人群", "上午低峰", "康养体验和安静服务需求上升", 1.10),
        ("P2-TRG-008", "老人康养人群", "健康活动", "中医康复与国学课程需求上升", 1.20),
        ("P2-TRG-009", "外地游客与文化参观人群", "参观动线经过", "展陈、导览和纪念消费需求上升", 1.15),
        ("P2-TRG-010", "外地游客与文化参观人群", "活动展览", "文化体验和轻餐停留需求上升", 1.20),
        ("P2-TRG-011", "夜间活动与演艺人群", "夜间演出", "餐饮、饮品和活动补给需求上升", 1.35),
        ("P2-TRG-012", "夜间活动与演艺人群", "政策允许夜间经营", "夜间消费场景才可进入测算", 1.00),
    ]
    return [
        {
            "trigger_id": tid,
            "persona_name": persona,
            "trigger_condition": condition,
            "demand_effect": effect,
            "prototype_multiplier": multiplier,
            "calibration_status": "needs_real_flow_and_behavior_data",
            "output_status": "needs_review",
        }
        for tid, persona, condition, effect, multiplier in base
    ]


def build_formula() -> list[dict[str, object]]:
    base = [
        ("P2-FORM-001", "demand_fit_score", 0.18, "业态/场景与 persona 需求匹配度", "0-100", "needs_review_assumption"),
        ("P2-FORM-002", "supply_gap_score", 0.18, "目标需求与现有供给覆盖差距", "0-100", "needs_verified_supply"),
        ("P2-FORM-003", "spatial_access_score", 0.14, "入口/节点/路径可达性", "0-100", "blocked_by_dwg_and_route_gap"),
        ("P2-FORM-004", "scene_synergy_score", 0.12, "与周边运动/文化/游乐/水绿标签的协同", "0-100", "pdf_proxy_only"),
        ("P2-FORM-005", "revenue_potential_score", 0.12, "消费转化、客单、频次的潜在贡献", "0-100", "blocked_by_revenue_cost_gap"),
        ("P2-FORM-006", "implementation_feasibility_score", 0.12, "改造、授权、政策、施工可行性", "0-100", "needs_operator_confirmation"),
        ("P2-FORM-007", "risk_penalty_score", -0.10, "审批、授权、夜间经营、施工和邻避风险扣分", "0-100", "needs_review"),
        ("P2-FORM-008", "evidence_confidence_score", 0.14, "输入证据完整度与可追溯性", "0-100", "computed_from_status_fields"),
    ]
    return [
        {
            "formula_id": fid,
            "metric_name": name,
            "prototype_weight": weight,
            "metric_definition": definition,
            "value_range": value_range,
            "calibration_status": status,
            "output_status": "needs_review",
        }
        for fid, name, weight, definition, value_range, status in base
    ]


def infer_tags(text: str) -> tuple[str, int]:
    tags: list[str] = []
    score = 50
    mapping = [
        ("桃花源", "文化休闲/轻餐", 8),
        ("廉洁", "文化展陈", 7),
        ("12#", "运动康复/轻餐", 6),
        ("南门地下", "大体量复合空间", 6),
        ("露天剧场", "活动演艺/夜间消费", 5),
        ("10#2A03", "中医国学康养", 7),
        ("中医", "康养", 5),
        ("烘焙", "烘焙早午餐", 4),
        ("剧场", "演艺活动", 4),
    ]
    for keyword, tag, delta in mapping:
        if keyword in text:
            tags.append(tag)
            score += delta
    return ";".join(dict.fromkeys(tags)) or "待复核业态", min(score, 82)


def build_scores(nodes: list[dict[str, str]], gaps: list[dict[str, str]]) -> list[dict[str, object]]:
    blocking_domains = {row.get("input_domain", "") for row in gaps if "blocking" in row.get("blocking_level", "")}
    blocking_domains |= {"geometry", "operation_authorization"}
    rows: list[dict[str, object]] = []
    for index, node in enumerate(nodes, start=1):
        text = " ".join(node.values())
        tags, demand_fit = infer_tags(text)
        evidence_confidence = 45
        if node.get("area_sqm"):
            evidence_confidence += 8
        if node.get("source_semantic_ids"):
            evidence_confidence += 7
        geometry_ready = "geometry" not in blocking_domains
        spatial_access = 25 if not geometry_ready else 55
        implementation = 35 if "operation_authorization" in blocking_domains else 55
        method_score = round(demand_fit * 0.36 + spatial_access * 0.18 + implementation * 0.18 + evidence_confidence * 0.28, 2)
        rows.append(
            {
                "candidate_score_id": f"P2-METHOD-SCORE-{index:03d}",
                "node_id": node.get("node_id", ""),
                "node_name": node.get("node_name", ""),
                "candidate_theme_tags": tags,
                "demand_fit_score_prototype": demand_fit,
                "spatial_access_score_prototype": spatial_access,
                "implementation_feasibility_score_prototype": implementation,
                "evidence_confidence_score_prototype": evidence_confidence,
                "method_readiness_score_prototype": method_score,
                "score_use_boundary": "ranking_method_draft_not_final_site_selection",
                "blocking_gaps": ";".join(sorted(blocking_domains)),
                "output_status": "needs_review",
            }
        )
    return rows


def build_api_contract() -> list[dict[str, object]]:
    base = [
        ("P2-API-001", "GET", "/p2/health", "模型服务健康检查", "no_key"),
        ("P2-API-002", "GET", "/p2/personas", "读取 persona 参数原型", "needs_review"),
        ("P2-API-003", "GET", "/p2/triggers", "读取需求触发矩阵", "needs_review"),
        ("P2-API-004", "GET", "/p2/candidates", "读取 P2 项目节点候选", "needs_review"),
        ("P2-API-005", "GET", "/p2/formula", "读取供需缺口评分公式", "needs_review"),
        ("P2-API-006", "POST", "/p2/score-preview", "用原型参数返回候选节点评分预览", "prototype_only"),
        ("P2-API-007", "GET", "/p2/gaps", "读取输入缺口登记", "needs_review"),
        ("P2-API-008", "GET", "/p2/evidence-status", "读取证据/缺口/转换状态摘要", "needs_review"),
    ]
    return [
        {
            "api_id": api_id,
            "method": method,
            "path": path,
            "purpose": purpose,
            "auth_or_key_policy": "no_real_key_in_collection" if status != "no_key" else "no_key_required",
            "request_body_status": "draft_schema_only",
            "response_status": status,
            "output_status": "needs_review",
        }
        for api_id, method, path, purpose, status in base
    ]


def main() -> None:
    nodes = read_csv(NODES)
    gaps = read_csv(GAPS)
    assumptions = read_csv(ASSUMPTIONS)

    personas = build_personas()
    triggers = build_triggers()
    formula = build_formula()
    scores = build_scores(nodes, gaps)
    api_contract = build_api_contract()

    write_csv(
        OUT_PERSONAS,
        personas,
        ["persona_id", "persona_name", "prototype_weight", "key_needs", "source_basis", "calibration_status", "output_status", "p2_use"],
    )
    write_csv(
        OUT_TRIGGERS,
        triggers,
        ["trigger_id", "persona_name", "trigger_condition", "demand_effect", "prototype_multiplier", "calibration_status", "output_status"],
    )
    write_csv(
        OUT_FORMULA,
        formula,
        ["formula_id", "metric_name", "prototype_weight", "metric_definition", "value_range", "calibration_status", "output_status"],
    )
    write_csv(
        OUT_SCORES,
        scores,
        [
            "candidate_score_id",
            "node_id",
            "node_name",
            "candidate_theme_tags",
            "demand_fit_score_prototype",
            "spatial_access_score_prototype",
            "implementation_feasibility_score_prototype",
            "evidence_confidence_score_prototype",
            "method_readiness_score_prototype",
            "score_use_boundary",
            "blocking_gaps",
            "output_status",
        ],
    )
    write_csv(
        OUT_API,
        api_contract,
        ["api_id", "method", "path", "purpose", "auth_or_key_policy", "request_body_status", "response_status", "output_status"],
    )

    REPORT.write_text(
        "\n".join(
            [
                "# P2 方法原型报告",
                "",
                "- 阶段口径：P2 方法原型闭环，不是 P3 真实校准，也不是 P4 完整 Agent/GIS 仿真。",
                f"- 项目节点候选：{len(nodes)} 条。",
                f"- 业态/场景假设来源：{len(assumptions)} 条 needs_review 假设。",
                f"- persona 参数原型：{len(personas)} 条。",
                f"- 需求触发矩阵：{len(triggers)} 条。",
                f"- 供需缺口评分公式：{len(formula)} 条。",
                f"- 候选节点评分预览：{len(scores)} 条。",
                f"- API 契约草案：{len(api_contract)} 条。",
                "",
                "## 使用边界",
                "",
                "- 所有 P2 方法原型输出均为 `needs_review`。",
                "- 候选评分只用于验证公式和字段链路，不是最终选址排序。",
                "- DWG 仍为 `pending_conversion`；没有可信转换产物前，不做几何、图层、面积、坐标或动线计算。",
                "- 真实客流、转化率、收益/成本、运营授权缺口仍需 P3/P4 前闭合或显式假设。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"p2_persona_parameter_prototype.csv rows={len(personas)}")
    print(f"p2_demand_trigger_matrix.csv rows={len(triggers)}")
    print(f"p2_supply_gap_scoring_formula.csv rows={len(formula)}")
    print(f"p2_candidate_method_readiness_scores.csv rows={len(scores)}")
    print(f"p2_postman_api_contract_draft.csv rows={len(api_contract)}")


if __name__ == "__main__":
    main()
