# 计算与模型知识包 2026-06-09

## 定位

- 这个文件是每次修改仿真、DeepSeek 约束、收益预测、节点解释和报告生成前的计算模型入口。
- 它不是论文堆积表，而是把近年核心库、方法参考库和经典理论按项目可用的模型层重新组织。
- 老板三层示例只保留为方向种子：Persona、ABM、Monte Carlo 都被放进更大的计算栈里。

## 当前规模

- 模型知识包：4405 条
- 覆盖模型层：13 类
- 年份分布：{'2026': 2764, '2025': 1610, '2001': 4, '2003': 1, '1996': 1, '1998': 3, '2017': 1, '1992': 1, '2011': 3, '2010': 2, '2009': 2, '2008': 1, '1994': 1, '2015': 1, '2005': 2, '2022': 1, '2019': 2, '0': 2, '2023': 1, '2021': 1, '2020': 1}
- 来源层级：{'core': 3170, 'screened': 1204, 'classic': 31}

## 正式计算栈

1. **evidence_data_foundation**：先锁定 PDF/CAD/客流/消费/POI 的证据与单位，禁止无来源参数进入计算。
2. **spatial_geometry_accessibility**：把 CAD/PDF/GIS 转成可量测空间底座，记录功能区、入口、路网、面积和误差。
3. **synthetic_population_persona**：把三类客群扩成微观 Persona：收入、频次、同行结构、任务、时段、价格敏感度。
4. **activity_chain_time_geography**：生成到达、游览、停留、补给、消费、离园活动链，避免单点静态判断。
5. **discrete_choice_spatial_interaction**：用选择/吸引力逻辑约束目的地和消费触发，LLM 只解释候选。
6. **abm_pedestrian_crowd_engine**：把 Persona 活动链放进 ABM/步行层，输出轨迹、拥挤、瓶颈和热力。
7. **queue_capacity_discrete_event**：对餐饮、咖啡亭、入口服务点做排队和服务容量仿真。
8. **revenue_conversion_unit_economics**：用客单价、转化率、复购/频次、容量和业态组合计算收益，不用单一均值替代。
9. **monte_carlo_uncertainty**：对关键变量做随机扰动，输出 P5/P50/P95 和场景区间。
10. **sensitivity_calibration_validation**：用敏感性分析找关键参数，并记录校准、验证、随机种子和复核状态。
11. **optimization_scenario_decision**：把多个候选节点/业态组合转成方案优先级、前置条件和试运营动作。
12. **real_world_modulators**：把天气、节假日、活动日、收入、人口、合规、噪声和投诉作为真实世界乘子。
13. **llm_agent_guardrails**：DeepSeek 只负责候选和结构化草案，所有输出必须过 schema、规则、证据和人工复核。

## 分层证据入口

### real_world_modulators

- 数量：420
- 控制问题：天气、季节、节假日、活动日、收入、人口、合规、投诉和真实运营边界。
- 调用方式：
  `py -3.12 30_extraction\scripts\query_model_computation_knowledge_20260609.py --layer real_world_modulators --query "奥森 仿真 收益" --limit 8`
- 代表资料：
  - 2026 | core | SAP IBP vs Custom AI Planning Engines: A Comparative Performance Study
  - 2026 | core | Balancing food safety and sustainability: trade-off risk assessments and predictive modeling
  - 2026 | core | Digital Twin (DT) and Extended Reality (XR) in the Construction Industry: A Systematic Literature Review
  - 2026 | core | Domain Knowledge-Enhanced LLMs for Fraud and Concept Drift Detection
  - 2026 | core | Fine-grained urban land use simulation: Integrating spatial dynamic modeling with a pre-trained vision-language model
  - 2026 | core | Linking digital twin paradigm for urban heat monitoring and policy integration to building smart city climate resilience
  - 2026 | core | LocalBench: Benchmarking LLMs on County-Level Local Knowledge and Reasoning
  - 2026 | core | Using Multi-Attribute Decision Analysis to Examine the Impact of Social Fitness of Shaded Public Space on Older Persons’ Depression

### spatial_geometry_accessibility

- 数量：420
- 控制问题：CAD/PDF/GIS 转换、六区细分、路网可达性、入口关系和服务半径。
- 调用方式：
  `py -3.12 30_extraction\scripts\query_model_computation_knowledge_20260609.py --layer spatial_geometry_accessibility --query "奥森 仿真 收益" --limit 8`
