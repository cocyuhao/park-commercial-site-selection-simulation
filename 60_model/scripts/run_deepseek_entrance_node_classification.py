from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "60_model" / "src"))

from llm_router import route_for, run_deepseek_task  # noqa: E402


INPUT_CSV = ROOT / "50_external_gis" / "amap_routes" / "amap_p0_entrance_node_candidates.csv"
OUT_CSV = ROOT / "50_external_gis" / "amap_routes" / "amap_p0_entrance_node_semantic_draft_deepseek.csv"
OUT_DIR = ROOT / "60_model" / "llm_runs"
RAW_JSONL = OUT_DIR / "deepseek_entrance_node_semantic_raw.jsonl"
PROGRESS_JSON = OUT_DIR / "deepseek_entrance_node_semantic_progress.json"
REPORT = ROOT / "40_quality_evidence" / "deepseek_entrance_node_semantic_report.md"


ALLOWED_NODE_TYPES = {
    "official_or_named_gate",
    "parking_access_node",
    "transit_or_station_node",
    "internal_facility_node",
    "nearby_commercial_or_wrong_match",
    "park_area_centroid_or_generic",
    "unclear",
}

ALLOWED_PRIORITIES = {
    "P0_best_access_proxy_candidate",
    "P1_valid_visit_node_candidate",
    "P2_context_or_internal_node",
    "P3_low_confidence_or_wrong_match",
}

FIELDS = [
    "node_candidate_id",
    "query_id",
    "park_id",
    "park_name",
    "keyword",
    "node_kind",
    "amap_poi_id",
    "node_name",
    "amap_type",
    "address",
    "longitude",
    "latitude",
    "semantic_node_type_draft",
    "route_use_priority_draft",
    "official_entrance_likelihood_draft",
    "visitor_origin_suitability_draft",
    "needs_field_validation",
    "reason_draft",
    "output_status",
    "executor",
    "model",
    "review_gate",
    "llm_task_id",
    "run_id",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def chunked(rows: list[dict[str, str]], size: int) -> list[list[dict[str, str]]]:
    return [rows[index : index + size] for index in range(0, len(rows), size)]


def compact_item(row: dict[str, str], index: int) -> dict[str, str]:
    return {
        "node_candidate_id": f"NODE-CAND-{index:04d}",
        "query_id": row.get("query_id", ""),
        "park_id": row.get("park_id", ""),
        "park_name": row.get("park_name", ""),
        "keyword": row.get("keyword", ""),
        "node_kind": row.get("node_kind", ""),
        "node_name": row.get("node_name", ""),
        "amap_type": row.get("amap_type", ""),
        "address": row.get("address", ""),
    }


def extract_json_array(text: str) -> list[dict[str, Any]]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped, flags=re.IGNORECASE).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    start = stripped.find("[")
    end = stripped.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("DeepSeek response does not contain a JSON array")
    data = json.loads(stripped[start : end + 1])
    if not isinstance(data, list):
        raise ValueError("DeepSeek response JSON is not a list")
    return data


def normalize_enum(value: Any, allowed: set[str], default: str) -> str:
    value = str(value or "").strip()
    return value if value in allowed else default


def normalize_confidence(value: Any) -> str:
    value = str(value or "").strip().lower()
    return value if value in {"low", "medium", "high"} else "low"


def make_messages(items: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "你是公园商业选址项目的低成本 GIS 语义初筛助手。"
                "你的输出只能作为 draft，不能做官方入口判断，不能标注 checked。"
                "只根据输入的高德名称、类型和地址分类；不要补充外部知识或发明事实。"
                "只输出 JSON 数组，不输出 Markdown。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请对以下入口/节点候选做语义初筛。\n"
                "semantic_node_type_draft 只能取：official_or_named_gate, parking_access_node, "
                "transit_or_station_node, internal_facility_node, nearby_commercial_or_wrong_match, "
                "park_area_centroid_or_generic, unclear。\n"
                "route_use_priority_draft 只能取：P0_best_access_proxy_candidate, "
                "P1_valid_visit_node_candidate, P2_context_or_internal_node, "
                "P3_low_confidence_or_wrong_match。\n"
                "official_entrance_likelihood_draft 和 visitor_origin_suitability_draft 只能取 low/medium/high。\n"
                "needs_field_validation 必须是 yes。\n"
                "output_status 必须是 draft。\n"
                "判断口径：明确门/出入口/入口/南门/北门/东门/西门优先作为入口候选；停车场/停车场出入口可作访问节点；"
                "站点/地铁/观光车售票处可作访问节点；体育场馆/商户/博物馆/餐厅/泛公园名通常不是官方入口；"
                "公园本体或泛名称为 centroid/generic。\n"
                "每个输入必须输出一条，字段为 node_candidate_id, semantic_node_type_draft, route_use_priority_draft, "
                "official_entrance_likelihood_draft, visitor_origin_suitability_draft, needs_field_validation, reason_draft, output_status。\n"
                "输入 JSON：\n"
                + json.dumps(items, ensure_ascii=False)
            ),
        },
    ]


