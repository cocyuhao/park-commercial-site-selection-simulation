# 近年知识库 2026-06-09

## 结论

- 状态：pass
- 原始候选：152726
- 去重后：30553
- 筛选入库：23091
- A 档：5516
- B 档：8384
- C 档：9191

## 主题覆盖

- simulation_stack_mega:persona_synthetic_population: 1764
- simulation_stack_persona_abm_mc:activity_chain_time_geography: 1532
- simulation_stack_persona_abm_mc:calibration_validation_evidence: 1517
- simulation_stack_persona_abm_mc:classic_theory_reference: 1461
- simulation_stack_persona_abm_mc:discrete_choice_spatial_interaction: 1441
- simulation_stack_persona_abm_mc:persona_synthetic_population: 1421
- simulation_stack_persona_abm_mc:monte_carlo_uncertainty_sensitivity: 1383
- simulation_stack_persona_abm_mc:abm_pedestrian_crowd_engine: 1324
- simulation_stack_persona_abm_mc:tools_official_and_practical: 1275
- simulation_stack_mega:activity_chain_time_geography: 1273
- simulation_stack_persona_abm_mc:queue_capacity_discrete_event: 1226
- agent_llm_simulation: 1030
- real_world_constraints: 918
- safety_regulation_public_governance: 917
- weather_season_event_demand: 891
- operations_revenue_unit_economics: 884
- queue_crowd_capacity_operations: 864
- demographics_income_market_segmentation: 860
- human_mobility_behavior: 857
- retail_operations_revenue: 814
- spatial_site_selection: 809
- official_statistics_open_data_context: 798
- cad_bim_gis_digital_twin: 776
- park_recreation_tourism: 772
- park_publicness_experience_equity: 764
- transport_accessibility_last_mile: 748
- simulation_stack_mega:calibration_validation_evidence: 714
- decision_reporting_methods: 682
- simulation_stack_mega:abm_pedestrian_crowd_engine: 660
- simulation_stack_mega:cad_gis_spatial_data_foundation: 656
- ai_evaluation_observability_guardrails: 641
- data_quality_evidence_chain: 638
- multi_criteria_optimization_uncertainty: 634
- service_design_ai_workbench_ux: 511
- simulation_stack_mega:real_world_modulators: 462
- computation_model_mega:stochastic_uncertainty_sensitivity: 450
- computation_model_mega:gis_network_geometry_model: 446
- computation_model_mega:facility_location_optimization: 425
- computation_model_mega:abm_microsimulation_pedestrian: 399
- computation_model_mega:demand_revenue_forecasting: 378
- simulation_stack_mega:monte_carlo_uncertainty_sensitivity: 357
- simulation_stack_mega:discrete_choice_spatial_interaction: 328
- simulation_stack_mega:queue_capacity_discrete_event: 318
- computation_model_mega:bayesian_calibration_validation: 309
- computation_model_mega:discrete_event_queue_capacity: 307
- computation_model_mega:llm_agent_model_control: 299
- computation_model_mega:synthetic_population_activity_travel: 277
- computation_model_mega:discrete_choice_spatial_interaction: 190
- simulation_stack_persona_abm_mc:arxiv_recent: 131

## 项目落点

