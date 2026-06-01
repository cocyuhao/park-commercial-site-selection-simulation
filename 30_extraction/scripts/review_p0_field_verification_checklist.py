from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECKLIST_CSV = ROOT / "70_outputs" / "processed_tables" / "p0_field_verification_checklist_deepseek.csv"
WORKLIST_CSV = ROOT / "70_outputs" / "processed_tables" / "poi_supply_p0_followup_worklist_enriched.csv"
ROUTE_REVIEW_CSV = ROOT / "70_outputs" / "processed_tables" / "poi_supply_p0_route_access_review.csv"
OUT_REVIEW = ROOT / "40_quality_evidence" / "p0_field_verification_checklist_local_review.csv"
OUT_REPORT = ROOT / "40_quality_evidence" / "p0_field_verification_checklist_local_review.md"

EXPECTED_TYPE_COUNTS = {
    "p0_poi_business_and_authorization": 7,
    "primary_access_node_field_check": 20,
    "secondary_parking_or_visit_node_field_check": 7,
}

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


def add(rows: list[dict[str, str]], status: str, severity: str, finding: str, evidence: str) -> None:
    rows.append(
        {
            "check_id": f"FIELD-AUDIT-{len(rows) + 1:03d}",
            "status": status,
            "severity": severity,
            "finding": finding,
            "evidence": evidence,
        }
    )


def ok(condition: bool) -> str:
    return "pass" if condition else "fail"


def normalize_name(text: str, park_name: str = "") -> str:
    value = text.strip()
    if park_name and value.startswith(park_name):
        value = value[len(park_name) :]
    value = re.sub(r"[（(](?:入口|出口|出入口)[）)]", "", value)
    value = re.sub(r"[（()）\s\-—]", "", value)
    return value


def parse_missing_fields(current_known_info: str) -> set[str]:
    mapping = {
        "tel": "contact",
        "contact": "contact",
        "opentime": "opening_hours",
        "opening_hours": "opening_hours",
        "cost_yuan": "cost_yuan",
    }
    missing: set[str] = set()
    for part in current_known_info.split(";"):
        key, _, value = part.partition("=")
        normalized = mapping.get(key.strip())
        if normalized and value.strip() == "缺失":
            missing.add(normalized)
    return missing


def extract_origin_phrases(question_text: str) -> list[str]:
    phrases = re.findall(r"从([^？。；;，,\n]+?)(?:能否|可否|是否|可以)", question_text)
    cleaned: list[str] = []
    for phrase in phrases:
        value = phrase.strip().strip("：:")
        if value:
            cleaned.append(value)
    return cleaned


def build_node_aliases(rows: list[dict[str, str]]) -> tuple[dict[str, set[str]], dict[str, list[str]]]:
    aliases_by_park: dict[str, set[str]] = defaultdict(set)
    clusters: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        if row.get("checklist_type") == "p0_poi_business_and_authorization":
            continue
        park_name = row.get("park_name", "")
        target_name = row.get("target_name", "")
        if not target_name:
            continue
        aliases_by_park[park_name].add(normalize_name(target_name, park_name))
        aliases_by_park[park_name].add(normalize_name(target_name))
        base_name = re.sub(r"[（(](?:入口|出口|出入口)[）)]$", "", target_name)
        cluster_key = f"{park_name}:{normalize_name(base_name, park_name)}"
        clusters[cluster_key].append(target_name)
    duplicate_clusters = {
        cluster_key: sorted(set(names))
        for cluster_key, names in clusters.items()
        if len(set(names)) > 1
    }
    return aliases_by_park, duplicate_clusters


