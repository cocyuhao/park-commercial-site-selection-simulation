from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "10_research" / "china_academic_sources_20260610"
QUALITY_DIR = ROOT / "40_quality_evidence"

REGISTRY_JSON = OUT_DIR / "china_academic_source_registry_20260610.json"
REGISTRY_CSV = OUT_DIR / "china_academic_source_registry_20260610.csv"
QUERY_MATRIX_JSON = OUT_DIR / "china_simulation_query_matrix_20260610.json"
QUERY_MATRIX_CSV = OUT_DIR / "china_simulation_query_matrix_20260610.csv"
IMPORT_SCHEMA_JSON = OUT_DIR / "china_academic_import_schema_20260610.json"
README_MD = OUT_DIR / "README.md"
VERIFY_JSON = QUALITY_DIR / "china_academic_source_registry_verification_20260610.json"


SOURCE_REGISTRY: list[dict[str, Any]] = [
    {
        "source_id": "CN-SRC-001",
        "name": "万方数据开放平台",
        "homepage": "https://apps.wanfangdata.com.cn/open",
        "api_docs": "https://apps.wanfangdata.com.cn/open/market/apis",
        "access_mode": "official_api_or_authorized_export",
        "automation_priority": "high",
        "secret_env": "WANFANG_API_KEY",
        "project_use": "中文期刊、学位、会议、科技报告等来源；优先补中国城市、公园、商业、交通、消费、仿真与规划语境。",
        "boundary": "需要按万方开放平台授权使用；未授权前只接导出文件，不做绕登录抓取。",
    },
    {
        "source_id": "CN-SRC-002",
        "name": "AMiner 开放平台",
        "homepage": "https://open.aminer.cn/",
        "api_docs": "https://open.aminer.cn/",
        "access_mode": "official_api_or_web_export",
        "automation_priority": "high",
        "secret_env": "AMINER_API_KEY",
        "project_use": "学者、论文、机构和学术图谱；用于补充 AI/Agent/仿真、城市计算、行为建模的中文与国际混合线索。",
        "boundary": "以官方开放平台能力为准；不能把网页检索结果当已复核事实。",
    },
    {
        "source_id": "CN-SRC-003",
        "name": "中国知网 CNKI",
        "homepage": "https://www.cnki.net/",
        "api_docs": "https://www.cnki.net/",
        "access_mode": "institutional_license_or_manual_export",
        "automation_priority": "medium",
        "secret_env": "",
        "project_use": "中文核心文献和政策/规划类文章强源；用于人工导出后导入知识库，补中国语境和行业表达。",
        "boundary": "通常依赖机构授权或商业接口；不做未授权爬取，不在脚本中模拟登录。",
    },
    {
        "source_id": "CN-SRC-004",
        "name": "维普中文期刊服务平台",
        "homepage": "https://www.cqvip.com/",
        "api_docs": "https://www.cqvip.com/",
        "access_mode": "institutional_license_or_manual_export",
        "automation_priority": "medium",
        "secret_env": "",
        "project_use": "中文期刊补充源；用于复核国内公园商业、公共空间、消费、城市治理相关研究。",
        "boundary": "按平台授权和导出规则接入；不做未授权爬取。",
    },
    {
        "source_id": "CN-SRC-005",
        "name": "百度学术",
        "homepage": "https://xueshu.baidu.com/",
        "api_docs": "https://xueshu.baidu.com/",
        "access_mode": "manual_search_lead_only",
        "automation_priority": "low",
        "secret_env": "",
        "project_use": "中文线索发现和题名补查；只作为发现入口，不作为结构化证据主源。",
        "boundary": "不作为自动批量抓取源；命中后回到万方/CNKI/维普/DOI/出版方复核。",
    },
    {
        "source_id": "CN-SRC-006",
        "name": "国家哲学社会科学文献中心",
        "homepage": "https://www.ncpssd.org/",
        "api_docs": "https://www.ncpssd.org/",
        "access_mode": "manual_search_or_authorized_export",
        "automation_priority": "medium",
        "secret_env": "",
        "project_use": "社科、城市治理、公共空间、消费和政策研究补充源；适合中国语境方法和语言表达。",
        "boundary": "以平台授权和导出为准，不做绕登录抓取。",
    },
    {
        "source_id": "CN-SRC-007",
        "name": "国家科技图书文献中心 NSTL",
        "homepage": "https://www.nstl.gov.cn/",
        "api_docs": "https://www.nstl.gov.cn/",
        "access_mode": "manual_search_or_authorized_export",
        "automation_priority": "medium",
        "secret_env": "",
        "project_use": "科技文献、工程、仿真、GIS、城市计算和标准线索补充。",
        "boundary": "按 NSTL 服务条款和授权导出接入。",
    },
    {
        "source_id": "CN-SRC-008",
        "name": "中国科技论文在线",
        "homepage": "http://www.paper.edu.cn/",
        "api_docs": "http://www.paper.edu.cn/",
        "access_mode": "manual_search_or_authorized_export",
        "automation_priority": "medium",
        "secret_env": "",
        "project_use": "高校科技论文线索，补充仿真、规划、GIS、客流预测等中文材料。",
        "boundary": "只用公开页面线索和授权导出，不做批量绕限制抓取。",
    },
    {
        "source_id": "CN-SRC-009",
        "name": "中国社会科学网",
        "homepage": "https://www.cssn.cn/",
        "api_docs": "https://www.cssn.cn/",
        "access_mode": "manual_search_lead_only",
        "automation_priority": "low",
        "secret_env": "",
        "project_use": "城市治理、公共性、消费社会、文旅政策的中文语境线索。",
        "boundary": "作为政策和观点线索，不作为结构化论文主源。",
    },
    {
        "source_id": "CN-SRC-010",
        "name": "国家标准全文公开系统",
        "homepage": "https://openstd.samr.gov.cn/",
        "api_docs": "https://openstd.samr.gov.cn/",
        "access_mode": "manual_search_or_authorized_export",
        "automation_priority": "medium",
        "secret_env": "",
        "project_use": "规范、标准、术语和合规边界；补消防、食品、公共设施、无障碍等真实世界约束。",
        "boundary": "标准文本按官方公开与授权范围使用，不能替代法律意见。",
    },
    {
        "source_id": "CN-SRC-011",
        "name": "北京市统计局 / 国家统计局公开数据",
        "homepage": "https://tjj.beijing.gov.cn/",
        "api_docs": "https://tjj.beijing.gov.cn/",
        "access_mode": "official_open_data_or_manual_export",
        "automation_priority": "high",
        "secret_env": "",
        "project_use": "北京人口、收入、消费、旅游、服务业等宏观边界，支撑奥森本地化校准。",
        "boundary": "只能作为宏观或区域边界，不能直接替代奥森周边街道级真实交易数据。",
    },
    {
        "source_id": "CN-SRC-012",
        "name": "北京市文化和旅游局 / 文旅公开数据",
        "homepage": "https://whlyj.beijing.gov.cn/",
        "api_docs": "https://whlyj.beijing.gov.cn/",
        "access_mode": "official_open_data_or_manual_export",
        "automation_priority": "medium",
        "secret_env": "",
        "project_use": "景区、旅游、文旅消费、假日客流和政策语境补充。",
        "boundary": "公开数据需标明年份和统计口径；不能混成项目实时客流。",
    },
    {
        "source_id": "CN-SRC-013",
        "name": "北京市园林绿化局公开信息",
        "homepage": "https://yllhj.beijing.gov.cn/",
        "api_docs": "https://yllhj.beijing.gov.cn/",
        "access_mode": "official_open_data_or_manual_export",
        "automation_priority": "medium",
        "secret_env": "",
        "project_use": "公园管理、绿地、活动、政策、运营边界与公共性要求。",
        "boundary": "只作为政策与运营边界，不自动推出商业收益。",
    },
    {
        "source_id": "CN-SRC-014",
        "name": "北京市市场监督管理局公开信息",
        "homepage": "https://scjgj.beijing.gov.cn/",
        "api_docs": "https://scjgj.beijing.gov.cn/",
        "access_mode": "official_open_data_or_manual_export",
        "automation_priority": "medium",
        "secret_env": "",
        "project_use": "食品经营许可、市场监管、商户合规和经营主体信息线索。",
        "boundary": "合规判断需复核现行法规和具体经营主体，不作为法律意见。",
    },
    {
        "source_id": "CN-SRC-015",
        "name": "高德地图开放平台",
        "homepage": "https://lbs.amap.com/",
        "api_docs": "https://lbs.amap.com/api/webservice/summary",
        "access_mode": "official_api",
        "automation_priority": "high",
        "secret_env": "AMAP_WEB_SERVICE_KEY",
        "project_use": "POI、路径、周边供给、可达性和空间校准；这是项目已有强相关中文/中国空间数据源。",
        "boundary": "Key 只放 `.env`；API 结果必须记录时间、参数和坐标系。",
    },
]


