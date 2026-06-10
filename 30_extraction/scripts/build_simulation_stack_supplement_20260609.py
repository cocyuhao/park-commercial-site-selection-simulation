from __future__ import annotations

import importlib.util
import json
import argparse
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import httpx


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "30_extraction" / "scripts" / "build_recent_knowledge_base_20260609.py"
KB_DIR = ROOT / "10_research" / "recent_knowledge_base_20260609"
QUALITY_DIR = ROOT / "40_quality_evidence"

RAW_SUPPLEMENT = KB_DIR / "raw_simulation_stack_supplement_20260609.jsonl"
SCREENED_SUPPLEMENT = KB_DIR / "screened_simulation_stack_supplement_20260609.jsonl"
QUERY_SUPPLEMENT = KB_DIR / "simulation_stack_query_matrix_20260609.json"
VERIFY_SUPPLEMENT = QUALITY_DIR / "simulation_stack_supplement_verification_20260609.json"

RECENT_QUERY_BLOCKS: dict[str, list[str]] = {
    "persona_synthetic_population": [
        "synthetic population agent based model urban mobility",
        "synthetic population activity based travel demand model",
        "synthetic population visitor behavior urban park",
        "persona based agent simulation consumer behavior",
        "LLM persona simulation human mobility",
        "generative agents persona behavior simulation",
        "visitor typology recreation site simulation",
        "tourist typology agent based simulation",
        "population synthesis small area travel demand",
        "activity travel demand synthesis agent based modelling",
        "mobile phone data synthetic population urban mobility",
        "GPS data synthetic population activity pattern",
        "heterogeneous agents visitor flow simulation",
        "resident tourist worker persona park simulation",
        "consumer persona demand forecasting retail location",
        "socioeconomic synthetic population leisure demand",
        "age group persona urban park activity behavior",
        "family visitor persona recreation demand",
        "older adults persona park accessibility demand",
        "sports wellness visitor persona park behavior",
    ],
    "activity_chain_time_geography": [
        "activity chain model visitor flow urban park",
        "activity based travel demand park visitor",
        "time geography leisure activity simulation",
        "tourist itinerary activity chain simulation",
        "dwell time activity sequence retail visitor",
        "spatio temporal visitor behavior activity chain",
        "origin destination activity chain pedestrian simulation",
        "activity based model leisure consumption",
        "daily activity schedule agent based simulation",
        "urban recreation activity pattern modeling",
        "park visit activity sequence dwell time",
        "visitor route activity chain public space",
        "shopping activity chain consumer movement",
        "tourism activity chain destination choice",
        "activity based microsimulation urban mobility",
        "multi purpose trip activity chain retail",
        "activity chain calibration mobile phone data",
        "activity sequence prediction human mobility",
        "agent based itinerary simulation tourism",
        "time use survey activity based travel demand",
    ],
    "abm_pedestrian_crowd_engine": [
        "agent based model park visitor flow simulation",
        "agent based simulation pedestrian public space design",
        "Mesa agent based modeling urban mobility",
        "Mesa Python agent based pedestrian simulation",
        "agent based model commercial street pedestrian behavior",
        "multi agent pedestrian simulation urban plaza",
        "social force model pedestrian grouping avoidance simulation",
        "cellular automata pedestrian flow simulation public space",
        "crowd simulation urban park visitor flow",
        "pedestrian microsimulation route choice public space",
        "agent based pedestrian route choice attraction",
        "agent based simulation crowd density comfort",
        "evacuation pedestrian simulation public park",
        "multi agent simulation crowd bottleneck public space",
        "pedestrian simulation calibration validation",
        "agent based digital twin pedestrian simulation",
        "data driven agent based pedestrian behavior modeling",
        "ABM visitor flow park service facility",
        "agent based simulation commercial complex pedestrian",
        "public space design optimization agent based simulation",
    ],
    "discrete_choice_spatial_interaction": [
        "discrete choice model park recreation demand",
        "multinomial logit visitor destination choice",
        "nested logit tourist destination choice",
        "store choice model visitor spending retail",
        "destination choice model urban park visitor",
        "Huff model retail location visitor flow",
        "gravity model retail store choice consumer movement",
        "spatial interaction model retail site selection",
        "random utility model recreation demand",
        "choice experiment willingness to pay urban recreation",
        "visitor willingness to pay urban park services",
        "consumer choice model leisure service demand",
        "destination choice mobility POI visits",
        "activity destination choice travel demand model",
        "joint destination activity choice model",
        "price sensitivity discrete choice retail food beverage",
        "mixed logit recreational site choice",
        "latent class model visitor typology park",
        "choice modeling urban green space visits",
        "retail attraction model footfall destination choice",
    ],
    "queue_capacity_discrete_event": [
        "queue simulation cafe service throughput",
        "discrete event simulation food beverage service capacity",
        "SimPy queue simulation service capacity",
        "service time queue model retail food beverage",
        "capacity planning visitor attraction queue management",
        "queue length wait time retail service simulation",
        "food court queue simulation demand capacity",
        "kiosk service capacity queue simulation",
        "retail checkout queue simulation discrete event",
        "visitor facility capacity queue model park",
        "crowd bottleneck queue simulation public space",
        "staffing optimization queue simulation service operations",
        "inventory capacity demand simulation retail kiosk",
        "service throughput optimization cafe simulation",
        "discrete event simulation small retail operations",
        "queueing model visitor service public attraction",
        "capacity constrained demand simulation food retail",
        "peak hour queue simulation public space services",
        "agent based queue behavior service facility",
        "operational digital twin queue service simulation",
    ],
    "monte_carlo_uncertainty_sensitivity": [
        "Monte Carlo simulation visitor flow revenue forecast",
        "Monte Carlo retail demand uncertainty simulation",
        "Monte Carlo scenario analysis commercial site selection",
        "P5 P50 P95 demand forecast Monte Carlo retail",
        "uncertainty quantification agent based simulation urban",
        "stochastic simulation park visitor demand forecasting",
        "probabilistic decision support retail site selection",
        "Bayesian calibration Monte Carlo demand simulation",
        "sensitivity analysis visitor flow simulation",
        "global sensitivity analysis agent based model",
        "SALib sensitivity analysis simulation model",
        "Latin hypercube sampling demand simulation retail",
        "scenario based simulation visitor flow public space",
        "baseline pilot full scenario Monte Carlo simulation",
        "coffee kiosk demand simulation foot traffic uncertainty",
        "revenue forecast uncertainty food beverage visitor flow",
        "Monte Carlo conversion rate footfall dwell time",
        "stochastic demand service capacity simulation",
        "Bayesian structural time series retail demand forecast",
        "probabilistic forecast park visitor demand",
    ],
    "calibration_validation_evidence": [
        "agent based model calibration validation urban mobility",
        "ABM calibration validation visitor behavior",
        "pedestrian model calibration validation mobile data",
        "simulation model validation public space pedestrian",
        "data assimilation agent based simulation urban mobility",
        "Bayesian calibration agent based model",
        "inverse calibration pedestrian simulation",
        "cross validation visitor flow forecasting",
        "model validation Monte Carlo simulation demand",
        "calibrating activity based travel demand model",
        "calibrating queue simulation service operations",
        "evidence grounded simulation decision support",
        "simulation auditability evidence traceability",
        "uncertainty communication simulation based decision support",
        "human in the loop validation LLM agent simulation",
        "LLM agent simulation calibration validation",
        "RAG evidence grounded generation simulation report",
        "structured output validation JSON schema LLM agent",
        "agent trace execution provenance simulation",
        "observability trace evaluation AI agent workflow",
    ],
    "tools_official_and_practical": [
        "Mesa Python agent based modeling framework",
        "Mesa ABM Python documentation",
        "SimPy discrete event simulation Python",
        "SimPy queue resource capacity simulation",
        "OR-Tools optimization facility location Python",
        "SALib sensitivity analysis Python Monte Carlo",
        "PyMC Bayesian calibration simulation",
        "NumPy Monte Carlo simulation demand forecasting",
        "SciPy stochastic simulation Python",
        "Mesa agent based modeling geospatial",
        "mesa geo agent based model GIS Python",
        "networkx pedestrian route choice simulation",
        "shapely geospatial Python pedestrian accessibility",
        "geopandas urban mobility simulation Python",
        "osmnx walkability route choice Python",
        "simpy service operations queue retail",
        "agentpy agent based model Python",
        "cadquery shapely CAD geometry Python",
        "ezdxf parse DWG DXF Python geospatial",
        "pydantic JSON schema LLM structured output validation",
    ],
}

