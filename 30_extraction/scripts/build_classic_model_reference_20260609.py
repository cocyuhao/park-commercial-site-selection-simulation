from __future__ import annotations

import asyncio
import json
import re
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import httpx


ROOT = Path(__file__).resolve().parents[2]
KB_DIR = ROOT / "10_research" / "recent_knowledge_base_20260609"
QUALITY_DIR = ROOT / "40_quality_evidence"

OUTPUT_JSONL = KB_DIR / "classic_model_reference_20260609.jsonl"
OUTPUT_CSV = KB_DIR / "classic_model_reference_20260609.csv"
VERIFY_JSON = QUALITY_DIR / "classic_model_reference_verification_20260609.json"

OPENALEX_ROWS = 8
CROSSREF_ROWS = 8
REQUEST_SLEEP_SECONDS = 0.25
CONCURRENCY = 8
RETRY_COUNT = 3


CLASSIC_QUERY_ROWS = [
    {
        "layer": "spatial_interaction_retail_location",
        "query": "Huff probabilistic analysis shopping center trade areas",
        "project_use": "约束商业节点吸引力、服务半径、竞品分流和空间交互。",
    },
    {
        "layer": "spatial_interaction_retail_location",
        "query": "Reilly law retail gravitation",
        "project_use": "作为重力/吸引力模型的历史参照，不直接套公式。",
    },
    {
        "layer": "spatial_interaction_retail_location",
        "query": "Wilson entropy maximizing spatial interaction model",
        "project_use": "用于理解 OD、到访概率和空间交互的约束形式。",
    },
    {
        "layer": "discrete_choice_destination",
        "query": "McFadden conditional logit qualitative choice behavior",
        "project_use": "约束 destination/activity/spend 的选择逻辑，避免 LLM 自由编行为。",
    },
    {
        "layer": "discrete_choice_destination",
        "query": "Ben-Akiva Lerman discrete choice analysis",
        "project_use": "作为离散选择模型的教科书级参考，用于模型接口设计。",
    },
    {
        "layer": "discrete_choice_destination",
        "query": "Train discrete choice methods with simulation",
        "project_use": "支持混合 logit、模拟选择和异质偏好建模。",
    },
    {
        "layer": "agent_based_modeling",
        "query": "Schelling dynamic models segregation agent based",
        "project_use": "说明微观规则能产生宏观空间形态，用于 ABM 解释边界。",
    },
    {
        "layer": "agent_based_modeling",
        "query": "Epstein Axtell growing artificial societies agent based model",
        "project_use": "作为多主体仿真框架参考，不直接迁移结论。",
    },
    {
        "layer": "agent_based_modeling",
        "query": "Bonabeau agent based modeling methods and techniques",
        "project_use": "支撑什么时候该用 ABM、什么时候不该用 ABM 的判断。",
    },
    {
        "layer": "agent_based_modeling",
        "query": "Tesfatsion agent based computational economics",
        "project_use": "支撑经济行为主体、市场交互和局部规则的抽象。",
    },
    {
        "layer": "pedestrian_crowd_simulation",
        "query": "Helbing Molnar social force model pedestrian dynamics",
        "project_use": "约束拥挤、避让、瓶颈和步行动态，不把地图热力当静态图。",
    },
    {
        "layer": "pedestrian_crowd_simulation",
        "query": "Burstedde simulation pedestrian dynamics cellular automata",
        "project_use": "用于比较社会力与元胞自动机类步行模型。",
    },
    {
        "layer": "pedestrian_crowd_simulation",
        "query": "pedestrian simulation validation crowd dynamics",
        "project_use": "约束轨迹层必须校准和验证，而不是只画热力图。",
    },
    {
        "layer": "discrete_event_queue_capacity",
        "query": "Sargent verification validation simulation models",
        "project_use": "支撑仿真模型校验、确认和可信度评估。",
    },
    {
        "layer": "discrete_event_queue_capacity",
        "query": "Law simulation modeling and analysis discrete event",
        "project_use": "用于离散事件仿真、排队容量和试运营指标设计。",
    },
    {
        "layer": "discrete_event_queue_capacity",
        "query": "queueing theory service capacity operations",
        "project_use": "支撑咖啡亭、餐饮、入口服务点的等待时间和服务能力。",
    },
    {
        "layer": "uncertainty_monte_carlo",
        "query": "Monte Carlo simulation uncertainty analysis",
        "project_use": "支撑 P5/P50/P95 与收益区间输出。",
    },
    {
        "layer": "uncertainty_monte_carlo",
        "query": "McKay Latin hypercube sampling analysis computer experiments",
        "project_use": "用于减少 Monte Carlo 抽样浪费，提高参数空间覆盖。",
    },
    {
        "layer": "uncertainty_monte_carlo",
        "query": "Kennedy O'Hagan Bayesian calibration computer models",
        "project_use": "用于模型校准、不确定性传播和仿真可信度表达。",
    },
    {
        "layer": "sensitivity_analysis",
        "query": "Sobol sensitivity estimates nonlinear mathematical models",
        "project_use": "支撑全局敏感性分析，找出最影响收益和拥挤的变量。",
    },
    {
        "layer": "sensitivity_analysis",
        "query": "Morris elementary effects sensitivity analysis",
        "project_use": "用于高维参数初筛，避免一开始就盲目全量仿真。",
    },
    {
        "layer": "sensitivity_analysis",
        "query": "Saltelli global sensitivity analysis",
        "project_use": "支撑敏感性排序和模型解释。",
    },
    {
        "layer": "calibration_validation",
        "query": "model calibration validation computer simulation uncertainty",
        "project_use": "支撑模型参数、随机种子、误差和复核状态记录。",
    },
    {
        "layer": "activity_based_travel_demand",
        "query": "activity based travel demand model Bowman Ben Akiva",
        "project_use": "用于把到达、游览、补给、消费、离园串成活动链。",
    },
    {
        "layer": "activity_based_travel_demand",
        "query": "time geography activity pattern Hägerstrand",
        "project_use": "用于约束活动链的时间、空间和可达性边界。",
    },
    {
        "layer": "microsimulation_synthetic_population",
        "query": "microsimulation synthetic population travel demand",
        "project_use": "支撑 Persona 从三类粗分扩展到微观个体属性。",
    },
    {
        "layer": "optimization_decision_support",
        "query": "facility location allocation model optimization",
        "project_use": "用于多候选点比较、容量分配和方案组合选择。",
    },
    {
        "layer": "optimization_decision_support",
        "query": "multi criteria decision making site selection retail",
        "project_use": "支撑把多指标从死分数改成可解释的优先级和条件。",
    },
    {
        "layer": "digital_twin_gis",
        "query": "geographic information systems spatial analysis network accessibility",
        "project_use": "支撑 CAD/GIS/路网/可达性进入仿真底座。",
    },
    {
        "layer": "digital_twin_gis",
        "query": "digital twin urban mobility simulation calibration",
        "project_use": "支撑数字底座与动态仿真之间的校准关系。",
    },
]


