"""
PDF 表格数据质量综合验证脚本 (Python 3.12)

验证方法:
  M5 - 双引擎交叉验证 (pdfplumber vs PyMuPDF) - 文本型PDF表格提取一致性
  M6 - 数据质量统计分析 (329张表空行率/噪声率/有效数据率)
  M7 - 结构完整性校验 (CSV row_count vs JSONL实际行数对比)
  M8 - 语义内容验证 (中文比例、数字字段检测、关键词命中率)

输出: 40_quality_evidence/verify_pdf_tables_report.json
"""

from __future__ import annotations

import csv
import json
import re
import statistics
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pdfplumber
import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "40_quality_evidence"
REPORT_FILE = OUT_DIR / "verify_pdf_tables_report.json"

TABLES_JSONL = ROOT / "30_extraction" / "tables" / "pdf_native_tables.jsonl"
TABLES_CSV = ROOT / "30_extraction" / "tables" / "pdf_native_tables_summary.csv"
TEXT_PDF = ROOT / "20_raw_data" / "pdf" / "城市绿心公园区域大数据分析报告-20221023-20231022(1).pdf"
IMG_PDF = ROOT / "20_raw_data" / "pdf" / "奥林匹克森林公园区域大数据分析报告-20241230-202512291772157987.pdf"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _is_noise_cell(cell: str | None) -> bool:
    """判断单元格是否为噪声(空格/斜杠/分隔符)."""
    if cell is None:
        return True
    cleaned = re.sub(r"[\s/|\\,.\-—–]", "", str(cell))
    return len(cleaned) == 0


def _has_chinese(text: str) -> bool:
    return any("\u4e00" <= c <= "\u9fff" for c in text)


def _has_number(text: str) -> bool:
    return bool(re.search(r"\d+\.?\d*%?", text))


def _chinese_ratio(cells: list[str]) -> float:
    non_empty = [c for c in cells if c and c.strip()]
    if not non_empty:
        return 0.0
    return sum(1 for c in non_empty if _has_chinese(c)) / len(non_empty)


def _number_ratio(cells: list[str]) -> float:
    non_empty = [c for c in cells if c and c.strip()]
    if not non_empty:
        return 0.0
    return sum(1 for c in non_empty if _has_number(c)) / len(non_empty)


# ---------------------------------------------------------------------------
# M5 - 双引擎交叉验证 (pdfplumber vs PyMuPDF)
# ---------------------------------------------------------------------------

