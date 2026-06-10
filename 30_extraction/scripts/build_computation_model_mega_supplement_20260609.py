from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx


ROOT = Path(__file__).resolve().parents[2]
KB_DIR = ROOT / "10_research" / "recent_knowledge_base_20260609"
QUALITY_DIR = ROOT / "40_quality_evidence"
BASE_SCRIPT = ROOT / "30_extraction" / "scripts" / "build_recent_knowledge_base_20260609.py"

QUERY_MATRIX_JSON = KB_DIR / "computation_model_mega_query_matrix_20260609.json"
QUERY_MATRIX_CSV = KB_DIR / "computation_model_mega_query_matrix_20260609.csv"
RAW_JSONL = KB_DIR / "raw_computation_model_mega_20260609.jsonl"
SCREENED_JSONL = KB_DIR / "screened_computation_model_mega_20260609.jsonl"
CLASSIC_JSONL = KB_DIR / "classic_computation_model_reference_mega_20260609.jsonl"
ERROR_JSONL = KB_DIR / "computation_model_mega_fetch_errors_20260609.jsonl"
QUERY_PROGRESS_JSONL = KB_DIR / "computation_model_mega_query_progress_20260609.jsonl"
RUN_STATE_JSON = QUALITY_DIR / "computation_model_mega_run_state_20260609.json"
VERIFY_JSON = QUALITY_DIR / "computation_model_mega_supplement_verification_20260609.json"

TARGET_RECENT_QUERY_COUNT = 5200
TARGET_CLASSIC_QUERY_COUNT = 240
BLOCK_QUERY_LIMIT = 520
OPENALEX_PER_PAGE = 10
CROSSREF_ROWS = 10
CONCURRENCY = 8
RETRY_COUNT = 3
BATCH_SIZE = 160


