from __future__ import annotations

import argparse
import asyncio
import csv
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import httpx


ROOT = Path(__file__).resolve().parents[2]
BASE_SCRIPT = ROOT / "30_extraction" / "scripts" / "build_recent_knowledge_base_20260609.py"
KB_DIR = ROOT / "10_research" / "recent_knowledge_base_20260609"
QUALITY_DIR = ROOT / "40_quality_evidence"

QUERY_MATRIX = KB_DIR / "simulation_stack_mega_query_matrix_20260609.json"
RAW_JSONL = KB_DIR / "raw_simulation_stack_mega_20260609.jsonl"
SCREENED_JSONL = KB_DIR / "screened_simulation_stack_mega_20260609.jsonl"
CLASSIC_JSONL = KB_DIR / "classic_theory_reference_mega_20260609.jsonl"
OFFICIAL_JSON = KB_DIR / "official_simulation_tool_sources_20260609.json"
VERIFY_JSON = QUALITY_DIR / "simulation_stack_mega_supplement_verification_20260609.json"

OPENALEX_PER_PAGE = 20
CROSSREF_ROWS = 20
CONCURRENCY = 10
TARGET_RECENT_QUERY_COUNT = 3000
BLOCK_QUERY_LIMIT = 360


OFFICIAL_SOURCES = [
    {
        "name": "Mesa",
        "url": "https://mesa.readthedocs.io/en/stable/",
        "project_use": "ABM 轨迹层候选实现；用于 Agent 状态、空间、数据收集和可视化。",
        "source_type": "official_documentation",
    },
    {
        "name": "SimPy",
        "url": "https://simpy.readthedocs.io/",
        "project_use": "离散事件和队列容量层候选实现；用于咖啡亭、餐饮、入口服务压力。",
        "source_type": "official_documentation",
    },
    {
        "name": "SALib",
        "url": "https://salib.readthedocs.io/",
        "project_use": "敏感性分析候选工具；用于 Monte Carlo 后的参数影响排序。",
        "source_type": "official_documentation",
    },
    {
        "name": "OpenAlex Works API",
        "url": "https://docs.openalex.org/api-entities/works",
        "project_use": "近年论文知识库抓取来源；用于批量检索和去重前的元数据输入。",
        "source_type": "official_documentation",
    },
]


