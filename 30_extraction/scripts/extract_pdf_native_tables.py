from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import fitz


ROOT = Path(__file__).resolve().parents[2]
RAW_PDF_DIR = ROOT / "20_raw_data" / "pdf"
OUT_DIR = ROOT / "30_extraction" / "tables"
SUMMARY_PATH = OUT_DIR / "pdf_native_tables_summary.csv"
JSONL_PATH = OUT_DIR / "pdf_native_tables.jsonl"


def normalize_cell(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_rows: list[dict[str, Any]] = []
    table_count = 0

    with JSONL_PATH.open("w", encoding="utf-8") as jsonl:
        for pdf_path in sorted(RAW_PDF_DIR.glob("*.pdf")):
            rel = pdf_path.relative_to(ROOT).as_posix()
            doc = fitz.open(str(pdf_path))
            for page_index, page in enumerate(doc, start=1):
                try:
                    found = page.find_tables()
                    tables = found.tables
                except Exception as exc:
                    summary_rows.append(
                        {
                            "table_id": "",
                            "source_file": rel,
                            "page": page_index,
                            "table_index": "",
                            "row_count": "",
                            "column_count": "",
                            "bbox": "",
                            "status": "error",
                            "sample": repr(exc),
                        }
                    )
                    continue

                for table_index, table in enumerate(tables, start=1):
                    table_count += 1
                    rows = [[normalize_cell(cell) for cell in row] for row in table.extract()]
                    row_count = len(rows)
                    column_count = max((len(row) for row in rows), default=0)
                    table_id = f"TBL-{table_count:05d}"
                    sample = " | ".join(" / ".join(row) for row in rows[:3])[:260]
                    # 内联质量指标：下游自动门控依赖这两个字段，无需 Codex 手动核查
                    total_cells = row_count * column_count
                    filled_cells = sum(1 for row in rows for cell in row if cell.strip())
                    fill_rate = round(filled_cells / total_cells, 3) if total_cells > 0 else 0.0
                    if fill_rate >= 0.7:
                        quality_flag = "good"
                    elif fill_rate >= 0.3:
                        quality_flag = "partial"
                    else:
                        quality_flag = "empty"
                    record = {
                        "table_id": table_id,
                        "source_file": rel,
                        "page": page_index,
                        "table_index": table_index,
                        "bbox": list(table.bbox) if getattr(table, "bbox", None) else [],
                        "row_count": row_count,
                        "column_count": column_count,
                        "fill_rate": fill_rate,
                        "quality_flag": quality_flag,
                        "rows": rows,
                    }
                    jsonl.write(json.dumps(record, ensure_ascii=False) + "\n")
                    summary_rows.append(
                        {
                            "table_id": table_id,
                            "source_file": rel,
                            "page": page_index,
                            "table_index": table_index,
                            "row_count": row_count,
                            "column_count": column_count,
                            "fill_rate": fill_rate,
                            "quality_flag": quality_flag,
                            "bbox": json.dumps(record["bbox"], ensure_ascii=False),
                            "status": "ok",
                            "sample": sample,
                        }
                    )

    fieldnames = ["table_id", "source_file", "page", "table_index", "row_count", "column_count", "fill_rate", "quality_flag", "bbox", "status", "sample"]
    with SUMMARY_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"native_pdf_tables={table_count} -> {SUMMARY_PATH}; {JSONL_PATH}")


if __name__ == "__main__":
    main()
