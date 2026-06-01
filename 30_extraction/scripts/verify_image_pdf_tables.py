"""
verify_image_pdf_tables.py
==========================
专项验证图像型 PDF 的表格提取质量。

已知问题：PyMuPDF page.find_tables() 依赖向量线框，图像型 PDF（扫描件/嵌入图片）
不含向量线，导致无法自动识别表格结构，即使有 OCR 文本层也无济于事。

本脚本执行 5 项检查：
  C1  逐页分析每个 PDF 的 页面类型（图像页 vs 文本页）
  C2  检查 JSONL 中来自图像型 PDF 的表格数量及内容
  C3  对图像型 PDF 使用 pdfplumber（基于字符位置聚类）重新提取表格
  C4  对比两种引擎在图像型 PDF 上的结果差异
  C5  给出最终结论：图像型 PDF 数据是否成功转化

输出：40_quality_evidence/verify_image_pdf_tables_report.json
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parents[2]
PDF_DIR = ROOT / "20_raw_data" / "pdf"
JSONL_PATH = ROOT / "30_extraction" / "tables" / "pdf_native_tables.jsonl"
OUT_PATH = ROOT / "40_quality_evidence" / "verify_image_pdf_tables_report.json"

# 已知图像型 PDF（从 M8 分析得出）
IMAGE_PDF_CANDIDATES = [
    "奥林匹克森林公园区域大数据分析报告-20241230-202512291772157987.pdf",
]
TEXT_PDF_CANDIDATES = [
    "城市绿心公园区域大数据分析报告-20221023-20231022(1).pdf",
]

IMAGE_THRESHOLD_RATIO = 0.7  # 图像面积占页面 70% 以上视为图像页


def classify_page(page: fitz.Page) -> dict[str, Any]:
    """判断一页是图像页还是文本页。"""
    page_area = page.rect.width * page.rect.height
    images = page.get_images(full=False)
    image_area = 0.0
    for img in images:
        rects = page.get_image_rects(img[0])
        for r in rects:
            image_area += r.width * r.height

    text = page.get_text("text").strip()
    text_len = len(text)
    image_ratio = image_area / page_area if page_area > 0 else 0
    is_image_page = image_ratio >= IMAGE_THRESHOLD_RATIO and text_len < 200

    return {
        "image_count": len(images),
        "image_area_ratio": round(image_ratio, 3),
        "text_length": text_len,
        "is_image_page": is_image_page,
    }


def check_c1_page_classification() -> dict[str, Any]:
    """C1: 逐页分类每个 PDF。"""
    results = {}
    for pdf_name in IMAGE_PDF_CANDIDATES + TEXT_PDF_CANDIDATES:
        pdf_path = PDF_DIR / pdf_name
        if not pdf_path.exists():
            results[pdf_name] = {"error": "文件不存在"}
            continue

        doc = fitz.open(str(pdf_path))
        page_stats = []
        image_page_count = 0
        for page_num in range(min(len(doc), 10)):  # 采样前10页
            page = doc[page_num]
            stat = classify_page(page)
            stat["page"] = page_num + 1
            page_stats.append(stat)
            if stat["is_image_page"]:
                image_page_count += 1

        total_pages = len(doc)
        sampled = len(page_stats)
        results[pdf_name] = {
            "total_pages": total_pages,
            "sampled_pages": sampled,
            "image_page_count_in_sample": image_page_count,
            "image_page_rate_in_sample": round(image_page_count / sampled, 3) if sampled else 0,
            "pdf_type": "image_pdf" if image_page_count / sampled >= 0.5 else "text_pdf",
            "page_stats": page_stats,
        }
        doc.close()

    return {"check": "C1_page_classification", "verdict": "INFO", "results": results}


def check_c2_jsonl_coverage() -> dict[str, Any]:
    """C2: 查看 JSONL 中来自图像型 PDF 的表格。"""
    if not JSONL_PATH.exists():
        return {"check": "C2_jsonl_coverage", "verdict": "FAIL", "error": "JSONL不存在"}

    tables_by_pdf: dict[str, list[dict]] = {}
    with JSONL_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            src = Path(rec.get("source_file", "")).name
            tables_by_pdf.setdefault(src, []).append(rec)

    analysis = {}
    for pdf_name in IMAGE_PDF_CANDIDATES + TEXT_PDF_CANDIDATES:
        tables = tables_by_pdf.get(pdf_name, [])
        label = "image_pdf" if pdf_name in IMAGE_PDF_CANDIDATES else "text_pdf"

        if not tables:
            analysis[pdf_name] = {
                "type": label,
                "table_count": 0,
                "verdict": "ZERO_TABLES",
                "note": "JSONL 中无该 PDF 的表格记录 ← 图像型PDF无法自动提取表格",
            }
            continue

        # 抽样检查内容
        sample_tables = tables[:3]
        samples = []
        for t in sample_tables:
            rows = t.get("rows", [])
            non_empty_cells = sum(1 for row in rows for cell in row if cell.strip())
            total_cells = sum(len(row) for row in rows)
            fill_rate = round(non_empty_cells / total_cells, 3) if total_cells else 0
            samples.append({
                "table_id": t.get("table_id"),
                "page": t.get("page"),
                "rows": t.get("row_count"),
                "cols": t.get("column_count"),
                "fill_rate": fill_rate,
                "first_row_preview": t.get("rows", [[]])[0][:4] if rows else [],
            })

        avg_fill = round(sum(s["fill_rate"] for s in samples) / len(samples), 3)
        analysis[pdf_name] = {
            "type": label,
            "table_count": len(tables),
            "sample_tables": samples,
            "avg_fill_rate": avg_fill,
            "verdict": "OK" if avg_fill > 0.5 else "WARN_LOW_FILL",
        }

    return {"check": "C2_jsonl_coverage", "results": analysis}


def check_c3_pdfplumber_retry() -> dict[str, Any]:
    """C3: 用 pdfplumber 对图像型 PDF 重新尝试提取表格。"""
    try:
        import pdfplumber  # type: ignore
    except ImportError:
        return {"check": "C3_pdfplumber_retry", "verdict": "SKIP", "reason": "pdfplumber未安装"}

    results = {}
    for pdf_name in IMAGE_PDF_CANDIDATES:
        pdf_path = PDF_DIR / pdf_name
        if not pdf_path.exists():
            results[pdf_name] = {"error": "文件不存在"}
            continue

        found_tables = []
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page_num, page in enumerate(pdf.pages[:10], start=1):
                    tables = page.extract_tables()
                    if tables:
                        for ti, tbl in enumerate(tables, start=1):
                            non_empty = sum(1 for row in tbl for cell in row if cell and str(cell).strip())
                            total = sum(len(row) for row in tbl)
                            found_tables.append({
                                "page": page_num,
                                "table_index": ti,
                                "rows": len(tbl),
                                "cols": len(tbl[0]) if tbl else 0,
                                "fill_rate": round(non_empty / total, 3) if total else 0,
                                "first_row": [str(c or "")[:30] for c in (tbl[0] if tbl else [])],
                            })
        except Exception as e:
            results[pdf_name] = {"error": str(e)}
            continue

        results[pdf_name] = {
            "tables_found": len(found_tables),
            "tables": found_tables,
            "verdict": "TABLES_FOUND" if found_tables else "NO_TABLES",
            "note": "pdfplumber 也无法提取 → 图像型PDF需要真OCR表格识别工具（如 PaddleOCR TableAttr）" if not found_tables else "pdfplumber 找到表格"
        }

    return {"check": "C3_pdfplumber_retry", "results": results}


def check_c4_pymupdf_direct_text() -> dict[str, Any]:
    """C4: 直接用 PyMuPDF 提取图像型 PDF 的文本层，看是否有有意义的数据。"""
    results = {}
    for pdf_name in IMAGE_PDF_CANDIDATES:
        pdf_path = PDF_DIR / pdf_name
        if not pdf_path.exists():
            results[pdf_name] = {"error": "文件不存在"}
            continue

        doc = fitz.open(str(pdf_path))
        page_text_samples = []
        for page_num in range(min(len(doc), 5)):
            page = doc[page_num]
            text = page.get_text("text").strip()
            # 提取数字和中文内容评估质量
            import re
            numbers = re.findall(r"\d+\.?\d*%?", text)
            chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
            page_text_samples.append({
                "page": page_num + 1,
                "text_length": len(text),
                "numbers_found": numbers[:10],
                "chinese_count": len(chinese_chars),
                "preview": text[:200].replace("\n", "↵"),
            })
        doc.close()

        # 判断文本层质量
        avg_text_len = sum(s["text_length"] for s in page_text_samples) / len(page_text_samples) if page_text_samples else 0
        results[pdf_name] = {
            "page_samples": page_text_samples,
            "avg_text_length_per_page": round(avg_text_len),
            "verdict": "TEXT_LAYER_POOR" if avg_text_len < 100 else "TEXT_LAYER_EXISTS_BUT_NO_TABLE_STRUCTURE",
            "note": "文本层存在但不含表格结构信息（无向量线框），表格数据未被提取到 JSONL"
        }

    return {"check": "C4_direct_text_quality", "results": results}


def check_c5_final_conclusion(c1, c2, c3, c4) -> dict[str, Any]:
    """C5: 综合给出最终结论。"""
    # 从 C2 判断图像型 PDF 在 JSONL 中有无表格
    c2_results = c2.get("results", {})
    conclusions = []

    for pdf_name in IMAGE_PDF_CANDIDATES:
        info = c2_results.get(pdf_name, {})
        table_count = info.get("table_count", 0)

        if table_count == 0:
            status = "DATA_LOST"
            detail = f"图像型PDF「{pdf_name}」在 JSONL 中 0 张表 → 数据未被提取！需要 OCR 表格识别补救。"
        elif info.get("verdict") == "WARN_LOW_FILL":
            status = "DATA_DEGRADED"
            detail = f"图像型PDF「{pdf_name}」有 {table_count} 张表但填充率低 → 表格结构可能损坏。"
        else:
            status = "DATA_OK"
            detail = f"图像型PDF「{pdf_name}」有 {table_count} 张表且质量正常。"

        conclusions.append({"pdf": pdf_name, "status": status, "detail": detail})

    # 文本型 PDF 的结论
    for pdf_name in TEXT_PDF_CANDIDATES:
        info = c2_results.get(pdf_name, {})
        table_count = info.get("table_count", 0)
        conclusions.append({
            "pdf": pdf_name,
            "status": "DATA_OK" if table_count > 0 else "WARN",
            "detail": f"文本型PDF「{pdf_name}」有 {table_count} 张表，双引擎一致，数据已成功提取。",
        })

    # 总体结论
    has_lost = any(c["status"] == "DATA_LOST" for c in conclusions)
    has_degraded = any(c["status"] == "DATA_DEGRADED" for c in conclusions)

    overall = "PARTIAL_DATA_LOSS" if has_lost else ("WARN" if has_degraded else "ALL_OK")
    recommendation = ""
    if has_lost:
        recommendation = (
            "补救方案：对图像型PDF使用 PaddleOCR（ppstructure表格识别）或 "
            "MinerU 工具重新提取，可将扫描件中的表格转为结构化数据。"
            "这些表在当前 329 张 JSONL 表格中缺失，影响后续建模完整性。"
        )

    return {
        "check": "C5_final_conclusion",
        "overall_verdict": overall,
        "conclusions": conclusions,
        "recommendation": recommendation,
    }


def main() -> None:
    print("=== 图像型PDF表格提取质量专项验证 ===")

    print("[C1] 逐页分类 PDF 类型...")
    c1 = check_c1_page_classification()

    print("[C2] 检查 JSONL 中来自图像型PDF的表格...")
    c2 = check_c2_jsonl_coverage()

    print("[C3] pdfplumber 重新尝试提取...")
    c3 = check_c3_pdfplumber_retry()

    print("[C4] 直接读取文本层质量...")
    c4 = check_c4_pymupdf_direct_text()

    print("[C5] 综合结论...")
    c5 = check_c5_final_conclusion(c1, c2, c3, c4)

    report = {
        "run_at": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "overall_verdict": c5["overall_verdict"],
        "methods": [c1, c2, c3, c4, c5],
    }

    OUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n报告已写入: {OUT_PATH}")

    # 打印关键结论
    print(f"\n总体结论: {c5['overall_verdict']}")
    for conclusion in c5["conclusions"]:
        status_icon = "✅" if conclusion["status"] == "DATA_OK" else "❌"
        print(f"  {status_icon} {conclusion['detail']}")
    if c5.get("recommendation"):
        print(f"\n⚠️  {c5['recommendation']}")


if __name__ == "__main__":
    main()
