from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TABLES_JSONL = ROOT / "30_extraction" / "tables" / "pdf_native_tables.jsonl"
RAW_SEED = ROOT / "50_external_gis" / "poi_supply" / "pdf_hot_visit_poi_seed_raw.csv"
SUPPLY_BASE = ROOT / "70_outputs" / "processed_tables" / "poi_supply_base.csv"
REPORT = ROOT / "40_quality_evidence" / "poi_supply_base_report.md"


FOOD = "\u7f8e\u98df"
SHOPPING = "\u8d2d\u7269"
LEISURE = "\u5a31\u4e50\u4f11\u95f2"
SPORTS = "\u8fd0\u52a8\u5065\u8eab"
CITY_GREEN_HEART = "\u57ce\u5e02\u7eff\u5fc3\u516c\u56ed"
OLYMPIC_FOREST = "\u5965\u6797\u5339\u514b\u68ee\u6797\u516c\u56ed"


TABLE_SCOPE = {
    "TBL-00005": ("sample_city_green_heart", CITY_GREEN_HEART, "flow_population", FOOD),
    "TBL-00104": ("sample_olympic_forest", OLYMPIC_FOREST, "working_population", FOOD),
    "TBL-00106": ("sample_olympic_forest", OLYMPIC_FOREST, "working_population", SHOPPING),
    "TBL-00108": ("sample_olympic_forest", OLYMPIC_FOREST, "working_population", LEISURE),
    "TBL-00109": ("sample_olympic_forest", OLYMPIC_FOREST, "working_population", SPORTS),
    "TBL-00119": ("sample_olympic_forest", OLYMPIC_FOREST, "flow_population", FOOD),
    "TBL-00121": ("sample_olympic_forest", OLYMPIC_FOREST, "flow_population", SHOPPING),
    "TBL-00123": ("sample_olympic_forest", OLYMPIC_FOREST, "flow_population", LEISURE),
    "TBL-00124": ("sample_olympic_forest", OLYMPIC_FOREST, "flow_population", SPORTS),
}


RAW_FIELDS = [
    "source_record_id",
    "park_id",
    "park_name",
    "source_population_segment",
    "source_file",
    "source_page",
    "source_table_id",
    "source_rank",
    "source_business_scope",
    "poi_name",
    "source_index",
    "avg_cost_yuan",
    "business_area",
    "source_extra_info",
    "source_kind",
    "validation_status",
    "confidence",
    "notes",
]

BASE_FIELDS = [
    "poi_record_id",
    "park_id",
    "park_name",
    "poi_name",
    "standard_category",
    "source_business_scopes",
    "source_population_segments",
    "max_source_index",
    "avg_cost_yuan",
    "business_area",
    "source_table_ids",
    "source_pages",
    "source_ranks",
    "source_kind",
    "amap_poi_id",
    "amap_type",
    "amap_typecode",
    "longitude",
    "latitude",
    "distance_m",
    "radius_m",
    "in_park_status",
    "validation_status",
    "confidence",
    "notes",
]


def load_tables() -> dict[str, dict]:
    tables: dict[str, dict] = {}
    with TABLES_JSONL.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                tables[item["table_id"]] = item
    return tables


def clean_text(value: object) -> str:
    return re.sub(r"\s+", "", str(value or "")).strip()


def clean_poi_name(value: object) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    # PDF table extraction can split Chinese words across line breaks, while
    # English brand names such as "grid coffee" need to keep word spaces.
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"(?<=[（(])\s+", "", text)
    text = re.sub(r"\s+(?=[）)])", "", text)
    return text


def parse_avg_cost(extra_info: str) -> str:
    if "\u4eba\u5747\u6d88\u8d39" not in extra_info:
        return ""
    match = re.search(r"(\d+(?:\.\d+)?)", extra_info)
    return match.group(1) if match else ""


