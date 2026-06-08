from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RESEARCH_DIR = ROOT / "10_research"
RUN_DIR = RESEARCH_DIR / "expert_implementation_knowledge_20260607"
CHECKPOINT_PATH = RUN_DIR / "checkpoint.json"
RAW_PATH = RUN_DIR / "expert_implementation_openalex_raw.json"
SUMMARY_PATH = RUN_DIR / "expert_implementation_summary.json"
MD_PATH = RESEARCH_DIR / "expert_implementation_review_framework_20260607.md"


TOPIC_GROUPS: dict[str, list[str]] = {
    "AI 与人群仿真": [
        "LLM agent urban mobility simulation",
        "large language model agents human mobility simulation",
        "city simulation generative agents",
        "digital twin pedestrian simulation LLM",
        "agent based model urban park visitor behavior",
        "activity based model travel behavior simulation",
        "human state alignment LLM simulation users",
        "program synthesis human behavior routines LLM",
        "LLM behavioral simulation validation causal inference",
        "agent based model calibration validation urban simulation",
    ],
    "目标人群与消费": [
        "urban park visitor segmentation consumer spending",
        "family visitor behavior urban parks amenities",
        "sports recreation park visitor spending food beverage",
        "wellness tourism urban parks health services",
        "tourism destination visitor spending behavior park",
        "income level consumer spending food beverage urban recreation",
        "resident population income retail demand spatial analysis",
        "youth consumer behavior coffee tea urban leisure",
        "elderly wellness service consumer behavior urban parks",
        "parent child leisure consumption urban park",
    ],
    "空间地理与周边": [
        "retail site selection GIS multi criteria decision analysis",
        "commercial location choice discrete choice model",
        "Huff model retail location choice 2024",
        "walkability retail demand urban park",
        "pedestrian route choice urban park amenities",
        "accessibility universal design urban parks facilities",
        "wayfinding pedestrian accessibility park visitor experience",
        "residential neighborhood park commercial demand GIS",
        "transit accessibility retail location choice",
        "urban green space surrounding population demand analysis",
    ],
    "时间天气与季节": [
        "weather impact park visitation consumer behavior",
        "seasonal demand outdoor recreation food beverage",
        "time of day park visitation consumer spending",
        "weekend holiday park visitor behavior food beverage",
        "nighttime economy public space park events",
        "outdoor recreation weather demand model",
        "urban park visitation temperature precipitation study",
        "seasonal event programming urban parks",
        "heat stress shade seating urban park visitor behavior",
        "winter outdoor event park commercial activation",
    ],
    "公园商业与运营": [
        "urban park visitor experience food beverage concession",
        "public park commercial services visitor experience",
        "park concession planning food beverage retail",
        "mobile food vending public space operations",
        "temporary retail pop-up stores public space operations",
        "public space placemaking commercial activation",
        "tenant mix retail destination visitor experience",
        "adaptive reuse park buildings commercial feasibility",
        "public building adaptive reuse commercial operations",
        "revenue management attractions visitor services",
    ],
    "工程消防安全与许可": [
        "fire safety evacuation public assembly venue planning",
        "outdoor event management urban parks noise crowd safety",
        "event crowd management public park safety",
        "food service facility design ventilation grease trap public venue",
        "restaurant kitchen exhaust fire safety public building",
        "medical service regulation wellness tourism business model",
        "traditional Chinese medicine wellness tourism consumer behavior",
        "public event noise complaint urban parks",
        "temporary structures outdoor event safety regulation",
        "underground commercial space evacuation safety retail",
    ],
    "服务运营与财务": [
        "queueing model food service operations visitor facilities",
        "service capacity planning queue abandonment food beverage",
        "food beverage concession revenue management public venue",
        "retail pop up store business model public space",
        "commercial feasibility study public private partnership park",
        "business case options appraisal public projects",
        "sensitivity analysis business case retail location",
        "scenario planning commercial real estate adaptive reuse",
        "cost benefit analysis urban park amenities",
        "customer journey public space service design",
    ],
    "维护可持续与风险": [
        "waste management food service public parks",
        "sustainable park concession operations",
        "public space maintenance cost food beverage kiosk",
        "urban park commercial activation community acceptance",
        "public space privatization commercial activities urban parks",
        "environmental impact outdoor events urban parks",
        "public toilet seating shade visitor satisfaction urban parks",
        "park safety risk management commercial events",
        "operational resilience outdoor venue weather risk",
        "social media sentiment park commercial activity",
    ],
}


