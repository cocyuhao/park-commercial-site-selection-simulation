# 人物仿真方法选择与论文吸收评估（2026-06-04）

> 状态：方法选择矩阵。  
> 回应用户纠正：不能只说“看过论文”，必须说明这些论文是否新、是否好、在本项目是否最优、有无替代方案、如何落成用户可自由增删改查的系统对象。

> 追加纠偏：用户说的“模仿人类”是后续 UI/可用性测试方法，指智能体像真实业务用户一样操作网页；不是方法层只判断“像不像人”。方法层必须先全盘吸收老板资料里的模型，再判断哪些适合本项目、哪些暂时禁用、哪些落成对象和门禁。

## 0. 先说实话：目前还没做到“全量工程吸收”

已完成：

- 老板六份资料已被抽取、归档并写入主控重基线。
- 21 篇论文/方法资料已被筛选进外部论文矩阵。
- ROTE、HumanLM、LLM-ABM 批判、SSR、MATSim/SUMO/AnyLogic、Huff/Logit/Gravity 等已转成设计约束。
- 已落地 `persona_state`、`behavior_program`、`node_explanation`、`deepseek_task_contract` 等 schema。
- 已把旧 DeepSeek 输出纳入 metadata-only envelope。
- 已开始把旧 P4 节点分数降级为 `node_explanation`。

还没有完成：

- 不是每篇论文都已经变成可运行代码。
- 人群状态、行为程序、选择概率、校准目标还没有全部进入 P6 页面 CRUD。
- 还没有把 1200 条衍生场景全面接成 UI 和 Selenium 用例。
- 还没有完成真实数据校准，因此不能称完整人物仿真完成。

所以当前正确口径是：**论文已经被用于重设系统方向和部分工程对象，但还没有完成全量工程吸收。**

## 1. 方法选择标准

后续每个方法都按 7 个维度评估：

| 维度 | 问题 |
|---|---|
| 新鲜度 | 是否是近年方法，是否仍有活跃文档或公开项目支撑 |
| 质量 | 是否来自高质量论文、官方文档、成熟产品或经典模型 |
| 本项目适配度 | 是否能解释公园商业中的人、路线、时间、消费、供需和校准 |
| 数据需求 | 当前资料能否支撑；缺什么资料 |
| 工程成本 | 是否适合当前本地 Python/P6 Web，而不是过早引入重平台 |
| 用户自由度 | 是否支持用户增删改查、采用/放弃、锁定/解锁 |
| 风险边界 | 哪些情况下不能使用或不能写成结论 |

## 2. 路线比较

| 路线 | 是否采用 | 为什么 |
|---|---|---|
| 让 DeepSeek 直接捏人、走路线、给分、写结论 | 不作为主线 | 成本低但不可复跑、容易幻觉、容易把“像人”误当真实行为；只能做候选生成和解释草稿 |
| 只用同事 POI/TGI 缺口公式 | 只作辅助层 | 能解释供需缺口，但不能解释人为什么来、什么时候买、什么时候放弃、路线怎么走 |
| 纯专业仿真引擎，如 AnyLogic/SUMO/MATSim | 作为参照和后续接口，不现在整套搬入 | 方法成熟，但当前缺完整路网、几何、OD、容量和校准数据；过早引入会增加复杂度 |
| 本地 Python ABM/Monte Carlo + schema + 用户可编辑假设 | 采用为当前主线 | 可复跑、可解释、可逐步补数据；能把 DeepSeek 约束在候选层 |
| 证据层 + 人群状态 + 行为程序 + 空间/消费概率 + 宏观校准 + P6 工作台 | 采用为总路线 | 最符合老板资料和用户要求：既能仿真人，也能保留用户自主权和缺口 |

## 3. 论文和方法逐项评估

| 方法/资料 | 新鲜度/质量 | 对本项目是否最优 | 采用方式 | 不采用/禁用边界 |
|---|---|---|---|---|
| ROTE / Modeling Others' Minds as Code | 新，2025 arXiv；高相关 | 对“路线/行为程序”很适合，但当前不宜完整复现 Bayesian/SMC | 采用“行为程序”思想：触发、状态、动作、放弃、外溢、证据、校准状态 | 不能声称已实现 ROTE；不能让 DeepSeek 生成代码后直接执行 |
| HumanLM | 新，2026；直接讨论用户模拟 | 对“精确画像”最关键；比普通 persona 更适合 | 采用 latent state：目的、疲劳、预算、同行、时间压力、绕行、风险容忍 | 不训练 HumanLM；不能用表面话术相似代替行为准确 |
| GameLook / SSR / Agent Bank | 方法启发强，需降级看待营销案例 | 适合纠正“裸分数”和“薄 persona” | 先自然语言理由，再映射优先级；智能体需要记忆资料 | 不照搬 85% 准确率；不把游戏案例当公园验证 |
| LLM-ABM 批判综述 | 新，2025；风险价值高 | 对防止空想最关键 | 作为风险门禁：believability 不等于 operational validity | 不用 LLM 多 agent 数量证明真实性 |
| Causal inference critique | 2023；高价值风险方法 | 对“LLM 模拟实验”很重要 | 提醒 prompt 和处理变量会混淆；保持缺口和对照 | 不把 TGI/相关性写成因果 |
| MATSim | 成熟、官方文档活跃 | 后续做活动链/园区出行可参考，但当前太重 | 借鉴活动计划、网络、校准概念 | 当前不引入完整 Java/MATSim 流程 |
| SUMO pedestrian | 成熟、官方文档活跃 | 适合路网/人行路径/OD 后续验证 | 作为路径和 OD 仿真的候选引擎 | 当前没有足够路网/OD，不能装作已接入 |
| AnyLogic Pedestrian Library | 成熟商业产品，文档完整 | 适合理解物理空间、服务点、密度、排队 | 学习“服务点容量、停留、密度、障碍、状态图” | 不引入闭源商业工具作为当前依赖 |
| Huff / Gravity | 经典、GIS/Business Analyst 仍在用 | 适合供需/吸引力/距离衰减底座 | 用于“去哪里买/是否绕行”的概率因子 | 不能单独决定商业结论 |
| Logit / discrete choice | 经典且仍有现代扩展 | 适合消费选择概率 | 后续 choice_probability schema 的底层思想 | 当前缺真实选择数据，先做参数占位和敏感性 |
| Retail complementary goods ABM | 专题相关 | 适合业态互补/替代 | 用于判断饮品、轻餐、文创、活动、服务是否互相带动 | 不孤立评价单点业态 |
| Cities RL+LLM 社区仿真 | 老板资料核心，方法完整 | 是宏观目标，但当前数据不够 | 采用状态-行为-证据链一致性 + 宏观统计一致性双门禁 | 不声称已复现 3000 agent/RL/UE/GIS/BIM |

