# 老板资料与外部方法落地台账（2026-06-04）

> 状态：工程落地台账。  
> 目的：回应“内容不能只提及、必须投入落地”的纠正，把老板六份资料和外部论文中的方法逐项转成系统对象、字段、门禁和禁用边界。  
> 口径：本文件不宣称完整仿真已完成；它定义哪些方法已经进入工程约束，哪些仍是待实现对象。

## 0. 当前结论

之前的整理已经覆盖了老板六份资料的主方向，但还没有做到“全量工程吸收”。

这里必须修正一个容易混淆的边界：用户要求的“模仿人类”是指后续 Selenium / Browser / 智能体像真实业务用户一样反复使用网页，检查页面是否顺手、是否会误导、是否适合业务人员使用；不是指方法层只判断“像不像人”。方法层的目标是全盘吸收资料里的模型，把状态、行为程序、空间、消费选择、校准和验证全部落成可复跑对象。

本次补充的落地动作是：

- 新增 `choice_probability.schema.json`，把 Huff / Logit / Gravity、POI/TGI、距离衰减、排队惩罚、价格匹配、营业时间和证据置信度转成可审核对象。
- 新增 `simulation_validation_target.schema.json`，把状态-行为-证据链一致性、路线可达、时间序列、宏观分布、业务决策验证转成可审核对象。
- 扩展 `person_simulation_control.schema.json`，让选择概率和验证目标也能被用户新增、编辑、采用、放弃、删除和锁定。
- 扩展 `deepseek_task_contract.schema.json` 和 `validate_deepseek_contract_output.py`，允许 DeepSeek 生成选择概率候选和验证目标候选，但仍必须 `needs_review`。
- 将旧 P4 节点分数降级为 `node_explanation`，主输出改为建议、依据、缺口和复核动作，旧分数默认折叠。

2026-06-04 继续纠偏：此前现代 AI 仿真资料吸收不足，经典 Huff / Logit / Gravity / Social Force 被放得过重。已新增 `modern_practical_method_rescreen_20260604.md`，把 AgentSociety、AI Metropolis、CAMS、MobiVerse、CitySim、GATSim 等现代 LLM agent / 城市移动仿真方法纳入主线复筛。当前方法主线调整为“轻量领域生成器 + 空间/运营约束 + LLM 个体修正/解释 + schema/校准/人工门禁”，经典方法只保留为选择概率的可解释因子。

## 1. 方法到工程对象的对应关系

