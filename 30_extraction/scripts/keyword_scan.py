from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PDF_TEXT_DIR = ROOT / "30_extraction" / "pdf_text"
PPT_TEXT_DIR = ROOT / "30_extraction" / "ppt_text"
OUT_PATH = ROOT / "30_extraction" / "tables" / "keyword_hits.csv"

KEYWORDS = [
    "客流",
    "到访",
    "TGI",
    "POI",
    "热门到访",
    "品牌",
    "咖啡",
    "餐饮",
    "小吃",
    "快餐",
    "供需",
    "缺口",
    "外溢",
    "收入",
    "收益",
    "回收期",
    "转化",
    "消费",
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def snippets(text: str, keyword: str, radius: int = 80) -> list[str]:
    clean = normalize(text)
    results = []
    start = 0
    while True:
        pos = clean.find(keyword, start)
        if pos == -1:
            break
        results.append(clean[max(0, pos - radius): pos + len(keyword) + radius])
        start = pos + len(keyword)
        if len(results) >= 3:
            break
    return results


def scan_pdf(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for page in data.get("pages", []):
        text = page.get("text", "")
        for keyword in KEYWORDS:
            for snippet in snippets(text, keyword):
                rows.append({
                    "source_file": data.get("source_file", path.name),
                    "unit_type": "page",
                    "unit_index": page.get("page"),
                    "keyword": keyword,
                    "snippet": snippet,
                })
    return rows


def scan_ppt(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for slide in data.get("slides", []):
        text = slide.get("text", "")
        for keyword in KEYWORDS:
            for snippet in snippets(text, keyword):
                rows.append({
                    "source_file": data.get("source_file", path.name),
                    "unit_type": "slide",
                    "unit_index": slide.get("slide"),
                    "keyword": keyword,
                    "snippet": snippet,
                })
    return rows


def main() -> None:
    rows = []
    for path in sorted(PDF_TEXT_DIR.glob("*.json")):
        rows.extend(scan_pdf(path))
    for path in sorted(PPT_TEXT_DIR.glob("*.json")):
        rows.extend(scan_ppt(path))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["hit_id", "source_file", "unit_type", "unit_index", "keyword", "snippet"]
    with OUT_PATH.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for idx, row in enumerate(rows, start=1):
            row = {"hit_id": f"HIT-{idx:05d}", **row}
            writer.writerow(row)
    print(f"found {len(rows)} keyword hits -> {OUT_PATH}")


if __name__ == "__main__":
    main()
