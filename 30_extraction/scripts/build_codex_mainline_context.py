from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "40_quality_evidence" / "codex_mainline_context_20260604.json"
OUT_MD = ROOT / "40_quality_evidence" / "codex_mainline_context_20260604.md"

AUTHORITATIVE_FILES = [
    "AGENTS.md",
    "00_control/codex_mainline_guardrails.md",
    "00_control/decisions.md",
    "progress.md",
    "findings.md",
    "handoff_next_chat.md",
    "next_chat_prompt.md",
    "10_research/boss_method_materials_20260604/full_system_rebaseline_20260604.md",
    "10_research/boss_method_materials_20260604/method_absorption_landing_register_20260604.md",
    "10_research/boss_method_materials_20260604/modern_practical_method_rescreen_20260604.md",
    "10_research/global_ai_simulation_design_rebaseline_20260604.md",
    "10_research/advanced_ai_learning_absorption_register_20260604.md",
    "10_research/method_tool_plugin_audit_20260604.md",
    "10_research/deepseek_api_concurrency_capacity_20260605.md",
    "40_quality_evidence/flowus_ai_design_probe_20260604/flowus_probe_report.json",
    "40_quality_evidence/project_context_legacy_risk_audit_20260605.md",
    "40_quality_evidence/method_model_landing_coverage_20260605.md",
    "60_model/scripts/adapt_choice_probability_and_validation_targets.py",
    "40_quality_evidence/choice_probability_adapter_20260604.md",
    "40_quality_evidence/simulation_validation_target_adapter_20260604.md",
]

MAINLINE_OUTPUTS = [
    "60_model/llm_runs/contract_envelopes/choice_probability_from_p2_p4_20260604.json",
    "60_model/llm_runs/contract_envelopes/simulation_validation_target_from_p2_20260604.json",
    "70_outputs/processed_tables/choice_probability_from_p2_p4_20260604.csv",
    "70_outputs/processed_tables/simulation_validation_target_from_p2_20260604.csv",
    "40_quality_evidence/choice_probability_contract_validation_20260604.json",
    "40_quality_evidence/simulation_validation_target_contract_validation_20260604.json",
    "40_quality_evidence/simulation_object_pool_api_validation_20260604.json",
    "40_quality_evidence/simulation_object_pool_browser_validation_20260604.json",
    "40_quality_evidence/global_ai_design_rebaseline_overview_validation_20260604.json",
    "40_quality_evidence/project_context_legacy_risk_audit_20260605.json",
    "40_quality_evidence/method_model_landing_coverage_20260605.json",
]

STALE_TOP_PHRASES = [
    "不要先自我增强",
    "不要用“强化 agent”打断主线",
    "Codex 自身强化放在 P6 对象池主线后",
    "Codex 自身强化、新对话上下文优化、全局配置调整和工具路由增强必须排在这条主线完成之后",
    "下一步仍是 P6 用户可控仿真对象池",
]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def head_lines(path: Path, limit: int = 80) -> list[str]:
    if not path.exists():
        return []
    return read_text(path).splitlines()[:limit]


def file_status(path_str: str) -> dict[str, Any]:
    path = ROOT / path_str
    return {
        "path": path_str,
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
    }


def scan_stale_top_phrases() -> list[dict[str, str]]:
    targets = ["next_chat_prompt.md", "handoff_next_chat.md", "progress.md", "findings.md", "00_control/decisions.md"]
    findings: list[dict[str, str]] = []
    for target in targets:
        lines = head_lines(ROOT / target, 90)
        top_text = "\n".join(lines)
        for phrase in STALE_TOP_PHRASES:
            if phrase in top_text:
                findings.append({"path": target, "phrase": phrase})
    return findings


def load_verification_summary() -> dict[str, Any]:
    report = ROOT / "40_quality_evidence" / "verification" / "implementation_verification_20260526.md"
    if not report.exists():
        return {"exists": False}
    summary: dict[str, Any] = {"exists": True, "path": rel(report)}
    for line in read_text(report).splitlines():
        if line.startswith("- 总检查项："):
            summary["checks"] = line.split("：", 1)[1].strip()
        if line.startswith("- 失败项："):
            summary["failures"] = line.split("：", 1)[1].strip()
    return summary