OFFICIAL_REAL_WORLD_SOURCES = [
    {
        "title": "北京市公园条例",
        "url": "https://www.beijing.gov.cn/zhengce/dfxfg/202101/t20210125_2231092.html",
        "dimension": "政策与公园适配",
        "use": "商业服务设施应统一规划、控制规模、按批准方案设置。",
    },
    {
        "title": "食品经营许可审查通则（2024）",
        "url": "https://www.gov.cn/lianbo/bumen/202405/content_6948719.htm",
        "dimension": "食品许可与厨房工程",
        "use": "咖啡、茶饮、热食、简单制售、高风险食品要区分操作区、设施设备和许可审查。",
    },
    {
        "title": "食品经营许可和备案管理办法",
        "url": "https://www.gov.cn/lianbo/bumen/202307/content_6891457.htm",
        "dimension": "食品许可与经营动作",
        "use": "餐饮、预包装、仓储、配送、备案/报告边界会直接改变运营方案。",
    },
    {
        "title": "营业性演出管理条例",
        "url": "https://www.gov.cn/zhengce/content/2008-03/28/content_4262.htm",
        "dimension": "演出与夜间活动",
        "use": "Live House、露天演出、小型商业演出必须先检查演出主体、噪声、人群和安全审批。",
    },
    {
        "title": "营业性演出管理条例实施细则",
        "url": "https://www.gov.cn/gongbao/content/2005/content_64222.htm",
        "dimension": "演出经营主体",
        "use": "演出经营主体、许可证和报批材料决定夜间内容是否能作为主方案。",
    },
    {
        "title": "医疗机构管理条例实施细则",
        "url": "https://www.dhms.gov.cn/wjj/Web/_F0_0_28D01YKGYB3EQXU2PMZGJ6VI31.htm",
        "dimension": "医疗/康养资质",
        "use": "国医、检测、针灸、药房要区分文化体验、健康管理和医疗机构服务。",
    },
    {
        "title": "HM Treasury The Green Book 2026",
        "url": "https://www.gov.uk/government/publications/the-green-book-appraisal-and-evaluation-in-central-government/the-green-book-2026",
        "dimension": "商业案例评审",
        "use": "用战略、经济、商业、财务、管理五视角组织专业评审。",
    },
    {
        "title": "GOV.UK Business case guidance",
        "url": "https://www.gov.uk/government/publications/business-case-guidance-for-projects-and-programmes",
        "dimension": "方案与证据",
        "use": "报告应呈现方案、证据、缺口和下一步，而不是最终拍板。",
    },
    {
        "title": "National Park Service Commercial Services",
        "url": "https://www.nps.gov/subjects/concessions/index.htm",
        "dimension": "游客服务与公共性",
        "use": "公园商业服务要服务游客使用和体验，不应脱离公共空间属性单纯追求收入。",
    },
]