MODEL_BLOCKS: dict[str, dict[str, list[str]]] = {
    "stochastic_uncertainty_sensitivity": {
        "methods": [
            "Monte Carlo simulation",
            "uncertainty quantification",
            "probabilistic simulation",
            "Bayesian uncertainty model",
            "Latin hypercube sampling",
            "Sobol sensitivity analysis",
            "Morris screening sensitivity",
            "scenario uncertainty analysis",
            "global sensitivity analysis",
            "stochastic demand simulation",
            "risk interval forecasting",
            "surrogate model uncertainty",
            "Gaussian process emulator",
        ],
        "contexts": [
            "park visitor demand",
            "retail revenue forecast",
            "food beverage conversion",
            "tourism visitor flow",
            "outdoor concession operation",
            "crowd capacity planning",
            "public space service demand",
            "commercial site selection",
            "weather affected footfall",
            "event day visitor demand",
        ],
        "outcomes": [
            "P5 P50 P95 interval",
            "parameter ranking",
            "robust scenario comparison",
            "calibration uncertainty",
            "decision support",
            "confidence interval",
            "revenue risk band",
            "model validation",
        ],
    },
    "bayesian_calibration_validation": {
        "methods": [
            "Bayesian calibration",
            "approximate Bayesian computation",
            "simulation model validation",
            "verification validation simulation",
            "posterior predictive check",
            "data assimilation",
            "parameter inference",
            "model discrepancy",
            "calibration validation",
            "uncertainty propagation",
            "probabilistic calibration",
            "simulation credibility assessment",
        ],
        "contexts": [
            "agent based model",
            "pedestrian simulation",
            "visitor flow model",
            "retail demand model",
            "digital twin simulation",
            "activity based model",
            "queue simulation",
            "revenue forecast",
            "urban mobility simulation",
            "park commercial decision",
        ],
        "outcomes": [
            "evidence traceability",
            "parameter calibration",
            "random seed control",
            "model risk",
            "validation evidence",
            "reproducibility",
            "decision confidence",
            "human review",
        ],
    },
    "discrete_choice_spatial_interaction": {
        "methods": [
            "multinomial logit",
            "nested logit",
            "mixed logit",
            "latent class choice model",
            "random utility model",
            "destination choice model",
            "activity choice model",
            "store choice model",
            "Huff model",
            "gravity model",
            "spatial interaction model",
            "choice set generation",
            "willingness to pay model",
        ],
        "contexts": [
            "park visitor",
            "tourism attraction",
            "urban retail",
            "food beverage kiosk",
            "recreation demand",
            "public space amenity",
            "commercial node",
            "POI visit",
            "family visitor",
            "older adults park",
        ],
        "outcomes": [
            "destination selection",
            "activity participation",
            "spending behavior",
            "price sensitivity",
            "market share",
            "attraction utility",
            "scenario comparison",
            "site selection",
        ],
    },
    "abm_microsimulation_pedestrian": {
        "methods": [
            "agent based model",
            "multi agent simulation",
            "Mesa agent based modeling",
            "microsimulation",
            "pedestrian simulation",
            "social force model",
            "cellular automata pedestrian",
            "route choice agent model",
            "crowd simulation",
            "behavioral agent model",
            "hybrid agent based simulation",
            "spatial agent simulation",
        ],
        "contexts": [
            "urban park",
            "public plaza",
            "commercial street",
            "lake trail",
            "entrance gate",
            "food service area",
            "sports event crowd",
            "festival visitor",
            "family recreation",
            "night economy public space",
        ],
        "outcomes": [
            "trajectory heatmap",
            "visitor flow",
            "dwell time",
            "crowd density",
            "bottleneck",
            "route sequence",
            "calibration validation",
            "safety risk",
        ],
    },
    "discrete_event_queue_capacity": {
        "methods": [
            "discrete event simulation",
            "queueing model",
            "queue simulation",
            "SimPy simulation",
            "service system simulation",
            "capacity planning model",
            "waiting time model",
            "throughput simulation",
            "inventory service simulation",
            "staffing simulation",
            "bottleneck analysis",
            "operational simulation",
        ],
        "contexts": [
            "coffee kiosk",
            "food beverage service",
            "park entrance",
            "visitor attraction",
            "festival booth",
            "retail counter",
            "public space service point",
            "sports event service",
            "peak hour queue",
            "small retail operations",
        ],
        "outcomes": [
            "service capacity",
            "wait time",
            "queue length",
            "staffing",
            "inventory",
            "revenue loss",
            "trial operation metrics",
            "bottleneck",
        ],
    },
    "facility_location_optimization": {
        "methods": [
            "facility location model",
            "location allocation",
            "p median model",
            "maximal covering location",
            "set covering location",
            "multi objective optimization",
            "robust optimization",
            "simulation optimization",
            "Pareto optimization",
            "MCDM site selection",
            "AHP TOPSIS",
            "PROMETHEE VIKOR",
        ],
        "contexts": [
            "park commercial node",
            "urban retail facility",
            "public amenity location",
            "food service site",
            "recreation service facility",
            "commercial concession",
            "visitor service point",
            "pedestrian accessibility",
            "GIS site selection",
            "multi node portfolio",
        ],
        "outcomes": [
            "priority ranking",
            "coverage",
            "accessibility",
            "trade off",
            "scenario optimization",
            "investment phasing",
            "decision support",
            "robustness",
        ],
    },
    "synthetic_population_activity_travel": {
        "methods": [
            "synthetic population",
            "population synthesis",
            "microsimulation population",
            "activity based travel demand",
            "activity chain model",
            "time geography",
            "itinerary model",
            "origin destination model",
            "tour generation model",
            "visitor typology model",
            "frequency segmentation",
            "persona simulation",
        ],
        "contexts": [
            "park visitor",
            "local residents",
            "tourists",
            "floating population",
            "family recreation",
            "older adults",
            "sports wellness",
            "commuter visitor",
            "festival visitor",
            "retail consumer",
        ],
        "outcomes": [
            "activity chain",
            "dwell time",
            "route sequence",
            "spending trigger",
            "time of day",
            "visit frequency",
            "demand forecasting",
            "scenario simulation",
        ],
    },
    "demand_revenue_forecasting": {
        "methods": [
            "retail demand forecasting",
            "footfall prediction",
            "conversion rate model",
            "revenue forecasting",
            "price sensitivity model",
            "willingness to pay",
            "customer spending prediction",
            "unit economics model",
            "dwell time conversion",
            "store performance model",
            "tourism expenditure model",
            "food beverage demand model",
        ],
        "contexts": [
            "park visitor",
            "urban retail",
            "food beverage kiosk",
            "commercial concession",
            "outdoor recreation",
            "tourism attraction",
            "public space service",
            "sports wellness service",
            "family leisure",
            "night economy",
        ],
        "outcomes": [
            "daily revenue",
            "conversion",
            "spending behavior",
            "price band",
            "scenario comparison",
            "sensitivity",
            "capacity constraint",
            "pilot operation",
        ],
    },
    "gis_network_geometry_model": {
        "methods": [
            "network accessibility model",
            "walkability model",
            "service radius model",
            "catchment area model",
            "space syntax",
            "GIS network analysis",
            "CAD GIS conversion",
            "BIM GIS integration",
            "digital twin geometry",
            "geospatial uncertainty",
            "spatial data fusion",
            "route distance model",
        ],
        "contexts": [
            "urban park",
            "pedestrian route",
            "commercial node",
            "entrance gate",
            "lake area",
            "service facility",
            "public space",
            "retail catchment",
            "visitor flow",
            "amenity planning",
        ],
        "outcomes": [
            "accessibility",
            "area measurement",
            "route distance",
            "catchment",
            "site selection",
            "heatmap",
            "node comparison",
            "geometry uncertainty",
        ],
    },
    "llm_agent_model_control": {
        "methods": [
            "LLM agent simulation",
            "structured output validation",
            "JSON schema validation",
            "tool use agent evaluation",
            "RAG faithfulness evaluation",
            "human in the loop validation",
            "agent trace observability",
            "LLM guardrails",
            "model risk management",
            "evidence grounded generation",
            "agent workflow evaluation",
            "fallback strategy",
        ],
        "contexts": [
            "simulation decision support",
            "business report generation",
            "urban planning decision",
            "retail site selection",
            "human behavior simulation",
            "DeepSeek compatible API",
            "low cost model orchestration",
            "agent based simulation",
            "customer facing workbench",
            "evidence chain",
        ],
        "outcomes": [
            "schema compliance",
            "hallucination control",
            "auditability",
            "decision confidence",
            "traceability",
            "human review",
            "risk control",
            "model replacement",
        ],
    },
}


