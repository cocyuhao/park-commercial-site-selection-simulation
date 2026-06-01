from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SUPPLY_BASE = ROOT / "70_outputs" / "processed_tables" / "poi_supply_base.csv"
QUERY_PLAN = ROOT / "50_external_gis" / "amap_poi" / "amap_poi_query_plan.csv"
REVIEW_CSV = ROOT / "40_quality_evidence" / "poi_supply_review.csv"
REVIEW_MD = ROOT / "40_quality_evidence" / "poi_supply_review.md"

EXPECTED_QUERY_ROWS = 24
EXPECTED_PARKS = {"sample_city_green_heart", "sample_olympic_forest"}
EXPECTED_AMAP_CATEGORIES = {
    "coffee",
    "tea_drink",
    "cold_drink",
    "fast_food",
    "restaurant",
    "cultural_creative",
    "convenience_retail",
    "sports_supply",
    "yoga_pilates",
    "night_dining_bar",
}

REVIEW_FIELDS = ["check_id", "severity", "scope", "status", "finding"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def add(
    rows: list[dict[str, str]],
    *,
    severity: str,
    scope: str,
    status: str,
    finding: str,
) -> None:
    rows.append(
        {
            "check_id": f"POIQA-{len(rows) + 1:03d}",
            "severity": severity,
            "scope": scope,
            "status": status,
            "finding": finding,
        }
    )


def status(ok: bool) -> str:
    return "pass" if ok else "needs_fix"


def review_supply(rows: list[dict[str, str]], checks: list[dict[str, str]]) -> None:
    add(
        checks,
        severity="info",
        scope="supply_base",
        status="pass",
        finding=f"供给底表当前 {len(rows)} 条；这是 PDF 热门到访种子，不是完整园内供给结论。",
    )

    blank_names = [row for row in rows if not row.get("poi_name", "").strip()]
    add(
        checks,
        severity="error",
        scope="supply_base",
        status=status(not blank_names),
        finding=f"POI 名称空值 {len(blank_names)} 条。",
    )

    wrong_status = [
        row
        for row in rows
        if row.get("validation_status") != "needs_amap_or_field_verification"
    ]
    add(
        checks,
        severity="error",
        scope="supply_base",
        status=status(not wrong_status),
        finding=f"非待高德/现场核验状态 {len(wrong_status)} 条。",
    )

    coords_filled = [
        row
        for row in rows
        if row.get("longitude") or row.get("latitude") or row.get("amap_poi_id")
    ]
    add(
        checks,
        severity="warning",
        scope="supply_base",
        status=status(not coords_filled),
        finding=f"高德字段已被填充 {len(coords_filled)} 条；P1 当前应先保留为空，待 API 核验后再写入。",
    )

    merged_english_names = [
        row["poi_name"]
        for row in rows
        if "coffee" in row.get("poi_name", "").lower()
        and "coffee(" in row.get("poi_name", "").lower()
        and "grid coffee" not in row.get("poi_name", "").lower()
    ]
    add(
        checks,
        severity="warning",
        scope="supply_base",
        status=status(not merged_english_names),
        finding=(
            "疑似英文品牌空格被吞并 "
            f"{len(merged_english_names)} 条：{';'.join(merged_english_names[:5])}"
        ),
    )

    category_counts = Counter(row.get("standard_category", "") for row in rows)
    add(
        checks,
        severity="info",
        scope="supply_base",
        status="pass",
        finding=f"标准业态分布：{dict(sorted(category_counts.items()))}",
    )


def review_query_plan(rows: list[dict[str, str]], checks: list[dict[str, str]]) -> None:
    add(
        checks,
        severity="error",
        scope="amap_query_plan",
        status=status(len(rows) == EXPECTED_QUERY_ROWS),
        finding=f"高德查询计划 {len(rows)} 条，预期 {EXPECTED_QUERY_ROWS} 条。",
    )

    query_ids = [row.get("query_id", "") for row in rows]
    duplicate_ids = [query_id for query_id, count in Counter(query_ids).items() if count > 1]
    add(
        checks,
        severity="error",
        scope="amap_query_plan",
        status=status(not duplicate_ids),
        finding=f"重复 query_id {len(duplicate_ids)} 个：{';'.join(duplicate_ids[:5])}",
    )

    parks = {row.get("park_id", "") for row in rows}
    add(
        checks,
        severity="error",
        scope="amap_query_plan",
        status=status(parks == EXPECTED_PARKS),
        finding=f"覆盖公园：{sorted(parks)}。",
    )

    categories = {row.get("commercial_category", "") for row in rows}
    missing_categories = sorted(EXPECTED_AMAP_CATEGORIES - categories)
    add(
        checks,
        severity="warning",
        scope="amap_query_plan",
        status=status(not missing_categories),
        finding=f"缺少高德查询业态：{missing_categories}。",
    )

    invalid_radius = [
        row
        for row in rows
        if not row.get("radius_m", "").isdigit() or int(row["radius_m"]) <= 0
    ]
    add(
        checks,
        severity="error",
        scope="amap_query_plan",
        status=status(not invalid_radius),
        finding=f"无效半径 {len(invalid_radius)} 条。",
    )

    blank_critical = [
        row.get("query_id", "")
        for row in rows
        if not row.get("city")
        or not row.get("center_address")
        or not row.get("amap_keywords")
        or not row.get("commercial_category")
    ]
    add(
        checks,
        severity="error",
        scope="amap_query_plan",
        status=status(not blank_critical),
        finding=f"关键查询字段空值 {len(blank_critical)} 条：{';'.join(blank_critical[:5])}",
    )

    priority_counts = Counter(row.get("priority", "") for row in rows)
    add(
        checks,
        severity="info",
        scope="amap_query_plan",
        status="pass",
        finding=f"查询优先级分布：{dict(sorted(priority_counts.items()))}",
    )


def write_csv(rows: list[dict[str, str]]) -> None:
    with REVIEW_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_md(rows: list[dict[str, str]]) -> None:
    by_status = Counter(row["status"] for row in rows)
    blocking = [
        row
        for row in rows
        if row["status"] == "needs_fix" and row["severity"] == "error"
    ]
    warnings = [
        row
        for row in rows
        if row["status"] == "needs_fix" and row["severity"] == "warning"
    ]

    lines = [
        "# P1 供给底表轻量复查",
        "",
        "## 结论",
        "",
        f"- 检查项：{len(rows)} 条。",
        f"- 状态统计：{dict(sorted(by_status.items()))}",
        f"- 阻塞问题：{len(blocking)} 条。",
        f"- 警告问题：{len(warnings)} 条。",
        "",
        "## 复查口径",
        "",
        "- 当前只复查 P1 供给底表和高德查询计划，不复查完整 PDF 原文。",
        "- `poi_supply_base.csv` 仍是 PDF 热门到访种子，不是最终园内/周边供给结论。",
        "- 高德 API 未运行前，坐标、距离、园内状态和营业状态应保持待核验。",
        "",
        "## 需要处理的问题",
        "",
    ]
    if not blocking and not warnings:
        lines.append("- 暂无阻塞或警告问题，可以进入高德 POI 小批量抓取。")
    else:
        for row in blocking + warnings:
            lines.append(f"- [{row['severity']}] {row['scope']}：{row['finding']}")

    lines.extend(
        [
            "",
            "## 输出文件",
            "",
            "- `40_quality_evidence/poi_supply_review.csv`",
        ]
    )
    REVIEW_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    supply_rows = read_csv(SUPPLY_BASE)
    query_rows = read_csv(QUERY_PLAN)
    checks: list[dict[str, str]] = []
    review_supply(supply_rows, checks)
    review_query_plan(query_rows, checks)
    write_csv(checks)
    write_md(checks)
    print(f"reviewed {len(supply_rows)} supply rows and {len(query_rows)} query rows")
    print(f"wrote {REVIEW_CSV}")
    print(f"wrote {REVIEW_MD}")


if __name__ == "__main__":
    main()
