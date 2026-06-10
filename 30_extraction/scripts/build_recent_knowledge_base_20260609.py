from __future__ import annotations

import csv
import json
import math
import re
import time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "10_research" / "recent_knowledge_base_20260609"
QUALITY_DIR = ROOT / "40_quality_evidence"

RAW_OPENALEX = OUT_DIR / "raw_openalex_20260609.jsonl"
RAW_CROSSREF = OUT_DIR / "raw_crossref_20260609.jsonl"
RAW_SEMANTIC = OUT_DIR / "raw_semantic_scholar_20260609.jsonl"
RAW_ARXIV = OUT_DIR / "raw_arxiv_20260609.jsonl"
QUERY_MATRIX = OUT_DIR / "query_matrix_20260609.json"
SCREENED_JSONL = OUT_DIR / "screened_knowledge_base_20260609.jsonl"
SCREENED_CSV = OUT_DIR / "screened_knowledge_base_20260609.csv"
LANDING_CSV = OUT_DIR / "project_landing_register_20260609.csv"
SUMMARY_MD = OUT_DIR / "knowledge_base_summary_20260609.md"
VERIFY_JSON = QUALITY_DIR / "recent_knowledge_base_verification_20260609.json"

MIN_YEAR = 2025
OPENALEX_PER_PAGE = 60
OPENALEX_PAGES = 1
CROSSREF_ROWS = 60
SEMANTIC_LIMIT = 30
ARXIV_LIMIT = 40
TARGET_SCREENED = 1000
MIN_QUERY_COUNT = 160
MIN_SOURCE_COUNT = 2


THEMES: dict[str, dict[str, Any]] = {
    "spatial_site_selection": {
        "landing": "空间选址、节点比较、可达性与竞品供给解释",
        "queries": [
            "commercial site selection GIS multi criteria decision making",
            "retail location choice spatial interaction Huff model",
            "location allocation urban retail accessibility POI",
            "urban commercial land use location choice machine learning",
            "point of interest retail site selection urban analytics",
            "gravity model retail location consumer choice",
            "MCDM AHP TOPSIS retail site selection GIS",
            "catchment area accessibility retail location modeling",
            "commercial facility location allocation pedestrian accessibility",
            "urban amenity location optimization POI big data",
        ],
    },
    "human_mobility_behavior": {
        "landing": "客流、活动链、停留、路线、分时段行为约束",
        "queries": [
            "human mobility modeling activity chain urban simulation",
            "pedestrian flow visitor behavior urban park simulation",
            "mobile phone data human mobility urban consumption behavior",
            "footfall prediction point of interest urban analytics",
            "time geography activity based travel demand model",
            "urban mobility digital twin pedestrian simulation",
            "visitor flow forecasting tourism recreation park",
            "agent based pedestrian behavior public space",
            "large scale human mobility prediction urban data",
            "origin destination mobility POI visit prediction",
        ],
    },
    "agent_llm_simulation": {
        "landing": "Agent Bank、人群状态、行为程序、LLM 约束、低成本模型边界",
        "queries": [
            "large language model agent based simulation urban mobility",
            "generative agents social simulation human behavior",
            "LLM agent simulation decision making environment",
            "agent based model reinforcement learning urban planning",
            "digital twin city simulation LLM agents",
            "multi agent simulation human behavior large language models",
            "LLM for activity based travel demand modeling",
            "agentic AI urban simulation GIS",
            "foundation model human mobility simulation",
            "synthetic population agent based urban simulation",
        ],
    },
    "park_recreation_tourism": {
        "landing": "公园商业、公园游憩、公共空间、游客体验与经营边界",
        "queries": [
            "urban park visitor behavior commercial services",
            "park recreation demand visitor satisfaction concession",
            "public park commercial facility planning",
            "green space tourism visitor consumption behavior",
            "urban park recreation service demand forecasting",
            "park amenity planning visitor experience",
            "public space retail recreation behavior",
            "cultural tourism park commercial development",
            "urban green space accessibility visitor behavior",
            "park concession management visitor services",
        ],
    },
    "retail_operations_revenue": {
        "landing": "业态组合、价格带、收益/成本、试运营、转化率与复购",
        "queries": [
            "retail demand forecasting consumer behavior location analytics",
            "retail revenue management pricing foot traffic",
            "store choice model consumer behavior urban retail",
            "consumer spending prediction POI mobility data",
            "experience economy retail service design public space",
            "pop up retail location strategy urban",
            "food beverage retail location demand forecasting",
            "sports retail wellness service consumer demand",
            "cultural creative retail tourism consumer behavior",
            "retail conversion rate footfall dwell time",
        ],
    },
    "real_world_constraints": {
        "landing": "天气、季节、收入、人口、合规、安全、舆情和真实落地约束",
        "queries": [
            "weather seasonality outdoor recreation visitor behavior",
            "income demographics leisure consumption urban services",
            "urban park safety fire regulation commercial operation",
            "public space governance commercial activity regulation",
            "food service licensing public park concession",
            "noise complaints night economy urban park",
            "climate weather effects pedestrian retail demand",
            "demographic segmentation leisure service demand",
            "community acceptance public space commercial development",
            "risk assessment urban commercial facility planning",
        ],
    },
    "decision_reporting_methods": {
        "landing": "证据链、商业报告、解释型推荐、多方案评审与不确定性表达",
        "queries": [
            "explainable decision support system site selection",
            "evidence based decision support urban planning AI",
            "multi criteria decision support commercial planning",
            "human centered AI decision support business reporting",
            "uncertainty communication decision support systems",
            "recommendation explanation decision support urban planning",
            "simulation based decision support retail planning",
            "business intelligence geospatial decision support",
            "AI assisted planning decision support evidence",
            "scenario planning urban commercial development",
        ],
    },
}

