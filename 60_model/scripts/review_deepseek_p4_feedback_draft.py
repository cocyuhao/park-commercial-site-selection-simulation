from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NODE = ROOT / "70_outputs" / "processed_tables" / "p4_feedback_node_priority_draft_deepseek.csv"
SCENE = ROOT / "70_outputs" / "processed_tables" / "p4_feedback_scenario_matrix_draft_deepseek.csv"
REQUEST = ROOT / "70_outputs" / "processed_tables" / "p4_feedback_data_request_to_partner_deepseek.csv"
OUT = ROOT / "40_quality_evidence" / "deepseek_p4_feedback_draft_review.csv"
OUT_MD = ROOT / "40_quality_evidence" / "deepseek_p4_feedback_draft_review.md"
FIELDS = ["check_id", "status", "severity", "finding", "evidence"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def add(rows: list[dict[str, str]], condition: bool, severity: str, finding: str, evidence: Path) -> None:
    rows.append({"check_id": f"P4-FEEDBACK-REVIEW-{len(rows)+1:03d}", "status": "pass" if condition else "fail", "severity": severity, "finding": finding, "evidence": str(evidence.relative_to(ROOT)).replace("\\", "/")})


def common(rows: list[dict[str, str]], name: str, table: list[dict[str, str]], path: Path) -> None:
    add(rows, Counter(row.get("output_status", "") for row in table) == {"needs_review": len(table)}, "error", f"{name} output_status", path)
    add(rows, Counter(row.get("executor", "") for row in table) == {"deepseek": len(table)}, "error", f"{name} executor", path)
    add(rows, Counter(row.get("llm_task_id", "") for row in table) == {"LLM-025": len(table)}, "error", f"{name} task", path)


def main() -> None:
    rows: list[dict[str, str]] = []
    node = read_csv(NODE)
    scene = read_csv(SCENE)
    request = read_csv(REQUEST)
    add(rows, len(node) == 6, "error", f"node rows={len(node)}", NODE)
    add(rows, len(scene) == 12, "error", f"scenario rows={len(scene)}", SCENE)
    add(rows, len(request) == 12, "error", f"request rows={len(request)}", REQUEST)
    for name, table, path in [("node", node, NODE), ("scene", scene, SCENE), ("request", request, REQUEST)]:
        common(rows, name, table, path)
    add(rows, all(row.get("node_id") for row in node), "error", "node ids are nonempty", NODE)
    add(rows, all("not_final" in row.get("use_boundary", "") or "feedback" in row.get("use_boundary", "") for row in node), "error", "node rows marked feedback/not_final", NODE)
    add(rows, all("placeholder" in row.get("placeholder_inputs_used", "").lower() or "占位" in row.get("placeholder_inputs_used", "") for row in node), "error", "node rows disclose placeholder inputs", NODE)
    node_text = "\n".join(" ".join(row.values()) for row in node)
    forbidden = ["checked", "final_recommendation", "最终推荐"]
    add(rows, not any(token in node_text for token in forbidden), "error", "no final/checked wording in node draft", NODE)
    req_text = "\n".join(" ".join(row.values()) for row in request)
    add(rows, all(token in req_text for token in ["真实客流", "转化率", "运营授权"]), "error", "data requests include core missing inputs", REQUEST)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    failures = [row for row in rows if row["status"] != "pass"]
    OUT_MD.write_text(f"# P4 feedback draft review\n\n- checks: {len(rows)}\n- failures: {len(failures)}\n", encoding="utf-8")
    print(f"review rows={len(rows)}")
    print(f"failures={len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