- 代表资料：
  - 2026 | core | Digital Twin (DT) and Extended Reality (XR) in the Construction Industry: A Systematic Literature Review
  - 2026 | core | Fine-grained urban land use simulation: Integrating spatial dynamic modeling with a pre-trained vision-language model
  - 2026 | core | Linking digital twin paradigm for urban heat monitoring and policy integration to building smart city climate resilience
  - 2026 | core | The Role of Digital Twin Technology in Enhancing Energy Efficiency in Buildings: A Systematic Literature Review
  - 2026 | core | Real-Time Digital Twin Architecture for Immersive Industrial Automation Training
  - 2026 | core | Urban color in public design: a review of spatial aesthetics and behavioral impact in Chinese and South Korean cities using structural equation modell
  - 2026 | core | On digital twins in defense: overview and applications
  - 2026 | core | Elevating Informality: Street Vending, Design Politics, and the Remaking of Public Space in Bandung

### llm_agent_guardrails

- 数量：420
- 控制问题：DeepSeek 的薄封装、JSON 输出、规则校验、人工复核和日志追踪。
- 调用方式：
  `py -3.12 30_extraction\scripts\query_model_computation_knowledge_20260609.py --layer llm_agent_guardrails --query "奥森 仿真 收益" --limit 8`
- 代表资料：
  - 2026 | core | Enterprise Spatial Data Provenance Knowledge Infrastructure
  - 2026 | core | SAPIENT: A Multi-Agent Framework for Corporate Reputation Intelligence Through Sentinel Monitoring and LLM-Based Synthetic Population Simulation
  - 2026 | core | Compliance Digital Twins for Autonomous Financial Agents: Reliability-Aware Scenario Assurance via Calibrated LLM Evaluation
  - 2026 | core | AI Agent Based Service Innovation to Enhance Efficiency and User Experience AI Agent Based Service Innovation to Enhance Efficiencyand User Experience
  - 2026 | core | Integrating Human-in-the-Loop Systems in AI-Based Fraud Detection for Accountable Decision-Making
  - 2026 | core | Integrating Large Language Models as Cognitive Agents into the GAMA Platform for Urban Mobility Simulation
  - 2026 | core | Prompt Injection Attacks in Large Language Models and AI Agent Systems: A Comprehensive Review of Vulnerabilities, Attack Vectors, and Defense Mechani
  - 2026 | core | DigMethpy: an AI-empowered digital catalysis platform for methane pyrolysis molten catalyst design

### optimization_scenario_decision

- 数量：320
- 控制问题：候选节点组合、优先级、约束条件、试运营动作和方案比较。
- 调用方式：
  `py -3.12 30_extraction\scripts\query_model_computation_knowledge_20260609.py --layer optimization_scenario_decision --query "奥森 仿真 收益" --limit 8`
- 代表资料：
  - 2026 | core | SAP IBP vs Custom AI Planning Engines: A Comparative Performance Study
  - 2026 | core | Application and Prospects of LiDAR in Nature-Based Solutions: A Bibliometric Analysis
  - 2026 | core | AI-Driven Building Automation Systems for Energy Optimization and Predictive Maintenance: A Quantitative Case Study of Smart Building Performance Enha
  - 2026 | core | Sustainable Port Site Selection in Mountainous Areas Within Continuous Dam Zones: A Multi-Criteria Decision-Making Framework
  - 2026 | core | Integration of GIS and MCDM for temporary shelter site selection in earthquake-risk zone: a case study with sensitivity analysis
  - 2026 | core | Pedestrian-Oriented Microclimate Optimization for Urban Plazas: Integrating Movement Patterns with Thermal Comfort Simulation
  - 2026 | core | A Proactive Maintenance Framework for Road and Bridge Infrastructure Based on Digital Twin, BIM, GIS, and IoT Integration
  - 2026 | core | A fuzzy-based decision framework for optimal co-working space site selection

### evidence_data_foundation

- 数量：320
- 控制问题：证据输入、字段来源、数据体检、单位一致性和客户结论的可追溯边界。
- 调用方式：
  `py -3.12 30_extraction\scripts\query_model_computation_knowledge_20260609.py --layer evidence_data_foundation --query "奥森 仿真 收益" --limit 8`