def iter_poi_rows(table: dict) -> list[dict[str, str]]:
    rows = table["rows"]
    if not rows:
        return []

    header = [str(cell) for cell in rows[0]]
    groups: list[int] = []
    for index, name in enumerate(header):
        if name == "POI\u540d\u79f0" and index > 0:
            groups.append(index - 1)

    parsed: list[dict[str, str]] = []
    for row in rows[1:]:
        for start in groups:
            values = list(row) + [""] * 6
            rank = clean_text(values[start])
            poi_name = clean_poi_name(values[start + 1])
            source_index = clean_text(values[start + 2])
            extra = clean_text(values[start + 3])
            business_area = clean_text(values[start + 4])

            if not poi_name or rank in {"", "0"}:
                continue
            if "\u6837\u672c\u91cf\u4e0d\u8db3" in poi_name:
                continue
            parsed.append(
                {
                    "source_rank": rank,
                    "poi_name": poi_name,
                    "source_index": source_index,
                    "avg_cost_yuan": parse_avg_cost(extra),
                    "business_area": business_area,
                    "source_extra_info": extra,
                }
            )
    return parsed


def classify(scope: str, poi_name: str) -> str:
    name_lower = poi_name.lower()
    if "\u5496\u5561" in poi_name or "coffee" in name_lower:
        return "coffee"
    if "\u666e\u62c9\u63d0" in poi_name or "\u745c\u4f3d" in poi_name:
        return "yoga_pilates"
    if scope == FOOD:
        if "\u4eb2\u5b50" in poi_name:
            return "family_restaurant"
        return "food_dining"
    if scope == SHOPPING:
        if "\u7f57\u68ee" in poi_name or "\u4fbf\u5229" in poi_name:
            return "convenience_retail"
        if "\u8fd0\u52a8" in poi_name or "\u6237\u5916" in poi_name or "\u88c5\u5907" in poi_name or "\u7403\u62cd" in poi_name:
            return "sports_supply"
        return "retail"
    if scope == LEISURE:
        if "\u6e38\u4e50\u573a" in poi_name:
            return "family_recreation"
        return "leisure"
    if scope == SPORTS:
        return "sports_service"
    return "other"