REAL_WORLD_REVIEW_DIMENSIONS = [
    ("政策与公园适配", "是否符合公园定位、生态与公共服务边界；是否统一规划、控制规模。"),
    ("目标人群", "亲子、运动、银发、白领、游客、夜间活动、文化研学等群体是否分别有需求触发和支付能力。"),
    ("周边人口与收入", "周边居住区、办公、学校、游客来源、消费层级和客单价承受力是否支撑该业态。"),
    ("时间节律", "工作日/周末/节假日、早中晚、活动前后、淡旺季是否决定运营形态。"),
    ("天气与季节", "高温、降雨、寒冷、风、空气质量、遮阴/避雨/取暖是否改变停留和消费。"),
    ("地理与可达", "入口、路线、绕行距离、无障碍、停车、公交地铁、视线可见性和导视是否成立。"),
    ("空间与工程", "面积、层高、结构、给排水、电力、排烟、冷链、垃圾、库房、后勤、无障碍是否闭合。"),
    ("消防与安全", "疏散、排队、人群密度、临时搭建、用火用电、儿童/老人安全、夜间照明是否闭合。"),
    ("许可与合规", "食品、演出、医疗、外摆、酒水、夜间、临时市集、活动审批等边界是否清晰。"),
    ("运营模型", "直营、联营、租赁、快闪、移动摊车、预约活动、季节运营、招商模块如何拆分。"),
    ("财务与招商", "租金/分成、CAPEX、OPEX、人力、设备、库存、客单价、转化率和回收期是否能复核。"),
    ("体验与品牌", "是否增加公园停留、服务游客痛点、避免过度商业化，是否与奥森调性一致。"),
    ("维护与可持续", "保洁、垃圾、油污、噪声、投诉、设备维护、能源、水耗、生态影响是否可控。"),
    ("新闻舆情与社区接受", "周边居民、游客、媒体、社交平台对商业化、噪声和价格的接受度。"),
    ("仿真与数据校准", "哪些参数会改变结论；真实数据、敏感性分析、人工复核和版本验收是否准备好。"),
]


def _request_json(url: str, timeout: int = 28) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "codex-park-expert-implementation/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _query_openalex(query: str, per_page: int, pages: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cursor = "*"
    for _ in range(pages):
        params = {
            "search": query,
            "filter": "from_publication_date:2024-01-01,to_publication_date:2026-12-31",
            "per-page": str(per_page),
            "cursor": cursor,
            "sort": "cited_by_count:desc",
        }
        url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
        data = _request_json(url)
        for work in data.get("results", []):
            source = ((work.get("primary_location") or {}).get("source") or {})
            rows.append(
                {
                    "query": query,
                    "title": work.get("title", ""),
                    "year": work.get("publication_year"),
                    "doi": work.get("doi", ""),
                    "openalex_id": work.get("id", ""),
                    "cited_by_count": work.get("cited_by_count", 0),
                    "type": work.get("type", ""),
                    "source": source.get("display_name", ""),
                    "source_type": source.get("type", ""),
                    "landing_page": ((work.get("primary_location") or {}).get("landing_page_url") or ""),
                    "open_access": (work.get("open_access") or {}).get("is_oa", False),
                    "concepts": [item.get("display_name") for item in (work.get("concepts") or [])[:8]],
                }
            )
        cursor = (data.get("meta") or {}).get("next_cursor")
        if not cursor:
            break
        time.sleep(0.12)
    return rows


def _load_checkpoint() -> dict[str, Any]:
    if CHECKPOINT_PATH.exists():
        return json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "completed_queries": [],
        "query_results": {},
        "errors": [],
    }


def _save_checkpoint(data: dict[str, Any]) -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = datetime.now().isoformat(timespec="seconds")
    CHECKPOINT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _all_queries() -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for group, queries in TOPIC_GROUPS.items():
        for query in queries:
            pairs.append((group, query))
    return pairs


def collect_batch(limit_queries: int, per_page: int, pages: int) -> dict[str, Any]:
    checkpoint = _load_checkpoint()
    completed = set(checkpoint.get("completed_queries", []))
    processed = 0
    for group, query in _all_queries():
        if query in completed:
            continue
        if processed >= limit_queries:
            break
        try:
            rows: list[dict[str, Any]] = []
            last_error = ""
            for attempt in range(3):
                try:
                    rows = _query_openalex(query, per_page=per_page, pages=pages)
                    last_error = ""
                    break
                except Exception as exc:  # noqa: BLE001
                    last_error = str(exc)
                    time.sleep(0.8 + attempt)
            if last_error:
                raise RuntimeError(last_error)
            for row in rows:
                row["topic_group"] = group
            checkpoint["query_results"][query] = rows
            checkpoint["completed_queries"].append(query)
        except Exception as exc:  # noqa: BLE001
            checkpoint["errors"].append({"query": query, "error": str(exc), "at": datetime.now().isoformat(timespec="seconds")})
        processed += 1
        _save_checkpoint(checkpoint)
        time.sleep(0.15)
    return checkpoint


def dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for row in rows:
        key = (row.get("doi") or row.get("openalex_id") or row.get("title") or "").lower()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def score_row(row: dict[str, Any]) -> int:
    text = " ".join(
        [
            str(row.get("title", "")),
            str(row.get("query", "")),
            str(row.get("topic_group", "")),
            " ".join(str(item) for item in row.get("concepts") or []),
        ]
    ).lower()
    weights = {
        "simulation": 5,
        "agent": 5,
        "mobility": 5,
        "digital twin": 5,
        "urban": 4,
        "park": 5,
        "visitor": 5,
        "retail": 4,
        "location": 4,
        "concession": 5,
        "choice": 4,
        "queue": 4,
        "service": 4,
        "income": 4,
        "resident": 4,
        "weather": 4,
        "season": 4,
        "accessibility": 4,
        "fire": 4,
        "safety": 4,
        "event": 4,
        "medical": 4,
        "wellness": 4,
        "business case": 4,
        "cost": 4,
        "calibration": 5,
        "validation": 5,
        "large language": 5,
        "llm": 5,
    }
    score = sum(weight for word, weight in weights.items() if word in text)
    year = int(row.get("year") or 0)
    if year >= 2026:
        score += 10
    elif year == 2025:
        score += 7
    elif year == 2024:
        score += 4
    score += min(int(row.get("cited_by_count") or 0), 100) // 5
    if row.get("doi"):
        score += 2
    if row.get("open_access"):
        score += 1
    negatives = [
        "microplastic",
        "battery",
        "electrocatalyst",
        "nitrate",
        "intrusion detection",
        "wireless",
        "6g",
        "cancer",
        "alzheimer",
        "genome",
        "groundwater",
        "heavy metals",
        "agriculture",
        "vehicle network",
        "self-driving laboratories",
    ]
    score -= sum(8 for word in negatives if word in text)
    return score


PROJECT_RELEVANCE: dict[str, list[str]] = {
    "AI 与人群仿真": ["agent", "simulation", "mobility", "urban", "human", "behavior", "digital twin", "large language", "llm"],
    "目标人群与消费": ["visitor", "consumer", "spending", "income", "family", "sports", "wellness", "park", "tourism", "leisure"],
    "空间地理与周边": ["retail", "location", "gis", "walkability", "accessibility", "residential", "transit", "park", "pedestrian"],
    "时间天气与季节": ["weather", "season", "time", "holiday", "weekend", "night", "temperature", "visitation", "outdoor"],
    "公园商业与运营": ["park", "concession", "food", "beverage", "retail", "public space", "placemaking", "visitor", "pop-up"],
    "工程消防安全与许可": ["fire", "evacuation", "safety", "event", "noise", "kitchen", "medical", "wellness", "underground"],
    "服务运营与财务": ["queue", "service", "revenue", "business case", "cost", "feasibility", "retail", "customer journey", "concession"],
    "维护可持续与风险": ["waste", "sustainable", "maintenance", "community", "environmental", "risk", "complaint", "sentiment", "park"],
}


def relevance_reasons(row: dict[str, Any]) -> list[str]:
    text = " ".join(
        [
            str(row.get("title", "")),
            str(row.get("query", "")),
            " ".join(str(item) for item in row.get("concepts") or []),
        ]
    ).lower()
    group = str(row.get("topic_group") or "")
    terms = PROJECT_RELEVANCE.get(group, [])
    return [term for term in terms if term in text]


