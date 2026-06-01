from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOUNDARY_FILTER = ROOT / "70_outputs" / "processed_tables" / "poi_supply_candidates_amap_boundary_filter.csv"
OUT_CSV = ROOT / "70_outputs" / "processed_tables" / "poi_supply_in_park_candidate_review.csv"
REPORT = ROOT / "40_quality_evidence" / "in_park_candidate_review_report.md"


FIELDS = [
    "review_id",
    "candidate_id",
    "park_id",
    "park_name",
    "amap_poi_id",
    "poi_name",
    "standard_categories",
    "amap_type",
    "address",
    "longitude",
    "latitude",
    "wgs84_longitude",
    "wgs84_latitude",
    "min_distance_m",
    "distance_band",
    "boundary_filter_status",
    "p1_boundary_supply_status",
    "boundary_filter_confidence",
    "rating",
    "cost_yuan",
    "opentime_today",
    "opentime_week",
    "tel",
    "pdf_seed_match_status",
    "pdf_seed_poi_names",
    "source_strength_status",
    "opening_hours_status",
    "contact_status",
    "spend_status",
    "business_info_status",
    "route_access_status",
    "operation_authorization_status",
    "field_review_priority",
    "candidate_use_status",
    "recommended_next_action",
    "review_notes",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(rows: list[dict[str, str]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def status_present(value: str, present_status: str, missing_status: str) -> str:
    return present_status if str(value or "").strip() else missing_status


def source_strength(row: dict[str, str]) -> str:
    if row.get("pdf_seed_match_status") == "matched_pdf_seed":
        return "pdf_seed_plus_amap_boundary"
    return "amap_boundary_only"


def business_info_status(row: dict[str, str]) -> str:
    has_open = bool(row.get("opentime_today") or row.get("opentime_week"))
    has_tel = bool(row.get("tel"))
    has_rating = bool(row.get("rating"))
    if has_open and has_tel and has_rating:
        return "amap_business_fields_sufficient_for_p1_review"
    if has_open or has_tel or has_rating:
        return "amap_business_fields_partial"
    return "amap_business_fields_missing"


def priority(row: dict[str, str]) -> str:
    if row.get("pdf_seed_match_status") == "matched_pdf_seed":
        return "P0_pdf_seed_boundary_match"
    info_status = business_info_status(row)
    if info_status != "amap_business_fields_sufficient_for_p1_review":
        return "P0_missing_business_fields"
    if any(category in row.get("standard_categories", "") for category in ["coffee", "convenience_retail", "sports_supply"]):
        return "P1_key_category"
    return "P2_normal_field_review"


def recommended_action(row: dict[str, str]) -> str:
    actions = [
        "核验是否实际营业",
        "核验是否属于园内运营或可授权经营点",
        "补入口/节点步行可达性",
    ]
    if not (row.get("opentime_today") or row.get("opentime_week")):
        actions.append("补营业时间")
    if not row.get("tel"):
        actions.append("补联系电话或公开联系方式")
    if not row.get("cost_yuan"):
        actions.append("补消费价格或客单价口径")
    if row.get("pdf_seed_match_status") == "matched_pdf_seed":
        actions.append("回连 PDF 热门到访种子，确认名称是否同一商户")
    return "；".join(actions)


def build_rows(boundary_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    inside = [row for row in boundary_rows if row.get("boundary_filter_status") == "inside_osm_polygon"]
    output_rows: list[dict[str, str]] = []
    for row in inside:
        output_rows.append(
            {
                "review_id": f"INPARK-REVIEW-{len(output_rows) + 1:03d}",
                "candidate_id": row.get("candidate_id", ""),
                "park_id": row.get("park_id", ""),
                "park_name": row.get("park_name", ""),
                "amap_poi_id": row.get("amap_poi_id", ""),
                "poi_name": row.get("poi_name", ""),
                "standard_categories": row.get("standard_categories", ""),
                "amap_type": row.get("amap_type", ""),
                "address": row.get("address", ""),
                "longitude": row.get("longitude", ""),
                "latitude": row.get("latitude", ""),
                "wgs84_longitude": row.get("wgs84_longitude", ""),
                "wgs84_latitude": row.get("wgs84_latitude", ""),
                "min_distance_m": row.get("min_distance_m", ""),
                "distance_band": row.get("distance_band", ""),
                "boundary_filter_status": row.get("boundary_filter_status", ""),
                "p1_boundary_supply_status": row.get("p1_boundary_supply_status", ""),
                "boundary_filter_confidence": row.get("boundary_filter_confidence", ""),
                "rating": row.get("rating", ""),
                "cost_yuan": row.get("cost_yuan", ""),
                "opentime_today": row.get("opentime_today", ""),
                "opentime_week": row.get("opentime_week", ""),
                "tel": row.get("tel", ""),
                "pdf_seed_match_status": row.get("pdf_seed_match_status", ""),
                "pdf_seed_poi_names": row.get("pdf_seed_poi_names", ""),
                "source_strength_status": source_strength(row),
                "opening_hours_status": status_present(
                    row.get("opentime_today") or row.get("opentime_week"),
                    "has_opening_hours",
                    "missing_opening_hours",
                ),
                "contact_status": status_present(row.get("tel", ""), "has_contact", "missing_contact"),
                "spend_status": status_present(row.get("cost_yuan", ""), "has_cost_yuan", "missing_cost_yuan"),
                "business_info_status": business_info_status(row),
                "route_access_status": "needs_entrance_or_route_api_verification",
                "operation_authorization_status": "needs_operator_or_field_confirmation",
                "field_review_priority": priority(row),
                "candidate_use_status": "p1_in_park_candidate_not_final_supply",
                "recommended_next_action": recommended_action(row),
                "review_notes": "OSM polygon 内候选；仍需现场营业、入口路径和运营授权核验，不能直接进入最终供给结论。",
            }
        )
    return output_rows


def write_report(rows: list[dict[str, str]]) -> None:
    by_park = Counter(row["park_name"] for row in rows)
    by_priority = Counter(row["field_review_priority"] for row in rows)
    by_source = Counter(row["source_strength_status"] for row in rows)
    by_business = Counter(row["business_info_status"] for row in rows)
    by_category: Counter[str] = Counter()
    by_park_category: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        for category in row["standard_categories"].split(";"):
            if category:
                by_category[category] += 1
                by_park_category[row["park_name"]][category] += 1

    opening = sum(1 for row in rows if row["opening_hours_status"] == "has_opening_hours")
    contact = sum(1 for row in rows if row["contact_status"] == "has_contact")
    cost = sum(1 for row in rows if row["spend_status"] == "has_cost_yuan")
    rating = sum(1 for row in rows if row.get("rating"))

    lines = [
        "# 园内候选 POI 复核清单报告",
        "",
        "## 结论",
        "",
        f"- OSM polygon 内候选：{len(rows)} 条。",
        f"- 按公园统计：{dict(sorted(by_park.items()))}",
        f"- 复核优先级：{dict(sorted(by_priority.items()))}",
        f"- 来源强度：{dict(sorted(by_source.items()))}",
        f"- 高德经营字段状态：{dict(sorted(by_business.items()))}",
        f"- 字段覆盖：rating {rating}/{len(rows)}，opentime {opening}/{len(rows)}，tel {contact}/{len(rows)}，cost_yuan {cost}/{len(rows)}。",
        "",
        "## 按业态统计",
        "",
        f"- 总体：{dict(sorted(by_category.items()))}",
    ]
    for park_name, counter in sorted(by_park_category.items()):
        lines.append(f"- {park_name}：{dict(sorted(counter.items()))}")

    lines.extend(
        [
            "",
            "## 口径限制",
            "",
            "- 本清单只包含 OSM polygon 内候选，不是最终可经营点位清单。",
            "- `candidate_use_status` 全部保持为 `p1_in_park_candidate_not_final_supply`。",
            "- 仍需核验：实际营业状态、入口/节点步行可达、是否属于园方可运营/可授权资产、现场限制条件。",
            "- 高德营业时间、电话、评分和人均消费是公开 POI 字段，可作为 P1 复核线索，不能替代现场或经营方确认。",
            "",
            "## 输出文件",
            "",
            "- `70_outputs/processed_tables/poi_supply_in_park_candidate_review.csv`",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    boundary_rows = read_csv(BOUNDARY_FILTER)
    rows = build_rows(boundary_rows)
    write_csv(rows)
    write_report(rows)
    print(f"wrote {len(rows)} in-park candidate review rows to {OUT_CSV}")
    print(f"wrote report to {REPORT}")


if __name__ == "__main__":
    main()