def build_raw_seed_rows(tables: dict[str, dict]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for table_id, (park_id, park_name, segment, scope) in TABLE_SCOPE.items():
        table = tables[table_id]
        for parsed in iter_poi_rows(table):
            rows.append(
                {
                    "source_record_id": f"PDFSEED-{len(rows) + 1:04d}",
                    "park_id": park_id,
                    "park_name": park_name,
                    "source_population_segment": segment,
                    "source_file": table["source_file"],
                    "source_page": str(table["page"]),
                    "source_table_id": table_id,
                    "source_rank": parsed["source_rank"],
                    "source_business_scope": scope,
                    "poi_name": parsed["poi_name"],
                    "source_index": parsed["source_index"],
                    "avg_cost_yuan": parsed["avg_cost_yuan"],
                    "business_area": parsed["business_area"],
                    "source_extra_info": parsed["source_extra_info"],
                    "source_kind": "pdf_hot_visit_seed",
                    "validation_status": "needs_amap_or_field_verification",
                    "confidence": "medium",
                    "notes": "\u533a\u57df\u5185\u70ed\u95e8\u5230\u8bbf\u8868\u79cd\u5b50\uff0c\u4e0d\u7b49\u4e8e\u56ed\u5185\u5b8c\u6574\u4f9b\u7ed9\u6e05\u5355\u3002",
                }
            )
    return rows


def best_numeric(values: list[str]) -> str:
    numbers = [float(v) for v in values if re.fullmatch(r"\d+(?:\.\d+)?", str(v or ""))]
    if not numbers:
        return ""
    value = max(numbers)
    return str(int(value)) if value.is_integer() else str(value)


def first_non_empty(values: list[str]) -> str:
    for value in values:
        if str(value or "").strip():
            return str(value)
    return ""


def unique_join(values: list[str]) -> str:
    seen: list[str] = []
    for value in values:
        value = str(value or "").strip()
        if value and value not in seen:
            seen.append(value)
    return ";".join(seen)


def build_supply_base(raw_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in raw_rows:
        grouped[(row["park_id"], row["poi_name"])].append(row)

    base_rows: list[dict[str, str]] = []
    for (park_id, poi_name), group in sorted(grouped.items()):
        category = classify(group[0]["source_business_scope"], poi_name)
        base_rows.append(
            {
                "poi_record_id": f"POI-{len(base_rows) + 1:04d}",
                "park_id": park_id,
                "park_name": group[0]["park_name"],
                "poi_name": poi_name,
                "standard_category": category,
                "source_business_scopes": unique_join([r["source_business_scope"] for r in group]),
                "source_population_segments": unique_join([r["source_population_segment"] for r in group]),
                "max_source_index": best_numeric([r["source_index"] for r in group]),
                "avg_cost_yuan": first_non_empty([r["avg_cost_yuan"] for r in group]),
                "business_area": first_non_empty([r["business_area"] for r in group]),
                "source_table_ids": unique_join([r["source_table_id"] for r in group]),
                "source_pages": unique_join([r["source_page"] for r in group]),
                "source_ranks": unique_join([r["source_rank"] for r in group]),
                "source_kind": "pdf_hot_visit_seed",
                "amap_poi_id": "",
                "amap_type": "",
                "amap_typecode": "",
                "longitude": "",
                "latitude": "",
                "distance_m": "",
                "radius_m": "",
                "in_park_status": "unknown",
                "validation_status": "needs_amap_or_field_verification",
                "confidence": "medium",
                "notes": "\u6765\u81ea PDF \u533a\u57df\u5185\u70ed\u95e8\u5230\u8bbf\u8868\uff1b\u5c1a\u672a\u7ecf\u9ad8\u5fb7 POI \u5750\u6807\u3001\u8ddd\u79bb\u548c\u8425\u4e1a\u72b6\u6001\u6838\u9a8c\u3002",
            }
        )
    return base_rows


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def count_by(rows: list[dict[str, str]], field: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in rows:
        key = row[field]
        result[key] = result.get(key, 0) + 1
    return dict(sorted(result.items()))


def write_report(raw_rows: list[dict[str, str]], base_rows: list[dict[str, str]]) -> None:
    lines = [
        "# POI 供给底表 P1 初版报告",
        "",
        "## 结果",
        "",
        f"- PDF 区域内热门到访 POI 种子行：{len(raw_rows)} 条。",
        f"- 去重后的初版供给底表：{len(base_rows)} 条。",
        f"- 按公园统计：{count_by(base_rows, 'park_name')}",
        f"- 按标准业态统计：{count_by(base_rows, 'standard_category')}",
        "",
        "## 口径",
        "",
        "- 当前表只使用 PDF 中明确为“区域内范围内”的热门到访地点表。",
        "- 城市绿心仅纳入第 9 页区域内美食类热门到访表；后续需用高德补咖啡、零售、文创、运动等完整供给。",
        "- 奥森纳入工作人口和流动人口两组区域内商业相关表，并按 POI 名称去重。",
        "- 该表是供给核验种子，不是最终园内供给结论；是否在园内、是否营业、距离入口/节点多远，均需高德或现场清单闭合。",
        "",
        "## 输出文件",
        "",
        "- `50_external_gis/poi_supply/pdf_hot_visit_poi_seed_raw.csv`",
        "- `70_outputs/processed_tables/poi_supply_base.csv`",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    tables = load_tables()
    missing = sorted(set(TABLE_SCOPE) - set(tables))
    if missing:
        raise ValueError(f"Missing tables: {missing}")

    raw_rows = build_raw_seed_rows(tables)
    base_rows = build_supply_base(raw_rows)
    write_csv(RAW_SEED, RAW_FIELDS, raw_rows)
    write_csv(SUPPLY_BASE, BASE_FIELDS, base_rows)
    write_report(raw_rows, base_rows)
    print(f"wrote {len(raw_rows)} raw seed rows to {RAW_SEED}")
    print(f"wrote {len(base_rows)} supply rows to {SUPPLY_BASE}")
    print(f"wrote report to {REPORT}")


if __name__ == "__main__":
    main()