EXPANDED_THEMES: dict[str, dict[str, Any]] = {
    "cad_bim_gis_digital_twin": {
        "landing": "CAD/DWG、BIM、GIS、数字孪生和可量测空间转换",
        "queries": [
            "BIM GIS integration urban digital twin facility planning",
            "CAD GIS conversion building footprint spatial analysis",
            "urban digital twin public space facility simulation",
            "BIM to GIS semantic interoperability urban planning",
            "digital twin for urban park planning simulation",
            "geospatial data quality building footprint extraction planning",
            "scan to BIM GIS urban facility management",
            "computer aided design GIS spatial decision support",
            "building information modelling public space operations",
            "3D city model urban facility location analysis",
        ],
    },
    "simulation_stack_persona_abm_mc": {
        "landing": "Persona、活动链、ABM/Mesa、离散选择、队列容量、Monte Carlo 和校准验证",
        "queries": [
            "agent based modeling park visitor behavior simulation",
            "agent based model visitor flow urban park",
            "park visitor agent based simulation trajectory",
            "tourism visitor agent based model itinerary",
            "synthetic population urban mobility activity based model",
            "persona based simulation consumer behavior large language model",
            "LLM agent persona simulation human mobility",
            "generative agents visitor behavior simulation",
            "activity based travel demand synthesis agent based model",
            "activity chain visitor flow urban park",
            "time geography visitor behavior park simulation",
            "dwell time activity chain retail consumer movement",
            "pedestrian simulation social force model public space",
            "pedestrian simulation cellular automata urban park",
            "multi agent pedestrian simulation public space crowd",
            "microsimulation pedestrian flow commercial street",
            "crowd simulation queue capacity public space retail",
            "queueing simulation food beverage service capacity",
            "discrete event simulation cafe service throughput",
            "SimPy discrete event simulation queue service capacity",
            "Mesa agent based modeling urban simulation",
            "Mesa Python agent based model social simulation",
            "agent based simulation calibration validation urban mobility",
            "ABM calibration validation pedestrian model",
            "sensitivity analysis agent based model visitor behavior",
            "Monte Carlo simulation retail demand uncertainty",
            "Monte Carlo simulation visitor flow revenue forecast",
            "uncertainty quantification agent based simulation urban",
            "stochastic simulation park visitor demand forecasting",
            "scenario based simulation visitor flow public space",
            "baseline pilot full scenario Monte Carlo simulation retail",
            "coffee kiosk demand forecasting foot traffic simulation",
            "outdoor food beverage demand forecasting park visitors",
            "retail conversion rate footfall dwell time model",
            "store choice model visitor spending park recreation",
            "destination choice model urban park visitor",
            "discrete choice model recreation demand park",
            "multinomial logit park recreation demand",
            "nested logit visitor destination choice tourism",
            "Huff model retail location visitor flow",
            "gravity model store choice consumer movement",
            "agent based model route choice pedestrian attraction",
            "route choice model park visitor pedestrian",
            "spatial interaction model retail site visitor flow",
            "Bayesian calibration Monte Carlo simulation demand",
            "Bayesian structural time series retail demand simulation",
            "probabilistic decision support retail site selection",
            "simulation optimization service capacity retail location",
            "Monte Carlo sensitivity analysis commercial site selection",
            "agent based digital twin visitor flow simulation",
            "urban digital twin agent based pedestrian simulation",
            "human behavior simulation social infrastructure park",
            "data driven agent based spatio temporal behavior modeling",
            "spatio temporal human behavior modeling park simulation",
            "visitor typology micro zoning recreation site",
            "visitor segmentation willingness to pay urban recreation",
            "mobile phone data park visitor supply demand mismatch",
            "GPS tracks tourist spatial temporal behavior park",
            "LLM structured output JSON schema validation agent simulation",
            "LLM guardrails structured JSON evidence grounded generation",
            "RAG faithfulness evaluation agent decision support",
            "agent traces execution provenance LLM simulation",
            "human in the loop validation LLM agent simulation",
            "model risk management LLM decision support simulation",
            "operational digital twin queue simulation retail service",
            "capacity planning visitor attraction queue management simulation",
            "service time queue model food beverage operations",
            "crowd density pedestrian comfort public space simulation",
            "public space agent based simulation design optimization",
            "urban walking space agent based simulation optimization",
            "social force model pedestrian grouping avoidance simulation",
            "cellular automata pedestrian flow evacuation simulation",
            "agent based model commercial street pedestrian crossing",
            "multi agent simulation ultra high density pedestrian crowd",
        ],
    },
    "weather_season_event_demand": {
        "landing": "天气、季节、活动事件、微气候与分时需求波动",
        "queries": [
            "weather effects retail foot traffic demand forecasting",
            "seasonality outdoor recreation visitor demand modeling",
            "microclimate thermal comfort pedestrian activity public space",
            "event driven crowd flow urban park visitor behavior",
            "rain temperature effects consumer mobility retail visits",
            "seasonal demand forecasting leisure service operations",
            "urban heat comfort park visitor behavior simulation",
            "weather aware pedestrian flow prediction",
            "festival event tourism visitor flow forecasting",
            "climate adaptation outdoor commercial public space",
        ],
    },
    "demographics_income_market_segmentation": {
        "landing": "人口、收入、家庭结构、客群画像和消费能力约束",
        "queries": [
            "income demographics leisure consumption behavior urban",
            "socioeconomic segmentation retail location analytics",
            "household income consumer spending urban amenities",
            "age group park recreation demand segmentation",
            "family leisure consumption public space services",
            "older adults urban park accessibility service demand",
            "youth sports wellness consumption urban services",
            "consumer expenditure mobility data urban retail demand",
            "residential demographics commercial site selection",
            "market segmentation geospatial retail planning",
        ],
    },
    "safety_regulation_public_governance": {
        "landing": "消防、食品许可、公共空间治理、安全和投诉约束",
        "queries": [
            "public space commercial activity regulation governance",
            "food service licensing public park concession management",
            "fire safety risk assessment commercial facility planning",
            "crowd safety regulation public event urban park",
            "noise complaint night economy urban public space",
            "public park concession policy governance",
            "urban commercial facility safety accessibility regulation",
            "risk governance outdoor food beverage operations",
            "public acceptance commercial development urban green space",
            "emergency evacuation public space retail facility",
        ],
    },
    "operations_revenue_unit_economics": {
        "landing": "价格带、转化率、坪效、人效、库存、试运营和退出条件",
        "queries": [
            "retail unit economics footfall conversion rate",
            "food beverage revenue management demand forecasting",
            "pop up retail operations trial metrics",
            "retail inventory planning demand forecasting small business",
            "pricing strategy consumer choice urban retail",
            "service operations capacity planning queue retail",
            "retail store performance foot traffic dwell time",
            "tourism concession revenue management park",
            "commercial tenant mix optimization revenue",
            "business model validation public space retail",
        ],
    },
    "queue_crowd_capacity_operations": {
        "landing": "排队、拥挤、容量、动线、安全阈值和运营压力测试",
        "queries": [
            "queue simulation service capacity retail operations",
            "crowd density pedestrian simulation public space safety",
            "agent based crowd simulation evacuation retail",
            "capacity planning visitor attraction queue management",
            "pedestrian congestion simulation urban plaza",
            "service time queue model food beverage operations",
            "crowd flow bottleneck detection urban public space",
            "real time crowd management digital twin",
            "visitor capacity management recreation area",
            "pedestrian comfort crowd density public space",
        ],
    },
    "transport_accessibility_last_mile": {
        "landing": "地铁、停车、步行、自行车、最后一公里和出入口可达性",
        "queries": [
            "last mile accessibility retail location urban mobility",
            "metro station pedestrian accessibility commercial complex",
            "parking availability retail demand urban location",
            "bike pedestrian accessibility urban park visitors",
            "transit oriented retail location choice",
            "walkability public space commercial activity",
            "origin destination travel demand park accessibility",
            "multimodal accessibility urban amenity planning",
            "entrance gate accessibility visitor flow park",
            "pedestrian route choice retail location analysis",
        ],
    },
    "multi_criteria_optimization_uncertainty": {
        "landing": "多目标优化、MCDM、鲁棒性、不确定性和情景推演",
        "queries": [
            "multi objective optimization facility location uncertainty",
            "robust site selection multi criteria decision making GIS",
            "scenario analysis urban planning decision support",
            "uncertainty analysis retail location model",
            "sensitivity analysis commercial site selection",
            "Pareto optimization urban facility location",
            "Bayesian decision support site selection",
            "multi criteria decision analysis public facility planning",
            "explainable optimization urban planning decision support",
            "simulation optimization retail location planning",
        ],
    },
    "ai_evaluation_observability_guardrails": {
        "landing": "LLM/Agent 评估、可观测性、提示约束、风险检查和人工复核",
        "queries": [
            "LLM agent evaluation benchmark tool use reliability",
            "AI agent observability trace evaluation 2026",
            "large language model guardrails structured output validation",
            "LLM hallucination detection evidence grounded generation",
            "human in the loop AI decision support governance",
            "agentic AI workflow evaluation business process",
            "retrieval augmented generation citation faithfulness evaluation",
            "LLM simulation calibration validation human behavior",
            "AI generated report quality evaluation decision support",
            "model risk management generative AI applications",
        ],
    },
    "service_design_ai_workbench_ux": {
        "landing": "AI 工作台、客服端可用性、报告交互和人机协作界面",
        "queries": [
            "human centered AI interface decision support workbench",
            "conversational user interface business report generation",
            "AI workbench user experience design decision making",
            "human AI collaboration workflow interface design",
            "explainable AI dashboard user experience decision support",
            "agentic user interface design principles",
            "business intelligence dashboard UX decision support",
            "AI report generation interface human centered design",
            "trust calibration AI decision support interface",
            "professional services AI copilot workflow design",
        ],
    },
    "park_publicness_experience_equity": {
        "landing": "公园公共性、体验、公平性、亲子/银发/运动客群和非商业边界",
        "queries": [
            "urban park publicness commercial services visitor experience",
            "equitable urban green space planning older adults accessibility",
            "family friendly park recreation service demand",
            "sports recreation park visitor behavior services",
            "public space commercialization social equity",
            "urban green space service quality visitor satisfaction",
            "park amenity demand children families older adults",
            "inclusive public space commercial activity planning",
            "recreation experience economy urban park",
            "visitor typology urban park micro zoning",
        ],
    },
    "data_quality_evidence_chain": {
        "landing": "数据质量、证据链、可追溯、表格抽取、PDF/CAD/POI 数据治理",
        "queries": [
            "data quality assessment geospatial decision support",
            "evidence based urban planning data provenance",
            "PDF table extraction quality evaluation",
            "geospatial data provenance urban analytics",
            "data lineage decision support system urban planning",
            "information extraction validation business reports",
            "data fusion POI mobility survey urban analytics",
            "knowledge graph evidence chain decision support",
            "auditability AI decision support system",
            "traceable analytics urban planning evidence",
        ],
    },
    "official_statistics_open_data_context": {
        "landing": "官方统计、开放数据、人口收入、消费、旅游和城市治理资料接入",
        "queries": [
            "official statistics consumer spending urban retail analysis",
            "open data urban planning commercial site selection",
            "census demographics retail demand forecasting",
            "tourism statistics visitor consumption urban park",
            "open government data mobility urban analytics",
            "income distribution consumer expenditure spatial analysis",
            "urban big data open data decision support planning",
            "public data integration retail location analytics",
            "small area statistics commercial planning",
            "administrative data urban service demand forecasting",
        ],
    },
}