- 天气、收入、人口、合规等现实约束：9553 条；用法：约束真实世界落地：把收入、天气、人口、许可、安全和舆情列为决策前置变量。
- 空间节点与 GIS/POI/可达性：7715 条；用法：约束地图/节点比较：距离、可达、POI 供给和竞品密度不能单独变成收益结论。
- Agent/LLM/仿真方法：6376 条；用法：约束 DeepSeek：只做候选生成、解释和初筛；概率/排名/收益必须由规则和证据复核。
- AI 约束评估与人工复核：5399 条；用法：约束 DeepSeek 和 Agent：只允许生成候选、解释、初筛和草案，最终排序必须经证据、schema 和人工复核。
- 决策支持与报告表达：5362 条；用法：约束报告结构：写多方案、依据、不可判断边界和下一步动作，不写模板化空话。
- 天气季节活动与微气候：5057 条；用法：约束分时段预测：把晴雨、冷热、节假日、活动日和季节波动作为需求乘子，不写成固定客流。
- 商业业态、价格与转化：4070 条；用法：约束报告建议：节点建议必须包含价格带、转化触发、试运营指标和退出条件。
- 公园游憩与公共空间：3580 条；用法：约束公园商业：公共性、游客体验和游憩需求优先，不把普通商场逻辑硬套公园。
- 客流、活动链与路线：2445 条；用法：约束仿真：先生成分时段活动链和路线，再计算停留与消费触发。
- 合规安全治理与投诉约束：2176 条；用法：约束落地建议：食品、消防、噪声、夜间运营和公共空间治理必须成为方案边界和退出条件。
- 人口收入与客群市场分层：1911 条；用法：约束客群模型：把亲子、银发、运动、通勤、游客和周边居民分开，不用单一平均收入替代真实需求。
- Monte Carlo 与敏感性分析：1661 条；用法：约束不确定性：P5/P50/P95 不只扰动日客流，还要扰动天气、转化率、客单价、客群比例和容量。
- Persona 与活动链建模：1471 条；用法：约束 Persona：三类客群只是底座，必须叠加频次、任务、同行结构、时段和停留活动链。
- CAD/GIS/数字孪生与空间转换：1183 条；用法：约束 CAD/PDF/DWG 处理：先记录坐标、比例尺、图层和转换误差，再进入面积、动线和节点模拟。
- ABM/Mesa 与步行仿真引擎：962 条；用法：约束轨迹层：Mesa 可作为实现工具，核心是 Agent 状态转移、路线、拥挤、热力和校准。
- 运营收益容量与试运营指标：955 条；用法：约束商业建议：每个建议要能落到价格带、转化触发、容量、人效、库存和试运营复盘指标。
- 数据质量证据链与可追溯：503 条；用法：约束全链路：所有结论必须能回到 PDF/CAD/POI/表格/脚本输出，不能把工具日志写给客户。
- 未分类：434 条；用法：作为辅助背景，进入方法库但不直接生成项目结论。
- 离散选择与消费/目的地选择：424 条；用法：约束决策逻辑：目的地、活动和消费触发要用选择模型/效用逻辑表达，不用固定模板替代。

## 各主题高分样本

### spatial_site_selection
- 2026 | 84.86 | A Holistic Framework for Flood Risk Assessment and Optimal Design of Mitigation Measures | https://doi.org/10.1007/s40710-026-00818-1
- 2026 | 82.75 | Resilient Electric Vehicle Charging Stations in Urban Areas: A Systematic Literature Review | https://doi.org/10.3390/wevj17030148
- 2026 | 82.75 | Equity-Oriented Decision-Making for Renewable Energy Investments | https://doi.org/10.3390/en19020463
- 2026 | 82.75 | Fine-grained urban land use simulation: Integrating spatial dynamic modeling with a pre-trained vision-language model | https://doi.org/10.1016/j.compenvurbsys.2026.102416
- 2026 | 81.73 | A Multi-Criteria Evaluation of Powertrain Options for Long-Term Rental with Implications for Sustainable Transport | https://doi.org/10.3390/su18020553

### human_mobility_behavior
- 2026 | 82.75 | Linking digital twin paradigm for urban heat monitoring and policy integration to building smart city climate resilience | https://doi.org/10.1007/s44327-025-00179-8
- 2026 | 81.73 | Designing for mild winters: evidence-based thermal comfort benchmarks from urban parks in a sub-tropical city | https://doi.org/10.1007/s00484-026-03190-9
- 2026 | 81.73 | Reimagining Urban Public Spaces through Human-Centered Spatial Design in Growing Coastal Cities | https://doi.org/10.24815/riwayat.v9i1.377
- 2026 | 81.73 | Urban color in public design: a review of spatial aesthetics and behavioral impact in Chinese and South Korean cities using structural equation modelling approaches | https://doi.org/10.3389/fpsyg.2026.1692740
- 2026 | 81.73 | Urban Injection in Historic Centers: Space Syntax Approach | https://doi.org/10.38094/jastt71692

