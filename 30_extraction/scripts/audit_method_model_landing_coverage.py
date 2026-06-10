from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "40_quality_evidence" / "method_model_landing_coverage_20260605.json"
OUT_MD = ROOT / "40_quality_evidence" / "method_model_landing_coverage_20260605.md"


MODEL_COVERAGE = [
    {
        "id": "SSR_DLR_FLR",
        "name": "DLR / FLR / SSR synthetic user rating methods",
        "source": "老板长图与 591775 PDF；boss_model_inventory",
        "principle": "LLM 不直接打裸分；先产生动机、担忧、放弃理由，再映射为推进优先级。",
        "signals": [
            ("10_research/boss_method_materials_20260604/boss_model_inventory_20260604.md", ["DLR", "FLR", "SSR"]),
            ("00_control/decisions.md", ["裸分数", "推进优先级"]),
            ("90_p6_expert_dashboard/static/app.js", ["discussion_score_draft", "推进优先级"]),
        ],
        "required_next": "继续清理用户可见分数字段，把分数默认折叠，主视觉只保留建议、依据和复核动作。",
    },
    {
        "id": "ROTE_BEHAVIOR_PROGRAM",
        "name": "ROTE / behavior program / finite state behavior",
        "source": "2510.01272v1.pdf；ROTE / Modeling Others' Minds as Code",
        "principle": "游客行为应变成可编辑、可复核的行为程序，不是每次临场让 LLM 编故事。",
        "signals": [
            ("60_model/schemas/behavior_program.schema.json", ["trigger_context", "candidate_actions", "failure_condition"]),
            ("70_outputs/processed_tables/p2_behavior_program_templates_20260604.csv", ["program_id", "trigger_condition", "abandon_or_spillover_condition"]),
            ("10_research/boss_method_materials_20260604/boss_model_inventory_20260604.md", ["ROTE", "Finite State Machines"]),
            ("90_p6_expert_dashboard/static/index.html", ["behavior_program", "新增行为程序"]),
            ("40_quality_evidence/simulation_object_pool_persona_behavior_validation_20260605.json", ["has_behavior_program_objects", "behavior_program=12"]),
        ],
        "required_next": "behavior_program 已进入对象池；下一步是让仿真任务入口选择、组合和预检行为程序，而不是只展示对象。",
    },
    {
        "id": "HUMANLM_LATENT_STATE",
        "name": "HumanLM latent state alignment",
        "source": "2603.03303.pdf；HumanLM",
        "principle": "人物仿真准确性先看潜在状态是否充分，而不是看 AI 回答像不像人。",
        "signals": [
            ("60_model/schemas/persona_state.schema.json", ["purpose", "time_pressure", "queue_tolerance", "companion_context"]),
            ("70_outputs/processed_tables/p2_persona_state_profiles_20260604.csv", ["persona_id", "visit_purpose", "calibration_status"]),
            ("10_research/boss_method_materials_20260604/boss_model_inventory_20260604.md", ["HumanLM", "Latent State Modeling"]),
            ("10_research/boss_method_materials_20260604/simulation_accuracy_plan_20260604.md", ["状态准确", "行为准确"]),
            ("90_p6_expert_dashboard/static/index.html", ["persona_state", "新增人群状态"]),
            ("40_quality_evidence/simulation_object_pool_persona_behavior_validation_20260605.json", ["has_persona_state_objects", "persona_state=6"]),
        ],
        "required_next": "persona_state 已进入对象池；下一步是让 AI 工作台和仿真预检稳定显示 state -> behavior -> demand -> advice 链。",
    },
    {
        "id": "RL_LLM_SOCIAL_SIM",
        "name": "RL + LLM high-definition social simulation",
        "source": "人工智能模拟实验论文.docx；已转换 - main-1.docx",
        "principle": "宏观统计奖励 + 微观 LLM 草评；不能用页面 smoke test 代替仿真准确性验证。",
        "signals": [
            ("10_research/boss_method_materials_20260604/boss_model_inventory_20260604.md", ["PPO", "Macro Statistical Reward", "Micro LLM Reward"]),
            ("10_research/boss_method_materials_20260604/unified_simulation_method_matrix_20260604.md", ["状态-行为-证据链一致性", "宏观统计一致性双门禁"]),
            ("60_model/schemas/simulation_validation_target.schema.json", ["metric_family", "acceptance_rule"]),
        ],
        "required_next": "建立微观状态-行为一致性验证脚本和宏观校准目标清单，不把干跑结果当完整仿真。",
    },
    {
        "id": "SPATIAL_ACTIVITY_CHAIN",
        "name": "Social Force / RVO / MATSim spatial and activity-chain simulation",
        "source": "外部论文；老板统一矩阵",
        "principle": "空间仿真不是地图点位展示；需要路径、容量、活动链、拥挤和可达约束。",
        "signals": [
            ("10_research/boss_method_materials_20260604/unified_simulation_method_matrix_20260604.md", ["Social Force", "RVO", "MATSim"]),
            ("60_model/simulation/engine.py", ["boundary_filter_status", "blocked_gate_count"]),
            ("90_p6_expert_dashboard/app.py", ["MAP_CONTEXT_FILE", "MAP_BOUNDARY_FILE"]),
        ],
        "required_next": "将现有地图/POI 只作为空间线索，后续在 P3 几何闭合后再接路网/容量/活动链。",
    },
    {
        "id": "CHOICE_GAP_MODEL",
        "name": "Huff / Logit / Gravity / POI-TGI demand-supply gap",
        "source": "外部零售选址模型；同事 POI_TGI_Calculator",
        "principle": "供需缺口是辅助层；选择概率由人群状态、行为程序、空间成本、排队、价格和供给共同决定。",
        "signals": [
            ("60_model/schemas/choice_probability.schema.json", ["factor_inputs", "distance_decay", "queue_penalty"]),
            ("10_research/poi_tgi_calculator_selective_absorption_20260604.md", ["POI_TGI_Calculator", "选择性吸收"]),
            ("10_research/method_tool_plugin_audit_20260604.md", ["POI_TGI_Calculator", "降级为辅助"]),
        ],
        "required_next": "把 POI/TGI 指标接入 choice_probability.factor_inputs，作为可开关辅助因子。",
    },
    {
        "id": "MACRO_VALIDATION_METRICS",
        "name": "SARIMA / SSIM / KL-Divergence / DTW validation metrics",
        "source": "老板社区仿真资料与统一矩阵",
        "principle": "真实准确性需要对齐时段客流、热力形态、分布和曲线，而不是只靠截图或 AI 文字。",
        "signals": [
            ("10_research/boss_method_materials_20260604/boss_model_inventory_20260604.md", ["SARIMA", "SSIM", "KL-Divergence", "DTW"]),
            ("10_research/boss_method_materials_20260604/simulation_accuracy_plan_20260604.md", ["宏观验证", "DTW"]),
            ("60_model/schemas/simulation_validation_target.schema.json", ["metric_family", "reference_data", "required_fields"]),
        ],
        "required_next": "把验证目标对象在 UI 中作为运行前置条件展示，并阻止未闭合数据时宣称仿真可信。",
    },
    {
        "id": "DEEPSEEK_CONSTRAINED_WORKER",
        "name": "DeepSeek constrained semantic worker",
        "source": "DeepSeek API docs；本地契约；老板资料",
        "principle": "DeepSeek 便宜但不是总设计师；禁止逐游客实时调用，采用批处理、缓存和本地验证。",
        "signals": [
            ("10_research/deepseek_api_concurrency_capacity_20260605.md", ["账号并发", "capacity expansion", "不应每个虚拟游客都调用一次 DeepSeek"]),
            ("10_research/boss_method_materials_20260604/deepseek_constrained_simulation_design_20260604.md", ["行为程序编译器", "逐游客"]),
            ("60_model/schemas/deepseek_task_contract.schema.json", ["output_status", "review_required"]),
            ("60_model/src/llm_router.py", ["run_deepseek_task", "risk == \"high\""]),
        ],
        "required_next": "补 DeepSeek 调用队列、缓存、429 退避和 OpenTelemetry span；不得把多 key 当并发方案。",
    },
    {
        "id": "AGENTIC_UI_HUMAN_OVERSIGHT",
        "name": "Agentic UI / human oversight / GUI agent risk",
        "source": "2026 AI/HCI 检索、Flowus、豆包/Codex 参考",
        "principle": "界面要让用户采用、放弃、锁定、复核；不能把 AI 草稿当不可修改的系统判断。",
        "signals": [
            ("10_research/advanced_ai_learning_absorption_register_20260604.md", ["agent 可读 UI", "检查点调度", "旧产物信任地图"]),
            ("40_quality_evidence/advanced_agentic_workflow_validation_20260604.json", ["risk_taxonomy", "agent_readability"]),
            ("90_p6_expert_dashboard/static/app.js", ["user_locked", "adoption_status"]),
        ],
        "required_next": "把人群状态、行为程序、选择概率、验证目标全部做成同样的可控对象链路。",
    },
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def evaluate_signal(path_rel: str, patterns: list[str]) -> dict[str, Any]:
    path = ROOT / path_rel
    if not path.exists():
        return {"path": path_rel, "exists": False, "matched": [], "missing": patterns, "bytes": 0}
    text = read_text(path)
    matched = [pattern for pattern in patterns if pattern in text]
    missing = [pattern for pattern in patterns if pattern not in text]
    return {"path": path_rel, "exists": True, "matched": matched, "missing": missing, "bytes": path.stat().st_size}


def evaluate_entry(entry: dict[str, Any]) -> dict[str, Any]:
    signals = [evaluate_signal(path, patterns) for path, patterns in entry["signals"]]
    exists_count = sum(1 for signal in signals if signal["exists"])
    full_match_count = sum(1 for signal in signals if signal["exists"] and not signal["missing"])
    partial_match_count = sum(1 for signal in signals if signal["exists"] and signal["matched"] and signal["missing"])
    missing_files = [signal["path"] for signal in signals if not signal["exists"]]
    missing_terms = {
        signal["path"]: signal["missing"]
        for signal in signals
        if signal["exists"] and signal["missing"]
    }
    if full_match_count == len(signals):
        status = "covered"
    elif exists_count and (full_match_count or partial_match_count):
        status = "partial"
    else:
        status = "missing"
    return {
        **entry,
        "status": status,
        "signals": signals,
        "coverage": {
            "signal_count": len(signals),
            "existing_file_count": exists_count,
            "full_match_count": full_match_count,
            "partial_match_count": partial_match_count,
            "missing_files": missing_files,
            "missing_terms": missing_terms,
        },
    }


def build_payload() -> dict[str, Any]:
    rows = [evaluate_entry(entry) for entry in MODEL_COVERAGE]
    counts = {status: sum(1 for row in rows if row["status"] == status) for status in ["covered", "partial", "missing"]}
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "purpose": "Audit whether boss methods and external papers have real landing points in schemas, UI, contracts, scripts, and gates.",
        "status_counts": counts,
        "items": rows,
        "completion_boundary": "Partial coverage is not completion. A model is useful only after it has explicit schema/API/UI/validation/gate landing points and user-facing wording stays non-final.",
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# 老板模型与外部论文落点覆盖审计（2026-06-05）",
        "",
        f"- 生成时间：{payload['generated_at']}",
        f"- covered：{payload['status_counts']['covered']}",
        f"- partial：{payload['status_counts']['partial']}",
        f"- missing：{payload['status_counts']['missing']}",
        "",
        "## 结论",
        "",
        "- 昨天的资料不是白读，但 partial 仍不能当 completion：已有文档、schema、对象池或草稿 CSV，不等于已经完成真实人物仿真。",
        "- 老板模型和外部论文的正确落地标准是：schema、adapter、UI 可编辑对象、DeepSeek 契约、本地验证脚本和门禁至少命中一条真实链路。",
        "- 2026-06-05 纠偏：旧报告曾写 persona_state / behavior_program 尚未进入前端对象池；该结论已过时。当前对象池验证已确认 persona_state=6、behavior_program=12，并保留新增、编辑、采用、放弃、删除动作。",
        "- 当前最明显缺口已变成：仿真任务入口还不能选择并组合人群状态/行为程序；DeepSeek 队列/缓存/429 退避尚未完整产品化；宏观验证指标还只是验证目标，没有真实计算。",
        "",
        "## 覆盖明细",
        "",
    ]
    for item in payload["items"]:
        lines.extend(
            [
                f"### {item['id']} - {item['status']}",
                "",
                f"- 名称：{item['name']}",
                f"- 来源：{item['source']}",
                f"- 原理：{item['principle']}",
                f"- 下一步：{item['required_next']}",
                "- 落点信号：",
            ]
        )
        for signal in item["signals"]:
            marker = "ok" if signal["exists"] and not signal["missing"] else "partial" if signal["exists"] and signal["matched"] else "missing"
            lines.append(
                f"  - `{signal['path']}`：{marker}；matched={signal['matched']}；missing={signal['missing']}"
            )
        lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    payload = build_payload()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(payload)
    print(f"wrote {rel(OUT_JSON)}")
    print(f"wrote {rel(OUT_MD)}")
    print(f"covered={payload['status_counts']['covered']} partial={payload['status_counts']['partial']} missing={payload['status_counts']['missing']}")


if __name__ == "__main__":
    main()
