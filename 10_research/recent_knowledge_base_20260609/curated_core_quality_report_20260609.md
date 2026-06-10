# 部署级核心知识库质量报告 2026-06-09

## 结论

- 状态：pass
- 输入筛选库：23091 条
- 部署级核心库：3085 条
- 方法参考库：17306 条
- 剔除/暂不使用：2700 条
- 核心库来源：{'openalex': 1701, 'crossref': 1594, 'semantic_scholar': 11, 'arxiv': 90}

## 为什么要二次筛选

- 第一轮筛选解决“量”和“近年来源”问题，但仍会把部分泛 AI、能源、医疗、灾害、政策类文章误判为高分。
- 二次筛选按项目锚点、偏题信号、来源可信度、摘要完整度和可落地动作重分层。
- 以后默认用部署级核心库做架构和报告约束；方法参考库只用于启发方法，不直接变成客户结论。

## 核心库落点

- 空间节点与 GIS/POI/可达性: 1686
- 天气、收入、人口、合规等现实约束: 1582
- 公园游憩与公共空间: 989
- Agent/LLM/仿真方法: 958
- 决策支持与报告表达: 855
- AI 约束评估与人工复核: 846
- 天气季节活动与微气候: 756
- 商业业态、价格与转化: 742
- 客流、活动链与路线: 607
- 合规安全治理与投诉约束: 458
- CAD/GIS/数字孪生与空间转换: 422
- 人口收入与客群市场分层: 321
- Persona 与活动链建模: 307
- ABM/Mesa 与步行仿真引擎: 149
- 运营收益容量与试运营指标: 145
- Monte Carlo 与敏感性分析: 127
- 数据质量证据链与可追溯: 74
- 离散选择与消费/目的地选择: 50

## 核心库主题覆盖

- human_mobility_behavior: 375
- queue_crowd_capacity_operations: 370
- agent_llm_simulation: 363
- park_recreation_tourism: 347
- transport_accessibility_last_mile: 316
- simulation_stack_persona_abm_mc:abm_pedestrian_crowd_engine: 313
- cad_bim_gis_digital_twin: 300
- simulation_stack_persona_abm_mc:activity_chain_time_geography: 297
- park_publicness_experience_equity: 291
- spatial_site_selection: 285
- weather_season_event_demand: 284
- retail_operations_revenue: 280
- simulation_stack_persona_abm_mc:discrete_choice_spatial_interaction: 270
- operations_revenue_unit_economics: 268
- demographics_income_market_segmentation: 261
- multi_criteria_optimization_uncertainty: 247
- safety_regulation_public_governance: 239
- simulation_stack_persona_abm_mc:persona_synthetic_population: 235
- simulation_stack_persona_abm_mc:calibration_validation_evidence: 233
- real_world_constraints: 218
- simulation_stack_persona_abm_mc:queue_capacity_discrete_event: 205
- simulation_stack_mega:activity_chain_time_geography: 197
- simulation_stack_mega:persona_synthetic_population: 177
- official_statistics_open_data_context: 175
- simulation_stack_persona_abm_mc:classic_theory_reference: 155
- simulation_stack_persona_abm_mc:monte_carlo_uncertainty_sensitivity: 149
- data_quality_evidence_chain: 141
- decision_reporting_methods: 122
- simulation_stack_persona_abm_mc:tools_official_and_practical: 94
- ai_evaluation_observability_guardrails: 93
- simulation_stack_mega:abm_pedestrian_crowd_engine: 83
- simulation_stack_mega:cad_gis_spatial_data_foundation: 82
- computation_model_mega:gis_network_geometry_model: 76
- service_design_ai_workbench_ux: 61
- simulation_stack_mega:real_world_modulators: 57
- computation_model_mega:abm_microsimulation_pedestrian: 57
- simulation_stack_mega:calibration_validation_evidence: 51
- computation_model_mega:facility_location_optimization: 48
- simulation_stack_mega:queue_capacity_discrete_event: 38
- computation_model_mega:synthetic_population_activity_travel: 37
- computation_model_mega:demand_revenue_forecasting: 36
- computation_model_mega:stochastic_uncertainty_sensitivity: 35
- computation_model_mega:discrete_event_queue_capacity: 34
- simulation_stack_mega:discrete_choice_spatial_interaction: 34
- computation_model_mega:bayesian_calibration_validation: 29
- computation_model_mega:llm_agent_model_control: 22
- computation_model_mega:discrete_choice_spatial_interaction: 17
- simulation_stack_mega:monte_carlo_uncertainty_sensitivity: 12
- simulation_stack_persona_abm_mc:arxiv_recent: 11

## 下一步使用方式

- 用 `30_extraction/scripts/query_recent_knowledge_base_20260609.py` 按主题调用核心库。
- 用 `knowledge_theme_playbooks_20260609.json` 把知识映射到项目动作。
- 用 `integrated_simulation_architecture_blueprint_20260609.md` 把老板方向种子、近年知识库和现有项目捏合成正式仿真架构。