### agent_llm_simulation
- 2026 | 82.75 | LocalBench: Benchmarking LLMs on County-Level Local Knowledge and Reasoning | https://doi.org/10.1609/aaai.v40i45.41190
- 2026 | 82.75 | An Enterprise Agentic Architecture Framework for Agentic AI Governance and Scalable Autonomy | https://doi.org/10.64539/sjcs.v2i1.2026.368
- 2026 | 82.75 | A Hybrid Decision-Making Framework for Autonomous Vehicles in Urban Environments Based on Multi-Agent Reinforcement Learning with Explainable AI | https://doi.org/10.3390/vehicles8010008
- 2026 | 81.73 | Agent-Based Modeling of Urban Agriculture: Decision-Making, Policy Incentives, and Sustainability in Food Systems | https://doi.org/10.3390/complexities2010002
- 2026 | 80.0 | Modeling Ultra-High-Density Exposure and Evacuation Dynamics in a High-Density Urban Plaza: An Agent-Based Simulation Study of Guangzhou Huacheng Plaza | https://doi.org/10.3390/buildings16101922

### park_recreation_tourism
- 2026 | 83.47 | Energy Management in Microgrids: Commercial, Industrial, and Residential Perspectives | https://doi.org/10.3390/en19020419
- 2026 | 82.75 | Using Multi-Attribute Decision Analysis to Examine the Impact of Social Fitness of Shaded Public Space on Older Persons’ Depression | https://doi.org/10.3390/su18010539
- 2026 | 82.75 | Socio‐demographic and geographical patterns in forest and park use: Insights from 33 European countries | https://doi.org/10.1002/pan3.70257
- 2026 | 81.73 | Integrating GIS and AHP for sustainable ecotourism site suitability analysis: a case study of Bahir Dar, Ethiopia | https://doi.org/10.1038/s41598-026-41548-6
- 2026 | 81.73 | Reliable Emergency Facility Location Planning Under Complex Polygonal Barriers and Facility Failure Risks | https://doi.org/10.3390/mca31020050

### retail_operations_revenue
- 2026 | 84.02 | Balancing food safety and sustainability: trade-off risk assessments and predictive modeling | https://doi.org/10.3389/fsci.2026.1720772
- 2026 | 83.47 | Food Safety in the Catering Sector: Nonconformities, Challenges, and Strategic Interventions With Insights From South Asia and Africa | https://doi.org/10.1002/fsn3.71400
- 2026 | 82.75 | Resilient Electric Vehicle Charging Stations in Urban Areas: A Systematic Literature Review | https://doi.org/10.3390/wevj17030148
- 2026 | 80.0 | Unlocking Langkawi's tourism potential: Spatial analysis of attractions and facilities | https://doi.org/10.17576/geo-2026-2201-11
- 2026 | 80.0 | Inflation and Consumer Demand Reallocation: Evidence from Retail Equity Performance in Metropolitan Houston | https://doi.org/10.64137/31080030/ijfems-v2i2p101

### real_world_constraints
- 2026 | 84.86 | A Holistic Framework for Flood Risk Assessment and Optimal Design of Mitigation Measures | https://doi.org/10.1007/s40710-026-00818-1
- 2026 | 83.47 | Public health and urban resilience implications of sustainable sanitary waste management | https://doi.org/10.1186/s12982-026-01525-w
- 2026 | 82.75 | Using Multi-Attribute Decision Analysis to Examine the Impact of Social Fitness of Shaded Public Space on Older Persons’ Depression | https://doi.org/10.3390/su18010539
- 2026 | 81.73 | Large Recreation Declines Persist for Years after Severe Wildfire but Not after Low-Severity or Prescribed Fire | https://doi.org/10.22541/essoar.15002752/v1
- 2026 | 81.73 | Fruitful outcomes without fatal costs: non-lethal alternatives show promise in alleviating human-wildlife conflict involving an island flying fox | https://doi.org/10.7717/peerj.20859

### decision_reporting_methods
- 2026 | 85.76 | SAP IBP vs Custom AI Planning Engines: A Comparative Performance Study | https://doi.org/10.55124/jdit.v3i1.278
- 2026 | 84.02 | Bridging Analog and Digital: A Case Study on Pandemic Accelerated Digital Disruption in Healthcare Retail | https://doi.org/10.61093/hem.2025.4-02
- 2026 | 81.73 | Sustainability Indicators and Urban Decision-Making: A Multi-Layer Framework for Evidence-Based Urban Governance | https://doi.org/10.3390/urbansci10020070
- 2026 | 80.0 | A Decision-Support Framework for Equitable Urban Green Space Planning: Cooling-Weighted Park Accessibility for Older Adults | https://doi.org/10.3390/land15060989
- 2026 | 80.0 | AI-Based Decision Support Systems for Sustainable Development Policy and Planning | https://doi.org/10.55041/ijsrem29769

