# 外部论文筛选与落地映射（2026-06-04）

> 目的：补足老板六份方法资料的外部学术参照，但只保留能落到本项目模块的内容。  
> 口径：这些论文方向一致，但不是天然同一套系统；本文只把它们转成设计约束。  
> 资料来源：本地已保存 OpenAlex 查询结果 `external_method_papers_openalex_20260604.json`，并对核心条目打开官方 arXiv、项目页、DOI 或官方文档核验。

## 1. 筛选原则

采用论文必须至少满足一项：

- 能解释为什么不能让 LLM 直接模拟人、直接打分或直接给最终结论。
- 能提供人群状态、行为程序、空间运动、消费选择、校准验证中的一个可落地模块。
- 能指出风险：偏差、身份扁平化、因果混淆、不可复跑、缺少真实校准。
- 能帮助页面和报告把“分数”改成“解释 + 建议 + 补证动作”。

不采用或降级：

- 只证明 LLM 很像人，但没有验证或校准机制。
- 与公园商业选址无关的纯 NLP、纯图像、纯通用 agent 论文。
- 检索结果中标题相似但主题偏离的条目。

## 2. 当前 21 篇高价值条目

| ID | 论文/资料 | 模块 | 采用点 | 禁用边界 |
|---|---|---|---|---|
| LIT-001 | Modeling Others' Minds as Code / ROTE | 行为程序层 | 把日常行为写成脚本/程序；LLM 生成候选，概率推断处理不确定性 | 当前不宣称已实现 ROTE 或贝叶斯程序推断 |
| LIT-002 | HumanLM | 人群状态层 | 先生成潜在状态，再生成行为/回答；避免只模仿表面文本 | 不训练专用模型，不把文本相似当行为准确 |
| LIT-003 | Real world community oriented high-definition social simulation | 校准验证层 | RL+LLM、真实 GIS/BIM、3000 agents、微观/宏观双门禁 | 本项目没有 Unreal/GIS/BIM 全量环境，不能照搬完成度 |
| LIT-004 | Generative Agents | 工作台/记忆/计划 | 记忆、反思、计划可用于 AI 工作台和项目历史 | 25 人小镇不是商业选址验证 |
| LIT-005 | Out of One, Many | 人群样本 | 不要模拟一个平均人，要按群体分布模拟 | 不能替代真实样本、问卷或现场数据 |
| LIT-006 | LLMs to Simulate Multiple Humans | AI 被试验证 | 可做早期 synthetic participants 设计 | 必须和真人/真实数据对照 |
| LIT-007 | LLM Agents Grounded in Self-Reports / 1000+ agents | 合成用户记忆 | 丰富访谈/自述比人口统计更可靠 | 没有访谈/自述材料时不能伪造“深层记忆” |
| LIT-008 | LLMs for Market Research | 市场研究辅助 | AI 可做数据增强、早期方向探索 | 不能替代正式调研和 A/B |
| LIT-009 | LLM simulation causal inference critique | 风险控制 | 提醒实验设计和 prompt 模糊会引入混淆 | 不把 TGI/相关性写成因果 |
| LIT-010 | Critical review of generative ABM | 风险控制 | LLM 不自动解决 ABM 的校准、验证、复现 | 页面 believability 不能等于 operational validity |
| LIT-011 | LLMs and Computational Social Science | 计算社会科学 | LLM 适合解释、文本和扩展，但要与计算模型分工 | 不让 LLM 替代模型主干 |
| LIT-012 | Homo Silicus | 经济主体模拟 | 可参考经济选择实验设计 | 警惕模型偏见和身份扁平化 |
| LIT-013 | LLMs replacing human participants can misportray identity groups | 风险控制 | 禁止平均化、扁平化人群 | 不把“白领/亲子”写成完整人 |
| LIT-014 | Diminished diversity-of-thought | 风险控制 | 多 agent 不等于多样性，要在参数和真实数据中引入差异 | 不把多轮采样当真实多样性 |
| LIT-015 | Social Force Model | 空间运动 | 行人运动、拥挤、避让不能靠 LLM 文本 | 当前无完整路径/容量数据时只做设计参照 |
| LIT-016 | Reciprocal Velocity Obstacles | 空间运动/避障 | 若做动态轨迹，需要基础运动约束 | 不把前端动画当真实仿真 |
| LIT-017 | MATSim | 活动链/交通 ABM | 大规模出行仿真要有日程、网络、选择、校准 | 当前 dashboard dry-run 不是 MATSim 级仿真 |
| LIT-018 | Gravity / Spatial Interaction | 空间吸引 | 距离衰减、吸引力、外溢可解释 | 不能只用重力模型决定商业结论 |
| LIT-019 | Logit / discrete choice | 消费选择 | 消费选择概率应由可解释变量和校准支撑 | 不让 LLM 一句话决定购买概率 |
| LIT-020 | Retail Location Choice with Complementary Goods | 业态互补 | 候选业态存在互补/替代关系 | 不孤立评价单节点 |
| LIT-021 | Survey on LLM-based autonomous agents | Agent 工程 | 记忆、计划、工具调用可用于工作台架构 | 不替代领域仿真模型 |

