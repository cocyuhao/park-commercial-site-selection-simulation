# Codex 主线防偏航上下文包

- 生成时间：2026-06-06T22:45:06
- 当前优先级：先完成全局重基线门禁，再继续重构 AI 工作台、方法对象池、资料池、仿真任务和旧产物信任地图。
- 主线插入规则：Codex 自身强化只能作为主线防偏航层插入，不得替代仿真主线。
- 下一步：按全局 AI 仿真决策系统重基线，继续重构 AI 工作台、资料池/方法对象池、仿真任务入口，并建立旧文件信任地图，避免历史产物被误判为新方向成果。

## 不可越界

- 系统总定位是 AI 驱动仿真决策系统；公园商业选址只是当前场景，不得把全局能力写死为单一公园商业工作台。
- 老板六份方法资料是系统级重基线，不是补缺口资料。
- Flowus 和 2026 AI/HCI/agentic UI 资料是判断材料，必须落成对象、状态、交互和门禁，不得只写学习总结。
- 方法、工具、插件、论文和同事成果必须进入审计清单，不能再用一句“已学习/已参考/已使用”带过。
- DeepSeek 是低成本语义工人，只能输出 draft/needs_review。
- 旧 P4 完整仿真、ROI、最终排名、裸分数必须降级或重审。
- choice_probability 不得编造 probability_value。
- simulation_validation_target 用于阻止旧 dry-run 被误写成完整仿真。
- 同事远端成果只能只读比较、选择性吸收，不能覆盖本地胜出逻辑。
- 历史长文件夹必须建立信任分级：仍可信、需降级、仅历史参考、应废弃，不能默认沿用旧结论。
- 老板模型和外部论文必须通过落点覆盖审计，不得只列模型名或论文名。
- DeepSeek 并发按账号计算，不能靠多 API Key 当架构；系统不得逐游客实时调用 DeepSeek。

## 必读文件状态

- `AGENTS.md`：存在，13784 bytes
- `00_control/codex_mainline_guardrails.md`：存在，3726 bytes
- `00_control/decisions.md`：存在，78475 bytes
- `progress.md`：存在，154044 bytes
- `findings.md`：存在，111569 bytes
- `handoff_next_chat.md`：存在，135083 bytes
- `next_chat_prompt.md`：存在，28477 bytes
- `10_research/boss_method_materials_20260604/full_system_rebaseline_20260604.md`：存在，13080 bytes
- `10_research/boss_method_materials_20260604/method_absorption_landing_register_20260604.md`：存在，9182 bytes
- `10_research/boss_method_materials_20260604/modern_practical_method_rescreen_20260604.md`：存在，8083 bytes
- `10_research/global_ai_simulation_design_rebaseline_20260604.md`：存在，11902 bytes
- `10_research/advanced_ai_learning_absorption_register_20260604.md`：存在，12749 bytes
- `10_research/method_tool_plugin_audit_20260604.md`：存在，11517 bytes
- `10_research/deepseek_api_concurrency_capacity_20260605.md`：存在，3247 bytes
- `40_quality_evidence/flowus_ai_design_probe_20260604/flowus_probe_report.json`：存在，11897 bytes
- `40_quality_evidence/project_context_legacy_risk_audit_20260605.md`：存在，18791 bytes
- `40_quality_evidence/method_model_landing_coverage_20260605.md`：存在，9506 bytes
- `60_model/scripts/adapt_choice_probability_and_validation_targets.py`：存在，24753 bytes
- `40_quality_evidence/choice_probability_adapter_20260604.md`：存在，793 bytes
- `40_quality_evidence/simulation_validation_target_adapter_20260604.md`：存在，790 bytes

## 主线输出状态

- `60_model/llm_runs/contract_envelopes/choice_probability_from_p2_p4_20260604.json`：存在，100222 bytes
- `60_model/llm_runs/contract_envelopes/simulation_validation_target_from_p2_20260604.json`：存在，20591 bytes
- `70_outputs/processed_tables/choice_probability_from_p2_p4_20260604.csv`：存在，42969 bytes
- `70_outputs/processed_tables/simulation_validation_target_from_p2_20260604.csv`：存在，4676 bytes
- `40_quality_evidence/choice_probability_contract_validation_20260604.json`：存在，306 bytes
- `40_quality_evidence/simulation_validation_target_contract_validation_20260604.json`：存在，313 bytes
- `40_quality_evidence/simulation_object_pool_api_validation_20260604.json`：存在，872 bytes
- `40_quality_evidence/simulation_object_pool_browser_validation_20260604.json`：存在，1421 bytes
- `40_quality_evidence/global_ai_design_rebaseline_overview_validation_20260604.json`：存在，590 bytes
- `40_quality_evidence/project_context_legacy_risk_audit_20260605.json`：存在，59218 bytes
- `40_quality_evidence/method_model_landing_coverage_20260605.json`：存在，17035 bytes

## 顶部旧口径扫描

- 未在当前入口文件顶部发现旧的“不要先自我增强”口径。

## 启动命令

- `powershell -NoProfile -ExecutionPolicy Bypass -File .\00_control\start_codex_mainline.ps1`
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\00_control\start_codex_mainline.ps1 -FullGate`

## 门禁摘要

- 报告：`40_quality_evidence/verification/implementation_verification_20260526.md`
- 检查项：1049
- 失败项：0
