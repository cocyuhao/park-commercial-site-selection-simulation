from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FETCH_LOG = ROOT / "50_external_gis" / "amap_poi" / "amap_fetch_log.csv"
AMAP_CLEAN = ROOT / "50_external_gis" / "amap_poi" / "amap_poi_clean.csv"
REVIEW_CSV = ROOT / "40_quality_evidence" / "amap_poi_fetch_review.csv"
REVIEW_MD = ROOT / "40_quality_evidence" / "amap_poi_fetch_review.md"


REVIEW_FIELDS = ["check_id", "severity", "scope", "status", "finding"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def add(
    checks: list[dict[str, str]],
    *,
    severity: str,
    scope: str,
    status: str,
    finding: str,
) -> None:
    checks.append(
        {
            "check_id": f"AMAPQA-{len(checks) + 1:03d}",
            "severity": severity,
            "scope": scope,
            "status": status,
            "finding": finding,
        }
    )


def status(ok: bool) -> str:
    return "pass" if ok else "needs_review"


def count_non_empty(rows: list[dict[str, str]], field: str) -> int:
    return sum(1 for row in rows if str(row.get(field, "")).strip())


def review_logs(logs: list[dict[str, str]], checks: list[dict[str, str]]) -> None:
    status_counts = Counter(row.get("status", "") for row in logs)
    info_counts = Counter(row.get("info", "") for row in logs)
    errors = [row for row in logs if row.get("status") not in {"1"}]
    zero_results = [
        row
        for row in logs
        if row.get("api_endpoint") == "v5/place/around"
        and row.get("status") == "1"
        and row.get("result_count") == "0"
    ]
    saturated = [
        row
        for row in logs
        if row.get("api_endpoint") == "v5/place/around"
        and row.get("status") == "1"
        and row.get("result_count") == "25"
    ]

    add(
        checks,
        severity="info",
        scope="fetch_log",
        status="pass",
        finding=f"接口日志 {len(logs)} 条；状态分布 {dict(sorted(status_counts.items()))}；info 分布 {dict(sorted(info_counts.items()))}。",
    )
    add(
        checks,
        severity="error",
        scope="fetch_log",
        status=status(not errors),
        finding=f"非成功接口日志 {len(errors)} 条。",
    )
    add(
        checks,
        severity="warning",
        scope="fetch_log",
        status=status(not zero_results),
        finding=f"零结果周边查询 {len(zero_results)} 条：{';'.join(row['query_id'] for row in zero_results)}。",
    )
    add(
        checks,
        severity="warning",
        scope="fetch_log",
        status=status(not saturated),
        finding=f"达到单页上限 25 条的查询 {len(saturated)} 条，后续可能需要分页：{';'.join(row['query_id'] for row in saturated)}。",
    )


def review_clean(rows: list[dict[str, str]], checks: list[dict[str, str]]) -> None:
    by_park = Counter(row.get("park_name", "") for row in rows)
    by_category = Counter(row.get("commercial_category", "") for row in rows)
    duplicate_pairs = [
        key
        for key, count in Counter(
            (row.get("park_id", ""), row.get("commercial_category", ""), row.get("amap_poi_id", ""))
            for row in rows
            if row.get("amap_poi_id")
        ).items()
        if count > 1
    ]
    unique_pois = {
        (row.get("park_id", ""), row.get("amap_poi_id", ""))
        for row in rows
        if row.get("amap_poi_id")
    }

    add(
        checks,
        severity="info",
        scope="amap_clean",
        status="pass",
        finding=f"清洗 POI 行 {len(rows)} 条；按公园 {dict(sorted(by_park.items()))}。",
    )
    add(
        checks,
        severity="info",
        scope="amap_clean",
        status="pass",
        finding=f"按业态 {dict(sorted(by_category.items()))}。",
    )
    add(
        checks,
        severity="info",
        scope="amap_clean",
        status="pass",
        finding=f"按公园去重后的 Amap POI ID 数：{len(unique_pois)}。",
    )
    add(
        checks,
        severity="warning",
        scope="amap_clean",
        status=status(not duplicate_pairs),
        finding=f"同一公园同一业态内重复 POI ID {len(duplicate_pairs)} 个。",
    )
    for field in ["longitude", "latitude", "distance_m"]:
        missing = len(rows) - count_non_empty(rows, field)
        add(
            checks,
            severity="error",
            scope="amap_clean",
            status=status(missing == 0),
            finding=f"{field} 缺失 {missing} 条。",
        )
    for field in ["rating", "cost_yuan", "opentime_today", "opentime_week", "tel"]:
        present = count_non_empty(rows, field)
        add(
            checks,
            severity="info",
            scope="amap_clean",
            status="pass",
            finding=f"{field} 有值 {present} 条。",
        )


def write_csv(rows: list[dict[str, str]]) -> None:
    with REVIEW_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_md(rows: list[dict[str, str]]) -> None:
    by_status = Counter(row["status"] for row in rows)
    warnings = [row for row in rows if row["status"] == "needs_review"]
    errors = [row for row in warnings if row["severity"] == "error"]

    lines = [
        "# 高德 POI 抓取复查报告",
        "",
        "## 结论",
        "",
        f"- 检查项：{len(rows)} 条。",
        f"- 状态统计：{dict(sorted(by_status.items()))}",
        f"- 阻塞问题：{len(errors)} 条。",
        f"- 需关注项：{len(warnings)} 条。",
        "",
        "## 关键发现",
        "",
    ]
    for row in rows:
        if row["severity"] == "info" or row["status"] == "needs_review":
            lines.append(f"- [{row['severity']}] {row['finding']}")

    lines.extend(
        [
            "",
            "## 口径",
            "",
            "- 本轮是 P1 小批量 POI 抓取，不等于最终完整供给清单。",
            "- `distance_m` 为高德周边搜索返回距离，仍需结合公园边界和入口/节点做园内/周边过滤。",
            "- 查询达到单页上限的业态后续需要分页或缩小半径复查。",
            "",
            "## 输出文件",
            "",
            "- `50_external_gis/amap_poi/amap_fetch_log.csv`",
            "- `50_external_gis/amap_poi/amap_poi_clean.csv`",
            "- `70_outputs/processed_tables/poi_supply_base_amap.csv`",
            "- `40_quality_evidence/amap_poi_fetch_review.csv`",
        ]
    )
    REVIEW_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    logs = read_csv(FETCH_LOG)
    clean_rows = read_csv(AMAP_CLEAN)
    checks: list[dict[str, str]] = []
    review_logs(logs, checks)
    review_clean(clean_rows, checks)
    write_csv(checks)
    write_md(checks)
    print(f"reviewed {len(logs)} log rows and {len(clean_rows)} clean POI rows")
    print(f"wrote {REVIEW_CSV}")
    print(f"wrote {REVIEW_MD}")


if __name__ == "__main__":
    main()