### cad_bim_gis_digital_twin
- 2026 | 83.47 | Digital Twin (DT) and Extended Reality (XR) in the Construction Industry: A Systematic Literature Review | https://doi.org/10.3390/buildings16030517
- 2026 | 82.75 | Fine-grained urban land use simulation: Integrating spatial dynamic modeling with a pre-trained vision-language model | https://doi.org/10.1016/j.compenvurbsys.2026.102416
- 2026 | 82.75 | The Role of Digital Twin Technology in Enhancing Energy Efficiency in Buildings: A Systematic Literature Review | https://doi.org/10.1002/ese3.70388
- 2026 | 81.73 | Integrating digital twins, BIM, and GIS for urban health equity: Advancing smart and sustainable healthcare planning | https://doi.org/10.1016/j.scs.2026.107429
- 2026 | 81.73 | On digital twins in defense: overview and applications | https://doi.org/10.1177/15485129261441817

### simulation_stack_persona_abm_mc

### weather_season_event_demand
- 2026 | 82.75 | Using Multi-Attribute Decision Analysis to Examine the Impact of Social Fitness of Shaded Public Space on Older Persons’ Depression | https://doi.org/10.3390/su18010539
- 2026 | 82.75 | Infrastructure, Governance, and Price Stability as Binding Constraints on Inbound Tourism to India | https://doi.org/10.3390/tourhosp7020057
- 2026 | 81.73 | From Prediction to Explanation: Explainable Machine Learning for Motor Vehicle–Involved Pedestrian and Cyclist Crash Risk | https://doi.org/10.3390/infrastructures11030077
- 2026 | 81.73 | Designing for mild winters: evidence-based thermal comfort benchmarks from urban parks in a sub-tropical city | https://doi.org/10.1007/s00484-026-03190-9
- 2026 | 81.73 | Reimagining Urban Public Spaces through Human-Centered Spatial Design in Growing Coastal Cities | https://doi.org/10.24815/riwayat.v9i1.377

### demographics_income_market_segmentation
- 2026 | 83.47 | Energy Management in Microgrids: Commercial, Industrial, and Residential Perspectives | https://doi.org/10.3390/en19020419
- 2026 | 82.75 | Socio‐demographic and geographical patterns in forest and park use: Insights from 33 European countries | https://doi.org/10.1002/pan3.70257
- 2026 | 81.73 | Public Space Privatization: A Catalyst for Urban Spaces Gentrification | https://doi.org/10.21625/archive-sr.v10i1.1252
- 2026 | 81.73 | Elevating Informality: Street Vending, Design Politics, and the Remaking of Public Space in Bandung | https://doi.org/10.17645/up.11073
- 2026 | 80.0 | Inflation and Consumer Demand Reallocation: Evidence from Retail Equity Performance in Metropolitan Houston | https://doi.org/10.64137/31080030/ijfems-v2i2p101

### safety_regulation_public_governance
- 2026 | 84.86 | A Holistic Framework for Flood Risk Assessment and Optimal Design of Mitigation Measures | https://doi.org/10.1007/s40710-026-00818-1
- 2026 | 83.47 | Public health and urban resilience implications of sustainable sanitary waste management | https://doi.org/10.1186/s12982-026-01525-w
- 2026 | 82.75 | Infrastructure, Governance, and Price Stability as Binding Constraints on Inbound Tourism to India | https://doi.org/10.3390/tourhosp7020057
- 2026 | 81.73 | Reliable Emergency Facility Location Planning Under Complex Polygonal Barriers and Facility Failure Risks | https://doi.org/10.3390/mca31020050
- 2026 | 81.73 | Governance Challenges Amid Post-Pandemic Office Market Disruption: Unpacking the Drivers of High Vacancy Rates in Commercial Office Spaces | https://doi.org/10.61093/pgrl.2(1).66-79.2026

