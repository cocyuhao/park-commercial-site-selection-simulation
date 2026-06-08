# 现代实用方法复筛与工程落地（2026-06-04）

> 状态：现代方法补强与工程决策记录。  
> 背景：用户指出此前方法学习偏旧，过度停留在 Huff / Logit / Gravity / Social Force 等经典底座，没有充分吸收人工智能时代的城市仿真、LLM agent、混合生成器和现代数据工程。此文件用于修正主线。

## 0. 结论先写清楚

用户指出的问题成立：此前把经典方法讲得太重，现代 AI 仿真方法没有被放到主结构里。

本轮修正后的主线不是“用 DeepSeek 直接扮演很多游客”，也不是“用一个旧选址公式给节点打分”。正确主线应是：

1. 用真实资料、GIS、POI/TGI、时段、天气、客群和运营规则生成受约束的活动链与候选选择。
2. 用轻量领域生成器或本地仿真引擎批量展开场景。
3. 用 LLM 做个体差异、语义解释、异常案例、报告表达和候选行为程序，不做最终裁判。
4. 用 schema、规则、证据、敏感性分析、参数校准和人工复核收口。
5. UI 层让业务人员能新增、删除、采用、放弃、锁定这些对象，不把系统写死。

一句话：LLM 是现代仿真系统里的语义增强器和低成本生成工人，不是无约束的真理机。

## 1. 现代论文/方法的实际吸收

| 来源 | 年份 | 现代意义 | 对本项目的落点 | 当前动作 |
|---|---:|---|---|---|
| AgentSociety: Large-Scale Simulation of LLM-Driven Generative Agents | 2025 | 大规模 LLM generative agents 与社会行为仿真 | 说明 LLM agent 可以参与行为层，但必须有环境、状态和规则约束 | 作为未来多 agent 架构参考，不直接用 DeepSeek 无限循环 |
| AI Metropolis: Scaling LLM-based Multi-Agent Simulation with Out-of-order Execution | 2024 | 大规模 LLM 多智能体需要调度、并行和事件顺序控制 | 后续若做千级/万级游客，不应同步逐个问 LLM | 当前先用本地轻量生成器和批处理，不上分布式 |
| CAMS: CityGPT-Powered Agentic Framework for Urban Human Mobility Simulation | 2025 | 用城市知识与 LLM agent 做人类移动仿真 | 与本项目“人为什么来、怎么走、何时买/放弃”高度相关 | 进入 `behavior_program` / `simulation_validation_target` 思路 |
| MobiVerse: Hybrid Lightweight Domain-Specific Generator + LLMs | 2025 | 把轻量领域生成器和 LLM 结合，兼顾规模和个体差异 | 这是本项目当前最适合的路线：规则/数据先生成，LLM 后修正/解释 | 作为 P3/P4 主技术方向 |
| CitySim: Large-Scale LLM-Driven Agent Simulation | 2025 | 城市行为和城市动态的 LLM-driven agent 仿真 | 提醒 UI 工作台不应只聊天，而要围绕项目、历史、状态和对象运行 | 作为 P6 工作台和后端对象池参考 |
| GATSim: Urban Mobility Simulation with Generative Agents | 2025/2026 | 生成式 agent 用于城市移动仿真 | 可借鉴“生成行为 + 交通/空间约束”的分层 | 暂不做交通大模型，吸收分层思想 |
| ROTE / HumanLM / RL+LLM 社区仿真 | 2025/2026 | 行为程序、潜在状态、奖励与宏观校准 | 老板资料已经把这些方法指向本项目核心 | 已落成 schema 和验证目标；继续做 adapter |
| LLM-ABM 批判与因果批判 | 2024/2025 | 防止 LLM 编故事、把相关性当因果 | DeepSeek 必须 `needs_review`；报告不能把 POI/TGI 写成因果 | 已写入契约与决策边界 |

## 2. 经典方法的降级位置

这些方法不是不用，而是不再当主线：

| 经典方法 | 现在的地位 | 为什么不能当主角 |
|---|---|---|
| Huff / Gravity | `choice_probability.factor_inputs` 中的距离衰减、吸引力、供给承接因子 | 它们解释“去哪买”的一部分，但不解释状态、时段、结伴、排队、营业、天气和资料缺口 |
| Logit / Discrete Choice | 选择概率候选模型族 | 没有真实选择数据时，不能把参数写死成最终概率 |
| Social Force / RVO | 空间拥挤、避障、密度参考 | 当前缺真实几何、路径和容量，不可假装已经完成空间运动仿真 |
| MATSim / SUMO / AnyLogic | 成熟外部引擎候选 | 当前数据门禁没闭合，过早引入会把复杂度推高而不是提高真实性 |