BLOCK_SPECS: dict[str, dict[str, list[str]]] = {
    "persona_synthetic_population": {
        "methods": [
            "synthetic population",
            "persona based agent simulation",
            "heterogeneous agent population",
            "visitor typology",
            "resident tourist worker persona",
            "LLM persona simulation",
            "generative agents persona",
            "agent profile synthesis",
            "socioeconomic segmentation",
            "activity demand synthesis",
        ],
        "contexts": [
            "urban park",
            "public space",
            "tourism attraction",
            "commercial street",
            "retail service",
            "food beverage kiosk",
            "sports wellness park",
            "family recreation",
            "older adults park",
            "transit adjacent park",
            "visitor flow",
            "leisure consumption",
        ],
        "outcomes": [
            "demand forecasting",
            "activity choice",
            "spending behavior",
            "dwell time",
            "route choice",
            "willingness to pay",
            "frequency segmentation",
            "scenario simulation",
        ],
    },
    "activity_chain_time_geography": {
        "methods": [
            "activity chain model",
            "activity based travel demand",
            "time geography",
            "itinerary simulation",
            "tour sequence model",
            "dwell time model",
            "spatio temporal behavior",
            "daily activity schedule",
            "multi purpose trip",
            "activity destination choice",
        ],
        "contexts": [
            "park visitor",
            "urban recreation",
            "tourist itinerary",
            "retail visitor",
            "commercial complex",
            "pedestrian public space",
            "festival visitor",
            "family outing",
            "fitness route",
            "lake park",
            "entrance plaza",
            "service facility",
        ],
        "outcomes": [
            "visitor flow",
            "consumption trigger",
            "dwell time",
            "origin destination",
            "route sequence",
            "peak hour demand",
            "activity transition",
            "simulation calibration",
        ],
    },
    "abm_pedestrian_crowd_engine": {
        "methods": [
            "agent based model",
            "multi agent simulation",
            "Mesa agent based modeling",
            "pedestrian microsimulation",
            "social force model",
            "cellular automata pedestrian",
            "crowd simulation",
            "digital twin agent based",
            "route choice agent model",
            "public space simulation",
        ],
        "contexts": [
            "urban park visitor",
            "commercial street pedestrian",
            "public plaza",
            "entrance gate",
            "lake trail",
            "food service area",
            "tourism attraction",
            "metro station connection",
            "sports event crowd",
            "family recreation crowd",
            "older adults walking",
            "night economy public space",
        ],
        "outcomes": [
            "trajectory heatmap",
            "crowd density",
            "bottleneck",
            "route choice",
            "safety risk",
            "service accessibility",
            "visitor flow",
            "calibration validation",
        ],
    },
    "discrete_choice_spatial_interaction": {
        "methods": [
            "discrete choice model",
            "multinomial logit",
            "nested logit",
            "mixed logit",
            "random utility model",
            "Huff model",
            "gravity model",
            "spatial interaction model",
            "destination choice",
            "store choice model",
        ],
        "contexts": [
            "park recreation demand",
            "visitor destination",
            "retail location",
            "food beverage choice",
            "tourism attraction",
            "public space services",
            "commercial facility",
            "leisure consumption",
            "urban green space",
            "walkable retail",
            "POI visit",
            "willingness to pay",
        ],
        "outcomes": [
            "choice probability",
            "spending",
            "destination selection",
            "site selection",
            "price sensitivity",
            "attraction utility",
            "scenario comparison",
            "market share",
        ],
    },
    "queue_capacity_discrete_event": {
        "methods": [
            "queue simulation",
            "discrete event simulation",
            "SimPy resource capacity",
            "service time model",
            "capacity planning",
            "throughput optimization",
            "waiting time model",
            "staffing simulation",
            "inventory service simulation",
            "operational digital twin",
        ],
        "contexts": [
            "coffee kiosk",
            "food beverage service",
            "retail checkout",
            "park entrance",
            "visitor attraction",
            "public service facility",
            "festival booth",
            "sports event service",
            "commercial service area",
            "peak hour queue",
            "small retail operations",
            "mobile food cart",
        ],
        "outcomes": [
            "wait time",
            "queue length",
            "service capacity",
            "revenue loss",
            "staffing",
            "inventory",
            "bottleneck",
            "trial operation metrics",
        ],
    },
    "monte_carlo_uncertainty_sensitivity": {
        "methods": [
            "Monte Carlo simulation",
            "uncertainty quantification",
            "stochastic simulation",
            "probabilistic forecast",
            "Bayesian calibration",
            "Latin hypercube sampling",
            "global sensitivity analysis",
            "SALib sensitivity analysis",
            "scenario analysis",
            "P5 P50 P95 forecast",
        ],
        "contexts": [
            "visitor flow",
            "retail demand",
            "park revenue",
            "food beverage conversion",
            "commercial site selection",
            "weather demand",
            "holiday event",
            "capacity constrained service",
            "customer segment mix",
            "pilot coffee kiosk",
            "full scenario optimization",
            "baseline scenario",
        ],
        "outcomes": [
            "revenue interval",
            "risk band",
            "sensitivity ranking",
            "scenario comparison",
            "decision support",
            "confidence interval",
            "robustness",
            "model validation",
        ],
    },
    "calibration_validation_evidence": {
        "methods": [
            "model calibration",
            "simulation validation",
            "Bayesian calibration",
            "data assimilation",
            "cross validation",
            "sensitivity analysis",
            "evidence traceability",
            "execution provenance",
            "auditability",
            "human in the loop validation",
        ],
        "contexts": [
            "agent based model",
            "pedestrian simulation",
            "visitor behavior",
            "activity based demand",
            "queue simulation",
            "Monte Carlo forecast",
            "LLM agent simulation",
            "RAG report generation",
            "urban mobility",
            "park commercial decision",
            "digital twin",
            "customer report",
        ],
        "outcomes": [
            "parameter calibration",
            "validation evidence",
            "uncertainty communication",
            "schema validation",
            "risk control",
            "reproducibility",
            "source attribution",
            "decision confidence",
        ],
    },
    "cad_gis_spatial_data_foundation": {
        "methods": [
            "CAD GIS conversion",
            "DWG DXF geospatial",
            "BIM GIS integration",
            "building footprint extraction",
            "3D city model",
            "digital twin spatial data",
            "geospatial data quality",
            "spatial accessibility",
            "network analysis",
            "walkability analysis",
        ],
        "contexts": [
            "urban park",
            "public space facility",
            "commercial node",
            "entrance gate",
            "pedestrian route",
            "service radius",
            "retail location",
            "tourism attraction",
            "lake area",
            "trail network",
            "plaza",
            "food service area",
        ],
        "outcomes": [
            "site selection",
            "area measurement",
            "route distance",
            "accessibility",
            "geometry uncertainty",
            "spatial decision support",
            "heatmap",
            "node comparison",
        ],
    },
    "real_world_modulators": {
        "methods": [
            "weather demand model",
            "seasonality demand forecasting",
            "microclimate comfort",
            "event crowd forecasting",
            "income segmentation",
            "population demographics",
            "holiday effect",
            "night economy governance",
            "noise complaint risk",
            "fire safety regulation",
        ],
        "contexts": [
            "park visitor",
            "retail foot traffic",
            "outdoor food beverage",
            "urban recreation",
            "tourism attraction",
            "commercial service",
            "public space",
            "family visitor",
            "older adults",
            "sports users",
            "local residents",
            "outside tourists",
        ],
        "outcomes": [
            "conversion rate",
            "visitor flow",
            "spending behavior",
            "service capacity",
            "risk boundary",
            "scenario modifier",
            "demand uncertainty",
            "pilot operation",
        ],
    },
}

