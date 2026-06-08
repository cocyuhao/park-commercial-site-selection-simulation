from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "70_outputs" / "processed_tables" / "person_simulation_feature_derivatives_1000_20260604.csv"
OUT_JSON = ROOT / "40_quality_evidence" / "person_simulation_feature_derivatives_validation_20260607.json"
OUT_MD = ROOT / "40_quality_evidence" / "person_simulation_feature_derivatives_validation_20260607.md"

REQUIRED_COLUMNS = [
    "derivative_id",
    "persona_id",
    "persona_name",
    "persona_core_need",
    "income_segment_id",
    "income_segment_name",
    "income_price_band",
    "income_sensitivity_note",
    "income_evidence_hint",
    "time_band_id",
    "time_band_name",
    "time_range",
    "weather_id",
    "weather_name",
    "weather_effect",
    "node_context_id",
    "node_context_name",
    "node_role",
    "demand_trigger_id",
    "demand_trigger_name",
    "candidate_supply_action_id",
    "candidate_supply_action_name",
    "priority_label",
    "user_control_needed",
    "data_needed",
    "deepseek_role",
    "why_it_matters",
]

MIN_COVERAGE = {
    "persona_id": 8,
    "income_segment_id": 5,
    "time_band_id": 6,
    "weather_id": 5,
    "node_context_id": 6,
    "demand_trigger_id": 10,
    "candidate_supply_action_id": 14,
}

REQUIRED_TERMS = [
    "收入",
    "预算",
    "消费支出",
    "价格带",
    "天气",
    "节假日",
    "同行",
    "路径",
    "节点",
    "补货",
    "关闭",
    "客单价",
    "转化率",
    "DeepSeek",
    "采用",
    "放弃",
    "锁定",
    "待复核",
    "建议",
]

MOJIBAKE_MARKERS = ["??", "�", "锘", "乱码"]


def read_rows() -> list[dict[str, str]]:
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def passfail(condition: bool) -> str:
    return "pass" if condition else "fail"


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"name": name, "passed": passed, "detail": detail})


def validate() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    rows = read_rows()
    headers = list(rows[0].keys()) if rows else []
    text_blob = "\n".join(" ".join(str(value) for value in row.values()) for row in rows)

    add_check(checks, "row_count_at_least_1000", len(rows) >= 1000, f"rows={len(rows)}")
    add_check(checks, "required_columns_present", set(REQUIRED_COLUMNS) <= set(headers), f"columns={headers}")

    coverage = {key: len({row.get(key, "") for row in rows if row.get(key, "")}) for key in MIN_COVERAGE}
    for key, minimum in MIN_COVERAGE.items():
        add_check(checks, f"coverage_{key}", coverage.get(key, 0) >= minimum, f"{key}={coverage.get(key, 0)} minimum={minimum}")

    empty_counts = Counter()
    bad_rows: list[str] = []
    for row in rows:
        row_text = " ".join(str(value) for value in row.values())
        if any(marker in row_text for marker in MOJIBAKE_MARKERS):
            bad_rows.append(row.get("derivative_id", "unknown"))
        for column in REQUIRED_COLUMNS:
            if not str(row.get(column, "")).strip():
                empty_counts[column] += 1

    add_check(checks, "no_mojibake_markers", not bad_rows, f"bad_rows={bad_rows[:10]} total={len(bad_rows)}")
    add_check(checks, "required_cells_non_empty", not empty_counts, f"empty_counts={dict(empty_counts)}")

    missing_terms = [term for term in REQUIRED_TERMS if term not in text_blob]
    add_check(checks, "business_terms_covered", not missing_terms, f"missing_terms={missing_terms}")

    deepseek_bad = [
        row.get("derivative_id", "unknown")
        for row in rows
        if "不得" not in row.get("deepseek_role", "") or "待复核" not in row.get("deepseek_role", "")
    ]
    add_check(checks, "deepseek_boundary_every_row", not deepseek_bad, f"bad_rows={deepseek_bad[:10]} total={len(deepseek_bad)}")

    control_bad = [
        row.get("derivative_id", "unknown")
        for row in rows
        if not all(term in row.get("user_control_needed", "") for term in ["采用", "放弃", "删除", "锁定"])
    ]
    add_check(checks, "user_control_every_row", not control_bad, f"bad_rows={control_bad[:10]} total={len(control_bad)}")

    recommendation_bad = [
        row.get("derivative_id", "unknown")
        for row in rows
        if "建议" not in row.get("why_it_matters", "") or "裸分" not in row.get("why_it_matters", "")
    ]
    add_check(checks, "specific_recommendation_not_raw_score", not recommendation_bad, f"bad_rows={recommendation_bad[:10]} total={len(recommendation_bad)}")

    failures = [check for check in checks if not check["passed"]]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": passfail(not failures),
        "failure_count": len(failures),
        "csv_path": str(CSV_PATH.relative_to(ROOT)).replace("\\", "/"),
        "summary": {
            "row_count": len(rows),
            "column_count": len(headers),
            "file_bytes": CSV_PATH.stat().st_size if CSV_PATH.exists() else 0,
        },
        "coverage": coverage,
        "checks": checks,
        "boundary": "This validates a scenario/feature coverage pool, not final simulation accuracy.",
    }
    return payload


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# 人物仿真衍生特征验证（2026-06-07）",
        "",
        f"- 状态：{payload['status']}",
        f"- 失败数：{payload['failure_count']}",
        f"- CSV：`{payload['csv_path']}`",
        f"- 行数：{payload['summary']['row_count']}",
        f"- 字节：{payload['summary']['file_bytes']}",
        "",
        "## 维度覆盖",
        "",
        "| 维度 | 唯一值数量 |",
        "|---|---:|",
    ]
    for key, value in payload["coverage"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(["", "## 检查项", "", "| 检查 | 结果 | 说明 |", "|---|---|---|"])
    for check in payload["checks"]:
        result = "pass" if check["passed"] else "fail"
        detail = str(check["detail"]).replace("\n", " ")
        lines.append(f"| {check['name']} | {result} | {detail} |")
    lines.extend(["", "## 边界", "", str(payload["boundary"])])
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    payload = validate()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(payload)
    print(f"status={payload['status']} failures={payload['failure_count']} rows={payload['summary']['row_count']}")
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    if payload["failure_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
