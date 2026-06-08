from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "70_outputs" / "processed_tables" / "osen_real_calibration_inputs_20260607.csv"
JSON_PATH = ROOT / "40_quality_evidence" / "osen_real_calibration_inputs_20260607.json"
MD_PATH = ROOT / "40_quality_evidence" / "osen_real_calibration_inputs_20260607.md"
SUPPLEMENT_PATH = ROOT / "90_p6_expert_dashboard" / "cache" / "real_calibration_supplements.json"

FIELDS = [
    "calibration_id",
    "dimension",
    "indicator_name",
    "segment",
    "period",
    "value",
    "unit",
    "source_file",
    "source_page_or_slide",
    "source_strength",
    "simulation_use",
    "cannot_claim",
    "next_data_needed",
    "raw_text_snippet",
    "output_status",
]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return [dict(row) for row in csv.DictReader(file)]


def read_supplements() -> list[dict[str, Any]]:
    if not SUPPLEMENT_PATH.exists():
        return []
    try:
        data = json.loads(SUPPLEMENT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def normalize_supplement(row: dict[str, Any], index: int) -> dict[str, str]:
    supplement_id = str(row.get("supplement_id") or f"RC-SUP-LOCAL-{index:03d}")
    return {
        "calibration_id": supplement_id,
        "dimension": str(row.get("dimension") or "user_supplement"),
        "indicator_name": str(row.get("indicator_name") or "用户补充校准输入"),
        "segment": str(row.get("segment") or "待确认范围"),
        "period": str(row.get("period") or "待确认时期"),
        "value": str(row.get("value") or ""),
        "unit": str(row.get("unit") or ""),
        "source_file": str(row.get("source_file") or "用户补充资料"),
        "source_page_or_slide": str(row.get("source_page_or_slide") or "user_supplement"),
        "source_strength": str(row.get("source_strength") or "local_user_supplement"),
        "simulation_use": str(row.get("simulation_use") or "作为用户补充校准输入进入预检和报告，待人工复核后用于仿真参数。"),
        "cannot_claim": str(row.get("cannot_claim") or "不能直接写成最终收益、最终排名、真实转化或投资定案。"),
        "next_data_needed": str(row.get("next_data_needed") or "补来源文件、采集口径、时段、样本量、复核人和可追溯证据。"),
        "raw_text_snippet": str(row.get("raw_text_snippet") or row.get("note") or "用户补充校准输入，等待来源复核。"),
        "output_status": "needs_review",
    }


def dedupe(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for row in rows:
        key = str(row.get("calibration_id") or "")
        if not key or key in seen:
            continue
        seen.add(key)
        result.append({field: str(row.get(field) or "") for field in FIELDS})
    return result


def write_csv(rows: list[dict[str, str]]) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    base_rows = [
        row
        for row in read_csv_rows(CSV_PATH)
        if not str(row.get("calibration_id") or "").startswith("RC-SUP-")
    ]
    supplements = [normalize_supplement(row, index) for index, row in enumerate(read_supplements(), start=1)]
    rows = dedupe(base_rows + supplements)
    write_csv(rows)

    strengths = Counter(row.get("source_strength", "") for row in rows)
    payload = {
        "status": "pass",
        "output_status": "needs_review",
        "not_final": True,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "count": len(rows),
        "supplement_count": len(supplements),
        "source_strength_counts": dict(strengths),
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "rule": "只合并已有校准输入和用户补充；不生成最终收益、最终排名、真实转化或投资定案。",
    }
    JSON_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    MD_PATH.write_text(
        "\n".join(
            [
                "# 奥森真实校准输入重建报告",
                "",
                f"- 状态：{payload['status']}",
                f"- 输入总数：{payload['count']}",
                f"- 用户补充数：{payload['supplement_count']}",
                f"- 来源强度：{json.dumps(payload['source_strength_counts'], ensure_ascii=False)}",
                "- 边界：全部仍为待复核输入，不是最终商业结论。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
