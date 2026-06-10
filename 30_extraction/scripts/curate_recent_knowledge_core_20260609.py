from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
KB_DIR = ROOT / "10_research" / "recent_knowledge_base_20260609"
QUALITY_DIR = ROOT / "40_quality_evidence"

SCREENED_JSONL = KB_DIR / "screened_knowledge_base_20260609.jsonl"
CURATED_JSONL = KB_DIR / "curated_core_knowledge_base_20260609.jsonl"
CURATED_CSV = KB_DIR / "curated_core_knowledge_base_20260609.csv"
METHOD_REFERENCE_CSV = KB_DIR / "method_reference_knowledge_base_20260609.csv"
REJECTED_CSV = KB_DIR / "curation_rejected_misfit_20260609.csv"
PLAYBOOK_JSON = KB_DIR / "knowledge_theme_playbooks_20260609.json"
QUALITY_REPORT_MD = KB_DIR / "curated_core_quality_report_20260609.md"
INTEGRATED_ARCHITECTURE_MD = KB_DIR / "integrated_simulation_architecture_blueprint_20260609.md"
VERIFY_JSON = QUALITY_DIR / "recent_knowledge_core_verification_20260609.json"

MIN_CORE_TOTAL = 1000
MIN_CORE_THEMES = 14
MIN_CORE_SOURCES = 2

PROJECT_ANCHORS = {
    "park_public_space": r"\bpark\b|green space|public space|urban plaza|recreation|visitor|tourism|amenity|concession",
    "retail_commercial": r"retail|commercial|consumer|spending|food beverage|pricing|revenue|store choice|tenant mix|conversion|unit economics",
    "spatial_mobility": r"\bGIS\b|geospatial|spatial|site selection|location|accessibility|catchment|POI|pedestrian|mobility|footfall|route choice|walkability",
    "simulation_agents": r"agent-based|agent based|multi-agent|LLM|large language model|digital twin|simulation|synthetic population|Monte Carlo|uncertainty",
    "operations_capacity": r"queue|capacity|service time|dwell time|crowd|density|bottleneck|inventory|trial metrics|demand forecasting",
    "real_world_constraints": r"weather|seasonality|microclimate|income|demographic|population|safety|fire|license|regulation|noise|complaint|governance",
    "evidence_decision": r"decision support|explainable|evidence|provenance|data quality|lineage|auditability|report|scenario|sensitivity",
    "cad_geometry": r"\bCAD\b|\bDWG\b|\bBIM\b|building footprint|3D city|geometry|spatial conversion|interoperability",
    "persona_activity_choice": r"persona|synthetic population|activity chain|activity-based|activity based|visitor typology|itinerary|discrete choice|multinomial logit|nested logit|Huff|gravity model",
    "pedestrian_abm_engine": r"\bMesa\b|agent-based|agent based|ABM|social force|cellular automata|pedestrian simulation|crowd simulation|microsimulation",
    "monte_carlo_uncertainty": r"Monte Carlo|uncertainty quantification|stochastic simulation|probabilistic|P5|P50|P95|Bayesian calibration",
}

OFF_DOMAIN_PATTERNS = {
    "medical_health": r"clinical|patient|hospital|healthcare|global health|primary healthcare|disease|cancer|drug|genomic|medical",
    "energy_microgrid": r"microgrid|renewable energy|electric vehicle charging|smart grid|solar|wind farm|battery|power system",
    "industrial_materials": r"chemical|material|protein|molecular|semiconductor|quantum|wireless sensor only",
    "port_space_disaster_only": r"space tourism|port policy|sanitary waste|wildfire|flood risk|earthquake emergency only|fuel infrastructure",
    "generic_language_only": r"English language needs|language learning|translation classroom|education only",
}

WEAK_VENUE_PATTERNS = r"IJRASET|International Journal of Research Publication|SSRN|preprint|Research Square|Zenodo|TechRxiv"


def load_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with SCREENED_JSONL.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def text_blob(row: dict[str, Any]) -> str:
    return " ".join(
        str(part or "")
        for part in [
            row.get("title"),
            row.get("abstract"),
            row.get("venue"),
            row.get("theme"),
            " ".join(row.get("project_landing", []) or []),
        ]
    )