def screen(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for row in rows:
        row["implementation_score"] = score_row(row)
        row["relevance_reasons"] = relevance_reasons(row)
    candidates = [
        row
        for row in rows
        if row.get("implementation_score", 0) >= 9
        and len(row.get("relevance_reasons") or []) >= 2
    ]
    return sorted(candidates, key=lambda item: (item.get("implementation_score", 0), len(item.get("relevance_reasons") or []), item.get("year") or 0), reverse=True)


def summarize() -> dict[str, Any]:
    checkpoint = _load_checkpoint()
    all_rows: list[dict[str, Any]] = []
    for rows in checkpoint.get("query_results", {}).values():
        all_rows.extend(rows)
    unique = dedupe(all_rows)
    screened = screen(unique)
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "topic_group_count": len(TOPIC_GROUPS),
        "query_total": len(_all_queries()),
        "completed_query_count": len(checkpoint.get("completed_queries", [])),
        "raw_count": len(all_rows),
        "unique_count": len(unique),
        "screened_count": len(screened),
        "official_real_world_sources": OFFICIAL_REAL_WORLD_SOURCES,
        "real_world_review_dimensions": REAL_WORLD_REVIEW_DIMENSIONS,
        "topic_counts": Counter(row.get("topic_group", "未知") for row in screened),
        "top_rows": screened[:300],
        "errors": checkpoint.get("errors", []),
    }
    RAW_PATH.write_text(json.dumps({"checkpoint": checkpoint, "unique_rows": unique}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    MD_PATH.write_text(build_markdown(summary), encoding="utf-8")
    return summary


def build_markdown(summary: dict[str, Any]) -> str:
    topic_counts = summary.get("topic_counts") or {}
    lines = [
        "# 真实世界专家评审知识底座（2026-06-07）",
        "",
        "## 1. 当前覆盖范围",
        "",
        f"- 主题组：{summary['topic_group_count']} 个。",
        f"- 查询总数：{summary['query_total']} 个。",
        f"- 已完成查询：{summary['completed_query_count']} 个。",
        f"- 原始候选：{summary['raw_count']} 条。",
        f"- 去重候选：{summary['unique_count']} 条。",
        f"- 高相关筛选：{summary['screened_count']} 条。",
        "- 本底座用于约束真实世界实施评审，不直接把论文标题塞进客户报告。",
        "",
        "## 2. 主题覆盖",
        "",
    ]
    for group, count in sorted(dict(topic_counts).items(), key=lambda item: item[1], reverse=True):
        lines.append(f"- {group}：{count}")
    lines.extend(["", "## 3. 真实世界评审维度", ""])
    for title, detail in REAL_WORLD_REVIEW_DIMENSIONS:
        lines.append(f"- **{title}**：{detail}")
    lines.extend(["", "## 4. 官方/实践约束", ""])
    for item in OFFICIAL_REAL_WORLD_SOURCES:
        lines.append(f"- [{item['title']}]({item['url']})：{item['use']}")
    lines.extend(["", "## 5. 高相关候选（前 150 条）", "", "| 主题 | 年份 | 分数 | 引用 | 题名 | 来源 |", "|---|---:|---:|---:|---|---|"])
    for row in summary.get("top_rows", [])[:150]:
        title = str(row.get("title") or "").replace("|", "/")
        source = str(row.get("source") or row.get("landing_page") or "").replace("|", "/")
        lines.append(f"| {row.get('topic_group','')} | {row.get('year','')} | {row.get('implementation_score',0)} | {row.get('cited_by_count',0)} | {title} | {source[:70]} |")
    lines.extend(
        [
            "",
            "## 6. 已转成报告规则",
            "",
            "每个节点建议必须回答：",
            "",
            "1. 服务谁：目标人群、收入/支付能力、到访目的、同行关系和身体状态。",
            "2. 什么时候发生：早中晚、工作日/周末/节假日、季节、天气和活动前后。",
            "3. 在哪里发生：入口、路线、绕行、可见性、遮阴/避雨、停车、地铁和周边居住/办公/学校。",
            "4. 做什么形态：低改造试点、标准运营、重资产版本或暂缓版本。",
            "5. 如何落地：空间、工程、消防、食品、医疗、演出、外摆、夜间和后勤要求。",
            "6. 如何赚钱和控风险：招商模式、客单价、转化率、CAPEX/OPEX、季节波动、投诉和维护。",
            "7. 哪些证据会改变判断：客流、转化、周边人口/收入、CAD/GIS、现场审批和试运营结果。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit-queries", type=int, default=12)
    parser.add_argument("--per-page", type=int, default=50)
    parser.add_argument("--pages", type=int, default=3)
    parser.add_argument("--summarize-only", action="store_true")
    args = parser.parse_args()

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    if not args.summarize_only:
        collect_batch(args.limit_queries, args.per_page, args.pages)
    summary = summarize()
    print(json.dumps({k: v for k, v in summary.items() if k not in {"top_rows", "topic_counts"}}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