## 3. 检索中主动排除的噪声

OpenAlex 的部分查询会返回高引用但无关的条目，例如图像增强、分子模拟、通用深度强化学习综述等。这类论文不进入方法矩阵，因为它们不能回答本项目的核心问题：公园商业选址中，人的状态、空间、消费和证据校准如何被可复跑地连接。

保守处理原则：

- 与公园商业、社会仿真、ABM、空间运动、消费选择、LLM 用户模拟无明确关系的条目，排除。
- 只有营销报道但缺少论文/项目页支撑的条目，保留为线索，不作为强方法依据。
- DOI 页面无法直接打开但 OpenAlex/本地资料记录完整的经典条目，先保留为方法旁证，后续再补正式 bibliographic 细节。

## 4. 对本项目最关键的 8 个方法判断

1. DeepSeek 不应在仿真循环中逐游客调用；应批量生成候选状态、候选行为程序和解释文本。
2. 仿真主干必须是本地 Python、schema、随机种子、日志和可复跑验证。
3. 人群不应只有 persona 标签，应有可编辑的潜在状态。
4. 行为不应是 AI 临场编故事，应是可编辑、可校验、可加权的行为程序。
5. 空间不是静态地图截图；要有路径、距离、容量、拥挤、放弃和外溢。
6. 消费不是裸分数；应由自然语言理由、选择概率、证据缺口和优先级共同表达。
7. 页面不是测试面板；要让业务人员能看懂“为什么、现在做什么、还缺什么”。
8. 报告不能把草案写成结论；必须区分已确认、早期信号、待复核和禁用判断。

## 5. 对 DeepSeek 接入的直接约束

DeepSeek 可以承担：

- `state_profile_draft`：人群状态草稿。
- `behavior_program_draft`：行为程序草稿。
- `node_reasoning_draft`：节点解释草稿。
- `report_language_draft`：报告语言草稿。
- `micro_reasonableness_judge`：微观合理性草评。

DeepSeek 输出不得直接承担：

- `checked_evidence`
- `final_ranking`
- `roi_forecast`
- `conversion_rate`
- `simulation_complete`
- `operation_decision`

每个 DeepSeek 任务必须对应：

- 输入文件列表。
- JSON schema。
- 字段白名单。
- 输出状态 `draft/needs_review`。
- 本地复核脚本。
- 失败重试或降级策略。

## 6. 下一步应转成的工程对象

| 工程对象 | 来源支撑 | 先做什么 |
|---|---|---|
| `persona_state_schema` | HumanLM、1000 agents、自述材料 | 先定义字段和 UI 展示，不急于跑完整仿真 |
| `behavior_program_schema` | ROTE、Generative Agents | 先做脚本草稿库和校验器 |
| `node_priority_explanation` | SSR、logit、retail ABM | 主视觉改为建议和补证动作 |
| `spatial_simulation_gate` | Social Force、RVO、MATSim | 明确缺少哪些路径/容量/几何数据 |
| `macro_validation_plan` | community simulation | 定义 SSIM/KL/DTW/峰值曲线等验证目标 |
| `deepseek_task_contracts` | DeepSeek 官方文档 | 只做受限 JSON 输出和缓存批处理 |

## 7. 已核验的官方/学术链接

- ROTE / Modeling Others' Minds as Code: `https://arxiv.org/abs/2510.01272`
- HumanLM project: `https://humanlm.stanford.edu/`
- Generative Agents: `https://arxiv.org/abs/2304.03442`
- 1000+ grounded individual simulations: `https://arxiv.org/abs/2411.10109`
- LLM simulation causal critique: `https://arxiv.org/abs/2312.15524`
- Critical review of generative ABM: `https://arxiv.org/abs/2504.03274`
- MATSim: `https://doi.org/10.5334/baw`
- DeepSeek API quick start: `https://api-docs.deepseek.com/`
- DeepSeek JSON Output: `https://api-docs.deepseek.com/guides/json_mode/`
- DeepSeek model/pricing page: `https://api-docs.deepseek.com/quick_start/pricing`