CLASSIC_QUERIES = [
    "Huff model retail location classic",
    "gravity model spatial interaction retail classic",
    "random utility model McFadden discrete choice",
    "multinomial logit model discrete choice classic",
    "nested logit destination choice classic",
    "mixed logit choice model Train classic",
    "activity based travel demand Bowman Ben Akiva",
    "time geography Hagerstrand activity space",
    "agent based modeling Epstein Axtell Sugarscape",
    "agent based computational economics Tesfatsion classic",
    "social force model Helbing pedestrian dynamics",
    "cellular automata pedestrian dynamics floor field model",
    "discrete event simulation Law Kelton validation",
    "queueing theory service capacity operations classic",
    "Monte Carlo simulation uncertainty analysis classic",
    "global sensitivity analysis Saltelli classic",
    "Bayesian calibration computer models Kennedy O'Hagan",
    "Latin hypercube sampling McKay classic",
    "space syntax pedestrian movement retail location",
    "central place theory retail location classic",
    "location allocation model facility location classic",
    "microsimulation travel demand classic",
    "simulation modeling validation Sargent classic",
    "uncertainty quantification simulation model validation classic",
]


def load_base_module() -> Any:
    spec = importlib.util.spec_from_file_location("kb_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["kb_base_mega"] = module
    spec.loader.exec_module(module)
    return module


def normalize_query(query: str) -> str:
    return re.sub(r"\s+", " ", query.strip())


def build_queries() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for block, spec in BLOCK_SPECS.items():
        for method in spec["methods"]:
            for context in spec["contexts"]:
                for outcome in spec["outcomes"]:
                    variants = [
                        f"{method} {context} {outcome}",
                        f"{context} {method} {outcome}",
                    ]
                    for query in variants:
                        query = normalize_query(query)
                        key = query.lower()
                        if key not in seen:
                            seen.add(key)
                            rows.append({"block": block, "query": query, "reference_class": "recent_priority"})
                    if len([row for row in rows if row["block"] == block]) >= BLOCK_QUERY_LIMIT:
                        break
                if len([row for row in rows if row["block"] == block]) >= BLOCK_QUERY_LIMIT:
                    break
            if len([row for row in rows if row["block"] == block]) >= BLOCK_QUERY_LIMIT:
                break
    for query in CLASSIC_QUERIES:
        rows.append({"block": "classic_theory_reference", "query": query, "reference_class": "classic_theory"})
    if sum(1 for row in rows if row["reference_class"] == "recent_priority") < TARGET_RECENT_QUERY_COUNT:
        raise RuntimeError("recent query matrix below target")
    return rows


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


async def fetch_openalex(client: httpx.AsyncClient, query_info: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    query = query_info["query"]
    is_classic = query_info["reference_class"] == "classic_theory"
    filter_value = "type:article" if is_classic else "from_publication_date:2025-01-01,type:article"
    params = {
        "search": query,
        "filter": filter_value,
        "per-page": OPENALEX_PER_PAGE,
        "select": "id,doi,title,display_name,publication_year,publication_date,cited_by_count,abstract_inverted_index,authorships,primary_location,locations,concepts,keywords,open_access,type,type_crossref",
    }
    errors: list[dict[str, str]] = []
    try:
        response = await client.get("https://api.openalex.org/works", params=params)
        response.raise_for_status()
        rows = response.json().get("results", [])
        for row in rows:
            row["_source"] = "openalex"
            row["_theme"] = f"simulation_stack_mega:{query_info['block']}"
            row["_query"] = query
            row["_reference_class"] = query_info["reference_class"]
            row["_query_block"] = query_info["block"]
        return rows, errors
    except Exception as exc:
        errors.append({"source": "openalex", "query": query, "block": query_info["block"], "error": repr(exc)})
        return [], errors


async def fetch_crossref(client: httpx.AsyncClient, query_info: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    query = query_info["query"]
    is_classic = query_info["reference_class"] == "classic_theory"
    params = {
        "query.bibliographic": query,
        "filter": "type:journal-article" if is_classic else "from-pub-date:2025-01-01,type:journal-article",
        "rows": CROSSREF_ROWS,
        "select": "DOI,title,published-print,published-online,published,container-title,is-referenced-by-count,subject,abstract,URL,type",
    }
    errors: list[dict[str, str]] = []
    try:
        response = await client.get("https://api.crossref.org/works", params=params)
        response.raise_for_status()
        rows = response.json().get("message", {}).get("items", [])
        for row in rows:
            row["_source"] = "crossref"
            row["_theme"] = f"simulation_stack_mega:{query_info['block']}"
            row["_query"] = query
            row["_reference_class"] = query_info["reference_class"]
            row["_query_block"] = query_info["block"]
        return rows, errors
    except Exception as exc:
        errors.append({"source": "crossref", "query": query, "block": query_info["block"], "error": repr(exc)})
        return [], errors


async def fetch_all(query_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    headers = {"User-Agent": "park-commercial-site-selection-simulation/1.0 (mailto:local@example.invalid)"}
    semaphore = asyncio.Semaphore(CONCURRENCY)
    raw_rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    async with httpx.AsyncClient(headers=headers, timeout=35, follow_redirects=True) as client:
        async def run_one(index: int, query_info: dict[str, str]) -> None:
            async with semaphore:
                if index % 50 == 0:
                    print(f"[{index}/{len(query_rows)}] {query_info['block']} / {query_info['query']}")
                openalex_rows, openalex_errors = await fetch_openalex(client, query_info)
                crossref_rows, crossref_errors = await fetch_crossref(client, query_info)
                raw_rows.extend(openalex_rows)
                raw_rows.extend(crossref_rows)
                errors.extend(openalex_errors)
                errors.extend(crossref_errors)

        await asyncio.gather(*(run_one(index, row) for index, row in enumerate(query_rows, start=1)))
    return raw_rows, errors


def record_key(base: Any, row: dict[str, Any]) -> str:
    return base.record_key(row)


def merge_records(base: Any, existing: list[dict[str, Any]], supplement: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for row in existing + supplement:
        rescored = {**row, **base.score_record(row)}
        key = record_key(base, rescored)
        if key not in by_key:
            by_key[key] = rescored
            continue
        old = by_key[key]
        old["source"] = "+".join(sorted(set(str(old.get("source") or "").split("+")) | set(str(rescored.get("source") or "").split("+"))))
        old["theme"] = "+".join(sorted(set(str(old.get("theme") or "").split("+")) | set(str(rescored.get("theme") or "").split("+"))))
        if rescored.get("query") and str(rescored["query"]) not in str(old.get("query") or ""):
            old["query"] = f"{old.get('query', '')} || {rescored['query']}".strip(" |")
        if float(rescored.get("score") or 0) > float(old.get("score") or 0):
            for field in ["score", "tier", "category_hits", "category_count", "project_landing", "rejection_reason", "abstract", "venue", "cited_by_count"]:
                if field in rescored:
                    old[field] = rescored[field]
    merged = [row for row in by_key.values() if row.get("tier") != "reject_low_relevance"]
    merged.sort(key=lambda r: (float(r.get("score") or 0), int(r.get("year") or 0), int(r.get("cited_by_count") or 0)), reverse=True)
    return merged


def stats_for(rows: list[dict[str, Any]], rejected_total: int) -> dict[str, Any]:
    return {
        "dedup_total": len(rows) + rejected_total,
        "screened_total": len(rows),
        "rejected_total": rejected_total,
        "tier_counts": dict(Counter(row["tier"] for row in rows)),
        "year_counts": dict(Counter(str(row.get("year")) for row in rows)),
        "theme_counts": dict(Counter(theme for row in rows for theme in str(row.get("theme") or "").split("+"))),
        "category_counts": dict(Counter(cat for row in rows for cat, hit in row.get("category_hits", {}).items() if hit)),
        "source_counts": dict(Counter(src for row in rows for src in str(row.get("source") or "").split("+"))),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["reference_class", "block", "query"]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def flatten_classic(base: Any, raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for item in raw_rows:
        if item.get("_reference_class") != "classic_theory":
            continue
        record = base.flatten_record(item)
        if not record.get("title"):
            continue
        record["reference_class"] = "classic_theory"
        record["curation_tier"] = "theory_reference"
        record["quality_reason"] = "经典理论参考；用于方法框架，不直接作为奥森客户结论。"
        records.append(record)
    by_key = {}
    for record in records:
        by_key.setdefault(base.record_key(record), record)
    return list(by_key.values())


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="构建 1000+ 查询级仿真栈 Mega 知识补充")
    parser.add_argument("--reuse-existing", action="store_true")
    args = parser.parse_args()

    base = load_base_module()
    query_rows = build_queries()
    QUERY_MATRIX.write_text(json.dumps({"query_count": len(query_rows), "queries": query_rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(KB_DIR / "simulation_stack_mega_query_matrix_20260609.csv", query_rows)
    OFFICIAL_JSON.write_text(json.dumps(OFFICIAL_SOURCES, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.reuse_existing and RAW_JSONL.exists() and SCREENED_JSONL.exists():
        raw_rows = read_jsonl(RAW_JSONL)
        screened = read_jsonl(SCREENED_JSONL)
        rejected: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []
        supplement_stats = base.screen(raw_rows)[2]
    else:
        raw_rows, errors = asyncio.run(fetch_all(query_rows))
        write_jsonl(RAW_JSONL, raw_rows)
        screened, rejected, supplement_stats = base.screen([row for row in raw_rows if row.get("_reference_class") != "classic_theory"])
        write_jsonl(SCREENED_JSONL, screened)

    classics = flatten_classic(base, raw_rows)
    write_jsonl(CLASSIC_JSONL, classics)

    old_verify = json.loads(base.VERIFY_JSON.read_text(encoding="utf-8")) if base.VERIFY_JSON.exists() else {}
    existing = read_jsonl(base.SCREENED_JSONL)
    merged = merge_records(base, existing, screened)
    old_rejected = int((old_verify.get("screening_stats") or {}).get("rejected_total") or 0)
    stats = stats_for(merged, old_rejected + len(rejected))
    raw_counts = dict(old_verify.get("raw_counts") or {})
    source_counts = Counter(row.get("_source") for row in raw_rows)
    for source in ["openalex", "crossref", "semantic_scholar", "arxiv"]:
        raw_counts[source] = int(raw_counts.get(source) or 0) + int(source_counts.get(source) or 0)
    raw_counts["total"] = sum(raw_counts.get(source, 0) for source in ["openalex", "crossref", "semantic_scholar", "arxiv"])
    meta = {
        "raw_counts": raw_counts,
        "errors": list((old_verify.get("errors") or [])[:100]) + errors[:100],
        "query_count": int(old_verify.get("query_count") or 0) + len(query_rows),
    }
    base.write_outputs(merged, rejected, stats, meta)
    verify = {
        "status": "pass" if len(query_rows) >= TARGET_RECENT_QUERY_COUNT and len(screened) >= 6000 and stats["screened_total"] >= 22000 else "needs_action",
        "query_count": len(query_rows),
        "recent_query_count": sum(1 for row in query_rows if row["reference_class"] == "recent_priority"),
        "classic_query_count": sum(1 for row in query_rows if row["reference_class"] == "classic_theory"),
        "blocks": dict(Counter(row["block"] for row in query_rows)),
        "raw_total": len(raw_rows),
        "screened_total": len(screened),
        "classic_reference_total": len(classics),
        "merged_screened_total": stats["screened_total"],
        "merged_category_counts": stats["category_counts"],
        "merged_theme_counts": stats["theme_counts"],
        "source_counts": dict(source_counts),
        "official_sources": OFFICIAL_SOURCES,
        "files": {
            "query_matrix": str(QUERY_MATRIX.relative_to(ROOT)),
            "raw": str(RAW_JSONL.relative_to(ROOT)),
            "screened": str(SCREENED_JSONL.relative_to(ROOT)),
            "classic": str(CLASSIC_JSONL.relative_to(ROOT)),
            "official_sources": str(OFFICIAL_JSON.relative_to(ROOT)),
            "merged_screened": str(base.SCREENED_JSONL.relative_to(ROOT)),
            "merged_verify": str(base.VERIFY_JSON.relative_to(ROOT)),
        },
        "errors": errors[:100],
    }
    VERIFY_JSON.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
