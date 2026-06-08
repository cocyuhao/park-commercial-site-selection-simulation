# 证据驱动方向复位（2026-06-05）

> 目的：回应“学习了但没用、又在旧版本上打补丁、方向可能跑偏”的纠正。  
> 状态：主线复位文件，不是完成报告。后续每个大改动都应先对照本文，说明采用了哪条证据、拒绝了哪条旧惯性、落成了哪个对象或验证。

## 0. 当前判断

刚才的浏览器验证和对象池修补只属于“窄验证收束”，不能被当成主线推进。

真正主线应该从“修旧 P6 页面”切回“AI 驱动仿真决策系统”：

1. 先根据老板六份资料、Flowus 三页、2026 AI/agent/HCI 文献和仓库旧产物做方向复位。
2. 再判断哪些旧功能保留、哪些冻结、哪些重构。
3. 再实施一个小而真实的落地点。
4. 每个落地点必须有浏览器/API/schema/文档证据，不允许只靠口头判断。

## 1. 已核实的学习证据

### 1.1 Flowus 三页

本轮已用真实 Chrome DevTools 打开三条用户给出的 Flowus 页面，并保存快照和截图：

| 页面 | 本地证据 | 对本项目的有效启发 | 禁止照搬 |
|---|---|---|---|
| 零代码开发，给 App 注入灵魂（下） | `10_research/flowus_design_learning_20260605/flowus_153eefbc_snapshot.txt`，`flowus_153eefbc_screenshot.png` | 先 PRD / 信息架构，再做视觉和实现；原型可以先于代码，动效服务于交互反馈 | 不照搬移动端小白教程口吻，不直接套 Pencil/Cursor 流程 |
| 让网站告别 AI 味 | `flowus_6616d9c9_snapshot.txt`，`flowus_6616d9c9_screenshot.png` | 高级感来自真实参考、视觉质感、微动效和清晰构图；去 AI 味不是换几个词 | 不把背景视频、液态玻璃、营销 Hero 搬进决策系统 |
| 零代码开发，给 App 注入灵魂（上） | `flowus_780bf704_snapshot.txt`，`flowus_780bf704_screenshot.png` | 先定义目标用户、核心感受、视觉隐喻、反目标，再让 AI 实现；“不要让 AI 包揽一切决定” | 不把“像不像人”误解成方法标准；它说的是产品体验和设计流程 |

对本项目的强制转化：

- 任何 UI 大改前必须先定义：目标用户、工作流、对象、反目标。
- 不再先堆页面，再补逻辑。
- 视觉高级感必须来自“可信业务对象 + 清晰动作 + 稳定反馈”，不是装饰。
- 动效只用于加载、采用、放弃、锁定、展开、报告生成、仿真进度这些状态变化。

### 1.2 老板六份方法资料

本地抽取已确认六份资料完整进入项目资料池：

| source_id | 类型 | 标题/来源 | 抽取状态 |
|---|---|---|---|
| BOSS-METHOD-001 | 长图 | 合成用户/市场研究案例 | 已切片，需人工视觉复核 |
| BOSS-METHOD-002 | PDF | Modeling Others' Minds as Code | 31 页，约 100675 字 |
| BOSS-METHOD-003 | PDF | HumanLM: Simulating Users with State Alignment Beats Response Imitation | 27 页，约 84807 字 |
| BOSS-METHOD-004 | PDF | GameLook 合成玩家案例 | 7 页，约 5806 字 |
| BOSS-METHOD-005 | DOCX | 人工智能模拟实验论文 | 46 段，约 1129 字 |
| BOSS-METHOD-006 | DOCX | 已转换 - main-1 | 312 段，5 表，约 82024 字 |

对本项目的强制转化：

- HumanLM：先建 `persona_state`，不要只给“亲子/白领/老人”薄标签。
- ROTE：先建 `behavior_program`，让行为成为可编辑、可复核程序，不让 LLM 临场编故事。
- RL + LLM 社区仿真：当前只能做结构化 dry-run；没有真实几何、客流、转化、成本、授权，不得说完整仿真。
- DLR/FLR/SSR：裸分数要降级，先输出动机、担忧、放弃条件、依据和具体建议，再映射为推进优先级。
- 真实验证：Selenium 只能证明产品可用，不能证明仿真准确。

### 1.3 2026 外部资料

昨天已有 OpenAlex 原始检索结果：`10_research/ai_design_2026_openalex_raw_20260604.json`，共 47 条。  
Semantic Scholar 和 arXiv 本地原始结果出现 429 / timeout，不能当完整学习，只能标记为待补。

当前可用的高相关 2026 条目包括：

| 方向 | 条目 | DOI | 本项目采用点 |
|---|---|---|---|
| 多步 agent 检查点 | When Should Users Check? Modeling Confirmation Frequency in Multi-Step Agentic AI Tasks | https://doi.org/10.1145/3772318.3790655 | 资料解析、仿真、报告生成不能一键到底；高风险动作要中间检查 |
| 交互式解释 | Co-Explainers: A Position on Interactive XAI for Human-AI Collaboration as a Harm-Mitigation Infrastructure | https://doi.org/10.3390/make8030069 | 解释应成为对象级基础设施，不是报告末尾一段 AI 文 |
| AI 辅助决策 | How AI-Assisted Decision-Making Paradigms and Explainability Shape Human-AI Collaboration | https://doi.org/10.3390/su18073516 | 用户应能评估、反驳、采用或放弃 AI 建议 |
| 多 agent 可视分析 | SCSimulator: An Exploratory Visual Analytics Framework... | https://doi.org/10.1145/3742413.3789061 | 仿真不是文本建议，必须有输入对象、约束、对照、可视分析 |
| 工业实时决策支持 | Hybrid AI and LLM-Enabled Agent-Based Real-Time Decision Support Architecture... | https://doi.org/10.3390/ai7020051 | LLM 和本地模型分层；DeepSeek 只做候选和解释，不做最终判断 |
| 可复用 agent workflow | ReUseIt: Synthesizing Reusable AI Agent Workflows for Web Automation | https://doi.org/10.1145/3742413.3789083 | 工作流应沉淀为对象和状态，不靠一次性聊天记忆 |