def build_payload() -> dict[str, Any]:
    missing = [item for item in AUTHORITATIVE_FILES + MAINLINE_OUTPUTS if not (ROOT / item).exists()]
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "purpose": "Codex 主线防偏航上下文包：锁定全局 AI 仿真决策系统重基线，避免旧文件和旧 P6 口径误导后续判断。",
        "current_priority": "先完成全局重基线门禁，再继续重构 AI 工作台、方法对象池、资料池、仿真任务和旧产物信任地图。",
        "mainline_insert_rule": "Codex 自身强化只能作为主线防偏航层插入，不得替代仿真主线。",
        "next_mainline_step": "按全局 AI 仿真决策系统重基线，继续重构 AI 工作台、资料池/方法对象池、仿真任务入口，并建立旧文件信任地图，避免历史产物被误判为新方向成果。",
        "non_negotiables": [
            "系统总定位是 AI 驱动仿真决策系统；公园商业选址只是当前场景，不得把全局能力写死为单一公园商业工作台。",
            "老板六份方法资料是系统级重基线，不是补缺口资料。",
            "Flowus 和 2026 AI/HCI/agentic UI 资料是判断材料，必须落成对象、状态、交互和门禁，不得只写学习总结。",
            "方法、工具、插件、论文和同事成果必须进入审计清单，不能再用一句“已学习/已参考/已使用”带过。",
            "DeepSeek 是低成本语义工人，只能输出 draft/needs_review。",
            "旧 P4 完整仿真、ROI、最终排名、裸分数必须降级或重审。",
            "choice_probability 不得编造 probability_value。",
            "simulation_validation_target 用于阻止旧 dry-run 被误写成完整仿真。",
            "同事远端成果只能只读比较、选择性吸收，不能覆盖本地胜出逻辑。",
            "历史长文件夹必须建立信任分级：仍可信、需降级、仅历史参考、应废弃，不能默认沿用旧结论。",
            "老板模型和外部论文必须通过落点覆盖审计，不得只列模型名或论文名。",
            "DeepSeek 并发按账号计算，不能靠多 API Key 当架构；系统不得逐游客实时调用 DeepSeek。",
        ],
        "authoritative_files": [file_status(item) for item in AUTHORITATIVE_FILES],
        "mainline_outputs": [file_status(item) for item in MAINLINE_OUTPUTS],
        "missing_files": missing,
        "stale_top_phrase_findings": scan_stale_top_phrases(),
        "verification_summary": load_verification_summary(),
        "startup_commands": [
            "powershell -NoProfile -ExecutionPolicy Bypass -File .\\00_control\\start_codex_mainline.ps1",
            "powershell -NoProfile -ExecutionPolicy Bypass -File .\\00_control\\start_codex_mainline.ps1 -FullGate",
        ],
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# Codex 主线防偏航上下文包",
        "",
        f"- 生成时间：{payload['generated_at']}",
        f"- 当前优先级：{payload['current_priority']}",
        f"- 主线插入规则：{payload['mainline_insert_rule']}",
        f"- 下一步：{payload['next_mainline_step']}",
        "",
        "## 不可越界",
        "",
    ]
    for item in payload["non_negotiables"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 必读文件状态", ""])
    for item in payload["authoritative_files"]:
        status = "存在" if item["exists"] else "缺失"
        lines.append(f"- `{item['path']}`：{status}，{item['bytes']} bytes")
    lines.extend(["", "## 主线输出状态", ""])
    for item in payload["mainline_outputs"]:
        status = "存在" if item["exists"] else "缺失"
        lines.append(f"- `{item['path']}`：{status}，{item['bytes']} bytes")
    lines.extend(["", "## 顶部旧口径扫描", ""])
    stale = payload["stale_top_phrase_findings"]
    if stale:
        for item in stale:
            lines.append(f"- 发现旧口径：`{item['path']}` -> {item['phrase']}")
    else:
        lines.append("- 未在当前入口文件顶部发现旧的“不要先自我增强”口径。")
    lines.extend(["", "## 启动命令", ""])
    for command in payload["startup_commands"]:
        lines.append(f"- `{command}`")
    lines.extend(["", "## 门禁摘要", ""])
    summary = payload["verification_summary"]
    if summary.get("exists"):
        lines.append(f"- 报告：`{summary.get('path')}`")
        lines.append(f"- 检查项：{summary.get('checks', 'unknown')}")
        lines.append(f"- 失败项：{summary.get('failures', 'unknown')}")
    else:
        lines.append("- 尚未找到总门禁报告。")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(payload)
    missing_count = len(payload["missing_files"])
    stale_count = len(payload["stale_top_phrase_findings"])
    print(f"wrote {rel(OUT_JSON)}")
    print(f"wrote {rel(OUT_MD)}")
    print(f"missing_files={missing_count} stale_top_phrases={stale_count}")
    if missing_count or stale_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