def request_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    full_url = f"{url}?{urlencode(params, doseq=True)}"
    req = Request(full_url, headers={"User-Agent": "park-commercial-site-selection-simulation/1.0 (mailto:local@example.invalid)"})
    with urlopen(req, timeout=40) as response:
        return json.loads(response.read().decode("utf-8"))


def abstract_from_openalex(index: dict[str, list[int]] | None) -> str:
    if not index:
        return ""
    tokens: list[tuple[int, str]] = []
    for word, positions in index.items():
        for position in positions:
            tokens.append((position, word))
    return " ".join(word for _, word in sorted(tokens))


def normalize_title(title: Any) -> str:
    if isinstance(title, list):
        return str(title[0]) if title else ""
    return str(title or "")


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def year_from_crossref(item: dict[str, Any]) -> int:
    for field in ["published-print", "published-online", "published"]:
        parts = item.get(field, {}).get("date-parts") if isinstance(item.get(field), dict) else None
        if parts and parts[0]:
            try:
                return int(parts[0][0])
            except Exception:
                continue
    return 0


def fetch_openalex(row: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    try:
        payload = request_json(
            "https://api.openalex.org/works",
            {
                "search": row["query"],
                "per-page": OPENALEX_ROWS,
                "select": "id,doi,title,display_name,publication_year,cited_by_count,abstract_inverted_index,primary_location,locations,concepts,keywords,type",
            },
        )
    except Exception as exc:
        return [], [{"source": "openalex", "query": row["query"], "error": repr(exc)}]
    records = []
    for item in payload.get("results", []):
        primary = item.get("primary_location") or {}
        source = primary.get("source") or {}
        records.append(
            {
                "source": "openalex",
                "layer": row["layer"],
                "query": row["query"],
                "title": clean_text(item.get("display_name") or item.get("title")),
                "year": int(item.get("publication_year") or 0),
                "doi": item.get("doi"),
                "url": item.get("id") or item.get("doi"),
                "venue": clean_text(source.get("display_name")),
                "cited_by_count": int(item.get("cited_by_count") or 0),
                "abstract": abstract_from_openalex(item.get("abstract_inverted_index"))[:1200],
                "project_use": row["project_use"],
                "reference_class": "classic_model_method",
            }
        )
    return records, errors


def fetch_crossref(row: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        payload = request_json(
            "https://api.crossref.org/works",
            {
                "query.bibliographic": row["query"],
                "rows": CROSSREF_ROWS,
                "select": "DOI,title,published-print,published-online,published,container-title,is-referenced-by-count,abstract,URL,type",
            },
        )
    except Exception as exc:
        return [], [{"source": "crossref", "query": row["query"], "error": repr(exc)}]
    records = []
    for item in payload.get("message", {}).get("items", []):
        records.append(
            {
                "source": "crossref",
                "layer": row["layer"],
                "query": row["query"],
                "title": clean_text(normalize_title(item.get("title"))),
                "year": year_from_crossref(item),
                "doi": item.get("DOI"),
                "url": item.get("URL") or (f"https://doi.org/{item['DOI']}" if item.get("DOI") else ""),
                "venue": clean_text(normalize_title(item.get("container-title"))),
                "cited_by_count": int(item.get("is-referenced-by-count") or 0),
                "abstract": clean_text(item.get("abstract"))[:1200],
                "project_use": row["project_use"],
                "reference_class": "classic_model_method",
            }
        )
    return records, []


async def request_json_async(client: httpx.AsyncClient, url: str, params: dict[str, Any]) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(RETRY_COUNT):
        try:
            response = await client.get(url, params=params)
            if response.status_code == 429:
                await asyncio.sleep(1.5 * (attempt + 1))
                continue
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(0.8 * (attempt + 1))
    raise RuntimeError(repr(last_error))


async def fetch_openalex_async(client: httpx.AsyncClient, row: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        payload = await request_json_async(
            client,
            "https://api.openalex.org/works",
            {
                "search": row["query"],
                "per-page": OPENALEX_ROWS,
                "select": "id,doi,title,display_name,publication_year,cited_by_count,abstract_inverted_index,primary_location,locations,concepts,keywords,type",
            },
        )
    except Exception as exc:
        return [], [{"source": "openalex", "query": row["query"], "error": repr(exc)}]
    records = []
    for item in payload.get("results", []):
        primary = item.get("primary_location") or {}
        source = primary.get("source") or {}
        records.append(
            {
                "source": "openalex",
                "layer": row["layer"],
                "query": row["query"],
                "title": clean_text(item.get("display_name") or item.get("title")),
                "year": int(item.get("publication_year") or 0),
                "doi": item.get("doi"),
                "url": item.get("id") or item.get("doi"),
                "venue": clean_text(source.get("display_name")),
                "cited_by_count": int(item.get("cited_by_count") or 0),
                "abstract": abstract_from_openalex(item.get("abstract_inverted_index"))[:1200],
                "project_use": row["project_use"],
                "reference_class": "classic_model_method",
            }
        )
    return records, []


async def fetch_crossref_async(client: httpx.AsyncClient, row: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        payload = await request_json_async(
            client,
            "https://api.crossref.org/works",
            {
                "query.bibliographic": row["query"],
                "rows": CROSSREF_ROWS,
                "select": "DOI,title,published-print,published-online,published,container-title,is-referenced-by-count,abstract,URL,type",
            },
        )
    except Exception as exc:
        return [], [{"source": "crossref", "query": row["query"], "error": repr(exc)}]
    records = []
    for item in payload.get("message", {}).get("items", []):
        records.append(
            {
                "source": "crossref",
                "layer": row["layer"],
                "query": row["query"],
                "title": clean_text(normalize_title(item.get("title"))),
                "year": year_from_crossref(item),
                "doi": item.get("DOI"),
                "url": item.get("URL") or (f"https://doi.org/{item['DOI']}" if item.get("DOI") else ""),
                "venue": clean_text(normalize_title(item.get("container-title"))),
                "cited_by_count": int(item.get("is-referenced-by-count") or 0),
                "abstract": clean_text(item.get("abstract"))[:1200],
                "project_use": row["project_use"],
                "reference_class": "classic_model_method",
            }
        )
    return records, []


async def fetch_all_async() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    headers = {"User-Agent": "park-commercial-site-selection-simulation/1.0 (mailto:local@example.invalid)"}
    semaphore = asyncio.Semaphore(CONCURRENCY)
    all_records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    async with httpx.AsyncClient(headers=headers, timeout=35, follow_redirects=True) as client:
        async def run_one(index: int, row: dict[str, str]) -> None:
            async with semaphore:
                print(f"[{index}/{len(CLASSIC_QUERY_ROWS)}] {row['layer']} / {row['query']}")
                openalex_rows, openalex_errors = await fetch_openalex_async(client, row)
                crossref_rows, crossref_errors = await fetch_crossref_async(client, row)
                all_records.extend(openalex_rows)
                all_records.extend(crossref_rows)
                errors.extend(openalex_errors)
                errors.extend(crossref_errors)

        await asyncio.gather(*(run_one(index, row) for index, row in enumerate(CLASSIC_QUERY_ROWS, start=1)))
    return all_records, errors


def score_record(record: dict[str, Any]) -> dict[str, Any]:
    text = " ".join(str(record.get(k) or "") for k in ["title", "abstract", "query", "venue"]).lower()
    method_hits = sum(
        1
        for pattern in [
            "agent",
            "simulation",
            "choice",
            "logit",
            "spatial",
            "huff",
            "gravity",
            "queue",
            "monte carlo",
            "sensitivity",
            "calibration",
            "pedestrian",
            "activity",
            "facility location",
            "digital twin",
            "gis",
        ]
        if pattern in text
    )
    year = int(record.get("year") or 0)
    cited = int(record.get("cited_by_count") or 0)
    doi_bonus = 8 if record.get("doi") else 0
    classic_bonus = 18 if 1950 <= year <= 2018 else 0
    citation_bonus = min(25, cited // 100)
    score = method_hits * 6 + classic_bonus + citation_bonus + doi_bonus
    record["model_reference_score"] = score
    record["quality_reason"] = (
        f"方法命中 {method_hits} 类；引用数 {cited}；"
        f"{'有 DOI；' if record.get('doi') else ''}"
        "作为模型/计算骨架参考，不直接写入客户结论。"
    )
    return record


def dedupe(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for record in records:
        title = clean_text(record.get("title")).lower()
        if not title:
            continue
        key = clean_text(record.get("doi") or title).lower()
        if not key:
            continue
        current = by_key.get(key)
        if current is None or float(record.get("model_reference_score") or 0) > float(current.get("model_reference_score") or 0):
            by_key[key] = record
    rows = list(by_key.values())
    rows.sort(key=lambda item: (float(item.get("model_reference_score") or 0), int(item.get("cited_by_count") or 0)), reverse=True)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    import csv

    fields = [
        "layer",
        "model_reference_score",
        "year",
        "title",
        "source",
        "venue",
        "doi",
        "url",
        "cited_by_count",
        "project_use",
        "quality_reason",
        "query",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    all_records, errors = asyncio.run(fetch_all_async())

    scored = [score_record(record) for record in all_records]
    usable = [
        record
        for record in scored
        if int(record.get("year") or 0) <= 2024
        and float(record.get("model_reference_score") or 0) >= 18
        and clean_text(record.get("title"))
    ]
    deduped = dedupe(usable)
    write_jsonl(OUTPUT_JSONL, deduped)
    write_csv(OUTPUT_CSV, deduped)

    verification = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "pass" if len(deduped) >= 80 and len(Counter(row["layer"] for row in deduped)) >= 8 else "needs_action",
        "query_count": len(CLASSIC_QUERY_ROWS),
        "raw_total": len(all_records),
        "usable_total": len(usable),
        "deduped_total": len(deduped),
        "layer_counts": dict(Counter(row["layer"] for row in deduped)),
        "source_counts": dict(Counter(row["source"] for row in deduped)),
        "files": {
            "classic_jsonl": str(OUTPUT_JSONL.relative_to(ROOT)),
            "classic_csv": str(OUTPUT_CSV.relative_to(ROOT)),
        },
        "errors": errors[:50],
        "rule": "经典理论只作为模型骨架和方法边界参考；客户结论仍以本地证据、近年核心库和可复核计算为准。",
    }
    VERIFY_JSON.write_text(json.dumps(verification, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verification, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