def run(chunk_size: int) -> None:
    task_id = "LLM-011"
    route = route_for(task_id)
    source_rows = read_csv(INPUT_CSV)
    indexed = [(index, row, compact_item(row, index)) for index, row in enumerate(source_rows, start=1)]
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    results_by_id: dict[str, dict[str, str]] = {}
    raw_records: list[dict[str, Any]] = []
    with RAW_JSONL.open("w", encoding="utf-8") as raw_file:
        for chunk_index, chunk in enumerate(chunked(indexed, chunk_size), start=1):
            items = [item for _, _, item in chunk]
            content = run_deepseek_task(task_id, make_messages(items), temperature=0.0)
            raw_record = {
                "run_id": run_id,
                "task_id": task_id,
                "task_name": route.task_name,
                "executor": route.default_executor,
                "model": route.model,
                "output_status": route.output_status,
                "chunk_index": chunk_index,
                "input_node_candidate_ids": [item["node_candidate_id"] for item in items],
                "response_excerpt": content[:3000],
            }
            raw_file.write(json.dumps(raw_record, ensure_ascii=False) + "\n")
            raw_records.append(raw_record)
            parsed = extract_json_array(content)
            for item in parsed:
                node_id = str(item.get("node_candidate_id", "")).strip()
                if not node_id:
                    continue
                results_by_id[node_id] = {
                    "semantic_node_type_draft": normalize_enum(
                        item.get("semantic_node_type_draft", ""),
                        ALLOWED_NODE_TYPES,
                        "unclear",
                    ),
                    "route_use_priority_draft": normalize_enum(
                        item.get("route_use_priority_draft", ""),
                        ALLOWED_PRIORITIES,
                        "P3_low_confidence_or_wrong_match",
                    ),
                    "official_entrance_likelihood_draft": normalize_confidence(item.get("official_entrance_likelihood_draft", "")),
                    "visitor_origin_suitability_draft": normalize_confidence(item.get("visitor_origin_suitability_draft", "")),
                    "needs_field_validation": "yes",
                    "reason_draft": str(item.get("reason_draft", "") or "")[:260],
                    "output_status": "draft",
                    "executor": route.default_executor,
                    "model": route.model,
                    "review_gate": route.review_gate,
                    "llm_task_id": task_id,
                    "run_id": run_id,
                }

    out_rows: list[dict[str, str]] = []
    for index, source, compact in indexed:
        node_id = compact["node_candidate_id"]
        result = results_by_id.get(
            node_id,
            {
                "semantic_node_type_draft": "unclear",
                "route_use_priority_draft": "P3_low_confidence_or_wrong_match",
                "official_entrance_likelihood_draft": "low",
                "visitor_origin_suitability_draft": "low",
                "needs_field_validation": "yes",
                "reason_draft": "DeepSeek 未返回该节点，保守标记为 unclear。",
                "output_status": "draft",
                "executor": route.default_executor,
                "model": route.model,
                "review_gate": route.review_gate,
                "llm_task_id": task_id,
                "run_id": run_id,
            },
        )
        out_rows.append(
            {
                "node_candidate_id": node_id,
                "query_id": source.get("query_id", ""),
                "park_id": source.get("park_id", ""),
                "park_name": source.get("park_name", ""),
                "keyword": source.get("keyword", ""),
                "node_kind": source.get("node_kind", ""),
                "amap_poi_id": source.get("amap_poi_id", ""),
                "node_name": source.get("node_name", ""),
                "amap_type": source.get("amap_type", ""),
                "address": source.get("address", ""),
                "longitude": source.get("longitude", ""),
                "latitude": source.get("latitude", ""),
                **result,
            }
        )

    write_csv(OUT_CSV, out_rows, FIELDS)
    PROGRESS_JSON.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "total_rows": len(source_rows),
                "classified_rows": len(out_rows),
                "remaining_rows": len(source_rows) - len(out_rows),
                "raw_chunks": len(raw_records),
                "chunk_size": chunk_size,
                "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    by_type = Counter(row["semantic_node_type_draft"] for row in out_rows)
    by_priority = Counter(row["route_use_priority_draft"] for row in out_rows)
    by_status = Counter(row["output_status"] for row in out_rows)
    lines = [
        "# DeepSeek 入口/节点语义初筛报告",
        "",
        "## 结论",
        "",
        f"- 输入节点：{len(source_rows)} 条。",
        f"- 输出状态：{dict(sorted(by_status.items()))}",
        f"- 语义类型：{dict(sorted(by_type.items()))}",
        f"- 路径使用优先级：{dict(sorted(by_priority.items()))}",
        f"- DeepSeek 批次：{len(raw_records)} 个。",
        "",
        "## 口径限制",
        "",
        "- 本结果由 DeepSeek 生成，只能作为 `draft`。",
        "- 不能作为官方入口清单或最终可达性结论。",
        "- 后续必须由本地规则、现场或官方资料确认。",
        "",
        "## 输出文件",
        "",
        "- `50_external_gis/amap_routes/amap_p0_entrance_node_semantic_draft_deepseek.csv`",
        "- `60_model/llm_runs/deepseek_entrance_node_semantic_raw.jsonl`",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(out_rows)} draft node classifications to {OUT_CSV}")
    print(f"wrote report to {REPORT}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunk-size", type=int, default=8)
    args = parser.parse_args()
    run(args.chunk_size)


if __name__ == "__main__":
    main()