### operations_revenue_unit_economics
- 2026 | 85.76 | SAP IBP vs Custom AI Planning Engines: A Comparative Performance Study | https://doi.org/10.55124/jdit.v3i1.278
- 2026 | 85.49 | Deep Learning Methods for Demand Forecasting and Inventory Optimization in Modern Supply Chains | https://doi.org/10.55220/2576-6759.v11i3.906
- 2026 | 82.75 | Infrastructure, Governance, and Price Stability as Binding Constraints on Inbound Tourism to India | https://doi.org/10.3390/tourhosp7020057
- 2026 | 82.75 | The economic impact of ESG-Driven office building Renovations: Evidence from prime Spanish commercial real estate | https://doi.org/10.1016/j.enbuild.2026.117132
- 2026 | 81.73 | Mapping the Nexus of Climate Resilience, Investment, Land Use, and Energy Justice in Energy Transition Regions: A Review | https://doi.org/10.3390/en19030704

### queue_crowd_capacity_operations
- 2026 | 82.75 | Economic and logistical performance of refrigerated electric and hydrogen light commercial vehicles. A total cost of ownership and hybrid simulation perspective | https://doi.org/10.1016/j.rtbm.2026.101595
- 2026 | 82.75 | Algorithmic Evaluation of Fire Evacuation Efficiency Under Dynamic Crowd and Smoke Conditions | https://doi.org/10.3390/fire9010032
- 2026 | 82.75 | Real-Time Digital Twin Architecture for Immersive Industrial Automation Training | https://doi.org/10.3390/s26072023
- 2026 | 82.75 | From informality to insight: Measuring inclusivity gaps in neighbourhood public space design through Informal Public Space Activity Diversity (IPSAD) in dense urban contexts | https://doi.org/10.1016/j.habitatint.2026.103726
- 2026 | 81.73 | Large Recreation Declines Persist for Years after Severe Wildfire but Not after Low-Severity or Prescribed Fire | https://doi.org/10.22541/essoar.15002752/v1

### transport_accessibility_last_mile
- 2026 | 82.75 | Resilient Electric Vehicle Charging Stations in Urban Areas: A Systematic Literature Review | https://doi.org/10.3390/wevj17030148
- 2026 | 82.75 | Hydrogen Compression Choices for Tomorrow’s Refueling Stations: Review of Recent Advances and Selection Guide | https://doi.org/10.3390/hydrogen7010025
- 2026 | 82.75 | From informality to insight: Measuring inclusivity gaps in neighbourhood public space design through Informal Public Space Activity Diversity (IPSAD) in dense urban contexts | https://doi.org/10.1016/j.habitatint.2026.103726
- 2026 | 81.73 | Urban color in public design: a review of spatial aesthetics and behavioral impact in Chinese and South Korean cities using structural equation modelling approaches | https://doi.org/10.3389/fpsyg.2026.1692740
- 2026 | 81.73 | Resilience-Oriented Study on Pedestrian Accessibility Between Subway Stations and Commercial Complexes in Cities | https://doi.org/10.3390/land15020266

### multi_criteria_optimization_uncertainty
- 2026 | 82.75 | Resilient Electric Vehicle Charging Stations in Urban Areas: A Systematic Literature Review | https://doi.org/10.3390/wevj17030148
- 2026 | 82.75 | Using Multi-Attribute Decision Analysis to Examine the Impact of Social Fitness of Shaded Public Space on Older Persons’ Depression | https://doi.org/10.3390/su18010539
- 2026 | 81.73 | A bi-objective robust optimization model for location-transportation under uncertainty with psychological costs | https://doi.org/10.1371/journal.pone.0340058
- 2026 | 81.73 | Massive Retail Location Choice as a Human‐Flow‐Covering Problem | https://doi.org/10.1111/gean.70036
- 2026 | 81.73 | Decoding green space supply–demand mismatch through urban morphology: Toward equitable urban planning with explainable machine learning | https://doi.org/10.1371/journal.pone.0342596

### ai_evaluation_observability_guardrails
- 2026 | 85.2 | Large language models in global health | https://doi.org/10.1038/s44360-025-00024-7
- 2026 | 84.02 | Safety of a large language model-based clinical decision support system in African primary healthcare | https://doi.org/10.1038/s44360-026-00082-5
- 2026 | 83.47 | Domain Knowledge-Enhanced LLMs for Fraud and Concept Drift Detection | https://doi.org/10.3390/electronics15030534
- 2026 | 82.75 | An Enterprise Agentic Architecture Framework for Agentic AI Governance and Scalable Autonomy | https://doi.org/10.64539/sjcs.v2i1.2026.368
- 2026 | 82.75 | Assessing the impact of safety guardrails on large language models using irritability metrics | https://doi.org/10.1038/s41746-025-02333-3