def method5_dual_engine() -> dict:
    """
    对文本型PDF(城市绿心)同时用pdfplumber和PyMuPDF提取前10页的表格,
    对比: 表格数量、行列数分布、内容相似度.
    """
    print("\n[M5] 双引擎交叉验证 (pdfplumber vs PyMuPDF)...")
    result: dict = {
        "method": "M5_dual_engine",
        "description": "pdfplumber vs PyMuPDF 在文本型PDF上表格提取一致性",
        "pdf": TEXT_PDF.name,
    }

    if not TEXT_PDF.exists():
        result["verdict"] = "SKIP"
        result["verdict_detail"] = f"PDF文件不存在: {TEXT_PDF.name}"
        return result

    PAGES_TO_CHECK = 10  # 前10页

    # --- pdfplumber ---
    plumber_tables: list[dict] = []
    try:
        with pdfplumber.open(str(TEXT_PDF)) as pdf:
            for page_num in range(min(PAGES_TO_CHECK, len(pdf.pages))):
                page = pdf.pages[page_num]
                tables = page.extract_tables()
                for t_idx, table in enumerate(tables):
                    if table:
                        rows_clean = [[str(c or "") for c in row] for row in table]
                        plumber_tables.append({
                            "page": page_num + 1,
                            "table_index": t_idx + 1,
                            "rows": len(rows_clean),
                            "cols": max(len(r) for r in rows_clean) if rows_clean else 0,
                            "first_row": rows_clean[0] if rows_clean else [],
                        })
        print(f"  pdfplumber: 前{PAGES_TO_CHECK}页找到 {len(plumber_tables)} 张表")
    except Exception as exc:
        result["pdfplumber_error"] = str(exc)
        print(f"  pdfplumber ERROR: {exc}")

    # --- PyMuPDF ---
    pymupdf_tables: list[dict] = []
    try:
        doc = fitz.open(str(TEXT_PDF))
        for page_num in range(min(PAGES_TO_CHECK, len(doc))):
            page = doc[page_num]
            tabs = page.find_tables()
            if tabs and tabs.tables:
                for t_idx, tab in enumerate(tabs.tables):
                    tab_data = tab.extract()
                    if tab_data:
                        rows_clean = [[str(c or "") for c in row] for row in tab_data]
                        pymupdf_tables.append({
                            "page": page_num + 1,
                            "table_index": t_idx + 1,
                            "rows": len(rows_clean),
                            "cols": max(len(r) for r in rows_clean) if rows_clean else 0,
                            "first_row": rows_clean[0] if rows_clean else [],
                        })
        doc.close()
        print(f"  PyMuPDF:    前{PAGES_TO_CHECK}页找到 {len(pymupdf_tables)} 张表")
    except Exception as exc:
        result["pymupdf_error"] = str(exc)
        print(f"  PyMuPDF ERROR: {exc}")

    # --- 对比 ---
    result["pdfplumber_table_count"] = len(plumber_tables)
    result["pymupdf_table_count"] = len(pymupdf_tables)
    result["pdfplumber_tables"] = plumber_tables
    result["pymupdf_tables"] = pymupdf_tables

    # 比较同页同索引的表格行列数
    comparisons: list[dict] = []
    for pt in plumber_tables:
        key = (pt["page"], pt["table_index"])
        match = next(
            (mt for mt in pymupdf_tables if mt["page"] == key[0] and mt["table_index"] == key[1]),
            None,
        )
        if match:
            row_diff = abs(pt["rows"] - match["rows"])
            col_diff = abs(pt["cols"] - match["cols"])
            comparisons.append({
                "page": key[0],
                "table_index": key[1],
                "plumber_rows": pt["rows"],
                "pymupdf_rows": match["rows"],
                "plumber_cols": pt["cols"],
                "pymupdf_cols": match["cols"],
                "row_diff": row_diff,
                "col_diff": col_diff,
                "structure_match": row_diff <= 1 and col_diff <= 1,
            })
            status = "OK" if (row_diff <= 1 and col_diff <= 1) else "DIFF"
            print(f"  {status} Page{key[0]} T{key[1]}: pdfplumber {pt['rows']}r×{pt['cols']}c vs PyMuPDF {match['rows']}r×{match['cols']}c")

    result["cross_comparisons"] = comparisons
    if comparisons:
        match_rate = sum(1 for c in comparisons if c["structure_match"]) / len(comparisons)
        result["structure_match_rate"] = round(match_rate, 3)
        result["verdict"] = "PASS" if match_rate >= 0.8 else "WARN"
        result["verdict_detail"] = (
            f"双引擎找到 pdfplumber={len(plumber_tables)}, PyMuPDF={len(pymupdf_tables)}; "
            f"共有表格结构吻合率={match_rate:.1%} ({len(comparisons)}条对比)"
        )
    elif len(plumber_tables) == 0 and len(pymupdf_tables) == 0:
        result["verdict"] = "WARN"
        result["verdict_detail"] = f"前{PAGES_TO_CHECK}页均未检测到表格"
    else:
        result["verdict"] = "WARN"
        result["verdict_detail"] = (
            f"两引擎在同页同索引无交集 (plumber={len(plumber_tables)}, mupdf={len(pymupdf_tables)})"
        )

    print(f"  => {result['verdict']}: {result.get('verdict_detail', '')}")
    return result


# ---------------------------------------------------------------------------
# M6 - 数据质量统计分析
# ---------------------------------------------------------------------------