THEMES.update(EXPANDED_THEMES)


CATEGORY_PATTERNS = {
    "spatial_gis": r"\bGIS\b|geospatial|spatial|location|site selection|location allocation|accessibility|catchment|Huff|gravity|POI|point of interest|MCDM|AHP|TOPSIS",
    "mobility_flow": r"mobility|pedestrian|footfall|visitor flow|travel demand|origin destination|activity chain|dwell time|route choice|walkability",
    "agent_simulation": r"agent-based|agent based|multi-agent|LLM|large language model|generative agents|digital twin|simulation|reinforcement learning|synthetic population",
    "park_recreation": r"park|green space|recreation|tourism|visitor satisfaction|public space|amenity|concession",
    "retail_business": r"retail|commercial|consumer|spending|pricing|revenue|store choice|food beverage|conversion|service design",
    "real_world_context": r"weather|season|climate|income|demographic|population|safety|fire|license|regulation|governance|noise|complaint|risk",
    "decision_support": r"decision support|explainable|evidence-based|scenario|uncertainty|recommendation|business intelligence|multi criteria",
    "cad_bim_data": r"\bBIM\b|\bCAD\b|\bDWG\b|digital twin|3D city|building footprint|geospatial data quality|interoperability",
    "socioeconomic_market": r"socioeconomic|household|income|expenditure|segmentation|market segmentation|census|residential demographics",
    "weather_event": r"weather|seasonality|microclimate|thermal comfort|event driven|festival|rain|temperature|climate adaptation",
    "safety_regulation": r"fire safety|licensing|regulation|governance|noise complaint|emergency evacuation|public acceptance|risk governance",
    "operations_capacity": r"unit economics|capacity planning|queue|service time|inventory|tenant mix|revenue management|pricing strategy|trial metrics",
    "ai_guardrails": r"guardrails|hallucination|faithfulness|observability|trace|human in the loop|model risk|structured output|RAG",
    "data_evidence_quality": r"data quality|provenance|lineage|auditability|evidence chain|information extraction|data fusion|open data",
    "persona_activity_model": r"persona|synthetic population|activity chain|activity-based|activity based|time geography|visitor typology|itinerary|dwell time",
    "choice_model": r"discrete choice|multinomial logit|nested logit|destination choice|store choice|Huff|gravity model|spatial interaction",
    "abm_pedestrian_engine": r"\bMesa\b|agent-based|agent based|ABM|social force|cellular automata|pedestrian simulation|crowd simulation|microsimulation",
    "monte_carlo_uncertainty": r"Monte Carlo|uncertainty quantification|stochastic simulation|probabilistic|P5|P50|P95|sensitivity analysis|Bayesian calibration",
}

