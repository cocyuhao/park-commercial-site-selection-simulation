from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RESEARCH_DIR = ROOT / "10_research"
RAW_PATH = RESEARCH_DIR / "recommendation_review_openalex_20260607.json"
MD_PATH = RESEARCH_DIR / "recommendation_review_framework_20260607.md"


QUERIES = [
    "LLM agent urban mobility simulation 2026",
    "large language model agent city simulation human mobility 2025",
    "urban park visitor experience commercial concession planning",
    "retail location choice multi criteria decision analysis site selection 2025",
    "public park food beverage concession visitor services planning",
    "agent based model retail location choice complementary goods",
    "discrete choice model retail location consumer behavior",
    "business case options appraisal recommendations evidence report",
]

OFFICIAL_AND_PRACTICAL_SOURCES = [
    {
        "title": "HM Treasury The Green Book 2026",
        "url": "https://www.gov.uk/government/publications/the-green-book-appraisal-and-evaluation-in-central-government/the-green-book-2026",
        "use": "把节点判断拆成战略、经济/价值、商业、财务、管理五类问题；报告必须提供可选方案和推荐理由。",
    },
    {
        "title": "GOV.UK business case guidance for projects and programmes",
        "url": "https://www.gov.uk/government/publications/business-case-guidance-for-projects-and-programmes",
        "use": "把当前报告定位成可迭代 business case，不把工作稿写成最终投资结论。",
    },
    {
        "title": "US National Park Service Commercial Services",
        "url": "https://www.nps.gov/subjects/concessions/index.htm",
        "use": "公园商业服务必须服务游客体验和公共使用边界，不只追求商业收入。",
    },
    {
        "title": "Purdue OWL Abstracts and Executive Summaries",
        "url": "https://owl.purdue.edu/owl/subject_specific_writing/writing_in_engineering/handbook_on_report_formats/abstracts_and_executive_summaries.html",
        "use": "执行摘要应自足、简洁、具体，不能把结论埋进机器式长段落。",
    },
    {
        "title": "University of Nottingham Business reports",
        "url": "https://www.nottingham.ac.uk/studyingeffectively/assessment/types/business.aspx",
        "use": "商业报告应解释建议如何得出，帮助决策者快速找到信息。",
    },
]


def _get_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "codex-park-simulation-research/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def search_openalex(query: str) -> list[dict[str, Any]]:
    params = {
        "search": query,
        "filter": "from_publication_date:2024-01-01,to_publication_date:2026-12-31",
        "per-page": "8",
        "sort": "cited_by_count:desc",
    }
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    data = _get_json(url)
    rows: list[dict[str, Any]] = []
    for work in data.get("results", []):
        rows.append(
            {
                "query": query,
                "title": work.get("title", ""),
                "year": work.get("publication_year"),
                "doi": work.get("doi", ""),
                "openalex_id": work.get("id", ""),
                "cited_by_count": work.get("cited_by_count", 0),
                "type": work.get("type", ""),
                "primary_location": ((work.get("primary_location") or {}).get("landing_page_url") or ""),
                "concepts": [item.get("display_name") for item in (work.get("concepts") or [])[:5]],
            }
        )
    return rows