- 代表资料：
  - 2026 | core | SAP IBP vs Custom AI Planning Engines: A Comparative Performance Study
  - 2026 | core | Linking digital twin paradigm for urban heat monitoring and policy integration to building smart city climate resilience
  - 2026 | core | The economic impact of ESG-Driven office building Renovations: Evidence from prime Spanish commercial real estate
  - 2026 | core | Economic and logistical performance of refrigerated electric and hydrogen light commercial vehicles. A total cost of ownership and hybrid simulation p
  - 2026 | core | spanishoddata: A package for accessing and working with Spanish Open Mobility Big Data
  - 2026 | core | Urban color in public design: a review of spatial aesthetics and behavioral impact in Chinese and South Korean cities using structural equation modell
  - 2026 | core | On digital twins in defense: overview and applications
  - 2026 | core | Pedestrian Safety in Developing Countries: A Systematic Literature Review and Gap Analysis

### revenue_conversion_unit_economics

- 数量：320
- 控制问题：客单价、转化率、价格带、复购频次、业态组合和收益区间。
- 调用方式：
  `py -3.12 30_extraction\scripts\query_model_computation_knowledge_20260609.py --layer revenue_conversion_unit_economics --query "奥森 仿真 收益" --limit 8`
- 代表资料：
  - 2026 | core | Deep Learning Methods for Demand Forecasting and Inventory Optimization in Modern Supply Chains
  - 2026 | core | The economic impact of ESG-Driven office building Renovations: Evidence from prime Spanish commercial real estate
  - 2026 | core | The Reuse of Modern Historical Buildings in Tianjin--The Impact of Commercial Tenants on the Protection of Concession-Era Architecture
  - 2026 | core | Dynamic Integration in Agent-Based Modeling: Strategies for Optimizing Land-Use Change Policies in Peri-Urban Areas through Interactive Simulation
  - 2026 | core | Enhancing Inventory Planning in Retail SMES through Data‑Driven Demand Forecasting
  - 2026 | core | Developing a novel pricing model for super fresh products considering uncertainty: a case study from the fruit retail sector
  - 2026 | core | Visitor preferences and willingness to pay for urban recreation: the case of Entoto Recreational Park in Addis Ababa, Ethiopia
  - 2026 | core | Enabling the Circular Food Economy Through Industry 4.0: A Review of Applications, Challenges, and Policies in the European Union

### synthetic_population_persona

- 数量：320
- 控制问题：本地居民/外区游客/流动人口之外的频次、同行结构、收入、任务和价格敏感度。
- 调用方式：
  `py -3.12 30_extraction\scripts\query_model_computation_knowledge_20260609.py --layer synthetic_population_persona --query "奥森 仿真 收益" --limit 8`
- 代表资料：
  - 2026 | core | Using Multi-Attribute Decision Analysis to Examine the Impact of Social Fitness of Shaded Public Space on Older Persons’ Depression
  - 2026 | core | From informality to insight: Measuring inclusivity gaps in neighbourhood public space design through Informal Public Space Activity Diversity (IPSAD) 
  - 2026 | core | Resilience-Oriented Study on Pedestrian Accessibility Between Subway Stations and Commercial Complexes in Cities
  - 2026 | core | Origin-destination flow clustering for sustainable forest recreation planning – case study of Vienna Metropolitan Area, Austria
  - 2026 | core | Park morphology and urban structure for active living: a suburban case from Seongnam City
  - 2026 | core | Measuring Vitality and Spatial Efficiency of Public Spaces in Commercial Complexes: A Multi-Source Data-Driven Analysis in Guangzhou, China
  - 2026 | core | TikTok queues in tourism
  - 2026 | core | Analysis of Accessibility to Major Tourist Attractions in Wuhan from Subjective and Objective Perspectives

### abm_pedestrian_crowd_engine

- 数量：320
- 控制问题：Agent 状态转移、位置序列、功能区转移、拥挤瓶颈和热力图。
- 调用方式：
  `py -3.12 30_extraction\scripts\query_model_computation_knowledge_20260609.py --layer abm_pedestrian_crowd_engine --query "奥森 仿真 收益" --limit 8`
