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
CORE_JSONL = KB_DIR / "curated_core_knowledge_base_20260609.jsonl"
CLASSIC_JSONL = KB_DIR / "classic_model_reference_20260609.jsonl"

PACK_JSONL = KB_DIR / "model_computation_knowledge_pack_20260609.jsonl"
PACK_CSV = KB_DIR / "model_computation_knowledge_pack_20260609.csv"
PLAYBOOK_MD = KB_DIR / "model_computation_stack_playbook_20260609.md"
VERIFY_JSON = QUALITY_DIR / "model_computation_knowledge_pack_verification_20260609.json"

MIN_PACK_TOTAL = 2200
MIN_LAYER_COUNT = 12


MODEL_LAYERS = {
    "evidence_data_foundation": {
        "patterns": [
            r"evidence|provenance|lineage|data quality|validation|audit|schema|source attribution",
            r"PDF|table extraction|CAD|DWG|GIS|geospatial data",
        ],
        "controls": "证据输入、字段来源、数据体检、单位一致性和客户结论的可追溯边界。",
    },
    "spatial_geometry_accessibility": {
        "patterns": [
            r"GIS|geospatial|accessibility|catchment|network|walkability|route choice|service radius|location allocation",
            r"CAD|DWG|BIM|geometry|building footprint|digital twin",
        ],
        "controls": "CAD/PDF/GIS 转换、六区细分、路网可达性、入口关系和服务半径。",
    },
    "synthetic_population_persona": {
        "patterns": [
            r"synthetic population|persona|demographic|income|visitor typology|population segmentation",
            r"willingness to pay|frequency segmentation|resident|tourist|family|older adults",
        ],
        "controls": "本地居民/外区游客/流动人口之外的频次、同行结构、收入、任务和价格敏感度。",
    },
    "activity_chain_time_geography": {
        "patterns": [
            r"activity chain|activity-based|activity based|time geography|itinerary|origin destination",
            r"route sequence|dwell time|activity transition|peak hour",
        ],
        "controls": "到达、游览、停留、换区、补给、消费、离园的时间空间链路。",
    },
    "discrete_choice_spatial_interaction": {
        "patterns": [
            r"discrete choice|multinomial logit|nested logit|mixed logit|destination choice|utility",
            r"Huff|gravity model|spatial interaction|market share|choice model",
        ],
        "controls": "destination/activity/spend 的选择概率和吸引力逻辑，防止 LLM 自由编结果。",
    },
    "abm_pedestrian_crowd_engine": {
        "patterns": [
            r"agent-based|agent based|multi-agent|ABM|Mesa|pedestrian simulation|crowd simulation|social force|cellular automata",
            r"trajectory|heatmap|crowd density|bottleneck|microsimulation",
        ],
        "controls": "Agent 状态转移、位置序列、功能区转移、拥挤瓶颈和热力图。",
    },
    "queue_capacity_discrete_event": {
        "patterns": [
            r"queue|queueing|discrete event|SimPy|service capacity|service time|wait time|inventory|staffing",
            r"bottleneck|trial operation|throughput|capacity planning",
        ],
        "controls": "咖啡亭、餐饮、入口服务、库存、人效和高峰服务压力。",
    },
    "revenue_conversion_unit_economics": {
        "patterns": [
            r"revenue|spending|conversion|pricing|price sensitivity|unit economics|food beverage|retail operations",
            r"customer spend|willingness to pay|profit|demand forecasting",
        ],
        "controls": "客单价、转化率、价格带、复购频次、业态组合和收益区间。",
    },
    "monte_carlo_uncertainty": {
        "patterns": [
            r"Monte Carlo|uncertainty quantification|stochastic simulation|probabilistic|confidence interval|risk band",
            r"P5|P50|P95|Latin hypercube|random seed",
        ],
        "controls": "日客流、天气、客群比例、客单价、转化率、容量和活动日的置信水位。",
    },
    "sensitivity_calibration_validation": {
        "patterns": [
            r"sensitivity analysis|Sobol|Morris|SALib|calibration|Bayesian calibration|validation|verification",
            r"model validation|parameter calibration|scenario comparison|robustness",
        ],
        "controls": "参数影响排序、模型校准、可复跑验证、异常兜底和复核状态。",
    },
    "optimization_scenario_decision": {
        "patterns": [
            r"optimization|scenario optimization|decision support|multi criteria|MCDM|robust optimization|simulation optimization",
            r"site selection|portfolio|priority ranking|trade-off",
        ],
        "controls": "候选节点组合、优先级、约束条件、试运营动作和方案比较。",
    },
    "real_world_modulators": {
        "patterns": [
            r"weather|seasonality|holiday|event|microclimate|temperature|rain|income|demographic|population",
            r"noise|complaint|license|fire|safety|regulation|governance",
        ],
        "controls": "天气、季节、节假日、活动日、收入、人口、合规、投诉和真实运营边界。",
    },
    "llm_agent_guardrails": {
        "patterns": [
            r"LLM|large language model|agent|structured output|JSON schema|guardrail|evaluation|observability",
            r"human review|auditability|fallback|tool calling|AI agent",
        ],
        "controls": "DeepSeek 的薄封装、JSON 输出、规则校验、人工复核和日志追踪。",
    },
}