### service_design_ai_workbench_ux
- 2026 | 81.73 | A Comprehensive Review of Human-Robot Collaborative Manufacturing Systems: Technologies, Applications, and Future Trends | https://doi.org/10.3390/su18010515
- 2026 | 80.0 | Human-Centered AI in Learning Design: Integrating AI to Support Learners at the Margins | https://doi.org/10.64137/30508509/ijhsims-v3i1p102
- 2026 | 80.0 | Toward a Standards Framework for Hybrid Intelligence Governance: Integrating Human Judgment and AI Decision Support | https://doi.org/10.3390/standards6020020
- 2026 | 80.0 | E-State: A Multilingual and Explainable AI Framework for Real Estate Decision Support | https://doi.org/10.22214/ijraset.2026.80576
- 2026 | 80.0 | Decoding Hepatic Pathologies: A Novel Explainable AI Framework for Transparent Liver Disease Decision Support | https://doi.org/10.25258/ijddt.16.6s.131

### park_publicness_experience_equity
- 2026 | 82.75 | Socio‐demographic and geographical patterns in forest and park use: Insights from 33 European countries | https://doi.org/10.1002/pan3.70257
- 2026 | 82.75 | From informality to insight: Measuring inclusivity gaps in neighbourhood public space design through Informal Public Space Activity Diversity (IPSAD) in dense urban contexts | https://doi.org/10.1016/j.habitatint.2026.103726
- 2026 | 81.73 | Elevating Informality: Street Vending, Design Politics, and the Remaking of Public Space in Bandung | https://doi.org/10.17645/up.11073
- 2026 | 81.73 | Coastal public realms and housing livability in Saudi cities: developing a comprehensive waterfront development index (CWDI) for Jeddah | https://doi.org/10.3389/fbuil.2026.1750109
- 2026 | 81.73 | Optimizing Urban Green Space Ecosystem Services for Climate Resilience: A Multi-Dimensional Assessment of Urban Park Cooling Effects | https://doi.org/10.3390/f17030383

### data_quality_evidence_chain
- 2026 | 82.75 | spanishoddata: A package for accessing and working with Spanish Open Mobility Big Data | https://doi.org/10.1177/23998083251415040
- 2026 | 81.73 | Digitalizing Urban Planning Governance: Empirical Evidence from Yerevan and a Multi-Layer Framework for Data-Driven City Management | https://doi.org/10.3390/urbansci10040183
- 2026 | 80.0 | A Decision-Support Framework for Equitable Urban Green Space Planning: Cooling-Weighted Park Accessibility for Older Adults | https://doi.org/10.3390/land15060989
- 2026 | 80.0 | Smart Civic Issue Reporting System with Hybrid AI Classification and Geospatial Analytics for Efficient Urban Governance | https://doi.org/10.5281/zenodo.20430433
- 2026 | 80.0 | Enterprise Spatial Data Provenance Knowledge Infrastructure | https://doi.org/10.3390/ijgi15050182

### official_statistics_open_data_context
- 2026 | 82.75 | spanishoddata: A package for accessing and working with Spanish Open Mobility Big Data | https://doi.org/10.1177/23998083251415040
- 2026 | 81.73 | Socialist Consumption Revisited: Paternalistic Policies and Consumer Needs during the Polish Crisis | https://doi.org/10.1017/s0018246x26101496
- 2026 | 80.0 | Inflation and Consumer Demand Reallocation: Evidence from Retail Equity Performance in Metropolitan Houston | https://doi.org/10.64137/31080030/ijfems-v2i2p101
- 2026 | 80.0 | UNDERSTANDING RURAL CONSUMER BEHAVIOUR IN EMERGING FOOD RETAIL FORMATS: A STUDY ON PURCHASING TRENDS AND RETAIL PREFERENCES | https://doi.org/10.55955/510003
- 2026 | 80.0 | Enhancing Inventory Planning in Retail SMES through Data‑Driven Demand Forecasting | https://doi.org/10.58806/ijiissh.2026.v3i3n01

## 边界

- 这不是“照搬论文结论”的库，而是方法、约束、变量和检查项库。
- 进入报告前仍要结合本地 PDF、CAD、策划 DOCX、POI/TGI、证据台账和真实校准输入。
- DeepSeek 只能使用本库做候选解释和初筛，不能直接输出最终排序、收益或定案结论。