NEGATIVE_PATTERNS = r"molecular|protein|gene|cancer|clinical trial|battery|quantum|wireless sensor only|image segmentation only"


def reconstruct_abstract(index: dict[str, list[int]] | None) -> str:
    if not index:
        return ""
    words: list[tuple[int, str]] = []
    for word, positions in index.items():
        for pos in positions:
            words.append((pos, word))
    return " ".join(word for _, word in sorted(words))


def normalize_title(title: Any) -> str:
    if isinstance(title, list):
        return " ".join(str(item) for item in title if item)
    return str(title or "").strip()


def safe_year(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, dict):
        parts = value.get("date-parts")
        if parts and parts[0]:
            return safe_year(parts[0][0])
    if isinstance(value, list) and value:
        return safe_year(value[0])
    if isinstance(value, str):
        match = re.search(r"(20\d{2})", value)
        if match:
            return int(match.group(1))
    return None


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def fetch_openalex(client: httpx.Client, theme: str, query: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cursor = "*"
    for page in range(OPENALEX_PAGES):
        params = {
            "search": query,
            "filter": f"from_publication_date:{MIN_YEAR}-01-01,type:article",
            "per-page": OPENALEX_PER_PAGE,
            "cursor": cursor,
            "select": "id,doi,title,display_name,publication_year,publication_date,cited_by_count,abstract_inverted_index,authorships,primary_location,locations,concepts,keywords,open_access,type,type_crossref",
        }
        response = client.get("https://api.openalex.org/works", params=params)
        response.raise_for_status()
        payload = response.json()
        for item in payload.get("results", []):
            item["_source"] = "openalex"
            item["_theme"] = theme
            item["_query"] = query
            rows.append(item)
        cursor = payload.get("meta", {}).get("next_cursor")
        if not cursor:
            break
        time.sleep(0.08)
    return rows


def fetch_crossref(client: httpx.Client, theme: str, query: str) -> list[dict[str, Any]]:
    params = {
        "query.bibliographic": query,
        "filter": f"from-pub-date:{MIN_YEAR}-01-01,type:journal-article",
        "rows": CROSSREF_ROWS,
        "select": "DOI,title,published-print,published-online,published,container-title,is-referenced-by-count,subject,abstract,URL,type",
    }
    response = client.get("https://api.crossref.org/works", params=params)
    response.raise_for_status()
    rows = []
    for item in response.json().get("message", {}).get("items", []):
        item["_source"] = "crossref"
        item["_theme"] = theme
        item["_query"] = query
        rows.append(item)
    time.sleep(0.08)
    return rows


def fetch_semantic(client: httpx.Client, theme: str, query: str) -> list[dict[str, Any]]:
    params = {
        "query": query,
        "year": f"{MIN_YEAR}-2026",
        "limit": SEMANTIC_LIMIT,
        "fields": "title,abstract,year,citationCount,venue,externalIds,authors,url,isOpenAccess,fieldsOfStudy,publicationTypes,publicationDate",
    }
    response = client.get("https://api.semanticscholar.org/graph/v1/paper/search", params=params)
    if response.status_code in {403, 429, 500, 502, 503}:
        time.sleep(1.0)
        return []
    response.raise_for_status()
    rows = []
    for item in response.json().get("data", []):
        item["_source"] = "semantic_scholar"
        item["_theme"] = theme
        item["_query"] = query
        rows.append(item)
    time.sleep(0.25)
    return rows


def fetch_arxiv(client: httpx.Client, theme: str, query: str) -> list[dict[str, Any]]:
    search_query = "all:" + " AND ".join(f'"{part}"' for part in query.split()[:5])
    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": ARXIV_LIMIT,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    response = client.get("https://export.arxiv.org/api/query", params=params)
    if response.status_code >= 400:
        return []
    root = ET.fromstring(response.text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    rows = []
    for entry in root.findall("atom:entry", ns):
        published = entry.findtext("atom:published", default="", namespaces=ns)
        year = safe_year(published)
        if not year or year < MIN_YEAR:
            continue
        rows.append(
            {
                "_source": "arxiv",
                "_theme": theme,
                "_query": query,
                "id": entry.findtext("atom:id", default="", namespaces=ns),
                "title": clean_text(entry.findtext("atom:title", default="", namespaces=ns)),
                "abstract": clean_text(entry.findtext("atom:summary", default="", namespaces=ns)),
                "year": year,
                "published": published,
                "authors": [clean_text(author.findtext("atom:name", default="", namespaces=ns)) for author in entry.findall("atom:author", ns)],
                "url": entry.findtext("atom:id", default="", namespaces=ns),
            }
        )
    time.sleep(0.25)
    return rows


def flatten_record(item: dict[str, Any]) -> dict[str, Any]:
    source = item.get("_source", "")
    theme = item.get("_theme", "")
    query = item.get("_query", "")
    if source == "openalex":
        title = normalize_title(item.get("title") or item.get("display_name"))
        abstract = reconstruct_abstract(item.get("abstract_inverted_index"))
        doi = item.get("doi") or ""
        url = doi or item.get("id") or ""
        year = safe_year(item.get("publication_year"))
        cited = int(item.get("cited_by_count") or 0)
        venue = ((item.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
        concepts = [c.get("display_name", "") for c in item.get("concepts", [])[:10] if isinstance(c, dict)]
        keywords = [k.get("display_name", "") for k in item.get("keywords", [])[:10] if isinstance(k, dict)]
        authors = [a.get("author", {}).get("display_name", "") for a in item.get("authorships", [])[:6] if isinstance(a, dict)]
    elif source == "crossref":
        title = normalize_title(item.get("title"))
        abstract = clean_text(re.sub("<[^>]+>", " ", item.get("abstract") or ""))
        doi = item.get("DOI") or ""
        url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")
        year = safe_year(item.get("published-online") or item.get("published-print") or item.get("published"))
        cited = int(item.get("is-referenced-by-count") or 0)
        venue = normalize_title(item.get("container-title"))
        concepts = list(item.get("subject") or [])[:10]
        keywords = []
        authors = []
    elif source == "semantic_scholar":
        title = normalize_title(item.get("title"))
        abstract = clean_text(item.get("abstract") or "")
        external = item.get("externalIds") or {}
        doi = external.get("DOI") or ""
        url = item.get("url") or (f"https://doi.org/{doi}" if doi else "")
        year = safe_year(item.get("year") or item.get("publicationDate"))
        cited = int(item.get("citationCount") or 0)
        venue = item.get("venue") or ""
        concepts = list(item.get("fieldsOfStudy") or [])[:10]
        keywords = []
        authors = [a.get("name", "") for a in item.get("authors", [])[:6] if isinstance(a, dict)]
    else:
        title = normalize_title(item.get("title"))
        abstract = clean_text(item.get("abstract") or "")
        doi = ""
        url = item.get("url") or item.get("id") or ""
        year = safe_year(item.get("year") or item.get("published"))
        cited = 0
        venue = "arXiv"
        concepts = ["Computer Science", "AI"] if "LLM" in query or "agent" in query.lower() else []
        keywords = []
        authors = item.get("authors", [])[:6]

    return {
        "source": source,
        "theme": theme,
        "query": query,
        "title": clean_text(title),
        "abstract": clean_text(abstract),
        "year": year,
        "doi": doi.lower().replace("https://doi.org/", ""),
        "url": url,
        "venue": clean_text(venue),
        "cited_by_count": cited,
        "authors": authors,
        "concepts": concepts,
        "keywords": keywords,
    }


def record_key(record: dict[str, Any]) -> str:
    if record.get("doi"):
        return f"doi:{record['doi'].lower()}"
    if record.get("url"):
        return f"url:{record['url'].lower()}"
    title = re.sub(r"[^a-z0-9]+", " ", record.get("title", "").lower()).strip()
    return f"title:{title[:160]}"


def score_record(record: dict[str, Any]) -> dict[str, Any]:
    title = record.get("title", "")
    abstract = record.get("abstract", "")
    text = f"{title} {abstract} {' '.join(record.get('concepts', []))} {' '.join(record.get('keywords', []))}"
    text_lower = text.lower()
    category_hits = {
        category: bool(re.search(pattern, text, re.IGNORECASE))
        for category, pattern in CATEGORY_PATTERNS.items()
    }
    hit_count = sum(category_hits.values())
    year = record.get("year") or 0
    score = 0.0
    score += 26 if year >= 2026 else 16 if year == 2025 else -20
    score += min(20, hit_count * 5)
    score += 10 if any(category_hits.get(c) for c in ("spatial_gis", "mobility_flow", "agent_simulation")) else 0
    score += 8 if any(category_hits.get(c) for c in ("retail_business", "park_recreation", "real_world_context")) else 0
    score += 6 if any(
        category_hits.get(c)
        for c in (
            "cad_bim_data",
            "socioeconomic_market",
            "weather_event",
            "safety_regulation",
            "operations_capacity",
            "ai_guardrails",
            "data_evidence_quality",
            "persona_activity_model",
            "choice_model",
            "abm_pedestrian_engine",
            "monte_carlo_uncertainty",
        )
    ) else 0
    score += 5 if record.get("doi") else 0
    score += 5 if len(abstract) >= 300 else 2 if abstract else 0
    score += min(10, math.log1p(max(int(record.get("cited_by_count") or 0), 0)) * 2.5)
    if re.search(NEGATIVE_PATTERNS, text_lower, re.IGNORECASE):
        score -= 30
    if len(title) < 12:
        score -= 10
    if year and year < MIN_YEAR:
        score -= 30

    if score >= 62:
        tier = "A_directly_actionable"
    elif score >= 46:
        tier = "B_project_relevant"
    elif score >= 32:
        tier = "C_contextual_support"
    else:
        tier = "reject_low_relevance"

    landing = []
    if category_hits["spatial_gis"]:
        landing.append("空间节点与 GIS/POI/可达性")
    if category_hits["mobility_flow"]:
        landing.append("客流、活动链与路线")
    if category_hits["agent_simulation"]:
        landing.append("Agent/LLM/仿真方法")
    if category_hits["park_recreation"]:
        landing.append("公园游憩与公共空间")
    if category_hits["retail_business"]:
        landing.append("商业业态、价格与转化")
    if category_hits["real_world_context"]:
        landing.append("天气、收入、人口、合规等现实约束")
    if category_hits["decision_support"]:
        landing.append("决策支持与报告表达")
    if category_hits.get("cad_bim_data"):
        landing.append("CAD/GIS/数字孪生与空间转换")
    if category_hits.get("socioeconomic_market"):
        landing.append("人口收入与客群市场分层")
    if category_hits.get("weather_event"):
        landing.append("天气季节活动与微气候")
    if category_hits.get("safety_regulation"):
        landing.append("合规安全治理与投诉约束")
    if category_hits.get("operations_capacity"):
        landing.append("运营收益容量与试运营指标")
    if category_hits.get("ai_guardrails"):
        landing.append("AI 约束评估与人工复核")
    if category_hits.get("data_evidence_quality"):
        landing.append("数据质量证据链与可追溯")
    if category_hits.get("persona_activity_model"):
        landing.append("Persona 与活动链建模")
    if category_hits.get("choice_model"):
        landing.append("离散选择与消费/目的地选择")
    if category_hits.get("abm_pedestrian_engine"):
        landing.append("ABM/Mesa 与步行仿真引擎")
    if category_hits.get("monte_carlo_uncertainty"):
        landing.append("Monte Carlo 与敏感性分析")

    rejection_reason = ""
    if tier == "reject_low_relevance":
        rejection_reason = "年份、摘要或主题命中不足；暂不进入项目知识库。"
    return {
        "score": round(score, 2),
        "tier": tier,
        "category_hits": category_hits,
        "category_count": hit_count,
        "project_landing": landing,
        "rejection_reason": rejection_reason,
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


def collect() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    headers = {"User-Agent": "park-commercial-site-selection-simulation/1.0 (mailto:local@example.invalid)"}
    openalex_rows: list[dict[str, Any]] = []
    crossref_rows: list[dict[str, Any]] = []
    semantic_rows: list[dict[str, Any]] = []
    arxiv_rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    query_rows = []

    with httpx.Client(headers=headers, timeout=45, follow_redirects=True) as client:
        for theme, info in THEMES.items():
            for query in info["queries"]:
                query_rows.append({"theme": theme, "query": query, "landing": info["landing"]})
                try:
                    openalex_rows.extend(fetch_openalex(client, theme, query))
                except Exception as exc:
                    errors.append({"source": "openalex", "theme": theme, "query": query, "error": repr(exc)})
                try:
                    crossref_rows.extend(fetch_crossref(client, theme, query))
                except Exception as exc:
                    errors.append({"source": "crossref", "theme": theme, "query": query, "error": repr(exc)})

        semantic_queries = [info["queries"][0] for info in THEMES.values()] + [info["queries"][1] for info in THEMES.values()]
        for query in semantic_queries:
            theme = next((name for name, info in THEMES.items() if query in info["queries"]), "mixed")
            try:
                semantic_rows.extend(fetch_semantic(client, theme, query))
            except Exception as exc:
                errors.append({"source": "semantic_scholar", "theme": theme, "query": query, "error": repr(exc)})

        arxiv_queries = [
            "large language model agent simulation",
            "human mobility simulation",
            "digital twin city simulation",
            "agent based urban planning",
            "LLM decision support",
            "pedestrian simulation urban",
            "RAG evaluation faithfulness",
            "multi agent urban simulation",
            "human behavior generative agents",
            "LLM observability trace evaluation",
        ]
        for query in arxiv_queries:
            try:
                arxiv_rows.extend(fetch_arxiv(client, "agent_llm_simulation", query))
            except Exception as exc:
                errors.append({"source": "arxiv", "theme": "agent_llm_simulation", "query": query, "error": repr(exc)})

    write_jsonl(RAW_OPENALEX, openalex_rows)
    write_jsonl(RAW_CROSSREF, crossref_rows)
    write_jsonl(RAW_SEMANTIC, semantic_rows)
    write_jsonl(RAW_ARXIV, arxiv_rows)
    QUERY_MATRIX.write_text(json.dumps({"themes": THEMES, "queries": query_rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    raw = openalex_rows + crossref_rows + semantic_rows + arxiv_rows
    meta = {
        "raw_counts": {
            "openalex": len(openalex_rows),
            "crossref": len(crossref_rows),
            "semantic_scholar": len(semantic_rows),
            "arxiv": len(arxiv_rows),
            "total": len(raw),
        },
        "errors": errors,
        "query_count": len(query_rows),
    }
    return raw, meta


def screen(raw_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    source_seen: defaultdict[str, set[str]] = defaultdict(set)
    for item in raw_rows:
        record = flatten_record(item)
        if not record.get("title"):
            continue
        key = record_key(record)
        scored = {**record, **score_record(record)}
        if key in by_key:
            old = by_key[key]
            old["source"] = "+".join(sorted(set(str(old["source"]).split("+")) | {record["source"]}))
            old["source_count"] = len(old["source"].split("+"))
            old["theme"] = "+".join(sorted(set(str(old["theme"]).split("+")) | {record["theme"]}))
            old["query"] = old["query"] + " || " + record["query"] if record["query"] not in old["query"] else old["query"]
            if scored["score"] > old["score"]:
                for field in ["score", "tier", "category_hits", "category_count", "project_landing", "rejection_reason", "abstract", "venue", "cited_by_count"]:
                    old[field] = scored[field]
        else:
            scored["source_count"] = 1
            by_key[key] = scored
        source_seen[key].add(record["source"])

    all_records = list(by_key.values())
    screened = [r for r in all_records if r["tier"] != "reject_low_relevance"]
    rejected = [r for r in all_records if r["tier"] == "reject_low_relevance"]
    screened.sort(key=lambda r: (r["score"], r.get("year") or 0, r.get("cited_by_count") or 0), reverse=True)
    rejected.sort(key=lambda r: (r["score"], r.get("year") or 0), reverse=True)

    stats = {
        "dedup_total": len(all_records),
        "screened_total": len(screened),
        "rejected_total": len(rejected),
        "tier_counts": dict(Counter(r["tier"] for r in screened)),
        "year_counts": dict(Counter(str(r.get("year")) for r in screened)),
        "theme_counts": dict(Counter(theme for r in screened for theme in str(r["theme"]).split("+"))),
        "category_counts": dict(Counter(cat for r in screened for cat, hit in r["category_hits"].items() if hit)),
        "source_counts": dict(Counter(src for r in screened for src in str(r["source"]).split("+"))),
    }
    return screened, rejected, stats


def build_landing_rows(screened: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in screened:
        for landing in row.get("project_landing", []) or ["未分类"]:
            grouped[landing].append(row)
    for landing, items in sorted(grouped.items(), key=lambda kv: len(kv[1]), reverse=True):
        top = sorted(items, key=lambda r: r["score"], reverse=True)[:20]
        rows.append(
            {
                "landing_area": landing,
                "screened_count": len(items),
                "tier_a_count": sum(1 for item in items if item["tier"] == "A_directly_actionable"),
                "top_titles": " | ".join(item["title"][:90] for item in top[:8]),
                "project_use": landing,
                "how_to_apply": landing_to_action(landing),
            }
        )
    return rows


def landing_to_action(landing: str) -> str:
    mapping = {
        "空间节点与 GIS/POI/可达性": "约束地图/节点比较：距离、可达、POI 供给和竞品密度不能单独变成收益结论。",
        "客流、活动链与路线": "约束仿真：先生成分时段活动链和路线，再计算停留与消费触发。",
        "Agent/LLM/仿真方法": "约束 DeepSeek：只做候选生成、解释和初筛；概率/排名/收益必须由规则和证据复核。",
        "公园游憩与公共空间": "约束公园商业：公共性、游客体验和游憩需求优先，不把普通商场逻辑硬套公园。",
        "商业业态、价格与转化": "约束报告建议：节点建议必须包含价格带、转化触发、试运营指标和退出条件。",
        "天气、收入、人口、合规等现实约束": "约束真实世界落地：把收入、天气、人口、许可、安全和舆情列为决策前置变量。",
        "决策支持与报告表达": "约束报告结构：写多方案、依据、不可判断边界和下一步动作，不写模板化空话。",
        "CAD/GIS/数字孪生与空间转换": "约束 CAD/PDF/DWG 处理：先记录坐标、比例尺、图层和转换误差，再进入面积、动线和节点模拟。",
        "人口收入与客群市场分层": "约束客群模型：把亲子、银发、运动、通勤、游客和周边居民分开，不用单一平均收入替代真实需求。",
        "天气季节活动与微气候": "约束分时段预测：把晴雨、冷热、节假日、活动日和季节波动作为需求乘子，不写成固定客流。",
        "合规安全治理与投诉约束": "约束落地建议：食品、消防、噪声、夜间运营和公共空间治理必须成为方案边界和退出条件。",
        "运营收益容量与试运营指标": "约束商业建议：每个建议要能落到价格带、转化触发、容量、人效、库存和试运营复盘指标。",
        "AI 约束评估与人工复核": "约束 DeepSeek 和 Agent：只允许生成候选、解释、初筛和草案，最终排序必须经证据、schema 和人工复核。",
        "数据质量证据链与可追溯": "约束全链路：所有结论必须能回到 PDF/CAD/POI/表格/脚本输出，不能把工具日志写给客户。",
        "Persona 与活动链建模": "约束 Persona：三类客群只是底座，必须叠加频次、任务、同行结构、时段和停留活动链。",
        "离散选择与消费/目的地选择": "约束决策逻辑：目的地、活动和消费触发要用选择模型/效用逻辑表达，不用固定模板替代。",
        "ABM/Mesa 与步行仿真引擎": "约束轨迹层：Mesa 可作为实现工具，核心是 Agent 状态转移、路线、拥挤、热力和校准。",
        "Monte Carlo 与敏感性分析": "约束不确定性：P5/P50/P95 不只扰动日客流，还要扰动天气、转化率、客单价、客群比例和容量。",
    }
    return mapping.get(landing, "作为辅助背景，进入方法库但不直接生成项目结论。")


def write_outputs(screened: list[dict[str, Any]], rejected: list[dict[str, Any]], stats: dict[str, Any], meta: dict[str, Any]) -> None:
    fields = [
        "tier",
        "score",
        "year",
        "title",
        "source",
        "theme",
        "venue",
        "doi",
        "url",
        "cited_by_count",
        "category_count",
        "project_landing_text",
        "query",
        "abstract_excerpt",
    ]
    csv_rows = []
    for row in screened:
        csv_rows.append(
            {
                **row,
                "project_landing_text": "; ".join(row.get("project_landing", [])),
                "abstract_excerpt": row.get("abstract", "")[:500],
            }
        )
    write_jsonl(SCREENED_JSONL, screened)
    write_csv(SCREENED_CSV, csv_rows, fields)

    landing_rows = build_landing_rows(screened)
    write_csv(LANDING_CSV, landing_rows, ["landing_area", "screened_count", "tier_a_count", "top_titles", "project_use", "how_to_apply"])

    top_by_theme = {}
    for theme in THEMES:
        items = [r for r in screened if theme in str(r["theme"]).split("+")]
        top_by_theme[theme] = [
            {"title": r["title"], "year": r["year"], "score": r["score"], "url": r["url"]}
            for r in sorted(items, key=lambda r: r["score"], reverse=True)[:10]
        ]

    source_counts = stats.get("source_counts", {})
    source_diversity_ok = len(source_counts) >= MIN_SOURCE_COUNT and source_counts.get("openalex", 0) > 0
    query_matrix_ok = meta["query_count"] >= MIN_QUERY_COUNT
    tier_depth_ok = stats["screened_total"] >= TARGET_SCREENED and stats["tier_counts"].get("A_directly_actionable", 0) >= 80
    status = "pass" if tier_depth_ok and source_diversity_ok and query_matrix_ok else "needs_action"
    verify = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "target_screened": TARGET_SCREENED,
        "min_query_count": MIN_QUERY_COUNT,
        "min_source_count": MIN_SOURCE_COUNT,
        "min_year": MIN_YEAR,
        "raw_counts": meta["raw_counts"],
        "query_count": meta["query_count"],
        "query_matrix_ok": query_matrix_ok,
        "source_diversity_ok": source_diversity_ok,
        "tier_depth_ok": tier_depth_ok,
        "screening_stats": stats,
        "source_files": {
            "query_matrix": str(QUERY_MATRIX.relative_to(ROOT)),
            "screened_jsonl": str(SCREENED_JSONL.relative_to(ROOT)),
            "screened_csv": str(SCREENED_CSV.relative_to(ROOT)),
            "landing_csv": str(LANDING_CSV.relative_to(ROOT)),
        },
        "errors": meta["errors"][:200],
        "quality_rules": [
            "2026 优先，2025 兼容；2024 及更早默认不进入本轮筛选。",
            "筛选分数来自主题命中、年份、摘要完整度、DOI/来源、引用和项目落点。",
            "A/B/C 均为已筛选知识；reject_low_relevance 不进入项目知识库。",
            "知识库提供方法和约束，不直接把论文数字写成奥森结论。",
            f"检索矩阵必须不少于 {MIN_QUERY_COUNT} 条查询。",
            "通过必须至少两个来源入库，且 OpenAlex 必须真实贡献记录，避免单源假通过。",
        ],
    }
    VERIFY_JSON.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 近年知识库 2026-06-09",
        "",
        "## 结论",
        "",
        f"- 状态：{status}",
        f"- 原始候选：{meta['raw_counts']['total']}",
        f"- 去重后：{stats['dedup_total']}",
        f"- 筛选入库：{stats['screened_total']}",
        f"- A 档：{stats['tier_counts'].get('A_directly_actionable', 0)}",
        f"- B 档：{stats['tier_counts'].get('B_project_relevant', 0)}",
        f"- C 档：{stats['tier_counts'].get('C_contextual_support', 0)}",
        "",
        "## 主题覆盖",
        "",
    ]
    for key, count in sorted(stats["theme_counts"].items(), key=lambda kv: kv[1], reverse=True):
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## 项目落点", ""])
    for row in landing_rows:
        lines.append(f"- {row['landing_area']}：{row['screened_count']} 条；用法：{row['how_to_apply']}")
    lines.extend(["", "## 各主题高分样本", ""])
    for theme, items in top_by_theme.items():
        lines.append(f"### {theme}")
        for item in items[:5]:
            lines.append(f"- {item['year']} | {item['score']} | {item['title']} | {item['url']}")
        lines.append("")
    lines.extend(
        [
            "## 边界",
            "",
            "- 这不是“照搬论文结论”的库，而是方法、约束、变量和检查项库。",
            "- 进入报告前仍要结合本地 PDF、CAD、策划 DOCX、POI/TGI、证据台账和真实校准输入。",
            "- DeepSeek 只能使用本库做候选解释和初筛，不能直接输出最终排序、收益或定案结论。",
        ]
    )
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    raw, meta = collect()
    screened, rejected, stats = screen(raw)
    write_jsonl(OUT_DIR / "rejected_low_relevance_20260609.jsonl", rejected)
    write_outputs(screened, rejected, stats, meta)
    source_counts = stats.get("source_counts", {})
    source_diversity_ok = len(source_counts) >= MIN_SOURCE_COUNT and source_counts.get("openalex", 0) > 0
    query_matrix_ok = meta["query_count"] >= MIN_QUERY_COUNT
    tier_depth_ok = stats["screened_total"] >= TARGET_SCREENED and stats["tier_counts"].get("A_directly_actionable", 0) >= 80
    print(
        json.dumps(
            {
                "status": "pass" if tier_depth_ok and source_diversity_ok and query_matrix_ok else "needs_action",
                "raw": meta["raw_counts"],
                "query_count": meta["query_count"],
                "dedup_total": stats["dedup_total"],
                "screened_total": stats["screened_total"],
                "tier_counts": stats["tier_counts"],
                "source_counts": stats.get("source_counts", {}),
                "verify": str(VERIFY_JSON.relative_to(ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
