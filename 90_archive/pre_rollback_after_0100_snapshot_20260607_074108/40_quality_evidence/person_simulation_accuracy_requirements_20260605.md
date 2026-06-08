# 人物仿真准确性约束矩阵（2026-06-05）

- 生成时间：2026-06-07T03:24:40
- 状态：needs_review
- 用途：把老板六份资料、近期论文和当前工程对象转成可检查要求，防止“学了但不用”。

## 当前对象基础

- persona_state_profiles: 6
- behavior_program_templates: 12
- choice_probability_rows: 36
- validation_targets: 10
- feature_derivatives: 1200

## 方法来源与采用方式

| ID | 年份 | 来源 | 本项目采用方式 | 链接 |
|---|---:|---|---|---|
| BOSS-ROTE | 2025 | ROTE / Modeling Others' Minds as Code | 把游客行为写成可编辑、可复核的行为程序；DeepSeek 只能生成候选脚本。 | https://arxiv.org/abs/2510.01272 |
| BOSS-HUMANLM | 2026 | HumanLM latent state alignment | 先建潜在状态，再解释行为和需求；不把回复像真人当准确性标准。 | https://humanlm.stanford.edu/ |
| BOSS-RL-LLM | 2025 | Real-world community oriented high-definition social simulation | 形成微观状态-行为一致性和宏观统计一致性双门禁。 | https://doi.org/10.1016/j.cities.2025.106468 |
| MOD-AGENTSOCIETY | 2025/2026 | AgentSociety: Large-Scale Simulation of LLM-Driven Generative Agents | 大规模 generative agent 需要真实环境和仿真引擎，不应把聊天当仿真。 | https://arxiv.org/abs/2502.08691 |
| MOD-CAMS | 2025 | CAMS: A CityGPT-Powered Agentic Framework for Urban Human Mobility Simulation | 移动仿真要同时处理个体移动模式和群体分布约束，不能只靠 LLM 常识。 | https://arxiv.org/abs/2506.13599 |
| MOD-MOBIVERSE | 2025 | MobiVerse: Hybrid Lightweight Domain-Specific Generator and Large Language Models | 本项目主线采用轻量领域生成器/本地仿真为主，LLM 做上下文修正和解释。 | https://arxiv.org/abs/2506.21784 |
| MOD-GATSIM | 2025/2026 | GATSim: Urban Mobility Simulation with Generative Agents | 生成式移动 agent 需要认知结构、记忆、规划和交通/空间环境耦合。 | https://arxiv.org/abs/2506.23306 |
| RISK-LLM-ABM | 2024/2025 | Critical review of generative ABM and LLM simulated subjects | 防止把 believability、流畅解释或相关性当成 operational validity。 | https://arxiv.org/abs/2504.03274 |
| CTRL-CODEX-PRIMARY | 2026 | Development-time Codex governance and production DeepSeek-only boundary | Codex 只在开发期负责方法设计、约束、复核、门禁和最终判断；最终市场化网站内置 AI 只能使用 DeepSeek。 | AGENTS.md#十一、高能力主-agent--Codex-专属职责 |

## 准确性要求

### ACC-001 人群状态

- 要求：每个人群必须从浅标签升级为潜在状态画像。
- 为什么提高准确性：目的、时间压力、疲劳、同行、预算和绕行容忍会直接改变路线、停留、消费和放弃行为。
- 当前工程落点：persona_state.schema.json; p2_persona_state_profiles_20260604.csv; P6 对象池 persona_state
- 方法依据：BOSS-HUMANLM; MOD-GATSIM
- DeepSeek 允许：把资料和用户自然语言整理成 persona_state 草稿。
- DeepSeek 禁止：不得决定最终人群分布、不得把缺失的真实比例补成事实。
- 用户控制：用户可新增、编辑、采用、放弃、删除、锁定人群状态。
- 仍需数据：真实人群构成、时段客流、现场观察、访谈或运营记录。
- 验证方式：schema 校验 + 状态-行为一致性复核 + 真实资料回放。
- 状态：partial_landed
- 下一步工程动作：在仿真任务入口让用户选择 persona_state 组合和权重。

### ACC-002 行为程序

- 要求：行为必须以可编辑行为程序表达，而不是每次由 LLM 临场编故事。
- 为什么提高准确性：触发条件、动作、失败条件和外溢条件可复核，才有机会被真实轨迹和业务反馈校准。
- 当前工程落点：behavior_program.schema.json; p2_behavior_program_templates_20260604.csv; P6 对象池 behavior_program
- 方法依据：BOSS-ROTE; MOD-MOBIVERSE
- DeepSeek 允许：生成候选行为程序、解释触发和失败条件。
- DeepSeek 禁止：不得逐游客实时调用、不得直接输出最终路线或购买动作。
- 用户控制：用户可编辑触发、动作、放弃、外溢、来源和待复核项。
- 仍需数据：路径观察、停留时间、排队、天气、活动和真实服务使用记录。
- 验证方式：行为程序 schema 校验 + 微观状态-行为链检查。
- 状态：partial_landed
- 下一步工程动作：新增仿真预检：未选择行为程序时不允许宣称完成仿真。