def screen(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    screened: list[dict[str, Any]] = []
    relevant_words = [
        "agent",
        "simulation",
        "mobility",
        "location",
        "choice",
        "retail",
        "park",
        "visitor",
        "business",
        "case",
        "urban",
        "large language",
        "multi-criteria",
    ]
    for row in rows:
        key = (row.get("doi") or row.get("openalex_id") or row.get("title") or "").lower()
        if not key or key in seen:
            continue
        seen.add(key)
        title = (row.get("title") or "").lower()
        concepts = " ".join(str(item).lower() for item in row.get("concepts") or [])
        relevance = sum(1 for word in relevant_words if word in title or word in concepts)
        if relevance <= 0:
            continue
        row["relevance_signal"] = relevance
        screened.append(row)
    screened.sort(key=lambda item: (item.get("relevance_signal", 0), item.get("year") or 0, item.get("cited_by_count") or 0), reverse=True)
    return screened[:32]


def build_markdown(screened: list[dict[str, Any]]) -> str:
    lines = [
        "# 节点建议与报告评审框架补强（2026-06-07）",
        "",
        "## 1. 为什么要重做节点建议表",
        "",
        "当前 DOCX 的节点表已经能渲染，但建议颗粒度仍偏粗，容易让业务读者觉得像粗略方案。后续报告必须把每个节点拆成“依据、可选方案、推荐动作、定案条件、风险控制、复核动作”，而不是只给一句修改建议或神秘分数。",
        "",
        "## 2. 已采用的本地方法约束",
        "",
        "- 老板六份方法资料：状态对齐、行为程序、真实数据校准、微观/宏观双验证，不能让 LLM 直接给最终结论。",
        "- 项目证据链：CAD/DWG、北园图纸 PDF、证据台账、高德 POI、策划书都分层使用；PPT/策划表述不能直接当强证据。",
        "- 产品优先级方法：不只排序，要给分歧解释、置信度、工作量和下一步验证动作。",
        "",
        "## 3. 官方与实践来源",
        "",
    ]
    for source in OFFICIAL_AND_PRACTICAL_SOURCES:
        lines.append(f"- [{source['title']}]({source['url']})：{source['use']}")
    lines.extend(
        [
            "",
            "## 4. 近年论文候选筛选",
            "",
            "| 题名 | 年份 | 引用 | 用到哪里 |",
            "|---|---:|---:|---|",
        ]
    )
    for row in screened[:24]:
        title = str(row.get("title") or "").replace("|", "/")
        use = "用于校准 LLM agent、城市移动、选址选择、商业报告或多方案评审结构。"
        lines.append(f"| {title} | {row.get('year', '')} | {row.get('cited_by_count', 0)} | {use} |")
    lines.extend(
        [
            "",
            "## 5. 落到报告的硬结构",
            "",
            "每个节点必须至少写清：",
            "",
            "1. 适合服务的人群状态：运动、亲子、文化、康养、夜间、通勤或游客。",
            "2. 需求触发：口渴、疲劳、等待、拍照、活动前后、亲子照护、康复体验等。",
            "3. 可选方案：低改造试点、标准运营、重资产/暂缓条件。",
            "4. 推荐动作：先做什么、放在哪里、用什么运营形态、如何验证。",
            "5. 定案条件：客流、转化、成本、审批、消防、资质、路径和控制点。",
            "6. 风险控制：哪些内容不能先承诺，哪些应作为备选或折叠。",
            "7. 会改变判断的证据：补到什么数据后，建议可能升级或降级。",
            "",
            "## 6. 禁止继续使用的报告方式",
            "",
            "- 不用裸分数当主结论。",
            "- 不用一句“建议做咖啡/康养/文创”替代运营方案。",
            "- 不把 POI/TGI 相关性写成收益结论。",
            "- 不把 CAD 坐标写成高德坐标。",
            "- 不把模型初稿、PPT 表达、热门 POI 表写成经营事实。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict[str, Any]] = []
    for query in QUERIES:
        try:
            all_rows.extend(search_openalex(query))
        except Exception as exc:  # noqa: BLE001
            all_rows.append({"query": query, "error": str(exc)})
        time.sleep(0.2)
    screened = screen([row for row in all_rows if not row.get("error")])
    raw = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "queries": QUERIES,
        "official_and_practical_sources": OFFICIAL_AND_PRACTICAL_SOURCES,
        "raw_count": len(all_rows),
        "screened_count": len(screened),
        "raw_rows": all_rows,
        "screened_rows": screened,
    }
    RAW_PATH.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    MD_PATH.write_text(build_markdown(screened), encoding="utf-8")
    print(json.dumps({"raw": str(RAW_PATH), "md": str(MD_PATH), "screened_count": len(screened)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