def method6_quality_stats() -> dict:
    """
    分析 pdf_native_tables.jsonl 中329张表的质量统计:
    - 空行率 (所有单元格均为噪声)
    - 有效行率 (至少有一个非噪声单元格)
    - 全空表比例
    - 每张表的平均有效行数
    - 中文字段比例
    - 数字字段比例
    """
    print("\n[M6] 数据质量统计分析 (329张表)...")
    result: dict = {
        "method": "M6_quality_stats",
        "description": "329张PDF原生表格的空行率/有效数据率/中文率/数字率统计",
    }

    if not TABLES_JSONL.exists():
        result["verdict"] = "SKIP"
        result["verdict_detail"] = f"JSONL不存在: {TABLES_JSONL}"
        return result

    lines = TABLES_JSONL.read_text(encoding="utf-8").strip().splitlines()
    total_tables = len(lines)

    empty_tables = 0      # 整张表全为噪声
    partial_tables = 0    # 有部分有效数据
    full_tables = 0       # 全部行均有效

    all_effective_rates: list[float] = []
    all_chinese_rates: list[float] = []
    all_number_rates: list[float] = []
    all_row_counts: list[int] = []
    all_col_counts: list[int] = []

    for line in lines:
        obj = json.loads(line)
        rows: list[list] = obj.get("rows", [])
        if not rows:
            empty_tables += 1
            all_effective_rates.append(0.0)
            all_chinese_rates.append(0.0)
            all_number_rates.append(0.0)
            continue

        all_row_counts.append(len(rows))
        all_col_counts.append(max(len(r) for r in rows) if rows else 0)

        all_cells = [str(cell or "") for row in rows for cell in row]
        non_noise_cells = [c for c in all_cells if not _is_noise_cell(c)]

        effective_rows = [
            row for row in rows
            if any(not _is_noise_cell(cell) for cell in row)
        ]
        eff_rate = len(effective_rows) / len(rows) if rows else 0.0
        all_effective_rates.append(eff_rate)

        cn_rate = _chinese_ratio(all_cells)
        num_rate = _number_ratio(all_cells)
        all_chinese_rates.append(cn_rate)
        all_number_rates.append(num_rate)

        if eff_rate == 0.0:
            empty_tables += 1
        elif eff_rate < 1.0:
            partial_tables += 1
        else:
            full_tables += 1

    avg_eff = statistics.mean(all_effective_rates) if all_effective_rates else 0.0
    avg_cn = statistics.mean(all_chinese_rates) if all_chinese_rates else 0.0
    avg_num = statistics.mean(all_number_rates) if all_number_rates else 0.0
    median_rows = statistics.median(all_row_counts) if all_row_counts else 0
    median_cols = statistics.median(all_col_counts) if all_col_counts else 0

    print(f"  总计: {total_tables} 张表")
    print(f"  全空噪声表: {empty_tables} ({empty_tables/total_tables:.1%})")
    print(f"  部分有效表: {partial_tables} ({partial_tables/total_tables:.1%})")
    print(f"  全部有效表: {full_tables} ({full_tables/total_tables:.1%})")
    print(f"  平均有效行率: {avg_eff:.1%}")
    print(f"  平均中文字段率: {avg_cn:.1%}")
    print(f"  平均数字字段率: {avg_num:.1%}")
    print(f"  中位行数: {median_rows}, 中位列数: {median_cols}")

    result.update({
        "total_tables": total_tables,
        "empty_noise_tables": empty_tables,
        "partial_valid_tables": partial_tables,
        "fully_valid_tables": full_tables,
        "empty_rate": round(empty_tables / total_tables, 3),
        "partial_rate": round(partial_tables / total_tables, 3),
        "full_rate": round(full_tables / total_tables, 3),
        "avg_effective_row_rate": round(avg_eff, 3),
        "avg_chinese_cell_rate": round(avg_cn, 3),
        "avg_number_cell_rate": round(avg_num, 3),
        "median_row_count": float(median_rows),
        "median_col_count": float(median_cols),
    })

    # 判断标准：全空率<50%且平均有效率>30% => PASS
    if empty_tables / total_tables < 0.5 and avg_eff > 0.3:
        result["verdict"] = "PASS"
        result["verdict_detail"] = (
            f"全空表={empty_tables/total_tables:.1%}, 平均有效行={avg_eff:.1%}, "
            f"中文率={avg_cn:.1%}, 数字率={avg_num:.1%}"
        )
    elif empty_tables / total_tables < 0.7:
        result["verdict"] = "WARN"
        result["verdict_detail"] = (
            f"全空表偏高={empty_tables/total_tables:.1%}, 需人工复查"
        )
    else:
        result["verdict"] = "FAIL"
        result["verdict_detail"] = f"全空表比例过高: {empty_tables/total_tables:.1%}"

    print(f"  => {result['verdict']}: {result['verdict_detail']}")
    return result


# ---------------------------------------------------------------------------
# M7 - 结构完整性校验 (CSV vs JSONL)
# ---------------------------------------------------------------------------

