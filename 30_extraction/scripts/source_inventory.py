from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "20_raw_data"
CATALOG_PATH = ROOT / "40_quality_evidence" / "data_catalog.csv"
LOG_PATH = ROOT / "30_extraction" / "extraction_logs" / "source_inventory.json"


def classify_role(path: Path) -> str:
    suffix = path.suffix.lower()
    name = path.name
    if suffix == ".pdf":
        return "source_report_pdf"
    if suffix in {".ppt", ".pptx"}:
        return "presentation_or_assumption_material"
    if suffix in {".csv", ".xlsx", ".xls"}:
        return "structured_table"
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return "image_or_screenshot"
    return "unknown"


def iter_raw_files() -> list[Path]:
    if not RAW_DIR.exists():
        return []
    supported_suffixes = {".pdf", ".ppt", ".pptx", ".csv", ".xlsx", ".xls", ".png", ".jpg", ".jpeg", ".webp"}
    return sorted(
        [
            p
            for p in RAW_DIR.rglob("*")
            if p.is_file()
            and not p.name.startswith("~$")
            and p.suffix.lower() in supported_suffixes
        ]
    )


def main() -> None:
    rows = []
    now = datetime.now().isoformat(timespec="seconds")

    for idx, path in enumerate(iter_raw_files(), start=1):
        rel = path.relative_to(ROOT).as_posix()
        rows.append(
            {
                "source_id": f"SRC-{idx:04d}",
                "file_path": rel,
                "file_name": path.name,
                "file_type": path.suffix.lower().lstrip("."),
                "size_bytes": path.stat().st_size,
                "last_modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
                "cataloged_at": now,
                "role": classify_role(path),
                "evidence_strength_default": "medium_high" if path.suffix.lower() == ".pdf" else "medium_low",
                "notes": "",
            }
        )

    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CATALOG_PATH.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [
            "source_id",
            "file_path",
            "file_name",
            "file_type",
            "size_bytes",
            "last_modified",
            "cataloged_at",
            "role",
            "evidence_strength_default",
            "notes",
        ])
        writer.writeheader()
        writer.writerows(rows)

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text(
        json.dumps({"cataloged_at": now, "file_count": len(rows), "files": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"cataloged {len(rows)} files -> {CATALOG_PATH}")


if __name__ == "__main__":
    main()