def quality_classify(row: dict[str, Any]) -> dict[str, Any]:
    text = text_blob(row)
    anchor_hits = {
        name: bool(re.search(pattern, text, re.IGNORECASE))
        for name, pattern in PROJECT_ANCHORS.items()
    }
    off_domain_hits = {
        name: bool(re.search(pattern, text, re.IGNORECASE))
        for name, pattern in OFF_DOMAIN_PATTERNS.items()
    }
    anchor_count = sum(anchor_hits.values())
    off_count = sum(off_domain_hits.values())
    year = int(row.get("year") or 0)
    abstract_len = len(row.get("abstract") or "")
    source_tokens = set(str(row.get("source") or "").split("+"))
    venue = str(row.get("venue") or "")
    score = float(row.get("score") or 0)
    tier = row.get("tier") or ""
    weak_venue = bool(re.search(WEAK_VENUE_PATTERNS, venue, re.IGNORECASE))

    direct_theme = bool(
        set(str(row.get("theme") or "").split("+"))
        & {
            "spatial_site_selection",
            "human_mobility_behavior",
            "agent_llm_simulation",
            "park_recreation_tourism",
            "retail_operations_revenue",
            "real_world_constraints",
            "cad_bim_gis_digital_twin",
            "weather_season_event_demand",
            "demographics_income_market_segmentation",
            "safety_regulation_public_governance",
            "operations_revenue_unit_economics",
            "queue_crowd_capacity_operations",
            "transport_accessibility_last_mile",
            "multi_criteria_optimization_uncertainty",
            "ai_evaluation_observability_guardrails",
            "service_design_ai_workbench_ux",
            "park_publicness_experience_equity",
            "data_quality_evidence_chain",
        }
    )
    strong_project_fit = anchor_hits["park_public_space"] or (
        anchor_hits["retail_commercial"] and anchor_hits["spatial_mobility"]
    ) or (
        anchor_hits["simulation_agents"] and (anchor_hits["spatial_mobility"] or anchor_hits["evidence_decision"])
    ) or (
        anchor_hits["cad_geometry"] and anchor_hits["spatial_mobility"]
    ) or (
        anchor_hits["persona_activity_choice"] and (anchor_hits["park_public_space"] or anchor_hits["spatial_mobility"] or anchor_hits["retail_commercial"])
    ) or (
        anchor_hits["pedestrian_abm_engine"] and (anchor_hits["spatial_mobility"] or anchor_hits["park_public_space"])
    ) or (
        anchor_hits["monte_carlo_uncertainty"] and (anchor_hits["retail_commercial"] or anchor_hits["evidence_decision"] or anchor_hits["simulation_agents"])
    )

    reason: list[str] = []
    if strong_project_fit:
        reason.append("命中公园/商业/空间/仿真/证据链的直接项目锚点")
    if anchor_count >= 3:
        reason.append(f"跨 {anchor_count} 类项目变量")
    if "openalex" in source_tokens:
        reason.append("OpenAlex 可核验元数据")
    if row.get("doi"):
        reason.append("有 DOI")
    if abstract_len >= 300:
        reason.append("摘要信息充足")
    if weak_venue:
        reason.append("期刊/来源可信度弱，最多作为参考")
    if off_count:
        reason.append("存在偏题领域信号：" + ",".join(k for k, v in off_domain_hits.items() if v))

    if (
        year >= 2025
        and direct_theme
        and strong_project_fit
        and anchor_count >= 2
        and off_count == 0
        and not weak_venue
        and (score >= 50 or tier == "A_directly_actionable")
    ):
        curation_tier = "core_deployment"
    elif year >= 2025 and anchor_count >= 2 and not (weak_venue and off_count):
        curation_tier = "method_reference"
    else:
        curation_tier = "reject_misfit"

    return {
        "curation_tier": curation_tier,
        "anchor_count": anchor_count,
        "anchor_hits": anchor_hits,
        "off_domain_hits": off_domain_hits,
        "weak_venue": weak_venue,
        "quality_reason": "；".join(reason) if reason else "项目锚点不足",
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def to_csv_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "curation_tier": row["curation_tier"],
        "tier": row.get("tier"),
        "score": row.get("score"),
        "year": row.get("year"),
        "title": row.get("title"),
        "source": row.get("source"),
        "theme": row.get("theme"),
        "venue": row.get("venue"),
        "doi": row.get("doi"),
        "url": row.get("url"),
        "anchor_count": row.get("anchor_count"),
        "project_landing_text": "; ".join(row.get("project_landing", [])),
        "quality_reason": row.get("quality_reason"),
        "query": row.get("query"),
        "abstract_excerpt": (row.get("abstract") or "")[:500],
    }


