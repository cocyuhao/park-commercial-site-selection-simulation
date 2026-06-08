# 页面是否重做的当前裁决审计（2026-06-05）

## 结论

- 结论：还没有完成整站级重做。
- 当前状态：旧 P6 页面壳上的过渡重基线，已接入对象链、AI 项目综合、仿真任务预检和验证体系。
- 工程判断：旧壳不能作为最终产品继续修补；下一步应页面级重构，迁移已验证底座，废弃旧叙事。

## 为什么不是继续小修

- 新链路已经存在：全局仿真链路台、对象链路矩阵、仿真任务入口、项目综合 AI。
- 旧壳也仍存在：节点清单、空间地图、资料导入、方法对象池、报告、AI 工作台仍按旧 view 并列。
- 这说明当前是过渡状态：能跑、能验证，但信息架构还没有完全跟上老板资料和现代仿真主线。

## 检查结果

- PASS `NEW-CHAIN-LANDED`：{"全局仿真链路台": 1, "对象链路矩阵": 1, "当前推进事项": 1, "仿真任务入口": 2, "项目综合": 10, "DeepSeek": 1}
- PASS `PAGE-VALIDATION-PASS`：{"status": "pass", "failure_count": 0}
- PASS `OBJECT-CHAIN-PASS`：{"object_count": 10, "summary": {"total_items": 10, "usable_count": 3, "draft_count": 6, "needs_input_count": 0, "blocked_count": 1}}
- PASS `PREFLIGHT-PASS-BUT-NOT-FINAL-SIMULATION`：{"status": "pass", "scope": "仿真任务入口只验证资料依据、对象组合和运行前预检；不证明完整人物仿真已经完成。"}
- PASS `OLD-SHELL-STILL-PRESENT`：{"节点清单": 6, "空间地图": 2, "资料导入": 4, "方法对象池": 0, "分析报告": 1, "专家 AI 工作台": 2, "panel": 55, "side-nav-item": 0}
- PASS `NO_FORBIDDEN_VISIBLE_LEAK_IN_STATIC_SURFACE`：{"visible_static_text": {"debug": 0, "traceback": 0, "ConnectError": 0, "external_preview_only": 0}, "internal_identifiers_allowed_but_must_not_render": {"raw": 26, "payload": 18}}
- PASS `BOSS-REBASELINE-REQUIRES-SYSTEM-LAYER`："full_system_rebaseline_20260604.md"
- PASS `BLUEPRINT-SAYS-NOT-PATCHING`："page_layer_rebuild_blueprint_20260605.md"
- PASS `RECENT-SIMULATION-LEARNING-BOUNDARY`："simulation_task_entry_evidence_reinforcement_20260605.md"
- PASS `CSS-STILL-LEGACY-PANEL-DOMINANT`：{"panel_reference_count": 55, "object_chain_count": 21}
- PASS `UI_UX_PRO_MAX_DESIGN_SYSTEM_USED`："10_research/ui_skill_design_system_audit_20260605.md"

## 迁移判断

### keep_as_verified_backend_or_data_base
- FastAPI dashboard/object-chain payload
- 资料池上传、采用、放弃、删除的后端状态
- 人群状态、行为程序、选择概率、验证目标对象数据
- 仿真任务预检接口和完整仿真阻止边界
- DeepSeek-only 生产端角色约束
- Playwright/axe/Lighthouse/OTel/高级 QA 证据链

### refactor_into_new_workflow_surface
- 左侧导航和旧 view 切换应重组为全局工作流步骤
- 全局推进台应成为任务编排首页，而不是多个 panel 的集合
- 资料池和方法对象池应合并为可采用/锁定/反驳的对象链工作区
- AI 工作台应成为项目综合与节点分析的持续沟通区，而不是独立问答页
- 节点、地图、报告应作为对象链下游工作区，不再并列成旧页面栏目

### retire_or_hide_from_user_surface
- 旧项目总览式死文案
- 裸分数、最终推荐、ROI 或完整仿真完成口径
- raw/debug/payload/traceback/ConnectError 等后端词
- 把静态地图兜底误写成真实自由地图仿真
- 把旧 dry-run 或 DeepSeek 草稿写成最终业务判断

## 下一版信息架构

- **01 全局链路台**：显示资料、状态、行为、选择、空间、验证、报告的整体进度和阻塞项。 依据：Flowus 设计学习, page_layer_rebuild_blueprint, object_chain API
- **02 资料与空间底座**：集中处理老板资料、策划文案、CAD/图纸、PDF 表格、高德 POI 和用户上传资料。 依据：老板资料 6/6, CAD/策划资料, evidence_ledger, AMap POI
- **03 人物仿真对象工坊**：让用户管理人群状态、行为程序、选择概率和验证目标，DeepSeek 只能生成候选。 依据：ROTE, HumanLM, MobileCity, M2LSimu
- **04 仿真任务预检**：组合对象并检查真实校准、宏观验证、空间几何和运营数据缺口。 依据：simulation_task_preflight, P3 gate, human oversight
- **05 决策解释与报告工作稿**：只在平台链路可回放后生成工作报告，明确已确认、待复核和禁止判断。 依据：DeepSeek-only, checked evidence rules, 商业报告语言规则

## 证据文件

- `00_control/page_layer_rebuild_blueprint_20260605.md`
- `10_research/boss_method_materials_20260604/full_system_rebaseline_20260604.md`
- `10_research/simulation_task_entry_evidence_reinforcement_20260605.md`
- `40_quality_evidence/page_layer_rebuild_validation_20260605.json`
- `40_quality_evidence/object_chain_rebaseline_validation_20260605.json`
- `40_quality_evidence/simulation_task_entry_preflight_validation_20260605.json`
