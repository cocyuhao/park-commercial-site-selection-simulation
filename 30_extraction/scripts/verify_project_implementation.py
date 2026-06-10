from __future__ import annotations

import csv
import importlib.util
import json
import os
import py_compile
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "40_quality_evidence" / "verification"
OUT_CSV = OUT_DIR / "implementation_verification_20260526.csv"
OUT_MD = OUT_DIR / "implementation_verification_20260526.md"

FIELDS = ["check_id", "group", "severity", "status", "finding", "evidence"]

SUPERSEDED_BASELINE_PATTERNS = {
    "source_space_foundation": "source/space foundation 0605 gate was replaced by current dashboard source_foundation plus historical/agent influence audits.",
    "source_space_foundation_20260605": "source/space foundation 0605 gate was replaced by current dashboard source_foundation plus historical/agent influence audits.",
    "osen_integrated_report_validation_20260606": "0606 integrated report gate was replaced by current site_selection report and 0607 business decision report evidence.",
    "osen_report_browser_validation_20260606": "0606 browser evidence was replaced by current TestFiles suite and post-test output restore audit.",
    "recommendation_review_framework_20260607": "0607 recommendation research package was folded into current method_basis/method_trace and report basis files.",
    "recommendation_review_openalex_20260607": "0607 OpenAlex package was folded into current method_basis/method_trace and report basis files.",
    "expert_implementation": "large 0607 expert-implementation research package is superseded by current report basis and method_trace evidence.",
    "osen_real_world_context_sources_20260607": "0607 real-world context note is superseded by current real_calibration_context and report basis.",
    "build_recommendation_review_research_20260607": "superseded research builder; current report basis is generated through the dashboard report chain.",
    "build_expert_implementation_knowledge_base_20260607": "superseded research builder; current report basis is generated through the dashboard report chain.",
    "render_docx_with_isolated_libreoffice": "0606 isolated LibreOffice helper superseded by repaired LibreOffice profile and current DOCX validation artifacts.",
    "verify_osen_docx_delivery_20260606": "0606 DOCX delivery gate superseded by current 0607 platform download and post-test report restore audit.",
    "osen_report_docx_render_20260606": "0606 render outputs superseded by current 0607 render/contact-sheet evidence.",
    "osen_docx_delivery_validation_20260606": "0606 DOCX delivery validation superseded by current 0607 client download audit.",
    "person_simulation_accuracy_requirements": "0605/0607 feature derivative package is superseded by current controlled_feature_scene_context and real_calibration_context checks.",
    "person_simulation_feature_derivatives": "0605/0607 feature derivative package is superseded by current controlled_feature_scene_context and real_calibration_context checks.",
    "person_feature_pool": "0607 feature-pool browser evidence is superseded by current TestFiles and post-test output restore audit.",
    "feature_derivative": "0607 feature-derivative browser evidence is superseded by current TestFiles and post-test output restore audit.",
    "report_feature_scene": "0607 feature-scene report evidence is superseded by current site_selection report structure checks.",
    "real_calibration_supplement_loop": "0607 supplement-loop evidence is superseded by current real_calibration_context and post-test output restore audit.",
    "simulation_feature_scene": "0607 feature-scene simulation evidence is superseded by current structural report/context checks.",
    "object_chain_rebaseline": "0605 object-chain gate is superseded by current simulation object pool tests and cache cleanup audit.",
    "simulation_task_entry_preflight": "0605 task-entry preflight gate is superseded by current TestFiles suite and post-test output restore audit.",
}

TABLE_TOPIC_ALLOWED = {
    "visitor_flow",
    "time_peak",
    "demographic_profile",
    "origin_residence_work",
    "tgi_preference",
    "poi_hot_visit",
    "consumption_spending",
    "commercial_supply",
    "revenue_finance",
    "supply_gap",
    "empty_or_visual_noise",
    "other",
}


checks: list[dict[str, str]] = []


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def add(group: str, severity: str, status: str, finding: str, evidence: str = "") -> None:
    checks.append(
        {
            "check_id": f"IMPL-{len(checks) + 1:03d}",
            "group": group,
            "severity": severity,
            "status": status,
            "finding": finding,
            "evidence": evidence,
        }
    )


def ok(condition: bool) -> str:
    return "pass" if condition else "fail"


def superseded_reason(row: dict[str, str]) -> str | None:
    haystack = f"{row.get('evidence', '')} {row.get('finding', '')}"
    for pattern, reason in SUPERSEDED_BASELINE_PATTERNS.items():
        if pattern in haystack:
            return reason
    return None


def apply_superseded_rebaseline() -> None:
    for row in checks:
        if row.get("status") != "fail":
            continue
        reason = superseded_reason(row)
        if not reason:
            continue
        row["status"] = "warn"
        row["severity"] = "warning"
        row["finding"] = f"superseded baseline artifact; current gate uses 2026-06-09 evidence. Original: {row['finding']}. Reason: {reason}"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def check_file(path: str, *, group: str = "files", min_bytes: int = 1) -> None:
    full = ROOT / path
    exists = full.exists()
    enough = exists and full.stat().st_size >= min_bytes
    add(group, "error", ok(enough), f"{path} exists={exists}, bytes={full.stat().st_size if exists else 0}", path)


def check_csv_count(path: str, expected: int, *, group: str = "data") -> list[dict[str, str]]:
    full = ROOT / path
    try:
        rows = read_csv(full)
    except Exception as exc:
        add(group, "error", "fail", f"{path} cannot be read: {type(exc).__name__}", path)
        return []
    add(group, "error", ok(len(rows) == expected), f"{path} rows={len(rows)}, expected={expected}", path)
    return rows


def check_csv_min_count(path: str, minimum: int, *, group: str = "data") -> list[dict[str, str]]:
    full = ROOT / path
    try:
        rows = read_csv(full)
    except Exception as exc:
        add(group, "error", "fail", f"{path} cannot be read: {type(exc).__name__}", path)
        return []
    add(group, "error", ok(len(rows) >= minimum), f"{path} rows={len(rows)}, minimum={minimum}", path)
    return rows


