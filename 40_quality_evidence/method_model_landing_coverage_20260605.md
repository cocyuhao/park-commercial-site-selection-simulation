# 老板模型与外部论文落点覆盖审计（2026-06-05）

- 生成时间：2026-06-05T12:54:46
- covered：8
- partial：1
- missing：0

## 结论

- 昨天的资料不是白读，但 partial 仍不能当 completion：已有文档、schema、对象池或草稿 CSV，不等于已经完成真实人物仿真。
- 老板模型和外部论文的正确落地标准是：schema、adapter、UI 可编辑对象、DeepSeek 契约、本地验证脚本和门禁至少命中一条真实链路。
- 2026-06-05 纠偏：旧报告曾写 persona_state / behavior_program 尚未进入前端对象池；该结论已过时。当前对象池验证已确认 persona_state=6、behavior_program=12，并保留新增、编辑、采用、放弃、删除动作。
- 当前最明显缺口已变成：仿真任务入口还不能选择并组合人群状态/行为程序；DeepSeek 队列/缓存/429 退避尚未完整产品化；宏观验证指标还只是验证目标，没有真实计算。

## 覆盖明细

### SSR_DLR_FLR - covered

- 名称：DLR / FLR / SSR synthetic user rating methods
- 来源：老板长图与 591775 PDF；boss_model_inventory
- 原理：LLM 不直接打裸分；先产生动机、担忧、放弃理由，再映射为推进优先级。
- 下一步：继续清理用户可见分数字段，把分数默认折叠，主视觉只保留建议、依据和补证动作。
- 落点信号：
  - `10_research/boss_method_materials_20260604/boss_model_inventory_20260604.md`：ok；matched=['DLR', 'FLR', 'SSR']；missing=[]
  - `00_control/decisions.md`：ok；matched=['裸分数', '推进优先级']；missing=[]
  - `90_p6_expert_dashboard/static/app.js`：ok；matched=['discussion_score_draft', '推进优先级']；missing=[]

### ROTE_BEHAVIOR_PROGRAM - covered

- 名称：ROTE / behavior program / finite state behavior
- 来源：2510.01272v1.pdf；ROTE / Modeling Others' Minds as Code
- 原理：游客行为应变成可编辑、可复核的行为程序，不是每次临场让 LLM 编故事。
- 下一步：behavior_program 已进入对象池；下一步是让仿真任务入口选择、组合和预检行为程序，而不是只展示对象。
- 落点信号：
  - `60_model/schemas/behavior_program.schema.json`：ok；matched=['trigger_context', 'candidate_actions', 'failure_condition']；missing=[]
  - `70_outputs/processed_tables/p2_behavior_program_templates_20260604.csv`：ok；matched=['program_id', 'trigger_condition', 'abandon_or_spillover_condition']；missing=[]
  - `10_research/boss_method_materials_20260604/boss_model_inventory_20260604.md`：ok；matched=['ROTE', 'Finite State Machines']；missing=[]
  - `90_p6_expert_dashboard/static/index.html`：ok；matched=['behavior_program', '新增行为程序']；missing=[]
  - `40_quality_evidence/simulation_object_pool_persona_behavior_validation_20260605.json`：ok；matched=['has_behavior_program_objects', 'behavior_program=12']；missing=[]

### HUMANLM_LATENT_STATE - covered

- 名称：HumanLM latent state alignment
- 来源：2603.03303.pdf；HumanLM
- 原理：人物仿真准确性先看潜在状态是否充分，而不是看 AI 回答像不像人。
- 下一步：persona_state 已进入对象池；下一步是让 AI 工作台和仿真预检稳定显示 state -> behavior -> demand -> advice 链。
- 落点信号：
  - `60_model/schemas/persona_state.schema.json`：ok；matched=['purpose', 'time_pressure', 'queue_tolerance', 'companion_context']；missing=[]
  - `70_outputs/processed_tables/p2_persona_state_profiles_20260604.csv`：ok；matched=['persona_id', 'visit_purpose', 'calibration_status']；missing=[]
  - `10_research/boss_method_materials_20260604/boss_model_inventory_20260604.md`：ok；matched=['HumanLM', 'Latent State Modeling']；missing=[]
  - `10_research/boss_method_materials_20260604/simulation_accuracy_plan_20260604.md`：ok；matched=['状态准确', '行为准确']；missing=[]
  - `90_p6_expert_dashboard/static/index.html`：ok；matched=['persona_state', '新增人群状态']；missing=[]
  - `40_quality_evidence/simulation_object_pool_persona_behavior_validation_20260605.json`：ok；matched=['has_persona_state_objects', 'persona_state=6']；missing=[]

### RL_LLM_SOCIAL_SIM - covered

- 名称：RL + LLM high-definition social simulation
- 来源：人工智能模拟实验论文.docx；已转换 - main-1.docx
- 原理：宏观统计奖励 + 微观 LLM 草评；不能用页面 smoke test 代替仿真准确性验证。
- 下一步：建立微观状态-行为一致性验证脚本和宏观校准目标清单，不把干跑结果当完整仿真。
- 落点信号：
  - `10_research/boss_method_materials_20260604/boss_model_inventory_20260604.md`：ok；matched=['PPO', 'Macro Statistical Reward', 'Micro LLM Reward']；missing=[]
  - `10_research/boss_method_materials_20260604/unified_simulation_method_matrix_20260604.md`：ok；matched=['状态-行为-证据链一致性', '宏观统计一致性双门禁']；missing=[]
  - `60_model/schemas/simulation_validation_target.schema.json`：ok；matched=['metric_family', 'acceptance_rule']；missing=[]