CLASSIC_THEORY_SEEDS = [
    "Huff probabilistic analysis shopping center trade areas",
    "Reilly law retail gravitation",
    "Wilson entropy maximizing spatial interaction model",
    "McFadden conditional logit qualitative choice behavior",
    "Ben Akiva Lerman discrete choice analysis",
    "Train discrete choice methods with simulation",
    "Schelling dynamic models segregation",
    "Epstein Axtell growing artificial societies",
    "Bonabeau agent based modeling methods techniques",
    "Tesfatsion agent based computational economics",
    "Helbing Molnar social force model pedestrian dynamics",
    "Burstedde cellular automata pedestrian dynamics",
    "Sargent verification validation simulation models",
    "Law simulation modeling and analysis",
    "Banks discrete event system simulation",
    "Kendall queueing theory notation",
    "Little law queueing systems",
    "McKay Latin hypercube sampling computer experiments",
    "Kennedy O'Hagan Bayesian calibration computer models",
    "Sobol sensitivity estimates nonlinear mathematical models",
    "Morris elementary effects sensitivity analysis",
    "Saltelli global sensitivity analysis",
    "Hägerstrand time geography",
    "Bowman Ben Akiva activity based travel demand",
    "Beckmann McGuire Winsten transportation studies",
    "Daganzo activity based travel demand",
    "Dijkstra shortest path algorithm",
    "Church ReVelle maximal covering location problem",
    "Hakimi optimum locations switching centers",
    "Toregas location set covering problem",
    "Weber location problem",
    "Hotelling stability in competition location",
    "Christaller central place theory",
    "Luce individual choice behavior",
    "Simon bounded rationality decision",
    "Saaty analytic hierarchy process",
    "Hwang Yoon TOPSIS",
    "Roy ELECTRE outranking",
    "Brans PROMETHEE",
    "Box Jenkins time series analysis forecasting control",
    "Hyndman forecast principles practice",
]