CLASSIC_REFERENCE_QUERIES = [
    "Huff model retail location classic",
    "gravity model spatial interaction retail classic",
    "random utility discrete choice McFadden",
    "activity based travel demand Bowman Ben Akiva",
    "time geography Hagerstrand activity space",
    "agent based modeling Epstein Axtell Sugarscape",
    "social force model Helbing pedestrian dynamics",
    "cellular automata pedestrian dynamics floor field model",
    "Monte Carlo simulation uncertainty analysis classic",
    "queueing theory service capacity operations classic",
    "Law Kelton simulation modeling analysis validation",
    "Saltelli sensitivity analysis global methods",
    "Bayesian calibration computer models Kennedy O'Hagan",
    "Holland genetic algorithms optimization classic",
    "discrete event simulation queueing systems classic",
    "space syntax pedestrian movement retail location",
    "central place theory retail location classic",
    "location allocation model facility location classic",
    "agent based computational economics Tesfatsion classic",
    "microsimulation travel demand classic",
]


def expanded_queries() -> list[dict[str, str]]:
    rows = []
    for block, queries in RECENT_QUERY_BLOCKS.items():
        for query in queries:
            rows.append({"block": block, "query": query, "reference_class": "recent_priority"})
    for query in CLASSIC_REFERENCE_QUERIES:
        rows.append({"block": "classic_theory_reference", "query": query, "reference_class": "classic_theory"})
    return rows


