# 先进 AI 仿真与工作台学习吸收台账（2026-06-04）

> 状态：纠偏后的“学习外化”台账。  
> 目的：防止已学习内容在长对话、压缩上下文或新 agent 接手时丢失；也防止把旧公式、旧页面和旧门禁重新包装成“先进系统”。  
> 总判断：本项目不应停留在“公园商业选址页面 + AI 对话框 + 节点分数”。它应升级为“AI 驱动仿真决策系统”：人和 agent 都围绕同一组对象、状态、能力、证据、复核点和报告链路协作。

## 0. 为什么上一版还不够先进

上一版重基线已经做对了几件事：全局定位、对象池、裸分数降级、Flowus 资料证据化、2026 文献初筛、浏览器验证和总门禁。

但它仍有三个不足：

1. 先进性表达不够。
   - 仍容易被理解成“把旧 P6 页面修好”，而不是从根上升级为 agentic capability system。

2. 学习内容散落。
   - 老板资料、Flowus、豆包/Codex 参考、2026 论文、用户纠偏和代码落地分散在很多文件里，新对话很容易只读到其中一小块。

3. 旧东西降级还不彻底。
   - Huff / Logit / Gravity / Social Force / 门禁 / 报告草稿这些旧能力可以保留，但必须明确只是因子、验证层或历史资产，不再做系统叙事中心。

因此本文件进一步把先进资料转成工程要求。后续不能只说“参考了论文”，必须落成对象、状态机、能力接口、UI 交互、验证指标或禁用边界。

## 1. 先进方向的总升级

旧方向：

- 上传资料。
- 展示节点。
- 给节点打分。
- 地图可看。
- AI 可以聊。
- 最后生成报告。

新方向：

- 资料进入对象池，决定哪些状态、行为、空间、供给、校准目标被激活。
- AI 不是一个问答框，而是项目、节点、资料、仿真任务和报告之间的协作层。
- 页面不是给人“看结果”，而是让人审查、采用、放弃、锁定、回退和复核对象。
- agent 不能绕开用户；多步任务必须设置检查点，错误和不确定性要停在对象层，不要扩散到报告。
- 仿真不是一次 dry-run，而是可复跑的对象链：人群状态 -> 行为程序 -> 空间路径 -> 选择概率 -> 校准目标 -> 对照指标 -> 工作报告。
- UI 要同时人类可读和 agent 可读：每个对象有 ID、来源、状态、动作、危险级别和复核点，便于 Selenium/Browser/agent 做真实使用验证。

## 2. 2026 优先资料如何进入系统