def build_review(
    checklist_rows: list[dict[str, str]],
    worklist_rows: list[dict[str, str]],
    route_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    review: list[dict[str, str]] = []

    type_counts = Counter(row.get("checklist_type", "") for row in checklist_rows)
    status_counts = Counter(row.get("output_status", "") for row in checklist_rows)
    executor_counts = Counter(row.get("executor", "") for row in checklist_rows)
    task_counts = Counter(row.get("llm_task_id", "") for row in checklist_rows)
    gate_counts = Counter(row.get("p2_gate_draft", "") for row in checklist_rows)

    business_rows = [
        row for row in checklist_rows if row.get("checklist_type") == "p0_poi_business_and_authorization"
    ]

    worklist_by_id = {row.get("work_item_id", ""): row for row in worklist_rows}
    route_by_id = {row.get("work_item_id", ""): row for row in route_rows}
    checklist_source_ids = {row.get("source_id", "") for row in business_rows}
    worklist_ids = set(worklist_by_id)

    missing_field_mismatches: list[str] = []
    for row in business_rows:
        source_id = row.get("source_id", "")
        worklist_row = worklist_by_id.get(source_id)
        if not worklist_row:
            continue
        checklist_missing = parse_missing_fields(row.get("current_known_info", ""))
        worklist_missing = {
            field.strip()
            for field in worklist_row.get("missing_business_fields", "").split(";")
            if field.strip()
        }
        if checklist_missing != worklist_missing:
            missing_field_mismatches.append(
                f"{source_id}: checklist={sorted(checklist_missing)} worklist={sorted(worklist_missing)}"
            )

    blocked_business_items = [
        row.get("work_item_id", "")
        for row in worklist_rows
        if row.get("route_access_status") == "needs_entrance_or_route_api_verification"
        and row.get("operation_authorization_status") == "needs_operator_or_field_confirmation"
        and row.get("can_enter_p2_supply") == "no"
    ]
    route_ready_items = [
        row.get("work_item_id", "")
        for row in route_rows
        if row.get("route_access_status_after_api") == "amap_center_proxy_route_returned_needs_entrance_validation"
        and row.get("can_enter_p2_supply_after_route") == "no"
    ]

    node_aliases, duplicate_clusters = build_node_aliases(checklist_rows)
    unmatched_origin_phrases: list[str] = []
    for row in business_rows:
        park_name = row.get("park_name", "")
        aliases = node_aliases.get(park_name, set())
        for phrase in extract_origin_phrases(row.get("on_site_questions_draft", "")):
            normalized_phrase = normalize_name(phrase, park_name)
            matched = any(
                normalized_phrase and (normalized_phrase in alias or alias in normalized_phrase)
                for alias in aliases
            )
            if not matched:
                unmatched_origin_phrases.append(f"{row.get('checklist_id', '')}:{phrase}")

    add(review, ok(len(checklist_rows) == 34), "error", f"field checklist rows={len(checklist_rows)}", str(CHECKLIST_CSV))
    add(review, ok(type_counts == EXPECTED_TYPE_COUNTS), "error", f"field checklist type counts={dict(type_counts)}", "checklist_type")
    add(review, ok(status_counts == {"needs_review": len(checklist_rows)}), "error", f"field checklist output_status counts={dict(status_counts)}", "output_status")
    add(review, ok(executor_counts == {"deepseek": len(checklist_rows)}), "error", f"field checklist executor counts={dict(executor_counts)}", "executor")
    add(review, ok(task_counts == {"LLM-015": len(checklist_rows)}), "error", f"field checklist llm_task_id counts={dict(task_counts)}", "llm_task_id")
    add(review, ok(gate_counts == {"do_not_enter_p2_until_field_or_official_confirmation": len(checklist_rows)}), "error", f"field checklist p2 gate counts={dict(gate_counts)}", "p2_gate_draft")
    add(review, ok(checklist_source_ids == worklist_ids), "error", f"business checklist source ids={sorted(checklist_source_ids)}", str(WORKLIST_CSV))
    add(review, ok(not missing_field_mismatches), "error", f"business missing field mismatches={missing_field_mismatches}", "current_known_info vs missing_business_fields")
    add(review, ok(len(blocked_business_items) == len(worklist_rows)), "error", f"business items still blocked locally={len(blocked_business_items)}/{len(worklist_rows)}", "route_access_status + operation_authorization_status + can_enter_p2_supply")
    add(review, ok(set(route_ready_items) == worklist_ids), "error", f"center-proxy route reviewed items={sorted(route_ready_items)}", str(ROUTE_REVIEW_CSV))
    add(
        review,
        "warning" if unmatched_origin_phrases else "pass",
        "warning",
        f"unmatched business origin phrases={unmatched_origin_phrases}",
        "on_site_questions_draft vs node checklist aliases",
    )
    cluster_summary = {
        key: len(value)
        for key, value in sorted(duplicate_clusters.items())
    }
    add(review, "pass", "info", f"duplicate node clusters for field visit batching={cluster_summary}", "node checklist target_name")
    add(
        review,
        "pass",
        "info",
        f"all checklist rows still require field or official confirmation; no row can be closed locally={len(checklist_rows)}/{len(checklist_rows)}",
        "checklist + enriched worklist + route review",
    )
    return review


def write_report(
    review_rows: list[dict[str, str]],
    checklist_rows: list[dict[str, str]],
    worklist_rows: list[dict[str, str]],
) -> None:
    type_counts = Counter(row.get("checklist_type", "") for row in checklist_rows)
    review_statuses = Counter(row.get("status", "") for row in review_rows)
    missing_field_counts = Counter()
    for row in worklist_rows:
        for field in row.get("missing_business_fields", "").split(";"):
            field = field.strip()
            if field:
                missing_field_counts[field] += 1

    warning_rows = [row for row in review_rows if row["status"] == "warning"]
    cluster_rows = [
        row for row in review_rows if "duplicate node clusters" in row["finding"]
    ]

    lines = [
        "# P0 待核验清单本地审计报告",
        "",
        "## 结论",
        "",
        f"- 审计项状态：{dict(sorted(review_statuses.items()))}",
        f"- 清单类型分布：{dict(sorted(type_counts.items()))}",
        f"- 7 条业务核验项缺失经营字段分布：{dict(sorted(missing_field_counts.items()))}",
        "- 当前 34 条清单都仍不能在本地直接关单；本轮能做的是结构核验、去歧义和现场执行优化。",
        "",
        "## 本地已核验事实",
        "",
        "- 7 条业务核验项与 enriched P0 工作单一一对应。",
        "- 7 条业务核验项的缺失经营字段与当前工作单保持一致。",
        "- 7 条 P0 路径记录都只有中心点代理步行结果，仍不能替代真实入口或节点路径。",
        "- 27 条节点类清单全部仍属于官方或现场确认范围，当前不能在本地改成已确认入口。",
        "",
        "## 交接细节提醒",
        "",
    ]

    if warning_rows:
        for row in warning_rows:
            lines.append(f"- {row['finding']}")
    else:
        lines.append("- 本轮未发现新的结构性警告项。")

    lines.extend(
        [
            "",
            "## 现场执行建议",
            "",
        ]
    )
    if cluster_rows:
        for row in cluster_rows:
            lines.append(f"- {row['finding']}")
    else:
        lines.append("- 本轮未生成新的节点聚类建议。")

    lines.extend(
        [
            "",
            "## 输出文件",
            "",
            "- `40_quality_evidence/p0_field_verification_checklist_local_review.csv`",
            "- `40_quality_evidence/p0_field_verification_checklist_local_review.md`",
        ]
    )
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    checklist_rows = read_csv(CHECKLIST_CSV)
    worklist_rows = read_csv(WORKLIST_CSV)
    route_rows = read_csv(ROUTE_REVIEW_CSV)
    review_rows = build_review(checklist_rows, worklist_rows, route_rows)
    write_csv(OUT_REVIEW, review_rows, REVIEW_FIELDS)
    write_report(review_rows, checklist_rows, worklist_rows)
    failures = [row for row in review_rows if row["status"] == "fail"]
    warnings = [row for row in review_rows if row["status"] == "warning"]
    print(f"wrote local checklist review rows={len(review_rows)} to {OUT_REVIEW}")
    print(f"wrote report to {OUT_REPORT}")
    print(f"failures={len(failures)} warnings={len(warnings)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()