## 4. 当前最优方法组合

当前最优不是“最新论文全搬”，也不是“DeepSeek 直接捏人”。最优组合是：

1. **用户可编辑对象层**  
   所有人群、状态、行为、供给、场景、校准目标、运营方案都必须是对象，支持新增、编辑、采用、放弃、删除、锁定。

2. **DeepSeek 受限生成层**  
   DeepSeek 只生成候选：人群状态、行为程序、节点解释、报告草稿、状态-行为一致性草评。所有输出必须有 schema、source_refs、missing_inputs、needs_review。

3. **本地 Python 仿真层**  
   Python 负责抽样、概率、路径成本、选择、敏感性、随机种子、门禁和复跑。

4. **空间/消费模型层**  
   空间用距离、可达、容量、排队、外溢；消费用 Huff/Logit/Gravity/互补替代做可解释概率，不用 LLM 直接给最终概率。

5. **校准验证层**  
   没有真实客流、转化率、收益成本、授权和几何时，只输出草案；有真实数据后才算 SSIM/KL/DTW/峰谷/现场复核。

## 5. “自由可加减”的硬性规则

用户反复强调自由和自主权，因此后续 UI/API 必须满足：

- 不写死人群。
- 不写死节点。
- 不写死业态。
- 不写死行为脚本。
- 不写死 DeepSeek 生成结果。
- 不把采用状态藏在后端。
- 不让 AI 自动替用户采用或删除。

每个对象必须至少有：

| 字段 | 含义 |
|---|---|
| `id` | 稳定 ID |
| `object_type` | 人群、状态、行为程序、时间场景、空间节点、供给设施、校准目标、运营方案 |
| `display_name` | 给人看的名称 |
| `source_refs` | 来自哪些资料 |
| `editable_fields` | 用户能改的字段 |
| `missing_inputs` | 缺什么 |
| `adoption_state` | 已采用 / 候选 / 暂未采用 / 已放弃 |
| `user_locked` | 用户是否锁定，锁定后 DeepSeek 不能覆盖 |
| `deepseek_allowed_actions` | DeepSeek 允许做什么 |
| `review_notes` | 人工复核说明 |

## 6. 对已有工作的纠偏

| 已有内容 | 当前判断 | 下一步 |
|---|---|---|
| `person_simulation_control.schema.json` | 方向对，但还没真正进入 UI | 接 P6 CRUD |
| 1200 条衍生场景 | 有用，但目前只是样本空间 | 抽样转测试和页面候选 |
| P4 节点讨论分 | 必须降级 | 已开始转 `node_explanation`，分数默认隐藏 |
| 旧 DeepSeek 输出 envelope | 只纳管元数据 | 继续做任务专用 adapter |
| POI/TGI 缺口 | 有价值 | 接入 choice_probability 和 demand/supply 层 |
| P6 工作台 | 产品壳可用 | 需要接状态/行为/供给/校准对象 CRUD |

## 7. 参考资料清单

已核验或使用的高优先级来源：

- ROTE / Modeling Others' Minds as Code: https://arxiv.org/abs/2510.01272
- HumanLM: https://arxiv.org/abs/2603.03303
- LLM causal inference critique: https://arxiv.org/abs/2312.15524
- Generative ABM critical review: https://arxiv.org/abs/2504.03274
- MATSim docs: https://www.matsim.org/docs/
- SUMO pedestrians docs: https://sumo.dlr.de/userdoc/Simulation/Pedestrians.html
- AnyLogic Pedestrian Library: https://anylogic.help/9/libraries/pedestrian/index.html
- UrbanSim docs: https://cloud.urbansim.com/docs/general/documentation/urbansim.html
- ArcGIS Huff Model docs: https://pro.arcgis.com/en/pro-app/latest/tool-reference/business-analyst/understanding-huff-model.htm
- Retail complementary goods ABM: https://econpapers.repec.org/paper/nexwpaper/clustercomplements.htm

## 8. 下一步工程化顺序

1. 完成 `node_explanation` adapter，把旧节点分数全部降级为建议和补证动作。
2. 新增 `choice_probability.schema.json` 和 `simulation_validation_target.schema.json`。
3. 把 `person_simulation_control.schema.json` 接进 P6 页面，支持自由 CRUD。
4. DeepSeek 只生成候选对象，用户在页面里采用、放弃、删除、锁定。
5. 把 1200 条衍生场景抽样进 Selenium/单元测试。
6. 再考虑真正的仿真引擎扩展，而不是先做漂亮动画或最终排名。