| 资料/方向 | 为什么先进 | 本项目吸收方式 | 禁止误用 |
|---|---|---|---|
| Agentic information systems, 2026 | 把系统从被动工具升级为可行动、可委托、可协同的 agentic IS | UI 不再只是页面；每个对象要有可调用动作、状态、记忆、复核和责任边界 | 不把“加个 AI 聊天框”当 agentic system |
| Agentic AI as a new frontier in IS, 2026 | 强调 promise/peril/research opportunities，适合作为系统治理边界 | 建立权限、动作后果、对象锁定、审计轨迹和人机责任迁移 | 不让 AI 直接做最终商业判断 |
| When Should Users Check?, CHI 2026 | 多步 agent 任务不能只在最后确认，检查频率要和风险/成本相关 | 资料解析、仿真运行、报告生成要有中间检查点；高风险动作必须确认 | 不让“生成报告/跑仿真”一键到底 |
| When Should AI Step Aside?, 2026 | 不同用户介入节奏不同，系统应支持短暂接管、持续监控和手动修正 | AI 工作台支持新对话、范围切换、用户改写、采用/放弃、锁定对象 | 不把用户当只会点确认的小白 |
| Dark Patterns Meet GUI Agents, CHI 2026 | GUI agent 易受操纵界面影响，人类监督很重要 | 删除、覆盖、采用、锁定、报告发布等动作要避免诱导式按钮和隐藏后果 | 不做“看起来自动很聪明”的假自动化 |
| LLM dark patterns / co-creativity dark patterns, 2026 | AI 可能出现迎合、锚定、循环、语气压制等交互偏差 | AI 输出必须保留“可反驳、待复核、用户可不同意”的结构 | 不让 AI 用权威口吻压用户判断 |
| Just Do It!? Computer-use agents blind goal-directedness, ICLR 2026 | computer-use agents 可能盲目追目标而忽略上下文风险 | Browser/Selenium 智能体测试要检查“是否该停手”，不是只检查能不能点完 | 不让 agent 自动删除、覆盖、提交或推送 |
| SCSimulator, IUI 2026 | LLM-driven MAS + visual analytics 用于复杂决策，不是纯文本结论 | 仿真任务要有可视分析对象：输入、约束、候选、冲突、对照、解释 | 不把“AI 写了一段建议”当仿真可视分析 |
| RESPOND, AAAI 2026 | LLM agents 与高保真外部模型耦合，适合灾害/人群响应模拟 | 本项目应耦合 GIS/路径/客流/运营约束；LLM 只是行为与解释层 | 不让 LLM 单独生成空间/客流真实性 |
| MCP-SIM, npj AI 2026 | 自纠错多 agent 仿真把欠规范提示转为验证过的仿真和解释 | 后续仿真任务应有 generator / validator / explainer / reviewer 分层 | 不把多 agent 循环当作天然正确 |
| PhysCodeBench / self-corrective simulation, 2026 | 自纠错必须配合领域验证，不是 agent 互相聊天 | 对地图、路线、选择概率、校准指标设置领域校验器 | 不让 agent 自夸“已修复” |
| ScaleSim, 2026 | 大规模多 agent 仿真会遇到内存和调度问题 | 后续做大规模人物仿真时先做抽样、分层、缓存和可复跑批次 | 不追求“1000 个 agent”表面规模 |
| Applications of human-machine collaborative decision-making, 2026 | 先进决策系统要处理角色配置、交互讨论、信任解释、权责迁移 | AI 工作台要清楚显示当前由谁判断、谁确认、谁负责下一步 | 不把 AI 结论伪装成组织决策 |
| AI shared decision-making systematic review, 2026 | 决策支持不只透明，而要给用户能评估的理由和价值对齐依据 | 报告用“为什么现在适合/不适合推进、谁受影响、缺什么证据” | 不只给技术解释或模型字段 |
| Co-Explainers, 2026 | 解释是协作基础设施，不是报告末尾附注 | 节点、资料、仿真任务和报告都要有可展开解释对象 | 不把解释做成一大段 AI 味说明 |
| ToolSmith / enterprise tool creation, AAAI 2026 | 工具生成要有 API spec、自然语言测试、安全沙箱和闭环验证 | 本项目新增工具/API 时同步生成测试、沙箱样例和门禁，不直接让 LLM 写接口 | 不把 DeepSeek 生成代码直接并入 |
| LightAgent / production trace, 2026 | 新框架重视记忆、MCP/skill、trace observability | 可借鉴 trace 思想：每次 AI/仿真任务保存输入对象、工具调用、错误和输出摘要 | 不因框架新就替换本项目主栈 |

## 3. 应升级出的系统能力

### 3.1 对象能力层，而不是页面功能堆叠

每个重要元素都必须成为对象：

- `project_scope`
- `source_material`
- `method_object`
- `persona_state`
- `behavior_program`
- `choice_probability`
- `spatial_node`
- `poi_context`
- `simulation_task`
- `validation_target`
- `ai_session`
- `report_draft`
- `legacy_artifact`

每个对象至少有：

- 稳定 ID。
- 来源。
- 当前状态。
- 可执行动作。
- 用户采用状态。
- 锁定状态。
- 风险级别。
- 缺失输入。
- 复核责任。

### 3.2 agent 可读 UI

页面不能只给人看，也要给测试 agent 和未来自动化读。

要求：

- 关键卡片有稳定 `data-object-id`。
- 关键动作有稳定 `data-action`。
- 状态不靠颜色单独表达。
- 旧内部状态映射为用户文案，但 DOM / API 保留结构化状态供测试读取。
- Selenium/Browser 测试应验证：状态变化、动作后果、锁定规则、报告生成限制、错误不清空。

### 3.3 检查点调度

所有长链任务要分阶段，不再一键到底：

- 资料导入：上传 -> 解析 -> 关联对象 -> 用户采用。
- AI 分析：选择范围 -> 给出理解 -> 发现缺口 -> 用户确认 -> 生成报告。
- 仿真任务：选择输入对象 -> 预检 -> 运行 -> 指标对照 -> 人工复核。
- 报告生成：会话充分性 -> 报告类型 -> 草稿 -> 依据/缺口复核 -> 下载。

### 3.4 多 agent 是角色分层，不是数量堆叠

后续若引入多 agent，只允许按角色分层：