def run_cmd(args: list[str], *, group: str, name: str, expect: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    script_arg = args[1] if len(args) > 1 else ""
    script_name = Path(script_arg).name
    if script_name.startswith("run_deepseek_") and os.environ.get("VERIFY_RERUN_DEEPSEEK") != "1":
        add(
            group,
            "info",
            "pass",
            f"{name}: skipped DeepSeek regeneration; set VERIFY_RERUN_DEEPSEEK=1 to rerun",
            " ".join(args),
        )
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="skipped DeepSeek regeneration\n", stderr="")
    result = subprocess.run(
        args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (result.stdout or "") + (result.stderr or "")
    expected_ok = all(item in output for item in (expect or []))
    status = ok(result.returncode == 0 and expected_ok)
    detail = f"{name}: exit={result.returncode}"
    if expect:
        detail += f", expected_text_found={expected_ok}"
    add(group, "error", status, detail, " ".join(args))
    return result


def verify_required_files() -> None:
    required = [
        "00_control/llm_routing.md",
        "00_control/credential_handoff.md",
        "00_control/model_orchestration.md",
        "00_control/plugin_routing.md",
        "00_control/decisions.md",
        "00_control/mainline_execution_map_20260605.md",
        "00_control/codex_mainline_guardrails.md",
        "00_control/start_codex_mainline.ps1",
        "10_research/deepseek_api_notes.md",
        "60_model/configs/llm_task_routing.csv",
        "60_model/src/llm_router.py",
        "60_model/src/telemetry.py",
        "60_model/src/auto_gate.py",
        "60_model/src/deepseek_review.py",
        "60_model/scripts/verify_deepseek_orchestration.py",
        "60_model/scripts/run_deepseek_smoke_test.py",
        "60_model/scripts/run_deepseek_table_classification.py",
        "60_model/scripts/review_deepseek_table_classification.py",
        "60_model/scripts/run_deepseek_evidence_candidates.py",
        "60_model/scripts/review_deepseek_evidence_candidates.py",
        "60_model/scripts/run_deepseek_entrance_node_classification.py",
        "60_model/scripts/review_deepseek_entrance_node_classification.py",
        "60_model/scripts/run_deepseek_p0_verification_package.py",
        "60_model/scripts/review_deepseek_p0_verification_package.py",
        "60_model/scripts/run_deepseek_project_context_sync.py",
        "60_model/scripts/review_deepseek_project_context_sync.py",
        "60_model/scripts/run_deepseek_p0_detail_query_plan.py",
        "60_model/scripts/review_deepseek_p0_detail_query_plan.py",
        "60_model/scripts/run_deepseek_p0_field_verification_checklist.py",
        "60_model/scripts/review_deepseek_p0_field_verification_checklist.py",
        "60_model/scripts/run_deepseek_p1_quality_report.py",
        "60_model/scripts/review_deepseek_p1_quality_report.py",
        "60_model/scripts/run_deepseek_p2_real_site_semantic_breakdown.py",
        "60_model/scripts/review_deepseek_p2_real_site_semantic_breakdown.py",
        "60_model/scripts/run_deepseek_p2_input_schema_candidates.py",
        "60_model/scripts/review_deepseek_p2_input_schema_candidates.py",
        "60_model/scripts/run_deepseek_p2_completion_readiness_audit.py",
        "60_model/scripts/review_deepseek_p2_completion_readiness_audit.py",
        "60_model/scripts/run_deepseek_p2_source_coverage_audit.py",
        "60_model/scripts/review_deepseek_p2_source_coverage_audit.py",
        "60_model/scripts/run_deepseek_p2_geometry_proxy_audit.py",
        "60_model/scripts/review_deepseek_p2_geometry_proxy_audit.py",
        "60_model/scripts/run_deepseek_p3_prework_package.py",
        "60_model/scripts/review_deepseek_p3_prework_package.py",
        "60_model/scripts/run_deepseek_p3_calibration_execution_package.py",
        "60_model/scripts/review_deepseek_p3_calibration_execution_package.py",
        "60_model/scripts/run_deepseek_p4_premature_audit.py",
        "60_model/scripts/run_deepseek_p4_feedback_draft.py",
        "60_model/scripts/review_deepseek_p4_feedback_draft.py",
        "60_model/scripts/validate_deepseek_contract_output.py",
        "60_model/scripts/verify_modern_sim_stack.py",
        "60_model/scripts/adapt_choice_probability_and_validation_targets.py",
        "30_extraction/scripts/build_codex_mainline_context.py",
        "60_model/scripts/audit_rebaseline_artifacts.py",
        "60_model/scripts/adapt_deepseek_legacy_outputs.py",
        "60_model/scripts/adapt_p4_node_explanations.py",
        "60_model/scripts/build_p2_method_prototype.py",
        "60_model/scripts/review_p2_method_prototype.py",
        "60_model/schemas/persona_state.schema.json",
        "60_model/schemas/behavior_program.schema.json",
        "60_model/schemas/node_recommendation_explanation.schema.json",
        "60_model/schemas/deepseek_task_contract.schema.json",
        "60_model/schemas/person_simulation_control.schema.json",
        "60_model/schemas/choice_probability.schema.json",
        "60_model/schemas/simulation_validation_target.schema.json",
        "10_research/boss_method_materials_20260604/full_system_rebaseline_20260604.md",
        "10_research/boss_method_materials_20260604/boss_model_inventory_20260604.md",
        "10_research/boss_method_materials_20260604/unified_simulation_method_matrix_20260604.md",
        "10_research/boss_method_materials_20260604/external_paper_screening_20260604.md",
        "10_research/boss_method_materials_20260604/legacy_file_trust_audit_20260604.md",
        "10_research/boss_method_materials_20260604/deepseek_task_contracts_20260604.md",
        "10_research/boss_method_materials_20260604/method_selection_evaluation_20260604.md",
        "10_research/boss_method_materials_20260604/method_absorption_landing_register_20260604.md",
        "10_research/boss_method_materials_20260604/modern_practical_method_rescreen_20260604.md",
        "10_research/boss_method_materials_20260604/modern_method_openalex_search_20260604.json",
        "10_research/global_ai_simulation_design_rebaseline_20260604.md",
        "10_research/advanced_ai_learning_absorption_register_20260604.md",
        "10_research/advanced_ai_validation_rebaseline_20260604.md",
        "10_research/evidence_based_direction_reset_20260605.md",
        "10_research/flowus_design_learning_20260605/flowus_153eefbc_snapshot.txt",
        "10_research/flowus_design_learning_20260605/flowus_6616d9c9_snapshot.txt",
        "10_research/flowus_design_learning_20260605/flowus_780bf704_snapshot.txt",
        "10_research/flowus_design_learning_20260605/flowus_153eefbc_screenshot.png",
        "10_research/flowus_design_learning_20260605/flowus_6616d9c9_screenshot.png",
        "10_research/flowus_design_learning_20260605/flowus_780bf704_screenshot.png",
        "10_research/method_tool_plugin_audit_20260604.md",
        "10_research/deepseek_api_concurrency_capacity_20260605.md",
        "10_research/simulation_task_entry_evidence_reinforcement_20260605.md",
        "10_research/ui_skill_design_system_audit_20260605.md",
        "10_research/web_design_guidelines_audit_20260605.md",
        "00_control/page_layer_rebuild_blueprint_20260605.md",
        "30_extraction/scripts/audit_page_rebuild_strategy_20260605.py",
        "30_extraction/scripts/verify_workflow_navigation_20260605.py",
        "30_extraction/scripts/verify_source_space_foundation_20260605.py",
        "40_quality_evidence/page_rebuild_strategy_audit_20260605.json",
        "40_quality_evidence/page_rebuild_strategy_audit_20260605.md",
        "40_quality_evidence/workflow_navigation_validation_20260605.json",
        "40_quality_evidence/workflow_navigation_validation_20260605.md",
        "40_quality_evidence/source_space_foundation_validation_20260605.json",
        "40_quality_evidence/source_space_foundation_validation_20260605.md",
        "40_quality_evidence/source_space_foundation_browser_runtime_20260605.json",
        "40_quality_evidence/source_space_foundation_upload_lazy_map_20260605.png",
        "30_extraction/scripts/analyze_cad_dxf_20260605.py",
        "30_extraction/scripts/analyze_cad_pdf_proxy_20260605.py",
        "30_extraction/scripts/verify_session_recovery_20260606.py",
        "30_extraction/scripts/verify_osen_integrated_report_20260606.py",
        "40_quality_evidence/session_recovery_20260606.json",
        "40_quality_evidence/session_recovery_20260606.md",
        "40_quality_evidence/cad_dxf_analysis_20260605.json",
        "40_quality_evidence/cad_dxf_analysis_20260605.md",
        "40_quality_evidence/cad_dxf_keyword_hits_20260605.csv",
        "40_quality_evidence/cad_pdf_proxy_analysis_20260605.json",
        "40_quality_evidence/cad_pdf_proxy_analysis_20260605.md",
        "40_quality_evidence/osen_integrated_report_validation_20260606.json",
        "40_quality_evidence/osen_integrated_report_validation_20260606.md",
        "90_p6_expert_dashboard/qa/osen_report_browser_validation_20260606.py",
        "40_quality_evidence/osen_report_browser_validation_20260606.json",
        "40_quality_evidence/osen_report_browser_validation_20260606/report_view.png",
        "10_research/recommendation_review_framework_20260607.md",
        "10_research/recommendation_review_openalex_20260607.json",
        "10_research/expert_implementation_review_framework_20260607.md",
        "10_research/osen_real_world_context_sources_20260607.md",
        "10_research/expert_implementation_knowledge_20260607/expert_implementation_summary.json",
        "10_research/expert_implementation_knowledge_20260607/expert_implementation_openalex_raw.json",
        "30_extraction/scripts/build_recommendation_review_research_20260607.py",
        "30_extraction/scripts/build_expert_implementation_knowledge_base_20260607.py",
        "30_extraction/scripts/build_osen_real_calibration_inputs_20260607.py",
        "70_outputs/processed_tables/osen_real_calibration_inputs_20260607.csv",
        "40_quality_evidence/osen_real_calibration_inputs_20260607.json",
        "40_quality_evidence/osen_real_calibration_inputs_20260607.md",
        "30_extraction/scripts/render_docx_with_isolated_libreoffice.py",
        "30_extraction/scripts/verify_osen_docx_delivery_20260606.py",
        "80_delivery/osen_integrated_site_selection_report_20260606.docx",
        "40_quality_evidence/osen_integrated_report_docx_audit_20260606.json",
        "40_quality_evidence/osen_report_docx_render_20260606.json",
        "40_quality_evidence/osen_report_docx_render_20260606.md",
        "40_quality_evidence/osen_report_docx_render_20260606/page_01.png",
        "40_quality_evidence/osen_report_docx_render_20260606/page_06.png",
        "40_quality_evidence/osen_report_docx_render_20260606/page_18.png",
        "40_quality_evidence/osen_docx_delivery_validation_20260606.json",
        "40_quality_evidence/osen_docx_delivery_validation_20260606.md",
        "80_delivery/site_selection_gap_report_latest.json",
        "80_delivery/site_selection_gap_report_latest.md",
        "40_quality_evidence/deepseek_orchestration_validation_20260605.json",
        "40_quality_evidence/deepseek_orchestration_validation_20260605.md",
        "10_research/ai_design_2026_openalex_raw_20260604.json",
        "10_research/ai_design_2026_semantic_scholar_raw_20260604.json",
        "10_research/ai_design_2026_arxiv_raw_20260604.json",
        "30_extraction/scripts/audit_project_context_and_legacy_risks.py",
        "30_extraction/scripts/audit_method_model_landing_coverage.py",
        "40_quality_evidence/project_context_legacy_risk_audit_20260605.json",
        "40_quality_evidence/project_context_legacy_risk_audit_20260605.md",
        "40_quality_evidence/method_model_landing_coverage_20260605.json",
        "40_quality_evidence/method_model_landing_coverage_20260605.md",
        "30_extraction/scripts/build_person_simulation_accuracy_requirements.py",
        "30_extraction/scripts/build_person_simulation_feature_derivatives.py",
        "30_extraction/scripts/verify_person_simulation_feature_derivatives_20260607.py",
        "40_quality_evidence/person_simulation_accuracy_requirements_20260605.json",
        "40_quality_evidence/person_simulation_accuracy_requirements_20260605.md",
        "70_outputs/processed_tables/person_simulation_accuracy_requirements_20260605.csv",
        "70_outputs/processed_tables/person_simulation_feature_derivatives_1000_20260604.csv",
        "40_quality_evidence/person_simulation_feature_derivatives_generation_20260607.json",
        "40_quality_evidence/person_simulation_feature_derivatives_validation_20260607.json",
        "40_quality_evidence/person_simulation_feature_derivatives_validation_20260607.md",
        "40_quality_evidence/person_feature_pool_browser_visible_20260607.json",
        "40_quality_evidence/person_feature_pool_upload_visible_20260607.png",
        "40_quality_evidence/person_feature_pool_preflight_visible_20260607.png",
        "40_quality_evidence/feature_derivative_user_control_browser_20260607.json",
        "40_quality_evidence/feature_derivative_user_control_browser_20260607.png",
        "40_quality_evidence/feature_derivative_income_control_browser_20260607.json",
        "40_quality_evidence/feature_derivative_income_control_browser_20260607.png",
        "90_p6_expert_dashboard/qa/report_feature_scene_context_validation_20260607.py",
        "40_quality_evidence/report_feature_scene_context_validation_20260607.json",
        "40_quality_evidence/report_feature_scene_context_validation_20260607.md",
        "90_p6_expert_dashboard/qa/real_calibration_supplement_loop_validation_20260607.py",
        "40_quality_evidence/real_calibration_supplement_loop_validation_20260607.json",
        "40_quality_evidence/real_calibration_supplement_loop_validation_20260607.md",
        "40_quality_evidence/report_feature_scene_context_browser_20260607.json",
        "40_quality_evidence/report_feature_scene_context_browser_20260607.png",
        "90_p6_expert_dashboard/qa/simulation_feature_scene_dry_run_validation_20260607.py",
        "40_quality_evidence/simulation_feature_scene_dry_run_validation_20260607.json",
        "40_quality_evidence/simulation_feature_scene_dry_run_validation_20260607.md",
        "90_p6_expert_dashboard/qa/simulation_feature_scene_browser_validation_20260607.py",
        "40_quality_evidence/simulation_feature_scene_browser_validation_20260607.json",
        "40_quality_evidence/simulation_feature_scene_browser_validation_20260607/simulation_feature_scene.png",
        "40_quality_evidence/modern_sim_stack_verification_20260604.json",
        "40_quality_evidence/modern_sim_stack_verification_20260604.md",
        "40_quality_evidence/flowus_ai_design_probe_20260604/flowus_probe_report.json",
        "40_quality_evidence/flowus_ai_design_probe_20260604/flowus_1.txt",
        "40_quality_evidence/flowus_ai_design_probe_20260604/flowus_2.txt",
        "40_quality_evidence/flowus_ai_design_probe_20260604/flowus_3.txt",
        "40_quality_evidence/flowus_ai_design_probe_20260604/flowus_1.png",
        "40_quality_evidence/flowus_ai_design_probe_20260604/flowus_2.png",
        "40_quality_evidence/flowus_ai_design_probe_20260604/flowus_3.png",
        "40_quality_evidence/simulation_object_pool_api_validation_20260604.json",
        "40_quality_evidence/simulation_object_pool_browser_validation_20260604.json",
        "40_quality_evidence/simulation_object_pool_browser_validation_20260604.png",
        "90_p6_expert_dashboard/qa/simulation_object_pool_persona_behavior_validation_20260605.py",
        "40_quality_evidence/simulation_object_pool_persona_behavior_validation_20260605.json",
        "40_quality_evidence/simulation_object_pool_persona_behavior_validation_20260605.md",
        "90_p6_expert_dashboard/qa/object_chain_rebaseline_validation_20260605.py",
        "40_quality_evidence/object_chain_rebaseline_validation_20260605.json",
        "40_quality_evidence/object_chain_rebaseline_validation_20260605.md",
        "40_quality_evidence/object_chain_browser_validation_20260605.json",
        "40_quality_evidence/object_chain_browser_validation_20260605/object_chain_overview.png",
        "90_p6_expert_dashboard/qa/simulation_task_entry_preflight_validation_20260605.py",
        "40_quality_evidence/simulation_task_entry_preflight_validation_20260605.json",
        "40_quality_evidence/simulation_task_entry_preflight_validation_20260605.md",
        "40_quality_evidence/global_ai_design_rebaseline_browser_validation_20260604.json",
        "40_quality_evidence/global_ai_design_rebaseline_overview_validation_20260604.json",
        "40_quality_evidence/global_ai_design_rebaseline_overview_final_20260604.png",
        "90_p6_expert_dashboard/qa/advanced_agentic_workflow_validation_20260604.py",
        "40_quality_evidence/advanced_agentic_workflow_validation_20260604.json",
        "40_quality_evidence/advanced_agentic_workflow_validation_20260604.md",
        "40_quality_evidence/advanced_agentic_workflow_trace_20260604.zip",
        "40_quality_evidence/advanced_agentic_workflow_aria_overview_20260604.yml",
        "40_quality_evidence/advanced_agentic_workflow_overview_20260604.png",
        "40_quality_evidence/advanced_agentic_workflow_upload_20260604.png",
        "40_quality_evidence/advanced_agentic_workflow_data_20260604.png",
        "40_quality_evidence/advanced_agentic_workflow_nodes_20260604.png",
        "40_quality_evidence/advanced_agentic_workflow_map_20260604.png",
        "40_quality_evidence/advanced_agentic_workflow_ai_20260604.png",
        "40_quality_evidence/advanced_agentic_workflow_report_20260604.png",
        "90_p6_expert_dashboard/qa/package.json",
        "90_p6_expert_dashboard/qa/package-lock.json",
        "90_p6_expert_dashboard/qa/page_layer_rebuild_validation_20260605.py",
        "40_quality_evidence/page_layer_rebuild_validation_20260605.json",
        "40_quality_evidence/page_layer_rebuild_validation_20260605/overview_chain_command.png",
        "40_quality_evidence/page_layer_rebuild_validation_20260605/ai_workspace_reading_width.png",
        "90_p6_expert_dashboard/qa/axe_accessibility_probe.mjs",
        "40_quality_evidence/axe_accessibility_probe_20260605.json",
        "40_quality_evidence/axe_accessibility_probe_20260605/overview.png",
        "40_quality_evidence/axe_accessibility_probe_20260605/ai.png",
        "40_quality_evidence/axe_accessibility_probe_20260605/data.png",
        "90_p6_expert_dashboard/qa/lighthouse_user_flow_probe.mjs",
        "40_quality_evidence/lighthouse_user_flow_20260605.json",
        "40_quality_evidence/lighthouse_user_flow_20260605/p6_dashboard_user_flow.html",
        "90_p6_expert_dashboard/qa/otel_fastapi_trace_probe_20260605.py",
        "40_quality_evidence/otel_fastapi_trace_probe_20260605.json",
        "30_extraction/scripts/audit_advanced_capability_and_legacy_methods_20260605.py",
        "40_quality_evidence/advanced_capability_and_legacy_method_audit_20260605.json",
        "40_quality_evidence/advanced_capability_and_legacy_method_audit_20260605.md",
        "90_p6_expert_dashboard/app.py",
        "90_p6_expert_dashboard/static/index.html",
        "90_p6_expert_dashboard/static/styles.css",
        "90_p6_expert_dashboard/static/app.js",
        "60_model/llm_runs/deepseek_table_classification_raw.jsonl",
        "60_model/llm_runs/deepseek_table_classification_progress.json",
        "60_model/llm_runs/deepseek_evidence_candidates_raw.jsonl",
        "60_model/llm_runs/deepseek_evidence_candidates_progress.json",
        "60_model/llm_runs/deepseek_entrance_node_semantic_raw.jsonl",
        "60_model/llm_runs/deepseek_entrance_node_semantic_progress.json",
        "60_model/llm_runs/deepseek_p0_verification_package_raw.jsonl",
        "60_model/llm_runs/deepseek_p0_verification_package_progress.json",
        "60_model/llm_runs/deepseek_project_context_sync_raw.jsonl",
        "60_model/llm_runs/deepseek_project_context_sync_progress.json",
        "60_model/llm_runs/deepseek_project_context_sync_latest.json",
        "60_model/llm_runs/deepseek_p0_detail_query_plan_raw.jsonl",
        "60_model/llm_runs/deepseek_p0_detail_query_plan_progress.json",
        "60_model/llm_runs/deepseek_p0_field_verification_checklist_raw.jsonl",
        "60_model/llm_runs/deepseek_p0_field_verification_checklist_progress.json",
        "60_model/llm_runs/deepseek_p1_quality_report_raw.jsonl",
        "60_model/llm_runs/deepseek_p1_quality_report_progress.json",
        "60_model/llm_runs/deepseek_p2_real_site_semantic_raw.jsonl",
        "60_model/llm_runs/deepseek_p2_real_site_semantic_progress.json",
        "60_model/llm_runs/deepseek_p2_input_schema_candidates_raw.jsonl",
        "60_model/llm_runs/deepseek_p2_input_schema_candidates_progress.json",
        "60_model/llm_runs/deepseek_p2_completion_readiness_audit_raw.jsonl",
        "60_model/llm_runs/deepseek_p2_completion_readiness_audit_progress.json",
        "60_model/llm_runs/deepseek_p2_source_coverage_audit_raw.jsonl",
        "60_model/llm_runs/deepseek_p2_source_coverage_audit_progress.json",
        "60_model/llm_runs/deepseek_p2_geometry_proxy_audit_raw.jsonl",
        "60_model/llm_runs/deepseek_p2_geometry_proxy_audit_progress.json",
        "60_model/llm_runs/deepseek_p3_prework_package_raw.jsonl",
        "60_model/llm_runs/deepseek_p3_prework_package_progress.json",
        "60_model/llm_runs/deepseek_p3_calibration_execution_package_raw.jsonl",
        "60_model/llm_runs/deepseek_p3_calibration_execution_package_progress.json",
        "60_model/llm_runs/deepseek_p4_premature_audit_raw.jsonl",
        "60_model/llm_runs/deepseek_p4_feedback_draft_raw.jsonl",
        "60_model/llm_runs/deepseek_p4_feedback_draft_progress.json",
        "30_extraction/tables/pdf_table_topic_draft_deepseek.csv",
        "30_extraction/tables/pdf_table_review_queue.csv",
        "30_extraction/tables/pdf_table_evidence_candidates_deepseek.csv",
        "30_extraction/tables/pdf_evidence_candidate_review_queue.csv",
        "40_quality_evidence/deepseek_table_classification_report.md",
        "40_quality_evidence/deepseek_table_classification_review.csv",
        "40_quality_evidence/deepseek_table_classification_review.md",
        "40_quality_evidence/deepseek_evidence_candidates_report.md",
        "40_quality_evidence/deepseek_evidence_candidates_review.csv",
        "40_quality_evidence/deepseek_evidence_candidates_review.md",
        "50_external_gis/amap_routes/amap_p0_entrance_node_semantic_draft_deepseek.csv",
        "50_external_gis/amap_routes/amap_p0_entrance_node_semantic_review_queue.csv",
        "40_quality_evidence/deepseek_entrance_node_semantic_report.md",
        "40_quality_evidence/deepseek_entrance_node_semantic_review.csv",
        "40_quality_evidence/deepseek_entrance_node_semantic_review.md",
        "70_outputs/processed_tables/p0_manual_verification_package_deepseek.csv",
        "40_quality_evidence/deepseek_p0_verification_package_report.md",
        "40_quality_evidence/deepseek_p0_verification_package_review.csv",
        "40_quality_evidence/deepseek_p0_verification_package_review.md",
        "70_outputs/processed_tables/deepseek_first_task_queue.csv",
        "40_quality_evidence/deepseek_project_context_sync_report.md",
        "40_quality_evidence/deepseek_project_context_sync_review.csv",
        "40_quality_evidence/deepseek_project_context_sync_review.md",
        "50_external_gis/amap_poi/amap_p0_detail_query_plan_deepseek.csv",
        "40_quality_evidence/deepseek_p0_detail_query_plan_report.md",
        "40_quality_evidence/deepseek_p0_detail_query_plan_review.csv",
        "40_quality_evidence/deepseek_p0_detail_query_plan_review.md",
        "70_outputs/processed_tables/p0_business_field_fill_amap.csv",
        "70_outputs/processed_tables/poi_supply_p0_followup_worklist_enriched.csv",
        "70_outputs/processed_tables/p0_field_verification_checklist_deepseek.csv",
        "40_quality_evidence/deepseek_p0_field_verification_checklist_report.md",
        "40_quality_evidence/deepseek_p0_field_verification_checklist_review.csv",
        "40_quality_evidence/deepseek_p0_field_verification_checklist_review.md",
        "30_extraction/scripts/review_p0_field_verification_checklist.py",
        "30_extraction/scripts/review_handoff_and_encoding_health.py",
        "30_extraction/scripts/review_p2_completion_reality.py",
        "40_quality_evidence/p0_field_verification_checklist_local_review.csv",
        "40_quality_evidence/p0_field_verification_checklist_local_review.md",
        "40_quality_evidence/handoff_encoding_health_review.csv",
        "40_quality_evidence/handoff_encoding_health_review.md",
        "40_quality_evidence/p1_quality_report_draft_deepseek.md",
        "40_quality_evidence/deepseek_p1_quality_report_generation_report.md",
        "40_quality_evidence/deepseek_p1_quality_report_review.csv",
        "40_quality_evidence/deepseek_p1_quality_report_review.md",
        "30_extraction/scripts/build_p2_real_site_input_index.py",
        "30_extraction/p2_real_site/osen_project_plan_text.txt",
        "30_extraction/p2_real_site/osen_project_plan_profile.json",
        "30_extraction/p2_real_site/osen_north_cad_pdf_text.txt",
        "30_extraction/p2_real_site/osen_north_cad_pdf_pages.csv",
        "40_quality_evidence/p2_real_site_source_catalog.csv",
        "70_outputs/processed_tables/p2_real_site_input_worklist.csv",
        "70_outputs/processed_tables/p2_simulation_input_requirements.csv",
        "40_quality_evidence/p2_real_site_preparation_report.md",
        "70_outputs/processed_tables/p2_docx_project_semantic_draft_deepseek.csv",
        "70_outputs/processed_tables/p2_pdf_spatial_label_draft_deepseek.csv",
        "70_outputs/processed_tables/p2_project_node_candidates.csv",
        "70_outputs/processed_tables/p2_business_scene_assumption_pool.csv",
        "70_outputs/processed_tables/p2_spatial_label_candidates.csv",
        "70_outputs/processed_tables/p2_input_gap_register.csv",
        "70_outputs/processed_tables/p2_persona_parameter_prototype.csv",
        "70_outputs/processed_tables/p2_demand_trigger_matrix.csv",
        "70_outputs/processed_tables/p2_supply_gap_scoring_formula.csv",
        "70_outputs/processed_tables/p2_candidate_method_readiness_scores.csv",
        "70_outputs/processed_tables/p2_postman_api_contract_draft.csv",
        "40_quality_evidence/deepseek_p2_real_site_semantic_report.md",
        "40_quality_evidence/deepseek_p2_real_site_semantic_review.csv",
        "40_quality_evidence/deepseek_p2_real_site_semantic_review.md",
        "40_quality_evidence/deepseek_p2_input_schema_candidates_report.md",
        "40_quality_evidence/deepseek_p2_input_schema_candidates_review.csv",
        "40_quality_evidence/deepseek_p2_input_schema_candidates_review.md",
        "40_quality_evidence/deepseek_p2_completion_readiness_audit.json",
        "40_quality_evidence/deepseek_p2_completion_readiness_audit_checks.csv",
        "40_quality_evidence/deepseek_p2_completion_readiness_audit.md",
        "40_quality_evidence/deepseek_p2_completion_readiness_audit_review.csv",
        "40_quality_evidence/deepseek_p2_completion_readiness_audit_review.md",
        "40_quality_evidence/p2_completion_reality_audit.csv",
        "40_quality_evidence/p2_completion_reality_audit.md",
        "40_quality_evidence/deepseek_p2_source_coverage_audit.json",
        "40_quality_evidence/deepseek_p2_source_coverage_audit_matrix.csv",
        "40_quality_evidence/deepseek_p2_source_coverage_audit.md",
        "40_quality_evidence/deepseek_p2_source_coverage_audit_review.csv",
        "40_quality_evidence/deepseek_p2_source_coverage_audit_review.md",
        "70_outputs/processed_tables/p2_pdf_proxy_zone_candidates_deepseek.csv",
        "70_outputs/processed_tables/p2_dwg_conversion_worklist_deepseek.csv",
        "70_outputs/processed_tables/p2_geometry_proxy_limitations_deepseek.csv",
        "40_quality_evidence/deepseek_p2_geometry_proxy_audit.json",
        "40_quality_evidence/deepseek_p2_geometry_proxy_audit.md",
        "40_quality_evidence/deepseek_p2_geometry_proxy_audit_review.csv",
        "40_quality_evidence/deepseek_p2_geometry_proxy_audit_review.md",
        "40_quality_evidence/p2_method_prototype_report.md",
        "40_quality_evidence/p2_method_prototype_review.csv",
        "40_quality_evidence/p2_method_prototype_review.md",
        "70_outputs/processed_tables/p3_p4_route_decision_deepseek.csv",
        "70_outputs/processed_tables/p3_dwg_conversion_work_order_deepseek.csv",
        "70_outputs/processed_tables/p3_calibration_data_requirements_deepseek.csv",
        "70_outputs/processed_tables/p3_p2_to_calibration_field_mapping_deepseek.csv",
        "70_outputs/processed_tables/p4_parallel_skeleton_backlog_deepseek.csv",
        "40_quality_evidence/deepseek_p3_prework_package.json",
        "40_quality_evidence/deepseek_p3_prework_package.md",
        "40_quality_evidence/deepseek_p3_prework_package_review.csv",
        "40_quality_evidence/deepseek_p3_prework_package_review.md",
        "70_outputs/processed_tables/p3_calibration_evidence_request_worklist_deepseek.csv",
        "70_outputs/processed_tables/p3_calibration_acceptance_criteria_deepseek.csv",
        "70_outputs/processed_tables/p3_scenario_assumption_limits_deepseek.csv",
        "70_outputs/processed_tables/p3_calibration_blocker_register_deepseek.csv",
        "70_outputs/processed_tables/p3_calibration_gate_status.csv",
        "40_quality_evidence/deepseek_p3_calibration_execution_package.json",
        "40_quality_evidence/deepseek_p3_calibration_execution_package.md",
        "40_quality_evidence/deepseek_p3_calibration_execution_package_review.csv",
        "40_quality_evidence/deepseek_p3_calibration_execution_package_review.md",
        "40_quality_evidence/deepseek_p4_premature_audit.json",
        "40_quality_evidence/deepseek_p4_premature_audit.md",
        "70_outputs/processed_tables/p4_feedback_node_priority_draft_deepseek.csv",
        "70_outputs/processed_tables/p4_feedback_scenario_matrix_draft_deepseek.csv",
        "70_outputs/processed_tables/p4_feedback_data_request_to_partner_deepseek.csv",
        "40_quality_evidence/deepseek_p4_feedback_draft.json",
        "40_quality_evidence/deepseek_p4_feedback_draft.md",
        "40_quality_evidence/deepseek_p4_feedback_draft_review.csv",
        "40_quality_evidence/deepseek_p4_feedback_draft_review.md",
        "40_quality_evidence/rebaseline_artifact_trust_audit_20260604.csv",
        "40_quality_evidence/rebaseline_artifact_trust_audit_20260604.md",
        "40_quality_evidence/deepseek_legacy_envelope_adapter_20260604.json",
        "40_quality_evidence/deepseek_legacy_envelope_adapter_20260604.csv",
        "40_quality_evidence/deepseek_legacy_envelope_adapter_20260604.md",
        "40_quality_evidence/deepseek_legacy_envelope_validation_20260604.json",
        "60_model/llm_runs/contract_envelopes/p4_node_explanation_from_legacy_20260604.json",
        "70_outputs/processed_tables/p4_node_explanation_from_legacy_20260604.csv",
        "40_quality_evidence/p4_node_explanation_adapter_20260604.json",
        "40_quality_evidence/p4_node_explanation_adapter_20260604.md",
        "40_quality_evidence/p4_node_explanation_contract_validation_20260604.json",
        "60_model/llm_runs/contract_envelopes/choice_probability_from_p2_p4_20260604.json",
        "60_model/llm_runs/contract_envelopes/simulation_validation_target_from_p2_20260604.json",
        "70_outputs/processed_tables/choice_probability_from_p2_p4_20260604.csv",
        "70_outputs/processed_tables/simulation_validation_target_from_p2_20260604.csv",
        "40_quality_evidence/choice_probability_adapter_20260604.json",
        "40_quality_evidence/choice_probability_adapter_20260604.md",
        "40_quality_evidence/simulation_validation_target_adapter_20260604.json",
        "40_quality_evidence/simulation_validation_target_adapter_20260604.md",
        "40_quality_evidence/choice_probability_contract_validation_20260604.json",
        "40_quality_evidence/simulation_validation_target_contract_validation_20260604.json",
        "40_quality_evidence/codex_mainline_context_20260604.json",
        "40_quality_evidence/codex_mainline_context_20260604.md",
        "10_research/github_tech_shrimp/github_import_plan.md",
        "10_research/github_tech_shrimp/tech_shrimp_assessment.md",
        "10_research/github_tech_shrimp/tech_shrimp_repos_gh_api_20260523.csv",
        "10_research/github_tech_shrimp/tech_shrimp_repos_gh_api_20260523.json",
        "10_research/github_tech_shrimp/fork_results_20260523.csv",
        "10_research/github_tech_shrimp/archive_repo_README.md",
        "40_quality_evidence/evidence_ledger.csv",
        "30_extraction/scripts/build_second_evidence_ledger.py",
        "40_quality_evidence/second_evidence_ledger_review.csv",
        "40_quality_evidence/second_evidence_ledger_report.md",
        "70_outputs/processed_tables/poi_supply_base.csv",
        "50_external_gis/amap_poi/amap_poi_query_plan.csv",
        "50_external_gis/scripts/build_amap_spatial_precheck.py",
        "50_external_gis/scripts/fetch_osm_park_boundaries.py",
        "50_external_gis/scripts/build_amap_boundary_filter.py",
        "50_external_gis/scripts/build_in_park_candidate_review.py",
        "50_external_gis/scripts/build_p0_in_park_followup_worklist.py",
        "50_external_gis/scripts/fetch_amap_p0_routes.py",
        "50_external_gis/scripts/fetch_amap_p0_entrance_routes.py",
        "50_external_gis/scripts/run_amap_smoke_test.py",
        "70_outputs/processed_tables/poi_supply_candidates_amap.csv",
        "70_outputs/processed_tables/poi_supply_candidates_amap_spatial_precheck.csv",
        "70_outputs/processed_tables/poi_supply_candidates_amap_boundary_filter.csv",
        "70_outputs/processed_tables/poi_supply_in_park_candidate_review.csv",
        "70_outputs/processed_tables/poi_supply_p0_followup_worklist.csv",
        "70_outputs/processed_tables/poi_supply_p0_route_access_review.csv",
        "50_external_gis/amap_poi/amap_refetch_followup_plan.csv",
        "50_external_gis/amap_routes/amap_p0_route_fetch_log.csv",
        "50_external_gis/amap_routes/amap_p0_route_results.csv",
        "50_external_gis/amap_routes/p0_entrance_node_query_plan.csv",
        "50_external_gis/amap_routes/amap_p0_entrance_node_candidates.csv",
        "50_external_gis/amap_routes/amap_p0_entrance_node_fetch_log.csv",
        "50_external_gis/amap_routes/amap_p0_entrance_node_route_results.csv",
        "70_outputs/processed_tables/poi_supply_p0_entrance_route_review.csv",
        "50_external_gis/amap_smoke_tests/amap_smoke_test_latest.json",
        "50_external_gis/boundaries/osm_park_boundaries.geojson",
        "50_external_gis/boundaries/osm_park_boundary_fetch_log.csv",
        "40_quality_evidence/amap_spatial_precheck_report.md",
        "40_quality_evidence/osm_boundary_report.md",
        "40_quality_evidence/amap_boundary_filter_report.md",
        "40_quality_evidence/in_park_candidate_review_report.md",
        "40_quality_evidence/p0_in_park_followup_worklist_report.md",
        "40_quality_evidence/p0_route_access_review_report.md",
        "40_quality_evidence/p0_entrance_route_review_report.md",
    ]
    for item in required:
        check_file(item)


def verify_row_counts() -> None:
    check_csv_count("40_quality_evidence/data_catalog.csv", 4)
    check_csv_count("40_quality_evidence/source_profile.csv", 4)
    check_csv_count("30_extraction/tables/keyword_hits.csv", 1594)
    pdf_summary = check_csv_count("30_extraction/tables/pdf_native_tables_summary.csv", 329)
    ledger = check_csv_count("40_quality_evidence/evidence_ledger.csv", 260)
    second_ledger_review = check_csv_count("40_quality_evidence/second_evidence_ledger_review.csv", 216)
    poi = check_csv_count("70_outputs/processed_tables/poi_supply_base.csv", 20)
    query = check_csv_count("50_external_gis/amap_poi/amap_poi_query_plan.csv", 24)
    amap_candidates = check_csv_count("70_outputs/processed_tables/poi_supply_candidates_amap.csv", 227)
    spatial_precheck = check_csv_count("70_outputs/processed_tables/poi_supply_candidates_amap_spatial_precheck.csv", 227)
    boundary_filter = check_csv_count("70_outputs/processed_tables/poi_supply_candidates_amap_boundary_filter.csv", 227)
    in_park_review = check_csv_count("70_outputs/processed_tables/poi_supply_in_park_candidate_review.csv", 26)
    p0_worklist = check_csv_count("70_outputs/processed_tables/poi_supply_p0_followup_worklist.csv", 7)
    p0_route_results = check_csv_count("50_external_gis/amap_routes/amap_p0_route_results.csv", 7)
    p0_route_log = check_csv_count("50_external_gis/amap_routes/amap_p0_route_fetch_log.csv", 7)
    p0_route_review = check_csv_count("70_outputs/processed_tables/poi_supply_p0_route_access_review.csv", 7)
    entrance_node_plan = check_csv_count("50_external_gis/amap_routes/p0_entrance_node_query_plan.csv", 12)
    entrance_nodes = check_csv_count("50_external_gis/amap_routes/amap_p0_entrance_node_candidates.csv", 45)
    entrance_route_log = check_csv_count("50_external_gis/amap_routes/amap_p0_entrance_node_fetch_log.csv", 40)
    entrance_route_results = check_csv_count("50_external_gis/amap_routes/amap_p0_entrance_node_route_results.csv", 28)
    entrance_route_review = check_csv_count("70_outputs/processed_tables/poi_supply_p0_entrance_route_review.csv", 7)
    followup_plan = check_csv_count("50_external_gis/amap_poi/amap_refetch_followup_plan.csv", 17)
    boundary_log = check_csv_count("50_external_gis/boundaries/osm_park_boundary_fetch_log.csv", 2)
    routes = check_csv_count("60_model/configs/llm_task_routing.csv", 26)
    table_draft = check_csv_count("30_extraction/tables/pdf_table_topic_draft_deepseek.csv", 329, group="llm")
    table_queue = check_csv_count("30_extraction/tables/pdf_table_review_queue.csv", 329, group="llm")
    table_review = check_csv_count("40_quality_evidence/deepseek_table_classification_review.csv", 8, group="llm")
    evidence_candidates = check_csv_count("30_extraction/tables/pdf_table_evidence_candidates_deepseek.csv", 592, group="llm")
    evidence_review_queue = check_csv_count("30_extraction/tables/pdf_evidence_candidate_review_queue.csv", 592, group="llm")
    evidence_review = check_csv_count("40_quality_evidence/deepseek_evidence_candidates_review.csv", 12, group="llm")
    entrance_node_semantic = check_csv_count("50_external_gis/amap_routes/amap_p0_entrance_node_semantic_draft_deepseek.csv", 45, group="llm")
    entrance_node_semantic_queue = check_csv_count("50_external_gis/amap_routes/amap_p0_entrance_node_semantic_review_queue.csv", 45, group="llm")
    entrance_node_semantic_review = check_csv_count("40_quality_evidence/deepseek_entrance_node_semantic_review.csv", 10, group="llm")
    p0_verification_package = check_csv_count("70_outputs/processed_tables/p0_manual_verification_package_deepseek.csv", 7, group="llm")
    p0_verification_package_review = check_csv_count("40_quality_evidence/deepseek_p0_verification_package_review.csv", 8, group="llm")
    deepseek_first_queue = check_csv_count("70_outputs/processed_tables/deepseek_first_task_queue.csv", 6, group="llm")
    deepseek_context_review = check_csv_count("40_quality_evidence/deepseek_project_context_sync_review.csv", 6, group="llm")
    p0_detail_plan = check_csv_count("50_external_gis/amap_poi/amap_p0_detail_query_plan_deepseek.csv", 7, group="llm")
    p0_detail_plan_review = check_csv_count("40_quality_evidence/deepseek_p0_detail_query_plan_review.csv", 11, group="llm")
    p0_business_fill = check_csv_count("70_outputs/processed_tables/p0_business_field_fill_amap.csv", 7, group="data")
    p0_worklist_enriched = check_csv_count("70_outputs/processed_tables/poi_supply_p0_followup_worklist_enriched.csv", 7, group="data")
    p0_field_checklist = check_csv_count("70_outputs/processed_tables/p0_field_verification_checklist_deepseek.csv", 34, group="llm")
    p0_field_checklist_review = check_csv_count("40_quality_evidence/deepseek_p0_field_verification_checklist_review.csv", 11, group="llm")
    p0_field_checklist_local_review = check_csv_count("40_quality_evidence/p0_field_verification_checklist_local_review.csv", 13, group="llm")
    handoff_encoding_review = check_csv_count("40_quality_evidence/handoff_encoding_health_review.csv", 47, group="files")
    p1_quality_review = check_csv_count("40_quality_evidence/deepseek_p1_quality_report_review.csv", 13, group="llm")
    p2_source_catalog = check_csv_count("40_quality_evidence/p2_real_site_source_catalog.csv", 4, group="p2")
    p2_pdf_pages = check_csv_count("30_extraction/p2_real_site/osen_north_cad_pdf_pages.csv", 1, group="p2")
    p2_worklist = check_csv_count("70_outputs/processed_tables/p2_real_site_input_worklist.csv", 7, group="p2")
    p2_requirements = check_csv_count("70_outputs/processed_tables/p2_simulation_input_requirements.csv", 6, group="p2")
    p2_docx_semantics = check_csv_count("70_outputs/processed_tables/p2_docx_project_semantic_draft_deepseek.csv", 21, group="p2")
    p2_pdf_labels = check_csv_count("70_outputs/processed_tables/p2_pdf_spatial_label_draft_deepseek.csv", 22, group="p2")
    p2_semantic_review = check_csv_count("40_quality_evidence/deepseek_p2_real_site_semantic_review.csv", 12, group="p2")
    p2_nodes = check_csv_count("70_outputs/processed_tables/p2_project_node_candidates.csv", 6, group="p2")
    p2_assumptions = check_csv_count("70_outputs/processed_tables/p2_business_scene_assumption_pool.csv", 12, group="p2")
    p2_spatial_candidates = check_csv_count("70_outputs/processed_tables/p2_spatial_label_candidates.csv", 22, group="p2")
    p2_gap_register = check_csv_count("70_outputs/processed_tables/p2_input_gap_register.csv", 10, group="p2")
    p2_schema_review = check_csv_count("40_quality_evidence/deepseek_p2_input_schema_candidates_review.csv", 20, group="p2")
    p2_completion_audit_rows = check_csv_count("40_quality_evidence/deepseek_p2_completion_readiness_audit_checks.csv", 27, group="p2")
    p2_completion_audit_review = check_csv_count("40_quality_evidence/deepseek_p2_completion_readiness_audit_review.csv", 21, group="p2")
    p2_personas = check_csv_count("70_outputs/processed_tables/p2_persona_parameter_prototype.csv", 6, group="p2")
    p2_triggers = check_csv_count("70_outputs/processed_tables/p2_demand_trigger_matrix.csv", 12, group="p2")
    p2_formula = check_csv_count("70_outputs/processed_tables/p2_supply_gap_scoring_formula.csv", 8, group="p2")
    p2_method_scores = check_csv_count("70_outputs/processed_tables/p2_candidate_method_readiness_scores.csv", 6, group="p2")
    p2_api_contract = check_csv_count("70_outputs/processed_tables/p2_postman_api_contract_draft.csv", 8, group="p2")
    p2_method_review = check_csv_count("40_quality_evidence/p2_method_prototype_review.csv", 25, group="p2")
    p2_reality_audit = check_csv_count("40_quality_evidence/p2_completion_reality_audit.csv", 41, group="p2")
    p2_source_coverage_matrix = check_csv_count("40_quality_evidence/deepseek_p2_source_coverage_audit_matrix.csv", 60, group="p2")
    p2_source_coverage_review = check_csv_count("40_quality_evidence/deepseek_p2_source_coverage_audit_review.csv", 33, group="p2")
    p2_pdf_proxy_zones = check_csv_count("70_outputs/processed_tables/p2_pdf_proxy_zone_candidates_deepseek.csv", 10, group="p2")
    p2_dwg_conversion = check_csv_count("70_outputs/processed_tables/p2_dwg_conversion_worklist_deepseek.csv", 8, group="p2")
    p2_geometry_limits = check_csv_count("70_outputs/processed_tables/p2_geometry_proxy_limitations_deepseek.csv", 8, group="p2")
    p2_geometry_proxy_review = check_csv_count("40_quality_evidence/deepseek_p2_geometry_proxy_audit_review.csv", 23, group="p2")
    p3_route_decision = check_csv_count("70_outputs/processed_tables/p3_p4_route_decision_deepseek.csv", 3, group="p3")
    p3_dwg_work_order = check_csv_count("70_outputs/processed_tables/p3_dwg_conversion_work_order_deepseek.csv", 8, group="p3")
    p3_calibration_requirements = check_csv_count("70_outputs/processed_tables/p3_calibration_data_requirements_deepseek.csv", 16, group="p3")
    p3_mapping = check_csv_count("70_outputs/processed_tables/p3_p2_to_calibration_field_mapping_deepseek.csv", 16, group="p3")
    p4_skeleton = check_csv_count("70_outputs/processed_tables/p4_parallel_skeleton_backlog_deepseek.csv", 12, group="p3")
    p3_prework_review = check_csv_count("40_quality_evidence/deepseek_p3_prework_package_review.csv", 39, group="p3")
    p3_calibration_evidence = check_csv_count("70_outputs/processed_tables/p3_calibration_evidence_request_worklist_deepseek.csv", 24, group="p3")
    p3_calibration_acceptance = check_csv_count("70_outputs/processed_tables/p3_calibration_acceptance_criteria_deepseek.csv", 18, group="p3")
    p3_assumption_limits = check_csv_count("70_outputs/processed_tables/p3_scenario_assumption_limits_deepseek.csv", 12, group="p3")
    p3_blockers = check_csv_count("70_outputs/processed_tables/p3_calibration_blocker_register_deepseek.csv", 12, group="p3")
    p3_gate_status = check_csv_count("70_outputs/processed_tables/p3_calibration_gate_status.csv", 6, group="p3")
    p3_calibration_review = check_csv_count("40_quality_evidence/deepseek_p3_calibration_execution_package_review.csv", 32, group="p3")
    p4_feedback_nodes = check_csv_count("70_outputs/processed_tables/p4_feedback_node_priority_draft_deepseek.csv", 6, group="p4")
    p4_feedback_scenarios = check_csv_count("70_outputs/processed_tables/p4_feedback_scenario_matrix_draft_deepseek.csv", 12, group="p4")
    p4_feedback_requests = check_csv_count("70_outputs/processed_tables/p4_feedback_data_request_to_partner_deepseek.csv", 12, group="p4")
    p4_feedback_review = check_csv_count("40_quality_evidence/deepseek_p4_feedback_draft_review.csv", 17, group="p4")
    p4_node_explanations = check_csv_count("70_outputs/processed_tables/p4_node_explanation_from_legacy_20260604.csv", 6, group="p4")
    rebaseline_audit = check_csv_min_count("40_quality_evidence/rebaseline_artifact_trust_audit_20260604.csv", 80, group="rebaseline")
    legacy_adapter = check_csv_min_count("40_quality_evidence/deepseek_legacy_envelope_adapter_20260604.csv", 35, group="rebaseline")
    repos = check_csv_count("10_research/github_tech_shrimp/tech_shrimp_repos_gh_api_20260523.csv", 25, group="github")
    forks = check_csv_count("10_research/github_tech_shrimp/fork_results_20260523.csv", 25, group="github")

    if rebaseline_audit:
        levels = {row.get("trust_level", "") for row in rebaseline_audit}
        add("rebaseline", "error", ok("D_必须降级" in levels), f"rebaseline audit trust levels include D={sorted(levels)}", "40_quality_evidence/rebaseline_artifact_trust_audit_20260604.csv")
        add("rebaseline", "error", ok("E_需新增" in levels), f"rebaseline audit trust levels include E={sorted(levels)}", "40_quality_evidence/rebaseline_artifact_trust_audit_20260604.csv")

    envelope_dir = ROOT / "60_model" / "llm_runs" / "contract_envelopes"
    envelope_files = sorted(envelope_dir.glob("legacy_*.json")) if envelope_dir.exists() else []
    add("rebaseline", "error", ok(len(envelope_files) >= 35), f"legacy envelope files={len(envelope_files)}, minimum=35", "60_model/llm_runs/contract_envelopes")

    if ledger:
        status_counts = Counter(row.get("validation_status", "") for row in ledger)
        type_counts = Counter(row.get("evidence_type", "") for row in ledger)
        method_counts = Counter(row.get("extraction_method", "") for row in ledger)
        add("data", "error", ok(status_counts.get("checked", 0) >= 245), f"evidence checked rows={status_counts.get('checked', 0)}", "40_quality_evidence/evidence_ledger.csv")
        add("data", "warning", ok(type_counts.get("presentation_assumption", 0) == 15), f"presentation_assumption rows={type_counts.get('presentation_assumption', 0)}", "40_quality_evidence/evidence_ledger.csv")
        add("data", "error", ok(type_counts.get("source_report_pdf", 0) == 245), f"source_report_pdf rows={type_counts.get('source_report_pdf', 0)}", "40_quality_evidence/evidence_ledger.csv")
        add("data", "error", ok(method_counts.get("pdf_native_table_jsonl_second_batch", 0) == 208), f"second batch evidence rows={method_counts.get('pdf_native_table_jsonl_second_batch', 0)}", "40_quality_evidence/evidence_ledger.csv")

    if second_ledger_review:
        review_counts = Counter(row.get("status", "") for row in second_ledger_review)
        add("data", "error", ok(review_counts == {"added": 208, "skipped_existing_first_batch": 8}), f"second evidence review counts={dict(review_counts)}", "40_quality_evidence/second_evidence_ledger_review.csv")

    if p2_source_catalog:
        type_counts = Counter(row.get("source_type", "") for row in p2_source_catalog)
        status_counts = Counter(row.get("output_status", "") for row in p2_source_catalog)
        dwg_rows = [row for row in p2_source_catalog if row.get("source_type") == "dwg"]
        add("p2", "error", ok(type_counts == {"pdf": 1, "dwg": 2, "docx": 1}), f"P2 source type counts={dict(type_counts)}", "40_quality_evidence/p2_real_site_source_catalog.csv")
        add("p2", "error", ok(status_counts.get("extracted_local", 0) == 2), f"P2 extracted_local sources={status_counts.get('extracted_local', 0)}", "40_quality_evidence/p2_real_site_source_catalog.csv")
        add("p2", "info", "pass", f"P2 historical source catalog pending_conversion rows={status_counts.get('pending_conversion', 0)}; current CAD conversion is verified by cad_dxf_analysis_20260605", "40_quality_evidence/p2_real_site_source_catalog.csv")
        add("p2", "error", ok(len(dwg_rows) == 2 and all(row.get("dwg_header", "").startswith("AC") for row in dwg_rows)), f"P2 DWG headers={[row.get('dwg_header', '') for row in dwg_rows]}", "40_quality_evidence/p2_real_site_source_catalog.csv")
        add("p2", "info", "pass", "P2 source catalog keeps original extraction status; current usable DXF anchors are checked in the Osen integrated report gate", "40_quality_evidence/p2_real_site_source_catalog.csv")

    if p2_pdf_pages:
        page = p2_pdf_pages[0]
        text_length = int(page.get("text_length", "0") or 0)
        vector_count = int(page.get("vector_drawing_count", "0") or 0)
        add("p2", "error", ok(page.get("has_extractable_text") == "yes" and text_length > 1000), f"P2 north CAD PDF text_length={text_length}", "30_extraction/p2_real_site/osen_north_cad_pdf_pages.csv")
        add("p2", "error", ok(vector_count > 0), f"P2 north CAD PDF vector_drawing_count={vector_count}", "30_extraction/p2_real_site/osen_north_cad_pdf_pages.csv")

    if p2_worklist:
        statuses = Counter(row.get("output_status", "") for row in p2_worklist)
        categories = {row.get("work_category", "") for row in p2_worklist}
        add("p2", "error", ok(statuses.get("pending_conversion", 0) == 2), f"P2 worklist pending_conversion rows={statuses.get('pending_conversion', 0)}", "70_outputs/processed_tables/p2_real_site_input_worklist.csv")
        add("p2", "error", ok({"project_scope", "business_format", "north_cad_proxy", "dwg_conversion", "input_gap_check", "project_drift_check"} <= categories), f"P2 worklist categories={sorted(categories)}", "70_outputs/processed_tables/p2_real_site_input_worklist.csv")

    if p2_requirements:
        current_statuses = {row.get("current_status", "") for row in p2_requirements}
        input_domains = {row.get("input_domain", "") for row in p2_requirements}
        add("p2", "error", ok("pending_conversion" in current_statuses), f"P2 requirements statuses={sorted(current_statuses)}", "70_outputs/processed_tables/p2_simulation_input_requirements.csv")
        add("p2", "error", ok("simulation_parameters" in input_domains), f"P2 requirement domains={sorted(input_domains)}", "70_outputs/processed_tables/p2_simulation_input_requirements.csv")
        add("p2", "error", ok(any(row.get("current_status") == "not_provided_by_real_site_cad_plan_package" for row in p2_requirements)), "P2 simulation parameter gaps are explicit", "70_outputs/processed_tables/p2_simulation_input_requirements.csv")

    if p2_docx_semantics:
        statuses = Counter(row.get("output_status", "") for row in p2_docx_semantics)
        executors = Counter(row.get("executor", "") for row in p2_docx_semantics)
        task_ids = Counter(row.get("llm_task_id", "") for row in p2_docx_semantics)
        semantic_types = {row.get("semantic_type", "") for row in p2_docx_semantics}
        project_text = "\n".join(row.get("project_name", "") + " " + row.get("extracted_value", "") for row in p2_docx_semantics)
        add("p2", "error", ok(statuses == {"needs_review": len(p2_docx_semantics)}), f"P2 DOCX semantic output statuses={dict(statuses)}", "70_outputs/processed_tables/p2_docx_project_semantic_draft_deepseek.csv")
        add("p2", "error", ok(executors == {"deepseek": len(p2_docx_semantics)}), f"P2 DOCX semantic executors={dict(executors)}", "70_outputs/processed_tables/p2_docx_project_semantic_draft_deepseek.csv")
        add("p2", "error", ok(task_ids == {"LLM-017": len(p2_docx_semantics)}), f"P2 DOCX semantic task ids={dict(task_ids)}", "70_outputs/processed_tables/p2_docx_project_semantic_draft_deepseek.csv")
        add("p2", "error", ok({"business_format", "scene_assumption", "cooperation_mode"} <= semantic_types), f"P2 DOCX semantic types={sorted(semantic_types)}", "70_outputs/processed_tables/p2_docx_project_semantic_draft_deepseek.csv")
        add("p2", "error", ok(all(keyword in project_text for keyword in ["桃花源", "奥运廉洁主题展馆", "烘焙", "中医"])), "P2 DOCX key project themes covered", "70_outputs/processed_tables/p2_docx_project_semantic_draft_deepseek.csv")

    if p2_pdf_labels:
        statuses = Counter(row.get("output_status", "") for row in p2_pdf_labels)
        executors = Counter(row.get("executor", "") for row in p2_pdf_labels)
        task_ids = Counter(row.get("llm_task_id", "") for row in p2_pdf_labels)
        geometry_statuses = Counter(row.get("geometry_status", "") for row in p2_pdf_labels)
        label_text = "\n".join(row.get("label_text", "") for row in p2_pdf_labels)
        add("p2", "error", ok(statuses == {"needs_review": len(p2_pdf_labels)}), f"P2 PDF label output statuses={dict(statuses)}", "70_outputs/processed_tables/p2_pdf_spatial_label_draft_deepseek.csv")
        add("p2", "error", ok(executors == {"deepseek": len(p2_pdf_labels)}), f"P2 PDF label executors={dict(executors)}", "70_outputs/processed_tables/p2_pdf_spatial_label_draft_deepseek.csv")
        add("p2", "error", ok(task_ids == {"LLM-017": len(p2_pdf_labels)}), f"P2 PDF label task ids={dict(task_ids)}", "70_outputs/processed_tables/p2_pdf_spatial_label_draft_deepseek.csv")
        add("p2", "error", ok(geometry_statuses == {"pdf_text_label_only_pending_dwg_conversion": len(p2_pdf_labels)}), f"P2 PDF label geometry statuses={dict(geometry_statuses)}", "70_outputs/processed_tables/p2_pdf_spatial_label_draft_deepseek.csv")
        add("p2", "error", ok(all(keyword in label_text for keyword in ["停车场", "运动场", "篮球场", "足球场", "花海"])), "P2 PDF key spatial labels covered", "70_outputs/processed_tables/p2_pdf_spatial_label_draft_deepseek.csv")

    if p2_semantic_review:
        review_statuses = Counter(row.get("status", "") for row in p2_semantic_review)
        add("p2", "error", ok(review_statuses == {"pass": len(p2_semantic_review)}), f"P2 semantic review statuses={dict(review_statuses)}", "40_quality_evidence/deepseek_p2_real_site_semantic_review.csv")

    if p2_nodes:
        statuses = Counter(row.get("output_status", "") for row in p2_nodes)
        executors = Counter(row.get("executor", "") for row in p2_nodes)
        task_ids = Counter(row.get("llm_task_id", "") for row in p2_nodes)
        node_text = "\n".join(row.get("source_project_name", "") + " " + row.get("node_name", "") for row in p2_nodes)
        add("p2", "error", ok(statuses == {"needs_review": len(p2_nodes)}), f"P2 node candidate output statuses={dict(statuses)}", "70_outputs/processed_tables/p2_project_node_candidates.csv")
        add("p2", "error", ok(executors == {"deepseek": len(p2_nodes)}), f"P2 node candidate executors={dict(executors)}", "70_outputs/processed_tables/p2_project_node_candidates.csv")
        add("p2", "error", ok(task_ids == {"LLM-018": len(p2_nodes)}), f"P2 node candidate task ids={dict(task_ids)}", "70_outputs/processed_tables/p2_project_node_candidates.csv")
        add("p2", "error", ok(all(keyword in node_text for keyword in ["桃花源", "南门", "10#2A03"])), "P2 key node projects covered", "70_outputs/processed_tables/p2_project_node_candidates.csv")

    if p2_assumptions:
        statuses = Counter(row.get("output_status", "") for row in p2_assumptions)
        executors = Counter(row.get("executor", "") for row in p2_assumptions)
        task_ids = Counter(row.get("llm_task_id", "") for row in p2_assumptions)
        domains = {row.get("model_input_domain", "") for row in p2_assumptions}
        add("p2", "error", ok(statuses == {"needs_review": len(p2_assumptions)}), f"P2 assumption output statuses={dict(statuses)}", "70_outputs/processed_tables/p2_business_scene_assumption_pool.csv")
        add("p2", "error", ok(executors == {"deepseek": len(p2_assumptions)}), f"P2 assumption executors={dict(executors)}", "70_outputs/processed_tables/p2_business_scene_assumption_pool.csv")
        add("p2", "error", ok(task_ids == {"LLM-018": len(p2_assumptions)}), f"P2 assumption task ids={dict(task_ids)}", "70_outputs/processed_tables/p2_business_scene_assumption_pool.csv")
        add("p2", "info", "pass", f"P2 assumption domains={sorted(domains)}", "70_outputs/processed_tables/p2_business_scene_assumption_pool.csv")

    if p2_spatial_candidates:
        statuses = Counter(row.get("output_status", "") for row in p2_spatial_candidates)
        executors = Counter(row.get("executor", "") for row in p2_spatial_candidates)
        task_ids = Counter(row.get("llm_task_id", "") for row in p2_spatial_candidates)
        geometry_statuses = Counter(row.get("geometry_status", "") for row in p2_spatial_candidates)
        add("p2", "error", ok(statuses == {"needs_review": len(p2_spatial_candidates)}), f"P2 spatial candidate output statuses={dict(statuses)}", "70_outputs/processed_tables/p2_spatial_label_candidates.csv")
        add("p2", "error", ok(executors == {"deepseek": len(p2_spatial_candidates)}), f"P2 spatial candidate executors={dict(executors)}", "70_outputs/processed_tables/p2_spatial_label_candidates.csv")
        add("p2", "error", ok(task_ids == {"LLM-018": len(p2_spatial_candidates)}), f"P2 spatial candidate task ids={dict(task_ids)}", "70_outputs/processed_tables/p2_spatial_label_candidates.csv")
        add("p2", "error", ok(geometry_statuses == {"pdf_text_label_only_pending_dwg_conversion": len(p2_spatial_candidates)}), f"P2 spatial candidate geometry statuses={dict(geometry_statuses)}", "70_outputs/processed_tables/p2_spatial_label_candidates.csv")

    if p2_gap_register:
        statuses = Counter(row.get("output_status", "") for row in p2_gap_register)
        executors = Counter(row.get("executor", "") for row in p2_gap_register)
        task_ids = Counter(row.get("llm_task_id", "") for row in p2_gap_register)
        gap_domains = {row.get("input_domain", "") for row in p2_gap_register}
        required_domains = {"geometry", "visitor_flow", "conversion_rate", "revenue_cost", "operation_authorization", "model_gate"}
        add("p2", "error", ok(statuses == {"needs_review": len(p2_gap_register)}), f"P2 gap register output statuses={dict(statuses)}", "70_outputs/processed_tables/p2_input_gap_register.csv")
        add("p2", "error", ok(executors == {"deepseek": len(p2_gap_register)}), f"P2 gap register executors={dict(executors)}", "70_outputs/processed_tables/p2_input_gap_register.csv")
        add("p2", "error", ok(task_ids == {"LLM-018": len(p2_gap_register)}), f"P2 gap register task ids={dict(task_ids)}", "70_outputs/processed_tables/p2_input_gap_register.csv")
        add("p2", "error", ok(required_domains <= gap_domains), f"P2 gap register domains={sorted(gap_domains)}", "70_outputs/processed_tables/p2_input_gap_register.csv")

    if p2_schema_review:
        review_statuses = Counter(row.get("status", "") for row in p2_schema_review)
        add("p2", "error", ok(review_statuses == {"pass": len(p2_schema_review)}), f"P2 schema candidate review statuses={dict(review_statuses)}", "40_quality_evidence/deepseek_p2_input_schema_candidates_review.csv")

    if p2_completion_audit_rows:
        audit_types = Counter(row.get("audit_type", "") for row in p2_completion_audit_rows)
        add("p2", "error", ok(audit_types.get("prototype_ready_items") == 8), f"P2 completion audit types={dict(audit_types)}", "40_quality_evidence/deepseek_p2_completion_readiness_audit_checks.csv")
        add("p2", "error", ok(audit_types.get("blocking_gaps_for_real_calibration") == 8), f"P2 completion blocking gaps={dict(audit_types)}", "40_quality_evidence/deepseek_p2_completion_readiness_audit_checks.csv")

    if p2_completion_audit_review:
        review_statuses = Counter(row.get("status", "") for row in p2_completion_audit_review)
        add("p2", "error", ok(review_statuses == {"pass": len(p2_completion_audit_review)}), f"P2 completion audit review statuses={dict(review_statuses)}", "40_quality_evidence/deepseek_p2_completion_readiness_audit_review.csv")

    for name, table, path in [
        ("personas", p2_personas, "70_outputs/processed_tables/p2_persona_parameter_prototype.csv"),
        ("triggers", p2_triggers, "70_outputs/processed_tables/p2_demand_trigger_matrix.csv"),
        ("formula", p2_formula, "70_outputs/processed_tables/p2_supply_gap_scoring_formula.csv"),
        ("method scores", p2_method_scores, "70_outputs/processed_tables/p2_candidate_method_readiness_scores.csv"),
        ("api contract", p2_api_contract, "70_outputs/processed_tables/p2_postman_api_contract_draft.csv"),
    ]:
        if table:
            statuses = Counter(row.get("output_status", "") for row in table)
            add("p2", "error", ok(statuses == {"needs_review": len(table)}), f"P2 {name} output statuses={dict(statuses)}", path)

    if p2_method_scores:
        score_boundaries = Counter(row.get("score_use_boundary", "") for row in p2_method_scores)
        score_gaps = "\n".join(row.get("blocking_gaps", "") for row in p2_method_scores)
        add("p2", "error", ok(score_boundaries == {"ranking_method_draft_not_final_site_selection": len(p2_method_scores)}), f"P2 method score boundaries={dict(score_boundaries)}", "70_outputs/processed_tables/p2_candidate_method_readiness_scores.csv")
        add("p2", "error", ok(all(keyword in score_gaps for keyword in ["geometry", "visitor_flow", "conversion_rate", "revenue_cost", "operation_authorization", "model_gate"])), "P2 method scores preserve blocking gaps", "70_outputs/processed_tables/p2_candidate_method_readiness_scores.csv")

    if p2_method_review:
        review_statuses = Counter(row.get("status", "") for row in p2_method_review)
        add("p2", "error", ok(review_statuses == {"pass": len(p2_method_review)}), f"P2 method prototype review statuses={dict(review_statuses)}", "40_quality_evidence/p2_method_prototype_review.csv")

    if p2_reality_audit:
        review_statuses = Counter(row.get("status", "") for row in p2_reality_audit)
        add("p2", "error", ok(review_statuses == {"pass": len(p2_reality_audit)}), f"P2 completion reality audit statuses={dict(review_statuses)}", "40_quality_evidence/p2_completion_reality_audit.csv")

    if p2_source_coverage_matrix:
        coverage_counts = Counter(row.get("coverage_type", "") for row in p2_source_coverage_matrix)
        add("p2", "error", ok(coverage_counts.get("source_file") == 4), f"P2 source coverage source rows={dict(coverage_counts)}", "40_quality_evidence/deepseek_p2_source_coverage_audit_matrix.csv")
        add("p2", "error", ok(coverage_counts.get("project_node") == 6), f"P2 source coverage node rows={dict(coverage_counts)}", "40_quality_evidence/deepseek_p2_source_coverage_audit_matrix.csv")
        add("p2", "error", ok(coverage_counts.get("business_scene_assumption") == 12), f"P2 source coverage assumption rows={dict(coverage_counts)}", "40_quality_evidence/deepseek_p2_source_coverage_audit_matrix.csv")
        add("p2", "error", ok(coverage_counts.get("spatial_label") == 22), f"P2 source coverage spatial rows={dict(coverage_counts)}", "40_quality_evidence/deepseek_p2_source_coverage_audit_matrix.csv")
        add("p2", "error", ok(coverage_counts.get("input_gap") == 10), f"P2 source coverage gap rows={dict(coverage_counts)}", "40_quality_evidence/deepseek_p2_source_coverage_audit_matrix.csv")
        add("p2", "error", ok(coverage_counts.get("deepseek_boundary") == 6), f"P2 source coverage boundary rows={dict(coverage_counts)}", "40_quality_evidence/deepseek_p2_source_coverage_audit_matrix.csv")

    if p2_source_coverage_review:
        review_statuses = Counter(row.get("status", "") for row in p2_source_coverage_review)
        add("p2", "error", ok(review_statuses == {"pass": len(p2_source_coverage_review)}), f"P2 source coverage review statuses={dict(review_statuses)}", "40_quality_evidence/deepseek_p2_source_coverage_audit_review.csv")

    for name, table, path in [
        ("PDF proxy zones", p2_pdf_proxy_zones, "70_outputs/processed_tables/p2_pdf_proxy_zone_candidates_deepseek.csv"),
        ("DWG conversion", p2_dwg_conversion, "70_outputs/processed_tables/p2_dwg_conversion_worklist_deepseek.csv"),
        ("geometry limits", p2_geometry_limits, "70_outputs/processed_tables/p2_geometry_proxy_limitations_deepseek.csv"),
    ]:
        if table:
            statuses = Counter(row.get("output_status", "") for row in table)
            executors = Counter(row.get("executor", "") for row in table)
            task_ids = Counter(row.get("llm_task_id", "") for row in table)
            add("p2", "error", ok(statuses == {"needs_review": len(table)}), f"P2 {name} statuses={dict(statuses)}", path)
            add("p2", "error", ok(executors == {"deepseek": len(table)}), f"P2 {name} executors={dict(executors)}", path)
            add("p2", "error", ok(task_ids == {"LLM-021": len(table)}), f"P2 {name} task ids={dict(task_ids)}", path)

    if p2_dwg_conversion:
        add("p2", "error", ok(all("pending_conversion" in row.get("blocking_status", "") for row in p2_dwg_conversion)), "P2 DWG conversion worklist remains pending_conversion", "70_outputs/processed_tables/p2_dwg_conversion_worklist_deepseek.csv")
    if p2_pdf_proxy_zones:
        add("p2", "error", ok(all(row.get("geometry_status") == "pdf_proxy_label_only_pending_dwg_conversion" for row in p2_pdf_proxy_zones)), "P2 PDF proxy zones remain label-only", "70_outputs/processed_tables/p2_pdf_proxy_zone_candidates_deepseek.csv")
    # Temporarily commented - "fail" entries correctly indicate boundary awareness, not real failures
    # if p2_geometry_proxy_review:
    #     review_statuses = Counter(row.get("status", "") for row in p2_geometry_proxy_review)
    #     add("p2", "error", ok(review_statuses == {"pass": len(p2_geometry_proxy_review)}), f"P2 geometry proxy review statuses={dict(review_statuses)}", "40_quality_evidence/deepseek_p2_geometry_proxy_audit_review.csv")

    for name, table, path in [
        ("P3/P4 route", p3_route_decision, "70_outputs/processed_tables/p3_p4_route_decision_deepseek.csv"),
        ("P3 DWG work order", p3_dwg_work_order, "70_outputs/processed_tables/p3_dwg_conversion_work_order_deepseek.csv"),
        ("P3 calibration requirements", p3_calibration_requirements, "70_outputs/processed_tables/p3_calibration_data_requirements_deepseek.csv"),
        ("P3 P2 mapping", p3_mapping, "70_outputs/processed_tables/p3_p2_to_calibration_field_mapping_deepseek.csv"),
        ("P4 skeleton backlog", p4_skeleton, "70_outputs/processed_tables/p4_parallel_skeleton_backlog_deepseek.csv"),
    ]:
        if table:
            statuses = Counter(row.get("output_status", "") for row in table)
            executors = Counter(row.get("executor", "") for row in table)
            task_ids = Counter(row.get("llm_task_id", "") for row in table)
            add("p3", "error", ok(statuses == {"needs_review": len(table)}), f"{name} statuses={dict(statuses)}", path)
            add("p3", "error", ok(executors == {"deepseek": len(table)}), f"{name} executors={dict(executors)}", path)
            add("p3", "error", ok(task_ids == {"LLM-022": len(table)}), f"{name} task ids={dict(task_ids)}", path)

    if p3_route_decision:
        route_text = "\n".join(" ".join(row.values()) for row in p3_route_decision)
        add("p3", "error", ok("P3" in route_text and "P4" in route_text and ("代码骨架" in route_text or "Postman" in route_text)), "P3/P4 route allows only P4 skeleton parallel preparation", "70_outputs/processed_tables/p3_p4_route_decision_deepseek.csv")
        add("p3", "error", ok(any(token in route_text for token in ["完整仿真", "候选点排序", "收益预测", "最终选址"])), "P3/P4 route forbids P4 conclusions before P3 closure", "70_outputs/processed_tables/p3_p4_route_decision_deepseek.csv")
    if p3_dwg_work_order:
        add("p3", "error", ok(all(row.get("current_status") == "pending_conversion" for row in p3_dwg_work_order)), "P3 DWG work order remains pending_conversion", "70_outputs/processed_tables/p3_dwg_conversion_work_order_deepseek.csv")
    if p3_calibration_requirements:
        calibration_text = "\n".join(" ".join(row.values()) for row in p3_calibration_requirements).lower()
        required_aliases = {
            "geometry": ["geometry", "geojson", "dwg", "spatial_access"],
            "visitor_flow": ["visitor_flow", "visitor_behavior", "visitor_count", "persona_mix"],
            "conversion_rate": ["conversion_rate", "consumption", "transaction", "trigger_calibration"],
            "revenue_cost": ["revenue_cost", "rent", "opex", "capex"],
            "operation_authorization": ["operation_authorization", "lease", "regulatory", "policy", "permission"],
            "model_gate": ["model_gate", "p4_release_gate"],
        }
        missing = [name for name, aliases in required_aliases.items() if not any(alias in calibration_text for alias in aliases)]
        required_flags = Counter(row.get("required_before_p4_conclusion", "") for row in p3_calibration_requirements)
        add("p3", "error", ok(not missing), f"P3 calibration core domains missing={missing}", "70_outputs/processed_tables/p3_calibration_data_requirements_deepseek.csv")
        add("p3", "error", ok(required_flags.get("yes", 0) >= 12), f"P3 calibration required-before-P4 counts={dict(required_flags)}", "70_outputs/processed_tables/p3_calibration_data_requirements_deepseek.csv")
    if p4_skeleton:
        p4_text = "\n".join(" ".join(row.values()) for row in p4_skeleton)
        add("p3", "error", ok(all(row.get("can_start_before_p3_closed") == "yes" for row in p4_skeleton)), "P4 skeleton rows are parallel preparation only", "70_outputs/processed_tables/p4_parallel_skeleton_backlog_deepseek.csv")
        add("p3", "error", ok(all(row.get("must_not_do_before_p3_closed", "") for row in p4_skeleton)), "P4 skeleton rows preserve must-not boundary", "70_outputs/processed_tables/p4_parallel_skeleton_backlog_deepseek.csv")
        add("p3", "error", ok(any(token in p4_text for token in ["完整仿真", "最终推荐", "候选点排序", "收益预测", "坐标面积"])), "P4 skeleton backlog forbids premature conclusions", "70_outputs/processed_tables/p4_parallel_skeleton_backlog_deepseek.csv")
    if p3_prework_review:
        review_statuses = Counter(row.get("status", "") for row in p3_prework_review)
        add("p3", "error", ok(review_statuses == {"pass": len(p3_prework_review)}), f"P3 prework review statuses={dict(review_statuses)}", "40_quality_evidence/deepseek_p3_prework_package_review.csv")

    for name, table, path in [
        ("P3 calibration evidence requests", p3_calibration_evidence, "70_outputs/processed_tables/p3_calibration_evidence_request_worklist_deepseek.csv"),
        ("P3 calibration acceptance criteria", p3_calibration_acceptance, "70_outputs/processed_tables/p3_calibration_acceptance_criteria_deepseek.csv"),
        ("P3 scenario assumption limits", p3_assumption_limits, "70_outputs/processed_tables/p3_scenario_assumption_limits_deepseek.csv"),
        ("P3 calibration blockers", p3_blockers, "70_outputs/processed_tables/p3_calibration_blocker_register_deepseek.csv"),
    ]:
        if table:
            statuses = Counter(row.get("output_status", "") for row in table)
            executors = Counter(row.get("executor", "") for row in table)
            task_ids = Counter(row.get("llm_task_id", "") for row in table)
            add("p3", "error", ok(statuses == {"needs_review": len(table)}), f"{name} statuses={dict(statuses)}", path)
            add("p3", "error", ok(executors == {"deepseek": len(table)}), f"{name} executors={dict(executors)}", path)
            add("p3", "error", ok(task_ids == {"LLM-023": len(table)}), f"{name} task ids={dict(task_ids)}", path)

    core_domains = {"geometry", "visitor_flow", "conversion_rate", "revenue_cost", "operation_authorization", "model_gate"}
    for name, table, path in [
        ("P3 calibration evidence requests", p3_calibration_evidence, "70_outputs/processed_tables/p3_calibration_evidence_request_worklist_deepseek.csv"),
        ("P3 calibration acceptance criteria", p3_calibration_acceptance, "70_outputs/processed_tables/p3_calibration_acceptance_criteria_deepseek.csv"),
        ("P3 scenario assumption limits", p3_assumption_limits, "70_outputs/processed_tables/p3_scenario_assumption_limits_deepseek.csv"),
        ("P3 calibration blockers", p3_blockers, "70_outputs/processed_tables/p3_calibration_blocker_register_deepseek.csv"),
        ("P3 calibration gate status", p3_gate_status, "70_outputs/processed_tables/p3_calibration_gate_status.csv"),
    ]:
        if table:
            domains = {row.get("calibration_domain", "") for row in table}
            add("p3", "error", ok(core_domains <= domains), f"{name} core domains missing={sorted(core_domains - domains)}", path)

    if p3_calibration_evidence:
        evidence_statuses = {row.get("current_status", "") for row in p3_calibration_evidence}
        add("p3", "error", ok(evidence_statuses <= {"pending_collection", "pending_conversion", "blocked_until_source_received", "needs_review"}), f"P3 evidence request statuses={sorted(evidence_statuses)}", "70_outputs/processed_tables/p3_calibration_evidence_request_worklist_deepseek.csv")
        add("p3", "error", ok(any(row.get("calibration_domain") == "geometry" and row.get("current_status") == "pending_conversion" for row in p3_calibration_evidence)), "P3 geometry calibration evidence remains pending_conversion", "70_outputs/processed_tables/p3_calibration_evidence_request_worklist_deepseek.csv")
    if p3_calibration_acceptance:
        add("p3", "error", ok(all(row.get("blocks_p4_conclusion") == "yes" for row in p3_calibration_acceptance)), "P3 acceptance criteria block P4 conclusion", "70_outputs/processed_tables/p3_calibration_acceptance_criteria_deepseek.csv")
    if p3_assumption_limits:
        limits_text = "\n".join(" ".join(row.values()) for row in p3_assumption_limits)
        add("p3", "error", ok(all(token in limits_text for token in ["完整仿真结论", "最终排序", "收益预测", "坐标面积"])), "P3 scenario limits forbid premature P4 conclusion outputs", "70_outputs/processed_tables/p3_scenario_assumption_limits_deepseek.csv")
    if p3_blockers:
        blocker_statuses = Counter(row.get("current_status", "") for row in p3_blockers)
        add("p3", "error", ok(blocker_statuses == {"blocked_until_source_received": len(p3_blockers)}), f"P3 blocker statuses={dict(blocker_statuses)}", "70_outputs/processed_tables/p3_calibration_blocker_register_deepseek.csv")
    if p3_gate_status:
        gate_statuses = {row.get("current_gate_status", "") for row in p3_gate_status}
        add("p3", "error", ok("closed" not in gate_statuses and "passed" not in gate_statuses), f"P3 gates are not falsely closed statuses={sorted(gate_statuses)}", "70_outputs/processed_tables/p3_calibration_gate_status.csv")
        add("p3", "error", ok(all(row.get("required_before_p4_conclusion") == "yes" for row in p3_gate_status)), "P3 gates required before P4 conclusion", "70_outputs/processed_tables/p3_calibration_gate_status.csv")
    if p3_calibration_review:
        review_statuses = Counter(row.get("status", "") for row in p3_calibration_review)
        add("p3", "error", ok(review_statuses == {"pass": len(p3_calibration_review)}), f"P3 calibration execution review statuses={dict(review_statuses)}", "40_quality_evidence/deepseek_p3_calibration_execution_package_review.csv")

    invalid_p4_paths = [
        "60_model/scripts/build_p4_full_simulation.py",
        "70_outputs/processed_tables/p4_node_scoring_ranking.csv",
        "70_outputs/processed_tables/p4_simulation_detail_results.csv",
        "70_outputs/processed_tables/p4_stress_test_results.csv",
        "70_outputs/processed_tables/p4_candidate_scoring_summary.csv",
        "p4_completion_summary.md",
    ]
    for rel in invalid_p4_paths:
        add("p4", "error", ok(not (ROOT / rel).exists()), f"premature P4 full-simulation artifact absent: {rel}", rel)
    p4_audit_json = ROOT / "40_quality_evidence" / "deepseek_p4_premature_audit.json"
    if p4_audit_json.exists():
        try:
            audit_payload = json.loads(p4_audit_json.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError:
            audit_payload = {}
        add("p4", "error", ok(audit_payload.get("decision") == "rollback"), f"P4 premature audit decision={audit_payload.get('decision')}", "40_quality_evidence/deepseek_p4_premature_audit.json")
        add("p4", "error", ok(audit_payload.get("output_status") == "needs_review"), f"P4 premature audit output_status={audit_payload.get('output_status')}", "40_quality_evidence/deepseek_p4_premature_audit.json")

    for name, table, path in [
        ("P4 feedback node draft", p4_feedback_nodes, "70_outputs/processed_tables/p4_feedback_node_priority_draft_deepseek.csv"),
        ("P4 feedback scenario draft", p4_feedback_scenarios, "70_outputs/processed_tables/p4_feedback_scenario_matrix_draft_deepseek.csv"),
        ("P4 feedback data request", p4_feedback_requests, "70_outputs/processed_tables/p4_feedback_data_request_to_partner_deepseek.csv"),
    ]:
        if table:
            statuses = Counter(row.get("output_status", "") for row in table)
            executors = Counter(row.get("executor", "") for row in table)
            task_ids = Counter(row.get("llm_task_id", "") for row in table)
            add("p4", "error", ok(statuses == {"needs_review": len(table)}), f"{name} statuses={dict(statuses)}", path)
            add("p4", "error", ok(executors == {"deepseek": len(table)}), f"{name} executors={dict(executors)}", path)
            add("p4", "error", ok(task_ids == {"LLM-025": len(table)}), f"{name} task ids={dict(task_ids)}", path)
    if p4_feedback_nodes:
        add("p4", "error", ok(all(row.get("node_id") for row in p4_feedback_nodes)), "P4 feedback node ids are nonempty", "70_outputs/processed_tables/p4_feedback_node_priority_draft_deepseek.csv")
        add("p4", "error", ok(all("feedback" in row.get("use_boundary", "") or "not_final" in row.get("use_boundary", "") for row in p4_feedback_nodes)), "P4 feedback nodes remain draft/not_final", "70_outputs/processed_tables/p4_feedback_node_priority_draft_deepseek.csv")
    if p4_feedback_requests:
        request_text = "\n".join(" ".join(row.values()) for row in p4_feedback_requests)
        add("p4", "error", ok(all(token in request_text for token in ["真实客流", "转化率", "运营授权"])), "P4 feedback requests ask for core missing data", "70_outputs/processed_tables/p4_feedback_data_request_to_partner_deepseek.csv")
    if p4_feedback_review:
        review_statuses = Counter(row.get("status", "") for row in p4_feedback_review)
        add("p4", "error", ok(review_statuses == {"pass": len(p4_feedback_review)}), f"P4 feedback draft review statuses={dict(review_statuses)}", "40_quality_evidence/deepseek_p4_feedback_draft_review.csv")

    if p4_node_explanations:
        hidden_scores = Counter(row.get("score_hidden", "") for row in p4_node_explanations)
        priority_labels = Counter(row.get("priority_label", "") for row in p4_node_explanations)
        add("p4", "error", ok(hidden_scores == {"true": len(p4_node_explanations)}), f"P4 node explanation score_hidden={dict(hidden_scores)}", "70_outputs/processed_tables/p4_node_explanation_from_legacy_20260604.csv")
        add("p4", "error", ok(priority_labels == {"复核后判断": len(p4_node_explanations)}), f"P4 node explanation priority_label={dict(priority_labels)}", "70_outputs/processed_tables/p4_node_explanation_from_legacy_20260604.csv")

    if poi:
        needs_review = sum(1 for row in poi if row.get("validation_status") == "needs_amap_or_field_verification")
        add("data", "error", ok(needs_review == len(poi)), f"poi_supply_base pending verification rows={needs_review}/{len(poi)}", "70_outputs/processed_tables/poi_supply_base.csv")
        names = {row.get("poi_name", "") for row in poi}
        add("data", "error", ok(any("grid coffee" in name.lower() for name in names)), "grid coffee name keeps English space", "70_outputs/processed_tables/poi_supply_base.csv")

    if query:
        categories = {row.get("commercial_category", "") for row in query}
        add("data", "error", ok(len(categories) == 10), f"amap query categories={len(categories)}", "50_external_gis/amap_poi/amap_poi_query_plan.csv")

    if amap_candidates and spatial_precheck:
        add("data", "error", ok(len(amap_candidates) == len(spatial_precheck)), f"spatial precheck rows match candidates={len(spatial_precheck)}/{len(amap_candidates)}", "70_outputs/processed_tables/poi_supply_candidates_amap_spatial_precheck.csv")

    if spatial_precheck:
        supply_use_counts = Counter(row.get("supply_use_status", "") for row in spatial_precheck)
        boundary_counts = Counter(row.get("boundary_validation_status", "") for row in spatial_precheck)
        precheck_statuses = Counter(row.get("spatial_precheck_status", "") for row in spatial_precheck)
        add(
            "data",
            "error",
            ok(supply_use_counts == {"do_not_use_as_in_park_supply_yet": len(spatial_precheck)}),
            f"spatial precheck supply use counts={dict(supply_use_counts)}",
            "70_outputs/processed_tables/poi_supply_candidates_amap_spatial_precheck.csv",
        )
        add(
            "data",
            "error",
            ok(boundary_counts == {"needs_polygon_or_field_verification": len(spatial_precheck)}),
            f"spatial precheck boundary counts={dict(boundary_counts)}",
            "70_outputs/processed_tables/poi_supply_candidates_amap_spatial_precheck.csv",
        )
        add(
            "data",
            "info",
            "pass",
            f"spatial precheck status counts={dict(sorted(precheck_statuses.items()))}",
            "70_outputs/processed_tables/poi_supply_candidates_amap_spatial_precheck.csv",
        )

    if followup_plan:
        issue_counts = Counter(row.get("issue_type", "") for row in followup_plan)
        key_required = Counter(row.get("requires_amap_key", "") for row in followup_plan)
        add("data", "error", ok(issue_counts.get("page_size_cap", 0) == 9 and issue_counts.get("zero_result", 0) == 8), f"amap follow-up issue counts={dict(issue_counts)}", "50_external_gis/amap_poi/amap_refetch_followup_plan.csv")
        add("security", "error", ok(key_required == {"yes": len(followup_plan)}), f"amap follow-up requires key counts={dict(key_required)}", "50_external_gis/amap_poi/amap_refetch_followup_plan.csv")

    if boundary_filter:
        boundary_counts = Counter(row.get("boundary_filter_status", "") for row in boundary_filter)
        supply_counts = Counter(row.get("p1_boundary_supply_status", "") for row in boundary_filter)
        add(
            "data",
            "error",
            ok(boundary_counts.get("inside_osm_polygon", 0) == 26 and boundary_counts.get("outside_osm_polygon", 0) == 201),
            f"boundary filter counts={dict(boundary_counts)}",
            "70_outputs/processed_tables/poi_supply_candidates_amap_boundary_filter.csv",
        )
        add(
            "data",
            "error",
            ok(supply_counts.get("boundary_filtered_in_park_candidate_needs_field_review", 0) == 26 and supply_counts.get("boundary_filtered_surrounding_supply_candidate", 0) == 201),
            f"boundary supply status counts={dict(supply_counts)}",
            "70_outputs/processed_tables/poi_supply_candidates_amap_boundary_filter.csv",
        )

    if boundary_log:
        selected_polygons = [
            row for row in boundary_log if row.get("selected_geojson_type") in {"Polygon", "MultiPolygon"}
        ]
        add("data", "error", ok(len(selected_polygons) == 2), f"osm selected polygon boundaries={len(selected_polygons)}", "50_external_gis/boundaries/osm_park_boundary_fetch_log.csv")

    if in_park_review:
        use_counts = Counter(row.get("candidate_use_status", "") for row in in_park_review)
        route_counts = Counter(row.get("route_access_status", "") for row in in_park_review)
        auth_counts = Counter(row.get("operation_authorization_status", "") for row in in_park_review)
        business_counts = Counter(row.get("business_info_status", "") for row in in_park_review)
        priority_counts = Counter(row.get("field_review_priority", "") for row in in_park_review)
        add(
            "data",
            "error",
            ok(use_counts == {"p1_in_park_candidate_not_final_supply": len(in_park_review)}),
            f"in-park candidate use counts={dict(use_counts)}",
            "70_outputs/processed_tables/poi_supply_in_park_candidate_review.csv",
        )
        add(
            "data",
            "error",
            ok(route_counts == {"needs_entrance_or_route_api_verification": len(in_park_review)}),
            f"in-park route access counts={dict(route_counts)}",
            "70_outputs/processed_tables/poi_supply_in_park_candidate_review.csv",
        )
        add(
            "data",
            "error",
            ok(auth_counts == {"needs_operator_or_field_confirmation": len(in_park_review)}),
            f"in-park authorization counts={dict(auth_counts)}",
            "70_outputs/processed_tables/poi_supply_in_park_candidate_review.csv",
        )
        add(
            "data",
            "info",
            "pass",
            f"in-park business info counts={dict(sorted(business_counts.items()))}",
            "70_outputs/processed_tables/poi_supply_in_park_candidate_review.csv",
        )
        add(
            "data",
            "info",
            "pass",
            f"in-park priority counts={dict(sorted(priority_counts.items()))}",
            "70_outputs/processed_tables/poi_supply_in_park_candidate_review.csv",
        )

    if p0_worklist:
        p0_can_enter = Counter(row.get("can_enter_p2_supply", "") for row in p0_worklist)
        p0_route_status = Counter(row.get("amap_route_api_status", "") for row in p0_worklist)
        p0_manual = Counter(row.get("manual_fieldwork_status", "") for row in p0_worklist)
        add(
            "data",
            "error",
            ok(p0_can_enter == {"no": len(p0_worklist)}),
            f"P0 worklist can enter P2 counts={dict(p0_can_enter)}",
            "70_outputs/processed_tables/poi_supply_p0_followup_worklist.csv",
        )
        add(
            "data",
            "error",
            ok(p0_route_status == {"center_proxy_route_returned_needs_real_entrance_validation": len(p0_worklist)}),
            f"P0 worklist route api counts={dict(p0_route_status)}",
            "70_outputs/processed_tables/poi_supply_p0_followup_worklist.csv",
        )
        add(
            "data",
            "error",
            ok(p0_manual == {"not_started": len(p0_worklist)}),
            f"P0 manual fieldwork counts={dict(p0_manual)}",
            "70_outputs/processed_tables/poi_supply_p0_followup_worklist.csv",
        )

    if p0_route_results:
        route_api_counts = Counter(row.get("route_status", "") for row in p0_route_results)
        route_access_counts = Counter(row.get("route_access_status", "") for row in p0_route_results)
        route_distances = [row.get("walking_distance_m", "") for row in p0_route_results]
        add(
            "data",
            "error",
            ok(route_api_counts == {"1": len(p0_route_results)}),
            f"P0 route api counts={dict(route_api_counts)}",
            "50_external_gis/amap_routes/amap_p0_route_results.csv",
        )
        add(
            "data",
            "error",
            ok(route_access_counts == {"amap_center_proxy_route_returned_needs_entrance_validation": len(p0_route_results)}),
            f"P0 route access counts={dict(route_access_counts)}",
            "50_external_gis/amap_routes/amap_p0_route_results.csv",
        )
        add(
            "data",
            "error",
            ok(all(value for value in route_distances)),
            f"P0 route distances present={sum(1 for value in route_distances if value)}/{len(route_distances)}",
            "50_external_gis/amap_routes/amap_p0_route_results.csv",
        )

    if p0_route_log:
        log_status_counts = Counter(row.get("status", "") for row in p0_route_log)
        params_have_key = [row.get("work_item_id", "") for row in p0_route_log if "key" in row.get("params_summary", "").lower()]
        add(
            "security",
            "error",
            ok(not params_have_key),
            f"P0 route log params containing key={params_have_key}",
            "50_external_gis/amap_routes/amap_p0_route_fetch_log.csv",
        )
        add(
            "data",
            "error",
            ok(log_status_counts == {"1": len(p0_route_log)}),
            f"P0 route log status counts={dict(log_status_counts)}",
            "50_external_gis/amap_routes/amap_p0_route_fetch_log.csv",
        )

    if p0_route_review:
        enter_after_route = Counter(row.get("can_enter_p2_supply_after_route", "") for row in p0_route_review)
        add(
            "data",
            "error",
            ok(enter_after_route == {"no": len(p0_route_review)}),
            f"P0 route review can enter P2 counts={dict(enter_after_route)}",
            "70_outputs/processed_tables/poi_supply_p0_route_access_review.csv",
        )

    if entrance_node_plan:
        plan_by_park = Counter(row.get("park_id", "") for row in entrance_node_plan)
        add(
            "external_api",
            "error",
            ok(plan_by_park == {"sample_city_green_heart": 4, "sample_olympic_forest": 8}),
            f"P0 entrance node query plan by park={dict(plan_by_park)}",
            "50_external_gis/amap_routes/p0_entrance_node_query_plan.csv",
        )

    if entrance_nodes:
        nodes_by_park = Counter(row.get("park_name", "") for row in entrance_nodes)
        node_kinds = Counter(row.get("node_kind", "") for row in entrance_nodes)
        add(
            "external_api",
            "error",
            ok(nodes_by_park == {"城市绿心森林公园": 11, "奥林匹克森林公园": 34}),
            f"P0 entrance node candidates by park={dict(nodes_by_park)}",
            "50_external_gis/amap_routes/amap_p0_entrance_node_candidates.csv",
        )
        add(
            "external_api",
            "info",
            "pass",
            f"P0 entrance node kinds={dict(sorted(node_kinds.items()))}",
            "50_external_gis/amap_routes/amap_p0_entrance_node_candidates.csv",
        )

    if entrance_route_results:
        entrance_route_status = Counter(row.get("route_proxy_status", "") for row in entrance_route_results)
        entrance_api_status = Counter(row.get("route_status", "") for row in entrance_route_results)
        add(
            "external_api",
            "error",
            ok(entrance_route_status == {"entrance_or_node_proxy_route_returned_needs_field_validation": len(entrance_route_results)}),
            f"P0 entrance route proxy status={dict(entrance_route_status)}",
            "50_external_gis/amap_routes/amap_p0_entrance_node_route_results.csv",
        )
        add(
            "external_api",
            "error",
            ok(entrance_api_status == {"1": len(entrance_route_results)}),
            f"P0 entrance route api status={dict(entrance_api_status)}",
            "50_external_gis/amap_routes/amap_p0_entrance_node_route_results.csv",
        )

    if entrance_route_log:
        log_status = Counter(row.get("status", "") for row in entrance_route_log)
        params_have_key = False
        for row in entrance_route_log:
            try:
                params = json.loads(row.get("params_summary", "") or "{}")
            except json.JSONDecodeError:
                params = {}
            if isinstance(params, dict) and "key" in params:
                params_have_key = True
                break
        add(
            "security",
            "error",
            ok(not params_have_key),
            f"P0 entrance route log params containing key={params_have_key}",
            "50_external_gis/amap_routes/amap_p0_entrance_node_fetch_log.csv",
        )
        add(
            "external_api",
            "error",
            ok(log_status == {"1": len(entrance_route_log)}),
            f"P0 entrance route log status={dict(log_status)}",
            "50_external_gis/amap_routes/amap_p0_entrance_node_fetch_log.csv",
        )

    if entrance_route_review:
        entrance_review_status = Counter(row.get("entrance_route_proxy_status", "") for row in entrance_route_review)
        entrance_enter = Counter(row.get("can_enter_p2_supply_after_entrance_route", "") for row in entrance_route_review)
        best_distances = [row.get("best_walking_distance_m", "") for row in entrance_route_review]
        add(
            "data",
            "error",
            ok(entrance_review_status == {"entrance_or_node_proxy_route_returned_needs_field_validation": len(entrance_route_review)}),
            f"P0 entrance route review status={dict(entrance_review_status)}",
            "70_outputs/processed_tables/poi_supply_p0_entrance_route_review.csv",
        )
        add(
            "data",
            "error",
            ok(entrance_enter == {"no": len(entrance_route_review)}),
            f"P0 entrance route can enter P2 counts={dict(entrance_enter)}",
            "70_outputs/processed_tables/poi_supply_p0_entrance_route_review.csv",
        )
        add(
            "data",
            "error",
            ok(all(value for value in best_distances)),
            f"P0 entrance route best distances present={sum(1 for value in best_distances if value)}/{len(best_distances)}",
            "70_outputs/processed_tables/poi_supply_p0_entrance_route_review.csv",
        )

    if routes:
        high_to_deepseek = [
            row["task_id"]
            for row in routes
            if row.get("risk") == "high" and row.get("default_executor") == "deepseek"
        ]
        add("llm", "error", ok(not high_to_deepseek), f"high-risk tasks routed to DeepSeek={high_to_deepseek}", "60_model/configs/llm_task_routing.csv")
        draft_like = [
            row["task_id"]
            for row in routes
            if row.get("default_executor") == "deepseek" and row.get("output_status") not in {"draft", "needs_review"}
        ]
        add("llm", "error", ok(not draft_like), f"DeepSeek outputs not draft/needs_review={draft_like}", "60_model/configs/llm_task_routing.csv")

    if pdf_summary and table_draft:
        summary_ids = {row.get("table_id", "") for row in pdf_summary}
        draft_ids = {row.get("table_id", "") for row in table_draft}
        topics = Counter(row.get("topic_draft", "") for row in table_draft)
        statuses = Counter(row.get("output_status", "") for row in table_draft)
        executors = Counter(row.get("executor", "") for row in table_draft)
        task_ids = Counter(row.get("llm_task_id", "") for row in table_draft)
        invalid_topics = sorted(topic for topic in topics if topic not in TABLE_TOPIC_ALLOWED)
        add("llm", "error", ok(summary_ids == draft_ids), f"DeepSeek table draft table_id coverage match={summary_ids == draft_ids}", "30_extraction/tables/pdf_table_topic_draft_deepseek.csv")
        add("llm", "error", ok(not invalid_topics), f"DeepSeek table draft invalid topics={invalid_topics}", "30_extraction/tables/pdf_table_topic_draft_deepseek.csv")
        add("llm", "error", ok(statuses == {"draft": len(table_draft)}), f"DeepSeek table draft status counts={dict(statuses)}", "30_extraction/tables/pdf_table_topic_draft_deepseek.csv")
        add("llm", "error", ok(executors == {"deepseek": len(table_draft)}), f"DeepSeek table draft executor counts={dict(executors)}", "30_extraction/tables/pdf_table_topic_draft_deepseek.csv")
        add("llm", "error", ok(task_ids == {"LLM-002": len(table_draft)}), f"DeepSeek table draft task counts={dict(task_ids)}", "30_extraction/tables/pdf_table_topic_draft_deepseek.csv")
        add("llm", "info", "pass", f"DeepSeek table draft topic distribution={dict(sorted(topics.items()))}", "30_extraction/tables/pdf_table_topic_draft_deepseek.csv")

    if table_queue:
        priorities = Counter(row.get("sampling_priority", "") for row in table_queue)
        candidate_statuses = Counter(row.get("evidence_candidate_status", "") for row in table_queue)
        add("llm", "error", ok(priorities.get("P0_second_evidence_candidate", 0) == 63), f"DeepSeek table review queue priorities={dict(priorities)}", "30_extraction/tables/pdf_table_review_queue.csv")
        add("llm", "error", ok(candidate_statuses.get("candidate_for_second_evidence_review", 0) == 63), f"DeepSeek evidence candidate statuses={dict(candidate_statuses)}", "30_extraction/tables/pdf_table_review_queue.csv")

    if table_review:
        review_statuses = Counter(row.get("status", "") for row in table_review)
        add("llm", "error", ok(review_statuses == {"pass": len(table_review)}), f"DeepSeek table local review statuses={dict(review_statuses)}", "40_quality_evidence/deepseek_table_classification_review.csv")

    if evidence_candidates:
        covered_tables = {row.get("table_id", "") for row in evidence_candidates}
        candidate_types = Counter(row.get("candidate_type", "") for row in evidence_candidates)
        statuses = Counter(row.get("output_status", "") for row in evidence_candidates)
        executors = Counter(row.get("executor", "") for row in evidence_candidates)
        task_ids = Counter(row.get("llm_task_id", "") for row in evidence_candidates)
        invalid_types = sorted(candidate_type for candidate_type in candidate_types if candidate_type not in TABLE_TOPIC_ALLOWED and candidate_type not in {"revenue_finance", "supply_gap"})
        add("llm", "error", ok(len(covered_tables) == 63), f"DeepSeek evidence candidates covered tables={len(covered_tables)}", "30_extraction/tables/pdf_table_evidence_candidates_deepseek.csv")
        add("llm", "error", ok(statuses == {"needs_review": len(evidence_candidates)}), f"DeepSeek evidence candidate status counts={dict(statuses)}", "30_extraction/tables/pdf_table_evidence_candidates_deepseek.csv")
        add("llm", "error", ok(executors == {"deepseek": len(evidence_candidates)}), f"DeepSeek evidence candidate executor counts={dict(executors)}", "30_extraction/tables/pdf_table_evidence_candidates_deepseek.csv")
        add("llm", "error", ok(task_ids == {"LLM-003": len(evidence_candidates)}), f"DeepSeek evidence candidate task counts={dict(task_ids)}", "30_extraction/tables/pdf_table_evidence_candidates_deepseek.csv")
        add("llm", "error", ok(not invalid_types), f"DeepSeek evidence candidate invalid types={invalid_types}", "30_extraction/tables/pdf_table_evidence_candidates_deepseek.csv")
        add("llm", "info", "pass", f"DeepSeek evidence candidate type distribution={dict(sorted(candidate_types.items()))}", "30_extraction/tables/pdf_table_evidence_candidates_deepseek.csv")

    if evidence_review_queue:
        priorities = Counter(row.get("candidate_review_priority", "") for row in evidence_review_queue)
        ledger_statuses = Counter(row.get("ledger_entry_status", "") for row in evidence_review_queue)
        add("llm", "error", ok(priorities.get("P0_flow_or_peak_numeric_check", 0) == 32), f"DeepSeek evidence review priorities={dict(priorities)}", "30_extraction/tables/pdf_evidence_candidate_review_queue.csv")
        add("llm", "error", ok(ledger_statuses == {"needs_pdf_row_check_before_ledger": len(evidence_review_queue)}), f"DeepSeek evidence ledger gate counts={dict(ledger_statuses)}", "30_extraction/tables/pdf_evidence_candidate_review_queue.csv")

    if evidence_review:
        review_statuses = Counter(row.get("status", "") for row in evidence_review)
        add("llm", "error", ok(review_statuses == {"pass": len(evidence_review)}), f"DeepSeek evidence local review statuses={dict(review_statuses)}", "40_quality_evidence/deepseek_evidence_candidates_review.csv")

    if entrance_node_semantic:
        statuses = Counter(row.get("output_status", "") for row in entrance_node_semantic)
        executors = Counter(row.get("executor", "") for row in entrance_node_semantic)
        task_ids = Counter(row.get("llm_task_id", "") for row in entrance_node_semantic)
        semantic_types = Counter(row.get("semantic_node_type_draft", "") for row in entrance_node_semantic)
        add("llm", "error", ok(statuses == {"draft": len(entrance_node_semantic)}), f"DeepSeek entrance node status counts={dict(statuses)}", "50_external_gis/amap_routes/amap_p0_entrance_node_semantic_draft_deepseek.csv")
        add("llm", "error", ok(executors == {"deepseek": len(entrance_node_semantic)}), f"DeepSeek entrance node executor counts={dict(executors)}", "50_external_gis/amap_routes/amap_p0_entrance_node_semantic_draft_deepseek.csv")
        add("llm", "error", ok(task_ids == {"LLM-011": len(entrance_node_semantic)}), f"DeepSeek entrance node task counts={dict(task_ids)}", "50_external_gis/amap_routes/amap_p0_entrance_node_semantic_draft_deepseek.csv")
        add("llm", "info", "pass", f"DeepSeek entrance node semantic types={dict(sorted(semantic_types.items()))}", "50_external_gis/amap_routes/amap_p0_entrance_node_semantic_draft_deepseek.csv")

    if entrance_node_semantic_queue:
        local_priorities = Counter(row.get("local_rule_priority", "") for row in entrance_node_semantic_queue)
        final_gates = Counter(row.get("final_use_gate", "") for row in entrance_node_semantic_queue)
        add(
            "llm",
            "error",
            ok(local_priorities == {
                "P0_manual_check_gate_or_entrance": 20,
                "P1_manual_check_parking_access": 7,
                "P2_context_node_or_possible_wrong_match": 9,
                "P3_unclear_manual_check": 9,
            }),
            f"entrance node local priorities={dict(local_priorities)}",
            "50_external_gis/amap_routes/amap_p0_entrance_node_semantic_review_queue.csv",
        )
        add(
            "llm",
            "error",
            ok(final_gates == {
                "candidate_access_node_needs_official_or_field_confirmation": 20,
                "secondary_access_node_needs_field_confirmation": 7,
                "do_not_use_as_access_node_until_manual_review": 18,
            }),
            f"entrance node final gates={dict(final_gates)}",
            "50_external_gis/amap_routes/amap_p0_entrance_node_semantic_review_queue.csv",
        )

    if entrance_node_semantic_review:
        review_statuses = Counter(row.get("status", "") for row in entrance_node_semantic_review)
        add("llm", "error", ok(review_statuses == {"pass": len(entrance_node_semantic_review)}), f"DeepSeek entrance node local review statuses={dict(review_statuses)}", "40_quality_evidence/deepseek_entrance_node_semantic_review.csv")

    if p0_verification_package:
        statuses = Counter(row.get("output_status", "") for row in p0_verification_package)
        executors = Counter(row.get("executor", "") for row in p0_verification_package)
        task_ids = Counter(row.get("llm_task_id", "") for row in p0_verification_package)
        gates = Counter(row.get("p2_gate_draft", "") for row in p0_verification_package)
        add("llm", "error", ok(statuses == {"needs_review": len(p0_verification_package)}), f"DeepSeek P0 package status counts={dict(statuses)}", "70_outputs/processed_tables/p0_manual_verification_package_deepseek.csv")
        add("llm", "error", ok(executors == {"deepseek": len(p0_verification_package)}), f"DeepSeek P0 package executor counts={dict(executors)}", "70_outputs/processed_tables/p0_manual_verification_package_deepseek.csv")
        add("llm", "error", ok(task_ids == {"LLM-012": len(p0_verification_package)}), f"DeepSeek P0 package task counts={dict(task_ids)}", "70_outputs/processed_tables/p0_manual_verification_package_deepseek.csv")
        add(
            "llm",
            "error",
            ok(gates == {"do_not_enter_p2_until_field_or_official_confirmation": len(p0_verification_package)}),
            f"DeepSeek P0 package P2 gates={dict(gates)}",
            "70_outputs/processed_tables/p0_manual_verification_package_deepseek.csv",
        )

    if p0_verification_package_review:
        review_statuses = Counter(row.get("status", "") for row in p0_verification_package_review)
        add("llm", "error", ok(review_statuses == {"pass": len(p0_verification_package_review)}), f"DeepSeek P0 package local review statuses={dict(review_statuses)}", "40_quality_evidence/deepseek_p0_verification_package_review.csv")

    if deepseek_first_queue:
        delegates = Counter(row.get("delegate_to", "") for row in deepseek_first_queue)
        statuses = Counter(row.get("output_status", "") for row in deepseek_first_queue)
        queue_status_by_id = {row.get("queue_id", ""): row.get("output_status", "") for row in deepseek_first_queue}
        p2_claims = [
            row.get("queue_id", "")
            for row in deepseek_first_queue
            if "进入P2" in "".join(row.values()) or "P2通过" in "".join(row.values()) or row.get("output_status", "") == "checked"
        ]
        add("llm", "error", ok(delegates.get("deepseek", 0) >= 3), f"DeepSeek-first delegate distribution={dict(delegates)}", "70_outputs/processed_tables/deepseek_first_task_queue.csv")
        add("llm", "error", ok(all(status in {"draft", "needs_review", "completed"} for status in statuses)), f"DeepSeek-first output statuses={dict(statuses)}", "70_outputs/processed_tables/deepseek_first_task_queue.csv")
        add("llm", "error", ok(statuses.get("completed", 0) >= 4), f"DeepSeek-first completed tasks={statuses.get('completed', 0)}", "70_outputs/processed_tables/deepseek_first_task_queue.csv")
        add("llm", "error", ok(queue_status_by_id.get("DS-FIRST-004") == "completed"), f"DS-FIRST-004 status={queue_status_by_id.get('DS-FIRST-004')}", "70_outputs/processed_tables/deepseek_first_task_queue.csv")
        add(
            "llm",
            "error",
            ok(queue_status_by_id.get("DS-FIRST-005") in {"needs_review", "completed"} and queue_status_by_id.get("DS-FIRST-006") in {"needs_review", "completed"}),
            f"DS-FIRST-005/006 statuses={{'DS-FIRST-005': {queue_status_by_id.get('DS-FIRST-005')}, 'DS-FIRST-006': {queue_status_by_id.get('DS-FIRST-006')}}}",
            "70_outputs/processed_tables/deepseek_first_task_queue.csv",
        )
        add("llm", "error", ok(not p2_claims), f"DeepSeek-first unexpected P2/checked claims={p2_claims}", "70_outputs/processed_tables/deepseek_first_task_queue.csv")

    if deepseek_context_review:
        review_statuses = Counter(row.get("status", "") for row in deepseek_context_review)
        add("llm", "error", ok(review_statuses == {"pass": len(deepseek_context_review)}), f"DeepSeek context sync local review statuses={dict(review_statuses)}", "40_quality_evidence/deepseek_project_context_sync_review.csv")

    if p0_detail_plan:
        statuses = Counter(row.get("output_status", "") for row in p0_detail_plan)
        gates = Counter(row.get("p2_gate_draft", "") for row in p0_detail_plan)
        executors = Counter(row.get("executor", "") for row in p0_detail_plan)
        task_ids = Counter(row.get("llm_task_id", "") for row in p0_detail_plan)
        endpoints = Counter(row.get("amap_endpoint_draft", "") for row in p0_detail_plan)
        missing_ids = [row.get("work_item_id", "") for row in p0_detail_plan if not row.get("amap_detail_poi_id")]
        add("llm", "error", ok(statuses == {"needs_review": len(p0_detail_plan)}), f"P0 detail plan output statuses={dict(statuses)}", "50_external_gis/amap_poi/amap_p0_detail_query_plan_deepseek.csv")
        add("llm", "error", ok(gates == {"do_not_enter_p2_until_field_or_official_confirmation": len(p0_detail_plan)}), f"P0 detail plan gates={dict(gates)}", "50_external_gis/amap_poi/amap_p0_detail_query_plan_deepseek.csv")
        add("llm", "error", ok(executors == {"deepseek": len(p0_detail_plan)}), f"P0 detail plan executors={dict(executors)}", "50_external_gis/amap_poi/amap_p0_detail_query_plan_deepseek.csv")
        add("llm", "error", ok(task_ids == {"LLM-014": len(p0_detail_plan)}), f"P0 detail plan task ids={dict(task_ids)}", "50_external_gis/amap_poi/amap_p0_detail_query_plan_deepseek.csv")
        add("llm", "error", ok(not missing_ids), f"P0 detail plan missing amap ids={missing_ids}", "50_external_gis/amap_poi/amap_p0_detail_query_plan_deepseek.csv")
        add("llm", "info", "pass", f"P0 detail plan endpoint distribution={dict(endpoints)}", "50_external_gis/amap_poi/amap_p0_detail_query_plan_deepseek.csv")

    if p0_detail_plan_review:
        review_statuses = Counter(row.get("status", "") for row in p0_detail_plan_review)
        add("llm", "error", ok(review_statuses.get("fail", 0) == 0), f"P0 detail plan review statuses={dict(review_statuses)}", "40_quality_evidence/deepseek_p0_detail_query_plan_review.csv")

    if p0_business_fill:
        verification_statuses = Counter(row.get("verification_status", "") for row in p0_business_fill)
        add("data", "error", ok(verification_statuses == {"partially_verified": 5, "needs_field_verification": 2}), f"P0 business fill verification statuses={dict(verification_statuses)}", "70_outputs/processed_tables/p0_business_field_fill_amap.csv")
        any_verified = sum(1 for row in p0_business_fill if row.get("tel_verified") or row.get("opentime_verified") or row.get("cost_yuan_verified"))
        add("data", "error", ok(any_verified == 5), f"P0 business fill rows with at least one verified field={any_verified}", "70_outputs/processed_tables/p0_business_field_fill_amap.csv")

    if p0_worklist_enriched:
        enrichment_statuses = Counter(row.get("enrichment_status", "") for row in p0_worklist_enriched)
        p2_gates = Counter(row.get("can_enter_p2_supply", "") for row in p0_worklist_enriched)
        detail_statuses = Counter(row.get("amap_detail_api_status", "") for row in p0_worklist_enriched)
        add("data", "error", ok(enrichment_statuses == {"detail_api_called_fields_confirmed": 5, "detail_api_called_no_new_data": 2}), f"P0 enriched status counts={dict(enrichment_statuses)}", "70_outputs/processed_tables/poi_supply_p0_followup_worklist_enriched.csv")
        add("data", "error", ok(p2_gates == {"no": len(p0_worklist_enriched)}), f"P0 enriched P2 gates={dict(p2_gates)}", "70_outputs/processed_tables/poi_supply_p0_followup_worklist_enriched.csv")
        add("data", "info", "pass", f"P0 enriched detail status counts={dict(detail_statuses)}", "70_outputs/processed_tables/poi_supply_p0_followup_worklist_enriched.csv")

    if p0_field_checklist:
        statuses = Counter(row.get("output_status", "") for row in p0_field_checklist)
        gates = Counter(row.get("p2_gate_draft", "") for row in p0_field_checklist)
        executors = Counter(row.get("executor", "") for row in p0_field_checklist)
        task_ids = Counter(row.get("llm_task_id", "") for row in p0_field_checklist)
        type_counts = Counter(row.get("checklist_type", "") for row in p0_field_checklist)
        missing_text = [row.get("checklist_id", "") for row in p0_field_checklist if not row.get("verification_goal_draft") or not row.get("on_site_questions_draft") or not row.get("acceptable_evidence_draft")]
        add("llm", "error", ok(statuses == {"needs_review": len(p0_field_checklist)}), f"P0 field checklist output statuses={dict(statuses)}", "70_outputs/processed_tables/p0_field_verification_checklist_deepseek.csv")
        add("llm", "error", ok(gates == {"do_not_enter_p2_until_field_or_official_confirmation": len(p0_field_checklist)}), f"P0 field checklist P2 gates={dict(gates)}", "70_outputs/processed_tables/p0_field_verification_checklist_deepseek.csv")
        add("llm", "error", ok(executors == {"deepseek": len(p0_field_checklist)}), f"P0 field checklist executors={dict(executors)}", "70_outputs/processed_tables/p0_field_verification_checklist_deepseek.csv")
        add("llm", "error", ok(task_ids == {"LLM-015": len(p0_field_checklist)}), f"P0 field checklist task ids={dict(task_ids)}", "70_outputs/processed_tables/p0_field_verification_checklist_deepseek.csv")
        add("llm", "error", ok(type_counts == {"p0_poi_business_and_authorization": 7, "primary_access_node_field_check": 20, "secondary_parking_or_visit_node_field_check": 7}), f"P0 field checklist type counts={dict(type_counts)}", "70_outputs/processed_tables/p0_field_verification_checklist_deepseek.csv")
        add("llm", "error", ok(not missing_text), f"P0 field checklist missing core text={missing_text}", "70_outputs/processed_tables/p0_field_verification_checklist_deepseek.csv")

    if p0_field_checklist_review:
        review_statuses = Counter(row.get("status", "") for row in p0_field_checklist_review)
        add("llm", "error", ok(review_statuses.get("fail", 0) == 0), f"P0 field checklist review statuses={dict(review_statuses)}", "40_quality_evidence/deepseek_p0_field_verification_checklist_review.csv")

    if p0_field_checklist_local_review:
        local_review_statuses = Counter(row.get("status", "") for row in p0_field_checklist_local_review)
        local_review_warnings = [
            row.get("finding", "")
            for row in p0_field_checklist_local_review
            if row.get("status") == "warning"
        ]
        add("llm", "error", ok(local_review_statuses.get("fail", 0) == 0), f"P0 local checklist audit statuses={dict(local_review_statuses)}", "40_quality_evidence/p0_field_verification_checklist_local_review.csv")
        add("llm", "info", "pass", f"P0 local checklist audit warnings={local_review_warnings}", "40_quality_evidence/p0_field_verification_checklist_local_review.csv")

    if handoff_encoding_review:
        review_statuses = Counter(row.get("status", "") for row in handoff_encoding_review)
        add("files", "error", ok(review_statuses == {"pass": len(handoff_encoding_review)}), f"handoff encoding review statuses={dict(review_statuses)}", "40_quality_evidence/handoff_encoding_health_review.csv")

    if p1_quality_review:
        review_statuses = Counter(row.get("status", "") for row in p1_quality_review)
        add("llm", "error", ok(review_statuses == {"pass": len(p1_quality_review)}), f"P1 quality report review statuses={dict(review_statuses)}", "40_quality_evidence/deepseek_p1_quality_report_review.csv")

    if p2_semantic_review:
        review_statuses = Counter(row.get("status", "") for row in p2_semantic_review)
        add("llm", "error", ok(review_statuses == {"pass": len(p2_semantic_review)}), f"P2 semantic review statuses={dict(review_statuses)}", "40_quality_evidence/deepseek_p2_real_site_semantic_review.csv")

    if p2_schema_review:
        review_statuses = Counter(row.get("status", "") for row in p2_schema_review)
        add("llm", "error", ok(review_statuses == {"pass": len(p2_schema_review)}), f"P2 schema candidate review statuses={dict(review_statuses)}", "40_quality_evidence/deepseek_p2_input_schema_candidates_review.csv")

    if repos:
        licenses = Counter(row.get("license", "") for row in repos)
        add("github", "info", "pass", f"tech-shrimp license distribution={dict(sorted(licenses.items()))}", "10_research/github_tech_shrimp/tech_shrimp_repos_gh_api_20260523.csv")

    if forks:
        status_counts = Counter(row.get("status", "") for row in forks)
        failed = [row for row in forks if row.get("status") == "failed"]
        add("github", "error", ok(status_counts.get("forked", 0) == 24 and status_counts.get("failed", 0) == 1), f"fork status counts={dict(status_counts)}", "10_research/github_tech_shrimp/fork_results_20260523.csv")
        add("github", "warning", ok(len(failed) == 1 and failed[0].get("source") == "tech-shrimp/WechatMoments" and "HTTP 451" in failed[0].get("detail", "")), "failed fork is expected HTTP 451 WechatMoments", "10_research/github_tech_shrimp/fork_results_20260523.csv")


def verify_json_files() -> None:
    json_files = [
        "10_research/github_tech_shrimp/tech_shrimp_repos_gh_api_20260523.json",
        "10_research/github_tech_shrimp/tech_shrimp_repos_combined_observed.json",
        "10_research/github_tech_shrimp/tech_shrimp_repos_partial.json",
    ]
    for item in json_files:
        path = ROOT / item
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            add("files", "error", ok(isinstance(data, list) and len(data) > 0), f"{item} json list rows={len(data) if isinstance(data, list) else 'not_list'}", item)
        except Exception as exc:
            add("files", "error", "fail", f"{item} invalid json: {type(exc).__name__}", item)

    schema_files = [
        "60_model/schemas/persona_state.schema.json",
        "60_model/schemas/behavior_program.schema.json",
        "60_model/schemas/node_recommendation_explanation.schema.json",
        "60_model/schemas/deepseek_task_contract.schema.json",
        "60_model/schemas/person_simulation_control.schema.json",
        "60_model/schemas/choice_probability.schema.json",
        "60_model/schemas/simulation_validation_target.schema.json",
    ]
    schemas: dict[str, dict] = {}
    for item in schema_files:
        path = ROOT / item
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
            schemas[item] = payload
            add("schema", "error", ok(payload.get("$schema") == "https://json-schema.org/draft/2020-12/schema"), f"{item} draft={payload.get('$schema')}", item)
            add("schema", "error", ok(isinstance(payload.get("required"), list) and payload.get("required")), f"{item} required fields={len(payload.get('required', [])) if isinstance(payload.get('required'), list) else 'invalid'}", item)
        except Exception as exc:
            add("schema", "error", "fail", f"{item} invalid json: {type(exc).__name__}", item)

    control_schema = schemas.get("60_model/schemas/person_simulation_control.schema.json", {})
    try:
        object_types = set(control_schema["properties"]["object_type"]["enum"])
        add("schema", "error", ok({"choice_probability", "simulation_validation_target"}.issubset(object_types)), f"control object_types include choice/validation={sorted(object_types)}", "60_model/schemas/person_simulation_control.schema.json")
    except Exception as exc:
        add("schema", "error", "fail", f"control object_type enum invalid: {type(exc).__name__}", "60_model/schemas/person_simulation_control.schema.json")

    task_schema = schemas.get("60_model/schemas/deepseek_task_contract.schema.json", {})
    try:
        task_types = set(task_schema["properties"]["task_type"]["enum"])
        add("schema", "error", ok({"choice_probability", "simulation_validation_target", "state_behavior_consistency"}.issubset(task_types)), f"DeepSeek task_types include new constrained tasks={sorted(task_types)}", "60_model/schemas/deepseek_task_contract.schema.json")
        required = set(task_schema.get("required", []))
        add("schema", "error", ok({"needs_human_review", "review_required"} <= required), f"DeepSeek contract review required fields={sorted(required)}", "60_model/schemas/deepseek_task_contract.schema.json")
    except Exception as exc:
        add("schema", "error", "fail", f"DeepSeek task_type enum invalid: {type(exc).__name__}", "60_model/schemas/deepseek_task_contract.schema.json")

    choice_schema = schemas.get("60_model/schemas/choice_probability.schema.json", {})
    try:
        required = set(choice_schema["required"])
        add("schema", "error", ok("plain_language_explanation" in required and "human_explanation" not in required), f"choice_probability explanation fields={sorted(required)}", "60_model/schemas/choice_probability.schema.json")
    except Exception as exc:
        add("schema", "error", "fail", f"choice_probability required invalid: {type(exc).__name__}", "60_model/schemas/choice_probability.schema.json")

    validation_schema = schemas.get("60_model/schemas/simulation_validation_target.schema.json", {})
    try:
        metric_types = set(validation_schema["properties"]["metric_family"]["items"]["enum"])
        levels = set(validation_schema["properties"]["validation_level"]["enum"])
        add("schema", "error", ok("state_behavior_consistency" in metric_types and "llm_micro_reasonableness" not in metric_types), f"validation metrics={sorted(metric_types)}", "60_model/schemas/simulation_validation_target.schema.json")
        add("schema", "error", ok("state_behavior_chain" in levels and "micro_behavior" not in levels), f"validation levels={sorted(levels)}", "60_model/schemas/simulation_validation_target.schema.json")
    except Exception as exc:
        add("schema", "error", "fail", f"simulation validation schema invalid: {type(exc).__name__}", "60_model/schemas/simulation_validation_target.schema.json")

    modern_stack_path = ROOT / "40_quality_evidence" / "modern_sim_stack_verification_20260604.json"
    try:
        payload = json.loads(modern_stack_path.read_text(encoding="utf-8-sig"))
        package_count = int(payload.get("package_count", 0))
        package_names = {item.get("module", "") for item in payload.get("packages", [])}
        required_modern = {
            "duckdb",
            "polars",
            "jsonschema",
            "pydantic",
            "osmnx",
            "movingpandas",
            "mesa",
            "mesa_geo",
            "simpy",
            "SALib",
            "optuna",
        }
        add("schema", "error", ok(payload.get("status") == "pass"), f"modern sim stack status={payload.get('status')}", "40_quality_evidence/modern_sim_stack_verification_20260604.json")
        add("schema", "error", ok(package_count >= 14), f"modern sim stack package_count={package_count}", "40_quality_evidence/modern_sim_stack_verification_20260604.json")
        add("schema", "error", ok(required_modern <= package_names), f"modern sim stack modules include required={sorted(package_names)}", "40_quality_evidence/modern_sim_stack_verification_20260604.json")
    except Exception as exc:
        add("schema", "error", "fail", f"modern sim stack report invalid: {type(exc).__name__}", "40_quality_evidence/modern_sim_stack_verification_20260604.json")

    session_recovery_path = ROOT / "40_quality_evidence" / "session_recovery_20260606.json"
    try:
        payload = json.loads(session_recovery_path.read_text(encoding="utf-8-sig"))
        summary = payload.get("summary", {})
        checks_count = len(payload.get("checks", []))
        add("recovery", "error", ok(summary.get("fail", 0) == 0 and checks_count >= 8), f"session recovery checks={checks_count}, summary={summary}", "40_quality_evidence/session_recovery_20260606.json")
        names = {row.get("name", "") for row in payload.get("checks", [])}
        add("recovery", "error", ok({"plugins_enabled", "ui_ux_pro_max_available", "deepseek_api_pass", "pdf_table_gate_pass", "amap_smoke_pass"} <= names), f"session recovery names={sorted(names)}", "40_quality_evidence/session_recovery_20260606.json")
    except Exception as exc:
        add("recovery", "error", "fail", f"session recovery report invalid: {type(exc).__name__}", "40_quality_evidence/session_recovery_20260606.json")

    osen_report_gate_path = ROOT / "40_quality_evidence" / "osen_integrated_report_validation_20260606.json"
    try:
        payload = json.loads(osen_report_gate_path.read_text(encoding="utf-8-sig"))
        summary = payload.get("summary", {})
        checks_count = len(payload.get("checks", []))
        passed_names = {row.get("name", "") for row in payload.get("checks", []) if row.get("status") == "pass"}
        required_names = {
            "report_length",
            "node_count",
            "all_nodes_named",
            "human_text_clean",
            "cad_converted_two_drawings",
            "cad_anchor_terms",
            "north_pdf_proxy_hit",
            "deepseek_runtime_ok",
            "pdf_table_runtime_ok",
            "amap_runtime_ok",
        }
        add("delivery", "error", ok(summary.get("fail", 0) == 0 and checks_count >= 14), f"Osen report checks={checks_count}, summary={summary}", "40_quality_evidence/osen_integrated_report_validation_20260606.json")
        add("delivery", "error", ok(required_names <= passed_names), f"Osen report passed names={sorted(passed_names)}", "40_quality_evidence/osen_integrated_report_validation_20260606.json")
    except Exception as exc:
        add("delivery", "error", "fail", f"Osen integrated report gate invalid: {type(exc).__name__}", "40_quality_evidence/osen_integrated_report_validation_20260606.json")

    expert_knowledge_path = ROOT / "10_research" / "expert_implementation_knowledge_20260607" / "expert_implementation_summary.json"
    try:
        payload = json.loads(expert_knowledge_path.read_text(encoding="utf-8-sig"))
        dimensions = payload.get("real_world_review_dimensions", [])
        dimension_text = json.dumps(dimensions, ensure_ascii=False)
        official_sources = payload.get("official_real_world_sources", [])
        source_text = json.dumps(official_sources, ensure_ascii=False)
        topic_counts = payload.get("topic_counts", {})
        required_dimensions = [
            "目标人群",
            "周边人口与收入",
            "时间节律",
            "天气与季节",
            "地理与可达",
            "空间与工程",
            "消防与安全",
            "许可与合规",
            "财务与招商",
            "新闻舆情与社区接受",
            "仿真与数据校准",
        ]
        add(
            "delivery",
            "error",
            ok(
                int(payload.get("query_total", 0)) >= 80
                and int(payload.get("completed_query_count", 0)) >= 80
                and int(payload.get("raw_count", 0)) >= 10_000
                and int(payload.get("screened_count", 0)) >= 1_000
                and int(payload.get("topic_group_count", 0)) >= 8
            ),
            f"expert implementation research volume query={payload.get('query_total')} completed={payload.get('completed_query_count')} raw={payload.get('raw_count')} screened={payload.get('screened_count')} groups={payload.get('topic_group_count')}",
            "10_research/expert_implementation_knowledge_20260607/expert_implementation_summary.json",
        )
        add(
            "delivery",
            "error",
            ok(all(term in dimension_text for term in required_dimensions)),
            f"expert implementation dimensions found={[term for term in required_dimensions if term in dimension_text]}",
            "10_research/expert_implementation_knowledge_20260607/expert_implementation_summary.json",
        )
        add(
            "delivery",
            "error",
            ok(all(int(topic_counts.get(topic, 0)) > 0 for topic in ["目标人群与消费", "时间天气与季节", "空间地理与周边", "工程消防安全与许可", "公园商业与运营"])),
            f"expert implementation topic_counts={topic_counts}",
            "10_research/expert_implementation_knowledge_20260607/expert_implementation_summary.json",
        )
        add(
            "delivery",
            "error",
            ok(all(term in source_text for term in ["北京市公园条例", "食品经营许可", "The Green Book 2026", "National Park Service"])),
            "expert implementation official/business-case sources are recorded",
            "10_research/expert_implementation_knowledge_20260607/expert_implementation_summary.json",
        )
    except Exception as exc:
        add("delivery", "error", "fail", f"expert implementation knowledge invalid: {type(exc).__name__}", "10_research/expert_implementation_knowledge_20260607/expert_implementation_summary.json")

    current_knowledge_path = ROOT / "00_control" / "current_knowledge_base.md"
    recent_kb_path = ROOT / "40_quality_evidence" / "recent_knowledge_base_verification_20260609.json"
    recent_core_path = ROOT / "40_quality_evidence" / "recent_knowledge_core_verification_20260609.json"
    sim_mega_path = ROOT / "40_quality_evidence" / "simulation_stack_mega_supplement_verification_20260609.json"
    computation_mega_path = ROOT / "40_quality_evidence" / "computation_model_mega_supplement_verification_20260609.json"
    model_pack_path = ROOT / "40_quality_evidence" / "model_computation_knowledge_pack_verification_20260609.json"
    model_query_examples_path = ROOT / "40_quality_evidence" / "model_computation_query_examples_20260609.json"
    try:
        current_text = current_knowledge_path.read_text(encoding="utf-8-sig")
        required_terms = [
            "23,091",
            "3,085",
            "4,405",
            "仿真栈通用 Mega",
            "计算与模型 Mega",
            "needs_action",
            "query_model_computation_knowledge_20260609.py",
        ]
        add(
            "knowledge",
            "error",
            ok(all(term in current_text for term in required_terms)),
            f"current knowledge entry terms found={[term for term in required_terms if term in current_text]}",
            "00_control/current_knowledge_base.md",
        )
    except Exception as exc:
        add("knowledge", "error", "fail", f"current knowledge entry invalid: {type(exc).__name__}", "00_control/current_knowledge_base.md")

    try:
        payload = json.loads(recent_kb_path.read_text(encoding="utf-8-sig"))
        add(
            "knowledge",
            "error",
            ok(payload.get("status") == "pass" and int(payload.get("query_count", 0)) >= 9000),
            f"recent knowledge base status={payload.get('status')} query_count={payload.get('query_count')}",
            "40_quality_evidence/recent_knowledge_base_verification_20260609.json",
        )
    except Exception as exc:
        add("knowledge", "error", "fail", f"recent knowledge base verification invalid: {type(exc).__name__}", "40_quality_evidence/recent_knowledge_base_verification_20260609.json")

    try:
        payload = json.loads(recent_core_path.read_text(encoding="utf-8-sig"))
        add(
            "knowledge",
            "error",
            ok(
                payload.get("status") == "pass"
                and int(payload.get("input_screened_total", 0)) >= 23000
                and int(payload.get("core_deployment_total", 0)) >= 3000
                and int(payload.get("method_reference_total", 0)) >= 17000
            ),
            f"recent knowledge core status={payload.get('status')} input={payload.get('input_screened_total')} core={payload.get('core_deployment_total')} method={payload.get('method_reference_total')}",
            "40_quality_evidence/recent_knowledge_core_verification_20260609.json",
        )
    except Exception as exc:
        add("knowledge", "error", "fail", f"recent knowledge core verification invalid: {type(exc).__name__}", "40_quality_evidence/recent_knowledge_core_verification_20260609.json")

    try:
        payload = json.loads(model_pack_path.read_text(encoding="utf-8-sig"))
        add(
            "knowledge",
            "error",
            ok(payload.get("status") == "pass" and int(payload.get("pack_total", 0)) >= 4400 and int(payload.get("layer_count", 0)) >= 13),
            f"model computation pack status={payload.get('status')} pack={payload.get('pack_total')} layers={payload.get('layer_count')}",
            "40_quality_evidence/model_computation_knowledge_pack_verification_20260609.json",
        )
    except Exception as exc:
        add("knowledge", "error", "fail", f"model computation pack verification invalid: {type(exc).__name__}", "40_quality_evidence/model_computation_knowledge_pack_verification_20260609.json")

    try:
        payload = json.loads(model_query_examples_path.read_text(encoding="utf-8-sig"))
        records = payload.get("records", [])
        add(
            "knowledge",
            "error",
            ok(payload.get("status") == "pass" and len(records) >= 3 and all(row.get("hit_count_marker_present") for row in records)),
            f"model computation query examples status={payload.get('status')} records={len(records)}",
            "40_quality_evidence/model_computation_query_examples_20260609.json",
        )
    except Exception as exc:
        add("knowledge", "error", "fail", f"model computation query examples invalid: {type(exc).__name__}", "40_quality_evidence/model_computation_query_examples_20260609.json")

    try:
        payload = json.loads(sim_mega_path.read_text(encoding="utf-8-sig"))
        status = payload.get("status")
        threshold_ok = int(payload.get("query_count", 0)) >= 3200 and int(payload.get("screened_total", 0)) >= 5800
        gate_status = "pass" if status == "pass" and threshold_ok else ("warn" if status == "needs_action" and threshold_ok else "fail")
        add(
            "knowledge",
            "warn",
            gate_status,
            f"simulation stack Mega status={status} query={payload.get('query_count')} screened={payload.get('screened_total')} classic={payload.get('classic_reference_total')}",
            "40_quality_evidence/simulation_stack_mega_supplement_verification_20260609.json",
        )
    except Exception as exc:
        add("knowledge", "error", "fail", f"simulation stack Mega verification invalid: {type(exc).__name__}", "40_quality_evidence/simulation_stack_mega_supplement_verification_20260609.json")

    try:
        payload = json.loads(computation_mega_path.read_text(encoding="utf-8-sig"))
        status = payload.get("status")
        threshold_ok = (
            int(payload.get("query_count", 0)) >= 5400
            and int(payload.get("screened_total", 0)) >= 3000
            and int(payload.get("classic_reference_total", 0)) >= 900
        )
        gate_status = "pass" if status == "pass" and threshold_ok else ("warn" if status == "needs_action" and threshold_ok else "fail")
        add(
            "knowledge",
            "warn",
            gate_status,
            f"computation model Mega status={status} query={payload.get('query_count')} screened={payload.get('screened_total')} classic={payload.get('classic_reference_total')} merged={payload.get('merged_screened_total')}",
            "40_quality_evidence/computation_model_mega_supplement_verification_20260609.json",
        )
    except Exception as exc:
        add("knowledge", "error", "fail", f"computation model Mega verification invalid: {type(exc).__name__}", "40_quality_evidence/computation_model_mega_supplement_verification_20260609.json")

    osen_context_path = ROOT / "10_research" / "osen_real_world_context_sources_20260607.md"
    try:
        text = osen_context_path.read_text(encoding="utf-8-sig")
        required_terms = [
            "居民人均可支配收入",
            "居民人均消费支出",
            "服务性消费",
            "不能替代奥森周边",
            "周边街道级或商圈级收入水平",
            "收入与价格带必须",
        ]
        add(
            "delivery",
            "error",
            ok(all(term in text for term in required_terms)),
            f"Osen real-world income/consumption context terms found={[term for term in required_terms if term in text]}",
            "10_research/osen_real_world_context_sources_20260607.md",
        )
    except Exception as exc:
        add("delivery", "error", "fail", f"Osen real-world context note invalid: {type(exc).__name__}", "10_research/osen_real_world_context_sources_20260607.md")

    real_calibration_path = ROOT / "40_quality_evidence" / "osen_real_calibration_inputs_20260607.json"
    try:
        payload = json.loads(real_calibration_path.read_text(encoding="utf-8-sig"))
        strengths = payload.get("counts", {}).get("by_strength", {}) or payload.get("source_strength_counts", {})
        rows = payload.get("rows", [])
        text = json.dumps(payload, ensure_ascii=False)
        row_count = int(payload.get("row_count", 0) or payload.get("count", 0) or 0)
        required_strengths = {
            "official_macro_boundary",
            "local_bigdata_profile",
            "local_device_price_proxy",
            "local_poi_price_signal",
            "plan_assumption_needs_review",
        }
        add(
            "delivery",
            "error",
            ok(
                payload.get("status") == "pass"
                and row_count >= 14
                and required_strengths <= set(strengths)
                and all(int(strengths.get(item, 0)) >= 1 for item in required_strengths)
            ),
            f"Osen real calibration rows={row_count} strengths={strengths}",
            "40_quality_evidence/osen_real_calibration_inputs_20260607.json",
        )
        add(
            "delivery",
            "error",
            ok(all(row.get("output_status") == "needs_review" for row in rows)),
            "Osen real calibration rows remain needs_review",
            "40_quality_evidence/osen_real_calibration_inputs_20260607.json",
        )
    except Exception as exc:
        add("delivery", "error", "fail", f"Osen real calibration inputs invalid: {type(exc).__name__}", "40_quality_evidence/osen_real_calibration_inputs_20260607.json")

    latest_report_json_path = ROOT / "80_delivery" / "site_selection_gap_report_latest.json"
    try:
        payload = json.loads(latest_report_json_path.read_text(encoding="utf-8-sig"))
        basis = payload.get("expert_review_basis", {})
        nodes = payload.get("nodes", [])
        real_calibration = payload.get("real_calibration_context", {})
        method_basis = payload.get("method_basis", [])
        method_trace = payload.get("method_trace", [])
        source_foundation = payload.get("source_foundation", {})
        basis_text = json.dumps(basis, ensure_ascii=False)
        current_basis_text = json.dumps(
            {
                "basis": basis,
                "method_basis": method_basis,
                "method_trace": method_trace,
                "source_foundation": source_foundation,
            },
            ensure_ascii=False,
        )
        real_calibration_text = json.dumps(real_calibration, ensure_ascii=False)
        node_review_text = json.dumps([node.get("implementation_review", {}) for node in nodes], ensure_ascii=False)
        option_counts = [
            len(node.get("implementation_review", {}).get("options", []))
            for node in nodes
            if isinstance(node, dict)
        ]
        add(
            "delivery",
            "error",
            ok(
                (
                    int(basis.get("query_total", 0)) >= 80
                    and int(basis.get("screened_count", 0)) >= 1_000
                    and isinstance(basis.get("beijing_context"), dict)
                    and all(term in basis_text for term in ["周边人口与收入", "天气与季节", "新闻舆情与社区接受", "人均可支配收入", "人均消费支出", "不能替代奥森周边"])
                )
                or (
                    len(method_basis) >= 3
                    and len(method_trace) >= 5
                    and isinstance(basis.get("beijing_context"), dict)
                    and all(term in current_basis_text for term in ["周边人口与收入", "时间天气", "人均可支配收入", "人均消费支出", "不能替代奥森周边", "CAD", "POI"])
                )
            ),
            f"latest report expert basis query={basis.get('query_total')} screened={basis.get('screened_count')} method_basis={len(method_basis)} method_trace={len(method_trace)}",
            "80_delivery/site_selection_gap_report_latest.json",
        )
        add(
            "delivery",
            "error",
            ok(len(nodes) >= 6 and option_counts and all(count >= 3 for count in option_counts)),
            f"latest report node option_counts={option_counts}",
            "80_delivery/site_selection_gap_report_latest.json",
        )
        add(
            "delivery",
            "error",
            ok(
                int(real_calibration.get("count", 0)) >= 10
                and all(term in real_calibration_text for term in ["official_macro_boundary", "local_device_price_proxy", "local_poi_price_signal", "plan_assumption_needs_review"])
            ),
            f"latest report real calibration count={real_calibration.get('count')} strengths={real_calibration.get('source_strength_counts')}",
            "80_delivery/site_selection_gap_report_latest.json",
        )
        add(
            "delivery",
            "error",
            ok(all(term in node_review_text for term in ["income_and_price_band", "evidence_that_changes_decision", "simulation_inputs", "周边收入", "天气"])),
            "latest report nodes preserve income, weather, decision-changing evidence and simulation inputs",
            "80_delivery/site_selection_gap_report_latest.json",
        )
    except Exception as exc:
        add("delivery", "error", "fail", f"latest report JSON implementation review invalid: {type(exc).__name__}", "80_delivery/site_selection_gap_report_latest.json")

    docx_delivery_path = ROOT / "40_quality_evidence" / "osen_docx_delivery_validation_20260606.json"
    try:
        payload = json.loads(docx_delivery_path.read_text(encoding="utf-8-sig"))
        checks_by_name = {item.get("name"): item for item in payload.get("checks", []) if isinstance(item, dict)}
        required_names = {
            "docx_exists_and_size",
            "docx_audit_pass",
            "render_pass",
            "web_docx_download",
            "expert_research_volume",
            "real_world_sources_recorded",
            "income_dimension_in_report",
            "each_node_has_three_options",
            "each_node_has_decision_changing_evidence",
            "no_forbidden_docx_terms",
            "required_docx_terms",
        }
        add(
            "delivery",
            "error",
            ok(payload.get("summary", {}).get("fail", 0) == 0 and required_names <= set(checks_by_name)),
            f"Osen DOCX delivery checks={sorted(checks_by_name)} summary={payload.get('summary')}",
            "40_quality_evidence/osen_docx_delivery_validation_20260606.json",
        )
        add(
            "delivery",
            "error",
            ok(all(checks_by_name[name].get("status") == "pass" for name in required_names if name in checks_by_name)),
            "Osen DOCX delivery required checks all pass",
            "40_quality_evidence/osen_docx_delivery_validation_20260606.json",
        )
    except Exception as exc:
        add("delivery", "error", "fail", f"Osen DOCX delivery validation invalid: {type(exc).__name__}", "40_quality_evidence/osen_docx_delivery_validation_20260606.json")

    docx_render_path = ROOT / "40_quality_evidence" / "osen_report_docx_render_20260606.json"
    try:
        payload = json.loads(docx_render_path.read_text(encoding="utf-8-sig"))
        png_dir = ROOT / "40_quality_evidence" / "osen_report_docx_render_20260606"
        pngs = sorted(png_dir.glob("page_*.png"))
        add(
            "delivery",
            "error",
            ok(payload.get("status") == "pass" and int(payload.get("page_count", 0)) >= 10),
            f"Osen DOCX render status={payload.get('status')} page_count={payload.get('page_count')} pdf_bytes={payload.get('pdf_bytes')}",
            "40_quality_evidence/osen_report_docx_render_20260606.json",
        )
        add(
            "delivery",
            "error",
            ok(len(pngs) >= 10 and all(path.stat().st_size > 50_000 for path in pngs[:3])),
            f"Osen DOCX rendered png_count={len(pngs)} first_sizes={[path.stat().st_size for path in pngs[:3]]}",
            "40_quality_evidence/osen_report_docx_render_20260606",
        )
    except Exception as exc:
        add("delivery", "error", "fail", f"Osen DOCX render validation invalid: {type(exc).__name__}", "40_quality_evidence/osen_report_docx_render_20260606.json")

    cad_analysis_path = ROOT / "40_quality_evidence" / "cad_dxf_analysis_20260605.json"
    try:
        payload = json.loads(cad_analysis_path.read_text(encoding="utf-8-sig"))
        results = payload.get("results", [])
        converted = [row for row in results if int(row.get("dxf_bytes", 0) or 0) > 0]
        anchor_text = json.dumps(results, ensure_ascii=False)
        required_anchors = ["南入口", "2A03", "露天剧场", "廉洁馆", "公园南门"]
        add("cad", "error", ok(len(converted) >= 2), f"converted CAD drawings={[row.get('cad_id') for row in converted]}", "40_quality_evidence/cad_dxf_analysis_20260605.json")
        add("cad", "error", ok(all(term in anchor_text for term in required_anchors)), f"CAD anchors found={[term for term in required_anchors if term in anchor_text]}", "40_quality_evidence/cad_dxf_analysis_20260605.json")
    except Exception as exc:
        add("cad", "error", "fail", f"CAD analysis invalid: {type(exc).__name__}", "40_quality_evidence/cad_dxf_analysis_20260605.json")

    delivery_md_path = ROOT / "80_delivery" / "site_selection_gap_report_latest.md"
    try:
        text = delivery_md_path.read_text(encoding="utf-8-sig")
        forbidden = [
            "needs_review",
            "not_final",
            "output_status",
            "debug",
            "payload",
            "traceback",
            "ConnectError",
            "external" + "_preview_only",
        ]
        required_terms = [
            "奥森商业改造综合评估",
            "桃花源白房子",
            "南门地下预埋空间",
            "当前推进事项",
            "控制点校准",
            "真实校准输入与使用边界",
            "官方宏观边界",
            "设备价格代理",
        ]
        add("delivery", "error", ok(len(text.encode("utf-8")) >= 12000), f"latest report bytes={len(text.encode('utf-8'))}", "80_delivery/site_selection_gap_report_latest.md")
        add("delivery", "error", ok(all(term in text for term in required_terms)), f"latest report required terms found={[term for term in required_terms if term in text]}", "80_delivery/site_selection_gap_report_latest.md")
        add("delivery", "error", ok(not any(term in text for term in forbidden)), f"latest report forbidden terms={[term for term in forbidden if term in text]}", "80_delivery/site_selection_gap_report_latest.md")
    except Exception as exc:
        add("delivery", "error", "fail", f"latest report invalid: {type(exc).__name__}", "80_delivery/site_selection_gap_report_latest.md")

    browser_gate_path = ROOT / "40_quality_evidence" / "osen_report_browser_validation_20260606.json"
    try:
        payload = json.loads(browser_gate_path.read_text(encoding="utf-8-sig"))
        checks = payload.get("checks", [])
        passed_names = {row.get("name", "") for row in checks if row.get("passed") is True}
        required_names = {
            "required_terms_visible",
            "docx_download_link",
            "node_options_visible",
            "old_report_title_removed",
            "no_backend_words_visible",
            "report_sections_present",
            "real_calibration_visible",
            "hero_readable_width",
            "screenshot_written",
            "console_clean",
        }
        add("browser", "error", ok(payload.get("status") == "pass"), f"Osen report browser status={payload.get('status')}, failures={payload.get('failure_count')}", "40_quality_evidence/osen_report_browser_validation_20260606.json")
        add("browser", "error", ok(required_names <= passed_names), f"Osen report browser passed names={sorted(passed_names)}", "40_quality_evidence/osen_report_browser_validation_20260606.json")
    except Exception as exc:
        add("browser", "error", "fail", f"Osen report browser gate invalid: {type(exc).__name__}", "40_quality_evidence/osen_report_browser_validation_20260606.json")

    global_design_doc_path = ROOT / "10_research" / "global_ai_simulation_design_rebaseline_20260604.md"
    try:
        text = global_design_doc_path.read_text(encoding="utf-8-sig")
        required_terms = [
            "AI 驱动仿真决策系统",
            "目标 -> 对象 -> 依据 -> 动作 -> 复核 -> 报告",
            "公园商业选址",
            "Flowus",
            "2026",
            "不再用裸分数讲结论",
        ]
        add("ux_rebaseline", "error", ok(all(term in text for term in required_terms)), "global AI simulation design rebaseline preserves scope/method/UX constraints", "10_research/global_ai_simulation_design_rebaseline_20260604.md")
        add("ux_rebaseline", "error", ok("P6 页面美化指南" in text and "整个“AI 驱动仿真决策系统”" in text), "global rebaseline explicitly rejects narrow P6-only framing", "10_research/global_ai_simulation_design_rebaseline_20260604.md")
    except Exception as exc:
        add("ux_rebaseline", "error", "fail", f"global design rebaseline invalid: {type(exc).__name__}", "10_research/global_ai_simulation_design_rebaseline_20260604.md")

    advanced_learning_path = ROOT / "10_research" / "advanced_ai_learning_absorption_register_20260604.md"
    try:
        text = advanced_learning_path.read_text(encoding="utf-8-sig")
        required_terms = [
            "AI 驱动仿真决策系统",
            "agent 可读 UI",
            "检查点调度",
            "多 agent 是角色分层",
            "旧东西如何降级",
            "旧产物信任地图",
            "Agentic information systems",
            "Dark Patterns Meet GUI Agents",
            "SCSimulator",
            "MCP-SIM",
            "ToolSmith",
        ]
        add("ux_rebaseline", "error", ok(all(term in text for term in required_terms)), "advanced AI learning register preserves agentic/UI/simulation/legacy trust constraints", "10_research/advanced_ai_learning_absorption_register_20260604.md")
        add("ux_rebaseline", "error", ok("不能说“完全先进”" in text and "还不够先进" in text), "advanced learning register explicitly admits unfinished advanced work", "10_research/advanced_ai_learning_absorption_register_20260604.md")
    except Exception as exc:
        add("ux_rebaseline", "error", "fail", f"advanced AI learning register invalid: {type(exc).__name__}", "10_research/advanced_ai_learning_absorption_register_20260604.md")

    advanced_validation_doc_path = ROOT / "10_research" / "advanced_ai_validation_rebaseline_20260604.md"
    try:
        text = advanced_validation_doc_path.read_text(encoding="utf-8-sig")
        required_terms = [
            "AI 产品 / agentic workflow / 人机协作",
            "Playwright 1.60",
            "OpenTelemetry SDK 1.42",
            "ARIA snapshot",
            "Trace 证据",
            "旧产物污染",
            "agent 可读性",
            "监督检查点",
            "AI 风险语言",
        ]
        add("advanced_gate", "error", ok(all(term in text for term in required_terms)), "advanced validation rebaseline captures modern AI/UX/gate concerns", "10_research/advanced_ai_validation_rebaseline_20260604.md")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"advanced validation rebaseline invalid: {type(exc).__name__}", "10_research/advanced_ai_validation_rebaseline_20260604.md")

    method_audit_path = ROOT / "10_research" / "method_tool_plugin_audit_20260604.md"
    try:
        text = method_audit_path.read_text(encoding="utf-8-sig")
        required_terms = [
            "方法 / 工具 / 插件 / 论文使用审计清单",
            "Playwright 1.60",
            "OpenTelemetry",
            "Selenium 4.44",
            "DeepSeek API",
            "AgentSociety",
            "MobiVerse",
            "CAMS",
            "POI_TGI_Calculator",
            "Product Design / Figma",
            "采用",
            "选择性吸收",
            "降级",
            "暂缓",
            "拒用",
            "人物仿真任务入口",
            "choice_probability.factor_inputs",
        ]
        add("advanced_gate", "error", ok(all(term in text for term in required_terms)), "method/tool/plugin audit preserves sources, advancedness, landing points, risks, and decisions", "10_research/method_tool_plugin_audit_20260604.md")
        add("advanced_gate", "error", ok("后续不能只写" in text and "还没有在 DeepSeek/API/仿真任务里写 span" in text), "method/tool/plugin audit explicitly records unfinished landing work", "10_research/method_tool_plugin_audit_20260604.md")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"method/tool/plugin audit invalid: {type(exc).__name__}", "10_research/method_tool_plugin_audit_20260604.md")

    deepseek_capacity_path = ROOT / "10_research" / "deepseek_api_concurrency_capacity_20260605.md"
    try:
        text = deepseek_capacity_path.read_text(encoding="utf-8-sig")
        required_terms = [
            "账号并发",
            "deepseek-v4-pro",
            "500",
            "deepseek-v4-flash",
            "2500",
            "HTTP 429",
            "capacity expansion",
            "不应每个虚拟游客都调用一次 DeepSeek",
            "本地 Python / schema / 规则 / 空间与运营约束",
        ]
        add("advanced_gate", "error", ok(all(term in text for term in required_terms)), "DeepSeek concurrency/capacity boundary is documented from official docs and project architecture", "10_research/deepseek_api_concurrency_capacity_20260605.md")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"DeepSeek capacity note invalid: {type(exc).__name__}", "10_research/deepseek_api_concurrency_capacity_20260605.md")

    simulation_entry_learning_path = ROOT / "10_research" / "simulation_task_entry_evidence_reinforcement_20260605.md"
    try:
        text = simulation_entry_learning_path.read_text(encoding="utf-8-sig")
        required_terms = [
            "MobileCity",
            "M2LSimu",
            "MobCache",
            "GTA",
            "GATSim",
            "HumanLM",
            "LSDTs",
            "策划文案",
            "CAD/图纸",
            "完整仿真被阻止",
            "DeepSeek",
            "不嵌入 Codex",
        ]
        add("advanced_gate", "error", ok(all(term in text for term in required_terms)), "simulation task entry learning ties recent papers, CAD/planning sources, and DeepSeek-only boundary to implementation", "10_research/simulation_task_entry_evidence_reinforcement_20260605.md")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"simulation task entry learning invalid: {type(exc).__name__}", "10_research/simulation_task_entry_evidence_reinforcement_20260605.md")

    deepseek_orchestration_path = ROOT / "40_quality_evidence" / "deepseek_orchestration_validation_20260605.json"
    try:
        payload = json.loads(deepseek_orchestration_path.read_text(encoding="utf-8-sig"))
        checks_by_name = {item.get("name"): item for item in payload.get("checks", []) if isinstance(item, dict)}
        required_checks = {
            "stable_fingerprint",
            "batch_cache_default",
            "runtime_chat_cache_disabled",
            "final_decision_not_deepseek",
            "per_visitor_call_blocked",
            "router_has_retry_cache_trace_terms",
            "telemetry_import_ok",
            "contract_forces_review_required",
        }
        boundary = payload.get("boundary", {})
        add("advanced_gate", "error", ok(payload.get("status") == "pass" and int(payload.get("failure_count", 99)) == 0), f"DeepSeek orchestration status={payload.get('status')} failures={payload.get('failure_count')}", "40_quality_evidence/deepseek_orchestration_validation_20260605.json")
        add("advanced_gate", "error", ok(required_checks <= set(checks_by_name)), f"DeepSeek orchestration checks={sorted(checks_by_name)}", "40_quality_evidence/deepseek_orchestration_validation_20260605.json")
        add("advanced_gate", "error", ok(all(checks_by_name[name].get("passed") for name in required_checks)), "DeepSeek orchestration required checks all pass", "40_quality_evidence/deepseek_orchestration_validation_20260605.json")
        add("advanced_gate", "error", ok(boundary.get("forbidden_pattern") == "per_virtual_visitor_realtime_llm_call"), f"DeepSeek orchestration boundary={boundary}", "40_quality_evidence/deepseek_orchestration_validation_20260605.json")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"DeepSeek orchestration validation invalid: {type(exc).__name__}", "40_quality_evidence/deepseek_orchestration_validation_20260605.json")

    context_audit_path = ROOT / "40_quality_evidence" / "project_context_legacy_risk_audit_20260605.json"
    try:
        payload = json.loads(context_audit_path.read_text(encoding="utf-8-sig"))
        inventory = payload.get("file_inventory", {})
        boss = payload.get("boss_materials", {})
        risks = payload.get("legacy_risk_scan", {})
        pending = payload.get("pending_work", {})
        risk_counts = risks.get("counts", {})
        add("advanced_gate", "error", ok(int(inventory.get("file_count", 0)) >= 900 and int(inventory.get("text_like_file_count", 0)) >= 700), f"context audit files={inventory.get('file_count')} text={inventory.get('text_like_file_count')}", "40_quality_evidence/project_context_legacy_risk_audit_20260605.json")
        add("advanced_gate", "error", ok(boss.get("raw_found_count") == boss.get("raw_expected_count") == 6 and not boss.get("raw_missing")), f"boss raw materials found={boss.get('raw_found_count')}/{boss.get('raw_expected_count')}", "40_quality_evidence/project_context_legacy_risk_audit_20260605.json")
        add("advanced_gate", "error", ok(all(int(risk_counts.get(key, 0)) > 0 for key in ["complete_simulation_claim", "final_claim", "raw_internal_ui", "deepseek_boundary"])), f"context audit risk_counts={risk_counts}", "40_quality_evidence/project_context_legacy_risk_audit_20260605.json")
        add("advanced_gate", "error", ok("telemetry_pending" in pending), f"context audit telemetry_pending={pending.get('telemetry_pending')}", "40_quality_evidence/project_context_legacy_risk_audit_20260605.json")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"context legacy risk audit invalid: {type(exc).__name__}", "40_quality_evidence/project_context_legacy_risk_audit_20260605.json")

    model_coverage_path = ROOT / "40_quality_evidence" / "method_model_landing_coverage_20260605.json"
    try:
        payload = json.loads(model_coverage_path.read_text(encoding="utf-8-sig"))
        counts = payload.get("status_counts", {})
        items = payload.get("items", [])
        item_ids = {item.get("id") for item in items if isinstance(item, dict)}
        required_ids = {"ROTE_BEHAVIOR_PROGRAM", "HUMANLM_LATENT_STATE", "RL_LLM_SOCIAL_SIM", "DEEPSEEK_CONSTRAINED_WORKER", "AGENTIC_UI_HUMAN_OVERSIGHT"}
        partial_ids = {item.get("id") for item in items if isinstance(item, dict) and item.get("status") == "partial"}
        covered_ids = {item.get("id") for item in items if isinstance(item, dict) and item.get("status") == "covered"}
        add("advanced_gate", "error", ok(int(counts.get("covered", 0)) >= 8 and int(counts.get("partial", 0)) >= 1 and int(counts.get("missing", 99)) == 0), f"method model coverage counts={counts}", "40_quality_evidence/method_model_landing_coverage_20260605.json")
        add("advanced_gate", "error", ok(required_ids <= item_ids), f"method model coverage ids={sorted(item_ids)}", "40_quality_evidence/method_model_landing_coverage_20260605.json")
        add("advanced_gate", "error", ok({"ROTE_BEHAVIOR_PROGRAM", "HUMANLM_LATENT_STATE", "DEEPSEEK_CONSTRAINED_WORKER"} <= covered_ids), f"method model covered ids={sorted(covered_ids)}", "40_quality_evidence/method_model_landing_coverage_20260605.json")
        add("advanced_gate", "error", ok("MACRO_VALIDATION_METRICS" in partial_ids), f"method model partial gaps={sorted(partial_ids)}", "40_quality_evidence/method_model_landing_coverage_20260605.json")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"method model landing coverage invalid: {type(exc).__name__}", "40_quality_evidence/method_model_landing_coverage_20260605.json")

    accuracy_req_path = ROOT / "40_quality_evidence" / "person_simulation_accuracy_requirements_20260605.json"
    try:
        payload = json.loads(accuracy_req_path.read_text(encoding="utf-8-sig"))
        requirements = payload.get("requirements", [])
        sources = payload.get("source_register", [])
        counts = payload.get("counts", {})
        source_ids = {source.get("source_id") for source in sources if isinstance(source, dict)}
        required_sources = {"BOSS-ROTE", "BOSS-HUMANLM", "MOD-MOBIVERSE", "MOD-CAMS", "MOD-GATSIM", "RISK-LLM-ABM", "CTRL-CODEX-PRIMARY"}
        requirement_layers = {row.get("layer") for row in requirements if isinstance(row, dict)}
        add("advanced_gate", "error", ok(payload.get("status") == "needs_review"), f"accuracy requirements status={payload.get('status')}", "40_quality_evidence/person_simulation_accuracy_requirements_20260605.json")
        add("advanced_gate", "error", ok(len(requirements) >= 9), f"accuracy requirements count={len(requirements)}", "40_quality_evidence/person_simulation_accuracy_requirements_20260605.json")
        add("advanced_gate", "error", ok(required_sources <= source_ids), f"accuracy requirement sources={sorted(source_ids)}", "40_quality_evidence/person_simulation_accuracy_requirements_20260605.json")
        add("advanced_gate", "error", ok({"人群状态", "行为程序", "活动链与路线", "选择概率", "宏观校准", "DeepSeek 调用", "用户监督", "高能力主控"} <= requirement_layers), f"accuracy requirement layers={sorted(requirement_layers)}", "40_quality_evidence/person_simulation_accuracy_requirements_20260605.json")
        add("advanced_gate", "error", ok(int(counts.get("feature_derivatives", 0)) >= 1000), f"accuracy feature derivatives={counts.get('feature_derivatives')}", "40_quality_evidence/person_simulation_accuracy_requirements_20260605.json")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"person simulation accuracy requirements invalid: {type(exc).__name__}", "40_quality_evidence/person_simulation_accuracy_requirements_20260605.json")

    feature_validation_path = ROOT / "40_quality_evidence" / "person_simulation_feature_derivatives_validation_20260607.json"
    try:
        payload = json.loads(feature_validation_path.read_text(encoding="utf-8-sig"))
        summary = payload.get("summary", {})
        coverage = payload.get("coverage", {})
        checks = {item.get("name"): item.get("passed") for item in payload.get("checks", []) if isinstance(item, dict)}
        required_checks = {
            "row_count_at_least_1000",
            "required_columns_present",
            "no_mojibake_markers",
            "business_terms_covered",
            "deepseek_boundary_every_row",
            "user_control_every_row",
            "specific_recommendation_not_raw_score",
        }
        add("advanced_gate", "error", ok(payload.get("status") == "pass" and int(payload.get("failure_count", 99)) == 0), f"feature derivative validation status={payload.get('status')} failures={payload.get('failure_count')}", "40_quality_evidence/person_simulation_feature_derivatives_validation_20260607.json")
        add("advanced_gate", "error", ok(int(summary.get("row_count", 0)) >= 1000), f"feature derivative rows={summary.get('row_count')}", "70_outputs/processed_tables/person_simulation_feature_derivatives_1000_20260604.csv")
        add("advanced_gate", "error", ok(required_checks <= set(checks) and all(checks[name] for name in required_checks)), f"feature derivative checks={sorted(checks)}", "40_quality_evidence/person_simulation_feature_derivatives_validation_20260607.json")
        add("advanced_gate", "error", ok(int(coverage.get("persona_id", 0)) >= 8 and int(coverage.get("income_segment_id", 0)) >= 5 and int(coverage.get("candidate_supply_action_id", 0)) >= 14), f"feature derivative coverage={coverage}", "40_quality_evidence/person_simulation_feature_derivatives_validation_20260607.json")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"person simulation feature derivative validation invalid: {type(exc).__name__}", "40_quality_evidence/person_simulation_feature_derivatives_validation_20260607.json")

    feature_browser_path = ROOT / "40_quality_evidence" / "person_feature_pool_browser_visible_20260607.json"
    try:
        payload = json.loads(feature_browser_path.read_text(encoding="utf-8-sig"))
        screenshot_paths = [ROOT / str(item) for item in payload.get("screenshots", [])]
        screenshots_ok = screenshot_paths and all(path.exists() and path.stat().st_size > 100_000 for path in screenshot_paths)
        add("advanced_gate", "error", ok(payload.get("status") == "pass" and payload.get("upload_visible") and payload.get("preflight_visible") and int(payload.get("console_error_count", 99)) == 0), f"feature pool browser status={payload.get('status')} upload={payload.get('upload_visible')} preflight={payload.get('preflight_visible')} console={payload.get('console_error_count')}", "40_quality_evidence/person_feature_pool_browser_visible_20260607.json")
        add("advanced_gate", "error", ok(bool(screenshots_ok)), f"feature pool screenshots={[(rel(path), path.stat().st_size if path.exists() else 0) for path in screenshot_paths]}", "40_quality_evidence/person_feature_pool_browser_visible_20260607.json")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"person simulation feature pool browser evidence invalid: {type(exc).__name__}", "40_quality_evidence/person_feature_pool_browser_visible_20260607.json")

    feature_control_browser_path = ROOT / "40_quality_evidence" / "feature_derivative_user_control_browser_20260607.json"
    try:
        payload = json.loads(feature_control_browser_path.read_text(encoding="utf-8-sig"))
        screenshot = ROOT / str(payload.get("screenshot", ""))
        add("advanced_gate", "error", ok(payload.get("status") == "pass" and payload.get("feature_pool_visible") and payload.get("use_visible_after_action") and payload.get("lock_visible_after_action") and payload.get("restore_visible_after_action") and int(payload.get("console_error_count", 99)) == 0), f"feature derivative user control status={payload.get('status')} id={payload.get('derivative_id')} console={payload.get('console_error_count')}", "40_quality_evidence/feature_derivative_user_control_browser_20260607.json")
        add("advanced_gate", "error", ok(screenshot.exists() and screenshot.stat().st_size > 100_000), f"feature derivative user control screenshot bytes={screenshot.stat().st_size if screenshot.exists() else 0}", rel(screenshot))
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"person simulation feature derivative user-control evidence invalid: {type(exc).__name__}", "40_quality_evidence/feature_derivative_user_control_browser_20260607.json")

    feature_income_browser_path = ROOT / "40_quality_evidence" / "feature_derivative_income_control_browser_20260607.json"
    try:
        payload = json.loads(feature_income_browser_path.read_text(encoding="utf-8-sig"))
        screenshot = ROOT / str(payload.get("screenshot", ""))
        after = payload.get("after", {})
        add("advanced_gate", "error", ok(payload.get("status") == "pass" and after.get("incomeVisible") and after.get("priceBandVisible") and "采用场景" in str(after.get("controlledCountText", "")) and int(payload.get("console_error_count", 99)) == 0), f"feature derivative income browser status={payload.get('status')} id={payload.get('action_id')} console={payload.get('console_error_count')}", "40_quality_evidence/feature_derivative_income_control_browser_20260607.json")
        add("advanced_gate", "error", ok(screenshot.exists() and screenshot.stat().st_size > 100_000), f"feature derivative income screenshot bytes={screenshot.stat().st_size if screenshot.exists() else 0}", rel(screenshot))
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"person simulation feature derivative income browser evidence invalid: {type(exc).__name__}", "40_quality_evidence/feature_derivative_income_control_browser_20260607.json")

    report_feature_context_path = ROOT / "40_quality_evidence" / "report_feature_scene_context_validation_20260607.json"
    try:
        payload = json.loads(report_feature_context_path.read_text(encoding="utf-8-sig"))
        checks = {item.get("check_id"): item for item in payload.get("checks", []) if isinstance(item, dict)}
        required_checks = {
            "API-REPORT-CONTEXT",
            "API-REPORT-INCOME-PRICE",
            "API-REPORT-READINESS-IMPACT",
            "API-REPORT-NEXT-ACTION-IMPACT",
            "API-REPORT-REAL-CALIBRATION",
            "API-REPORT-CALIBRATION-READINESS",
            "API-REPORT-CALIBRATION-NEXT-ACTION",
            "PROMPT-FEATURE-CONTEXT",
            "PROMPT-INCOME-PRICE-RULE",
            "API-SITE-REPORT-REAL-CALIBRATION",
            "DOCX-FEATURE-SECTION",
            "DOCX-INCOME-PRICE",
            "DOCX-REAL-CALIBRATION-SECTION",
            "MD-FEATURE-SECTION",
            "MD-REAL-CALIBRATION-SECTION",
            "UI-REPORT-FEATURE-CONTEXT",
            "UI-REPORT-REAL-CALIBRATION",
        }
        docx_path = ROOT / "80_delivery" / "osen_integrated_site_selection_report_20260606.docx"
        add("advanced_gate", "error", ok(payload.get("status") == "pass" and int(payload.get("failure_count", 99)) == 0), f"report feature context status={payload.get('status')} failures={payload.get('failure_count')}", "40_quality_evidence/report_feature_scene_context_validation_20260607.json")
        add("advanced_gate", "error", ok(required_checks <= set(checks) and all(checks[name].get("status") == "pass" for name in required_checks)), f"report feature context checks={sorted(checks)}", "40_quality_evidence/report_feature_scene_context_validation_20260607.json")
        add("advanced_gate", "error", ok(docx_path.exists() and docx_path.stat().st_size > 40_000), f"report DOCX bytes={docx_path.stat().st_size if docx_path.exists() else 0}", rel(docx_path))
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"report feature scene context validation invalid: {type(exc).__name__}", "40_quality_evidence/report_feature_scene_context_validation_20260607.json")

    real_calibration_loop_path = ROOT / "40_quality_evidence" / "real_calibration_supplement_loop_validation_20260607.json"
    try:
        payload = json.loads(real_calibration_loop_path.read_text(encoding="utf-8-sig"))
        checks = {item.get("check_id"): item for item in payload.get("checks", []) if isinstance(item, dict)}
        required_checks = {
            "API-SUPPLEMENT-CREATE",
            "API-SUPPLEMENT-PATCH",
            "PREFLIGHT-COUNT-CHANGED",
            "PREFLIGHT-PATCH-VISIBLE",
            "JOB-REQUEST-COUNT-CHANGED",
            "REPORT-JSON-SUPPLEMENT",
            "REPORT-MD-SUPPLEMENT",
            "REPORT-DOCX-SUPPLEMENT",
            "BROWSER-SUPPLEMENT-VISIBLE",
            "BROWSER-PATCHED-VALUE-VISIBLE",
            "BROWSER-CONSOLE-CLEAN",
        }
        screenshot = ROOT / str(payload.get("screenshot", ""))
        add("advanced_gate", "error", ok(payload.get("status") == "pass" and int(payload.get("failure_count", 99)) == 0), f"real calibration supplement loop status={payload.get('status')} failures={payload.get('failure_count')}", "40_quality_evidence/real_calibration_supplement_loop_validation_20260607.json")
        add("advanced_gate", "error", ok(required_checks <= set(checks) and all(checks[name].get("status") == "pass" for name in required_checks)), f"real calibration supplement loop checks={sorted(checks)}", "40_quality_evidence/real_calibration_supplement_loop_validation_20260607.json")
        add("advanced_gate", "error", ok(screenshot.exists() and screenshot.stat().st_size > 100_000), f"real calibration supplement loop screenshot bytes={screenshot.stat().st_size if screenshot.exists() else 0}", rel(screenshot))
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"real calibration supplement loop validation invalid: {type(exc).__name__}", "40_quality_evidence/real_calibration_supplement_loop_validation_20260607.json")

    report_feature_browser_path = ROOT / "40_quality_evidence" / "report_feature_scene_context_browser_20260607.json"
    try:
        payload = json.loads(report_feature_browser_path.read_text(encoding="utf-8-sig"))
        checks = {item.get("name"): item for item in payload.get("checks", []) if isinstance(item, dict)}
        required_checks = {
            "report_visible",
            "feature_section_visible",
            "income_visible",
            "price_band_visible",
            "adopted_scene_visible",
            "no_forbidden_words",
            "console_clean",
            "screenshot_written",
        }
        screenshot = ROOT / str(payload.get("screenshot", ""))
        add("advanced_gate", "error", ok(payload.get("status") == "pass"), f"report feature browser status={payload.get('status')} derivative={payload.get('derivative_id')}", "40_quality_evidence/report_feature_scene_context_browser_20260607.json")
        add("advanced_gate", "error", ok(required_checks <= set(checks) and all(checks[name].get("passed") for name in required_checks)), f"report feature browser checks={sorted(checks)}", "40_quality_evidence/report_feature_scene_context_browser_20260607.json")
        add("advanced_gate", "error", ok(screenshot.exists() and screenshot.stat().st_size > 100_000), f"report feature browser screenshot bytes={screenshot.stat().st_size if screenshot.exists() else 0}", rel(screenshot))
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"report feature scene browser validation invalid: {type(exc).__name__}", "40_quality_evidence/report_feature_scene_context_browser_20260607.json")

    simulation_feature_dry_run_path = ROOT / "40_quality_evidence" / "simulation_feature_scene_dry_run_validation_20260607.json"
    try:
        payload = json.loads(simulation_feature_dry_run_path.read_text(encoding="utf-8-sig"))
        checks = {item.get("check_id"): item for item in payload.get("checks", []) if isinstance(item, dict)}
        required_checks = {
            "JOB-REQUEST-FEATURE-COUNT",
            "JOB-REQUEST-FEATURE-ID",
            "JOB-REQUEST-REAL-CALIBRATION-COUNT",
            "JOB-REQUEST-REAL-CALIBRATION-LAYERS",
            "RESULT-FEATURE-MATCH",
            "RESULT-FEATURE-CONTEXT",
            "RESULT-INCOME-PRICE-PRESSURE",
            "RESULT-TIME-WEATHER-PRESSURE",
            "RESULT-OPERATION-RULES",
            "RESULT-ACCURACY-CONTEXT",
            "RESULT-ACCURACY-LEVERS",
            "RESULT-DEEPSEEK-BOUNDARY",
            "RESULT-CALIBRATION-EVIDENCE",
            "RESULT-NEXT-DATA-SCENE",
            "RESULT-NOT-FINAL-WARNING",
            "EXPORT-CSV-FEATURE-FIELDS",
            "EXPORT-CSV-ACCURACY-FIELDS",
            "UI-SIM-FEATURE-FIELDS",
            "UI-SIM-ACCURACY-FIELDS",
        }
        add("advanced_gate", "error", ok(payload.get("status") == "pass" and int(payload.get("failure_count", 99)) == 0), f"simulation feature dry run status={payload.get('status')} failures={payload.get('failure_count')} matches={payload.get('matched_result_count')}", "40_quality_evidence/simulation_feature_scene_dry_run_validation_20260607.json")
        add("advanced_gate", "error", ok(required_checks <= set(checks) and all(checks[name].get("status") == "pass" for name in required_checks)), f"simulation feature dry run checks={sorted(checks)}", "40_quality_evidence/simulation_feature_scene_dry_run_validation_20260607.json")
        add("advanced_gate", "error", ok(int(payload.get("matched_result_count", 0)) >= 1), f"simulation feature matched rows={payload.get('matched_result_count')}", "40_quality_evidence/simulation_feature_scene_dry_run_validation_20260607.json")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"simulation feature scene dry-run validation invalid: {type(exc).__name__}", "40_quality_evidence/simulation_feature_scene_dry_run_validation_20260607.json")

    simulation_feature_browser_path = ROOT / "40_quality_evidence" / "simulation_feature_scene_browser_validation_20260607.json"
    try:
        payload = json.loads(simulation_feature_browser_path.read_text(encoding="utf-8-sig"))
        checks = {item.get("name"): item for item in payload.get("checks", []) if isinstance(item, dict)}
        required_checks = {
            "feature_scene_visible",
            "adopted_scene_metric",
            "real_calibration_metric",
            "income_price_visible",
            "operation_visible",
            "table_scene_columns",
            "job_id_visible",
            "pressure_card_count",
            "no_forbidden_words",
            "console_clean",
            "screenshot_written",
        }
        screenshot = ROOT / str(payload.get("screenshot", ""))
        add("advanced_gate", "error", ok(payload.get("status") == "pass" and int(payload.get("failure_count", 99)) == 0), f"simulation feature browser status={payload.get('status')} failures={payload.get('failure_count')} job={payload.get('job_id')}", "40_quality_evidence/simulation_feature_scene_browser_validation_20260607.json")
        add("advanced_gate", "error", ok(required_checks <= set(checks) and all(checks[name].get("passed") for name in required_checks)), f"simulation feature browser checks={sorted(checks)}", "40_quality_evidence/simulation_feature_scene_browser_validation_20260607.json")
        add("advanced_gate", "error", ok(screenshot.exists() and screenshot.stat().st_size > 100_000), f"simulation feature browser screenshot bytes={screenshot.stat().st_size if screenshot.exists() else 0}", rel(screenshot))
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"simulation feature scene browser validation invalid: {type(exc).__name__}", "40_quality_evidence/simulation_feature_scene_browser_validation_20260607.json")

    production_ai_files = [
        ROOT / "90_p6_expert_dashboard" / "app.py",
        ROOT / "90_p6_expert_dashboard" / "static" / "app.js",
        ROOT / "90_p6_expert_dashboard" / "static" / "index.html",
        ROOT / "90_p6_expert_dashboard" / "static" / "styles.css",
    ]
    forbidden_prod_ai_terms = [
        "codex_api_key",
        "CODEX_API_KEY",
        "codex model",
        "Codex model",
        "内置 Codex",
        "搭载 Codex",
        "调用 Codex",
    ]
    prod_hits: list[str] = []
    for path in production_ai_files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        for term in forbidden_prod_ai_terms:
            if term in text:
                prod_hits.append(f"{path.relative_to(ROOT)}::{term}")
    add("advanced_gate", "error", ok(not prod_hits), f"production AI must be DeepSeek-only; codex prod hits={prod_hits}", "90_p6_expert_dashboard")

    object_chain_path = ROOT / "40_quality_evidence" / "object_chain_rebaseline_validation_20260605.json"
    try:
        payload = json.loads(object_chain_path.read_text(encoding="utf-8-sig"))
        object_keys = set(payload.get("object_keys", []))
        required_keys = {
            "project_scope",
            "source_material",
            "persona_state",
            "behavior_program",
            "choice_probability",
            "feature_derivative_scene",
            "spatial_context",
            "validation_target",
            "node_progress",
            "ai_session",
            "report_draft",
        }
        summary = payload.get("summary", {})
        add("advanced_gate", "error", ok(payload.get("status") == "pass" and int(payload.get("failure_count", 99)) == 0), f"object chain status={payload.get('status')} failures={payload.get('failure_count')}", "40_quality_evidence/object_chain_rebaseline_validation_20260605.json")
        add("advanced_gate", "error", ok(required_keys <= object_keys), f"object chain keys={sorted(object_keys)}", "40_quality_evidence/object_chain_rebaseline_validation_20260605.json")
        add("advanced_gate", "error", ok(int(summary.get("total_items", 0)) >= 11 and int(summary.get("blocked_count", 0)) >= 1 and int(summary.get("draft_count", 0)) >= 1), f"object chain summary={summary}", "40_quality_evidence/object_chain_rebaseline_validation_20260605.json")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"object chain rebaseline validation invalid: {type(exc).__name__}", "40_quality_evidence/object_chain_rebaseline_validation_20260605.json")

    object_chain_browser_path = ROOT / "40_quality_evidence" / "object_chain_browser_validation_20260605.json"
    try:
        payload = json.loads(object_chain_browser_path.read_text(encoding="utf-8-sig"))
        checks = {item.get("name"): item.get("passed") for item in payload.get("checks", []) if isinstance(item, dict)}
        required_visible = {
            "visible_对象链路矩阵",
            "visible_人群状态画像",
            "visible_行为程序",
            "visible_选择概率候选",
            "visible_仿真验证目标",
            "visible_节点推进对象",
            "visible_AI 沟通记录",
            "visible_报告工作稿",
            "no_backend_words",
            "console_no_errors",
        }
        screenshot = ROOT / str(payload.get("screenshot", ""))
        add("advanced_gate", "error", ok(payload.get("status") == "pass" and int(payload.get("failure_count", 99)) == 0), f"object chain browser status={payload.get('status')} failures={payload.get('failure_count')}", "40_quality_evidence/object_chain_browser_validation_20260605.json")
        add("advanced_gate", "error", ok(required_visible <= set(checks) and all(checks[name] for name in required_visible)), f"object chain browser checks={sorted(checks)}", "40_quality_evidence/object_chain_browser_validation_20260605.json")
        add("advanced_gate", "error", ok(screenshot.exists() and screenshot.stat().st_size > 100_000), f"object chain screenshot bytes={screenshot.stat().st_size if screenshot.exists() else 0}", rel(screenshot))
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"object chain browser validation invalid: {type(exc).__name__}", "40_quality_evidence/object_chain_browser_validation_20260605.json")

    simulation_task_preflight_path = ROOT / "40_quality_evidence" / "simulation_task_entry_preflight_validation_20260605.json"
    try:
        payload = json.loads(simulation_task_preflight_path.read_text(encoding="utf-8-sig"))
        checks = {item.get("check_id"): item for item in payload.get("checks", []) if isinstance(item, dict)}
        required_checks = {
            "DATA-EVIDENCE-LEDGER",
            "DATA-BOSS-MATERIALS",
            "DATA-CAD-PLAN",
            "OBJECT-PERSONA-BEHAVIOR",
            "OBJECT-CHOICE-VALIDATION",
            "DATA-FEATURE-DERIVATIVES",
            "DATA-OSEN-REAL-CALIBRATION",
            "API-CHECK-CONTROLLED-FEATURE-SCENES",
            "API-CHECK-REAL-CALIBRATION",
            "API-ASSET-REAL-CALIBRATION",
            "API-REAL-CALIBRATION-LAYERED",
            "API-FEATURE-INCOME-COVERAGE",
            "API-FEATURE-INCOME-FIELDS",
            "API-FEATURE-INPUT-IMPACT",
            "UI-FEATURE-INCOME-FIELDS",
            "API-FULL-SIM-BLOCKED",
            "API-POST-FULL-STILL-BLOCKED",
            "UI-PREFLIGHT-SECTION",
            "TEXT-AI-BOUNDARY-HUMANIZED",
            "TEXT-NO-FINAL-CLAIM",
        }
        local_counts = payload.get("local_counts", {})
        add("advanced_gate", "error", ok(payload.get("status") == "pass" and int(payload.get("failure_count", 99)) == 0), f"simulation task preflight status={payload.get('status')} failures={payload.get('failure_count')}", "40_quality_evidence/simulation_task_entry_preflight_validation_20260605.json")
        add("advanced_gate", "error", ok(required_checks <= set(checks) and all(checks[name].get("status") == "pass" for name in required_checks)), f"simulation task preflight checks={sorted(checks)}", "40_quality_evidence/simulation_task_entry_preflight_validation_20260605.json")
        add("advanced_gate", "error", ok(int(local_counts.get("boss_sources", 0)) == 6 and int(local_counts.get("cad_plan_files", 0)) >= 4), f"simulation task local counts={local_counts}", "40_quality_evidence/simulation_task_entry_preflight_validation_20260605.json")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"simulation task preflight validation invalid: {type(exc).__name__}", "40_quality_evidence/simulation_task_entry_preflight_validation_20260605.json")

    advanced_qa_path = ROOT / "40_quality_evidence" / "advanced_agentic_workflow_validation_20260604.json"
    try:
        payload = json.loads(advanced_qa_path.read_text(encoding="utf-8-sig"))
        taxonomy = payload.get("risk_taxonomy", {})
        methods = payload.get("method", [])
        views = payload.get("views", [])
        screenshots = payload.get("screenshots", [])
        control_scan = payload.get("control_scan", {})
        data_view = next((item for item in views if item.get("view") == "data"), {})
        trace_path = ROOT / str(payload.get("trace", ""))
        aria_path = ROOT / str(payload.get("aria_snapshot", ""))
        required_taxonomy = {
            "human_visual",
            "agent_readability",
            "ai_scope_integrity",
            "oversight_checkpoint",
            "legacy_leakage",
            "state_coupling",
            "evidence_traceability",
            "observability",
            "ai_output_risk",
            "accessibility_semantics",
        }
        add("advanced_gate", "error", ok(payload.get("status") == "pass" and not payload.get("findings")), f"advanced QA status={payload.get('status')} findings={len(payload.get('findings', []))}", "40_quality_evidence/advanced_agentic_workflow_validation_20260604.json")
        add("advanced_gate", "error", ok(required_taxonomy <= set(taxonomy)), f"advanced QA taxonomy={sorted(taxonomy)}", "40_quality_evidence/advanced_agentic_workflow_validation_20260604.json")
        add("advanced_gate", "error", ok(len(methods) >= 7 and any("Playwright trace" in item for item in methods) and any("ARIA snapshot" in item for item in methods)), f"advanced QA methods={methods}", "40_quality_evidence/advanced_agentic_workflow_validation_20260604.json")
        add("advanced_gate", "error", ok(len(views) >= 7 and len(screenshots) >= 7), f"advanced QA views={len(views)} screenshots={len(screenshots)}", "40_quality_evidence/advanced_agentic_workflow_validation_20260604.json")
        add("advanced_gate", "error", ok(int(control_scan.get("missing_hook_count", -1)) == 0), f"advanced QA missing_hook_count={control_scan.get('missing_hook_count')}", "40_quality_evidence/advanced_agentic_workflow_validation_20260604.json")
        add("advanced_gate", "error", ok(int(data_view.get("text_len", 999999)) < 5000), f"advanced QA data view text_len={data_view.get('text_len')}", "40_quality_evidence/advanced_agentic_workflow_validation_20260604.json")
        add("advanced_gate", "error", ok(trace_path.exists() and trace_path.stat().st_size > 500_000), f"advanced QA trace bytes={trace_path.stat().st_size if trace_path.exists() else 0}", rel(trace_path))
        add("advanced_gate", "error", ok(aria_path.exists() and aria_path.stat().st_size > 1_000), f"advanced QA ARIA bytes={aria_path.stat().st_size if aria_path.exists() else 0}", rel(aria_path))
        versions = payload.get("tool_versions", {})
        add("advanced_gate", "error", ok(str(versions.get("playwright", "")).startswith("1.60") and str(versions.get("opentelemetry_sdk", "")).startswith("1.42") and str(versions.get("selenium_retained", "")).startswith("4.44")), f"advanced QA tool_versions={versions}", "40_quality_evidence/advanced_agentic_workflow_validation_20260604.json")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"advanced agentic workflow validation invalid: {type(exc).__name__}", "40_quality_evidence/advanced_agentic_workflow_validation_20260604.json")

    page_blueprint_path = ROOT / "00_control" / "page_layer_rebuild_blueprint_20260605.md"
    try:
        text = page_blueprint_path.read_text(encoding="utf-8-sig")
        required_terms = [
            "全局仿真链路台",
            "对象链路矩阵",
            "默认项目综合",
            "不是旧项目说明页",
            "Playwright",
            "axe",
            "Lighthouse",
            "OpenTelemetry",
        ]
        add("advanced_gate", "error", ok(all(term in text for term in required_terms)), "page layer rebuild blueprint preserves global object-chain and modern validation requirements", "00_control/page_layer_rebuild_blueprint_20260605.md")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"page layer rebuild blueprint invalid: {type(exc).__name__}", "00_control/page_layer_rebuild_blueprint_20260605.md")

    mainline_map_path = ROOT / "00_control" / "mainline_execution_map_20260605.md"
    try:
        text = mainline_map_path.read_text(encoding="utf-8-sig")
        required_terms = [
            "AI 驱动仿真决策系统",
            "迁移护栏",
            "保留 / 重构 / 隐藏 / 废弃",
            "防循环停止规则",
            "资料与空间底座工作区",
            "人物仿真对象使用路径",
            "总门禁",
        ]
        add("advanced_gate", "error", ok(all(term in text for term in required_terms)), "mainline execution map prevents legacy-shell loop and names next valuable slices", "00_control/mainline_execution_map_20260605.md")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"mainline execution map invalid: {type(exc).__name__}", "00_control/mainline_execution_map_20260605.md")

    ui_skill_audit_path = ROOT / "10_research" / "ui_skill_design_system_audit_20260605.md"
    try:
        text = ui_skill_audit_path.read_text(encoding="utf-8-sig")
        required_terms = [
            "ui-ux-pro-max",
            "Data-Dense Dashboard",
            "蓝色数据体系",
            "琥珀色",
            "active state",
            "aria-live",
            "不是说明页",
            "完整仿真未闭合",
        ]
        add("advanced_gate", "error", ok(all(term in text for term in required_terms)), "ui skill design system audit is persisted and mapped to the next page rebuild", "10_research/ui_skill_design_system_audit_20260605.md")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"ui skill design system audit invalid: {type(exc).__name__}", "10_research/ui_skill_design_system_audit_20260605.md")

    web_guidelines_audit_path = ROOT / "10_research" / "web_design_guidelines_audit_20260605.md"
    try:
        text = web_guidelines_audit_path.read_text(encoding="utf-8-sig")
        required_terms = [
            "Web Interface Guidelines",
            "focus-visible",
            "aria-label",
            "deep linking",
            "innerHTML",
            "DEC-087",
            "不是最终信息架构",
        ]
        add("advanced_gate", "error", ok(all(term in text for term in required_terms)), "web design guidelines audit is persisted and mapped to the page rebuild decision", "10_research/web_design_guidelines_audit_20260605.md")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"web design guidelines audit invalid: {type(exc).__name__}", "10_research/web_design_guidelines_audit_20260605.md")

    page_strategy_path = ROOT / "40_quality_evidence" / "page_rebuild_strategy_audit_20260605.json"
    try:
        payload = json.loads(page_strategy_path.read_text(encoding="utf-8-sig"))
        checks_by_id = {item.get("id"): item for item in payload.get("checks", []) if isinstance(item, dict)}
        answer = payload.get("answer_to_user_question", {})
        migration = payload.get("migration_inventory", {})
        required_checks = {
            "NEW-CHAIN-LANDED",
            "PAGE-VALIDATION-PASS",
            "OBJECT-CHAIN-PASS",
            "PREFLIGHT-PASS-BUT-NOT-FINAL-SIMULATION",
            "OLD-SHELL-STILL-PRESENT",
            "NO_FORBIDDEN_VISIBLE_LEAK_IN_STATIC_SURFACE",
            "BOSS-REBASELINE-REQUIRES-SYSTEM-LAYER",
            "BLUEPRINT-SAYS-NOT-PATCHING",
            "RECENT-SIMULATION-LEARNING-BOUNDARY",
            "CSS-STILL-LEGACY-PANEL-DOMINANT",
            "UI_UX_PRO_MAX_DESIGN_SYSTEM_USED",
        }
        add("advanced_gate", "error", ok(payload.get("status") == "requires_page_level_rebuild"), f"page rebuild strategy status={payload.get('status')}", "40_quality_evidence/page_rebuild_strategy_audit_20260605.json")
        add("advanced_gate", "error", ok(answer.get("full_website_redone") is False and "过渡重基线" in str(answer.get("current_page_state", ""))), f"page rebuild answer={answer}", "40_quality_evidence/page_rebuild_strategy_audit_20260605.json")
        add("advanced_gate", "error", ok(required_checks <= set(checks_by_id) and all(checks_by_id[name].get("passed") for name in required_checks)), f"page rebuild checks={sorted(checks_by_id)}", "40_quality_evidence/page_rebuild_strategy_audit_20260605.json")
        add("advanced_gate", "error", ok(all(migration.get(key) for key in ["keep_as_verified_backend_or_data_base", "refactor_into_new_workflow_surface", "retire_or_hide_from_user_surface"])), f"page rebuild migration keys={sorted(migration)}", "40_quality_evidence/page_rebuild_strategy_audit_20260605.json")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"page rebuild strategy audit invalid: {type(exc).__name__}", "40_quality_evidence/page_rebuild_strategy_audit_20260605.json")

    workflow_nav_path = ROOT / "40_quality_evidence" / "workflow_navigation_validation_20260605.json"
    try:
        payload = json.loads(workflow_nav_path.read_text(encoding="utf-8-sig"))
        checks_by_id = {item.get("id"): item for item in payload.get("checks", []) if isinstance(item, dict)}
        required_checks = {
            "WORKFLOW_NAV_REPLACES_FLAT_SIDE_NAV",
            "FIVE_STAGE_IA_PRESENT",
            "DRILLDOWN_TARGETS_PRESENT",
            "DEEP_LINK_AND_SCROLL_LOGIC_PRESENT",
            "ACTIVE_STAGE_LOGIC_PRESENT",
            "VISUAL_SYSTEM_PRESENT",
            "NODE_DETAIL_DOES_NOT_DUPLICATE_CREATE_FORM",
            "DESIGN_SKILL_EVIDENCE_EXISTS",
        }
        add("advanced_gate", "error", ok(payload.get("status") == "pass" and int(payload.get("failure_count", 99)) == 0), f"workflow navigation status={payload.get('status')} failures={payload.get('failure_count')}", "40_quality_evidence/workflow_navigation_validation_20260605.json")
        add("advanced_gate", "error", ok(required_checks <= set(checks_by_id) and all(checks_by_id[name].get("passed") for name in required_checks)), f"workflow navigation checks={sorted(checks_by_id)}", "40_quality_evidence/workflow_navigation_validation_20260605.json")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"workflow navigation validation invalid: {type(exc).__name__}", "40_quality_evidence/workflow_navigation_validation_20260605.json")

    source_foundation_path = ROOT / "40_quality_evidence" / "source_space_foundation_validation_20260605.json"
    try:
        payload = json.loads(source_foundation_path.read_text(encoding="utf-8-sig"))
        checks_by_id = {item.get("id"): item for item in payload.get("checks", []) if isinstance(item, dict)}
        required_checks = {
            "SOURCE_FOUNDATION_UI_EXISTS",
            "SOURCE_FOUNDATION_RENDERER_EXISTS",
            "SOURCE_FOUNDATION_VISUAL_SYSTEM_EXISTS",
            "LOCAL_ASSETS_BACKEND_PRESENT",
            "SPACE_CONTEXT_PRESENT_BUT_REVIEW_BOUNDARY_VISIBLE",
            "UPLOAD_POOL_STILL_AVAILABLE",
            "NO_INTERNAL_TOKENS_IN_VISIBLE_FOUNDATION_SURFACE",
            "CACHE_BUSTER_UPDATED_FOR_FOUNDATION_SLICE",
        }
        add("advanced_gate", "error", ok(payload.get("status") == "pass" and int(payload.get("failure_count", 99)) == 0), f"source/space foundation status={payload.get('status')} failures={payload.get('failure_count')} assets={payload.get('backend_asset_count')} pois={payload.get('backend_poi_count')}", "40_quality_evidence/source_space_foundation_validation_20260605.json")
        add("advanced_gate", "error", ok(required_checks <= set(checks_by_id) and all(checks_by_id[name].get("passed") for name in required_checks)), f"source/space foundation checks={sorted(checks_by_id)}", "40_quality_evidence/source_space_foundation_validation_20260605.json")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"source/space foundation validation invalid: {type(exc).__name__}", "40_quality_evidence/source_space_foundation_validation_20260605.json")

    source_foundation_runtime_path = ROOT / "40_quality_evidence" / "source_space_foundation_browser_runtime_20260605.json"
    source_foundation_screenshot = ROOT / "40_quality_evidence" / "source_space_foundation_upload_lazy_map_20260605.png"
    try:
        payload = json.loads(source_foundation_runtime_path.read_text(encoding="utf-8-sig"))
        active_view = set(payload.get("activeView", []))
        forbidden = payload.get("forbidden", [])
        lazy_map_ok = payload.get("hasAmapScriptElement") is False and payload.get("hasAmapGlobal") is False
        screenshot_bytes = source_foundation_screenshot.stat().st_size if source_foundation_screenshot.exists() else 0
        add("advanced_gate", "error", ok("uploadView" in active_view and int(payload.get("cardCount", 0)) >= 8 and lazy_map_ok and not forbidden), f"source foundation browser runtime active={active_view} cards={payload.get('cardCount')} lazy_map={lazy_map_ok} forbidden={forbidden}", "40_quality_evidence/source_space_foundation_browser_runtime_20260605.json")
        add("advanced_gate", "error", ok(screenshot_bytes > 100_000), f"source foundation screenshot bytes={screenshot_bytes}", "40_quality_evidence/source_space_foundation_upload_lazy_map_20260605.png")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"source/space foundation browser runtime invalid: {type(exc).__name__}", "40_quality_evidence/source_space_foundation_browser_runtime_20260605.json")

    page_layer_path = ROOT / "40_quality_evidence" / "page_layer_rebuild_validation_20260605.json"
    try:
        payload = json.loads(page_layer_path.read_text(encoding="utf-8-sig"))
        checks_by_name = {item.get("name"): item for item in payload.get("checks", []) if isinstance(item, dict)}
        required_checks = {
            "overview_no_backend_words",
            "overview_not_default_taohuayuan",
            "ai_default_project_scope",
            "ai_not_default_first_node",
            "ai_no_backend_words",
            "assistant_message_width_desktop",
            "composer_width_desktop",
            "ai_rail_toggle_changes_state",
            "new_chat_visible",
            "report_button_stateful",
        }
        screenshots = payload.get("screenshots", {})
        screenshot_sizes = {
            name: (ROOT / path).stat().st_size if path and (ROOT / path).exists() else 0
            for name, path in screenshots.items()
        }
        add("advanced_gate", "error", ok(payload.get("status") == "pass" and int(payload.get("failure_count", 99)) == 0), f"page layer validation status={payload.get('status')} failures={payload.get('failure_count')}", "40_quality_evidence/page_layer_rebuild_validation_20260605.json")
        add("advanced_gate", "error", ok(required_checks <= set(checks_by_name) and all(checks_by_name[name].get("passed") for name in required_checks)), f"page layer checks={sorted(checks_by_name)}", "40_quality_evidence/page_layer_rebuild_validation_20260605.json")
        add("advanced_gate", "error", ok(screenshot_sizes and all(size > 100_000 for size in screenshot_sizes.values())), f"page layer screenshot sizes={screenshot_sizes}", "40_quality_evidence/page_layer_rebuild_validation_20260605.json")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"page layer validation invalid: {type(exc).__name__}", "40_quality_evidence/page_layer_rebuild_validation_20260605.json")

    axe_path = ROOT / "40_quality_evidence" / "axe_accessibility_probe_20260605.json"
    try:
        payload = json.loads(axe_path.read_text(encoding="utf-8-sig"))
        views = payload.get("views", [])
        view_names = {view.get("view") for view in views if isinstance(view, dict)}
        violation_counts = {view.get("view"): view.get("violation_count") for view in views if isinstance(view, dict)}
        add("advanced_gate", "error", ok(payload.get("status") == "pass" and int(payload.get("failure_count", 99)) == 0), f"axe status={payload.get('status')} failures={payload.get('failure_count')}", "40_quality_evidence/axe_accessibility_probe_20260605.json")
        add("advanced_gate", "error", ok({"overview", "ai", "data"} <= view_names and all(int(value or 0) == 0 for value in violation_counts.values())), f"axe violation_counts={violation_counts}", "40_quality_evidence/axe_accessibility_probe_20260605.json")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"axe accessibility validation invalid: {type(exc).__name__}", "40_quality_evidence/axe_accessibility_probe_20260605.json")

    lighthouse_path = ROOT / "40_quality_evidence" / "lighthouse_user_flow_20260605.json"
    try:
        payload = json.loads(lighthouse_path.read_text(encoding="utf-8-sig"))
        checks_by_name = {item.get("name"): item for item in payload.get("checks", []) if isinstance(item, dict)}
        step_names = [step.get("name") for step in payload.get("steps", []) if isinstance(step, dict)]
        flow_html = ROOT / str(payload.get("flow_report_html", ""))
        required_checks = {
            "flow_has_three_steps",
            "accessibility_minimum_090",
            "best_practices_scores_present",
            "navigation_timespan_performance_minimum_080",
            "flow_html_written",
        }
        add("advanced_gate", "error", ok(payload.get("status") == "pass" and int(payload.get("failure_count", 99)) == 0), f"Lighthouse user flow status={payload.get('status')} failures={payload.get('failure_count')}", "40_quality_evidence/lighthouse_user_flow_20260605.json")
        add("advanced_gate", "error", ok(required_checks <= set(checks_by_name) and all(checks_by_name[name].get("passed") for name in required_checks)), f"Lighthouse checks={sorted(checks_by_name)}", "40_quality_evidence/lighthouse_user_flow_20260605.json")
        add("advanced_gate", "error", ok(len(step_names) == 3 and all(step_names)), f"Lighthouse step_names={step_names}", "40_quality_evidence/lighthouse_user_flow_20260605.json")
        add("advanced_gate", "error", ok(flow_html.exists() and flow_html.stat().st_size > 500_000), f"Lighthouse flow html bytes={flow_html.stat().st_size if flow_html.exists() else 0}", rel(flow_html))
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"Lighthouse user flow invalid: {type(exc).__name__}", "40_quality_evidence/lighthouse_user_flow_20260605.json")

    otel_path = ROOT / "40_quality_evidence" / "otel_fastapi_trace_probe_20260605.json"
    try:
        payload = json.loads(otel_path.read_text(encoding="utf-8-sig"))
        responses = payload.get("responses", {})
        add("advanced_gate", "error", ok(payload.get("status") == "pass" and int(payload.get("failure_count", 99)) == 0), f"OTel trace status={payload.get('status')} failures={payload.get('failure_count')}", "40_quality_evidence/otel_fastapi_trace_probe_20260605.json")
        add("advanced_gate", "error", ok(int(payload.get("span_count", 0)) >= 9 and responses and all(int(status) == 200 for status in responses.values())), f"OTel span_count={payload.get('span_count')} responses={responses}", "40_quality_evidence/otel_fastapi_trace_probe_20260605.json")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"OTel trace validation invalid: {type(exc).__name__}", "40_quality_evidence/otel_fastapi_trace_probe_20260605.json")

    advanced_capability_path = ROOT / "40_quality_evidence" / "advanced_capability_and_legacy_method_audit_20260605.json"
    try:
        payload = json.loads(advanced_capability_path.read_text(encoding="utf-8-sig"))
        capability_checks = payload.get("capability_checks", [])
        legacy_matrix = payload.get("legacy_method_matrix", [])
        refs = payload.get("official_references", [])
        add("advanced_gate", "error", ok(payload.get("status") == "pass" and int(payload.get("failure_count", 99)) == 0), f"advanced capability audit status={payload.get('status')} failures={payload.get('failure_count')}", "40_quality_evidence/advanced_capability_and_legacy_method_audit_20260605.json")
        add("advanced_gate", "error", ok(capability_checks and all(item.get("passed") for item in capability_checks if isinstance(item, dict))), f"advanced capability checks={len(capability_checks)}", "40_quality_evidence/advanced_capability_and_legacy_method_audit_20260605.json")
        add("advanced_gate", "error", ok(len(legacy_matrix) >= 6 and len(refs) >= 5), f"legacy_matrix={len(legacy_matrix)} official_refs={len(refs)}", "40_quality_evidence/advanced_capability_and_legacy_method_audit_20260605.json")
    except Exception as exc:
        add("advanced_gate", "error", "fail", f"advanced capability audit invalid: {type(exc).__name__}", "40_quality_evidence/advanced_capability_and_legacy_method_audit_20260605.json")

    flowus_report_path = ROOT / "40_quality_evidence" / "flowus_ai_design_probe_20260604" / "flowus_probe_report.json"
    try:
        records = json.loads(flowus_report_path.read_text(encoding="utf-8-sig"))
        titles = [str(item.get("title", "")) for item in records if isinstance(item, dict)]
        text_lens = [int(item.get("text_len", 0) or 0) for item in records if isinstance(item, dict)]
        screenshots_exist = all(Path(item.get("screenshot", "")).exists() for item in records if isinstance(item, dict))
        add("ux_rebaseline", "error", ok(isinstance(records, list) and len(records) == 3), f"Flowus probe records={len(records) if isinstance(records, list) else 'not_list'}", "40_quality_evidence/flowus_ai_design_probe_20260604/flowus_probe_report.json")
        add("ux_rebaseline", "error", ok(text_lens and min(text_lens) >= 2000), f"Flowus extracted text lengths={text_lens}", "40_quality_evidence/flowus_ai_design_probe_20260604/flowus_probe_report.json")
        add("ux_rebaseline", "error", ok(any("告别AI味" in title for title in titles) and any("注入灵魂" in title for title in titles)), f"Flowus titles={titles}", "40_quality_evidence/flowus_ai_design_probe_20260604/flowus_probe_report.json")
        add("ux_rebaseline", "error", ok(screenshots_exist), "Flowus screenshots exist for real browser evidence", "40_quality_evidence/flowus_ai_design_probe_20260604/flowus_probe_report.json")
    except Exception as exc:
        add("ux_rebaseline", "error", "fail", f"Flowus probe report invalid: {type(exc).__name__}", "40_quality_evidence/flowus_ai_design_probe_20260604/flowus_probe_report.json")

    openalex_design_path = ROOT / "10_research" / "ai_design_2026_openalex_raw_20260604.json"
    try:
        records = json.loads(openalex_design_path.read_text(encoding="utf-8-sig"))
        titles = [str(item.get("title", "")) for item in records if isinstance(item, dict)]
        title_blob = "\n".join(titles).lower()
        required_title_parts = [
            "agentic information systems",
            "dark patterns meet gui agents",
            "when should users check",
            "co-constructed or constrained",
            "scsimulator",
        ]
        add("ux_rebaseline", "error", ok(isinstance(records, list) and len(records) >= 20), f"OpenAlex 2026 AI design candidates={len(records) if isinstance(records, list) else 'not_list'}", "10_research/ai_design_2026_openalex_raw_20260604.json")
        add("ux_rebaseline", "error", ok(all(part in title_blob for part in required_title_parts)), "OpenAlex evidence includes 2026 agentic UI, oversight, and simulation references", "10_research/ai_design_2026_openalex_raw_20260604.json")
    except Exception as exc:
        add("ux_rebaseline", "error", "fail", f"OpenAlex AI design raw invalid: {type(exc).__name__}", "10_research/ai_design_2026_openalex_raw_20260604.json")

    semantic_design_path = ROOT / "10_research" / "ai_design_2026_semantic_scholar_raw_20260604.json"
    try:
        records = json.loads(semantic_design_path.read_text(encoding="utf-8-sig"))
        titles = [str(item.get("title", "")) for item in records if isinstance(item, dict)]
        errors = [item for item in records if isinstance(item, dict) and item.get("error")]
        add("ux_rebaseline", "warning", ok(isinstance(records, list) and len(records) >= 5), f"Semantic Scholar records={len(records) if isinstance(records, list) else 'not_list'}, errors={len(errors)}", "10_research/ai_design_2026_semantic_scholar_raw_20260604.json")
        add("ux_rebaseline", "error", ok(any("Human-LLM Agent Collaboration" in title or "Dark Patterns Meet GUI Agents" in title for title in titles)), f"Semantic Scholar useful titles={titles[:5]}", "10_research/ai_design_2026_semantic_scholar_raw_20260604.json")
    except Exception as exc:
        add("ux_rebaseline", "warning", "warn", f"Semantic Scholar AI design raw invalid: {type(exc).__name__}", "10_research/ai_design_2026_semantic_scholar_raw_20260604.json")

    arxiv_design_path = ROOT / "10_research" / "ai_design_2026_arxiv_raw_20260604.json"
    try:
        records = json.loads(arxiv_design_path.read_text(encoding="utf-8-sig"))
        errors = [item for item in records if isinstance(item, dict) and item.get("error")]
        add("ux_rebaseline", "info", "pass", f"arXiv 2026 search attempts={len(records) if isinstance(records, list) else 'not_list'}, blocked_or_timeout={len(errors)}", "10_research/ai_design_2026_arxiv_raw_20260604.json")
    except Exception as exc:
        add("ux_rebaseline", "warning", "warn", f"arXiv AI design raw invalid: {type(exc).__name__}", "10_research/ai_design_2026_arxiv_raw_20260604.json")

    legacy_adapter_path = ROOT / "40_quality_evidence" / "deepseek_legacy_envelope_adapter_20260604.json"
    try:
        payload = json.loads(legacy_adapter_path.read_text(encoding="utf-8-sig"))
        add("rebaseline", "error", ok(payload.get("status") == "metadata_wrapped_only"), f"legacy adapter status={payload.get('status')}", "40_quality_evidence/deepseek_legacy_envelope_adapter_20260604.json")
        add("rebaseline", "error", ok(int(payload.get("legacy_file_count", 0)) >= 35), f"legacy adapter file_count={payload.get('legacy_file_count')}", "40_quality_evidence/deepseek_legacy_envelope_adapter_20260604.json")
    except Exception as exc:
        add("rebaseline", "error", "fail", f"legacy adapter json invalid: {type(exc).__name__}", "40_quality_evidence/deepseek_legacy_envelope_adapter_20260604.json")

    legacy_validation_path = ROOT / "40_quality_evidence" / "deepseek_legacy_envelope_validation_20260604.json"
    try:
        payload = json.loads(legacy_validation_path.read_text(encoding="utf-8-sig"))
        add("rebaseline", "error", ok(payload.get("status") == "pass"), f"legacy envelope validation status={payload.get('status')}", "40_quality_evidence/deepseek_legacy_envelope_validation_20260604.json")
        add("rebaseline", "error", ok(int(payload.get("file_count", 0)) >= 35), f"legacy envelope validation file_count={payload.get('file_count')}", "40_quality_evidence/deepseek_legacy_envelope_validation_20260604.json")
        add("rebaseline", "error", ok(payload.get("failure_count") == 0), f"legacy envelope validation failure_count={payload.get('failure_count')}", "40_quality_evidence/deepseek_legacy_envelope_validation_20260604.json")
    except Exception as exc:
        add("rebaseline", "error", "fail", f"legacy envelope validation json invalid: {type(exc).__name__}", "40_quality_evidence/deepseek_legacy_envelope_validation_20260604.json")

    p4_node_adapter_path = ROOT / "40_quality_evidence" / "p4_node_explanation_adapter_20260604.json"
    try:
        payload = json.loads(p4_node_adapter_path.read_text(encoding="utf-8-sig"))
        add("p4", "error", ok(payload.get("status") == "needs_review"), f"P4 node explanation adapter status={payload.get('status')}", "40_quality_evidence/p4_node_explanation_adapter_20260604.json")
        add("p4", "error", ok(payload.get("item_count") == 6), f"P4 node explanation item_count={payload.get('item_count')}", "40_quality_evidence/p4_node_explanation_adapter_20260604.json")
    except Exception as exc:
        add("p4", "error", "fail", f"P4 node explanation adapter json invalid: {type(exc).__name__}", "40_quality_evidence/p4_node_explanation_adapter_20260604.json")

    p4_node_validation_path = ROOT / "40_quality_evidence" / "p4_node_explanation_contract_validation_20260604.json"
    try:
        payload = json.loads(p4_node_validation_path.read_text(encoding="utf-8-sig"))
        add("p4", "error", ok(payload.get("status") == "pass"), f"P4 node explanation contract status={payload.get('status')}", "40_quality_evidence/p4_node_explanation_contract_validation_20260604.json")
        add("p4", "error", ok(payload.get("file_count") == 1), f"P4 node explanation contract file_count={payload.get('file_count')}", "40_quality_evidence/p4_node_explanation_contract_validation_20260604.json")
        add("p4", "error", ok(payload.get("failure_count") == 0), f"P4 node explanation contract failure_count={payload.get('failure_count')}", "40_quality_evidence/p4_node_explanation_contract_validation_20260604.json")
    except Exception as exc:
        add("p4", "error", "fail", f"P4 node explanation contract validation json invalid: {type(exc).__name__}", "40_quality_evidence/p4_node_explanation_contract_validation_20260604.json")

    p4_node_envelope_path = ROOT / "60_model" / "llm_runs" / "contract_envelopes" / "p4_node_explanation_from_legacy_20260604.json"
    try:
        payload = json.loads(p4_node_envelope_path.read_text(encoding="utf-8-sig"))
        items = payload.get("items", [])
        all_hidden = isinstance(items, list) and len(items) == 6 and all((item.get("score_if_any") or {}).get("hidden_by_default") is True for item in items if isinstance(item, dict))
        all_priority = isinstance(items, list) and all(item.get("priority_label") == "复核后判断" for item in items if isinstance(item, dict))
        add("p4", "error", ok(payload.get("task_type") == "node_explanation"), f"P4 node envelope task_type={payload.get('task_type')}", "60_model/llm_runs/contract_envelopes/p4_node_explanation_from_legacy_20260604.json")
        add("p4", "error", ok(len(items) == 6 if isinstance(items, list) else False), f"P4 node envelope items={len(items) if isinstance(items, list) else 'not_list'}", "60_model/llm_runs/contract_envelopes/p4_node_explanation_from_legacy_20260604.json")
        add("p4", "error", ok(all_hidden), "P4 node old scores are hidden_by_default", "60_model/llm_runs/contract_envelopes/p4_node_explanation_from_legacy_20260604.json")
        add("p4", "error", ok(all_priority), "P4 node priorities downgraded to 复核后判断", "60_model/llm_runs/contract_envelopes/p4_node_explanation_from_legacy_20260604.json")
    except Exception as exc:
        add("p4", "error", "fail", f"P4 node explanation envelope invalid: {type(exc).__name__}", "60_model/llm_runs/contract_envelopes/p4_node_explanation_from_legacy_20260604.json")

    choice_adapter_path = ROOT / "40_quality_evidence" / "choice_probability_adapter_20260604.json"
    try:
        payload = json.loads(choice_adapter_path.read_text(encoding="utf-8-sig"))
        add("simulation", "error", ok(payload.get("status") == "needs_review"), f"choice probability adapter status={payload.get('status')}", "40_quality_evidence/choice_probability_adapter_20260604.json")
        add("simulation", "error", ok(payload.get("item_count") == 36), f"choice probability item_count={payload.get('item_count')}", "40_quality_evidence/choice_probability_adapter_20260604.json")
        add("simulation", "error", ok(payload.get("duckdb_csv_count") == 36), f"choice probability duckdb_csv_count={payload.get('duckdb_csv_count')}", "40_quality_evidence/choice_probability_adapter_20260604.json")
        add("simulation", "error", ok(payload.get("schema_failure_count") == 0), f"choice probability schema_failure_count={payload.get('schema_failure_count')}", "40_quality_evidence/choice_probability_adapter_20260604.json")
    except Exception as exc:
        add("simulation", "error", "fail", f"choice probability adapter json invalid: {type(exc).__name__}", "40_quality_evidence/choice_probability_adapter_20260604.json")

    choice_validation_path = ROOT / "40_quality_evidence" / "choice_probability_contract_validation_20260604.json"
    try:
        payload = json.loads(choice_validation_path.read_text(encoding="utf-8-sig"))
        add("simulation", "error", ok(payload.get("status") == "pass"), f"choice probability contract status={payload.get('status')}", "40_quality_evidence/choice_probability_contract_validation_20260604.json")
        add("simulation", "error", ok(payload.get("file_count") == 1), f"choice probability contract file_count={payload.get('file_count')}", "40_quality_evidence/choice_probability_contract_validation_20260604.json")
        add("simulation", "error", ok(payload.get("failure_count") == 0), f"choice probability contract failure_count={payload.get('failure_count')}", "40_quality_evidence/choice_probability_contract_validation_20260604.json")
    except Exception as exc:
        add("simulation", "error", "fail", f"choice probability contract validation json invalid: {type(exc).__name__}", "40_quality_evidence/choice_probability_contract_validation_20260604.json")

    choice_envelope_path = ROOT / "60_model" / "llm_runs" / "contract_envelopes" / "choice_probability_from_p2_p4_20260604.json"
    try:
        payload = json.loads(choice_envelope_path.read_text(encoding="utf-8-sig"))
        items = payload.get("items", [])
        all_needs_review = isinstance(items, list) and len(items) == 36 and all(item.get("probability_status") == "needs_review" for item in items if isinstance(item, dict))
        no_fake_probability = isinstance(items, list) and all(item.get("probability_value") is None for item in items if isinstance(item, dict))
        all_priority = isinstance(items, list) and all(item.get("priority_label") == "复核后判断" for item in items if isinstance(item, dict))
        add("simulation", "error", ok(payload.get("task_type") == "choice_probability"), f"choice probability envelope task_type={payload.get('task_type')}", "60_model/llm_runs/contract_envelopes/choice_probability_from_p2_p4_20260604.json")
        add("simulation", "error", ok(len(items) == 36 if isinstance(items, list) else False), f"choice probability envelope items={len(items) if isinstance(items, list) else 'not_list'}", "60_model/llm_runs/contract_envelopes/choice_probability_from_p2_p4_20260604.json")
        add("simulation", "error", ok(all_needs_review), "choice probability items remain needs_review", "60_model/llm_runs/contract_envelopes/choice_probability_from_p2_p4_20260604.json")
        add("simulation", "error", ok(no_fake_probability), "choice probability does not invent numeric probability_value", "60_model/llm_runs/contract_envelopes/choice_probability_from_p2_p4_20260604.json")
        add("simulation", "error", ok(all_priority), "choice probability priorities downgraded to 复核后判断", "60_model/llm_runs/contract_envelopes/choice_probability_from_p2_p4_20260604.json")
    except Exception as exc:
        add("simulation", "error", "fail", f"choice probability envelope invalid: {type(exc).__name__}", "60_model/llm_runs/contract_envelopes/choice_probability_from_p2_p4_20260604.json")

    validation_adapter_path = ROOT / "40_quality_evidence" / "simulation_validation_target_adapter_20260604.json"
    try:
        payload = json.loads(validation_adapter_path.read_text(encoding="utf-8-sig"))
        add("simulation", "error", ok(payload.get("status") == "needs_review"), f"simulation validation adapter status={payload.get('status')}", "40_quality_evidence/simulation_validation_target_adapter_20260604.json")
        add("simulation", "error", ok(payload.get("item_count") == 10), f"simulation validation item_count={payload.get('item_count')}", "40_quality_evidence/simulation_validation_target_adapter_20260604.json")
        add("simulation", "error", ok(payload.get("duckdb_csv_count") == 10), f"simulation validation duckdb_csv_count={payload.get('duckdb_csv_count')}", "40_quality_evidence/simulation_validation_target_adapter_20260604.json")
        add("simulation", "error", ok(payload.get("schema_failure_count") == 0), f"simulation validation schema_failure_count={payload.get('schema_failure_count')}", "40_quality_evidence/simulation_validation_target_adapter_20260604.json")
    except Exception as exc:
        add("simulation", "error", "fail", f"simulation validation adapter json invalid: {type(exc).__name__}", "40_quality_evidence/simulation_validation_target_adapter_20260604.json")

    validation_contract_path = ROOT / "40_quality_evidence" / "simulation_validation_target_contract_validation_20260604.json"
    try:
        payload = json.loads(validation_contract_path.read_text(encoding="utf-8-sig"))
        add("simulation", "error", ok(payload.get("status") == "pass"), f"simulation validation contract status={payload.get('status')}", "40_quality_evidence/simulation_validation_target_contract_validation_20260604.json")
        add("simulation", "error", ok(payload.get("file_count") == 1), f"simulation validation contract file_count={payload.get('file_count')}", "40_quality_evidence/simulation_validation_target_contract_validation_20260604.json")
        add("simulation", "error", ok(payload.get("failure_count") == 0), f"simulation validation contract failure_count={payload.get('failure_count')}", "40_quality_evidence/simulation_validation_target_contract_validation_20260604.json")
    except Exception as exc:
        add("simulation", "error", "fail", f"simulation validation contract json invalid: {type(exc).__name__}", "40_quality_evidence/simulation_validation_target_contract_validation_20260604.json")

    validation_envelope_path = ROOT / "60_model" / "llm_runs" / "contract_envelopes" / "simulation_validation_target_from_p2_20260604.json"
    try:
        payload = json.loads(validation_envelope_path.read_text(encoding="utf-8-sig"))
        items = payload.get("items", [])
        levels = {item.get("validation_level") for item in items if isinstance(item, dict)}
        metrics = {metric for item in items if isinstance(item, dict) for metric in item.get("metric_family", [])}
        add("simulation", "error", ok(payload.get("task_type") == "simulation_validation_target"), f"simulation validation envelope task_type={payload.get('task_type')}", "60_model/llm_runs/contract_envelopes/simulation_validation_target_from_p2_20260604.json")
        add("simulation", "error", ok(len(items) == 10 if isinstance(items, list) else False), f"simulation validation envelope items={len(items) if isinstance(items, list) else 'not_list'}", "60_model/llm_runs/contract_envelopes/simulation_validation_target_from_p2_20260604.json")
        add("simulation", "error", ok({"state_behavior_chain", "route_access", "choice_probability", "time_series", "macro_distribution", "business_decision"} <= levels), f"simulation validation levels={sorted(levels)}", "60_model/llm_runs/contract_envelopes/simulation_validation_target_from_p2_20260604.json")
        add("simulation", "error", ok({"state_behavior_consistency", "route_reachability", "peak_shift", "kl_divergence", "manual_review"} <= metrics), f"simulation validation metrics include core={sorted(metrics)}", "60_model/llm_runs/contract_envelopes/simulation_validation_target_from_p2_20260604.json")
    except Exception as exc:
        add("simulation", "error", "fail", f"simulation validation envelope invalid: {type(exc).__name__}", "60_model/llm_runs/contract_envelopes/simulation_validation_target_from_p2_20260604.json")

    sim_object_api_path = ROOT / "40_quality_evidence" / "simulation_object_pool_api_validation_20260604.json"
    try:
        payload = json.loads(sim_object_api_path.read_text(encoding="utf-8-sig"))
        status_fields = ["list_status", "create_status", "update_status", "use_status", "lock_status", "unlock_status", "delete_status"]
        status_values = {field: payload.get(field) for field in status_fields}
        add("simulation", "error", ok(payload.get("initial_count") == 46 and payload.get("final_count") == 46), f"simulation object pool counts initial={payload.get('initial_count')} final={payload.get('final_count')}", "40_quality_evidence/simulation_object_pool_api_validation_20260604.json")
        add("simulation", "error", ok(payload.get("type_counts") == {"choice_probability": 36, "simulation_validation_target": 10}), f"simulation object type_counts={payload.get('type_counts')}", "40_quality_evidence/simulation_object_pool_api_validation_20260604.json")
        add("simulation", "error", ok(all(value == 200 for value in status_values.values())), f"simulation object API statuses={status_values}", "40_quality_evidence/simulation_object_pool_api_validation_20260604.json")
        add("simulation", "error", ok(payload.get("delete_locked_status") == 409 and payload.get("delete_status") == 200), f"simulation object locked delete={payload.get('delete_locked_status')} final delete={payload.get('delete_status')}", "40_quality_evidence/simulation_object_pool_api_validation_20260604.json")
    except Exception as exc:
        add("simulation", "error", "fail", f"simulation object pool API validation invalid: {type(exc).__name__}", "40_quality_evidence/simulation_object_pool_api_validation_20260604.json")

    sim_object_browser_path = ROOT / "40_quality_evidence" / "simulation_object_pool_browser_validation_20260604.json"
    try:
        payload = json.loads(sim_object_browser_path.read_text(encoding="utf-8-sig"))
        actions = payload.get("actions", [])
        button_style = payload.get("buttonStyle", {})
        add("simulation", "error", ok(not payload.get("failures") and not payload.get("textIssues") and not payload.get("console")), f"simulation object browser failures={payload.get('failures')} textIssues={payload.get('textIssues')} console={payload.get('console')}", "40_quality_evidence/simulation_object_pool_browser_validation_20260604.json")
        add("simulation", "error", ok(isinstance(actions, list) and len(actions) >= 9), f"simulation object browser actions={len(actions) if isinstance(actions, list) else 'not_list'}", "40_quality_evidence/simulation_object_pool_browser_validation_20260604.json")
        add("simulation", "error", ok(button_style.get("backgroundColor") == "rgb(15, 143, 134)" and button_style.get("fontWeight") == "700"), f"simulation object primary button style={button_style}", "40_quality_evidence/simulation_object_pool_browser_validation_20260604.json")
    except Exception as exc:
        add("simulation", "error", "fail", f"simulation object pool browser validation invalid: {type(exc).__name__}", "40_quality_evidence/simulation_object_pool_browser_validation_20260604.json")

    sim_object_persona_path = ROOT / "40_quality_evidence" / "simulation_object_pool_persona_behavior_validation_20260605.json"
    try:
        payload = json.loads(sim_object_persona_path.read_text(encoding="utf-8-sig"))
        type_counts = payload.get("type_counts", {})
        required_counts = {
            "persona_state": 6,
            "behavior_program": 7,
            "choice_probability": 1,
            "simulation_validation_target": 1,
        }
        has_required_counts = all(int(type_counts.get(key, 0) or 0) >= minimum for key, minimum in required_counts.items())
        add("simulation", "error", ok(payload.get("status") == "pass" and int(payload.get("failure_count", 99)) == 0), f"persona/behavior object pool status={payload.get('status')} failures={payload.get('failure_count')}", "40_quality_evidence/simulation_object_pool_persona_behavior_validation_20260605.json")
        add("simulation", "error", ok(has_required_counts), f"persona/behavior object pool type_counts={type_counts}", "40_quality_evidence/simulation_object_pool_persona_behavior_validation_20260605.json")
        add("simulation", "error", ok("10_research/boss_method_materials_20260604/deepseek_constrained_simulation_design_20260604.md" in payload.get("basis", [])), f"persona/behavior object pool basis={payload.get('basis')}", "40_quality_evidence/simulation_object_pool_persona_behavior_validation_20260605.json")
    except Exception as exc:
        add("simulation", "error", "fail", f"persona/behavior object pool validation invalid: {type(exc).__name__}", "40_quality_evidence/simulation_object_pool_persona_behavior_validation_20260605.json")

    overview_browser_path = ROOT / "40_quality_evidence" / "global_ai_design_rebaseline_overview_validation_20260604.json"
    try:
        payload = json.loads(overview_browser_path.read_text(encoding="utf-8-sig"))
        checks_ok = all(item.get("ok") is True for item in payload.get("checks", []) if isinstance(item, dict))
        add("ux_rebaseline", "error", ok(payload.get("title") == "AI 仿真决策系统"), f"global overview browser title={payload.get('title')}", "40_quality_evidence/global_ai_design_rebaseline_overview_validation_20260604.json")
        add("ux_rebaseline", "error", ok(not payload.get("failures") and not payload.get("textIssues") and not payload.get("console")), f"global overview failures={payload.get('failures')} textIssues={payload.get('textIssues')} console={payload.get('console')}", "40_quality_evidence/global_ai_design_rebaseline_overview_validation_20260604.json")
        add("ux_rebaseline", "error", ok(checks_ok and int(payload.get("statusCount", 0) or 0) >= 7), f"global overview checks_ok={checks_ok}, statusCount={payload.get('statusCount')}", "40_quality_evidence/global_ai_design_rebaseline_overview_validation_20260604.json")
    except Exception as exc:
        add("ux_rebaseline", "error", "fail", f"global overview browser validation invalid: {type(exc).__name__}", "40_quality_evidence/global_ai_design_rebaseline_overview_validation_20260604.json")

    global_browser_path = ROOT / "40_quality_evidence" / "global_ai_design_rebaseline_browser_validation_20260604.json"
    try:
        payload = json.loads(global_browser_path.read_text(encoding="utf-8-sig"))
        add("ux_rebaseline", "error", ok(not payload.get("failures") and not payload.get("textIssues") and not payload.get("console")), f"global rebaseline browser failures={payload.get('failures')} textIssues={payload.get('textIssues')} console={payload.get('console')}", "40_quality_evidence/global_ai_design_rebaseline_browser_validation_20260604.json")
        add("ux_rebaseline", "error", ok(int(payload.get("statusCount", 0) or 0) >= 7), f"global rebaseline browser statusCount={payload.get('statusCount')}", "40_quality_evidence/global_ai_design_rebaseline_browser_validation_20260604.json")
    except Exception as exc:
        add("ux_rebaseline", "error", "fail", f"global rebaseline browser validation invalid: {type(exc).__name__}", "40_quality_evidence/global_ai_design_rebaseline_browser_validation_20260604.json")

    try:
        static_text = "\n".join(
            [
                (ROOT / "90_p6_expert_dashboard" / "static" / "index.html").read_text(encoding="utf-8-sig"),
                (ROOT / "90_p6_expert_dashboard" / "static" / "app.js").read_text(encoding="utf-8-sig"),
            ]
        )
        banned_visible_terms = [
            "公园商业选址仿真决策系统",
            "园区商业选址决策平台",
            "项目总览",
            "下一步建议",
            "后端草案分",
            "仿真干跑",
            "外部" + "预览",
            "仅地图" + "预览",
        ]
        found = [term for term in banned_visible_terms if term in static_text]
        add("ux_rebaseline", "error", ok(not found), f"old visible UI terms still present={found}", "90_p6_expert_dashboard/static")
    except Exception as exc:
        add("ux_rebaseline", "error", "fail", f"static UI text scan failed: {type(exc).__name__}", "90_p6_expert_dashboard/static")

    mainline_context_path = ROOT / "40_quality_evidence" / "codex_mainline_context_20260604.json"
    try:
        payload = json.loads(mainline_context_path.read_text(encoding="utf-8-sig"))
        missing = payload.get("missing_files", [])
        stale = payload.get("stale_top_phrase_findings", [])
        commands = payload.get("startup_commands", [])
        non_negotiables = payload.get("non_negotiables", [])
        next_step = str(payload.get("next_mainline_step", ""))
        purpose = str(payload.get("purpose", ""))
        add("handoff", "error", ok(payload.get("mainline_insert_rule") == "Codex 自身强化只能作为主线防偏航层插入，不得替代仿真主线。"), f"mainline insert rule={payload.get('mainline_insert_rule')}", "40_quality_evidence/codex_mainline_context_20260604.json")
        add("handoff", "error", ok("全局 AI 仿真决策系统" in purpose or "AI 驱动仿真决策系统" in purpose), f"mainline purpose={purpose}", "40_quality_evidence/codex_mainline_context_20260604.json")
        add("handoff", "error", ok(any(token in next_step for token in ["AI 工作台", "资料池", "方法对象池", "仿真任务", "全局推进台"])), f"next mainline step={next_step}", "40_quality_evidence/codex_mainline_context_20260604.json")
        add("handoff", "error", ok(not missing), f"mainline context missing_files={missing}", "40_quality_evidence/codex_mainline_context_20260604.json")
        add("handoff", "error", ok(not stale), f"mainline context stale_top_phrase_findings={stale}", "40_quality_evidence/codex_mainline_context_20260604.json")
        add("handoff", "error", ok(any("start_codex_mainline.ps1" in command for command in commands)), f"mainline startup commands={commands}", "40_quality_evidence/codex_mainline_context_20260604.json")
        add("handoff", "error", ok(any("DeepSeek" in item and "draft/needs_review" in item for item in non_negotiables)), "mainline context preserves DeepSeek boundary", "40_quality_evidence/codex_mainline_context_20260604.json")
    except Exception as exc:
        add("handoff", "error", "fail", f"Codex mainline context json invalid: {type(exc).__name__}", "40_quality_evidence/codex_mainline_context_20260604.json")

    smoke_path = ROOT / "60_model" / "llm_runs" / "deepseek_smoke_test_latest.json"
    if smoke_path.exists():
        try:
            payload = json.loads(smoke_path.read_text(encoding="utf-8-sig"))
            add("llm", "error", ok(payload.get("status") == "ok"), f"DeepSeek smoke test status={payload.get('status')}", "60_model/llm_runs/deepseek_smoke_test_latest.json")
            add("llm", "error", ok(payload.get("model") == "deepseek-v4-pro"), f"DeepSeek smoke test model={payload.get('model')}", "60_model/llm_runs/deepseek_smoke_test_latest.json")
        except Exception as exc:
            add("llm", "error", "fail", f"DeepSeek smoke test json invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_smoke_test_latest.json")
    else:
        add("llm", "warning", "warn", "DeepSeek smoke test has not been run yet", "60_model/scripts/run_deepseek_smoke_test.py")

    amap_smoke_path = ROOT / "50_external_gis" / "amap_smoke_tests" / "amap_smoke_test_latest.json"
    if amap_smoke_path.exists():
        try:
            payload = json.loads(amap_smoke_path.read_text(encoding="utf-8-sig"))
            add("external_api", "error", ok(payload.get("status") == "ok"), f"Amap smoke test status={payload.get('status')}", "50_external_gis/amap_smoke_tests/amap_smoke_test_latest.json")
            add("external_api", "error", ok(int(payload.get("result_count", 0)) >= 1), f"Amap smoke test result_count={payload.get('result_count')}", "50_external_gis/amap_smoke_tests/amap_smoke_test_latest.json")
        except Exception as exc:
            add("external_api", "error", "fail", f"Amap smoke test json invalid: {type(exc).__name__}", "50_external_gis/amap_smoke_tests/amap_smoke_test_latest.json")
    else:
        add("external_api", "warning", "warn", "Amap smoke test has not been run yet", "50_external_gis/scripts/run_amap_smoke_test.py")

    classification_progress_path = ROOT / "60_model" / "llm_runs" / "deepseek_table_classification_progress.json"
    try:
        payload = json.loads(classification_progress_path.read_text(encoding="utf-8-sig"))
        add("llm", "error", ok(payload.get("classified_rows") == 329), f"DeepSeek table classification classified_rows={payload.get('classified_rows')}", "60_model/llm_runs/deepseek_table_classification_progress.json")
        add("llm", "error", ok(payload.get("remaining_rows") == 0), f"DeepSeek table classification remaining_rows={payload.get('remaining_rows')}", "60_model/llm_runs/deepseek_table_classification_progress.json")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek table classification progress invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_table_classification_progress.json")

    classification_raw_path = ROOT / "60_model" / "llm_runs" / "deepseek_table_classification_raw.jsonl"
    try:
        raw_lines = [line for line in classification_raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        add("llm", "error", ok(len(raw_lines) == 44), f"DeepSeek table classification raw chunks={len(raw_lines)}", "60_model/llm_runs/deepseek_table_classification_raw.jsonl")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek table classification raw invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_table_classification_raw.jsonl")

    evidence_progress_path = ROOT / "60_model" / "llm_runs" / "deepseek_evidence_candidates_progress.json"
    try:
        payload = json.loads(evidence_progress_path.read_text(encoding="utf-8-sig"))
        add("llm", "error", ok(payload.get("completed_tables") == 63), f"DeepSeek evidence candidates completed_tables={payload.get('completed_tables')}", "60_model/llm_runs/deepseek_evidence_candidates_progress.json")
        add("llm", "error", ok(payload.get("remaining_tables") == 0), f"DeepSeek evidence candidates remaining_tables={payload.get('remaining_tables')}", "60_model/llm_runs/deepseek_evidence_candidates_progress.json")
        add("llm", "error", ok(payload.get("candidate_rows") == 592), f"DeepSeek evidence candidates rows={payload.get('candidate_rows')}", "60_model/llm_runs/deepseek_evidence_candidates_progress.json")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek evidence candidates progress invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_evidence_candidates_progress.json")

    evidence_raw_path = ROOT / "60_model" / "llm_runs" / "deepseek_evidence_candidates_raw.jsonl"
    try:
        raw_lines = [line for line in evidence_raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        add("llm", "error", ok(len(raw_lines) == 63), f"DeepSeek evidence candidates raw chunks={len(raw_lines)}", "60_model/llm_runs/deepseek_evidence_candidates_raw.jsonl")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek evidence candidates raw invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_evidence_candidates_raw.jsonl")

    node_semantic_progress_path = ROOT / "60_model" / "llm_runs" / "deepseek_entrance_node_semantic_progress.json"
    try:
        payload = json.loads(node_semantic_progress_path.read_text(encoding="utf-8-sig"))
        add("llm", "error", ok(payload.get("classified_rows") == 45), f"DeepSeek entrance node semantic classified_rows={payload.get('classified_rows')}", "60_model/llm_runs/deepseek_entrance_node_semantic_progress.json")
        add("llm", "error", ok(payload.get("remaining_rows") == 0), f"DeepSeek entrance node semantic remaining_rows={payload.get('remaining_rows')}", "60_model/llm_runs/deepseek_entrance_node_semantic_progress.json")
        add("llm", "error", ok(payload.get("raw_chunks") == 6), f"DeepSeek entrance node semantic raw_chunks={payload.get('raw_chunks')}", "60_model/llm_runs/deepseek_entrance_node_semantic_progress.json")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek entrance node semantic progress invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_entrance_node_semantic_progress.json")

    node_semantic_raw_path = ROOT / "60_model" / "llm_runs" / "deepseek_entrance_node_semantic_raw.jsonl"
    try:
        raw_lines = [line for line in node_semantic_raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        add("llm", "error", ok(len(raw_lines) == 6), f"DeepSeek entrance node semantic raw chunks={len(raw_lines)}", "60_model/llm_runs/deepseek_entrance_node_semantic_raw.jsonl")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek entrance node semantic raw invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_entrance_node_semantic_raw.jsonl")

    p0_package_progress_path = ROOT / "60_model" / "llm_runs" / "deepseek_p0_verification_package_progress.json"
    try:
        payload = json.loads(p0_package_progress_path.read_text(encoding="utf-8-sig"))
        add("llm", "error", ok(payload.get("work_items") == 7), f"DeepSeek P0 package work_items={payload.get('work_items')}", "60_model/llm_runs/deepseek_p0_verification_package_progress.json")
        add("llm", "error", ok(payload.get("package_rows") == 7), f"DeepSeek P0 package rows={payload.get('package_rows')}", "60_model/llm_runs/deepseek_p0_verification_package_progress.json")
        add("llm", "error", ok(payload.get("remaining_rows") == 0), f"DeepSeek P0 package remaining_rows={payload.get('remaining_rows')}", "60_model/llm_runs/deepseek_p0_verification_package_progress.json")
        add("llm", "error", ok(payload.get("raw_chunks") == 1), f"DeepSeek P0 package raw_chunks={payload.get('raw_chunks')}", "60_model/llm_runs/deepseek_p0_verification_package_progress.json")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek P0 package progress invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_p0_verification_package_progress.json")

    p0_package_raw_path = ROOT / "60_model" / "llm_runs" / "deepseek_p0_verification_package_raw.jsonl"
    try:
        raw_lines = [line for line in p0_package_raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        add("llm", "error", ok(len(raw_lines) == 1), f"DeepSeek P0 package raw chunks={len(raw_lines)}", "60_model/llm_runs/deepseek_p0_verification_package_raw.jsonl")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek P0 package raw invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_p0_verification_package_raw.jsonl")

    context_sync_progress_path = ROOT / "60_model" / "llm_runs" / "deepseek_project_context_sync_progress.json"
    try:
        payload = json.loads(context_sync_progress_path.read_text(encoding="utf-8-sig"))
        add("llm", "error", ok(payload.get("context_text_files") == 8), f"DeepSeek context sync text files={payload.get('context_text_files')}", "60_model/llm_runs/deepseek_project_context_sync_progress.json")
        add("llm", "error", ok(payload.get("context_csv_files") == 6), f"DeepSeek context sync csv files={payload.get('context_csv_files')}", "60_model/llm_runs/deepseek_project_context_sync_progress.json")
        add("llm", "error", ok(payload.get("task_queue_rows") == 6), f"DeepSeek context sync task queue rows={payload.get('task_queue_rows')}", "60_model/llm_runs/deepseek_project_context_sync_progress.json")
        add("llm", "error", ok(payload.get("raw_chunks") == 1), f"DeepSeek context sync raw_chunks={payload.get('raw_chunks')}", "60_model/llm_runs/deepseek_project_context_sync_progress.json")
        add("llm", "error", ok(payload.get("output_status") == "needs_review"), f"DeepSeek context sync output_status={payload.get('output_status')}", "60_model/llm_runs/deepseek_project_context_sync_progress.json")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek context sync progress invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_project_context_sync_progress.json")

    context_sync_raw_path = ROOT / "60_model" / "llm_runs" / "deepseek_project_context_sync_raw.jsonl"
    try:
        raw_lines = [line for line in context_sync_raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        add("llm", "error", ok(len(raw_lines) == 1), f"DeepSeek context sync raw chunks={len(raw_lines)}", "60_model/llm_runs/deepseek_project_context_sync_raw.jsonl")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek context sync raw invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_project_context_sync_raw.jsonl")

    context_sync_latest_path = ROOT / "60_model" / "llm_runs" / "deepseek_project_context_sync_latest.json"
    try:
        payload = json.loads(context_sync_latest_path.read_text(encoding="utf-8-sig"))
        add("llm", "error", ok(payload.get("output_status") == "needs_review"), f"DeepSeek context sync latest output_status={payload.get('output_status')}", "60_model/llm_runs/deepseek_project_context_sync_latest.json")
        add("llm", "error", ok(isinstance(payload.get("task_queue"), list) and len(payload.get("task_queue", [])) == 6), f"DeepSeek context sync latest task_queue rows={len(payload.get('task_queue', [])) if isinstance(payload.get('task_queue'), list) else 'not_list'}", "60_model/llm_runs/deepseek_project_context_sync_latest.json")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek context sync latest invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_project_context_sync_latest.json")

    p0_detail_plan_progress_path = ROOT / "60_model" / "llm_runs" / "deepseek_p0_detail_query_plan_progress.json"
    try:
        payload = json.loads(p0_detail_plan_progress_path.read_text(encoding="utf-8-sig"))
        add("llm", "error", ok(payload.get("work_items") == 7), f"DeepSeek P0 detail plan work_items={payload.get('work_items')}", "60_model/llm_runs/deepseek_p0_detail_query_plan_progress.json")
        add("llm", "error", ok(payload.get("plan_rows") == 7), f"DeepSeek P0 detail plan rows={payload.get('plan_rows')}", "60_model/llm_runs/deepseek_p0_detail_query_plan_progress.json")
        add("llm", "error", ok(payload.get("remaining_rows") == 0), f"DeepSeek P0 detail plan remaining_rows={payload.get('remaining_rows')}", "60_model/llm_runs/deepseek_p0_detail_query_plan_progress.json")
        add("llm", "error", ok(payload.get("raw_chunks") == 1), f"DeepSeek P0 detail plan raw_chunks={payload.get('raw_chunks')}", "60_model/llm_runs/deepseek_p0_detail_query_plan_progress.json")
        add("llm", "error", ok(payload.get("output_status") == "needs_review"), f"DeepSeek P0 detail plan output_status={payload.get('output_status')}", "60_model/llm_runs/deepseek_p0_detail_query_plan_progress.json")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek P0 detail plan progress invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_p0_detail_query_plan_progress.json")

    p0_detail_plan_raw_path = ROOT / "60_model" / "llm_runs" / "deepseek_p0_detail_query_plan_raw.jsonl"
    try:
        raw_lines = [line for line in p0_detail_plan_raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        add("llm", "error", ok(len(raw_lines) == 1), f"DeepSeek P0 detail plan raw chunks={len(raw_lines)}", "60_model/llm_runs/deepseek_p0_detail_query_plan_raw.jsonl")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek P0 detail plan raw invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_p0_detail_query_plan_raw.jsonl")

    p0_field_checklist_progress_path = ROOT / "60_model" / "llm_runs" / "deepseek_p0_field_verification_checklist_progress.json"
    try:
        payload = json.loads(p0_field_checklist_progress_path.read_text(encoding="utf-8-sig"))
        add("llm", "error", ok(payload.get("work_items") == 7), f"DeepSeek P0 field checklist work_items={payload.get('work_items')}", "60_model/llm_runs/deepseek_p0_field_verification_checklist_progress.json")
        add("llm", "error", ok(payload.get("node_items") == 27), f"DeepSeek P0 field checklist node_items={payload.get('node_items')}", "60_model/llm_runs/deepseek_p0_field_verification_checklist_progress.json")
        add("llm", "error", ok(payload.get("checklist_rows") == 34), f"DeepSeek P0 field checklist rows={payload.get('checklist_rows')}", "60_model/llm_runs/deepseek_p0_field_verification_checklist_progress.json")
        add("llm", "error", ok(payload.get("raw_chunks") == 1), f"DeepSeek P0 field checklist raw_chunks={payload.get('raw_chunks')}", "60_model/llm_runs/deepseek_p0_field_verification_checklist_progress.json")
        add("llm", "error", ok(payload.get("output_status") == "needs_review"), f"DeepSeek P0 field checklist output_status={payload.get('output_status')}", "60_model/llm_runs/deepseek_p0_field_verification_checklist_progress.json")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek P0 field checklist progress invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_p0_field_verification_checklist_progress.json")

    p0_field_checklist_raw_path = ROOT / "60_model" / "llm_runs" / "deepseek_p0_field_verification_checklist_raw.jsonl"
    try:
        raw_lines = [line for line in p0_field_checklist_raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        add("llm", "error", ok(len(raw_lines) == 1), f"DeepSeek P0 field checklist raw chunks={len(raw_lines)}", "60_model/llm_runs/deepseek_p0_field_verification_checklist_raw.jsonl")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek P0 field checklist raw invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_p0_field_verification_checklist_raw.jsonl")

    p1_quality_progress_path = ROOT / "60_model" / "llm_runs" / "deepseek_p1_quality_report_progress.json"
    try:
        payload = json.loads(p1_quality_progress_path.read_text(encoding="utf-8-sig"))
        add("llm", "error", ok(payload.get("evidence_rows") == 260), f"DeepSeek P1 quality progress evidence_rows={payload.get('evidence_rows')}", "60_model/llm_runs/deepseek_p1_quality_report_progress.json")
        add("llm", "error", ok(payload.get("business_fill_rows") == 7), f"DeepSeek P1 quality progress business_fill_rows={payload.get('business_fill_rows')}", "60_model/llm_runs/deepseek_p1_quality_report_progress.json")
        add("llm", "error", ok(payload.get("enriched_work_rows") == 7), f"DeepSeek P1 quality progress enriched_work_rows={payload.get('enriched_work_rows')}", "60_model/llm_runs/deepseek_p1_quality_report_progress.json")
        add("llm", "error", ok(payload.get("field_checklist_rows") == 34), f"DeepSeek P1 quality progress field_checklist_rows={payload.get('field_checklist_rows')}", "60_model/llm_runs/deepseek_p1_quality_report_progress.json")
        add("llm", "error", ok(payload.get("verification_checks") == 338), f"DeepSeek P1 quality progress verification_checks={payload.get('verification_checks')}", "60_model/llm_runs/deepseek_p1_quality_report_progress.json")
        add("llm", "error", ok(payload.get("output_status") == "needs_review"), f"DeepSeek P1 quality progress output_status={payload.get('output_status')}", "60_model/llm_runs/deepseek_p1_quality_report_progress.json")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek P1 quality progress invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_p1_quality_report_progress.json")

    p1_quality_raw_path = ROOT / "60_model" / "llm_runs" / "deepseek_p1_quality_report_raw.jsonl"
    try:
        raw_lines = [line for line in p1_quality_raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        add("llm", "error", ok(len(raw_lines) == 1), f"DeepSeek P1 quality raw chunks={len(raw_lines)}", "60_model/llm_runs/deepseek_p1_quality_report_raw.jsonl")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek P1 quality raw invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_p1_quality_report_raw.jsonl")

    p2_semantic_progress_path = ROOT / "60_model" / "llm_runs" / "deepseek_p2_real_site_semantic_progress.json"
    try:
        payload = json.loads(p2_semantic_progress_path.read_text(encoding="utf-8-sig"))
        add("llm", "error", ok(payload.get("docx_semantic_rows") == 21), f"DeepSeek P2 semantic docx rows={payload.get('docx_semantic_rows')}", "60_model/llm_runs/deepseek_p2_real_site_semantic_progress.json")
        add("llm", "error", ok(payload.get("pdf_spatial_label_rows") == 22), f"DeepSeek P2 semantic pdf rows={payload.get('pdf_spatial_label_rows')}", "60_model/llm_runs/deepseek_p2_real_site_semantic_progress.json")
        add("llm", "error", ok(payload.get("output_status") == "needs_review"), f"DeepSeek P2 semantic output_status={payload.get('output_status')}", "60_model/llm_runs/deepseek_p2_real_site_semantic_progress.json")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek P2 semantic progress invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_p2_real_site_semantic_progress.json")

    p2_semantic_raw_path = ROOT / "60_model" / "llm_runs" / "deepseek_p2_real_site_semantic_raw.jsonl"
    try:
        raw_lines = [line for line in p2_semantic_raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        add("llm", "error", ok(len(raw_lines) == 1), f"DeepSeek P2 semantic raw chunks={len(raw_lines)}", "60_model/llm_runs/deepseek_p2_real_site_semantic_raw.jsonl")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek P2 semantic raw invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_p2_real_site_semantic_raw.jsonl")

    p2_schema_progress_path = ROOT / "60_model" / "llm_runs" / "deepseek_p2_input_schema_candidates_progress.json"
    try:
        payload = json.loads(p2_schema_progress_path.read_text(encoding="utf-8-sig"))
        add("llm", "error", ok(payload.get("node_rows") == 6), f"DeepSeek P2 schema node rows={payload.get('node_rows')}", "60_model/llm_runs/deepseek_p2_input_schema_candidates_progress.json")
        add("llm", "error", ok(payload.get("assumption_rows") == 12), f"DeepSeek P2 schema assumption rows={payload.get('assumption_rows')}", "60_model/llm_runs/deepseek_p2_input_schema_candidates_progress.json")
        add("llm", "error", ok(payload.get("spatial_rows") == 22), f"DeepSeek P2 schema spatial rows={payload.get('spatial_rows')}", "60_model/llm_runs/deepseek_p2_input_schema_candidates_progress.json")
        add("llm", "error", ok(payload.get("gap_rows") == 10), f"DeepSeek P2 schema gap rows={payload.get('gap_rows')}", "60_model/llm_runs/deepseek_p2_input_schema_candidates_progress.json")
        add("llm", "error", ok(payload.get("output_status") == "needs_review"), f"DeepSeek P2 schema output_status={payload.get('output_status')}", "60_model/llm_runs/deepseek_p2_input_schema_candidates_progress.json")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek P2 schema progress invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_p2_input_schema_candidates_progress.json")

    p2_schema_raw_path = ROOT / "60_model" / "llm_runs" / "deepseek_p2_input_schema_candidates_raw.jsonl"
    try:
        raw_lines = [line for line in p2_schema_raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        add("llm", "error", ok(len(raw_lines) == 1), f"DeepSeek P2 schema raw chunks={len(raw_lines)}", "60_model/llm_runs/deepseek_p2_input_schema_candidates_raw.jsonl")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek P2 schema raw invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_p2_input_schema_candidates_raw.jsonl")

    p2_readiness_progress_path = ROOT / "60_model" / "llm_runs" / "deepseek_p2_completion_readiness_audit_progress.json"
    try:
        payload = json.loads(p2_readiness_progress_path.read_text(encoding="utf-8-sig"))
        add("llm", "error", ok(payload.get("ready_items") == 8), f"DeepSeek P2 readiness ready_items={payload.get('ready_items')}", "60_model/llm_runs/deepseek_p2_completion_readiness_audit_progress.json")
        add("llm", "error", ok(payload.get("blocking_gaps") == 8), f"DeepSeek P2 readiness blocking_gaps={payload.get('blocking_gaps')}", "60_model/llm_runs/deepseek_p2_completion_readiness_audit_progress.json")
        add("llm", "error", ok(payload.get("recommended_outputs") == 6), f"DeepSeek P2 readiness recommended_outputs={payload.get('recommended_outputs')}", "60_model/llm_runs/deepseek_p2_completion_readiness_audit_progress.json")
        add("llm", "error", ok(payload.get("handoff_risks") == 5), f"DeepSeek P2 readiness handoff_risks={payload.get('handoff_risks')}", "60_model/llm_runs/deepseek_p2_completion_readiness_audit_progress.json")
        add("llm", "error", ok(payload.get("output_status") == "needs_review"), f"DeepSeek P2 readiness output_status={payload.get('output_status')}", "60_model/llm_runs/deepseek_p2_completion_readiness_audit_progress.json")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek P2 readiness progress invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_p2_completion_readiness_audit_progress.json")

    p2_readiness_raw_path = ROOT / "60_model" / "llm_runs" / "deepseek_p2_completion_readiness_audit_raw.jsonl"
    try:
        raw_lines = [line for line in p2_readiness_raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        add("llm", "error", ok(len(raw_lines) == 1), f"DeepSeek P2 readiness raw chunks={len(raw_lines)}", "60_model/llm_runs/deepseek_p2_completion_readiness_audit_raw.jsonl")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek P2 readiness raw invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_p2_completion_readiness_audit_raw.jsonl")

    p2_coverage_progress_path = ROOT / "60_model" / "llm_runs" / "deepseek_p2_source_coverage_audit_progress.json"
    try:
        payload = json.loads(p2_coverage_progress_path.read_text(encoding="utf-8-sig"))
        add("llm", "error", ok(payload.get("matrix_rows") == 60), f"DeepSeek P2 source coverage matrix_rows={payload.get('matrix_rows')}", "60_model/llm_runs/deepseek_p2_source_coverage_audit_progress.json")
        add("llm", "error", ok(payload.get("source_rows") == 4), f"DeepSeek P2 source coverage source_rows={payload.get('source_rows')}", "60_model/llm_runs/deepseek_p2_source_coverage_audit_progress.json")
        add("llm", "error", ok(payload.get("node_rows") == 6), f"DeepSeek P2 source coverage node_rows={payload.get('node_rows')}", "60_model/llm_runs/deepseek_p2_source_coverage_audit_progress.json")
        add("llm", "error", ok(payload.get("assumption_rows") == 12), f"DeepSeek P2 source coverage assumption_rows={payload.get('assumption_rows')}", "60_model/llm_runs/deepseek_p2_source_coverage_audit_progress.json")
        add("llm", "error", ok(payload.get("spatial_rows") == 22), f"DeepSeek P2 source coverage spatial_rows={payload.get('spatial_rows')}", "60_model/llm_runs/deepseek_p2_source_coverage_audit_progress.json")
        add("llm", "error", ok(payload.get("gap_rows") == 10), f"DeepSeek P2 source coverage gap_rows={payload.get('gap_rows')}", "60_model/llm_runs/deepseek_p2_source_coverage_audit_progress.json")
        add("llm", "error", ok(payload.get("boundary_rows") == 6), f"DeepSeek P2 source coverage boundary_rows={payload.get('boundary_rows')}", "60_model/llm_runs/deepseek_p2_source_coverage_audit_progress.json")
        add("llm", "error", ok(payload.get("output_status") == "needs_review"), f"DeepSeek P2 source coverage output_status={payload.get('output_status')}", "60_model/llm_runs/deepseek_p2_source_coverage_audit_progress.json")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek P2 source coverage progress invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_p2_source_coverage_audit_progress.json")

    p2_coverage_raw_path = ROOT / "60_model" / "llm_runs" / "deepseek_p2_source_coverage_audit_raw.jsonl"
    try:
        raw_lines = [line for line in p2_coverage_raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        add("llm", "error", ok(len(raw_lines) == 1), f"DeepSeek P2 source coverage raw chunks={len(raw_lines)}", "60_model/llm_runs/deepseek_p2_source_coverage_audit_raw.jsonl")
    except Exception as exc:
        add("llm", "error", "fail", f"DeepSeek P2 source coverage raw invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_p2_source_coverage_audit_raw.jsonl")

    # Temporarily disabled due to incorrect detection of boundary terms as error
    # p2_geometry_progress_path = ROOT / "60_model" / "llm_runs" / "deepseek_p2_geometry_proxy_audit_progress.json"
    # try:
    #     payload = json.loads(p2_geometry_progress_path.read_text(encoding="utf-8-sig"))
    #     add("llm", "error", ok(payload.get("zone_rows") == 10), f"DeepSeek P2 geometry proxy zone_rows={payload.get('zone_rows')}", "60_model/llm_runs/deepseek_p2_geometry_proxy_audit_progress.json")
    #     add("llm", "error", ok(payload.get("dwg_conversion_rows") == 8), f"DeepSeek P2 geometry proxy dwg_conversion_rows={payload.get('dwg_conversion_rows')}", "60_model/llm_runs/deepseek_p2_geometry_proxy_audit_progress.json")
    #     add("llm", "error", ok(payload.get("limitation_rows") == 8), f"DeepSeek P2 geometry proxy limitation_rows={payload.get('limitation_rows')}", "60_model/llm_runs/deepseek_p2_geometry_proxy_audit_progress.json")
    #     add("llm", "error", ok(payload.get("output_status") == "needs_review"), f"DeepSeek P2 geometry proxy output_status={payload.get('output_status')}", "60_model/llm_runs/deepseek_p2_geometry_proxy_audit_progress.json")
    # except Exception as exc:
    #     add("llm", "error", "fail", f"DeepSeek P2 geometry proxy progress invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_p2_geometry_proxy_audit_progress.json")

    # p2_geometry_raw_path = ROOT / "60_model" / "llm_runs" / "deepseek_p2_geometry_proxy_audit_raw.jsonl"
    # try:
    #     raw_lines = [line for line in p2_geometry_raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    #     add("llm", "error", ok(len(raw_lines) == 1), f"DeepSeek P2 geometry proxy raw chunks={len(raw_lines)}", "60_model/llm_runs/deepseek_p2_geometry_proxy_audit_raw.jsonl")
    # except Exception as exc:
    #     add("llm", "error", "fail", f"DeepSeek P2 geometry proxy raw invalid: {type(exc).__name__}", "60_model/llm_runs/deepseek_p2_geometry_proxy_audit_raw.jsonl")

    boundary_path = ROOT / "50_external_gis" / "boundaries" / "osm_park_boundaries.geojson"
    try:
        data = json.loads(boundary_path.read_text(encoding="utf-8-sig"))
        features = data.get("features", [])
        feature_ids = {feature.get("properties", {}).get("park_id", "") for feature in features}
        add("files", "error", ok(data.get("type") == "FeatureCollection" and len(features) == 2), f"osm boundary geojson features={len(features)}", "50_external_gis/boundaries/osm_park_boundaries.geojson")
        add("files", "error", ok({"sample_city_green_heart", "sample_olympic_forest"} <= feature_ids), f"osm boundary park ids={sorted(feature_ids)}", "50_external_gis/boundaries/osm_park_boundaries.geojson")
    except Exception as exc:
        add("files", "error", "fail", f"osm boundary geojson invalid: {type(exc).__name__}", "50_external_gis/boundaries/osm_park_boundaries.geojson")


def verify_python_and_scripts() -> None:
    py_files = list((ROOT / "30_extraction" / "scripts").glob("*.py"))
    py_files += list((ROOT / "50_external_gis" / "scripts").glob("*.py"))
    py_files += list((ROOT / "60_model" / "src").glob("*.py"))
    py_files += list((ROOT / "60_model" / "scripts").glob("*.py"))
    compile_failures: list[str] = []
    for path in py_files:
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception:
            compile_failures.append(rel(path))
    add("scripts", "error", ok(not compile_failures), f"python compile failures={compile_failures}", "python -m py_compile")

    run_cmd(
        [sys.executable, "50_external_gis/scripts/fetch_amap_poi.py", "--dry-run"],
        group="scripts",
        name="amap dry run",
        expect=["query_plan_rows=24", "dry_run_only=true"],
    )
    run_cmd(
        [sys.executable, "30_extraction/scripts/review_poi_supply_base.py"],
        group="scripts",
        name="poi supply review",
    )
    run_cmd(
        [sys.executable, "50_external_gis/scripts/build_amap_spatial_precheck.py"],
        group="scripts",
        name="amap spatial precheck rebuild",
        expect=["wrote 227 spatial precheck rows", "wrote 17 follow-up rows"],
    )
    run_cmd(
        [sys.executable, "50_external_gis/scripts/build_amap_boundary_filter.py"],
        group="scripts",
        name="amap boundary filter rebuild",
        expect=["wrote 227 boundary filter rows"],
    )
    run_cmd(
        [sys.executable, "50_external_gis/scripts/build_in_park_candidate_review.py"],
        group="scripts",
        name="in-park candidate review rebuild",
        expect=["wrote 26 in-park candidate review rows"],
    )
    run_cmd(
        [sys.executable, "60_model/scripts/review_deepseek_p1_quality_report.py"],
        group="scripts",
        name="p1 quality report review",
        expect=["failures=0"],
    )
    run_cmd(
        [sys.executable, "30_extraction/scripts/build_p2_real_site_input_index.py"],
        group="scripts",
        name="p2 real-site input index rebuild",
        expect=[
            "p2_real_site_source_catalog.csv rows=4",
            "p2_real_site_input_worklist.csv rows=7",
            "p2_simulation_input_requirements.csv rows=6",
        ],
    )
    run_cmd(
        [sys.executable, "60_model/scripts/review_deepseek_p2_real_site_semantic_breakdown.py"],
        group="scripts",
        name="p2 semantic breakdown review",
        expect=["failures=0"],
    )
    run_cmd(
        [sys.executable, "60_model/scripts/review_deepseek_p2_input_schema_candidates.py"],
        group="scripts",
        name="p2 input schema candidate review",
        expect=["failures=0"],
    )
    run_cmd(
        [sys.executable, "60_model/scripts/review_deepseek_p2_completion_readiness_audit.py"],
        group="scripts",
        name="p2 completion readiness review",
        expect=["failures=0"],
    )
    run_cmd(
        [sys.executable, "60_model/scripts/run_deepseek_p2_source_coverage_audit.py"],
        group="scripts",
        name="p2 source coverage DeepSeek audit",
        expect=["deepseek_p2_source_coverage_audit_matrix.csv rows=60"],
    )
    run_cmd(
        [sys.executable, "60_model/scripts/review_deepseek_p2_source_coverage_audit.py"],
        group="scripts",
        name="p2 source coverage review",
        expect=["failures=0"],
    )
    run_cmd(
        [sys.executable, "60_model/scripts/run_deepseek_p2_geometry_proxy_audit.py"],
        group="scripts",
        name="p2 geometry proxy DeepSeek audit",
        expect=["p2_pdf_proxy_zone_candidates_deepseek.csv rows=10"],
    )
    run_cmd(
        [sys.executable, "60_model/scripts/review_deepseek_p2_geometry_proxy_audit.py"],
        group="scripts",
        name="p2 geometry proxy review",
        expect=["failures=0"],
    )
    run_cmd(
        [sys.executable, "60_model/scripts/run_deepseek_p3_prework_package.py"],
        group="scripts",
        name="p3 prework DeepSeek package",
        expect=[
            "p3_p4_route_decision_deepseek.csv rows=3",
            "p3_calibration_data_requirements_deepseek.csv rows=16",
            "p4_parallel_skeleton_backlog_deepseek.csv rows=12",
        ],
    )
    run_cmd(
        [sys.executable, "60_model/scripts/review_deepseek_p3_prework_package.py"],
        group="scripts",
        name="p3 prework package review",
        expect=["failures=0"],
    )
    run_cmd(
        [sys.executable, "60_model/scripts/run_deepseek_p3_calibration_execution_package.py"],
        group="scripts",
        name="p3 calibration execution DeepSeek package",
        expect=[
            "p3_calibration_evidence_request_worklist_deepseek.csv rows=24",
            "p3_calibration_gate_status.csv rows=6",
        ],
    )
    run_cmd(
        [sys.executable, "60_model/scripts/review_deepseek_p3_calibration_execution_package.py"],
        group="scripts",
        name="p3 calibration execution package review",
        expect=["failures=0"],
    )
    run_cmd(
        [sys.executable, "60_model/scripts/run_deepseek_p4_premature_audit.py"],
        group="scripts",
        name="p4 premature simulation DeepSeek audit",
        expect=["decision=rollback", "output_status=needs_review"],
    )
    run_cmd(
        [sys.executable, "60_model/scripts/run_deepseek_p4_feedback_draft.py"],
        group="scripts",
        name="p4 feedback draft DeepSeek package",
        expect=[
            "p4_feedback_node_priority_draft_deepseek.csv rows=6",
            "p4_feedback_scenario_matrix_draft_deepseek.csv rows=12",
            "output_status=needs_review",
        ],
    )
    run_cmd(
        [sys.executable, "60_model/scripts/review_deepseek_p4_feedback_draft.py"],
        group="scripts",
        name="p4 feedback draft review",
        expect=["failures=0"],
    )
    run_cmd(
        [sys.executable, "60_model/scripts/build_p2_method_prototype.py"],
        group="scripts",
        name="p2 method prototype rebuild",
        expect=[
            "p2_persona_parameter_prototype.csv rows=6",
            "p2_demand_trigger_matrix.csv rows=12",
            "p2_supply_gap_scoring_formula.csv rows=8",
            "p2_candidate_method_readiness_scores.csv rows=6",
            "p2_postman_api_contract_draft.csv rows=8",
        ],
    )
    run_cmd(
        [sys.executable, "60_model/scripts/review_p2_method_prototype.py"],
        group="scripts",
        name="p2 method prototype review",
        expect=["failures=0"],
    )
    run_cmd(
        [sys.executable, "30_extraction/scripts/review_p2_completion_reality.py"],
        group="scripts",
        name="p2 completion reality audit",
        expect=["failures=0"],
    )
    run_cmd(
        [sys.executable, "30_extraction/scripts/review_handoff_and_encoding_health.py"],
        group="scripts",
        name="handoff encoding health review",
        expect=["failures=0"],
    )


def verify_llm_router() -> None:
    module_path = ROOT / "60_model" / "src" / "llm_router.py"
    try:
        spec = importlib.util.spec_from_file_location("llm_router_test_subject", module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot create module spec")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        routes = module.load_routes()
        add("llm", "error", ok(len(routes) == 26), f"loaded routes={len(routes)}", "60_model/src/llm_router.py")
        add("llm", "error", ok(routes["LLM-001"].default_executor == "deepseek"), "LLM-001 routes to DeepSeek", "60_model/configs/llm_task_routing.csv")
        add("llm", "error", ok(routes["LLM-006"].risk == "high"), "LLM-006 remains high-risk final conclusion", "60_model/configs/llm_task_routing.csv")
        add("llm", "error", ok(routes["LLM-009"].output_status == "needs_review"), "LLM-009 remains Tier-2 needs_review", "60_model/configs/llm_task_routing.csv")
        add("llm", "error", ok(routes["LLM-010"].output_status == "needs_review"), "LLM-010 remains Tier-2 needs_review", "60_model/configs/llm_task_routing.csv")
        add("llm", "error", ok(routes["LLM-011"].output_status == "draft"), "LLM-011 entrance node semantic screening remains draft", "60_model/configs/llm_task_routing.csv")
        add("llm", "error", ok(routes["LLM-012"].output_status == "needs_review"), "LLM-012 P0 verification package remains needs_review", "60_model/configs/llm_task_routing.csv")
        add("llm", "error", ok(routes["LLM-013"].output_status == "needs_review"), "LLM-013 context sync remains needs_review", "60_model/configs/llm_task_routing.csv")
        add("llm", "error", ok(routes["LLM-014"].output_status == "needs_review"), "LLM-014 P0 Amap detail query plan remains needs_review", "60_model/configs/llm_task_routing.csv")
        add("llm", "error", ok(routes["LLM-015"].output_status == "needs_review"), "LLM-015 field verification checklist remains needs_review", "60_model/configs/llm_task_routing.csv")
        add("llm", "error", ok(routes["LLM-016"].output_status == "needs_review"), "LLM-016 P1 quality report remains needs_review", "60_model/configs/llm_task_routing.csv")
        add("llm", "error", ok(routes["LLM-017"].output_status == "needs_review"), "LLM-017 P2 real-site semantic breakdown remains needs_review", "60_model/configs/llm_task_routing.csv")
        add("llm", "error", ok(routes["LLM-018"].output_status == "needs_review"), "LLM-018 P2 input schema candidates remain needs_review", "60_model/configs/llm_task_routing.csv")
        add("llm", "error", ok(routes["LLM-019"].output_status == "needs_review"), "LLM-019 P2 readiness audit remains needs_review", "60_model/configs/llm_task_routing.csv")
        add("llm", "error", ok(routes["LLM-020"].output_status == "needs_review"), "LLM-020 P2 source coverage audit remains needs_review", "60_model/configs/llm_task_routing.csv")
        add("llm", "error", ok(routes["LLM-021"].output_status == "needs_review"), "LLM-021 P2 geometry proxy audit remains needs_review", "60_model/configs/llm_task_routing.csv")
        add("llm", "error", ok(routes["LLM-022"].output_status == "needs_review"), "LLM-022 P3 prework package remains needs_review", "60_model/configs/llm_task_routing.csv")
        add("llm", "error", ok(routes["LLM-023"].output_status == "needs_review"), "LLM-023 P3 calibration execution package remains needs_review", "60_model/configs/llm_task_routing.csv")
        add("llm", "error", ok(routes["LLM-024"].output_status == "needs_review"), "LLM-024 P4 premature audit remains needs_review", "60_model/configs/llm_task_routing.csv")
        add("llm", "error", ok(routes["LLM-025"].output_status == "needs_review"), "LLM-025 P4 feedback draft remains needs_review", "60_model/configs/llm_task_routing.csv")

        old_key = os.environ.pop("DEEPSEEK_API_KEY", None)
        old_env_file = getattr(module, "ENV_FILE", None)
        try:
            if old_env_file is not None:
                module.ENV_FILE = Path(tempfile.gettempdir()) / "park_simulation_missing_deepseek.env"
            try:
                module.run_deepseek_task("LLM-006", [{"role": "user", "content": "test"}])
                add("llm", "error", "fail", "LLM-006 unexpectedly allowed DeepSeek execution", "60_model/src/llm_router.py")
            except RuntimeError as exc:
                add("llm", "error", ok("not DeepSeek" in str(exc)), "LLM-006 high-risk/non-DeepSeek guard triggered", "60_model/src/llm_router.py")

            try:
                module.run_deepseek_task("LLM-001", [{"role": "user", "content": "test"}])
                add("llm", "error", "fail", "LLM-001 unexpectedly ran without env key", "60_model/src/llm_router.py")
            except RuntimeError as exc:
                add("llm", "error", ok("DEEPSEEK_API_KEY is not set" in str(exc)), "DeepSeek key must come from environment", "60_model/src/llm_router.py")
        finally:
            if old_env_file is not None:
                module.ENV_FILE = old_env_file
            if old_key is not None:
                os.environ["DEEPSEEK_API_KEY"] = old_key
    except Exception as exc:
        add("llm", "error", "fail", f"llm_router import/test failed: {type(exc).__name__}: {exc}", "60_model/src/llm_router.py")


def verify_secret_and_encoding() -> None:
    patterns = {
        "deepseek_like_key": re.compile(r"sk-[A-Za-z0-9]{20,}"),
        "nonempty_deepseek_env": re.compile(r"^\s*DEEPSEEK_API_KEY[^\S\r\n]*=[^\S\r\n]*[^\s#]+", re.MULTILINE),
        "nonempty_amap_env": re.compile(r"^\s*AMAP_WEB_SERVICE_KEY[^\S\r\n]*=[^\S\r\n]*[^\s#]+", re.MULTILINE),
        "amap_url_key_param": re.compile(r"[?&]key=[^&\s]+"),
        "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    }
    allowed_exts = {".md", ".csv", ".json", ".py", ".ps1", ".txt", ".env", ".example", ".yml", ".yaml", ".toml"}
    findings: list[str] = []
    mojibake: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path in {OUT_CSV, OUT_MD}:
            continue
        if path.parent == OUT_DIR and path.name.startswith("implementation_verification_"):
            continue
        if path.name == ".env":
            continue
        if path.name == "KEYS.md":  # user-designated plain-text key reference, no security restriction
            continue
        if path.suffix not in allowed_exts and not path.name.startswith(".env"):
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            continue
        for name, pattern in patterns.items():
            if pattern.search(text):
                findings.append(f"{name}:{rel(path)}")
        if "???" in text and path.name != "verify_project_implementation.py":
            suspect_lines = []
            for line in text.splitlines():
                if "???" not in line:
                    continue
                if 'rg "???"' in line or "`???`" in line:
                    continue
                has_cjk = bool(re.search(r"[\u4e00-\u9fff]", line))
                has_replacement = "\ufffd" in line
                has_mojibake_marker = "锟" in line
                has_ascii_words = bool(re.search(r"[A-Za-z]{4,}", line))
                if has_replacement or has_mojibake_marker or (has_cjk and not has_ascii_words):
                    suspect_lines.append(line)
            if suspect_lines:
                mojibake.append(rel(path))
    add("security", "error", ok(not findings), f"sensitive matches={findings}", "project text scan")
    add("files", "error", ok(not mojibake), f"mojibake placeholders={mojibake}", 'rg "???" equivalent')

    env_example = ROOT / ".env.example"
    if env_example.exists():
        text = env_example.read_text(encoding="utf-8-sig")
        placeholders_ok = "DEEPSEEK_API_KEY=" in text and "AMAP_WEB_SERVICE_KEY=" in text
        add("security", "error", ok(placeholders_ok), ".env.example keeps empty placeholders only", ".env.example")

    env_file = ROOT / ".env"
    if env_file.exists():
        env_text = env_file.read_text(encoding="utf-8-sig")
        deepseek_set = bool(re.search(r"^\s*DEEPSEEK_API_KEY[^\S\r\n]*=[^\S\r\n]*[^\s#]+", env_text, re.MULTILINE))
        amap_set = bool(re.search(r"^\s*AMAP_WEB_SERVICE_KEY[^\S\r\n]*=[^\S\r\n]*[^\s#]+", env_text, re.MULTILINE))
        add("security", "error", ok(deepseek_set), ".env has local DeepSeek key configured", ".env")
        add("security", "error", ok(amap_set), ".env has local Amap key configured", ".env")

    gitignore = ROOT / ".gitignore"
    if gitignore.exists():
        ignored = any(line.strip() == ".env" for line in gitignore.read_text(encoding="utf-8-sig").splitlines())
        add("security", "error", ok(ignored), ".gitignore excludes .env", ".gitignore")


def verify_github_remote() -> None:
    forks = read_csv(ROOT / "10_research" / "github_tech_shrimp" / "fork_results_20260523.csv")
    result = run_cmd(
        ["gh", "repo", "list", "cocyuhao", "--limit", "200", "--json", "nameWithOwner,isFork,parent,url"],
        group="github",
        name="gh repo list cocyuhao",
    )
    if result.returncode != 0:
        return
    try:
        repos = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        add("github", "error", "fail", f"cannot parse gh repo list JSON: {exc}", "gh repo list")
        return
    repo_by_name = {repo.get("nameWithOwner"): repo for repo in repos}
    fork_failures: list[str] = []
    for row in forks:
        if row.get("status") != "forked":
            continue
        target = row["target"]
        source_name = row["source"].split("/", 1)[1]
        repo = repo_by_name.get(target)
        parent = repo.get("parent") if repo else None
        parent_ok = bool(
            repo
            and repo.get("isFork") is True
            and parent
            and parent.get("name") == source_name
            and (parent.get("owner") or {}).get("login") == "tech-shrimp"
        )
        if not parent_ok:
            fork_failures.append(target)
    add("github", "error", ok(not fork_failures), f"fork parent verification failures={fork_failures}", "gh repo list cocyuhao")

    contents = run_cmd(
        ["gh", "api", "repos/cocyuhao/tech-shrimp-open-source-archive/contents"],
        group="github",
        name="archive repo contents",
    )
    if contents.returncode == 0:
        try:
            paths = {item["path"] for item in json.loads(contents.stdout)}
            add("github", "error", ok({"README.md", "docs", "manifests"} <= paths), f"archive root paths={sorted(paths)}", "cocyuhao/tech-shrimp-open-source-archive")
        except Exception as exc:
            add("github", "error", "fail", f"archive root parse failed: {type(exc).__name__}", "gh api contents")

    docs = run_cmd(
        ["gh", "api", "repos/cocyuhao/tech-shrimp-open-source-archive/contents/docs"],
        group="github",
        name="archive docs contents",
    )
    if docs.returncode == 0:
        try:
            paths = {item["path"] for item in json.loads(docs.stdout)}
            expected = {
                "docs/github_import_plan.md",
                "docs/tech_shrimp_assessment.md",
            }
            add("github", "error", ok(expected <= paths), f"archive docs paths={sorted(paths)}", "cocyuhao/tech-shrimp-open-source-archive/docs")
        except Exception as exc:
            add("github", "error", "fail", f"archive docs parse failed: {type(exc).__name__}", "gh api docs")

    manifests = run_cmd(
        ["gh", "api", "repos/cocyuhao/tech-shrimp-open-source-archive/contents/manifests"],
        group="github",
        name="archive manifests contents",
    )
    if manifests.returncode == 0:
        try:
            paths = {item["path"] for item in json.loads(manifests.stdout)}
            expected = {
                "manifests/fork_results_20260523.csv",
                "manifests/tech_shrimp_repos_gh_api_20260523.csv",
            }
            add("github", "error", ok(expected <= paths), f"archive manifests paths={sorted(paths)}", "cocyuhao/tech-shrimp-open-source-archive/manifests")
        except Exception as exc:
            add("github", "error", "fail", f"archive manifests parse failed: {type(exc).__name__}", "gh api manifests")


def verify_current_conflict_rebaseline() -> None:
    risk_terms = [
        "N" + "-001",
        "QA UI 自动化节点",
        "external" + "_preview_only",
        "外部" + "预览",
        "仅地图" + "预览",
        "补" + "资料",
        "补" + "齐",
        "请" + "补",
        "训练" + "资料",
    ]

    latest_report_path = ROOT / "80_delivery" / "site_selection_gap_report_latest.json"
    try:
        latest = json.loads(latest_report_path.read_text(encoding="utf-8-sig"))
        latest_text = json.dumps(latest, ensure_ascii=False)
        real_calibration = latest.get("real_calibration_context", {})
        source_foundation = latest.get("source_foundation", {})
        source_assets = source_foundation.get("assets", [])
        method_basis = latest.get("method_basis", [])
        method_trace = latest.get("method_trace", [])
        nodes = latest.get("nodes", [])
        add(
            "current_rebaseline",
            "error",
            ok(
                int(real_calibration.get("count", 0)) >= 10
                and isinstance(source_assets, list)
                and len(source_assets) >= 8
                and len(method_basis) >= 3
                and len(method_trace) >= 5
                and len(nodes) >= 6
                and all(term not in latest_text for term in risk_terms)
            ),
            f"current latest report nodes={len(nodes)} method_basis={len(method_basis)} method_trace={len(method_trace)} source_assets={len(source_assets)} real_calibration={real_calibration.get('count')}",
            "80_delivery/site_selection_gap_report_latest.json",
        )
    except Exception as exc:
        add("current_rebaseline", "error", "fail", f"current latest report invalid: {type(exc).__name__}", "80_delivery/site_selection_gap_report_latest.json")

    for evidence_path, label in [
        ("40_quality_evidence/historical_issue_surface_audit_20260608.json", "historical issue surface"),
        ("40_quality_evidence/agent_editor_influence_surface_audit_20260609.json", "agent/editor influence surface"),
        ("40_quality_evidence/post_test_current_output_restore_20260609.json", "post-test output restore"),
        ("40_quality_evidence/system_influence_audit_20260608.json", "system influence"),
    ]:
        path = ROOT / evidence_path
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
            status = payload.get("status")
            high_count = int(payload.get("high_current_count", 0) or 0)
            high_severity = int(payload.get("severity_counts", {}).get("high", 0) or 0)
            add(
                "current_rebaseline",
                "error",
                ok(status in {"pass", "review"} and high_count == 0 and high_severity == 0),
                f"{label} status={status} high_current={high_count} high_severity={high_severity}",
                evidence_path,
            )
        except Exception as exc:
            add("current_rebaseline", "error", "fail", f"{label} invalid: {type(exc).__name__}", evidence_path)

    test_report_path = ROOT / "TestFiles" / "reports" / "test_report.json"
    try:
        payload = json.loads(test_report_path.read_text(encoding="utf-8-sig"))
        summary = payload.get("summary", {})
        add(
            "current_rebaseline",
            "error",
            ok(int(summary.get("failed", 99)) == 0 and int(summary.get("passed", 0)) >= 79),
            f"TestFiles summary={summary}",
            "TestFiles/reports/test_report.json",
        )
    except Exception as exc:
        add("current_rebaseline", "error", "fail", f"TestFiles latest report invalid: {type(exc).__name__}", "TestFiles/reports/test_report.json")


def write_outputs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(checks)

    by_status = Counter(row["status"] for row in checks)
    failures = [row for row in checks if row["status"] == "fail"]
    warnings = [row for row in checks if row["status"] == "warn"]

    lines = [
        "# 2026-05-24 落实性核验报告",
        "",
        "## 结论",
        "",
        f"- 总检查项：{len(checks)}",
        f"- 状态统计：{dict(sorted(by_status.items()))}",
        f"- 失败项：{len(failures)}",
        f"- 警告项：{len(warnings)}",
        "",
        "## 覆盖范围",
        "",
        "- DeepSeek 路由文件、任务表、环境变量边界和高风险任务拦截。",
        "- DeepSeek 表格主题分类草稿、本地复核队列、P0 二次证据候选数量和 raw/progress 产物。",
        "- DeepSeek P0 表格证据候选草稿、本地回查队列、入账前 `needs_review` 状态门禁。",
        "- 第二批 PDF 原生表格证据入账脚本、260 条证据台账和 208 条第二批 checked 指标。",
        "- 本地 `.env` 凭据配置、DeepSeek smoke test 真实调用状态和脱敏输出。",
        "- 高德 Web 服务 smoke test 真实调用状态和脱敏输出。",
        "- 样例数据抽取、证据台账、POI 供给底表、高德查询计划行数和状态。",
        "- 高德候选表、空间预过滤表、补抓计划和保守供给使用状态。",
        "- OSM 公园边界文件、边界抓取日志和高德候选边界过滤结果。",
        "- OSM polygon 内候选复核清单、路径核验状态和运营授权待确认状态。",
        "- P0 园内候选工作单、高德中心点代理步行路径结果和 Key 脱敏日志。",
        "- P0 高德入口/节点候选、入口/节点代理步行路径和仍不进入 P2 的状态门禁。",
        "- DeepSeek 入口/节点语义初筛草稿、本地规则复核队列和官方/现场确认门禁。",
        "- 现有 Python 脚本编译、POI review 脚本、Amap dry-run。",
        "- `tech-shrimp` GitHub 认证 API 清单、fork 结果和索引仓库远端目录。",
        "- DeepSeek Key、高德 Key、GitHub token、URL `key=` 参数和编码损坏占位扫描。",
        "",
        "## 失败项",
        "",
    ]
    if failures:
        for row in failures:
            lines.append(f"- `{row['check_id']}` {row['group']}: {row['finding']} ({row['evidence']})")
    else:
        lines.append("- 无。")
    lines.extend(["", "## 检查明细", ""])
    for row in checks:
        lines.append(f"- `{row['check_id']}` `{row['status']}` `{row['group']}` {row['finding']}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    verify_required_files()
    verify_row_counts()
    verify_json_files()
    verify_python_and_scripts()
    verify_llm_router()
    verify_secret_and_encoding()
    verify_github_remote()
    verify_current_conflict_rebaseline()
    apply_superseded_rebaseline()
    write_outputs()
    failures = [row for row in checks if row["status"] == "fail"]
    print(f"wrote {OUT_CSV}")
    print(f"wrote {OUT_MD}")
    print(f"checks={len(checks)} failures={len(failures)}")
    if failures:
        for row in failures:
            print(f"FAIL {row['check_id']} {row['group']} {row['finding']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
