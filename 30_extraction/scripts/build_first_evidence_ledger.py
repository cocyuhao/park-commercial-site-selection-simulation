from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TABLES_JSONL = ROOT / "30_extraction" / "tables" / "pdf_native_tables.jsonl"
KEYWORD_HITS = ROOT / "30_extraction" / "tables" / "keyword_hits.csv"
LEDGER = ROOT / "40_quality_evidence" / "evidence_ledger.csv"
REPORT = ROOT / "40_quality_evidence" / "first_evidence_ledger_report.md"

FIELDS = [
    "metric_id",
    "metric_name",
    "value",
    "unit",
    "source_file",
    "source_page_or_slide",
    "source_quote",
    "extraction_method",
    "evidence_type",
    "confidence",
    "validation_status",
    "notes",
]


def load_keyword_hits() -> list[dict[str, str]]:
    with KEYWORD_HITS.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_tables() -> dict[str, dict]:
    tables: dict[str, dict] = {}
    with TABLES_JSONL.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                tables[item["table_id"]] = item
    return tables


def find_hit(
    hits: list[dict[str, str]],
    *,
    source_contains: str,
    unit_index: int,
    text_contains: str,
) -> dict[str, str]:
    for hit in hits:
        if (
            source_contains in hit["source_file"]
            and str(unit_index) == str(hit["unit_index"])
            and text_contains in hit["snippet"]
        ):
            return hit
    raise ValueError(
        f"未找到关键词命中：source_contains={source_contains}, "
        f"unit_index={unit_index}, text_contains={text_contains}"
    )