本轮限制：

- 上述外部资料当前主要来自本地 OpenAlex 结果和已有研究文件。
- 后续若要引用某篇作为强依据，需要用官方/出版页面或 PDF 再逐篇打开核验。
- 不得把检索结果列表当作“已深读论文”。

## 2. 旧方向与新方向的冲突

| 旧惯性 | 为什么不够 | 新方向 |
|---|---|---|
| 修 P6 页面、补按钮、补文案 | 容易继续旧壳子，忽略系统主线变化 | 先重建对象链：资料 -> 人群状态 -> 行为程序 -> 选择概率 -> 验证目标 -> 仿真任务 -> 报告 |
| 节点打分 | 用户看不懂，且容易伪精确 | 主视觉改成推进优先级、依据、具体建议、待补资料 |
| AI 工作台只是聊天框 | 无项目/历史/范围/对象引用，容易孤立 | 变成项目沟通与报告工作台，能引用对象、生成报告、记录历史 |
| 地图只是静态图或 POI 展示 | 不等于空间仿真，也不满足自由地图要求 | 地图层先保证真实交互和不拖垮工作台；仿真层等 P3 几何闭合 |
| 门禁只看脚本是否通过 | 老门禁可能证明的是旧标准 | 门禁要区分产品可用性、方法落地、仿真准确性、证据可信度 |
| DeepSeek 做大脑 | DeepSeek 便宜但不稳，不适合最终判断和逐游客调用 | DeepSeek 做行为程序候选、资料整理、报告草稿；本地 Python 做模型和复核 |

## 3. 保留 / 冻结 / 重做矩阵

### 3.1 保留

- 资料抽取、证据台账、PDF 表格验证、DeepSeek API 健康验证。
- 已有 `persona_state`、`behavior_program`、`choice_probability`、`simulation_validation_target` 相关 CSV/schema 草稿。
- P6 工作台作为“可运行产品壳”，但不能作为最终方向本身。
- 浏览器/Playwright/Selenium 证据链，但只作为产品可用性验证。

### 3.2 冻结

- 继续围绕旧 P6 视觉做零散修补。
- 继续扩写旧节点分数逻辑。
- 继续把“门禁通过”理解成“仿真可信”。
- 继续让 AI 工作台输出无对象引用、无证据边界的长篇建议。

### 3.3 重做

- 全局首页 / 项目总览：从页面模块改成“全局推进台”。
- AI 工作台：从聊天框改成“项目沟通、对象引用、报告生成、历史归档”。
- 资料池：从文件列表改成“资料对象池”，显示资料影响哪些人群状态、行为程序、选择概率和验证目标。
- 节点页：从节点列表和分数改成“节点推进对象”，显示建议、依据、反例、补证动作。
- 仿真入口：从 dry-run 表格改成“输入对象选择 -> 预检 -> 运行 -> 校准目标 -> 复核”。

## 4. 下一步主线落地点

不建议马上继续大改 CSS，也不建议立刻上地图底层。

最符合当前证据的落地点是：

> 做一个“全局对象链路复位”：把资料、方法、人群状态、行为程序、选择概率、验证目标、节点、AI 会话、报告放进同一套可读状态矩阵，并在页面上只展示这个矩阵的业务动作，不再展示后端测试语言。

原因：

- 它直接吸收 Flowus 的“先定产品灵魂和信息架构”。
- 它直接吸收老板资料的“状态 -> 行为 -> 选择 -> 验证”。
- 它能防止继续修旧页面。
- 它不会和同事地图底层冲突。
- 它能把 DeepSeek 的角色、门禁、对象池和报告生成串起来。

最小可落地范围：

1. 新增/更新一个对象链路 API 或本地聚合函数，输出每类对象的数量、状态、缺口和下一步动作。
2. 页面第一屏把“全局推进台”作为主入口，显示链路状态而不是旧项目总览死文案。
3. 资料池和 AI 工作台只先引用链路对象，不马上重写全部样式。
4. 增加一个验证脚本：检查链路对象是否来自真实文件、是否没有 final/checked 越权、是否用户可见文案无后端词。

## 5. 当前未完成事项

- Flowus 三页已经真实打开并保存，但尚未转成设计 token / 信息架构草图。
- OpenAlex 2026 已有本地候选，但还需逐篇核验高相关论文。
- 旧产物信任审计已有第一版，但还没有和新 UI 每个入口绑定。
- 当前浏览器对象池验证还未复跑通过；刚才已确认 502 是 `httpx trust_env=True` 假阴性，后续仍需完成真实页面 QA。
- `persona_state` / `behavior_program` 已进入对象池 API/UI 的窄落地，但还未形成完整仿真任务输入选择。

## 6. 执行规则

后续每一步必须写清：

1. 引用了哪条本地/外部证据。
2. 拒绝了哪条旧惯性。
3. 改了哪个对象或链路。
4. 用什么验证证明它不是空想。
5. 哪些内容仍是 draft / needs_review。