THEMES: dict[str, list[str]] = {
    "公园商业与公共空间": [
        "城市公园 商业服务 游客需求",
        "公园商业 业态组合 运营",
        "公共空间 商业化 游客体验",
        "城市绿地 配套服务 消费行为",
        "公园 轻餐饮 咖啡亭 选址",
    ],
    "客群画像与消费": [
        "公园游客 客群画像 消费意愿",
        "居民休闲消费 公园 服务设施",
        "游客消费 客单价 休闲空间",
        "亲子客群 公园 活动需求",
        "银发人群 城市公园 服务需求",
    ],
    "人流仿真与 ABM": [
        "城市公园 人流仿真 Agent",
        "公共空间 行人仿真 多智能体",
        "游客行为 仿真 活动链",
        "行人轨迹 热力图 公园",
        "人群拥挤 瓶颈 仿真 公共空间",
    ],
    "排队容量与运营": [
        "咖啡亭 排队模型 服务能力",
        "餐饮服务 排队 仿真 公园",
        "游客服务设施 容量规划",
        "高峰客流 服务压力 仿真",
        "零售服务 等待时间 运营优化",
    ],
    "收益预测与不确定性": [
        "公园商业 收益预测 不确定性",
        "休闲消费 转化率 客单价 模型",
        "Monte Carlo 收益预测 商业选址",
        "敏感性分析 商业选址 参数",
        "情景分析 公园商业 经营",
    ],
    "GIS/CAD/空间选址": [
        "GIS 商业选址 公园",
        "可达性 公园 服务设施 选址",
        "CAD GIS 空间数据 城市规划",
        "POI 商业供给 公园 周边",
        "多准则决策 商业选址 GIS",
    ],
    "城市治理与合规": [
        "城市公园 商业经营 合规",
        "公共空间 噪声投诉 夜间经济",
        "食品经营许可 公园 商业",
        "消防安全 临时商业设施",
        "公园商业 公共性 治理",
    ],
    "AI 工作台与报告": [
        "人工智能 决策支持 城市规划",
        "大语言模型 智能体 仿真",
        "AI 报告生成 可信度 证据链",
        "人机协同 决策支持 界面",
        "知识库 检索增强 规划决策",
    ],
}