def compact(text: str, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def table_row_quote(table: dict, row: list[str]) -> str:
    header = " / ".join(str(cell) for cell in table["rows"][0])
    body = " / ".join(str(cell) for cell in row)
    return compact(f"{table['table_id']}：{header} | {body}")


def row_by_first_cell(table: dict, first_cell: str) -> list[str]:
    for row in table["rows"][1:]:
        if row and str(row[0]) == first_cell:
            return row
    raise ValueError(f"{table['table_id']} 未找到首列为 {first_cell!r} 的行")


def row_by_rank(table: dict, rank: str) -> list[str]:
    for row in table["rows"][1:]:
        if row and str(row[0]) == rank:
            return row
    raise ValueError(f"{table['table_id']} 未找到排序为 {rank!r} 的行")


def add(
    rows: list[dict[str, str]],
    *,
    metric_name: str,
    value: str | int | float,
    unit: str,
    source_file: str,
    source_page_or_slide: str,
    source_quote: str,
    extraction_method: str,
    evidence_type: str,
    confidence: str,
    validation_status: str,
    notes: str,
) -> None:
    rows.append(
        {
            "metric_id": f"MET-{len(rows) + 1:04d}",
            "metric_name": metric_name,
            "value": str(value),
            "unit": unit,
            "source_file": source_file,
            "source_page_or_slide": source_page_or_slide,
            "source_quote": compact(source_quote),
            "extraction_method": extraction_method,
            "evidence_type": evidence_type,
            "confidence": confidence,
            "validation_status": validation_status,
            "notes": notes,
        }
    )


def add_pdf_keyword_metrics(rows: list[dict[str, str]], hits: list[dict[str, str]]) -> None:
    city_day = find_hit(
        hits,
        source_contains="城市绿心公园",
        unit_index=2,
        text_contains="总到访人数为2,623,050",
    )
    total_visit = re.search(r"总到访人数为([\d,]+)", city_day["snippet"])
    peak_day = re.search(r"(\d{8})日的人数最大，为(\d+)", city_day["snippet"])
    if not total_visit or not peak_day:
        raise ValueError("城市绿心客流页无法解析")
    add(
        rows,
        metric_name="城市绿心样例-年总到访人数",
        value=total_visit.group(1).replace(",", ""),
        unit="人次/年",
        source_file=city_day["source_file"],
        source_page_or_slide="page 2",
        source_quote=city_day["snippet"],
        extraction_method="keyword_hits_regex",
        evidence_type="source_report_pdf",
        confidence="medium",
        validation_status="checked",
        notes="来自 keyword_hits.csv；已由多方法核验确认文本抽取一致，仍需后续核验原始报告口径。",
    )
    add(
        rows,
        metric_name="城市绿心样例-日峰值到访人数",
        value=peak_day.group(2),
        unit="人次/日",
        source_file=city_day["source_file"],
        source_page_or_slide="page 2",
        source_quote=city_day["snippet"],
        extraction_method="keyword_hits_regex",
        evidence_type="source_report_pdf",
        confidence="medium",
        validation_status="checked",
        notes=f"峰值日期 {peak_day.group(1)}；来自 keyword_hits.csv，未复算原始日序列。",
    )

    city_hour = find_hit(
        hits,
        source_contains="城市绿心公园",
        unit_index=3,
        text_contains="12时的时均人数最大",
    )
    peak_hour = re.search(r"(\d+)时的时均人数最大，为(\d+)", city_hour["snippet"])
    if not peak_hour:
        raise ValueError("城市绿心小时客流页无法解析")
    add(
        rows,
        metric_name="城市绿心样例-时均峰值客流",
        value=peak_hour.group(2),
        unit="人次/小时",
        source_file=city_hour["source_file"],
        source_page_or_slide="page 3",
        source_quote=city_hour["snippet"],
        extraction_method="keyword_hits_regex",
        evidence_type="source_report_pdf",
        confidence="medium",
        validation_status="checked",
        notes=f"峰值时段 {peak_hour.group(1)} 时；来自 keyword_hits.csv。",
    )

    olympic_specs = [
        ("奥森样例-全部人口日峰值到访人数", 2, "全部人口中", "人次/日"),
        ("奥森样例-流动人口日峰值到访人数", 4, "流动人口中", "人次/日"),
        ("奥森样例-到访人口日峰值到访人数", 6, "到访人口中", "人次/日"),
        ("奥森样例-全部人口时均峰值客流", 8, "全部人口中", "人次/小时"),
        ("奥森样例-流动人口时均峰值客流", 10, "流动人口中", "人次/小时"),
    ]
    for name, page, contains, unit in olympic_specs:
        hit = find_hit(
            hits,
            source_contains="奥林匹克森林公园",
            unit_index=page,
            text_contains=contains,
        )
        match = re.search(r"(?:(\d{8})日|(\d+)时)的时均?人数最大，为(\d+)", hit["snippet"])
        if not match:
            match = re.search(r"(?:(\d{8})日|(\d+)时)的人数最大，为(\d+)", hit["snippet"])
        if not match:
            raise ValueError(f"奥森客流页无法解析：page {page}")
        qualifier = f"峰值日期 {match.group(1)}" if match.group(1) else f"峰值时段 {match.group(2)} 时"
        add(
            rows,
            metric_name=name,
            value=match.group(3),
            unit=unit,
            source_file=hit["source_file"],
            source_page_or_slide=f"page {page}",
            source_quote=hit["snippet"],
            extraction_method="keyword_hits_regex",
            evidence_type="source_report_pdf",
            confidence="medium",
            validation_status="checked",
            notes=f"{qualifier}；来自 keyword_hits.csv，未复算原始日/小时序列。",
        )


def add_table_metrics(rows: list[dict[str, str]], tables: dict[str, dict]) -> None:
    table_specs = [
        ("TBL-00005", "1", "城市绿心样例-区域内美食类热门到访POI第一名指数", 2, "指数"),
        ("TBL-00005", "1", "城市绿心样例-区域内美食类热门到访POI第一名人均消费", 3, "元/人"),
        ("TBL-00049", "101-150元", "城市绿心样例-餐饮消费水平101-150元占比", 1, "%"),
        ("TBL-00049", "101-150元", "城市绿心样例-餐饮消费水平101-150元TGI", 3, "TGI指数"),
        ("TBL-00051", "11次及以上", "城市绿心样例-餐饮消费频次11次及以上占比", 1, "%"),
        ("TBL-00051", "11次及以上", "城市绿心样例-餐饮消费频次11次及以上TGI", 3, "TGI指数"),
        ("TBL-00066", "小吃快餐", "城市绿心样例-美食小吃快餐人群覆盖度", 1, "%"),
        ("TBL-00066", "小吃快餐", "城市绿心样例-美食小吃快餐TGI", 3, "TGI指数"),
        ("TBL-00068", "咖啡厅", "城市绿心样例-娱乐休闲咖啡厅人群覆盖度", 1, "%"),
        ("TBL-00068", "咖啡厅", "城市绿心样例-娱乐休闲咖啡厅TGI", 3, "TGI指数"),
        ("TBL-00119", "1", "奥森样例-区域内流动人口美食类热门到访POI第一名指数", 2, "指数"),
        ("TBL-00119", "1", "奥森样例-区域内流动人口美食类热门到访POI第一名人均消费", 3, "元/人"),
        ("TBL-00200", "51-100元", "奥森样例-餐饮消费水平51-100元占比", 1, "%"),
        ("TBL-00200", "101-150元", "奥森样例-餐饮消费水平101-150元TGI", 3, "TGI指数"),
        ("TBL-00201", "11次及以上", "奥森样例-餐饮消费频次11次及以上占比", 1, "%"),
        ("TBL-00201", "11次及以上", "奥森样例-餐饮消费频次11次及以上TGI", 3, "TGI指数"),
        ("TBL-00249", "咖啡厅", "奥森样例-娱乐休闲咖啡厅人群覆盖度", 1, "%"),
        ("TBL-00249", "咖啡厅", "奥森样例-娱乐休闲咖啡厅TGI", 3, "TGI指数"),
        ("TBL-00259", "冷饮店", "奥森样例-美食冷饮店人群覆盖度", 1, "%"),
        ("TBL-00259", "冷饮店", "奥森样例-美食冷饮店TGI", 3, "TGI指数"),
    ]
    for table_id, key, name, value_index, unit in table_specs:
        table = tables[table_id]
        row = row_by_rank(table, key) if key.isdigit() else row_by_first_cell(table, key)
        value = row[value_index]
        if unit in {"%", "元/人"}:
            value = re.sub(r"[^0-9.]", "", str(value))
        add(
            rows,
            metric_name=name,
            value=value,
            unit=unit,
            source_file=table["source_file"],
            source_page_or_slide=f"page {table['page']}",
            source_quote=table_row_quote(table, row),
            extraction_method="pdf_native_table_jsonl",
            evidence_type="source_report_pdf",
            confidence="medium",
            validation_status="checked",
            notes=f"来自 {table_id}；PDF 原生表格抽取已通过批量核验，仍需抽样人工复核业务口径。",
        )


def add_ppt_assumptions(rows: list[dict[str, str]], hits: list[dict[str, str]]) -> None:
    city_summary = find_hit(
        hits,
        source_contains="AI (1)(1).pptx",
        unit_index=11,
        text_contains="四大改造方案合计投入 380 万元",
    )
    for name, value, unit, quote_hint in [
        ("城市绿心PPT假设-四大改造方案合计投入", "380", "万元", "合计投入 380 万元"),
        ("城市绿心PPT假设-预计年公园收益增长", "620", "万元/年", "年公园收益增长 620 万元"),
        ("城市绿心PPT假设-综合加权回收期", "7.3", "月", "回收期仅 7.3 个月"),
        ("城市绿心PPT假设-营业额分成比例下限", "12", "%", "12–15% 营业额分成"),
        ("城市绿心PPT假设-营业额分成比例上限", "15", "%", "12–15% 营业额分成"),
    ]:
        add(
            rows,
            metric_name=name,
            value=value,
            unit=unit,
            source_file=city_summary["source_file"],
            source_page_or_slide="slide 11",
            source_quote=city_summary["snippet"],
            extraction_method="keyword_hits_manual_parse",
            evidence_type="presentation_assumption",
            confidence="assumption",
            validation_status="needs_review",
            notes=f"PPT 收益测算假设；命中片段包含“{quote_hint}”，需回查财务参数和真实经营数据。",
        )

    city_gap = find_hit(
        hits,
        source_contains="AI (1)(1).pptx",
        unit_index=6,
        text_contains="五大核心业态缺口",
    )
    add(
        rows,
        metric_name="城市绿心PPT假设-P0业态缺口数量",
        value="5",
        unit="个",
        source_file=city_gap["source_file"],
        source_page_or_slide="slide 6",
        source_quote=city_gap["snippet"],
        extraction_method="keyword_hits_manual_parse",
        evidence_type="presentation_assumption",
        confidence="assumption",
        validation_status="needs_review",
        notes="PPT 供需缺口判断；部分 TGI 可回查 PDF，园内供给仍需现场/高德 POI 核验。",
    )

    olympic_gap = find_hit(
        hits,
        source_contains="奥森修改稿0306.pptx",
        unit_index=5,
        text_contains="五大严重缺口",
    )
    add(
        rows,
        metric_name="奥森PPT假设-P0业态缺口数量",
        value="5",
        unit="个",
        source_file=olympic_gap["source_file"],
        source_page_or_slide="slide 5",
        source_quote=olympic_gap["snippet"],
        extraction_method="keyword_hits_manual_parse",
        evidence_type="presentation_assumption",
        confidence="assumption",
        validation_status="needs_review",
        notes="PPT 供需缺口判断；咖啡 TGI 可由 PDF 表格支持，园内供给数量仍需高德/现场核验。",
    )
    add(
        rows,
        metric_name="奥森PPT假设-精品咖啡园内现状店数",
        value="2",
        unit="家",
        source_file=olympic_gap["source_file"],
        source_page_or_slide="slide 5",
        source_quote=olympic_gap["snippet"],
        extraction_method="keyword_hits_manual_parse",
        evidence_type="presentation_assumption",
        confidence="assumption",
        validation_status="conflict",
        notes="PPT 声称“仅2家·位置偏角”；PDF 热门到访表内可见 3 个咖啡相关 POI，但该表不等于完整供给清单，需高德 POI 和现场清单核验。",
    )
    add(
        rows,
        metric_name="奥森PPT假设-瑜伽/普拉提园内现状店数",
        value="0",
        unit="家",
        source_file=olympic_gap["source_file"],
        source_page_or_slide="slide 5",
        source_quote=olympic_gap["snippet"],
        extraction_method="keyword_hits_manual_parse",
        evidence_type="presentation_assumption",
        confidence="assumption",
        validation_status="conflict",
        notes="PPT 声称“0家”；PDF 热门到访表可见“悦健达专项体能·康复·普拉提运动中心”，需高德 POI 和现场清单核验是否计入园内供给。",
    )

    olympic_finance = find_hit(
        hits,
        source_contains="奥森修改稿0306.pptx",
        unit_index=9,
        text_contains="合计 ¥1.13万 ¥5.06万 +¥3.93万 +¥1,430万",
    )
    for name, value, unit, quote_hint in [
        ("奥森PPT假设-P0改造当前日收益合计", "1.13", "万元/日", "合计 ¥1.13万"),
        ("奥森PPT假设-P0改造优化后日收益合计", "5.06", "万元/日", "¥5.06万"),
        ("奥森PPT假设-P0改造日收益增量", "3.93", "万元/日", "+¥3.93万"),
        ("奥森PPT假设-P0改造年收入增量", "1430", "万元/年", "+¥1,430万"),
        ("奥森PPT假设-P0基准回收期", "2.9", "月", "约2.9个月"),
        ("奥森PPT假设-P0总改造投入", "350", "万元", "¥350万"),
    ]:
        add(
            rows,
            metric_name=name,
            value=value,
            unit=unit,
            source_file=olympic_finance["source_file"],
            source_page_or_slide="slide 9",
            source_quote=olympic_finance["snippet"],
            extraction_method="keyword_hits_manual_parse",
            evidence_type="presentation_assumption",
            confidence="assumption",
            validation_status="needs_review",
            notes=f"PPT 财务测算假设；命中片段包含“{quote_hint}”，需回查转化率、客单价、分成和成本参数。",
        )


def add_ppt_supporting_pdf_metrics(rows: list[dict[str, str]], tables: dict[str, dict]) -> None:
    support_specs = [
        ("TBL-00038", "已育", "城市绿心样例-婚育已育占比", 1, "%"),
        ("TBL-00038", "已育", "城市绿心样例-婚育已育TGI", 3, "TGI指数"),
        ("TBL-00062", "星级酒店", "城市绿心样例-星级酒店偏好TGI", 3, "TGI指数"),
        ("TBL-00065", "国家级景点", "城市绿心样例-旅游景点国家级景点TGI", 3, "TGI指数"),
        ("TBL-00068", "咖啡厅", "城市绿心样例-娱乐休闲咖啡厅北京市大盘覆盖度", 2, "%"),
        ("TBL-00250", "瑜伽", "奥森样例-运动健身瑜伽人群覆盖度", 1, "%"),
        ("TBL-00250", "瑜伽", "奥森样例-运动健身瑜伽TGI", 3, "TGI指数"),
        ("TBL-00124", "2", "奥森样例-区域内流动人口普拉提相关热门POI指数", 2, "指数"),
    ]
    for table_id, key, name, value_index, unit in support_specs:
        table = tables[table_id]
        row = row_by_rank(table, key) if key.isdigit() else row_by_first_cell(table, key)
        value = row[value_index]
        if unit == "%":
            value = re.sub(r"[^0-9.]", "", str(value))
        add(
            rows,
            metric_name=name,
            value=value,
            unit=unit,
            source_file=table["source_file"],
            source_page_or_slide=f"page {table['page']}",
            source_quote=table_row_quote(table, row),
            extraction_method="pdf_native_table_jsonl",
            evidence_type="source_report_pdf",
            confidence="medium",
            validation_status="checked",
            notes=f"PPT 假设复核补充指标，来自 {table_id}；用于识别支持、部分支持或口径冲突。",
        )

    coffee_table = tables["TBL-00123"]
    coffee_rows = [
        row
        for row in coffee_table["rows"][1:]
        if len(row) > 1
        and ("咖啡" in str(row[1]).lower() or "coffee" in str(row[1]).lower())
    ]
    add(
        rows,
        metric_name="奥森样例-区域内流动人口娱乐休闲咖啡相关热门POI表内数量",
        value=len(coffee_rows),
        unit="个(热门表内)",
        source_file=coffee_table["source_file"],
        source_page_or_slide=f"page {coffee_table['page']}",
        source_quote=compact(
            f"{coffee_table['table_id']} 咖啡相关行："
            + "；".join(" / ".join(str(cell) for cell in row) for row in coffee_rows)
        ),
        extraction_method="pdf_native_table_jsonl_derived_count",
        evidence_type="source_report_pdf",
        confidence="medium",
        validation_status="checked",
        notes="这是热门到访表内咖啡相关 POI 数，不等于园内完整供给数量；用于提示 PPT“仅2家”需高德核验。",
    )


def write_ledger(rows: list[dict[str, str]]) -> None:
    with LEDGER.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_report(rows: list[dict[str, str]]) -> None:
    by_type: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for row in rows:
        by_type[row["evidence_type"]] = by_type.get(row["evidence_type"], 0) + 1
        by_status[row["validation_status"]] = by_status.get(row["validation_status"], 0) + 1

    lines = [
        "# 第一批证据入账报告",
        "",
        "## 结果",
        "",
        f"- 已写入 `40_quality_evidence/evidence_ledger.csv`：{len(rows)} 条指标。",
        f"- 证据类型统计：{by_type}",
        f"- 校验状态统计：{by_status}",
        "",
        "## 覆盖范围",
        "",
        "- 客流：城市绿心年总到访、日峰值、时均峰值；奥森日峰值和时均峰值。",
        "- TGI：餐饮消费、咖啡厅、美食/冷饮等与商业业态相关的画像指标。",
        "- POI：PDF 原生表格中的区域内美食类热门到访 POI 及人均消费。",
        "- 收益：PPT 方案中的年收益、投资额、回收期，均标记为 `presentation_assumption`。",
        "- 供需缺口：PPT 方案中的缺口数量和供给现状，均标记为 `needs_review`。",
        "- PPT 复核补充：追加婚育、酒店、旅游景点、瑜伽、普拉提、咖啡相关 PDF 支持指标。",
        "",
        "## 后续核验重点",
        "",
        "- PDF 指标目前只完成抽取一致性核验，仍需确认腾讯报告口径和样本定义。",
        "- PPT 收益和缺口指标不能直接进入最终结论，需回查财务参数、真实经营数据和高德 POI。",
        "- 双栏 PDF 表格后续要继续标准化拆分，避免左右栏混行影响批量入账。",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    hits = load_keyword_hits()
    tables = load_tables()
    rows: list[dict[str, str]] = []
    add_pdf_keyword_metrics(rows, hits)
    add_table_metrics(rows, tables)
    add_ppt_assumptions(rows, hits)
    add_ppt_supporting_pdf_metrics(rows, tables)
    write_ledger(rows)
    write_report(rows)
    print(f"wrote {len(rows)} rows to {LEDGER}")
    print(f"wrote report to {REPORT}")


if __name__ == "__main__":
    main()
