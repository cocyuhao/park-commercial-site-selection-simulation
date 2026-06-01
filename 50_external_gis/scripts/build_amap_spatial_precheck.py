from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = ROOT / "70_outputs" / "processed_tables" / "poi_supply_candidates_amap.csv"
FETCH_LOG = ROOT / "50_external_gis" / "amap_poi" / "amap_fetch_log.csv"
QUERY_PLAN = ROOT / "50_external_gis" / "amap_poi" / "amap_poi_query_plan.csv"
OUT_PRECHECK = ROOT / "70_outputs" / "processed_tables" / "poi_supply_candidates_amap_spatial_precheck.csv"
OUT_REFETCH_PLAN = ROOT / "50_external_gis" / "amap_poi" / "amap_refetch_followup_plan.csv"
REPORT = ROOT / "40_quality_evidence" / "amap_spatial_precheck_report.md"


PARK_CONTEXT_TERMS = {
    "sample_city_green_heart": [
        "城市绿心",
        "绿心公园",
        "绿心路",
        "绿心",
        "北京城市图书馆",
        "城市图书馆",
        "三大馆",
        "源心",
        "活力汇",
        "p11停车场",
    ],
    "sample_olympic_forest": [
        "奥林匹克森林公园",
        "奥林匹克公园",
        "奥森公园",
        "奥森",
        "森林公园南园",
        "森林公园北园",
        "南园",
        "北园",
    ],
}


ALT_KEYWORDS = {
    "tea_drink": "奶茶;茶饮店;饮品",
    "restaurant": "餐厅;中餐;简餐",
    "cultural_creative": "文创;纪念品;礼品",
    "souvenir": "纪念品;文创;礼品",
    "yoga_pilates": "瑜伽;普拉提;健身;运动康复",
    "night_dining_bar": "酒吧;精酿;夜宵",
}


EXTRA_PRECHECK_FIELDS = [
    "center_longitude",
    "center_latitude",
    "computed_center_distance_m",
    "distance_delta_m",
    "text_context_hits",
    "text_context_status",
    "distance_precheck_band",
    "spatial_precheck_status",
    "boundary_validation_status",
    "supply_use_status",
    "spatial_precheck_notes",
]


