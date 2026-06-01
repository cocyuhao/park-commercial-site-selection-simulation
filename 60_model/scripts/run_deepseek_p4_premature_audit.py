from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "60_model" / "src"))

from llm_router import run_deepseek_task  # noqa: E402  # type: ignore[import-not-found]


TASK_ID = "LLM-024"
RAW = ROOT / "60_model" / "llm_runs" / "deepseek_p4_premature_audit_raw.jsonl"
OUT_JSON = ROOT / "40_quality_evidence" / "deepseek_p4_premature_audit.json"
OUT_MD = ROOT / "40_quality_evidence" / "deepseek_p4_premature_audit.md"


def read_text(path: Path, limit: int = 7000) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")[:limit]


def read_csv_sample(path: Path, limit: int = 6) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))[:limit]


def main() -> None:
    context = {
        "p3_gate_status": read_csv_sample(ROOT / "70_outputs" / "processed_tables" / "p3_calibration_gate_status.csv", 10),
        "p4_script_excerpt": read_text(ROOT / "60_model" / "scripts" / "build_p4_full_simulation.py"),
        "p4_summary_excerpt": read_text(ROOT / "p4_completion_summary.md"),
        "p4_ranking_sample": read_csv_sample(ROOT / "70_outputs" / "processed_tables" / "p4_node_scoring_ranking.csv"),
        "p4_detail_sample": read_csv_sample(ROOT / "70_outputs" / "processed_tables" / "p4_simulation_detail_results.csv"),
        "project_boundary": (
            "P3 real calibration gates are not closed. Before P3 closes, P4 may only prepare skeleton/API/tests/config. "
            "P4 must not output full simulation conclusions, ranking, revenue forecast, coordinate/area inference, or final recommendation."
        ),
    }
    messages = [
        {
            "role": "system",
            "content": "You audit project artifacts. Return concise JSON only. All conclusions are needs_review and cannot become checked evidence.",
        },
        {
            "role": "user",
            "content": (
                "Audit whether the externally produced P4 artifacts should be accepted, improved, or rolled back. "
                "Return JSON with fields: decision, reasons (array), boundary_violations (array), data_quality_issues (array), "
                "recommended_action, output_status. Context follows:\n"
                + json.dumps(context, ensure_ascii=False)
            ),
        },
    ]
    content = run_deepseek_task(TASK_ID, messages, temperature=0.1)
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps({"task_id": TASK_ID, "response": content}, ensure_ascii=False) + "\n", encoding="utf-8")
    start = content.find("{")
    end = content.rfind("}")
    payload = json.loads(content[start : end + 1]) if start >= 0 and end > start else {"decision": "rollback", "raw": content}
    decision = str(payload.get("decision", "")).strip().lower().replace("-", "_")
    if decision in {"roll_back", "rollback", "reject", "remove"}:
        payload["decision"] = "rollback"
    payload["output_status"] = "needs_review"
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(
        "\n".join(
            [
                "# DeepSeek P4 premature simulation audit",
                "",
                f"- decision: {payload.get('decision', '')}",
                f"- recommended_action: {payload.get('recommended_action', '')}",
                f"- output_status: {payload.get('output_status', '')}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"decision={payload.get('decision')}")
    print(f"recommended_action={payload.get('recommended_action')}")
    print("output_status=needs_review")


if __name__ == "__main__":
    main()
