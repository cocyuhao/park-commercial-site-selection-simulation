# 老板方法资料中的模型清单与本项目落地边界（2026-06-04）

> 状态：模型目录稿。  
> 目的：回应“老板发的材料里有好多模型”的提醒，把模型名、用途、禁用边界和本项目落点单独列清楚。  
> 口径：这些模型方向一致，但不能被武断合成一个已完成系统；它们是后续工程设计的约束和候选工具箱。

## 0. 先纠正此前表达缺口

我此前把六份资料主要整理成“方向矩阵”，但没有把里面的具体模型充分展开。这会造成两个问题：

1. 后续 agent 可能只记住“LLM 不能直接打分”，却不知道该用什么模型替代。
2. 页面和报告可能继续停留在“分数/建议”层，而没有把状态、行为、空间、消费、校准这些模型链路做出来。

因此本文件把老板材料中的模型拆成目录：哪些现在能落地，哪些要等 P3 数据闭合，哪些只能作为风险边界。

## 1. 合成用户与市场研究模型

来源：长图、`591775 (已转换).pdf`

### 1.1 DLR / FLR / SSR

| 模型/方法 | 含义 | 对本项目的启发 | 禁用边界 |
|---|---|---|---|
| DLR | Direct Likert Rating，让 LLM 直接打 1-5 分 | 作为反例：不要让 AI 直接给节点分数 | 不采用为主方法 |
| FLR | 先让 LLM 写文字，再由另一个模型映射到 Likert | 比 DLR 好，但仍可能受二次模型偏差影响 | 可作旁证，不做最终判断 |
| SSR | Semantic Similarity Rating，先自然语言表达，再映射到参考语句 | 节点建议应先产生“为什么来/买/放弃”的自然语言，再映射为优先级 | 不把 SSR 准确率照搬成本项目承诺 |

本项目落地：

- 节点页面主视觉不显示裸分数。
- 让 AI/规则先输出自然语言理由：吸引点、消费动机、放弃条件、证据缺口。
- 再把理由映射为：优先推进 / 补资料后判断 / 仅空间观察 / 暂缓。

### 1.2 Agent Bank / 1000+ grounded agents

核心：合成用户需要丰富记忆素材或真实自述，而不是一句浅 persona。

本项目落地：

- 资料池要能说明资料被用于哪类人群状态、行为脚本或校准目标。
- 若没有访谈、观察或真实反馈，不能假装有“深层用户记忆”。
- 可先用 PDF/TGI/POI/上传计划形成“弱记忆”，但必须标记 `needs_review`。

## 2. ROTE：行为程序模型

来源：`2510.01272v1.pdf`

### 2.1 核心模型

| 模型/方法 | 资料中的作用 | 本项目可迁移点 |
|---|---|---|
| ROTE | Representing Others' Trajectories as Executables | 把游客行为写成可编辑程序/脚本，而非每次让 LLM 编故事 |
| Program Synthesis | LLM 生成候选 Python 行为程序 | DeepSeek 可生成候选行为程序，但必须被 schema 和校验器约束 |
| Finite State Machines | 用状态和转移表达行为脚本 | 适合表达“晨跑-补水-离开”“亲子-疲劳-轻餐” |
| Bayesian Inference | 对候选程序权重做概率更新 | 后续有真实轨迹/停留数据后可更新脚本权重 |
| Sequential Monte Carlo | 逐步更新候选程序分布 | P3/P4 之后才考虑，不应现在假装实现 |
| Noise Model | 承认人的行为有随机性 | 节点建议要保留不确定性 |

### 2.2 资料中提到的对照模型

- Behavior Cloning：需要大量轨迹，泛化差。
- Inverse Reinforcement Learning：可推奖励，但数据和假设要求高。
- Bayesian Inverse Planning：推目标/信念，但多智能体下计算重。
- Reward Machines：可表达非马尔可夫奖励结构，可作为后续复杂行为脚本参考。
- Naive LLM / LLM-only：作为反例，不能让 LLM 每次临场预测行为。