| 方法/模型 | 来源 | 必须落成的系统对象 | 当前工程落点 | 仍缺什么 |
|---|---|---|---|---|
| DLR 直接打分 | 老板长图 / GameLook | 反例门禁 | `node_explanation` 中旧分数默认隐藏；验证器禁止 final/checked | UI 继续弱化裸分数 |
| FLR 先写理由再映射评分 | 老板长图 / GameLook | 节点解释、报告草稿 | `node_explanation` 的 `why_now`、`specific_advice`、`review_actions` | 把 P6 节点详情改成理由优先 |
| SSR 语义相似评分 | 老板长图 / GameLook | 自然语言理由到优先级映射 | 方法约束已写入；当前尚未做独立 SSR 计算器 | 后续可做“理由相似度 -> 优先级”辅助工具 |
| Agent Bank / grounded agents | 老板长图 / GameLook | 资料记忆、人物状态、资料采用状态 | `person_simulation_control` 的 `source_material`、`persona_state` | P6 资料池需要显示资料影响了哪些状态和脚本 |
| ROTE 行为程序 | `2510.01272v1.pdf` | 行为脚本、状态转移、候选动作、失败条件 | `behavior_program.schema.json` | 真实轨迹不足，不能做 Bayesian / SMC 权重更新 |
| Program Synthesis | ROTE | DeepSeek 生成候选脚本，Python 校验 | `deepseek_task_contract` 的 `behavior_program` | 需要更多任务专用 adapter |
| Finite State Machine | ROTE | 状态、动作、转移 | `behavior_program` 的 trigger / action / transition | P6 还未可视化编辑状态机 |
| Bayesian Inference / SMC | ROTE | 程序权重更新 | 仅作为后续门禁记录 | 缺轨迹、停留、选择观测，当前禁用 |
| Behavior Cloning / IRL | ROTE 对照方法 | 风险边界 | `method_selection_evaluation` 已列为非当前主线 | 缺大量轨迹，当前禁用 |
| Reward Machines | ROTE 对照方法 | 复杂奖励结构候选 | 仅作为后续模型目录 | 当前不做复杂奖励机 |
| HumanLM 潜在状态 | `2603.03303.pdf` | 人群状态 | `persona_state.schema.json` | 需要 P6 CRUD 和真实资料回放 |
| State Alignment | HumanLM | 状态与行为一致性检查 | `simulation_validation_target` 的 `state_behavior_chain`、`state_behavior_consistency` | 需要状态-行为-证据链复核用例 |
| Response Imitation 反例 | HumanLM | 禁止只模仿话术 | 写入方法边界 | UI 报告还需减少 AI 味模板 |
| RL + LLM 社区仿真 | Cities 2026 论文 | 观察空间、动作空间、状态空间、双重奖励 | 本次落入 `simulation_validation_target`；已有 `persona_state` / `behavior_program` | 当前不训练 RL，不做 Unreal / 3D 复刻 |
| Observation / Action / State Space | Cities 2026 | 仿真控制对象 | `person_simulation_control` + `behavior_program` | 需要把具体动作空间接到 P6 |
| Micro Reward | Cities 2026 | 个体状态与动作链条验证 | `simulation_validation_target.metric_family=state_behavior_consistency/llm_draft_consistency_review/manual_review` | 需要业务人员可读复核面板 |
| Macro Reward | Cities 2026 | 宏观统计一致性 | `simulation_validation_target.metric_family=ssim/kl_divergence/dtw_r2/correlation/peak_shift` | 缺真实时段客流、手机/闸机/现场数据 |
| SARIMA 一致性 | Cities 2026 | 周期/时序验证 | `simulation_validation_target.metric_family=sarima_consistency` | 真实时序数据未闭合 |
| SSIM | Cities 2026 | 曲线/分布形态相似性 | `simulation_validation_target.metric_family=ssim` | 需要基准序列或热力图 |
| KL Divergence | Cities 2026 | 分布差异 | `simulation_validation_target.metric_family=kl_divergence` | 需要真实分布 |
| DTW-R2 | Cities 2026 | 时间序列错位相似 | `simulation_validation_target.metric_family=dtw_r2` | 需要真实序列 |
| Huff / Gravity | GIS/商业选址方法 | 吸引力、距离衰减、供给承接 | `choice_probability.method_family=huff/gravity`；`factor_inputs.distance_decay/poi_supply_capacity` | 需要候选供给容量与距离口径 |
| Logit / Discrete Choice | 选择模型 | 消费选择概率 | `choice_probability.method_family=logit` | 缺真实选择/转化数据，先 draft |
| POI/TGI 缺口 | 同事 POI/TGI 与本地数据 | 需求权重、供给差、建议依据 | `choice_probability.method_family=poi_tgi_gap` | 需要接入到节点解释和 P6 |
| Social Force / RVO | 行人仿真经典方法 | 拥挤、避障、密度 | 作为后续空间运动引擎候选 | 当前缺几何/路网，不装作已实现 |
| MATSim / SUMO / AnyLogic | 成熟仿真产品/引擎 | 活动链、行人路径、服务点容量 | 作为后续接口和验证参考 | 当前不整套引入，避免复杂度失控 |
| LLM-ABM 批判综述 | 外部论文 | 风险门禁 | DeepSeek 只可输出候选，必须 schema + review | 继续防止 LLM 批量编故事 |
| 因果推断批判 | 外部论文 | 禁止把相关性写成因果 | `choice_probability` 必须保留 `source_refs` 和 `missing_inputs` | 后续报告要明确“待复核/非因果” |

## 2. 用户自由度落地规则

所有仿真对象必须满足：

- 有稳定 ID。
- 有用户可读名称。
- 有来源引用。
- 有 `missing_inputs`。
- 有 `adoption_state` 或等价状态。
- 有 `user_locked`。
- DeepSeek 只允许草拟、解释、提缺口、润色，不允许自动确认、删除或覆盖用户锁定内容。

当前已经被纳入控制对象的类型：

- `source_material`
- `persona_state`
- `behavior_program`
- `choice_probability`
- `time_scenario`
- `spatial_node`
- `supply_facility`
- `calibration_target`
- `simulation_validation_target`
- `operation_plan`

## 3. 当前仍未落地的硬缺口

这些不是文字缺口，而是后续必须进入代码或页面的对象：

1. P6 页面里的“人群与行为程序”工作区。
2. P6 页面里的“选择概率/供需触发”解释区。
3. P6 页面里的“验证目标与真实数据缺口”区。
4. DeepSeek 的 `choice_probability` 任务 adapter。
5. DeepSeek 的 `simulation_validation_target` 任务 adapter。
6. 至少一个真实资料包回放：资料 -> 人群状态 -> 行为程序 -> 选择概率 -> 节点建议 -> 报告。
7. 把同事 POI/TGI 结果接成因素，不覆盖本地用户自由和证据门禁。

## 4. 禁止继续出现的误用

- 不说“完整人物仿真已完成”。
- 不把 DeepSeek 输出写成 checked。
- 不把 P4 旧分数当最终排序。
- 不把 85% / 90% 等论文或商业文章指标写成本项目承诺。
- 不把相关性、TGI、POI 缺口写成因果。
- 不把静态地图或 Selenium 页面点击当作仿真准确性验证。
- 不把“模仿人类操作测试”误解成方法层“像不像人”。
- 不把老板资料只当参考文献；每个可用方法必须进入对象、字段、门禁或后续任务。