IMPORT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "ChinaAcademicRecord",
    "type": "object",
    "required": ["source_id", "title", "year", "source_name", "query", "ingest_method"],
    "properties": {
        "source_id": {"type": "string", "description": "CN-SRC-001 等来源 ID"},
        "title": {"type": "string"},
        "authors": {"type": "array", "items": {"type": "string"}},
        "year": {"type": ["integer", "string"]},
        "source_name": {"type": "string", "description": "期刊/会议/数据库名"},
        "abstract": {"type": "string"},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "doi": {"type": "string"},
        "url": {"type": "string"},
        "citation_count": {"type": ["integer", "string", "null"]},
        "query": {"type": "string"},
        "theme": {"type": "string"},
        "ingest_method": {"enum": ["official_api", "authorized_export", "manual_export"]},
        "license_note": {"type": "string"},
        "project_use_note": {"type": "string"},
    },
}


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_query_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for theme, queries in THEMES.items():
        for index, query in enumerate(queries, start=1):
            rows.append(
                {
                    "theme": theme,
                    "query": query,
                    "priority": "high" if theme in {"人流仿真与 ABM", "收益预测与不确定性", "GIS/CAD/空间选址"} else "medium",
                    "source_preference": "万方/AMiner first; CNKI/VIP authorized export; OpenAlex/Crossref as international supplement",
                    "usage_rule": "仅作方法约束或中国语境补充；进入客户结论前必须连接本项目证据链。",
                    "query_id": f"CN-Q-{len(rows)+1:04d}",
                }
            )
    return rows


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    query_rows = build_query_rows()

    REGISTRY_JSON.write_text(json.dumps({"sources": SOURCE_REGISTRY}, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(
        REGISTRY_CSV,
        SOURCE_REGISTRY,
        ["source_id", "name", "homepage", "api_docs", "access_mode", "automation_priority", "secret_env", "project_use", "boundary"],
    )
    QUERY_MATRIX_JSON.write_text(json.dumps({"query_count": len(query_rows), "queries": query_rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(QUERY_MATRIX_CSV, query_rows, ["query_id", "theme", "query", "priority", "source_preference", "usage_rule"])
    IMPORT_SCHEMA_JSON.write_text(json.dumps(IMPORT_SCHEMA, ensure_ascii=False, indent=2), encoding="utf-8")

    readme = f"""# 国内学术与方法资料接入层（2026-06-10）

本目录用于把国内知识源纳入仿真知识库。原则是官方 API / 授权导出 / 人工导出优先，禁止未授权爬取。

## 当前源

- 万方数据开放平台：高优先级，优先 API 或授权导出。
- AMiner 开放平台：高优先级，适合学术图谱和 AI/仿真方向。
- CNKI：中文强源，但通常需要机构/商业授权，当前只做授权导出接入。
- 维普：中文期刊补充源，当前只做授权导出接入。
- 百度学术：只做线索发现，不做结构化主源。

## 接入顺序

1. 先用 `china_simulation_query_matrix_20260610.*` 检索。
2. 有官方 API Key 时写入 `.env`，不要提交。
3. 没有 API 时，导出 CSV/Excel/JSON 后按 `china_academic_import_schema_20260610.json` 规范化。
4. 进入客户报告前，必须关联本项目证据链，不能只引用论文结论。

生成时间：{datetime.now().isoformat(timespec='seconds')}
"""
    README_MD.write_text(readme, encoding="utf-8")

    access_modes = {row["access_mode"] for row in SOURCE_REGISTRY}
    verify = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "pass",
        "source_count": len(SOURCE_REGISTRY),
        "query_count": len(query_rows),
        "theme_count": len(THEMES),
        "high_priority_sources": [row["name"] for row in SOURCE_REGISTRY if row["automation_priority"] == "high"],
        "access_modes": sorted(access_modes),
        "files": {
            "registry_json": str(REGISTRY_JSON.relative_to(ROOT)),
            "registry_csv": str(REGISTRY_CSV.relative_to(ROOT)),
            "query_matrix_json": str(QUERY_MATRIX_JSON.relative_to(ROOT)),
            "query_matrix_csv": str(QUERY_MATRIX_CSV.relative_to(ROOT)),
            "import_schema": str(IMPORT_SCHEMA_JSON.relative_to(ROOT)),
            "readme": str(README_MD.relative_to(ROOT)),
        },
        "rule": "国内源优先接入，OpenAlex 降级为国际补源；未授权平台只接导出，不做绕登录抓取。",
    }
    VERIFY_JSON.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