本项目落地：

- 先做 `behavior_program_schema`：状态、触发、动作、放弃、外溢、证据、校准状态。
- 不急于实现 SMC 或贝叶斯权重更新；没有真实轨迹时只能做脚本候选。
- 前端应让用户看见并调整行为脚本，否则仿真仍是黑箱。

## 3. HumanLM：潜在状态模型

来源：`2603.03303.pdf`

### 3.1 核心模型

| 模型/方法 | 资料中的作用 | 本项目可迁移点 |
|---|---|---|
| Response Imitation | 模仿表面语言，是 HumanLM 批评对象 | 反对“AI 回复像人”就算模拟成功 |
| Latent State Modeling | 先生成潜在状态，再生成回应 | 游客画像要有目的、疲劳、预算、同行、绕行意愿 |
| State Alignment | 让生成状态与真实用户状态对齐 | 后续用真实反馈/观察校准人群状态 |
| LLM Judge | 比较 latent states 是否对齐 | DeepSeek 可做草评，但不能做最终门禁 |
| GRPO | 用批量 rollout 的对齐分数做强化学习 | 当前不训练模型，只学习“状态优先”的思想 |
| SFT baseline | 监督微调容易学表面风格 | 反例：不要只学报告/对话表面措辞 |

### 3.2 状态维度

HumanLM 原文强调：

- belief
- goal
- value
- stance
- emotion
- communication

公园商业语境转换：

- belief：用户认为哪里方便、哪里靠谱、哪里贵。
- goal：运动补给、亲子休息、社交停留、快取饮品、文化体验。
- value：安全、价格、品牌、速度、品质、安静、儿童友好。
- stance：对新增商业设施的接受/抗拒态度。
- emotion：疲劳、兴奋、烦躁、炎热、焦虑、放松。
- communication：业务报告里不直接呈现“说话风格”，但可用于 AI 工作台区分用户反馈语气。

本项目落地：

- 先定义 `persona_state_schema`。
- AI 工作台回答时必须解释 `state -> behavior -> demand -> advice` 链条。
- 不再只显示“亲子/白领/游客”这类薄标签。

## 4. 社区高清社会仿真：RL + LLM 混合模型

来源：`人工智能模拟实验论文.docx`、`已转换 - main-1.docx`

### 4.1 核心框架

| 模型/方法 | 资料中的作用 | 本项目可迁移点 |
|---|---|---|
| Unreal Engine | 构建高清虚拟社区 | 本项目暂不做 UE；只学习环境真实性要求 |
| GIS / BIM | 构建真实空间环境 | 本项目 P3 必须闭合 DWG/GIS/边界/路径 |
| 3000 agents | 大规模社区居民智能体 | 后续可做多 persona Monte Carlo，不急于逐人 LLM |
| RL framework | Agent, Environment, Observation, Action, Reward | 可作为 P4 真实仿真的结构模板 |
| PPO | 优化 policy network | 当前不训练 PPO；后续若有足够状态/动作/奖励再考虑 |
| Bellman Function / Bellman Equation | 长期回报和价值函数基础 | 当前只作理论背景，不直接实现 |
| Micro LLM Reward | LLM 对个体状态-动作链条做一致性草评 | 可用 DeepSeek 草评脚本是否符合资料、状态、路线、时间和场景 |
| Macro Statistical Reward | 模拟与真实数据差异形成宏观奖励 | 必须有真实客流/停留/转化数据才可使用 |
| Action Mask / rules | 约束不同人群可做动作 | 适合本项目先落地：儿童/老人/运动/亲子行为约束 |

### 4.2 观测与动作空间

资料中的观测：

- environment based observations
- action
- last action
- location
- last location
- phone usage
- age

本项目转换：

- time band
- weather / holiday / event
- current node
- last node
- route distance
- crowd / queue / seat capacity
- persona state
- demand trigger
- available POI/service

资料中的动作：

- go home
- go to workplace/school
- go to public area
- go to stores
- shopping / exercise / relax 等

