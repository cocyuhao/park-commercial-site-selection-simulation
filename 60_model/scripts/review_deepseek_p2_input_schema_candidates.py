from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NODES = ROOT / "70_outputs" / "processed_tables" / "p2_project_node_candidates.csv"
ASSUMPTIONS = ROOT / "70_outputs" / "processed_tables" / "p2_business_scene_assumption_pool.csv"
SPATIAL = ROOT / "70_outputs" / "processed_tables" / "p2_spatial_label_candidates.csv"
GAPS = ROOT / "70_outputs" / "processed_tables" / "p2_input_gap_register.csv"
PROGRESS_JSON = ROOT / "60_model" / "llm_runs" / "deepseek_p2_input_schema_candidates_progress.json"
OUT_REVIEW = ROOT / "40_quality_evidence" / "deepseek_p2_input_schema_candidates_review.csv"
REPORT = ROOT / "40_quality_evidence" / "deepseek_p2_input_schema_candidates_review.md"

FIELDS = ["check_id", "status", "severity", "finding", "evidence"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def ok(condition: bool) -> str:
    return "pass" if condition else "fail"


def add(rows: list[dict[str, str]], status: str, severity: str, finding: str, evidence: str) -> None:
    rows.append(
        {
            "check_id": f"P2-SCHEMA-REVIEW-{len(rows) + 1:03d}",
            "status": status,
            "severity": severity,
            "finding": finding,
            "evidence": evidence,
        }
    )


def all_status(rows: list[dict[str, str]], field: str, value: str) -> bool:
    return all(row.get(field) == value for row in rows)


def main() -> None:
    nodes = read_csv(NODES)
    assumptions = read_csv(ASSUMPTIONS)
    spatial = read_csv(SPATIAL)
    gaps = read_csv(GAPS)
    progress = json.loads(PROGRESS_JSON.read_text(encoding="utf-8-sig")) if PROGRESS_JSON.exists() else {}
    review: list[dict[str, str]] = []

    add(review, ok(len(nodes) == 6), "error", f"node rows={len(nodes)}", str(NODES))
    add(review, ok(len(assumptions) == 12), "error", f"assumption rows={len(assumptions)}", str(ASSUMPTIONS))
    add(review, ok(len(spatial) == 22), "error", f"spatial rows={len(spatial)}", str(SPATIAL))
    add(review, ok(len(gaps) == 10), "error", f"gap rows={len(gaps)}", str(GAPS))
    add(review, ok(all_status(nodes, "output_status", "needs_review")), "error", "all nodes remain needs_review", str(NODES))
    add(review, ok(all_status(assumptions, "output_status", "needs_review")), "error", "all assumptions remain needs_review", str(ASSUMPTIONS))
    add(review, ok(all_status(spatial, "output_status", "needs_review")), "error", "all spatial labels remain needs_review", str(SPATIAL))
    add(review, ok(all_status(gaps, "output_status", "needs_review")), "error", "all gaps remain needs_review", str(GAPS))
    add(review, ok(all_status(spatial, "geometry_status", "pdf_text_label_only_pending_dwg_conversion")), "error", "spatial labels keep pending geometry status", str(SPATIAL))
    add(review, ok(all(row.get("executor") == "deepseek" and row.get("llm_task_id") == "LLM-018" for row in nodes + assumptions + spatial + gaps)), "error", "executor/task id preserved", "all schema tables")

    gap_domains = {row.get("input_domain", "") for row in gaps}
    for required in ["geometry", "visitor_flow", "conversion_rate", "revenue_cost", "operation_authorization", "model_gate"]:
        add(review, ok(required in gap_domains), "error", f"required gap domain present: {required}", str(GAPS))

    node_projects = {row.get("source_project_name", "") for row in nodes}
    add(review, ok(any("桃花源" in item for item in node_projects)), "error", "桃花源 node present", str(NODES))
    add(review, ok(any("南门" in item for item in node_projects)), "error", "南门 node present", str(NODES))
    add(review, ok(any("10#2A03" in item for item in node_projects)), "error", "10#2A03 node present", str(NODES))
    add(review, ok(progress.get("output_status") == "needs_review"), "error", f"progress output_status={progress.get('output_status')}", str(PROGRESS_JSON))

    write_csv(OUT_REVIEW, review)
    status_counts = Counter(row["status"] for row in review)
    REPORT.write_text(
        "\n".join(
            [
                "# DeepSeek P2 输入 schema 候选表本地复核报告",
                "",
                "## 结论",
                "",
                f"- 复核项状态：{dict(sorted(status_counts.items()))}",
                f"- 项目节点候选：{len(nodes)} 条。",
                f"- 业态/场景假设池：{len(assumptions)} 条。",
                f"- 空间标签候选：{len(spatial)} 条。",
                f"- 输入缺口登记：{len(gaps)} 条。",
                "- 所有输出仍为 `needs_review`；空间标签仍为 PDF 文本线索，不含 DWG 几何。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    failures = [row for row in review if row["status"] == "fail"]
    print(f"wrote p2 schema review rows={len(review)} to {OUT_REVIEW}")
    print(f"wrote review report to {REPORT}")
    print(f"failures={len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