def method7_structure_integrity() -> dict:
    """
    对比 pdf_native_tables_summary.csv 中的 row_count/column_count
    与 pdf_native_tables.jsonl 中实际的行列数, 统计不一致率.
    """
    print("\n[M7] 结构完整性校验 (CSV declared vs JSONL actual)...")
    result: dict = {
        "method": "M7_structure_integrity",
        "description": "CSV声明的row_count/col_count vs JSONL实际行列数对比",
    }

    if not TABLES_JSONL.exists() or not TABLES_CSV.exists():
        result["verdict"] = "SKIP"
        result["verdict_detail"] = "JSONL或CSV文件不存在"
        return result

    # 读取CSV声明
    csv_decl: dict[str, dict] = {}
    with TABLES_CSV.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            csv_decl[row["table_id"]] = {
                "declared_rows": int(row.get("row_count") or 0),
                "declared_cols": int(row.get("column_count") or 0),
                "status": row.get("status", ""),
            }

    # 读取JSONL实际数据
    mismatches: list[dict] = []
    matches = 0
    total = 0

    lines = TABLES_JSONL.read_text(encoding="utf-8").strip().splitlines()
    for line in lines:
        obj = json.loads(line)
        tid = obj["table_id"]
        rows = obj.get("rows", [])
        actual_rows = len(rows)
        actual_cols = max((len(r) for r in rows), default=0)

        if tid not in csv_decl:
            continue

        declared_rows = csv_decl[tid]["declared_rows"]
        declared_cols = csv_decl[tid]["declared_cols"]
        total += 1

        row_ok = abs(actual_rows - declared_rows) <= 1
        col_ok = abs(actual_cols - declared_cols) <= 1

        if row_ok and col_ok:
            matches += 1
        else:
            mismatches.append({
                "table_id": tid,
                "declared_rows": declared_rows,
                "actual_rows": actual_rows,
                "declared_cols": declared_cols,
                "actual_cols": actual_cols,
                "row_diff": actual_rows - declared_rows,
                "col_diff": actual_cols - declared_cols,
            })

    if total == 0:
        result["verdict"] = "SKIP"
        result["verdict_detail"] = "无可对比数据"
        return result

    match_rate = matches / total
    print(f"  总计对比: {total} 张表")
    print(f"  结构一致: {matches} ({match_rate:.1%})")
    print(f"  不一致: {len(mismatches)}")
    if mismatches[:5]:
        print("  前5个不一致示例:")
        for m in mismatches[:5]:
            print(f"    {m['table_id']}: rows {m['declared_rows']}->{m['actual_rows']}, cols {m['declared_cols']}->{m['actual_cols']}")

    result.update({
        "total_compared": total,
        "structure_match": matches,
        "structure_mismatch": len(mismatches),
        "match_rate": round(match_rate, 3),
        "mismatches_sample": mismatches[:10],
    })
    result["verdict"] = "PASS" if match_rate >= 0.95 else ("WARN" if match_rate >= 0.80 else "FAIL")
    result["verdict_detail"] = (
        f"CSV vs JSONL结构一致率={match_rate:.1%} ({matches}/{total})"
    )

    print(f"  => {result['verdict']}: {result['verdict_detail']}")
    return result


# ---------------------------------------------------------------------------
# M8 - 语义内容验证
# ---------------------------------------------------------------------------

