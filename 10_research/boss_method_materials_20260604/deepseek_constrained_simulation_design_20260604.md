# DeepSeek 强约束仿真接入设计（2026-06-04）

## 结论

DeepSeek 适合接入，但不能作为逐个游客的实时仿真引擎。正确位置是“行为程序编译器”和“结果解释器”：

1. DeepSeek 根据资料、画像、触发条件和节点上下文生成结构化行为程序草稿。
2. 本地 Python 把行为程序编译成概率参数、约束和缺口清单。
3. 大规模仿真由本地 Monte Carlo / ABM / 路径模型执行。
4. DeepSeek 再把本地结果解释成业务语言，但所有输出保持 `needs_review`。

这样做能利用 DeepSeek 的低成本和语言理解能力，同时避免把模型幻觉变成真实商业结论。

## 为什么不能“每个游客问一次 DeepSeek”

- 成本会随游客数线性爆炸，便宜也会变贵。
- 同一个场景多次调用会产生不稳定输出，不利于复跑。
- LLM 对数字、概率、路径和供需平衡的长期一致性不可靠。
- 老板资料中 HumanLM 与高精度社区仿真都强调“状态对齐”和“真实数据校准”，而不是让模型自由编故事。
- 长图材料里的千人模拟和市场研究案例也强调：合成用户必须有真实样本、记忆、校准和外部验证。

## 推荐架构

### Layer 1：证据与状态层

输入：

- `p2_persona_parameter_prototype.csv`
- `p2_demand_trigger_matrix.csv`
- `p2_input_gap_register.csv`
- `p3_calibration_gate_status.csv`
- `evidence_ledger.csv`
- 老板六份方法资料的本地提取结果

输出：

- 人群状态画像
- 行为触发程序
- 验证目标
- 不能仿真的阻塞项

### Layer 2：DeepSeek 行为程序编译层

新增任务路由：

- `LLM-027`
- 名称：P2/P4 persona behavior program compiler
- 风险：medium
- 默认执行：DeepSeek
- 输出：`needs_review`
- 门禁：`persona_behavior_program_review`

DeepSeek 只允许输出严格 JSON，不允许输出 checked、final、ROI、收益预测、最终排序。

### Layer 3：本地仿真层

本地负责：

- 随机种子
- 人群权重抽样
- 时间段抽样
- 路径/距离/排队/天气/供给容量约束
- 放弃、外溢、替代选择
- 敏感性分析
- 结果日志与复跑

### Layer 4：业务解释层

DeepSeek 可以把本地结果解释成：

- 当前可以判断什么
- 现在不能判断什么
- 哪些资料会改变判断
- 下一步该补什么
- 节点优先级为什么是“优先/待补/暂缓”

但解释仍然只能是草稿。

## 强约束

- 所有 DeepSeek 输出必须含 `output_status=needs_review`。
- 所有 DeepSeek 输出必须含 `executor=deepseek` 和 `llm_task_id`。
- 任何真实结论必须能追溯到证据文件。
- 如果 `geometry / visitor_flow / conversion_rate / revenue_cost / operation_authorization` 任一阻塞，系统只能做框架预演和待补建议。
- 禁止 DeepSeek 直接生成最终商业推荐、最终排名、收益预测或 ROI。
- 禁止把 PPT 内容当强证据，只学习表达角度和报告结构。
- 禁止逐游客调用 DeepSeek；应按“人群 × 场景 × 节点 × 时间段”批量生成可缓存行为程序。

## 落地顺序

1. 先落静态状态画像、行为程序、验证目标。
2. 再接 DeepSeek JSON 编译脚本。
3. 再让 dashboard 展示人群仿真工作台。
4. 再把节点“分数”改成人类可读的优先级、依据和建议。
5. 最后做本地大规模 Monte Carlo 与 Selenium/浏览器验证。