### ACC-003 活动链与路线

- 要求：路线仿真必须由活动链、入口、路径、距离、容量和可达约束驱动。
- 为什么提高准确性：公园消费不是点到点移动；绕行、排队、座位、照明和营业时间会改变是否停留和是否消费。
- 当前工程落点：simulation_validation_target route_access; engine.py blocked gates
- 方法依据：MOD-CAMS; MOD-GATSIM; BOSS-RL-LLM
- DeepSeek 允许：解释路线选择的业务原因和缺失资料。
- DeepSeek 禁止：不得凭常识生成最终路线距离、拥挤或可达结论。
- 用户控制：用户可维护空间节点、供给设施、营业时间、路径缺口和授权状态。
- 仍需数据：DWG/DXF/GeoJSON、入口/路径网络、节点容量、座椅/排队/照明/授权。
- 验证方式：route_reachability + field_check + blocked gate。
- 状态：gated_design
- 下一步工程动作：把 spatial_node/supply_facility 纳入同一对象池并接仿真预检。

### ACC-004 选择概率

- 要求：选择概率由状态、行为、空间成本、价格、排队、供给和证据置信度共同决定。
- 为什么提高准确性：只看 POI/TGI 或节点分数会忽略人为什么买、为什么不买、为什么换地方。
- 当前工程落点：choice_probability.schema.json; choice_probability_from_p2_p4_20260604.csv
- 方法依据：BOSS-HUMANLM; MOD-MOBIVERSE; RISK-LLM-ABM
- DeepSeek 允许：生成概率因素说明和待补数据清单。
- DeepSeek 禁止：不得输出 final probability、ROI 或最终排名。
- 用户控制：用户可采用/放弃/锁定选择概率候选和因子。
- 仍需数据：转化率、客单价、距离、排队、价格带、竞品、营业时间、供给承接能力。
- 验证方式：因子完整性校验 + 敏感性分析 + 真实转化数据回放。
- 状态：partial_landed
- 下一步工程动作：建立 choice adapter，把 POI/TGI 降级为可开关辅助因子。

### ACC-005 供需与运营动作

- 要求：输出重点应是运营动作和补证动作，不是裸分或伪精确排名。
- 为什么提高准确性：业务人员需要知道该补什么数据、做什么试点、什么时候营业/补货/关闭，而不是只看分数。
- 当前工程落点：node_explanation; discussion_score_draft 折叠；推进优先级文案
- 方法依据：BOSS-ROTE; RISK-LLM-ABM
- DeepSeek 允许：把本地结果写成业务建议草稿。
- DeepSeek 禁止：不得把建议写成已验证结论，不得使用后端/debug 口吻。
- 用户控制：用户可采用、放弃、复核、生成报告或继续追问。
- 仍需数据：设施容量、补货/维护、营业时间、租金分成、授权、真实需求强度。
- 验证方式：报告结构检查 + 用户可见文案禁词扫描 + 真实资料引用检查。
- 状态：partial_landed
- 下一步工程动作：把运营动作绑定到状态/行为/概率对象，不让报告孤立生成。

### ACC-006 宏观校准

- 要求：完整仿真前必须定义客流、热力、分布、时间序列和业务决策的验证目标。
- 为什么提高准确性：没有真实校准，模型只能是方法原型；真实准确性要看曲线、分布和行为链是否对齐。
- 当前工程落点：simulation_validation_target.schema.json; p2_simulation_validation_targets_20260604.csv
- 方法依据：BOSS-RL-LLM; MOD-AGENTSOCIETY
- DeepSeek 允许：整理验证目标草稿和缺失数据说明。
- DeepSeek 禁止：不得把 Selenium、截图或 AI 解释当仿真准确性验证。
- 用户控制：用户可新增、采用、放弃、锁定验证目标和真实数据来源。
- 仍需数据：按入口/节点/时段客流、停留时长、转化率、交易、现场观察、活动日记录。
- 验证方式：SSIM/KL/DTW/correlation/field_check；当前缺数据时只可标 blocked/needs_review。
- 状态：partial_landed
- 下一步工程动作：新增验证目标预检面板，阻止未闭合数据时宣称完整仿真。

### ACC-007 DeepSeek 调用