def load_base_module() -> Any:
    spec = importlib.util.spec_from_file_location("kb_base", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["kb_base"] = module
    spec.loader.exec_module(module)
    return module


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


def merge_records(base: Any, existing: list[dict[str, Any]], supplement: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for row in existing + supplement:
        rescored = {**row, **base.score_record(row)}
        rescored["source_count"] = len(set(str(rescored.get("source") or "").split("+")))
        key = base.record_key(rescored)
        if key not in by_key:
            by_key[key] = rescored
            continue
        old = by_key[key]
        old["source"] = "+".join(sorted(set(str(old.get("source") or "").split("+")) | set(str(rescored.get("source") or "").split("+"))))
        old["source_count"] = len(set(old["source"].split("+")))
        old["theme"] = "+".join(sorted(set(str(old.get("theme") or "").split("+")) | set(str(rescored.get("theme") or "").split("+"))))
        if rescored.get("query") and str(rescored["query"]) not in str(old.get("query") or ""):
            old["query"] = f"{old.get('query', '')} || {rescored['query']}".strip(" |")
        if float(rescored.get("score") or 0) > float(old.get("score") or 0):
            for field in [
                "score",
                "tier",
                "category_hits",
                "category_count",
                "project_landing",
                "rejection_reason",
                "abstract",
                "venue",
                "cited_by_count",
                "quality_reason",
            ]:
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


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="构建或合并仿真栈专项知识补充")
    parser.add_argument("--reuse-existing", action="store_true", help="复用已抓取的 raw/screened 文件，只执行合并和验证")
    args = parser.parse_args()
    base = load_base_module()
    theme = "simulation_stack_persona_abm_mc"
    query_rows = expanded_queries()
    QUERY_SUPPLEMENT.write_text(json.dumps({"theme": theme, "queries": query_rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    errors: list[dict[str, str]] = []
    raw_rows: list[dict[str, Any]] = []
    if args.reuse_existing and RAW_SUPPLEMENT.exists() and SCREENED_SUPPLEMENT.exists():
        raw_rows = read_jsonl(RAW_SUPPLEMENT)
        supplement_screened = read_jsonl(SCREENED_SUPPLEMENT)
        supplement_rejected: list[dict[str, Any]] = []
        supplement_stats = base.screen(raw_rows)[2]
    else:
        headers = {"User-Agent": "park-commercial-site-selection-simulation/1.0 (mailto:local@example.invalid)"}
        with httpx.Client(headers=headers, timeout=45, follow_redirects=True) as client:
            for index, query_info in enumerate(query_rows, start=1):
                query = query_info["query"]
                fetch_theme = f"{theme}:{query_info['block']}"
                print(f"[{index}/{len(query_rows)}] {query_info['reference_class']} / {query_info['block']} / {query}")
                for source, fetcher in [("openalex", base.fetch_openalex), ("crossref", base.fetch_crossref)]:
                    try:
                        fetched = fetcher(client, fetch_theme, query)
                        for row in fetched:
                            row["_reference_class"] = query_info["reference_class"]
                            row["_query_block"] = query_info["block"]
                        raw_rows.extend(fetched)
                    except Exception as exc:
                        errors.append({"source": source, "theme": fetch_theme, "query": query, "error": repr(exc)})
                if index <= 24:
                    try:
                        fetched = base.fetch_semantic(client, fetch_theme, query)
                        for row in fetched:
                            row["_reference_class"] = query_info["reference_class"]
                            row["_query_block"] = query_info["block"]
                        raw_rows.extend(fetched)
                    except Exception as exc:
                        errors.append({"source": "semantic_scholar", "theme": fetch_theme, "query": query, "error": repr(exc)})
                time.sleep(0.08)
            for query in [
                "agent based urban simulation",
                "Monte Carlo demand forecasting",
                "activity based travel demand",
                "generative agents human behavior simulation",
                "LLM structured output validation",
                "agent traces execution provenance",
            ]:
                try:
                    fetched = base.fetch_arxiv(client, f"{theme}:arxiv_recent", query)
                    for row in fetched:
                        row["_reference_class"] = "recent_priority"
                        row["_query_block"] = "arxiv_recent"
                    raw_rows.extend(fetched)
                except Exception as exc:
                    errors.append({"source": "arxiv", "theme": theme, "query": query, "error": repr(exc)})

        write_jsonl(RAW_SUPPLEMENT, raw_rows)
        supplement_screened, supplement_rejected, supplement_stats = base.screen(raw_rows)
        write_jsonl(SCREENED_SUPPLEMENT, supplement_screened)

    old_verify = {}
    if base.VERIFY_JSON.exists():
        old_verify = json.loads(base.VERIFY_JSON.read_text(encoding="utf-8"))
    existing = read_jsonl(base.SCREENED_JSONL)
    merged = merge_records(base, existing, supplement_screened)
    old_rejected = int((old_verify.get("screening_stats") or {}).get("rejected_total") or 0)
    stats = stats_for(merged, old_rejected + len(supplement_rejected))
    raw_counts = dict((old_verify.get("raw_counts") or {}))
    supplement_source_counts = Counter(row.get("_source") for row in raw_rows)
    for source in ["openalex", "crossref", "semantic_scholar", "arxiv"]:
        raw_counts[source] = int(raw_counts.get(source) or 0) + int(supplement_source_counts.get(source) or 0)
    raw_counts["total"] = sum(raw_counts.get(source, 0) for source in ["openalex", "crossref", "semantic_scholar", "arxiv"])
    meta = {
        "raw_counts": raw_counts,
        "errors": list((old_verify.get("errors") or [])[:100]) + errors[:100],
        "query_count": int(old_verify.get("query_count") or 0) + len(query_rows),
    }
    base.write_outputs(merged, supplement_rejected, stats, meta)
    verify = {
        "status": "pass" if len(supplement_screened) >= 300 and stats["screened_total"] >= 1000 else "needs_action",
        "theme": theme,
        "supplement_query_count": len(query_rows),
        "supplement_query_blocks": dict(Counter(row["block"] for row in query_rows)),
        "supplement_reference_classes": dict(Counter(row["reference_class"] for row in query_rows)),
        "supplement_raw_total": len(raw_rows),
        "supplement_screened_total": len(supplement_screened),
        "supplement_rejected_total": len(supplement_rejected),
        "supplement_stats": supplement_stats,
        "merged_screened_total": stats["screened_total"],
        "merged_category_counts": stats["category_counts"],
        "merged_theme_counts": stats["theme_counts"],
        "files": {
            "raw_supplement": str(RAW_SUPPLEMENT.relative_to(ROOT)),
            "screened_supplement": str(SCREENED_SUPPLEMENT.relative_to(ROOT)),
            "query_matrix": str(QUERY_SUPPLEMENT.relative_to(ROOT)),
            "merged_screened": str(base.SCREENED_JSONL.relative_to(ROOT)),
            "merged_verify": str(base.VERIFY_JSON.relative_to(ROOT)),
        },
        "errors": errors[:100],
    }
    VERIFY_SUPPLEMENT.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