def build_playbooks(core_rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in core_rows:
        for landing in row.get("project_landing", []) or ["未分类"]:
            grouped[landing].append(row)
    playbooks: dict[str, Any] = {}
    for landing, rows in sorted(grouped.items(), key=lambda kv: len(kv[1]), reverse=True):
        top = sorted(rows, key=lambda r: (float(r.get("score") or 0), int(r.get("year") or 0)), reverse=True)[:12]
        playbooks[landing] = {
            "core_count": len(rows),
            "what_it_controls": landing,
            "how_to_use_in_project": landing_to_operational_rule(landing),
            "top_evidence": [
                {
                    "year": row.get("year"),
                    "title": row.get("title"),
                    "source": row.get("source"),
                    "venue": row.get("venue"),
                    "url": row.get("url"),
                }
                for row in top
            ],
        }
    return playbooks


def landing_to_operational_rule(landing: str) -> str:
    mapping = {
        "空间节点与 GIS/POI/可达性": "节点候选必须同时看可达性、供给密度、竞品距离、入口关系和步行路径；不能用单一分数定案。",
        "客流、活动链与路线": "仿真先生成客群分时活动链，再把路线、停留和消费触发连接起来。",
        "Agent/LLM/仿真方法": "DeepSeek 只做 Persona 候选、活动解释、异常兜底和草案；数值和排序交给规则、ABM、MC 与证据链。",
        "公园游憩与公共空间": "商业建议必须先满足公园公共性、体验连续性和游憩场景，不能套普通商场逻辑。",
        "商业业态、价格与转化": "每个业态建议必须落到价格带、转化触发、容量、人效、库存和退出条件。",
        "天气、收入、人口、合规等现实约束": "所有预测都要分晴雨冷热、季节/节假日、客群收入、消防许可、噪声和治理边界。",
        "决策支持与报告表达": "报告必须以结论、证据、方案、敏感性和动作呈现，不把内部训练/补资料话术写给客户。",
        "CAD/GIS/数字孪生与空间转换": "DWG/PDF/CAD 进入模型前要锁定坐标、比例尺、功能区边界、出入口、面积和转换误差。",
        "人口收入与客群市场分层": "至少拆分本地居民、外区游客、流动人口，再叠加入园频次、家庭/运动/银发/通勤等任务。",
        "天气季节活动与微气候": "把天气、季节、节假日和活动日作为需求乘子，而不是写成固定日客流。",
        "合规安全治理与投诉约束": "食品、消防、夜间运营、噪声和安全容量是方案约束，不是报告末尾的风险套话。",
        "运营收益容量与试运营指标": "建议需要能被试运营验证：日收入区间、排队长度、服务能力、库存、人效和复盘阈值。",
        "AI 约束评估与人工复核": "LLM 输出必须走 JSON schema、证据引用、异常兜底、人工复核和日志追踪。",
        "数据质量证据链与可追溯": "模型输入必须保留文件、页码/图层、抽取方法、置信度和校验状态。",
        "Persona 与活动链建模": "三类客群只是底座，还要叠加入园频次、任务、同行结构、时段偏好和停留活动链。",
        "离散选择与消费/目的地选择": "目的地、活动和消费触发要表达为选择/效用逻辑，避免固定模板决定行为。",
        "ABM/Mesa 与步行仿真引擎": "Mesa 是可选实现，核心是 Agent 状态转移、路线、拥挤、热力图和校准。",
        "Monte Carlo 与敏感性分析": "P5/P50/P95 要扰动多个变量，至少包括日客流、天气、转化率、客单价、客群比例和容量。",
    }
    return mapping.get(landing, "作为参考方法，不直接写入最终结论。")


def write_integrated_architecture_blueprint(core_rows: list[dict[str, Any]]) -> None:
    direction_seed = {
        "daily_peak": "109530 人/日（2025-11-01）",
        "hourly_peak": "17 时，时均 4847 人",
        "spend_levels": "本地居民 92 元、流动人口 129 元、外区游客 231 元",
        "persona_mix": "本地居民 45%、外区游客 38%、流动人口 17%",
        "visit_frequency": "高频 35%、中频 45%、低频 20%",
        "example_layers": "LLM Agent 决策层 + Mesa ABM 轨迹层 + Monte Carlo 不确定性层（仅作为方向种子）",
    }
    source_counts = Counter(src for row in core_rows for src in str(row.get("source") or "").split("+"))
    lines = [
        "# 奥森仿真系统融合架构蓝图 2026-06-09",
        "",
        "## 定位",
        "",
        "- 老板给出的三层结构不是最终设计，而是一个方向种子：它提示我们要有 Persona、轨迹仿真和不确定性输出。",
        "- 本项目正式架构必须比三层更完整：要同时处理真实证据、CAD/PDF 空间底座、客群任务、活动链、LLM 约束、ABM 轨迹、运营容量、收益测算、Monte Carlo、校准审计和客户报告。",
        "- DeepSeek 可以进入系统，但定位是低成本语义工人：负责生成候选、解释、JSON 草案和异常兜底；不能单独决定收益、排序或最终报告结论。",
        "",
        "## 已吸收的方向种子",
        "",
    ]
    for key, value in direction_seed.items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## 正式融合架构",
            "",
            "1. 证据输入层：统一接入 PDF 表格、CAD/DWG/PDF 图纸、策划 DOCX、POI/TGI、F11 分时客流、天气/节假日和证据台账。",
            "2. 空间数字底座层：六个功能区只是最小区划，还要记录出入口、步行路径、面积、服务半径、可达性、节点边界和 CAD 转换误差。",
            "3. 客群与任务层：保留本地居民、外区游客、流动人口三类基础 Persona，同时叠加入园频次、同行结构、任务目的、价格敏感度和时段偏好。",
            "4. 活动链层：先生成到达、游览、停留、换区、补给、消费、离园等活动链，再进入轨迹或收益计算。",
            "5. 受约束 LLM 层：DeepSeek 输入 Persona 字典、场景参数和证据摘要，输出标准 JSON；所有输出必须经过 schema、证据引用、fallback 和规则校验。",
            "6. ABM 轨迹层：Mesa 可以作为实现工具，但核心是 Agent 位置序列、功能区转移、停留时间、拥挤、瓶颈和热力图。",
            "7. 运营容量层：加入服务台数、排队时间、库存、人效、面积效率、噪声/消防/夜间运营边界和试运营退出条件。",
            "8. 收益与业态层：按客群、价格带、转化率、复购/到访频次和业态组合计算收入，不用单一客单价替代全部需求。",
            "9. Monte Carlo 与敏感性层：保留 P5/P50/P95，但扰动对象应包含日客流、天气、节假日、客群比例、客单价、转化率、容量和活动日。",
            "10. 校准审计层：每次仿真必须记录输入来源、参数来源、模型版本、随机种子、异常兜底和人工复核状态。",
            "11. 报告表达层：客户版报告只写基于已有资料的判断、预测和调整；不写训练资料、内部路径、API、调试日志或让客户补材料的措辞。",
            "",
            "## 三层种子如何被融合",
            "",
            "- LLM Agent 决策层：并入第 5 层，成为受约束、可替换、可审计的语义模块，而不是总控。",
            "- Mesa ABM 轨迹层：并入第 6 层；是否使用 Mesa 取决于可维护性和数据结构，不把库名写死成架构本身。",
            "- Monte Carlo 不确定性层：并入第 9 层；不只扰动日客流，还要扰动真实世界变量。",
            "- 三类 Persona：并入第 3 层；保留基础比例，但后续必须扩展任务、频次、同行结构和时段偏好。",
            "- 六个功能区：并入第 2 层；只是最小空间分区，不限制后续新增节点、出入口、服务半径和 CAD 细分。",
            "",
            "## 知识库支撑",
            "",
            f"- 部署级核心库来源分布：{dict(source_counts)}",
            "- 核心库只把项目锚点足够强、偏题信号被排除、来源不弱的资料作为直接支撑。",
            "- 方法参考库可以启发模型结构，但不能直接作为奥森商业结论依据。",
            "",
            "## 后续编码约束",
            "",
            "- 如果先做 `config.py / llm_agent.py / park_simulation.py / monte_carlo.py / main.py` 的最小可跑版，也必须预留上述 11 层接口。",
            "- `main.py` 打印 P5/P50/P95 和热力图权重只是演示输出；正式输出还要包含证据来源、参数来源、场景差异和可执行调整建议。",
            "- 任何报告生成前，都必须从核心知识库和本地证据台账检索相关约束，不能凭空补模板。",
        ]
    )
    INTEGRATED_ARCHITECTURE_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = load_rows()
    enriched = [{**row, **quality_classify(row)} for row in rows]
    core = [row for row in enriched if row["curation_tier"] == "core_deployment"]
    method = [row for row in enriched if row["curation_tier"] == "method_reference"]
    rejected = [row for row in enriched if row["curation_tier"] == "reject_misfit"]
    core.sort(key=lambda r: (float(r.get("score") or 0), int(r.get("year") or 0), int(r.get("cited_by_count") or 0)), reverse=True)
    method.sort(key=lambda r: (float(r.get("score") or 0), int(r.get("year") or 0)), reverse=True)

    fields = [
        "curation_tier",
        "tier",
        "score",
        "year",
        "title",
        "source",
        "theme",
        "venue",
        "doi",
        "url",
        "anchor_count",
        "project_landing_text",
        "quality_reason",
        "query",
        "abstract_excerpt",
    ]
    write_jsonl(CURATED_JSONL, core)
    write_csv(CURATED_CSV, [to_csv_row(row) for row in core], fields)
    write_csv(METHOD_REFERENCE_CSV, [to_csv_row(row) for row in method[:3000]], fields)
    write_csv(REJECTED_CSV, [to_csv_row(row) for row in rejected[:3000]], fields)
    playbooks = build_playbooks(core)
    PLAYBOOK_JSON.write_text(json.dumps(playbooks, ensure_ascii=False, indent=2), encoding="utf-8")
    write_integrated_architecture_blueprint(core)

    stats = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "pass" if len(core) >= MIN_CORE_TOTAL and len(playbooks) >= MIN_CORE_THEMES and len(Counter(src for row in core for src in str(row.get("source") or "").split("+"))) >= MIN_CORE_SOURCES else "needs_action",
        "input_screened_total": len(rows),
        "core_deployment_total": len(core),
        "method_reference_total": len(method),
        "reject_misfit_total": len(rejected),
        "core_source_counts": dict(Counter(src for row in core for src in str(row.get("source") or "").split("+"))),
        "core_year_counts": dict(Counter(str(row.get("year")) for row in core)),
        "core_theme_counts": dict(Counter(theme for row in core for theme in str(row.get("theme") or "").split("+"))),
        "core_landing_counts": dict(Counter(landing for row in core for landing in row.get("project_landing", []))),
        "files": {
            "curated_jsonl": str(CURATED_JSONL.relative_to(ROOT)),
            "curated_csv": str(CURATED_CSV.relative_to(ROOT)),
            "method_reference_csv": str(METHOD_REFERENCE_CSV.relative_to(ROOT)),
            "playbooks": str(PLAYBOOK_JSON.relative_to(ROOT)),
            "quality_report": str(QUALITY_REPORT_MD.relative_to(ROOT)),
            "integrated_architecture": str(INTEGRATED_ARCHITECTURE_MD.relative_to(ROOT)),
        },
        "rules": [
            "核心库要求命中真实项目锚点；偏医疗、能源、材料、灾害等领域的资料降级或剔除。",
            "弱来源不作为部署级依据；最多进入方法参考。",
            "核心库用于架构、提示词、仿真参数和报告约束；方法参考不能直接写入客户结论。",
        ],
    }
    VERIFY_JSON.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 部署级核心知识库质量报告 2026-06-09",
        "",
        "## 结论",
        "",
        f"- 状态：{stats['status']}",
        f"- 输入筛选库：{len(rows)} 条",
        f"- 部署级核心库：{len(core)} 条",
        f"- 方法参考库：{len(method)} 条",
        f"- 剔除/暂不使用：{len(rejected)} 条",
        f"- 核心库来源：{stats['core_source_counts']}",
        "",
        "## 为什么要二次筛选",
        "",
        "- 第一轮筛选解决“量”和“近年来源”问题，但仍会把部分泛 AI、能源、医疗、灾害、政策类文章误判为高分。",
        "- 二次筛选按项目锚点、偏题信号、来源可信度、摘要完整度和可落地动作重分层。",
        "- 以后默认用部署级核心库做架构和报告约束；方法参考库只用于启发方法，不直接变成客户结论。",
        "",
        "## 核心库落点",
        "",
    ]
    for landing, count in sorted(stats["core_landing_counts"].items(), key=lambda kv: kv[1], reverse=True):
        lines.append(f"- {landing}: {count}")
    lines.extend(["", "## 核心库主题覆盖", ""])
    for theme, count in sorted(stats["core_theme_counts"].items(), key=lambda kv: kv[1], reverse=True):
        lines.append(f"- {theme}: {count}")
    lines.extend(["", "## 下一步使用方式", ""])
    lines.extend(
        [
            "- 用 `30_extraction/scripts/query_recent_knowledge_base_20260609.py` 按主题调用核心库。",
            "- 用 `knowledge_theme_playbooks_20260609.json` 把知识映射到项目动作。",
            "- 用 `integrated_simulation_architecture_blueprint_20260609.md` 把老板方向种子、近年知识库和现有项目捏合成正式仿真架构。",
        ]
    )
    QUALITY_REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
