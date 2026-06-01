from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PDF_TEXT_DIR = ROOT / "30_extraction" / "pdf_text"
PPT_TEXT_DIR = ROOT / "30_extraction" / "ppt_text"
OUT_PATH = ROOT / "40_quality_evidence" / "source_profile.csv"


def profile_pdf(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    pages = data.get("pages", [])
    text_lengths = [int(p.get("text_length", 0)) for p in pages]
    return {
        "source_file": data.get("source_file", path.name),
        "source_kind": "pdf",
        "unit_count": len(pages),
        "nonempty_units": sum(1 for x in text_lengths if x > 0),
        "total_text_length": sum(text_lengths),
        "min_text_length": min(text_lengths) if text_lengths else 0,
        "max_text_length": max(text_lengths) if text_lengths else 0,
        "table_count": "",
        "picture_count": "",
        "chart_count": "",
        "quality_note": "text_extractable" if sum(text_lengths) > 0 else "needs_ocr",
    }


def profile_ppt(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    slides = data.get("slides", [])
    text_lengths = [int(s.get("text_length", 0)) for s in slides]
    table_count = sum(int(s.get("table_count", 0)) for s in slides)
    picture_count = sum(int(s.get("picture_count", 0)) for s in slides)
    chart_count = sum(int(s.get("chart_count", 0)) for s in slides)
    note = "presentation_assumptions"
    if table_count:
        note += ";contains_tables"
    if picture_count:
        note += ";contains_pictures"
    return {
        "source_file": data.get("source_file", path.name),
        "source_kind": "pptx",
        "unit_count": len(slides),
        "nonempty_units": sum(1 for x in text_lengths if x > 0),
        "total_text_length": sum(text_lengths),
        "min_text_length": min(text_lengths) if text_lengths else 0,
        "max_text_length": max(text_lengths) if text_lengths else 0,
        "table_count": table_count,
        "picture_count": picture_count,
        "chart_count": chart_count,
        "quality_note": note,
    }


def main() -> None:
    rows = []
    for path in sorted(PDF_TEXT_DIR.glob("*.json")):
        rows.append(profile_pdf(path))
    for path in sorted(PPT_TEXT_DIR.glob("*.json")):
        rows.append(profile_ppt(path))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source_file",
        "source_kind",
        "unit_count",
        "nonempty_units",
        "total_text_length",
        "min_text_length",
        "max_text_length",
        "table_count",
        "picture_count",
        "chart_count",
        "quality_note",
    ]
    with OUT_PATH.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"profiled {len(rows)} extracted sources -> {OUT_PATH}")


if __name__ == "__main__":
    main()