- 要求：DeepSeek 是受限语义工人：批量、缓存、schema、队列、退避、可观测。
- 为什么提高准确性：便宜模型可扩大候选生成，但不稳定输出必须被本地校验和人工复核约束。
- 当前工程落点：deepseek_task_contract.schema.json; llm_router.py; deepseek_api_concurrency_capacity_20260605.md
- 方法依据：MOD-MOBIVERSE; RISK-LLM-ABM
- DeepSeek 允许：摘要、草拟、解释、补缺口、报告润色。
- DeepSeek 禁止：逐游客实时调用、最终排名、最终收益、checked 证据、覆盖用户锁定对象。
- 用户控制：用户可看到 AI 草稿状态并决定采用/放弃/锁定。
- 仍需数据：任务输入对象、缓存键、429/timeout 日志、输出状态和复核结果。
- 验证方式：JSON schema + contract validator + OpenTelemetry span + 429/timeout 结构化记录。
- 状态：partial_landed
- 下一步工程动作：补 DeepSeek 队列、缓存、退避和任务级 trace。

### ACC-008 用户监督

- 要求：所有关键对象必须支持采用、放弃、删除、编辑、锁定和复核记录。
- 为什么提高准确性：用户纠错是系统可信度的一部分；AI 或同事产物不能覆盖本地严谨判断。
- 当前工程落点：person_simulation_control.schema.json; P6 对象池 action controls
- 方法依据：MOD-AGENTSOCIETY; MOD-GATSIM; RISK-LLM-ABM
- DeepSeek 允许：解释用户改动的影响和提醒缺口。
- DeepSeek 禁止：不得自动删除、自动确认、自动覆盖锁定对象。
- 用户控制：用户拥有对象生命周期控制权。
- 仍需数据：对象状态、锁定状态、采用状态、来源引用、变更记录。
- 验证方式：API/Browser/Playwright/Selenium 动作后果验证。
- 状态：partial_landed
- 下一步工程动作：把资料、persona、behavior、choice、validation 的关联关系显示出来。

### ACC-009 高能力主控

- 要求：Codex / 高能力主 agent 只负责开发期方法吸收、系统约束、验证门禁和最终复核；最终网站不得内置 Codex，生产 AI 只能使用 DeepSeek。
- 为什么提高准确性：DeepSeek 适合市场化产品内低成本批量语义工作，但其约束、schema、反例检查、模型边界和真实数据门禁必须在开发期由高能力主 agent 做扎实。
- 当前工程落点：AGENTS.md high-capability duties; verify_project_implementation.py; person_simulation_accuracy_requirements_20260605
- 方法依据：CTRL-CODEX-PRIMARY; BOSS-RL-LLM; RISK-LLM-ABM
- DeepSeek 允许：在最终网站中承担唯一内置 AI：摘要、草拟、解释、补缺口、报告润色。
- DeepSeek 禁止：不得替代开发期 Codex 的架构判断、方法筛选、门禁设计、最终复核和用户约束设计；不得在生产端声称 Codex 能力。
- 用户控制：用户可在开发期要求 Codex 放手做主线研究、设计和验证；最终网页端 DeepSeek 输出仍由用户采用/放弃/锁定。
- 仍需数据：老板资料、论文来源、本地对象、门禁结果、浏览器验证和用户纠偏记录。
- 验证方式：DEC 记录 + 准确性矩阵 + 总门禁 + 交接文件共同约束新对话；生产代码不得出现 Codex 内置 AI 配置。
- 状态：covered_as_governance
- 下一步工程动作：后续 DeepSeek 队列/网页接入时同步保留开发期 Codex 复核脚本和高风险禁用边界，但不要把 Codex 接入最终网站。

## 产物完整性检查

| 文件 | 存在 | 字节 |
|---|---:|---:|
| `10_research/boss_method_materials_20260604/boss_model_inventory_20260604.md` | True | 11173 |
| `10_research/boss_method_materials_20260604/simulation_accuracy_plan_20260604.md` | True | 6365 |
| `10_research/boss_method_materials_20260604/modern_practical_method_rescreen_20260604.md` | True | 8083 |
| `10_research/person_simulation_accuracy_knowledge_base_20260604.md` | True | 12615 |
| `30_extraction/scripts/build_person_simulation_feature_derivatives.py` | True | 12960 |
| `30_extraction/scripts/verify_person_simulation_feature_derivatives_20260607.py` | True | 6783 |
| `70_outputs/processed_tables/person_simulation_feature_derivatives_1000_20260604.csv` | True | 1697712 |
| `40_quality_evidence/person_simulation_feature_derivatives_validation_20260607.json` | True | 2717 |
| `40_quality_evidence/person_simulation_feature_derivatives_validation_20260607.md` | True | 1860 |
| `60_model/schemas/persona_state.schema.json` | True | 2117 |
| `60_model/schemas/behavior_program.schema.json` | True | 2834 |
| `60_model/schemas/choice_probability.schema.json` | True | 3927 |
| `60_model/schemas/simulation_validation_target.schema.json` | True | 3763 |
| `60_model/schemas/deepseek_task_contract.schema.json` | True | 2221 |
| `40_quality_evidence/simulation_object_pool_persona_behavior_validation_20260605.json` | True | 1938 |

## 边界

This matrix is an implementation gate, not a claim that full simulation is complete. Formal accuracy still requires P3 real data closure.