## 3. 本轮补上的现代工具栈

已安装并纳入验证：

| 能力层 | 工具 | 用途 |
|---|---|---|
| 现代数据处理 | DuckDB, Polars | 大表、场景矩阵、中间结果、可复跑查询 |
| 契约门禁 | jsonschema, Pydantic | LLM 输出和仿真对象强约束 |
| 空间与路网 | GeoPandas, Shapely, NetworkX, OSMnx | 边界、距离、路网、候选路径和空间连接 |
| 轨迹分析 | MovingPandas | 后续真实轨迹/走访路径校准 |
| Agent 原型 | Mesa, Mesa-Geo | Python 端 agent-based 原型，不替代最终校准 |
| 事件/队列 | SimPy | 排队、服务时长、营业时段、库存/供给限制 |
| 校准与敏感性 | SALib, Optuna | 找出最影响结果的输入，后续用真实数据调参 |

重型组件暂缓：

- Ray：适合大规模分布式 agent，但当前先补对象、证据和本地原型。
- MATSim / SUMO：适合成熟交通仿真，但需要真实路网、OD、活动链和校准资料。
- Unreal / AnyLogic：适合高保真演示或专业仿真产品化，但当前不是最短路径。

## 4. DeepSeek 的现代用法

DeepSeek 便宜，但不能因为便宜就让它当总设计师。

允许：

- 批量把资料拆成 `persona_state`、`behavior_program`、`choice_probability`、`simulation_validation_target` 候选。
- 生成多个行为程序草案，交给本地 schema 和规则过滤。
- 解释“为什么这个节点现在只能补证后判断”。
- 把报告草稿改成业务人员能读的语言。
- 生成反例清单：什么情况下这个建议会失效。

禁止：

- 直接给最终选址结论。
- 直接给 ROI、收益预测、最终排名。
- 直接把 POI/TGI 相关性说成因果。
- 直接覆盖用户锁定对象。
- 直接在 UI 里展示后端/debug/raw/payload。

## 5. 下一步落地顺序

1. 继续写 `choice_probability` adapter：输入人群状态、行为程序、节点、供给、时段和资料引用，输出优先级、解释、建议、缺口，不输出最终分。
2. 继续写 `simulation_validation_target` adapter：把真实资料缺口转成可复核指标，如路线可达、时段分布、状态-行为一致性、选择概率敏感性。
3. 用 DuckDB/Polars 建一个可复跑的场景矩阵查询层，不再手写散落 CSV 逻辑。
4. 用 SimPy 做一个最小服务队列原型：例如补水点、咖啡车、文创摊的排队、营业、库存和放弃逻辑。
5. 用 SALib/Optuna 标出“最值得补真实数据”的参数，而不是平均地喊“资料不足”。
6. 后续 P6 UI 接入对象池，让用户可以新增/删除/采用/放弃/锁定人群状态、行为程序、供给设施、验证目标。

## 6. 本轮外部来源

- AgentSociety: `https://arxiv.org/abs/2502.08691`
- AI Metropolis: `http://arxiv.org/abs/2411.03519`
- CAMS: `http://arxiv.org/abs/2506.13599`
- MobiVerse: `http://arxiv.org/abs/2506.21784`
- CitySim: `https://doi.org/10.18653/v1/2025.emnlp-industry.15`
- GATSim: `http://arxiv.org/abs/2506.23306`
- Mesa docs: `https://mesa.readthedocs.io/`
- Mesa-Geo docs: `https://mesa-geo.readthedocs.io/`
- OSMnx docs: `https://osmnx.readthedocs.io/`
- MovingPandas docs: `https://movingpandas.readthedocs.io/`
- DuckDB docs: `https://duckdb.org/docs/`
- Polars docs: `https://docs.pola.rs/`
- SimPy docs: `https://simpy.readthedocs.io/`
- SALib docs: `https://salib.readthedocs.io/`
- Optuna docs: `https://optuna.readthedocs.io/`

## 7. 需要记住的纠偏

本项目不是“旧 GIS 选址模型 + AI 聊天框”。它应该成为“证据驱动、LLM 增强、用户可控、可校准的人群行为与商业选址仿真系统”。

旧方法保留解释力，新方法承担主线，DeepSeek 做低成本语义工作，Codex/人工负责架构、证据、门禁和最终判断。
