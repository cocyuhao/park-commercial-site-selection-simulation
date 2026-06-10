from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "70_outputs" / "processed_tables"

STATIC_PROFILE = PROCESSED / "p2_persona_state_profiles_20260604.csv"
STATIC_PROGRAM = PROCESSED / "p2_behavior_program_templates_20260604.csv"
STATIC_VALIDATION = PROCESSED / "p2_simulation_validation_targets_20260604.csv"

DEEPSEEK_PROFILE = PROCESSED / "p2_persona_state_profiles_deepseek.csv"
DEEPSEEK_PROGRAM = PROCESSED / "p2_behavior_program_templates_deepseek.csv"
DEEPSEEK_VALIDATION = PROCESSED / "p2_simulation_validation_targets_deepseek.csv"

BLOCKING_DOMAINS = {
    "geometry",
    "visitor_flow",
    "conversion_rate",
    "revenue_cost",
    "operation_authorization",
}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def preferred_rows(deepseek_path: Path, static_path: Path) -> tuple[list[dict[str, str]], str]:
    deepseek_rows = read_csv_rows(deepseek_path)
    if deepseek_rows and all(row.get("output_status") == "needs_review" for row in deepseek_rows):
        return deepseek_rows, deepseek_path.name
    return read_csv_rows(static_path), static_path.name


def visible_status(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return "资料待复核"
    if "blocked" in text or "not_provided" in text:
        return "阻塞正式仿真"
    if "pending" in text:
        return "等待复核"
    if "needs" in text:
        return "待复核"
    if text in {"yes", "true"}:
        return "是"
    if text in {"no", "false"}:
        return "否"
    return text


def blocked_domains_from(gaps: list[dict[str, Any]], gates: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for gap in gaps:
        domain = str(gap.get("input_domain") or gap.get("calibration_domain") or "")
        status = str(gap.get("current_status") or gap.get("current_gate_status") or "")
        if domain in BLOCKING_DOMAINS and (
            "not_provided" in status
            or "blocked" in status
            or "pending" in status
            or "missing" in status
            or gap.get("blocking_level") in {"high", "blocking_for_simulation_calibration"}
        ):
            rows.append(
                {
                    "domain": domain,
                    "status": visible_status(status),
                    "reason": str(gap.get("why_it_matters") or gap.get("blocking_reason") or gap.get("gap_name") or ""),
                    "next_action": str(gap.get("next_action") or "补充真实资料后再校准。"),
                }
            )
    for gate in gates:
        domain = str(gate.get("calibration_domain") or "")
        status = str(gate.get("current_gate_status") or "")
        if domain in BLOCKING_DOMAINS and ("pending" in status or "blocked" in status):
            rows.append(
                {
                    "domain": domain,
                    "status": visible_status(status),
                    "reason": str(gate.get("blocking_reason") or ""),
                    "next_action": "关闭 P3 校准门禁后再进入正式仿真结论。",
                }
            )
    dedup: dict[str, dict[str, str]] = {}
    for row in rows:
        dedup.setdefault(row["domain"], row)
    return list(dedup.values())


def readiness_label(blocked: list[dict[str, str]], programs: list[dict[str, str]]) -> str:
    if not programs:
        return "行为程序尚未建立"
    if blocked:
        return "方法框架已建立，真实仿真仍被资料阻塞"
    return "可以进入受控仿真预演，仍需人工复核"


def build_persona_simulation_payload(
    gaps: list[dict[str, Any]] | None = None,
    gates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    gaps = gaps or []
    gates = gates or []
    profiles, profile_source = preferred_rows(DEEPSEEK_PROFILE, STATIC_PROFILE)
    programs, program_source = preferred_rows(DEEPSEEK_PROGRAM, STATIC_PROGRAM)
    validation_targets, validation_source = preferred_rows(DEEPSEEK_VALIDATION, STATIC_VALIDATION)
    blocked = blocked_domains_from(gaps, gates)
    can_run_local_preview = bool(profiles and programs)
    can_claim_full_simulation = can_run_local_preview and not blocked
    return {
        "summary": {
            "profile_count": len(profiles),
            "program_count": len(programs),
            "validation_target_count": len(validation_targets),
            "readiness_label": readiness_label(blocked, programs),
            "can_run_local_preview": can_run_local_preview,
            "can_claim_full_simulation": can_claim_full_simulation,
            "source_files": [profile_source, program_source, validation_source],
        },
        "method_layers": [
            {
                "name": "资料与状态层",
                "role": "读取真实资料、画像原型、触发矩阵和门禁状态，明确哪些结论还不能做。",
            },
            {
                "name": "DeepSeek 行为程序层",
                "role": "生成或校准结构化行为程序草稿，不逐游客调用，不输出最终推荐。",
            },
            {
                "name": "本地仿真层",
                "role": "用 Python 执行抽样、路径、排队、放弃、外溢和敏感性分析，确保可复跑。",
            },
            {
                "name": "业务解释层",
                "role": "把本地结果解释成人能读懂的依据、缺口和下一步动作，仍保持待复核。",
            },
        ],
        "deepseek_policy": {
            "recommended_use": [
                "按人群、场景、节点和时间段生成可缓存行为程序",
                "把仿真结果解释成业务语言",
                "整理资料缺口和待复核假设",
            ],
            "forbidden_use": [
                "逐个游客实时调用 DeepSeek",
                "直接输出最终排序、收益预测或 ROI",
                "把 PPT 或 AI 草稿写成 checked 证据",
                "在 P3 门禁未闭合时声称完成真实仿真",
            ],
            "output_status": "needs_review",
        },
        "blocked_domains": blocked,
        "persona_state_profiles": profiles,
        "behavior_programs": programs,
        "validation_targets": validation_targets,
        "output_status": "needs_review",
        "not_final": True,
    }
