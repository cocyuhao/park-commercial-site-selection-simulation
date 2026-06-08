from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SIM_DIR = ROOT / "60_model" / "simulation"
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

from report_docx import write_site_selection_docx  # noqa: E402


def main() -> None:
    report_path = ROOT / "80_delivery" / "site_selection_gap_report_latest.json"
    report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    result = write_site_selection_docx(report, ROOT / "80_delivery")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