- planner：拆任务和识别风险。
- extractor：抽取资料。
- simulator：调用本地模型。
- validator：查 schema、证据和指标。
- explainer：写业务解释。
- reviewer：指出不可信和缺口。

这些角色应通过对象和 schema 交换信息，不通过大段聊天互相传话。

### 3.5 解释升级为“可反驳理由”

报告和节点解释不能只是“模型认为”。

必须给：

- 当前能确认什么。
- 用了哪些资料。
- 哪些只是候选。
- 哪些判断不能做。
- 反例是什么。
- 用户下一步能怎么改变判断。

## 4. 旧东西如何降级

| 旧东西 | 保留价值 | 新位置 | 不能再做什么 |
|---|---|---|---|
| Huff / Gravity | 距离衰减、吸引力解释 | `choice_probability.factor_inputs` | 不能单独输出最终选址 |
| Logit | 选择概率框架 | `choice_probability.method_family` | 没真实选择数据时不能给真概率 |
| Social Force / RVO | 拥挤和移动启发 | 后续空间运动候选 | 不能替代真实地图路径 |
| 旧门禁 | 内部质量检查 | `verify_project_implementation.py` | 不能作为用户界面语言 |
| 旧节点分数 | 历史排序痕迹 | legacy internal / 折叠依据 | 不能作为主视觉或最终排名 |
| 旧 DeepSeek 输出 | 历史草稿 | metadata-only envelope | 不能直接进入 checked 证据 |
| 静态地图截图 | 兜底可见性 | 地图降级 fallback | 不能当自由地图或真实仿真 |
| 10 轮 Selenium | 可用性证据 | 浏览器 QA | 不能证明仿真准确 |

## 5. 当前已经落地的先进性

- 对象池 API/UI 已把 `choice_probability` 和 `simulation_validation_target` 从 CSV 变成可新增、编辑、采用、放弃、锁定、删除的用户可控对象。
- 节点主视觉已从裸分数转成推进优先级、依据和具体建议。
- 全局推进台已从旧项目总览改成系统链路状态。
- Flowus 资料已真实打开，进入产品调性和信息架构约束。
- 2026 资料已进入全局重基线和门禁，不再停留在聊天里。
- 启动脚本已防止新对话回到旧 P6 对象池口径。

## 6. 当前还不够先进的地方

这些必须承认，没有完成就不能说“完全先进”：

1. AI 工作台还没有完成 agentic workflow 重构。
   - 还需要项目/节点范围、历史、新对话、检查点、报告生成、用户反驳和对象引用。

2. 资料池和方法对象池还没有完全统一。
   - 资料影响了哪些 persona、behavior、choice、validation 还不够清楚。

3. 仿真任务入口还不成熟。
   - 需要输入对象选择、预检、校准目标、运行状态、失败原因和复核结果。

4. 旧产物信任地图仍需全仓库化。
   - 目前已有 rebaseline audit，但用户担心的是整个长历史目录，需要更完整的“信任分级 + 替换计划”。

5. 多 agent 还没进入生产链路。
   - 当前应先做严格对象/schema/validator；不要为了先进而先堆 agent。

## 7. 下一步落地顺序

1. 把本文件纳入总门禁和交接文件。
2. 继续重构 AI 工作台：范围、历史、新对话、检查点、生成报告、对象引用。
3. 重构资料池/方法对象池：采用、放弃、锁定、关联对象、解析说明。
4. 新增仿真任务入口：输入对象、校准目标、预检、运行、复核。
5. 建立旧产物信任地图：全仓库扫描旧完成声明、旧 P4、旧 ROI、旧最终推荐、旧裸分数、旧端口和旧 UI 口径。
6. 后续再考虑多 agent runtime；前提是对象、schema、验证和人类检查点已稳定。

## 8. 本轮参考证据

- Flowus 资料抽取：`40_quality_evidence/flowus_ai_design_probe_20260604/flowus_probe_report.json`
- OpenAlex 2026 检索：`10_research/ai_design_2026_openalex_raw_20260604.json`
- Semantic Scholar 2026 检索：`10_research/ai_design_2026_semantic_scholar_raw_20260604.json`
- 全局重基线：`10_research/global_ai_simulation_design_rebaseline_20260604.md`
- Springer: Agentic information systems, DOI `10.1007/s12525-025-00861-0`
- CHI 2026: When Should Users Check?
- CHI 2026: Dark Patterns Meet GUI Agents
- arXiv/IUI 2026: SCSimulator
- npj AI 2026: MCP-SIM
- AAAI 2026: RESPOND
- IBM Research 2026: ToolSmith