OFF_DOMAIN_RE = re.compile(
    r"clinical|patient|cancer|genomic|drug|molecular|semiconductor|quantum|microgrid|wind farm|solar power|battery chemistry|"
    r"hemoglobin|preterm|infant|pediatric|paediatric|disease|hospital|healthcare|medical|surgery|nursing|cardio|diabetes|"
    r"protein|enzyme|pharmaceutical|wireless sensor only|crop disease|livestock",
    re.IGNORECASE,
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def row_text(row: dict[str, Any]) -> str:
    return " ".join(
        str(part or "")
        for part in [
            row.get("title"),
            row.get("abstract"),
            row.get("theme"),
            row.get("venue"),
            row.get("quality_reason"),
            row.get("project_use"),
            " ".join(row.get("project_landing", []) or []),
        ]
    )


def layer_hits(row: dict[str, Any]) -> list[str]:
    text = row_text(row)
    hits = []
    for layer, spec in MODEL_LAYERS.items():
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in spec["patterns"]):
            hits.append(layer)
    return hits


def score_for_layer(row: dict[str, Any], layer: str, source_tier: str) -> float:
    text = row_text(row)
    spec = MODEL_LAYERS[layer]
    pattern_hits = sum(1 for pattern in spec["patterns"] if re.search(pattern, text, re.IGNORECASE))
    year = int(row.get("year") or 0)
    cited = int(row.get("cited_by_count") or 0)
    base_score = float(row.get("score") or row.get("model_reference_score") or 0)
    source_bonus = {"core": 20, "screened": 8, "classic": 14}.get(source_tier, 0)
    year_bonus = 18 if year >= 2026 else 12 if year >= 2025 else 5 if year else 0
    citation_bonus = min(18, cited // 100)
    doi_bonus = 5 if row.get("doi") else 0
    return pattern_hits * 16 + source_bonus + year_bonus + citation_bonus + doi_bonus + base_score / 8


def normalize_row(row: dict[str, Any], layer: str, source_tier: str) -> dict[str, Any]:
    project_landing = row.get("project_landing")
    if isinstance(project_landing, list):
        landing_text = "; ".join(str(item) for item in project_landing)
    else:
        landing_text = str(project_landing or row.get("project_use") or "")
    normalized = {
        "model_layer": layer,
        "layer_controls": MODEL_LAYERS[layer]["controls"],
        "source_tier": source_tier,
        "year": row.get("year"),
        "title": row.get("title"),
        "source": row.get("source"),
        "venue": row.get("venue"),
        "doi": row.get("doi"),
        "url": row.get("url"),
        "cited_by_count": row.get("cited_by_count"),
        "theme": row.get("theme"),
        "project_landing_text": landing_text,
        "quality_reason": row.get("quality_reason"),
        "query": row.get("query"),
        "abstract_excerpt": (row.get("abstract") or "")[:700],
    }
    normalized["model_pack_score"] = round(score_for_layer(row, layer, source_tier), 3)
    return normalized


def build_pack() -> list[dict[str, Any]]:
    core = read_jsonl(CORE_JSONL)
    screened = read_jsonl(SCREENED_JSONL)
    classic = read_jsonl(CLASSIC_JSONL)
    core_keys = {record_key(row) for row in core}
    candidates: list[dict[str, Any]] = []

    for source_tier, rows in [("core", core), ("screened", screened), ("classic", classic)]:
        for row in rows:
            text = row_text(row)
            if source_tier != "classic" and OFF_DOMAIN_RE.search(text):
                continue
            key = record_key(row)
            if source_tier == "screened" and key in core_keys:
                continue
            for layer in layer_hits(row):
                normalized = normalize_row(row, layer, source_tier)
                if normalized["model_pack_score"] >= (35 if source_tier != "classic" else 30):
                    candidates.append(normalized)

    by_layer_key: dict[tuple[str, str], dict[str, Any]] = {}
    for row in candidates:
        key = (row["model_layer"], record_key(row))
        current = by_layer_key.get(key)
        if current is None or float(row["model_pack_score"]) > float(current["model_pack_score"]):
            by_layer_key[key] = row

    rows = list(by_layer_key.values())
    rows.sort(key=lambda item: (item["model_layer"], float(item["model_pack_score"]), int(item.get("year") or 0)), reverse=True)

    capped: list[dict[str, Any]] = []
    per_layer: defaultdict[str, int] = defaultdict(int)
    for row in rows:
        limit = 420 if row["model_layer"] in {"spatial_geometry_accessibility", "real_world_modulators", "llm_agent_guardrails"} else 320
        if per_layer[row["model_layer"]] >= limit:
            continue
        capped.append(row)
        per_layer[row["model_layer"]] += 1
    capped.sort(key=lambda item: (float(item["model_pack_score"]), int(item.get("year") or 0)), reverse=True)
    return capped


def record_key(row: dict[str, Any]) -> str:
    doi = str(row.get("doi") or "").lower().strip()
    if doi:
        return doi
    title = re.sub(r"\W+", " ", str(row.get("title") or "").lower()).strip()
    return title[:180]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "model_layer",
        "model_pack_score",
        "source_tier",
        "year",
        "title",
        "source",
        "venue",
        "doi",
        "url",
        "cited_by_count",
        "layer_controls",
        "project_landing_text",
        "quality_reason",
        "query",
        "abstract_excerpt",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_playbook(rows: list[dict[str, Any]], stats: dict[str, Any]) -> None:
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["model_layer"]].append(row)

    lines = [
        "# 计算与模型知识包 2026-06-09",
        "",
        "## 定位",
        "",
        "- 这个文件是每次修改仿真、DeepSeek 约束、收益预测、节点解释和报告生成前的计算模型入口。",
        "- 它不是论文堆积表，而是把近年核心库、方法参考库和经典理论按项目可用的模型层重新组织。",
        "- 老板三层示例只保留为方向种子：Persona、ABM、Monte Carlo 都被放进更大的计算栈里。",
        "",
        "## 当前规模",
        "",
        f"- 模型知识包：{stats['pack_total']} 条",
        f"- 覆盖模型层：{stats['layer_count']} 类",
        f"- 年份分布：{stats['year_counts']}",
        f"- 来源层级：{stats['source_tier_counts']}",
        "",
        "## 正式计算栈",
        "",
    ]
    stack_lines = [
        ("evidence_data_foundation", "先锁定 PDF/CAD/客流/消费/POI 的证据与单位，禁止无来源参数进入计算。"),
        ("spatial_geometry_accessibility", "把 CAD/PDF/GIS 转成可量测空间底座，记录功能区、入口、路网、面积和误差。"),
        ("synthetic_population_persona", "把三类客群扩成微观 Persona：收入、频次、同行结构、任务、时段、价格敏感度。"),
        ("activity_chain_time_geography", "生成到达、游览、停留、补给、消费、离园活动链，避免单点静态判断。"),
        ("discrete_choice_spatial_interaction", "用选择/吸引力逻辑约束目的地和消费触发，LLM 只解释候选。"),
        ("abm_pedestrian_crowd_engine", "把 Persona 活动链放进 ABM/步行层，输出轨迹、拥挤、瓶颈和热力。"),
        ("queue_capacity_discrete_event", "对餐饮、咖啡亭、入口服务点做排队和服务容量仿真。"),
        ("revenue_conversion_unit_economics", "用客单价、转化率、复购/频次、容量和业态组合计算收益，不用单一均值替代。"),
        ("monte_carlo_uncertainty", "对关键变量做随机扰动，输出 P5/P50/P95 和场景区间。"),
        ("sensitivity_calibration_validation", "用敏感性分析找关键参数，并记录校准、验证、随机种子和复核状态。"),
        ("optimization_scenario_decision", "把多个候选节点/业态组合转成方案优先级、前置条件和试运营动作。"),
        ("real_world_modulators", "把天气、节假日、活动日、收入、人口、合规、噪声和投诉作为真实世界乘子。"),
        ("llm_agent_guardrails", "DeepSeek 只负责候选和结构化草案，所有输出必须过 schema、规则、证据和人工复核。"),
    ]
    for index, (layer, rule) in enumerate(stack_lines, start=1):
        lines.append(f"{index}. **{layer}**：{rule}")
    lines.extend(["", "## 分层证据入口", ""])
    for layer, layer_rows in sorted(grouped.items(), key=lambda kv: len(kv[1]), reverse=True):
        top = sorted(layer_rows, key=lambda r: float(r["model_pack_score"]), reverse=True)[:8]
        lines.extend(
            [
                f"### {layer}",
                "",
                f"- 数量：{len(layer_rows)}",
                f"- 控制问题：{MODEL_LAYERS[layer]['controls']}",
                "- 调用方式：",
                f"  `py -3.12 30_extraction\\scripts\\query_model_computation_knowledge_20260609.py --layer {layer} --query \"奥森 仿真 收益\" --limit 8`",
                "- 代表资料：",
            ]
        )
        for row in top:
            title = str(row.get("title") or "").replace("\n", " ")[:150]
            lines.append(f"  - {row.get('year')} | {row.get('source_tier')} | {title}")
        lines.append("")
    lines.extend(
        [
            "## 使用红线",
            "",
            "- 客户报告不能写“请补资料/训练资料/内部 API/路径/调试”。",
            "- 经典理论只约束模型边界，不直接变成奥森结论。",
            "- 近年论文只提供方法和变量启发，真实结论必须回到本地数据、证据台账和可复跑计算。",
            "- 如果模型包查询不到支撑，不允许凭感觉新增计算逻辑；先扩查询矩阵或查官方/论文来源。",
        ]
    )
    PLAYBOOK_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_pack()
    write_jsonl(PACK_JSONL, rows)
    write_csv(PACK_CSV, rows)
    stats = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "pass" if len(rows) >= MIN_PACK_TOTAL and len(Counter(row["model_layer"] for row in rows)) >= MIN_LAYER_COUNT else "needs_action",
        "pack_total": len(rows),
        "layer_count": len(Counter(row["model_layer"] for row in rows)),
        "layer_counts": dict(Counter(row["model_layer"] for row in rows)),
        "source_tier_counts": dict(Counter(row["source_tier"] for row in rows)),
        "source_counts": dict(Counter(str(row.get("source") or "") for row in rows)),
        "year_counts": dict(Counter(str(row.get("year")) for row in rows)),
        "files": {
            "pack_jsonl": str(PACK_JSONL.relative_to(ROOT)),
            "pack_csv": str(PACK_CSV.relative_to(ROOT)),
            "playbook": str(PLAYBOOK_MD.relative_to(ROOT)),
        },
        "rules": [
            "模型知识包用于仿真/计算/DeepSeek 约束的可调用入口，不等于客户报告证据。",
            "所有客户结论仍必须落回本地数据、证据台账和可复跑计算。",
            "老板三层示例被吸收进更大的计算栈，不作为架构上限。",
        ],
    }
    VERIFY_JSON.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    write_playbook(rows, stats)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