def load_base_module() -> Any:
    spec = importlib.util.spec_from_file_location("kb_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["kb_base_computation_model_mega"] = module
    spec.loader.exec_module(module)
    return module


def normalize_query(query: str) -> str:
    return re.sub(r"\s+", " ", query.strip())


def build_queries() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for block, spec in MODEL_BLOCKS.items():
        block_count = 0
        for method in spec["methods"]:
            for context in spec["contexts"]:
                for outcome in spec["outcomes"]:
                    variants = [
                        f"{method} {context} {outcome}",
                        f"{context} {method} {outcome}",
                    ]
                    for query in variants:
                        query = normalize_query(query)
                        key = f"recent::{query.lower()}"
                        if key in seen:
                            continue
                        seen.add(key)
                        rows.append({"block": block, "query": query, "reference_class": "recent_priority"})
                        block_count += 1
                        if block_count >= BLOCK_QUERY_LIMIT:
                            break
                    if block_count >= BLOCK_QUERY_LIMIT:
                        break
                if block_count >= BLOCK_QUERY_LIMIT:
                    break
            if block_count >= BLOCK_QUERY_LIMIT:
                break

    classic_contexts = [
        "simulation model",
        "retail location",
        "urban mobility",
        "pedestrian behavior",
        "visitor demand",
        "queue capacity",
    ]
    for seed in CLASSIC_THEORY_SEEDS:
        for context in classic_contexts:
            query = normalize_query(f"{seed} {context}")
            key = f"classic::{query.lower()}"
            if key in seen:
                continue
            seen.add(key)
            rows.append({"block": "classic_computation_theory", "query": query, "reference_class": "classic_theory"})
            if sum(1 for row in rows if row["reference_class"] == "classic_theory") >= TARGET_CLASSIC_QUERY_COUNT:
                break
        if sum(1 for row in rows if row["reference_class"] == "classic_theory") >= TARGET_CLASSIC_QUERY_COUNT:
            break

    if sum(1 for row in rows if row["reference_class"] == "recent_priority") < TARGET_RECENT_QUERY_COUNT:
        raise RuntimeError("recent computation/model query matrix below target")
    if sum(1 for row in rows if row["reference_class"] == "classic_theory") < TARGET_CLASSIC_QUERY_COUNT:
        raise RuntimeError("classic computation/model query matrix below target")
    return rows


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
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


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_query_csv(path: Path, rows: list[dict[str, str]]) -> None:
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["block", "reference_class", "query"], extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


async def request_json(client: httpx.AsyncClient, url: str, params: dict[str, Any]) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(RETRY_COUNT):
        try:
            response = await client.get(url, params=params)
            if response.status_code == 429:
                await asyncio.sleep(1.8 * (attempt + 1))
                continue
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(0.8 * (attempt + 1))
    raise RuntimeError(repr(last_error))


async def fetch_openalex(client: httpx.AsyncClient, query_info: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    is_classic = query_info["reference_class"] == "classic_theory"
    params = {
        "search": query_info["query"],
        "filter": "type:article" if is_classic else "from_publication_date:2025-01-01,type:article",
        "per-page": OPENALEX_PER_PAGE,
        "select": "id,doi,title,display_name,publication_year,publication_date,cited_by_count,abstract_inverted_index,authorships,primary_location,locations,concepts,keywords,open_access,type,type_crossref",
    }
    try:
        payload = await request_json(client, "https://api.openalex.org/works", params)
    except Exception as exc:
        return [], [{"source": "openalex", "query": query_info["query"], "block": query_info["block"], "error": repr(exc)}]
    rows = payload.get("results", [])
    for row in rows:
        row["_source"] = "openalex"
        row["_theme"] = f"computation_model_mega:{query_info['block']}"
        row["_query"] = query_info["query"]
        row["_reference_class"] = query_info["reference_class"]
        row["_query_block"] = query_info["block"]
    return rows, []


async def fetch_crossref(client: httpx.AsyncClient, query_info: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    is_classic = query_info["reference_class"] == "classic_theory"
    params = {
        "query.bibliographic": query_info["query"],
        "filter": "type:journal-article" if is_classic else "from-pub-date:2025-01-01,type:journal-article",
        "rows": CROSSREF_ROWS,
        "select": "DOI,title,published-print,published-online,published,container-title,is-referenced-by-count,subject,abstract,URL,type",
    }
    try:
        payload = await request_json(client, "https://api.crossref.org/works", params)
    except Exception as exc:
        return [], [{"source": "crossref", "query": query_info["query"], "block": query_info["block"], "error": repr(exc)}]
    rows = payload.get("message", {}).get("items", [])
    for row in rows:
        row["_source"] = "crossref"
        row["_theme"] = f"computation_model_mega:{query_info['block']}"
        row["_query"] = query_info["query"]
        row["_reference_class"] = query_info["reference_class"]
        row["_query_block"] = query_info["block"]
    return rows, []


async def fetch_all(query_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    headers = {"User-Agent": "park-commercial-site-selection-simulation/1.0 (mailto:local@example.invalid)"}
    semaphore = asyncio.Semaphore(CONCURRENCY)
    raw_rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    async with httpx.AsyncClient(headers=headers, timeout=35, follow_redirects=True) as client:
        async def run_one(index: int, query_info: dict[str, str]) -> None:
            async with semaphore:
                if index % 100 == 0:
                    print(f"[{index}/{len(query_rows)}] {query_info['block']} / {query_info['query']}")
                openalex_rows, openalex_errors = await fetch_openalex(client, query_info)
                crossref_rows, crossref_errors = await fetch_crossref(client, query_info)
                raw_rows.extend(openalex_rows)
                raw_rows.extend(crossref_rows)
                errors.extend(openalex_errors)
                errors.extend(crossref_errors)

        await asyncio.gather(*(run_one(index, row) for index, row in enumerate(query_rows, start=1)))
    return raw_rows, errors


def query_key(query_info: dict[str, str]) -> str:
    return f"{query_info['reference_class']}|{query_info['block']}|{query_info['query']}"


def completed_query_keys() -> set[str]:
    keys: set[str] = set()
    if not QUERY_PROGRESS_JSONL.exists():
        return keys
    with QUERY_PROGRESS_JSONL.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if row.get("status") == "completed" and row.get("query_key"):
                keys.add(str(row["query_key"]))
    return keys


async def fetch_batch(batch_rows: list[tuple[int, dict[str, str]]], total: int) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[dict[str, Any]]]:
    headers = {"User-Agent": "park-commercial-site-selection-simulation/1.0 (mailto:local@example.invalid)"}
    semaphore = asyncio.Semaphore(CONCURRENCY)
    raw_rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    progress_rows: list[dict[str, Any]] = []
    async with httpx.AsyncClient(headers=headers, timeout=35, follow_redirects=True) as client:
        async def run_one(index: int, query_info: dict[str, str]) -> None:
            async with semaphore:
                if index % 100 == 0:
                    print(f"[{index}/{total}] {query_info['block']} / {query_info['query']}")
                openalex_rows, openalex_errors = await fetch_openalex(client, query_info)
                crossref_rows, crossref_errors = await fetch_crossref(client, query_info)
                query_raw = openalex_rows + crossref_rows
                query_errors = openalex_errors + crossref_errors
                raw_rows.extend(query_raw)
                errors.extend(query_errors)
                progress_rows.append(
                    {
                        "query_key": query_key(query_info),
                        "status": "completed",
                        "block": query_info["block"],
                        "reference_class": query_info["reference_class"],
                        "query": query_info["query"],
                        "raw_count": len(query_raw),
                        "error_count": len(query_errors),
                    }
                )

        await asyncio.gather(*(run_one(index, row) for index, row in batch_rows))
    return raw_rows, errors, progress_rows


async def fetch_all_streaming(query_rows: list[dict[str, str]], resume: bool = True) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    if not resume:
        for path in [RAW_JSONL, ERROR_JSONL, QUERY_PROGRESS_JSONL, RUN_STATE_JSON]:
            if path.exists():
                path.unlink()
    if not RAW_JSONL.exists() and QUERY_PROGRESS_JSONL.exists():
        QUERY_PROGRESS_JSONL.unlink()
    done = completed_query_keys() if resume else set()
    indexed_pending = [(index, row) for index, row in enumerate(query_rows, start=1) if query_key(row) not in done]
    total = len(query_rows)
    for batch_start in range(0, len(indexed_pending), BATCH_SIZE):
        batch = indexed_pending[batch_start : batch_start + BATCH_SIZE]
        raw_rows, errors, progress_rows = await fetch_batch(batch, total)
        append_jsonl(RAW_JSONL, raw_rows)
        append_jsonl(ERROR_JSONL, errors)
        append_jsonl(QUERY_PROGRESS_JSONL, progress_rows)
        done_count = len(done) + batch_start + len(batch)
        state = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "status": "fetching" if done_count < total else "fetched",
            "query_count": total,
            "completed_query_count": done_count,
            "remaining_query_count": total - done_count,
            "last_batch_raw_count": len(raw_rows),
            "last_batch_error_count": len(errors),
            "raw_file": str(RAW_JSONL.relative_to(ROOT)),
            "error_file": str(ERROR_JSONL.relative_to(ROOT)),
            "progress_file": str(QUERY_PROGRESS_JSONL.relative_to(ROOT)),
        }
        RUN_STATE_JSON.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(state, ensure_ascii=False))
    return read_jsonl(RAW_JSONL), read_jsonl(ERROR_JSONL)


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
        record["quality_reason"] = "计算/模型经典理论参考；用于方法骨架和模型边界，不直接作为奥森客户结论。"
        records.append(record)
    by_key = {}
    for record in records:
        by_key.setdefault(base.record_key(record), record)
    rows = list(by_key.values())
    rows.sort(key=lambda r: (int(r.get("cited_by_count") or 0), int(r.get("year") or 0)), reverse=True)
    return rows


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="构建计算与模型 Mega 知识增量")
    parser.add_argument("--reuse-existing", action="store_true")
    parser.add_argument("--matrix-only", action="store_true")
    args = parser.parse_args()

    base = load_base_module()
    query_rows = build_queries()
    QUERY_MATRIX_JSON.write_text(json.dumps({"query_count": len(query_rows), "queries": query_rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    write_query_csv(QUERY_MATRIX_CSV, query_rows)
    if args.matrix_only:
        print(json.dumps({"status": "matrix_only", "query_count": len(query_rows), "blocks": dict(Counter(row["block"] for row in query_rows)), "reference_classes": dict(Counter(row["reference_class"] for row in query_rows))}, ensure_ascii=False, indent=2))
        return

    if args.reuse_existing and RAW_JSONL.exists() and SCREENED_JSONL.exists():
        raw_rows = read_jsonl(RAW_JSONL)
        screened = read_jsonl(SCREENED_JSONL)
        rejected: list[dict[str, Any]] = []
        errors = read_jsonl(ERROR_JSONL)
    else:
        raw_rows, errors = asyncio.run(fetch_all_streaming(query_rows, resume=True))
        screened, rejected, _ = base.screen([row for row in raw_rows if row.get("_reference_class") != "classic_theory"])
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
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "pass" if len(query_rows) >= TARGET_RECENT_QUERY_COUNT + TARGET_CLASSIC_QUERY_COUNT and len(screened) >= 4500 and len(classics) >= 120 and stats["screened_total"] >= 25000 else "needs_action",
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
        "error_count": len(errors),
        "files": {
            "query_matrix": str(QUERY_MATRIX_JSON.relative_to(ROOT)),
            "query_matrix_csv": str(QUERY_MATRIX_CSV.relative_to(ROOT)),
            "raw": str(RAW_JSONL.relative_to(ROOT)),
            "screened": str(SCREENED_JSONL.relative_to(ROOT)),
            "classic": str(CLASSIC_JSONL.relative_to(ROOT)),
            "errors": str(ERROR_JSONL.relative_to(ROOT)),
            "query_progress": str(QUERY_PROGRESS_JSONL.relative_to(ROOT)),
            "run_state": str(RUN_STATE_JSON.relative_to(ROOT)),
            "merged_screened": str(base.SCREENED_JSONL.relative_to(ROOT)),
            "merged_verify": str(base.VERIFY_JSON.relative_to(ROOT)),
        },
        "rule": "这是计算/模型专项增量：只追加合并，不替代已有知识库；经典理论为模型骨架，近年资料为当前方法与落地变量约束。",
        "errors": errors[:80],
    }
    VERIFY_JSON.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