本项目转换：

- enter park
- go to node
- stop / rest
- buy drink / light meal / souvenir / service
- queue / abandon
- spillover outside park
- return / exit

### 4.3 双重奖励

论文重点不是“LLM 很聪明”，而是纯 RL 和纯 LLM 都不够：

- 纯手机使用数据训练：可能学不到位置迁移和详细动作。
- 纯 LLM：动作不稳定、不可控、不可复现。
- 混合方式：宏观统计奖励 + 状态-行为链 LLM 草评奖励。

本项目落地：

- 没有真实宏观校准数据前，不做“训练完成”声明。
- 可以先做规则版双门禁：
  - 微观门禁：行为脚本是否符合人群状态和场景。
  - 宏观门禁：客流/TGI/POI/供需缺口是否有真实证据支撑。

## 5. 验证模型与指标

来源：社区仿真全文

| 指标/模型 | 资料中的作用 | 本项目可迁移点 |
|---|---|---|
| SARIMA | 检查真实/模拟时间序列是否具有内在一致性 | 有分时客流后可验证峰谷趋势 |
| SSIM | 把 24h x 7d 数据转为图像比较结构相似性 | 可用于热力图、时段客流矩阵或节点停留矩阵 |
| Fourier Transform / Phase Shift | 比较周期信号相位偏移 | 可用于峰值时间是否提前/滞后 |
| KL-Divergence | 比较真实和模拟分布差异 | 可用于业态需求分布、客流时段分布 |
| DTW / DTW-R2 | 比较时间序列形状相似性 | 可用于真实/模拟客流曲线对齐 |
| Social common sense validation | 用社会规律复核行为是否合理 | 用业务专家和现场观察复核“正常不正常” |

本项目落地：

- 现在先把这些写入验证目标。
- 等 P3 数据闭合后再真正计算。
- 不得把当前 Selenium 或页面截图当成仿真准确性验证；它们只是产品可用性验证。

## 6. 外部补强模型

这些不是老板材料主文，但与老板材料方向一致，适合后续补强：

| 模型 | 作用 | 本项目位置 |
|---|---|---|
| Social Force Model | 行人拥挤、避让、群体运动 | 空间运动层 |
| RVO | 多智能体避障 | 若做动态轨迹可视化 |
| MATSim | 活动链、多智能体出行仿真 | P4 长周期路线和活动链参照 |
| Huff Model | 商业吸引力与距离衰减 | 节点/业态吸引力解释 |
| Logit / MNL | 离散选择概率 | 消费/停留/绕行选择 |
| Gravity / Spatial Interaction | 空间交互和外溢 | 园内外供需与竞品影响 |
| Retail Complementary Goods ABM | 业态互补/替代 | 不孤立评价单点业态 |

## 7. 对当前工程的直接影响

### 现在就该做

- 文档纠偏：旧的“P4 完整仿真已完成”不能再作为当前事实。
- 节点 UI：分数降级，建议和补证动作升级。
- 资料池：资料要关联到人群、状态、行为、空间、供给、校准。
- AI 工作台：回答必须有 `state -> behavior -> demand -> advice` 链条。
- DeepSeek：生成候选而非最终判断。

### P3 数据闭合后再做

- 真实路径/容量/排队模型。
- 宏观校准指标计算。
- 真实转化率、收益成本和运营授权进入模型。
- 行为程序权重更新。
- 多 persona Monte Carlo / ABM。

### 暂不做

- Unreal Engine 高清复刻。
- PPO 训练。
- Sequential Monte Carlo 权重更新。
- HumanLM 专用训练。
- 每个游客实时调用 DeepSeek。

## 8. 给后续 agent 的一句话

老板给的“很多模型”不是让我们炫技堆模型，而是让系统避免三种错误：LLM 自由编故事、分数伪精确、没有真实校准就宣称仿真完成。正确路线是：先用状态和行为程序把人建起来，再用空间和消费选择模型让人行动，最后用真实数据和验证指标纠偏。
