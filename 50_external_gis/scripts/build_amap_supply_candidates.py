from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AMAP_CLEAN = ROOT / "50_external_gis" / "amap_poi" / "amap_poi_clean.csv"
PDF_SUPPLY = ROOT / "70_outputs" / "processed_tables" / "poi_supply_base.csv"
OUT_CSV = ROOT / "70_outputs" / "processed_tables" / "poi_supply_candidates_amap.csv"
REPORT = ROOT / "40_quality_evidence" / "amap_supply_candidates_report.md"


FIELDS = [
    "candidate_id",
    "park_id",
    "park_name",
    "amap_poi_id",
    "poi_name",
    "standard_categories",
    "amap_keywords",
    "amap_type",
    "amap_typecode",
    "address",
    "business_area",
    "longitude",
    "latitude",
    "min_distance_m",
    "distance_band",
    "rating",
    "cost_yuan",
    "opentime_today",
    "opentime_week",
    "tel",
    "source_query_ids",
    "pdf_seed_match_status",
    "pdf_seed_poi_record_ids",
    "pdf_seed_poi_names",
    "in_park_status",
    "validation_status",
    "confidence",
    "notes",
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


def normalize_name(value: str) -> str:
    text = str(value or "").lower()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[()（）·\-_—/、,，.。:：;；]", "", text)
    return text


def unique_join(values: list[str]) -> str:
    seen: list[str] = []
    for value in values:
        value = str(value or "").strip()
        if value and value not in seen:
            seen.append(value)
    return ";".join(seen)


def best_value(values: list[str]) -> str:
    for value in values:
        if str(value or "").strip():
            return str(value)
    return ""


def min_distance(values: list[str]) -> str:
    numbers = []
    for value in values:
        try:
            numbers.append(float(value))
        except (TypeError, ValueError):
            pass
    if not numbers:
        return ""
    value = min(numbers)
    return str(int(value)) if value.is_integer() else str(value)


def distance_band(distance_m: str) -> str:
    try:
        distance = float(distance_m)
    except (TypeError, ValueError):
        return "unknown"
    if distance <= 500:
        return "0-500m"
    if distance <= 1000:
        return "501-1000m"
    if distance <= 1500:
        return "1001-1500m"
    if distance <= 3000:
        return "1501-3000m"
    return "3000m+"


def build_pdf_index(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    indexed: list[dict[str, str]] = []
    for row in rows:
        indexed.append({**row, "_norm": normalize_name(row.get("poi_name", ""))})
    return indexed


def find_pdf_matches(amap_row: dict[str, str], pdf_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    norm = normalize_name(amap_row.get("poi_name", ""))
    if not norm:
        return []
    matches = []
    for pdf_row in pdf_rows:
        pdf_norm = pdf_row["_norm"]
        if not pdf_norm:
            continue
        if norm == pdf_norm or norm in pdf_norm or pdf_norm in norm:
            matches.append(pdf_row)
    return matches


def build_candidates(amap_rows: list[dict[str, str]], pdf_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in amap_rows:
        key = (row.get("park_id", ""), row.get("amap_poi_id", ""))
        if key[0] and key[1]:
            grouped[key].append(row)

    candidates: list[dict[str, str]] = []
    pdf_index = build_pdf_index(pdf_rows)
    for (_park_id, _amap_id), group in sorted(grouped.items()):
        distance = min_distance([row.get("distance_m", "") for row in group])
        sample = group[0]
        matches = find_pdf_matches(sample, pdf_index)
        candidates.append(
            {
                "candidate_id": f"AMAP-POI-{len(candidates) + 1:04d}",
                "park_id": sample.get("park_id", ""),
                "park_name": sample.get("park_name", ""),
                "amap_poi_id": sample.get("amap_poi_id", ""),
                "poi_name": sample.get("poi_name", ""),
                "standard_categories": unique_join([row.get("commercial_category", "") for row in group]),
                "amap_keywords": unique_join([row.get("amap_keyword", "") for row in group]),
                "amap_type": sample.get("amap_type", ""),
                "amap_typecode": sample.get("amap_typecode", ""),
                "address": sample.get("address", ""),
                "business_area": sample.get("business_area", ""),
                "longitude": sample.get("longitude", ""),
                "latitude": sample.get("latitude", ""),
                "min_distance_m": distance,
                "distance_band": distance_band(distance),
                "rating": best_value([row.get("rating", "") for row in group]),
                "cost_yuan": best_value([row.get("cost_yuan", "") for row in group]),
                "opentime_today": best_value([row.get("opentime_today", "") for row in group]),
                "opentime_week": best_value([row.get("opentime_week", "") for row in group]),
                "tel": best_value([row.get("tel", "") for row in group]),
                "source_query_ids": unique_join([row.get("query_id", "") for row in group]),
                "pdf_seed_match_status": "matched_pdf_seed" if matches else "not_in_pdf_seed",
                "pdf_seed_poi_record_ids": unique_join([row.get("poi_record_id", "") for row in matches]),
                "pdf_seed_poi_names": unique_join([row.get("poi_name", "") for row in matches]),
                "in_park_status": "needs_boundary_filter",
                "validation_status": "api_returned_needs_boundary_filter",
                "confidence": "medium",
                "notes": "按公园和高德 POI ID 去重；仍需公园边界/入口节点过滤和现场营业核验。",
            }
        )
    return candidates


def write_report(rows: list[dict[str, str]]) -> None:
    by_park = Counter(row["park_name"] for row in rows)
    by_band = Counter(row["distance_band"] for row in rows)
    by_match = Counter(row["pdf_seed_match_status"] for row in rows)
    categories = Counter()
    for row in rows:
        for category in row["standard_categories"].split(";"):
            if category:
                categories[category] += 1

    lines = [
        "# 高德供给候选表报告",
        "",
        "## 结果",
        "",
        f"- 高德去重供给候选：{len(rows)} 条。",
        f"- 按公园统计：{dict(sorted(by_park.items()))}",
        f"- 按距离圈层统计：{dict(sorted(by_band.items()))}",
        f"- PDF 种子匹配状态：{dict(sorted(by_match.items()))}",
        f"- 按业态统计（去重 POI 可归入多个查询业态）：{dict(sorted(categories.items()))}",
        "",
        "## 口径",
        "",
        "- 本表按 `park_id + amap_poi_id` 去重，减少同一 POI 被多个关键词重复命中的问题。",
        "- `min_distance_m` 是高德返回的该 POI 到查询中心点最小距离，不是步行路径距离。",
        "- `in_park_status` 仍为 `needs_boundary_filter`，需要公园边界或入口/节点坐标进一步过滤。",
        "- `pdf_seed_match_status` 仅表示名称层面的粗匹配，不表示供给数量已经闭合。",
        "",
        "## 输出文件",
        "",
        "- `70_outputs/processed_tables/poi_supply_candidates_amap.csv`",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    amap_rows = read_csv(AMAP_CLEAN)
    pdf_rows = read_csv(PDF_SUPPLY)
    candidates = build_candidates(amap_rows, pdf_rows)
    write_csv(candidates)
    write_report(candidates)
    print(f"wrote {len(candidates)} Amap supply candidates to {OUT_CSV}")
    print(f"wrote report to {REPORT}")


if __name__ == "__main__":
    main()
