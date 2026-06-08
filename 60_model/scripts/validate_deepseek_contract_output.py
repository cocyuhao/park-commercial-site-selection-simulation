from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

ALLOWED_TASK_TYPES = {
    "source_summary",
    "evidence_candidate",
    "persona_state",
    "behavior_program",
    "choice_probability",
    "simulation_validation_target",
    "node_explanation",
    "report_draft",
    "state_behavior_consistency",
    "micro_reasonableness",
}

ALLOWED_STATUSES = {"draft", "needs_review"}

FORBIDDEN_FINAL_STRINGS = [
    '"output_status": "checked"',
    '"output_status":"checked"',
    '"output_status": "final"',
    '"output_status":"final"',
    "完整仿真已完成",
    "最终排名如下",
    "最终推荐为",
    "最终选址推荐为",
    "收益预测为",
    "投资回收期为",
    "ROI为",
    "ROI 为",
]

TASK_ITEM_REQUIRED_FIELDS: dict[str, set[str]] = {
    "persona_state": {
        "persona_id",
        "segment_name",
        "state_status",
        "purpose",
        "time_pressure",
        "budget_sensitivity",
        "fatigue_level",
        "companion_context",
        "detour_tolerance",
        "queue_tolerance",
        "risk_notes",
        "evidence_refs",
        "missing_inputs",
    },
    "behavior_program": {
        "program_id",
        "persona_id",
        "trigger_context",
        "state_preconditions",
        "candidate_actions",
        "transition_notes",
        "source_refs",
        "validation_needed",
    },
    "choice_probability": {
        "choice_id",
        "project_id",
        "persona_id",
        "program_id",
        "node_id",
        "offer_id",
        "scenario_id",
        "method_family",
        "probability_status",
        "probability_value",
        "priority_label",
        "factor_inputs",
        "plain_language_explanation",
        "specific_advice",
        "source_refs",
        "missing_inputs",
        "user_locked",
    },
    "simulation_validation_target": {
        "target_id",
        "project_id",
        "target_name",
        "validation_level",
        "metric_family",
        "reference_data",
        "candidate_output",
        "acceptance_rule",
        "status",
        "source_refs",
        "missing_inputs",
        "review_notes",
        "user_locked",
    },
    "state_behavior_consistency": {
        "check_id",
        "project_id",
        "persona_id",
        "program_id",
        "scenario_id",
        "state_summary",
        "behavior_summary",
        "evidence_refs",
        "consistency_findings",
        "missing_inputs",
        "output_status",
    },
    "node_explanation": {
        "node_id",
        "mode",
        "priority_label",
        "why_now",
        "specific_advice",
        "evidence_support",
        "evidence_gaps",
        "review_actions",
        "score_if_any",
    },
    "report_draft": {
        "report_type",
        "title",
        "summary",
        "key_basis",
        "current_gaps",
        "review_required",
        "next_actions",
        "appendix_refs",
    },
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def add_failure(failures: list[dict[str, Any]], path: Path, code: str, detail: str) -> None:
    failures.append({"file": str(path), "code": code, "detail": detail})


def expect_list(value: Any, path: Path, failures: list[dict[str, Any]], field: str, *, non_empty: bool = False) -> None:
    if not isinstance(value, list):
        add_failure(failures, path, "field_type", f"{field} must be a list")
        return
    if non_empty and not value:
        add_failure(failures, path, "field_empty", f"{field} must not be empty")


def validate_source_refs(data: dict[str, Any], path: Path, failures: list[dict[str, Any]]) -> None:
    source_refs = data.get("source_refs")
    expect_list(source_refs, path, failures, "source_refs", non_empty=True)
    if not isinstance(source_refs, list):
        return
    for idx, ref in enumerate(source_refs):
        if not isinstance(ref, dict):
            add_failure(failures, path, "source_ref_type", f"source_refs[{idx}] must be an object")
            continue
        for field in ("source_file", "page_or_slide", "quote_or_table_ref"):
            value = ref.get(field)
            if not isinstance(value, str) or not value.strip():
                add_failure(failures, path, "source_ref_missing", f"source_refs[{idx}].{field} is required")


def validate_task_items(data: dict[str, Any], path: Path, failures: list[dict[str, Any]]) -> None:
    task_type = data.get("task_type")
    items = data.get("items")
    expect_list(items, path, failures, "items", non_empty=True)
    if not isinstance(items, list):
        return

    required = TASK_ITEM_REQUIRED_FIELDS.get(str(task_type), set())
    if not required:
        return

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            add_failure(failures, path, "item_type", f"items[{idx}] must be an object")
            continue
        missing = sorted(required - set(item))
        if missing:
            add_failure(failures, path, "item_missing_fields", f"items[{idx}] missing: {', '.join(missing)}")
        if task_type == "node_explanation":
            advice = item.get("specific_advice")
            actions = item.get("review_actions")
            if not isinstance(advice, list) or not advice:
                add_failure(failures, path, "node_advice_missing", "node_explanation requires non-empty specific_advice")
            if not isinstance(actions, list) or not actions:
                add_failure(failures, path, "node_review_actions_missing", "node_explanation requires non-empty review_actions")
            score = item.get("score_if_any")
            if isinstance(score, dict) and score.get("hidden_by_default") is not True:
                add_failure(failures, path, "score_not_hidden", "score_if_any.hidden_by_default must be true")


def validate_contract_file(path: Path) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    try:
        data = load_json(path)
    except Exception as exc:  # noqa: BLE001 - report exact parse failure
        return {
            "file": str(path),
            "passed": False,
            "failures": [{"file": str(path), "code": "json_parse", "detail": str(exc)}],
        }

    if not isinstance(data, dict):
        add_failure(failures, path, "root_type", "root must be an object")
        return {"file": str(path), "passed": False, "failures": failures}

    for field in ("task_id", "task_type", "output_status", "source_refs", "assumptions", "uncertainties", "needs_human_review", "review_required", "items"):
        if field not in data:
            add_failure(failures, path, "missing_field", f"{field} is required")

    task_type = data.get("task_type")
    if task_type not in ALLOWED_TASK_TYPES:
        add_failure(failures, path, "invalid_task_type", f"task_type={task_type!r} is not allowed")

    output_status = data.get("output_status")
    if output_status not in ALLOWED_STATUSES:
        add_failure(failures, path, "invalid_output_status", f"output_status={output_status!r} is not allowed")

    if data.get("needs_human_review") is not True:
        add_failure(failures, path, "review_required", "needs_human_review must be true")
    if data.get("review_required") is not True:
        add_failure(failures, path, "review_required", "review_required must be true")

    expect_list(data.get("assumptions"), path, failures, "assumptions")
    expect_list(data.get("uncertainties"), path, failures, "uncertainties")
    validate_source_refs(data, path, failures)
    validate_task_items(data, path, failures)

    serialized = json.dumps(data, ensure_ascii=False, sort_keys=True)
    for token in FORBIDDEN_FINAL_STRINGS:
        if token in serialized:
            add_failure(failures, path, "forbidden_final_claim", f"forbidden token found: {token}")

    return {"file": str(path), "passed": not failures, "failures": failures}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate DeepSeek draft outputs against local project contract.")
    parser.add_argument("paths", nargs="+", help="JSON files to validate.")
    parser.add_argument("--report", default="", help="Optional report output path.")
    args = parser.parse_args(argv)

    results = [validate_contract_file(Path(raw)) for raw in args.paths]
    report = {
        "validator": "validate_deepseek_contract_output.py",
        "status": "pass" if all(item["passed"] for item in results) else "fail",
        "file_count": len(results),
        "failure_count": sum(len(item["failures"]) for item in results),
        "results": results,
    }

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
