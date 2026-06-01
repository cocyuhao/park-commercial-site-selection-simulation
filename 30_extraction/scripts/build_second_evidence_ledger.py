from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "30_extraction" / "scripts"
PDF_TEXT_DIR = ROOT / "30_extraction" / "pdf_text"
LEDGER = ROOT / "40_quality_evidence" / "evidence_ledger.csv"
REVIEW_CSV = ROOT / "40_quality_evidence" / "second_evidence_ledger_review.csv"
REPORT = ROOT / "40_quality_evidence" / "second_evidence_ledger_report.md"

sys.path.insert(0, str(SCRIPT_DIR))
import build_first_evidence_ledger as first  # noqa: E402


FIELDS = first.FIELDS

SKIP_EXISTING_TABLE_ROW_FIELDS = {
    ("TBL-00049", "101-150元", "占比"),
    ("TBL-00049", "101-150元", "TGI"),
    ("TBL-00119", "1", "指数"),
    ("TBL-00119", "1", "人均消费"),
    ("TBL-00200", "51-100元", "占比"),
    ("TBL-00200", "101-150元", "TGI"),
    ("TBL-00201", "11次及以上", "占比"),
    ("TBL-00201", "11次及以上", "TGI"),
}


PROFILE_TABLES = [
    {"table_id": "TBL-00046", "park": "城市绿心", "population": "流动人口", "dimension": "全国消费水平v2"},
    {"table_id": "TBL-00049", "park": "城市绿心", "population": "流动人口", "dimension": "餐饮消费水平"},
    {"table_id": "TBL-00054", "park": "城市绿心", "population": "流动人口", "dimension": "酒店消费价格等级"},
    {"table_id": "TBL-00055", "park": "城市绿心", "population": "流动人口", "dimension": "酒店消费水平"},
    {"table_id": "TBL-00058", "park": "城市绿心", "population": "流动人口", "dimension": "出游月份", "share_label": "人群覆盖度"},
    {"table_id": "TBL-00194", "park": "奥森", "population": "流动人口", "dimension": "活跃商圈v2", "has_tgi": False, "share_label": "人群覆盖度"},
    {"table_id": "TBL-00198", "park": "奥森", "population": "全部人口", "dimension": "全国消费水平v2"},
    {"table_id": "TBL-00199", "park": "奥森", "population": "全部人口", "dimension": "酒店消费水平"},
    {"table_id": "TBL-00200", "park": "奥森", "population": "全部人口", "dimension": "餐饮消费水平"},
    {"table_id": "TBL-00201", "park": "奥森", "population": "全部人口", "dimension": "餐饮消费频次"},
    {"table_id": "TBL-00202", "park": "奥森", "population": "全部人口", "dimension": "商场到店频次"},
    {"table_id": "TBL-00213", "park": "奥森", "population": "工作人口", "dimension": "商场到店频次"},
    {"table_id": "TBL-00215", "park": "奥森", "population": "工作人口", "dimension": "酒店消费水平"},
    {"table_id": "TBL-00216", "park": "奥森", "population": "工作人口", "dimension": "全国消费水平v2"},
    {"table_id": "TBL-00217", "park": "奥森", "population": "工作人口", "dimension": "城市消费水平v2"},
    {"table_id": "TBL-00218", "park": "奥森", "population": "工作人口", "dimension": "餐饮消费频次"},
]


def rebuild_first_batch() -> list[dict[str, str]]:
    hits = first.load_keyword_hits()
    tables = first.load_tables()
    rows: list[dict[str, str]] = []
    first.add_pdf_keyword_metrics(rows, hits)
    first.add_table_metrics(rows, tables)
    first.add_ppt_assumptions(rows, hits)
    first.add_ppt_supporting_pdf_metrics(rows, tables)
    return rows


def normalize_number(value: Any) -> str:
    return re.sub(r"[^0-9.]", "", str(value or ""))


def pdf_page_context(source_file: str, page: int) -> str:
    stem = Path(source_file).stem
    candidates = [path for path in PDF_TEXT_DIR.glob("*.json") if path.stem == stem]
    if not candidates:
        return ""
    data = json.loads(candidates[0].read_text(encoding="utf-8"))
    for item in data.get("pages", []):
        if int(item.get("page", 0)) == int(page):
            text = re.sub(r"\s+", " ", item.get("text", "")).strip()
            period_match = re.search(r"\d{8}-\d{8}期间到访.+", text)
            return first.compact(period_match.group(0) if period_match else text, 180)
    return ""