REFETCH_FIELDS = [
    "followup_id",
    "query_id",
    "park_id",
    "park_name",
    "commercial_category",
    "issue_type",
    "current_keyword",
    "current_radius_m",
    "current_page_size",
    "current_result_count",
    "recommended_action",
    "suggested_page_num",
    "suggested_keywords",
    "suggested_radius_m",
    "requires_amap_key",
    "priority",
    "notes",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def to_float(value: str) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    radius_m = 6_371_000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_m * c


def distance_band(distance: float | None) -> str:
    if distance is None:
        return "unknown"
    if distance <= 500:
        return "0-500m_core_candidate"
    if distance <= 1000:
        return "501-1000m_near_core_candidate"
    if distance <= 1500:
        return "1001-1500m_edge_or_adjacent_candidate"
    if distance <= 3000:
        return "1501-3000m_surrounding_candidate"
    return "3000m_plus_out_of_scope_candidate"


def parse_params(params_summary: str) -> dict[str, str]:
    try:
        value = json.loads(params_summary or "{}")
    except json.JSONDecodeError:
        return {}
    return {str(k): str(v) for k, v in value.items()}


def center_locations(fetch_log_rows: list[dict[str, str]]) -> dict[str, tuple[str, str]]:
    centers: dict[str, tuple[str, str]] = {}
    for row in fetch_log_rows:
        if row.get("api_endpoint") != "v5/place/around":
            continue
        params = parse_params(row.get("params_summary", ""))
        location = params.get("location", "")
        if "," not in location:
            continue
        lon, lat = [part.strip() for part in location.split(",", 1)]
        if lon and lat:
            centers.setdefault(row.get("park_id", ""), (lon, lat))
    return centers


def text_context_hits(row: dict[str, str]) -> list[str]:
    park_id = row.get("park_id", "")
    terms = PARK_CONTEXT_TERMS.get(park_id, [])
    text = f"{row.get('poi_name', '')} {row.get('address', '')}".lower()
    return [term for term in terms if term.lower() in text]


def classify_candidate(row: dict[str, str], center: tuple[str, str] | None) -> dict[str, str]:
    lon = to_float(row.get("longitude", ""))
    lat = to_float(row.get("latitude", ""))
    reported_distance = to_float(row.get("min_distance_m", ""))
    computed_distance: float | None = None
    if center and lon is not None and lat is not None:
        center_lon = to_float(center[0])
        center_lat = to_float(center[1])
        if center_lon is not None and center_lat is not None:
            computed_distance = haversine_m(center_lon, center_lat, lon, lat)

    basis_distance = reported_distance if reported_distance is not None else computed_distance
    hits = text_context_hits(row)
    text_status = "park_context_hit" if hits else "no_park_context_hit"
    pdf_match = row.get("pdf_seed_match_status") == "matched_pdf_seed"

    if pdf_match:
        status = "pdf_seed_matched_needs_boundary_confirmation"
    elif hits:
        status = "park_context_needs_boundary_confirmation"
    elif basis_distance is not None and basis_distance <= 1000:
        status = "near_core_needs_boundary_confirmation"
    elif basis_distance is not None and basis_distance <= 1500:
        status = "edge_or_adjacent_needs_boundary_confirmation"
    else:
        status = "surrounding_competition_candidate"

    if status == "surrounding_competition_candidate":
        notes = "距离中心点较远且无公园文本命中，暂按周边竞品/外溢供给候选处理。"
    else:
        notes = "仅为文本和中心距离预过滤，仍需真实公园边界、入口节点或现场清单确认。"

    delta = ""
    if reported_distance is not None and computed_distance is not None:
        delta = f"{abs(reported_distance - computed_distance):.1f}"

    return {
        "center_longitude": center[0] if center else "",
        "center_latitude": center[1] if center else "",
        "computed_center_distance_m": f"{computed_distance:.1f}" if computed_distance is not None else "",
        "distance_delta_m": delta,
        "text_context_hits": ";".join(hits),
        "text_context_status": text_status,
        "distance_precheck_band": distance_band(basis_distance),
        "spatial_precheck_status": status,
        "boundary_validation_status": "needs_polygon_or_field_verification",
        "supply_use_status": "do_not_use_as_in_park_supply_yet",
        "spatial_precheck_notes": notes,
    }


def build_precheck_rows(
    candidate_rows: list[dict[str, str]], fetch_log_rows: list[dict[str, str]]
) -> list[dict[str, str]]:
    centers = center_locations(fetch_log_rows)
    rows = []
    for row in candidate_rows:
        extra = classify_candidate(row, centers.get(row.get("park_id", "")))
        rows.append({**row, **extra})
    return rows


def build_query_index(query_plan_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("query_id", ""): row for row in query_plan_rows}


def build_refetch_plan(
    fetch_log_rows: list[dict[str, str]], query_plan_rows: list[dict[str, str]]
) -> list[dict[str, str]]:
    query_index = build_query_index(query_plan_rows)
    rows: list[dict[str, str]] = []
    for row in fetch_log_rows:
        if row.get("api_endpoint") != "v5/place/around":
            continue
        params = parse_params(row.get("params_summary", ""))
        result_count = int(row.get("result_count") or 0)
        page_size = int(params.get("page_size") or 0)
        issue_type = ""
        if result_count == 0:
            issue_type = "zero_result"
        elif page_size and result_count >= page_size:
            issue_type = "page_size_cap"
        if not issue_type:
            continue

        query = query_index.get(row.get("query_id", ""), {})
        category = query.get("commercial_category", "")
        if issue_type == "page_size_cap":
            recommended_action = "fetch_page_2_then_rebuild_dedupe"
            suggested_page_num = "2"
            suggested_keywords = params.get("keywords", "")
            notes = "首轮返回达到单页上限，不能确认是否已覆盖完整供给；需要补抓下一页或缩小半径分段。"
            priority = "P0"
        else:
            recommended_action = "retry_with_synonyms_or_manual_check"
            suggested_page_num = "1"
            suggested_keywords = ALT_KEYWORDS.get(category, params.get("keywords", ""))
            notes = "零结果不能直接解释为业态缺失；先换关键词或结合现场/公开地图复核。"
            priority = "P1"

        rows.append(
            {
                "followup_id": f"AMAP-FOLLOWUP-{len(rows) + 1:03d}",
                "query_id": row.get("query_id", ""),
                "park_id": row.get("park_id", ""),
                "park_name": query.get("park_name", ""),
                "commercial_category": category,
                "issue_type": issue_type,
                "current_keyword": params.get("keywords", ""),
                "current_radius_m": params.get("radius", ""),
                "current_page_size": params.get("page_size", ""),
                "current_result_count": row.get("result_count", ""),
                "recommended_action": recommended_action,
                "suggested_page_num": suggested_page_num,
                "suggested_keywords": suggested_keywords,
                "suggested_radius_m": params.get("radius", ""),
                "requires_amap_key": "yes",
                "priority": priority,
                "notes": notes,
            }
        )
    return rows


def write_report(precheck_rows: list[dict[str, str]], followup_rows: list[dict[str, str]]) -> None:
    by_status = Counter(row["spatial_precheck_status"] for row in precheck_rows)
    by_park = defaultdict(Counter)
    by_use = Counter(row["supply_use_status"] for row in precheck_rows)
    for row in precheck_rows:
        by_park[row["park_name"]][row["spatial_precheck_status"]] += 1

    followup_by_issue = Counter(row["issue_type"] for row in followup_rows)
    page_cap = [row["query_id"] for row in followup_rows if row["issue_type"] == "page_size_cap"]
    zero_result = [row["query_id"] for row in followup_rows if row["issue_type"] == "zero_result"]

    lines = [
        "# 高德候选 POI 空间预过滤报告",
        "",
        "## 结论",
        "",
        f"- 输入候选：{len(precheck_rows)} 条。",
        f"- 空间预过滤状态：{dict(sorted(by_status.items()))}",
        f"- 供给使用状态：{dict(sorted(by_use.items()))}",
        f"- 补抓/复核计划：{len(followup_rows)} 条，按问题类型 {dict(sorted(followup_by_issue.items()))}。",
        "",
        "## 按公园统计",
        "",
    ]
    for park_name, counter in sorted(by_park.items()):
        lines.append(f"- {park_name}：{dict(sorted(counter.items()))}")

    lines.extend(
        [
            "",
            "## 需补抓或复核查询",
            "",
            f"- 达到单页上限：{';'.join(page_cap) if page_cap else '无'}。",
            f"- 零结果查询：{';'.join(zero_result) if zero_result else '无'}。",
            "",
            "## 口径限制",
            "",
            "- 本报告不是最终园内/园外判定；当前没有真实公园 polygon 或现场清单。",
            "- `spatial_precheck_status` 只基于高德中心点距离、POI 名称/地址文本和 PDF 种子匹配做预过滤。",
            "- 所有记录的 `supply_use_status` 均保持为 `do_not_use_as_in_park_supply_yet`，后续必须经过边界、入口节点或现场核验后才能进入缺口计算。",
            "- 达到单页上限的查询需要高德 Key 支持分页补抓；零结果查询需要换关键词或人工复核，不能直接证明该业态不存在。",
            "",
            "## 输出文件",
            "",
            "- `70_outputs/processed_tables/poi_supply_candidates_amap_spatial_precheck.csv`",
            "- `50_external_gis/amap_poi/amap_refetch_followup_plan.csv`",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    candidate_rows = read_csv(CANDIDATES)
    fetch_log_rows = read_csv(FETCH_LOG)
    query_plan_rows = read_csv(QUERY_PLAN)

    precheck_rows = build_precheck_rows(candidate_rows, fetch_log_rows)
    precheck_fields = list(candidate_rows[0].keys()) + EXTRA_PRECHECK_FIELDS if candidate_rows else EXTRA_PRECHECK_FIELDS
    write_csv(OUT_PRECHECK, precheck_rows, precheck_fields)

    refetch_rows = build_refetch_plan(fetch_log_rows, query_plan_rows)
    write_csv(OUT_REFETCH_PLAN, refetch_rows, REFETCH_FIELDS)

    write_report(precheck_rows, refetch_rows)
    print(f"wrote {len(precheck_rows)} spatial precheck rows to {OUT_PRECHECK}")
    print(f"wrote {len(refetch_rows)} follow-up rows to {OUT_REFETCH_PLAN}")
    print(f"wrote report to {REPORT}")


if __name__ == "__main__":
    main()
