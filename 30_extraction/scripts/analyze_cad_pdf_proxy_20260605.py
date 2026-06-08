from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import fitz


ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT / "CAD图及其计划" / "奥森北园(字体放大)-改造建筑示意-Model(1).pdf"
QUALITY_DIR = ROOT / "40_quality_evidence"
KEYWORDS = [
    "桃花源",
    "白房子",
    "廉洁",
    "展馆",
    "西分区",
    "管理中心",
    "南门",
    "地下",
    "预埋",
    "露天剧场",
    "2A03",
    "咖啡",
    "餐饮",
    "文创",
    "康养",
    "瑜伽",
    "入口",
    "改造",
]


def extract_pdf_hits() -> dict[str, Any]:
    doc = fitz.open(PDF_PATH)
    hits: list[dict[str, Any]] = []
    page_summaries: list[dict[str, Any]] = []
    for page_index, page in enumerate(doc):
        text = page.get_text()
        page_summaries.append(
            {
                "page": page_index + 1,
                "text_length": len(text),
                "text_line_count": len([line for line in text.splitlines() if line.strip()]),
                "vector_drawing_count": len(page.get_drawings()),
            }
        )
        data = page.get_text("dict")
        for block in data.get("blocks", []):
            for line in block.get("lines", []):
                line_text = "".join(span.get("text", "") for span in line.get("spans", [])).strip()
                if not line_text:
                    continue
                matched = [keyword for keyword in KEYWORDS if keyword in line_text]
                if matched:
                    hits.append(
                        {
                            "page": page_index + 1,
                            "text": line_text,
                            "keywords": matched,
                            "bbox": [round(float(x), 4) for x in line.get("bbox", [])],
                        }
                    )
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_file": str(PDF_PATH.relative_to(ROOT)),
        "method": "PyMuPDF text + vector drawing scan; used as readable proxy for north CAD drawing.",
        "page_summaries": page_summaries,
        "hits": hits,
        "use_boundary": "PDF is a readable drawing proxy. It helps locate labels and cross-check DWG conversion, but does not replace georeferenced CAD/GIS calibration.",
    }


def main() -> None:
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    payload = extract_pdf_hits()
    json_path = QUALITY_DIR / "cad_pdf_proxy_analysis_20260605.json"
    md_path = QUALITY_DIR / "cad_pdf_proxy_analysis_20260605.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 北园 CAD PDF 可读代理解析（2026-06-05）",
        "",
        f"- 来源：`{payload['source_file']}`",
        f"- 方法：{payload['method']}",
        f"- 使用边界：{payload['use_boundary']}",
        "",
        "## 页面概况",
    ]
    for page in payload["page_summaries"]:
        lines.append(
            f"- 第 {page['page']} 页：文本 {page['text_length']} 字符，非空行 {page['text_line_count']}，矢量图元 {page['vector_drawing_count']}"
        )
    lines.extend(["", "## 关键词命中"])
    for hit in payload["hits"][:80]:
        lines.append(f"- 第 {hit['page']} 页：{hit['text']}；关键词 {', '.join(hit['keywords'])}；bbox {hit['bbox']}")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"hits": len(payload["hits"]), "json": str(json_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
