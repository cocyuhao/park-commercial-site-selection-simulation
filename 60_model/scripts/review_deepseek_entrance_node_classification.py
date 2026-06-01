from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DRAFT_CSV = ROOT / "50_external_gis" / "amap_routes" / "amap_p0_entrance_node_semantic_draft_deepseek.csv"
OUT_QUEUE = ROOT / "50_external_gis" / "amap_routes" / "amap_p0_entrance_node_semantic_review_queue.csv"
OUT_REVIEW = ROOT / "40_quality_evidence" / "deepseek_entrance_node_semantic_review.csv"
REPORT = ROOT / "40_quality_evidence" / "deepseek_entrance_node_semantic_review.md"


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

QUEUE_FIELDS = [
    "semantic_review_id",
    "node_candidate_id",
    "park_id",
    "park_name",
    "node_name",
    "amap_type",
    "address",
    "semantic_node_type_draft",
    "route_use_priority_draft",
    "official_entrance_likelihood_draft",
    "visitor_origin_suitability_draft",
    "local_rule_priority",
    "final_use_gate",
    "review_instruction",
    "output_status",
]
REVIEW_FIELDS = ["check_id", "status", "severity", "finding", "evidence"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def local_rule_priority(row: dict[str, str]) -> str:
    name = row.get("node_name", "")
    amap_type = row.get("amap_type", "")
    address = row.get("address", "")
    if "暂停营业" in name or "暂停营业" in address:
        return "P3_unclear_manual_check"
    commercial_or_facility = any(
        token in amap_type or token in name
        for token in ["餐饮", "中餐厅", "快餐", "博物馆", "运动场馆", "网球场", "乒乓球", "羽毛球", "售票处"]
    )
    if any(token in name for token in ["出入口", "入口", "南门", "北门", "东门", "西门"]):
        return "P0_manual_check_gate_or_entrance"
    if "停车场" in name:
        return "P1_manual_check_parking_access"
    if any(token in name for token in ["站", "地铁"]):
        return "P1_manual_check_visit_or_transit_node"
    if commercial_or_facility:
        return "P2_context_node_or_possible_wrong_match"
    if any(token in address for token in ["出入口", "入口", "南门", "北门", "东门", "西门"]):
        return "P2_context_node_or_possible_wrong_match"
    return "P3_unclear_manual_check"


def final_use_gate(row: dict[str, str]) -> str:
    if row["local_rule_priority"].startswith("P0"):
        return "candidate_access_node_needs_official_or_field_confirmation"
    if row["local_rule_priority"].startswith("P1"):
        return "secondary_access_node_needs_field_confirmation"
    return "do_not_use_as_access_node_until_manual_review"


def review_instruction(row: dict[str, str]) -> str:
    gate = row["final_use_gate"]
    if gate.startswith("candidate"):
        return "优先人工核验是否为官方入口/出入口；确认后可作为 P1 路径代理节点。"
    if gate.startswith("secondary"):
        return "可作为停车/到达节点候选；需确认游客是否可从该节点进入或到达目标 POI。"
    return "暂不作为入口节点；仅保留为上下文或误匹配候选，必要时现场复核。"


def build_queue(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in rows:
        local_priority = local_rule_priority(row)
        queue_row = {
            "semantic_review_id": f"NODE-SEM-REVIEW-{len(out) + 1:04d}",
            "node_candidate_id": row.get("node_candidate_id", ""),
            "park_id": row.get("park_id", ""),
            "park_name": row.get("park_name", ""),
            "node_name": row.get("node_name", ""),
            "amap_type": row.get("amap_type", ""),
            "address": row.get("address", ""),
            "semantic_node_type_draft": row.get("semantic_node_type_draft", ""),
            "route_use_priority_draft": row.get("route_use_priority_draft", ""),
            "official_entrance_likelihood_draft": row.get("official_entrance_likelihood_draft", ""),
            "visitor_origin_suitability_draft": row.get("visitor_origin_suitability_draft", ""),
            "local_rule_priority": local_priority,
            "final_use_gate": "",
            "review_instruction": "",
            "output_status": row.get("output_status", ""),
        }
        queue_row["final_use_gate"] = final_use_gate(queue_row)
        queue_row["review_instruction"] = review_instruction(queue_row)
        out.append(queue_row)
    order = {
        "P0_manual_check_gate_or_entrance": 0,
        "P1_manual_check_parking_access": 1,
        "P1_manual_check_visit_or_transit_node": 2,
        "P2_context_node_or_possible_wrong_match": 3,
        "P3_unclear_manual_check": 4,
    }
    return sorted(out, key=lambda row: (order.get(row["local_rule_priority"], 9), row["park_id"], row["node_name"]))


def add_review(rows: list[dict[str, str]], status: str, severity: str, finding: str, evidence: str) -> None:
    rows.append(
        {
            "check_id": f"DSNODE-{len(rows) + 1:03d}",
            "status": status,
            "severity": severity,
            "finding": finding,
            "evidence": evidence,
        }
    )


def build_review(draft_rows: list[dict[str, str]], queue_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    review: list[dict[str, str]] = []
    statuses = Counter(row.get("output_status", "") for row in draft_rows)
    executors = Counter(row.get("executor", "") for row in draft_rows)
    task_ids = Counter(row.get("llm_task_id", "") for row in draft_rows)
    semantic_types = Counter(row.get("semantic_node_type_draft", "") for row in draft_rows)
    priorities = Counter(row.get("route_use_priority_draft", "") for row in draft_rows)
    invalid_types = sorted(value for value in semantic_types if value not in ALLOWED_NODE_TYPES)
    invalid_priorities = sorted(value for value in priorities if value not in ALLOWED_PRIORITIES)
    local_priorities = Counter(row.get("local_rule_priority", "") for row in queue_rows)
    gates = Counter(row.get("final_use_gate", "") for row in queue_rows)

    add_review(review, "pass" if len(draft_rows) == 45 else "fail", "error", f"DeepSeek node draft rows={len(draft_rows)}", "amap_p0_entrance_node_semantic_draft_deepseek.csv")
    add_review(review, "pass" if statuses == {"draft": len(draft_rows)} else "fail", "error", f"output_status counts={dict(statuses)}", "output_status")
    add_review(review, "pass" if executors == {"deepseek": len(draft_rows)} else "fail", "error", f"executor counts={dict(executors)}", "executor")
    add_review(review, "pass" if task_ids == {"LLM-011": len(draft_rows)} else "fail", "error", f"llm_task_id counts={dict(task_ids)}", "llm_task_id")
    add_review(review, "pass" if not invalid_types else "fail", "error", f"invalid semantic types={invalid_types}", "semantic_node_type_draft")
    add_review(review, "pass" if not invalid_priorities else "fail", "error", f"invalid route priorities={invalid_priorities}", "route_use_priority_draft")
    add_review(review, "pass", "info", f"semantic type distribution={dict(sorted(semantic_types.items()))}", "semantic_node_type_draft")
    add_review(review, "pass", "info", f"DeepSeek route priority distribution={dict(sorted(priorities.items()))}", "route_use_priority_draft")
    add_review(review, "pass", "info", f"local rule priority distribution={dict(sorted(local_priorities.items()))}", "local_rule_priority")
    add_review(review, "pass", "info", f"final use gate distribution={dict(sorted(gates.items()))}", "final_use_gate")
    return review


def write_report(review_rows: list[dict[str, str]], queue_rows: list[dict[str, str]]) -> None:
    by_status = Counter(row["status"] for row in review_rows)
    by_local = Counter(row["local_rule_priority"] for row in queue_rows)
    by_gate = Counter(row["final_use_gate"] for row in queue_rows)
    examples = [
        f"{row['node_candidate_id']} {row['park_name']} {row['node_name']} -> {row['local_rule_priority']}"
        for row in queue_rows
        if row["local_rule_priority"].startswith("P0")
    ][:20]
    lines = [
        "# DeepSeek 入口/节点语义初筛本地复核报告",
        "",
        "## 结论",
        "",
        f"- 复核项状态：{dict(sorted(by_status.items()))}",
        f"- 本地规则优先级：{dict(sorted(by_local.items()))}",
        f"- 最终使用门禁：{dict(sorted(by_gate.items()))}",
        "",
        "## P0 人工核验样例",
        "",
    ]
    for item in examples:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## 口径限制",
            "",
            "- DeepSeek 结果仍为 `draft`。",
            "- 本地规则只做字符串/类型初筛，不等于官方入口确认。",
            "- 所有节点进入路径或供给判断前仍需现场或官方资料确认。",
            "",
            "## 输出文件",
            "",
            "- `50_external_gis/amap_routes/amap_p0_entrance_node_semantic_review_queue.csv`",
            "- `40_quality_evidence/deepseek_entrance_node_semantic_review.csv`",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    draft_rows = read_csv(DRAFT_CSV)
    queue_rows = build_queue(draft_rows)
    review_rows = build_review(draft_rows, queue_rows)
    write_csv(OUT_QUEUE, queue_rows, QUEUE_FIELDS)
    write_csv(OUT_REVIEW, review_rows, REVIEW_FIELDS)
    write_report(review_rows, queue_rows)
    failures = [row for row in review_rows if row["status"] == "fail"]
    print(f"wrote semantic review queue rows={len(queue_rows)} to {OUT_QUEUE}")
    print(f"wrote review report to {REPORT}")
    print(f"failures={len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