### SPATIAL_ACTIVITY_CHAIN - covered

- 名称：Social Force / RVO / MATSim spatial and activity-chain simulation
- 来源：外部论文；老板统一矩阵
- 原理：空间仿真不是地图点位展示；需要路径、容量、活动链、拥挤和可达约束。
- 下一步：将现有地图/POI 只作为空间线索，后续在 P3 几何闭合后再接路网/容量/活动链。
- 落点信号：
  - `10_research/boss_method_materials_20260604/unified_simulation_method_matrix_20260604.md`：ok；matched=['Social Force', 'RVO', 'MATSim']；missing=[]
  - `60_model/simulation/engine.py`：ok；matched=['boundary_filter_status', 'blocked_gate_count']；missing=[]
  - `90_p6_expert_dashboard/app.py`：ok；matched=['MAP_CONTEXT_FILE', 'MAP_BOUNDARY_FILE']；missing=[]

### CHOICE_GAP_MODEL - covered

- 名称：Huff / Logit / Gravity / POI-TGI demand-supply gap
- 来源：外部零售选址模型；同事 POI_TGI_Calculator
- 原理：供需缺口是辅助层；选择概率由人群状态、行为程序、空间成本、排队、价格和供给共同决定。
- 下一步：把 POI/TGI 指标接入 choice_probability.factor_inputs，作为可开关辅助因子。
- 落点信号：
  - `60_model/schemas/choice_probability.schema.json`：ok；matched=['factor_inputs', 'distance_decay', 'queue_penalty']；missing=[]
  - `10_research/poi_tgi_calculator_selective_absorption_20260604.md`：ok；matched=['POI_TGI_Calculator', '选择性吸收']；missing=[]
  - `10_research/method_tool_plugin_audit_20260604.md`：ok；matched=['POI_TGI_Calculator', '降级为辅助']；missing=[]

### MACRO_VALIDATION_METRICS - partial

- 名称：SARIMA / SSIM / KL-Divergence / DTW validation metrics
- 来源：老板社区仿真资料与统一矩阵
- 原理：真实准确性需要对齐时段客流、热力形态、分布和曲线，而不是只靠截图或 AI 文字。
- 下一步：把验证目标对象在 UI 中作为运行前置条件展示，并阻止未闭合数据时宣称仿真可信。
- 落点信号：
  - `10_research/boss_method_materials_20260604/boss_model_inventory_20260604.md`：ok；matched=['SARIMA', 'SSIM', 'KL-Divergence', 'DTW']；missing=[]
  - `10_research/boss_method_materials_20260604/simulation_accuracy_plan_20260604.md`：partial；matched=['宏观验证']；missing=['DTW']
  - `60_model/schemas/simulation_validation_target.schema.json`：ok；matched=['metric_family', 'reference_data', 'required_fields']；missing=[]

### DEEPSEEK_CONSTRAINED_WORKER - covered

- 名称：DeepSeek constrained semantic worker
- 来源：DeepSeek API docs；本地契约；老板资料
- 原理：DeepSeek 便宜但不是总设计师；禁止逐游客实时调用，采用批处理、缓存和本地验证。
- 下一步：补 DeepSeek 调用队列、缓存、429 退避和 OpenTelemetry span；不得把多 key 当并发方案。
- 落点信号：
  - `10_research/deepseek_api_concurrency_capacity_20260605.md`：ok；matched=['账号并发', 'capacity expansion', '不应每个虚拟游客都调用一次 DeepSeek']；missing=[]
  - `10_research/boss_method_materials_20260604/deepseek_constrained_simulation_design_20260604.md`：ok；matched=['行为程序编译器', '逐游客']；missing=[]
  - `60_model/schemas/deepseek_task_contract.schema.json`：ok；matched=['output_status', 'review_required']；missing=[]
  - `60_model/src/llm_router.py`：ok；matched=['run_deepseek_task', 'risk == "high"']；missing=[]

### AGENTIC_UI_HUMAN_OVERSIGHT - covered

- 名称：Agentic UI / human oversight / GUI agent risk
- 来源：2026 AI/HCI 检索、Flowus、豆包/Codex 参考
- 原理：界面要让用户采用、放弃、锁定、复核；不能把 AI 草稿当不可修改的系统判断。
- 下一步：把人群状态、行为程序、选择概率、验证目标全部做成同样的可控对象链路。
- 落点信号：
  - `10_research/advanced_ai_learning_absorption_register_20260604.md`：ok；matched=['agent 可读 UI', '检查点调度', '旧产物信任地图']；missing=[]
  - `40_quality_evidence/advanced_agentic_workflow_validation_20260604.json`：ok；matched=['risk_taxonomy', 'agent_readability']；missing=[]
  - `90_p6_expert_dashboard/static/app.js`：ok；matched=['user_locked', 'adoption_status']；missing=[]