- 代表资料：
  - 2026 | core | A Hybrid Decision-Making Framework for Autonomous Vehicles in Urban Environments Based on Multi-Agent Reinforcement Learning with Explainable AI
  - 2026 | core | Simulation of Pedestrian Grouping and Avoidance Behavior Using an Enhanced Social Force Model
  - 2026 | core | Agent-Based Modeling of Urban Agriculture: Decision-Making, Policy Incentives, and Sustainability in Food Systems
  - 2026 | core | Modeling Ultra-High-Density Exposure and Evacuation Dynamics in a High-Density Urban Plaza: An Agent-Based Simulation Study of Guangzhou Huacheng Plaz
  - 2026 | core | Quantitative Risk Assessment of Ultra-High-Density Pedestrian Crowds Based on Multi-Agent Simulation
  - 2026 | core | Pedestrian Flow Model Based on Cellular Automata Under Visual Trajectory and Multi-Scenario Evacuation Simulation Research
  - 2026 | core | Agent-Based Modeling of Pedestrian Crossing Behavior in Commercial Streets: Seven Actionable Strategies for Safe and Sustainable Urban Mobility
  - 2026 | core | Optimizing Traditional Public Space Through Agent-Based Simulation: "A Case of Lagan Chowk"

### queue_capacity_discrete_event

- 数量：320
- 控制问题：咖啡亭、餐饮、入口服务、库存、人效和高峰服务压力。
- 调用方式：
  `py -3.12 30_extraction\scripts\query_model_computation_knowledge_20260609.py --layer queue_capacity_discrete_event --query "奥森 仿真 收益" --limit 8`
- 代表资料：
  - 2026 | core | Video-based cattle behaviour detection for digital twin development in precision dairy systems
  - 2026 | core | Assessing Emergency Egress on Retail Environments Through Pathfinder Simulation
  - 2026 | core | Modeling Ultra-High-Density Exposure and Evacuation Dynamics in a High-Density Urban Plaza: An Agent-Based Simulation Study of Guangzhou Huacheng Plaz
  - 2026 | core | Quantitative Risk Assessment of Ultra-High-Density Pedestrian Crowds Based on Multi-Agent Simulation
  - 2026 | core | Enhancing Urban Mobility: A Road Diet Approach to Improve Traffic Capacity and Pedestrian Safety
  - 2026 | core | Discrete Event Simulation Implementation for Service Throughput Optimization at Cafe King Kuphi
  - 2026 | core | Forecasting Racks-as-a-Service: Translating Demand Signals into Infrastructure Capacity
  - 2026 | core | Multi-stream Revenue Model for AI-based Fintech Lending using Enterprise Architecture Framework

### sensitivity_calibration_validation

- 数量：320
- 控制问题：参数影响排序、模型校准、可复跑验证、异常兜底和复核状态。
- 调用方式：
  `py -3.12 30_extraction\scripts\query_model_computation_knowledge_20260609.py --layer sensitivity_calibration_validation --query "奥森 仿真 收益" --limit 8`
- 代表资料：
  - 2026 | core | Integration of GIS and MCDM for temporary shelter site selection in earthquake-risk zone: a case study with sensitivity analysis
  - 2026 | core | Enhancing Digital Marketing Through Optimized CRM Selection: A Fuzzy AHP-TOPSIS Perspective
  - 2026 | core | Modeling Employment Sectoral Distribution Using POI Data: Assessing Tourism Functions in Data-Scarce Destinations
  - 2026 | core | Dynamic Evaluation of Urban Park Service Performance from the Perspective of “Vitality-Demand-Supply”: A Case Study of 59 Parks in Gongshu District, H
  - 2026 | core | Integrated assessment of environmental infrastructural and social risks for urban public safety
  - 2026 | core | Connect-4 AI: A Comprehensive Taxonomy and Critical Review of Methods and Metrics
  - 2026 | core | Systematic review of conceptual and methodological frameworks for sustainable landfill site selection using multi-criteria decision-making techniques
  - 2026 | core | Selection of Robots in Precision Agriculture Using Multi-Criteria Decision-Making Methods

### discrete_choice_spatial_interaction

- 数量：320
- 控制问题：destination/activity/spend 的选择概率和吸引力逻辑，防止 LLM 自由编结果。
- 调用方式：
  `py -3.12 30_extraction\scripts\query_model_computation_knowledge_20260609.py --layer discrete_choice_spatial_interaction --query "奥森 仿真 收益" --limit 8`
