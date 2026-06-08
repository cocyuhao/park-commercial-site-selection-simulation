from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PDF_TEXT = ROOT / "30_extraction" / "pdf_text" / "奥林匹克森林公园区域大数据分析报告-20241230-202512291772157987.json"
PPT_TEXT = ROOT / "30_extraction" / "ppt_text" / "奥森修改稿0306.json"
SUPPLEMENT_FILE = ROOT / "90_p6_expert_dashboard" / "cache" / "real_calibration_supplements.json"
OUT_CSV = ROOT / "70_outputs" / "processed_tables" / "osen_real_calibration_inputs_20260607.csv"
OUT_JSON = ROOT / "40_quality_evidence" / "osen_real_calibration_inputs_20260607.json"
OUT_MD = ROOT / "40_quality_evidence" / "osen_real_calibration_inputs_20260607.md"

FIELDS = [
    "calibration_id",
    "dimension",
    "indicator_name",
    "segment",
    "period",
    "value",
    "unit",
    "source_file",
    "source_page_or_slide",
    "source_strength",
    "simulation_use",
    "cannot_claim",
    "next_data_needed",
    "raw_text_snippet",
    "output_status",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_supplements() -> list[dict[str, Any]]:
    if not SUPPLEMENT_FILE.exists():
        return []
    data = json.loads(SUPPLEMENT_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"supplement file must be a list: {SUPPLEMENT_FILE}")
    return [item for item in data if isinstance(item, dict) and not item.get("deleted")]


def compact(text: str, limit: int = 420) -> str:
    value = re.sub(r"\s+", " ", text).strip()
    return value[:limit]


def page_with(term: str) -> dict[str, Any]:
    for page in read_json(PDF_TEXT).get("pages", []):
        if term in str(page.get("text", "")):
            return page
    return {}


def slide_with(term: str) -> dict[str, Any]:
    for slide in read_json(PPT_TEXT).get("slides", []):
        if term in str(slide.get("text", "")):
            return slide
    return {}


def row(
    calibration_id: str,
    dimension: str,
    indicator_name: str,
    segment: str,
    period: str,
    value: str,
    unit: str,
    source_file: str,
    source_page_or_slide: str,
    source_strength: str,
    simulation_use: str,
    cannot_claim: str,
    next_data_needed: str,
    raw_text_snippet: str,
    output_status: str = "needs_review",
) -> dict[str, str]:
    return {
        "calibration_id": calibration_id,
        "dimension": dimension,
        "indicator_name": indicator_name,
        "segment": segment,
        "period": period,
        "value": value,
        "unit": unit,
        "source_file": source_file,
        "source_page_or_slide": source_page_or_slide,
        "source_strength": source_strength,
        "simulation_use": simulation_use,
        "cannot_claim": cannot_claim,
        "next_data_needed": next_data_needed,
        "raw_text_snippet": raw_text_snippet,
        "output_status": output_status,
    }


def normalize_supplement(item: dict[str, Any], index: int) -> dict[str, str]:
    calibration_id = str(item.get("calibration_id") or item.get("supplement_id") or f"ORCI-S{index:03d}").strip()
    if not calibration_id.startswith("ORCI-S"):
        calibration_id = f"ORCI-S{index:03d}"
    allowed_strengths = {
        "official_macro_boundary",
        "local_bigdata_profile",
        "local_device_price_proxy",
        "local_poi_price_signal",
        "local_poi_demand_signal",
        "local_user_supplement",
        "plan_assumption_needs_review",
    }
    source_strength = str(item.get("source_strength") or "local_user_supplement").strip()
    if source_strength not in allowed_strengths:
        source_strength = "local_user_supplement"
    return row(
        calibration_id,
        str(item.get("dimension") or "user_supplement").strip(),
        str(item.get("indicator_name") or "用户补充校准输入").strip(),
        str(item.get("segment") or "待确认范围").strip(),
        str(item.get("period") or "待确认时期").strip(),
        str(item.get("value") or "待确认").strip(),
        str(item.get("unit") or "").strip(),
        str(item.get("source_file") or "90_p6_expert_dashboard/cache/real_calibration_supplements.json").strip(),
        str(item.get("source_page_or_slide") or "user_supplement").strip(),
        source_strength,
        str(item.get("simulation_use") or "作为用户补充校准输入进入预检和报告，待人工复核后用于仿真参数。").strip(),
        str(item.get("cannot_claim") or "不能直接写成最终收益、最终排名、真实转化或投资定案。").strip(),
        str(item.get("next_data_needed") or "补来源文件、采集口径、时段、样本量、复核人和可追溯证据。").strip(),
        compact(str(item.get("raw_text_snippet") or item.get("note") or "用户补充校准输入，等待来源复核。")),
        str(item.get("output_status") or "needs_review").strip(),
    )


def source_page(page: dict[str, Any]) -> str:
    page_no = page.get("page_number") or page.get("page") or ""
    return str(page_no)


def source_slide(slide: dict[str, Any]) -> str:
    number = slide.get("slide_number")
    if number is None:
        number = slide.get("index")
    if number is None:
        number = ""
    return str(number)


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    pdf_source = str(PDF_TEXT.relative_to(ROOT))
    ppt_source = str(PPT_TEXT.relative_to(ROOT))

    # Official macro boundary. These are verified upstream in
    # 10_research/osen_real_world_context_sources_20260607.md and must not be
    # treated as local park catchment income.
    rows.extend(
        [
            row(
                "ORCI-001",
                "macro_income",
                "北京市居民人均可支配收入",
                "全市居民",
                "2025",
                "89090",
                "元/人/年",
                "https://tjj.beijing.gov.cn/zxfbu/202601/t20260121_4451962.html",
                "web",
                "official_macro_boundary",
                "约束价格带和支付能力讨论的上位边界。",
                "不能当作奥森周边街道级收入，也不能证明某节点高客单成立。",
                "补奥森周边 1-3 公里街道/社区收入、居住办公结构和游客来源。",
                "北京市统计局 / 国家统计局北京调查总队：2025 年全市居民人均可支配收入 89090 元。",
                "needs_review",
            ),
            row(
                "ORCI-002",
                "macro_consumption",
                "北京市居民人均消费支出",
                "全市居民",
                "2025",
                "50667",
                "元/人/年",
                "https://tjj.beijing.gov.cn/zxfbu/202601/t20260121_4451977.html",
                "web",
                "official_macro_boundary",
                "约束文娱、亲子、康养、轻餐等业态的价格带讨论。",
                "不能替代项目周边真实消费结构和园内实际转化。",
                "补竞品客单价、园内交易、支付笔数、分时段转化率。",
                "北京市统计局 / 国家统计局北京调查总队：2025 年全市居民人均消费支出 50667 元。",
                "needs_review",
            ),
            row(
                "ORCI-003",
                "macro_service_consumption",
                "北京市居民人均服务性消费支出",
                "全市居民",
                "2025",
                "30052",
                "元/人/年",
                "https://tjj.beijing.gov.cn/zxfbu/202601/t20260121_4452019.html",
                "web",
                "official_macro_boundary",
                "说明服务消费有宏观背景，可约束体验、活动、康养和文娱判断。",
                "不能证明奥森某节点能承接高服务客单。",
                "补项目周边服务消费价格、报名转化、复购和场地容量。",
                "2025 年全市居民人均服务性消费支出 30052 元，占消费支出 59.3%。",
                "needs_review",
            ),
        ]
    )

    lifestyle = page_with("A10人群画像分析-APP偏好-生活")
    health = page_with("A10人群画像分析-APP偏好-健康")
    education = page_with("A10人群画像分析-APP偏好-教育")
    device_all = page_with("全部人口中，手机价格")
    device_work = page_with("工作人口中，手机价格")
    food_work = page_with("工作人口，在区域内范围内最热门到访 | 的美食类地点")
    food_mobile = page_with("流动人口，在区域内范围内最热门到访 | 的美食类地点")
    sports_work = page_with("工作人口，在区域内范围内最热门到访 | 的运动健身类地点")

    rows.extend(
        [
            row(
                "ORCI-101",
                "local_tgi_lifestyle",
                "美食/食材/票务生活偏好",
                "全部人口",
                "2024-12-30 至 2025-12-29",
                "美食 TGI 118；食材 TGI 122；票务 TGI 152",
                "TGI",
                pdf_source,
                source_page(lifestyle),
                "local_bigdata_profile",
                "用于判断轻餐、票务活动、亲子/演艺和补给服务是否值得进入候选。",
                "TGI 是偏好指数，不是成交率、客单价或收入。",
                "补真实消费转化、客单价、竞品价格和活动售卖数据。",
                compact(lifestyle.get("text", "")),
            ),
            row(
                "ORCI-102",
                "local_tgi_health",
                "运动健身与健康偏好",
                "全部/流动人口",
                "2024-12-30 至 2025-12-29",
                "运动健身 TGI 125；健康养生 TGI 123",
                "TGI",
                pdf_source,
                source_page(health),
                "local_bigdata_profile",
                "用于约束晨练、跑步、运动补给、拉伸康复、瑜伽/普拉提场景。",
                "不能证明某个节点有足够付费人群或可经营面积。",
                "补跑步路线客流、停留时长、补水需求、运动类竞品价格和可营业时段。",
                compact(health.get("text", "")),
            ),
            row(
                "ORCI-103",
                "local_tgi_parent_education",
                "教育与亲子偏好",
                "全部/流动人口",
                "2024-12-30 至 2025-12-29",
                "在线学堂 TGI 125；儿童教育 TGI 119；出国留学 TGI 145",
                "TGI",
                pdf_source,
                source_page(education),
                "local_bigdata_profile",
                "用于约束亲子活动、儿童文创、研学和家庭休憩场景。",
                "不能证明亲子客群在目标节点出现，也不能证明愿意付费。",
                "补家庭同行比例、儿童年龄段、周末/节假日流量和亲子竞品客单。",
                compact(education.get("text", "")),
            ),
            row(
                "ORCI-104",
                "local_income_proxy",
                "手机价格分段",
                "全部人口",
                "2024-12-30 至 2025-12-29",
                "2001-3000 元占比 17.51%；4001-5000 TGI 128；7001-8000 TGI 126",
                "设备价格代理变量",
                pdf_source,
                source_page(device_all),
                "local_device_price_proxy",
                "作为收入/消费能力的弱代理，帮助校验价格带不能只靠主观假设。",
                "手机价格不是个人收入；不能直接推出消费能力或高客单。",
                "补街道级收入、家庭结构、实际支付数据和竞品客单。",
                compact(device_all.get("text", "")),
            ),
            row(
                "ORCI-105",
                "local_income_proxy_work",
                "工作人口高端手机价格分段",
                "工作人口",
                "2024-12-30 至 2025-12-29",
                ">10000 元 TGI 128；5001-6000 TGI 123；6001-7000 TGI 130；7001-8000 TGI 132",
                "设备价格代理变量",
                pdf_source,
                source_page(device_work),
                "local_device_price_proxy",
                "提示工作人口存在较高设备价格分段偏好，可用于白领/商务/运动社交场景的价格敏感性讨论。",
                "不能直接证明高收入白领占比或高客单承接能力。",
                "补周边办公人群、工作日午晚高峰、支付客单和品牌价格带。",
                compact(device_work.get("text", "")),
            ),
            row(
                "ORCI-106",
                "local_competitor_price",
                "周边美食热门到访与客单",
                "工作人口",
                "2024-12-30 至 2025-12-29",
                "新净雅 231 元；咿道南门涮肉 92 元；亲子家庭餐厅 129 元",
                "人均消费",
                pdf_source,
                source_page(food_work),
                "local_poi_price_signal",
                "作为竞品价格带线索，用来约束园内餐饮/亲子/轻餐价格设定。",
                "热门到访不等于园内可复制，也不等于目标节点成交。",
                "补园内外竞品清单、距离、排队、营业时间、支付转化和品牌授权。",
                compact(food_work.get("text", "")),
            ),
            row(
                "ORCI-107",
                "local_competitor_price",
                "流动人口美食热门到访与客单",
                "流动人口",
                "2024-12-30 至 2025-12-29",
                "咿道南门涮肉 92 元；新净雅 231 元；亲子家庭餐厅 129 元",
                "人均消费",
                pdf_source,
                source_page(food_mobile),
                "local_poi_price_signal",
                "用于交叉验证流动人口的餐饮外溢和价格带。",
                "不能证明园内新增餐饮可达到同样客单。",
                "补流动人口来源、园内停留、节点可达性和消费转化。",
                compact(food_mobile.get("text", "")),
            ),
            row(
                "ORCI-108",
                "local_competitor_sports",
                "运动健身热门到访",
                "工作人口",
                "2024-12-30 至 2025-12-29",
                "国家网球中心莲花球场指数 3830；专项体能康复普拉提运动中心指数 1579",
                "热门到访指数",
                pdf_source,
                source_page(sports_work),
                "local_poi_demand_signal",
                "用于约束运动补给、康复拉伸、瑜伽普拉提和活动节点。",
                "热门运动 POI 不等于公园内空间、许可和付费转化已成立。",
                "补运动路线、时段客流、停留时长、课程价格和场地容量。",
                compact(sports_work.get("text", "")),
            ),
        ]
    )

    data_slide = slide_with("高峰日 10.9万")
    finance_slide = slide_with("消费者占比：35%")
    gap_slide = slide_with("流量很大，转化很低")
    rows.extend(
        [
            row(
                "ORCI-201",
                "plan_assumption_flow",
                "策划稿客流输入",
                "奥森整体",
                "方案稿",
                "高峰日 10.9 万；工作日日均 3.4 万",
                "人次",
                ppt_source,
                source_slide(data_slide),
                "plan_assumption_needs_review",
                "可作为试算入口参数的初稿。",
                "不能当作已复核客流；不能直接写入最终收益。",
                "补原始客流表、入口分布、分时段、天气、节假日和淡旺季数据。",
                compact(data_slide.get("text", "")),
            ),
            row(
                "ORCI-202",
                "plan_assumption_conversion",
                "策划稿消费转化假设",
                "奥森整体",
                "方案稿",
                "消费者占比 35%；触发率来自 12 类消费者行为决策树实测参数",
                "比例/说明",
                ppt_source,
                source_slide(finance_slide),
                "plan_assumption_needs_review",
                "可作为敏感性分析初始参数，不得替代真实转化。",
                "不能证明当前真实转化率、触发率或改造后收益。",
                "补真实支付笔数、客单价、到访到消费漏斗、试运营 AB 结果。",
                compact(finance_slide.get("text", "")),
            ),
            row(
                "ORCI-203",
                "plan_assumption_gap",
                "策划稿流量转化缺口",
                "奥森整体",
                "方案稿",
                "实际消费转化率 35%；当前实际收入估算约 173 万/天",
                "比例/金额",
                ppt_source,
                source_slide(gap_slide),
                "plan_assumption_needs_review",
                "可提示供需缺口方向，用于向业务方索取明细。",
                "不能作为已核验经营收入或最终商业测算。",
                "补园方财务、租金分成、商户流水、成本和外溢竞品成交。",
                compact(gap_slide.get("text", "")),
            ),
        ]
    )
    supplements = read_supplements()
    rows.extend(normalize_supplement(item, index) for index, item in enumerate(supplements, start=1))
    return rows


def write_csv(rows: list[dict[str, str]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_json(rows: list[dict[str, str]]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    by_strength: dict[str, int] = {}
    by_dimension: dict[str, int] = {}
    for item in rows:
        by_strength[item["source_strength"]] = by_strength.get(item["source_strength"], 0) + 1
        by_dimension[item["dimension"]] = by_dimension.get(item["dimension"], 0) + 1
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "pass",
        "row_count": len(rows),
        "source_files": [
            str(PDF_TEXT.relative_to(ROOT)),
            str(PPT_TEXT.relative_to(ROOT)),
            "10_research/osen_real_world_context_sources_20260607.md",
            str(SUPPLEMENT_FILE.relative_to(ROOT)),
        ],
        "counts": {"by_strength": by_strength, "by_dimension": by_dimension},
        "use_rule": "official_macro_boundary, local_bigdata_profile/proxy and plan_assumption_needs_review must remain separated.",
        "cannot_claim": "本输入包不能直接推出最终收益或排名，也不能证明街道级收入、真实转化、最终 ROI 或投资定案。",
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_md(rows: list[dict[str, str]]) -> None:
    lines = [
        "# 奥森真实校准输入包（2026-06-07）",
        "",
        f"- 状态：pass",
        f"- 行数：{len(rows)}",
        "- 规则：官方宏观收入/消费、本地大数据画像/价格代理、PPT 方案假设必须分层使用，不能混成最终结论。",
        "- 用途：给人物仿真、价格带、竞品价格、转化率、时间天气和供需缺口提供可追溯输入。",
        "- 边界：不证明最终 ROI、最终排名、真实客群占比或投资定案。",
        "",
        "## 分层摘要",
    ]
    for strength in sorted({row["source_strength"] for row in rows}):
        group = [row for row in rows if row["source_strength"] == strength]
        lines.append(f"- {strength}: {len(group)} 条")
    lines.extend(["", "## 关键输入"])
    for item in rows:
        lines.append(
            f"- `{item['calibration_id']}` {item['indicator_name']}（{item['segment']}）：{item['value']} {item['unit']}；"
            f"用途：{item['simulation_use']}；边界：{item['cannot_claim']}"
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_rows()
    if len(rows) < 10:
        raise SystemExit(f"too few rows: {len(rows)}")
    required_strengths = {"official_macro_boundary", "local_bigdata_profile", "local_device_price_proxy", "local_poi_price_signal", "plan_assumption_needs_review"}
    strengths = {row["source_strength"] for row in rows}
    missing = required_strengths - strengths
    if missing:
        raise SystemExit(f"missing strengths: {sorted(missing)}")
    write_csv(rows)
    write_json(rows)
    write_md(rows)
    print(json.dumps({"status": "pass", "rows": len(rows), "csv": str(OUT_CSV.relative_to(ROOT)), "json": str(OUT_JSON.relative_to(ROOT))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