def add_checked_metric(
    rows: list[dict[str, str]],
    *,
    metric_name: str,
    value: str,
    unit: str,
    table: dict[str, Any],
    row: list[str],
    notes: str,
) -> None:
    quote = first.table_row_quote(table, row)
    context = pdf_page_context(table["source_file"], table["page"])
    if context:
        quote = first.compact(f"{quote}；页面解读：{context}", 260)
    first.add(
        rows,
        metric_name=metric_name,
        value=value,
        unit=unit,
        source_file=table["source_file"],
        source_page_or_slide=f"page {table['page']}",
        source_quote=quote,
        extraction_method="pdf_native_table_jsonl_second_batch",
        evidence_type="source_report_pdf",
        confidence="medium",
        validation_status="checked",
        notes=notes,
    )


def add_profile_distribution_metrics(rows: list[dict[str, str]], tables: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    review_rows: list[dict[str, str]] = []
    existing_names = {row["metric_name"] for row in rows}

    for spec in PROFILE_TABLES:
        table = tables[spec["table_id"]]
        header = [str(cell) for cell in table["rows"][0]]
        has_tgi = spec.get("has_tgi", True) and "TGI" in header
        share_label = str(spec.get("share_label", "占比"))
        share_index = header.index(share_label)
        tgi_index = header.index("TGI") if has_tgi else None
        dimension = spec["dimension"]
        park = spec["park"]
        population = spec["population"]

        for row in table["rows"][1:]:
            label = str(row[0]).strip()
            if not label:
                continue
            source_key = label
            share_value = normalize_number(row[share_index])
            share_metric_name = f"{park}样例-{population}-{dimension}{label}{share_label}"
            if (table["table_id"], source_key, share_label) in SKIP_EXISTING_TABLE_ROW_FIELDS:
                review_rows.append({"table_id": table["table_id"], "row_key": source_key, "field": share_label, "status": "skipped_existing_first_batch"})
            elif share_metric_name not in existing_names:
                add_checked_metric(
                    rows,
                    metric_name=share_metric_name,
                    value=share_value,
                    unit="%",
                    table=table,
                    row=row,
                    notes=(
                        f"第二批 PDF 原生表格入账；{population}画像分布指标。"
                        "DeepSeek 仅用于候选发现，本行由本地脚本按表头和原始行确认。"
                    ),
                )
                existing_names.add(share_metric_name)
                review_rows.append({"table_id": table["table_id"], "row_key": source_key, "field": share_label, "status": "added"})

            if tgi_index is not None:
                tgi_metric_name = f"{park}样例-{population}-{dimension}{label}TGI"
                if (table["table_id"], source_key, "TGI") in SKIP_EXISTING_TABLE_ROW_FIELDS:
                    review_rows.append({"table_id": table["table_id"], "row_key": source_key, "field": "TGI", "status": "skipped_existing_first_batch"})
                elif tgi_metric_name not in existing_names:
                    add_checked_metric(
                        rows,
                        metric_name=tgi_metric_name,
                        value=normalize_number(row[tgi_index]),
                        unit="TGI指数",
                        table=table,
                        row=row,
                        notes=(
                            f"第二批 PDF 原生表格入账；{population}画像 TGI 指标。"
                            "TGI 只代表相对偏好/覆盖，不代表客流峰值或供给数量。"
                        ),
                    )
                    existing_names.add(tgi_metric_name)
                    review_rows.append({"table_id": table["table_id"], "row_key": source_key, "field": "TGI", "status": "added"})
    return review_rows


def rank_label(rank: str) -> str:
    return {"1": "第一名", "2": "第二名", "3": "第三名"}.get(rank, f"第{rank}名")


def add_poi_spending_metrics(rows: list[dict[str, str]], tables: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    review_rows: list[dict[str, str]] = []
    existing_names = {row["metric_name"] for row in rows}
    table = tables["TBL-00119"]
    for row in table["rows"][1:]:
        rank = str(row[0]).strip()
        if not rank:
            continue
        poi_name = str(row[1]).strip()
        index_name = f"奥森样例-区域内流动人口美食类热门到访POI{rank_label(rank)}指数"
        cost_name = f"奥森样例-区域内流动人口美食类热门到访POI{rank_label(rank)}人均消费"
        if (table["table_id"], rank, "指数") in SKIP_EXISTING_TABLE_ROW_FIELDS:
            review_rows.append({"table_id": table["table_id"], "row_key": rank, "field": "指数", "status": "skipped_existing_first_batch"})
        elif index_name not in existing_names:
            add_checked_metric(
                rows,
                metric_name=index_name,
                value=normalize_number(row[2]),
                unit="指数",
                table=table,
                row=row,
                notes=f"第二批 PDF 原生表格入账；热门到访 POI 为“{poi_name}”。热门到访表不等于完整园内供给清单。",
            )
            existing_names.add(index_name)
            review_rows.append({"table_id": table["table_id"], "row_key": rank, "field": "指数", "status": "added"})

        cost_match = re.search(r"人均消费\s*([0-9.]+)\s*元", str(row[3]))
        if cost_match:
            if (table["table_id"], rank, "人均消费") in SKIP_EXISTING_TABLE_ROW_FIELDS:
                review_rows.append({"table_id": table["table_id"], "row_key": rank, "field": "人均消费", "status": "skipped_existing_first_batch"})
            elif cost_name not in existing_names:
                add_checked_metric(
                    rows,
                    metric_name=cost_name,
                    value=cost_match.group(1),
                    unit="元/人",
                    table=table,
                    row=row,
                    notes=f"第二批 PDF 原生表格入账；热门到访 POI 为“{poi_name}”。人均消费来自扩展信息字段。",
                )
                existing_names.add(cost_name)
                review_rows.append({"table_id": table["table_id"], "row_key": rank, "field": "人均消费", "status": "added"})
    return review_rows


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_ledger(rows: list[dict[str, str]]) -> None:
    write_csv(LEDGER, rows, FIELDS)


def write_report(rows: list[dict[str, str]], review_rows: list[dict[str, str]]) -> None:
    by_type = Counter(row["evidence_type"] for row in rows)
    by_status = Counter(row["validation_status"] for row in rows)
    review_status = Counter(row["status"] for row in review_rows)
    second_batch = [row for row in rows if row["extraction_method"] == "pdf_native_table_jsonl_second_batch"]
    by_unit = Counter(row["unit"] for row in second_batch)
    lines = [
        "# 第二批证据入账报告",
        "",
        "## 结果",
        "",
        f"- `evidence_ledger.csv` 当前共 {len(rows)} 条指标。",
        f"- 第二批新增 {len(second_batch)} 条 PDF 原生表格指标。",
        f"- 入账动作统计：{dict(sorted(review_status.items()))}",
        f"- 全台账证据类型统计：{dict(sorted(by_type.items()))}",
        f"- 全台账校验状态统计：{dict(sorted(by_status.items()))}",
        f"- 第二批单位统计：{dict(sorted(by_unit.items()))}",
        "",
        "## 第二批范围",
        "",
        "- 城市绿心流动人口：全国消费水平、餐饮消费水平、酒店消费价格等级、酒店消费水平、出游月份。",
        "- 奥森全部人口：全国消费水平、酒店消费水平、餐饮消费水平、餐饮消费频次、商场到店频次。",
        "- 奥森流动人口：活跃商圈覆盖度。",
        "- 奥森工作人口：商场到店频次、酒店消费水平、全国消费水平、城市消费水平、餐饮消费频次。",
        "- 奥森区域内流动人口：美食类热门到访 POI 第二、第三名指数和人均消费。",
        "",
        "## 口径限制",
        "",
        "- DeepSeek 只用于发现候选；本次入账由本地脚本按 PDF 原生表格表头和原始行确认。",
        "- 画像覆盖度、占比和 TGI 不能解释为客流峰值、供给数量或收益。",
        "- 热门到访 POI 不等于完整园内供给清单，仍需高德/现场核验。",
        "- PDF 原生表格抽取仍可能受双栏或 OCR 结构影响，后续报告引用前应抽样查看原 PDF 页面。",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    tables = first.load_tables()
    rows = rebuild_first_batch()
    review_rows = []
    review_rows.extend(add_profile_distribution_metrics(rows, tables))
    review_rows.extend(add_poi_spending_metrics(rows, tables))
    write_ledger(rows)
    write_csv(REVIEW_CSV, review_rows, ["table_id", "row_key", "field", "status"])
    write_report(rows, review_rows)
    print(f"wrote {len(rows)} rows to {LEDGER}")
    print(f"second_batch_added={sum(1 for row in review_rows if row['status'] == 'added')}")
    print(f"wrote review to {REVIEW_CSV}")
    print(f"wrote report to {REPORT}")


if __name__ == "__main__":
    main()