def method8_semantic_content() -> dict:
    """
    对有效表格内容进行语义验证:
    - 关键词命中率 (业务相关词: 客流/TGI/消费/排名/到访/人数等)
    - 数值格式验证 (百分比/绝对数/指数)
    - 奥森PDF文本层质量检查 (图像型PDF的OCR层)
    """
    print("\n[M8] 语义内容验证 (关键词命中/数值格式/图像PDF文本层)...")
    result: dict = {
        "method": "M8_semantic_content",
        "description": "关键词命中率、数值格式验证、图像PDF文本层质量",
    }

    # --- 8a: 关键词命中率 ---
    KEYWORDS = [
        "客流", "到访", "人数", "游客",       # 客流类
        "TGI", "偏好", "画像", "年龄",         # 画像/TGI
        "消费", "人均", "收入", "金额",         # 消费
        "排名", "占比", "比例", "百分",         # 统计
        "工作地", "居住", "来源",               # 职住
        "POI", "景点", "商圈", "品牌",         # POI
    ]

    if TABLES_JSONL.exists():
        lines = TABLES_JSONL.read_text(encoding="utf-8").strip().splitlines()
        kw_hit_tables = 0
        pct_format_tables = 0  # 含百分比格式
        abs_format_tables = 0  # 含绝对整数
        non_empty_tables = 0

        for line in lines:
            obj = json.loads(line)
            rows = obj.get("rows", [])
            if not rows:
                continue
            all_text = " ".join(str(c or "") for row in rows for c in row)
            if not all_text.strip():
                continue
            non_empty_tables += 1

            has_kw = any(kw in all_text for kw in KEYWORDS)
            has_pct = bool(re.search(r"\d+\.?\d*%", all_text))
            has_abs = bool(re.search(r"\b\d{3,}\b", all_text))  # 3位以上整数

            if has_kw:
                kw_hit_tables += 1
            if has_pct:
                pct_format_tables += 1
            if has_abs:
                abs_format_tables += 1

        kw_rate = kw_hit_tables / non_empty_tables if non_empty_tables else 0.0
        pct_rate = pct_format_tables / non_empty_tables if non_empty_tables else 0.0
        abs_rate = abs_format_tables / non_empty_tables if non_empty_tables else 0.0

        result["keyword_analysis"] = {
            "non_empty_tables": non_empty_tables,
            "keyword_hit_tables": kw_hit_tables,
            "keyword_hit_rate": round(kw_rate, 3),
            "percentage_format_rate": round(pct_rate, 3),
            "absolute_number_rate": round(abs_rate, 3),
            "keywords_checked": KEYWORDS,
        }
        print(f"  非空表: {non_empty_tables}, 关键词命中: {kw_hit_tables} ({kw_rate:.1%})")
        print(f"  含百分比: {pct_format_tables} ({pct_rate:.1%}), 含绝对数: {abs_format_tables} ({abs_rate:.1%})")

    # --- 8b: 图像型PDF文本层质量 (奥森) ---
    img_pdf_check: dict = {}
    if IMG_PDF.exists():
        try:
            doc = fitz.open(str(IMG_PDF))
            sample_pages = [0, 1, 2, 5, 10, 20, 50]
            page_stats: list[dict] = []
            for pi in sample_pages:
                if pi >= len(doc):
                    continue
                page = doc[pi]
                text = page.get_text().strip()
                imgs = page.get_images()
                words = text.split()
                cn_words = sum(1 for w in words if _has_chinese(w))
                page_stats.append({
                    "page": pi + 1,
                    "image_count": len(imgs),
                    "text_length": len(text),
                    "word_count": len(words),
                    "chinese_word_count": cn_words,
                    "has_text_layer": len(text) > 10,
                })
            doc.close()

            pages_with_text = sum(1 for p in page_stats if p["has_text_layer"])
            img_pdf_check = {
                "pdf_name": IMG_PDF.name,
                "sampled_pages": len(page_stats),
                "pages_with_text_layer": pages_with_text,
                "text_coverage": round(pages_with_text / len(page_stats), 3) if page_stats else 0.0,
                "page_stats": page_stats,
                "note": "图像型PDF: 有文本层说明含OCR叠加，但不代表表格可被直接提取",
            }
            print(f"  奥森PDF文本层: 抽样{len(page_stats)}页, 有文本层={pages_with_text}页 ({pages_with_text/len(page_stats):.1%})")
        except Exception as exc:
            img_pdf_check = {"error": str(exc)}
            print(f"  奥森PDF检查ERROR: {exc}")
    else:
        img_pdf_check = {"note": f"奥森PDF不存在: {IMG_PDF.name}"}

    result["image_pdf_text_layer"] = img_pdf_check

    # verdict
    kw_rate_val = result.get("keyword_analysis", {}).get("keyword_hit_rate", 0.0)
    if kw_rate_val >= 0.3:
        result["verdict"] = "PASS"
        result["verdict_detail"] = (
            f"业务关键词命中率={kw_rate_val:.1%} (≥30%), "
            f"百分比格式={result.get('keyword_analysis',{}).get('percentage_format_rate',0):.1%}"
        )
    elif kw_rate_val > 0:
        result["verdict"] = "WARN"
        result["verdict_detail"] = f"关键词命中率偏低={kw_rate_val:.1%}, 建议检查表格内容"
    else:
        result["verdict"] = "FAIL"
        result["verdict_detail"] = "无关键词命中, 表格内容可能全为噪声"

    print(f"  => {result['verdict']}: {result['verdict_detail']}")
    return result


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("PDF 表格数据质量综合验证 (4种方法)")
    print("=" * 60)

    run_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    results: list[dict] = []

    results.append(method5_dual_engine())
    results.append(method6_quality_stats())
    results.append(method7_structure_integrity())
    results.append(method8_semantic_content())

    verdicts = [r.get("verdict", "UNKNOWN") for r in results]
    pass_count = sum(1 for v in verdicts if v == "PASS")
    fail_count = sum(1 for v in verdicts if v == "FAIL")
    overall = "PASS" if fail_count == 0 else ("WARN" if pass_count > 0 else "FAIL")

    report = {
        "run_at": run_at,
        "tables_jsonl": str(TABLES_JSONL),
        "tables_csv": str(TABLES_CSV),
        "overall_verdict": overall,
        "summary": {
            "PASS": pass_count,
            "WARN": sum(1 for v in verdicts if v == "WARN"),
            "FAIL": fail_count,
            "SKIP": sum(1 for v in verdicts if v == "SKIP"),
        },
        "methods": results,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n报告已写入: {REPORT_FILE}")
    print(f"\n总体结果: {overall}  (PASS={pass_count}, FAIL={fail_count})")
    print("=" * 60)

    if fail_count > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