- 代表资料：
  - 2026 | core | CAMP: A Context-Aware, Multimodal, and Privacy-Preserving Pedestrian Trajectory Prediction Framework
  - 2026 | core | Modeling digitally augmented Huff model: Evidence from Otaku culture–driven spatial interactions
  - 2026 | core | Code and Data for Competitive Facility Location under Cross-Nested Logit Customer Choice Model: Hardness and Exact Approaches
  - 2025 | core | Literature Review on Public Transport and Land Use: Based on CiteSpace Statistical Analysis
  - 2025 | core | An Investigation of Site Selection Decisions of Residential Development Projects in Hangzhou Based on Potential Market Segmentation
  - 2025 | core | Modeling Pedestrian Behavior in Metro Stations with Commercial Facilities: An Attractiveness-Based Approach
  - 2025 | core | Agentic Large Language Models for day-to-day route choices
  - 2025 | core | Simulating Complex Urban Behaviours With AI: Incorporating Improved Intelligent Agents in Urban Simulation Models

### monte_carlo_uncertainty

- 数量：320
- 控制问题：日客流、天气、客群比例、客单价、转化率、容量和活动日的置信水位。
- 调用方式：
  `py -3.12 30_extraction\scripts\query_model_computation_knowledge_20260609.py --layer monte_carlo_uncertainty --query "奥森 仿真 收益" --limit 8`
- 代表资料：
  - 2026 | core | Smart Cities in the Agentic AI Era: Three Vectors of Urban Transformation
  - 2026 | core | LLM Readiness Harness: Evaluation, Observability, and CI Gates for LLM/RAG Applications
  - 2025 | core | YOLOv10-DSNet: A Lightweight and Efficient UAV-Based Detection Framework for Real-Time Small Target Monitoring in Smart Cities
  - 2025 | core | Understanding the evolutionary processes and causes of groundwater drought using an interpretable machine learning model
  - 2026 | screened | LHS-Compatible Global Sensitivity Analysis Methods for Building Performance Simulation: A Rural Residential Case Study in Cold Climates
  - 2026 | screened | Posterior-Contact Soft-ZUPT for Foot-Mounted Inertial Navigation: Uncertainty-Aware Pseudo-Observation Modeling
  - 2026 | screened | Beyond peak demand: integrating occupancy sensing and analytics for evidence-based meeting space optimization
  - 2026 | screened | Application of SciML-Adapted PCMM to Deep Neural Network Surrogate Model Used for Aerodynamic Coefficient Prediction

### activity_chain_time_geography

- 数量：265
- 控制问题：到达、游览、停留、换区、补给、消费、离园的时间空间链路。
- 调用方式：
  `py -3.12 30_extraction\scripts\query_model_computation_knowledge_20260609.py --layer activity_chain_time_geography --query "奥森 仿真 收益" --limit 8`
- 代表资料：
  - 2026 | core | Consumer Movement Patterns and Their Influence on Retail Space Planning: Evidence from Organized Retail Stores
  - 2026 | core | Dwell Time Estimation Using Periodic Image Captures and Deep Learning
  - 2026 | core | Built Environment, Safety, and Urban Economic Contexts in Shaping Urban Park Visitation for Sustainable Urban Development: Evidence from a Multi-Metho
  - 2026 | core | Discrete Event Simulation Implementation for Service Throughput Optimization at Cafe King Kuphi
  - 2026 | core | Dual-adaptive event-triggered control for time-varying switched systems with average dwell time
  - 2026 | core | Stability and stabilization for positive switched delay systems under mode-dependent interval dwell time
  - 2026 | core | Exploring the effects of riverine flooding on traffic demand forecasting using activity-based modeling in Ubon Ratchathani, Thailand
  - 2026 | core | Stability analysis of switched systems under weighted average persistent dwell time switching

## 使用红线

- 客户报告不能写“请补资料/训练资料/内部 API/路径/调试”。
- 经典理论只约束模型边界，不直接变成奥森结论。
- 近年论文只提供方法和变量启发，真实结论必须回到本地数据、证据台账和可复跑计算。
- 如果模型包查询不到支撑，不允许凭感觉新增计算逻辑；先扩查询矩阵或查官方/论文来源。
