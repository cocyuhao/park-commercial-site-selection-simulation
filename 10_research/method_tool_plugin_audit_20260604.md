# 方法 / 工具 / 插件 / 论文使用审计清单（2026-06-04）

> 状态：主线审计资产。  
> 目的：回应“你是不是把先进性一句话带过、是不是还在用老东西”的纠偏。  
> 结论：后续不能只写“已学习/已参考/已使用插件”。每个工具、论文、插件、框架和同事成果都必须说明：为什么用、先进性是否足够、落到本项目哪里、风险是什么、下一步如何验证。

## 1. 审计规则

每个条目按六个问题判断：

1. 真实性：是否来自本地文件、官方文档、论文、GitHub 或可复跑验证。
2. 先进性：是否符合 2025-2026 的 AI agent / LLM simulation / human oversight / observability 方向。
3. 适配性：是否服务“人物仿真优先，供需缺口辅助”的主线。
4. 落地性：是否进入 schema、adapter、UI 对象、API、验证脚本、报告或交接。
5. 风险：是否会让旧分数、旧 P4、LLM 幻觉、插件堆叠或假自动化污染系统。
6. 决策：采用、选择性吸收、降级为因子、暂缓、拒用。

## 2. 当前采用的高级验证与可观察性工具

| 条目 | 来源 | 当前判断 | 本项目落点 | 风险/限制 | 决策 |
|---|---|---|---|---|---|
| Playwright 1.60 trace | 官方文档；本地 `playwright --version` | 比旧 Selenium smoke test 更适合复查浏览器轨迹、DOM 快照、截图、网络和控制台 | `90_p6_expert_dashboard/qa/advanced_agentic_workflow_validation_20260604.py`、`advanced_agentic_workflow_trace_20260604.zip`、`advanced_gate` | trace 不能替代业务逻辑校准；后续要按任务补断言 | 采用 |
| Playwright ARIA snapshot | 官方文档；本地 ARIA yml | 适合检查 agent 可读 UI 和可访问语义，不只看截图 | `advanced_agentic_workflow_aria_overview_20260604.yml`、`missing_hook_count=0` 门禁 | ARIA 结构不能证明视觉舒适，仍需截图和人眼检查 | 采用 |
| OpenTelemetry SDK / GenAI 语义 | 官方 GenAI semantic conventions；本地 SDK 可导入 | 用于后续 AI/仿真链路 trace：模型、工具、数据源、错误、span | `requirements.txt`、`advanced_ai_validation_rebaseline_20260604.md`、`advanced_gate` 工具版本检查 | 目前只安装和门禁登记，还未给 DeepSeek/API/仿真任务打 span | 采用但待实装 |
| Selenium 4.44 | 本地已安装；历史 10 轮测试 | 不算过时，但只能作为兼容/回归/反复点击，不再作为高级可用性证明 | 旧 Selenium 证据、对象池 browser validation、历史严格 10 轮 | Selenium-only 会漏掉 trace、ARIA、agent 可读性和逻辑风险 | 保留兼容，降级 |
| Chrome / Browser / Chrome DevTools | 本地 Chrome、插件能力 | 适合人眼、真实浏览器、console 和性能问题复核 | 高级 QA 使用系统 Chrome；后续重大 UI 必须看真实页面 | 不能把插件能力伪装成网站功能 | 采用 |

## 3. 当前采用的仿真与数据工程工具

| 条目 | 来源 | 当前判断 | 本项目落点 | 风险/限制 | 决策 |
|---|---|---|---|---|---|
| DuckDB / Polars | 现代数据栈验证 | 适合大表、衍生场景、批量对象加工，比临时 CSV 手工拼接更稳 | `verify_modern_sim_stack.py`、`modern_sim_stack_verification_20260604.json/md` | 还没有完全替代旧 CSV 管线 | 采用，后续 adapter 优先用 |
| jsonschema / Pydantic | 本地 schema 验证 | 适合约束 DeepSeek 输出和用户可控对象 | `choice_probability.schema.json`、`simulation_validation_target.schema.json`、`validate_deepseek_contract_output.py` | schema 只能管字段，不管真实世界是否正确 | 采用 |
| SimPy | 本地验证 | 适合服务、排队、补货、营业时间、等待时间等过程仿真 | 现代栈已安装；后续用于饮水机/售卖机/轻餐服务过程 | 还未接入 UI 任务入口 | 采用但待实装 |
| SALib / Optuna | 本地验证 | 适合敏感性分析、参数搜索、校准候选；能帮助识别哪些数据最影响判断 | 现代栈已安装；后续用于选择概率、供需和排队参数校准 | 不能在无真实目标函数时假装最优 | 采用但待实装 |
| Mesa / Mesa-Geo | 本地验证 | 适合 agent-based prototype 和空间 agent 框架 | 现代栈已安装；后续用于人物仿真原型 | 不要为了框架先进而重写全部本地系统 | 选择性采用 |
| OSMnx / MovingPandas / GeoPandas / Shapely / NetworkX | 本地验证 | 适合路网、轨迹、空间约束、边界和路径分析 | 现代栈已安装；既有 GIS 文件和地图逻辑可继续接入 | 高德 GCJ-02 与 OSM WGS84 坐标必须隔离记录 | 采用 |

## 4. LLM 与 agent 方法边界

| 条目 | 来源 | 当前判断 | 本项目落点 | 风险/限制 | 决策 |
|---|---|---|---|---|---|
| DeepSeek API | 本地路由、契约、历史调用 | 便宜，适合批量语义工人；不够稳，不做总设计师 | `deepseek_task_contract.schema.json`、`validate_deepseek_contract_output.py`、legacy envelope、`draft/needs_review` 规则 | 可能迎合、编造、漏证据；不得写 checked/final/ROI/最终推荐 | 受限采用 |
| 多 agent | 2026 agentic / simulation 资料 | 只按角色分层：planner/extractor/simulator/validator/explainer/reviewer | `advanced_ai_learning_absorption_register_20260604.md` | 不允许多开几个 LLM 聊天就宣称先进 | 暂缓 runtime，先做对象/schema |
| AgentSociety / AgentSociety2 | GitHub；LLM-native agent simulation platform | 对“城市环境 + LLM agents + replay + MCP + reasoning patterns”有启发 | 进入方法审计，作为后续 agent runtime 候选 | 体量大，直接接入会压过当前系统；需等对象和校准稳定 | 选择性吸收 |
| MobiVerse | arXiv 2025 | “轻量领域生成器 + LLM 上下文修正”非常贴合本项目，优先级高 | 支撑“先规则/数据生成基础行为链，再让 LLM 修正解释”的主线 | 不能把论文标题当完成；必须落到 adapter 和任务入口 | 采用为架构原则 |
| CAMS | arXiv 2025 | 强调个体移动模式与群体分布约束，贴合提高人物仿真准确性 | 支撑 persona/profile + collective constraints + trajectory alignment | 当前缺真实轨迹/客流对齐数据，不能声称达到论文效果 | 采用为方法方向 |
| AI Metropolis | MLSys 2025 | 解决 LLM 多 agent 调度和假依赖；适合规模扩大后降低成本 | 作为后续并行调度参考 | 当前还没到数万 agent，不先引入复杂调度 | 暂缓 |

## 5. 供需缺口与同事成果审计

| 条目 | 来源 | 当前判断 | 本项目落点 | 风险/限制 | 决策 |
|---|---|---|---|---|---|
| Hiromitsu1207/POI_TGI_Calculator | GitHub；2 commits，0 stars；README | 有用点：POI/TGI 供需缺口、外溢、运营/空间建议、PDF 指标解析、规则兜底 | `poi_tgi_calculator_selective_absorption_20260604.md`、供需缺口辅助层 | 同事方向把 TouristAgent/TGI/缺口放得过重；不能替代人物状态、路线、消费、时间和校准 | 选择性吸收 |
| POI/TGI 缺口 | 同事仓库与本项目现有 POI/TGI | 只能作为“供给/需求辅助层”，不是主线仿真结论 | `choice_probability.factor_inputs`、`poi_context`、报告缺口段 | 不得直接输出最终选址或收益 | 降级为辅助 |

## 6. UI / 产品 / 设计插件审计

| 条目 | 当前判断 | 本项目落点 | 风险/限制 | 决策 |
|---|---|---|---|---|
| Product Design / Figma | 适合下一阶段全局工作台重设计、对象链路图、设计系统规则 | 当前还没有生成 Figma 文件；已有 Flowus/豆包/Codex 参考和 CSS/UI 落地 | 不要把设计插件当作网页功能；必须先有对象链路和产品判断 | 下一轮 UI 大改时采用 |
| Build Web Apps | 已用于前端验证和技能路由 | 高级 QA、浏览器验证、前端修复 | 不能替代真实业务方法 | 采用 |
| Documents / Presentations / Spreadsheets | 适合读取老板资料、PPT 写法和表格校验 | 老板资料知识库、PPT 写作风格、CSV/JSON 产物 | PPT 内容不能当强证据，只学表达结构 | 采用 |
| GitHub | 适合只读同步、同事仓库吸收、公开资料校验 | 远端 selective sync、POI_TGI 仓库审计 | 不得整仓覆盖本地成果；不推送除非用户明确要求 | 采用但谨慎 |
| Superpowers / local skills | 适合约束决策、上下文收集、验证闭环 | 本轮使用 `context-gathering-discipline` 和 `decision-hygiene` | 不要堆叠重复技能造成假复杂 | 采用窄技能 |
| Gmail/Slack/Calendar/CRM 等账号插件 | 当前目标不需要读取 live account 数据 | 暂无落点 | 启动会增加噪声和隐私风险 | 暂缓 |
| Fal/Shutterstock/HeyGen/Remotion/HyperFrames/Game Studio | 可用于视觉/演示/视频，但当前主线是仿真系统 | 暂无主线落点 | 不得把媒体生成当成仿真准确性 | 暂缓 |

## 7. 哪些旧东西必须降级

| 旧东西 | 为什么不够 | 新位置 |
|---|---|---|
| Huff / Gravity / Logit 单独主导 | 经典但过于静态；不能解释时间、路线、排队、运营和真实校准 | 只作为选择概率因子 |
| Selenium-only 测试 | 点完不报错不等于人类可用或 agent 可读 | 保留回归，高级 QA 用 Playwright trace / ARIA |
| 行数/文件存在门禁 | 不能证明逻辑更好 | 只做基础完整性，新增 advanced_gate |
| LLM 直接打分 | DeepSeek 不够稳，容易把草稿写成结论 | LLM 只能生成候选、解释、反例和报告草稿 |
| 旧 P4 完整仿真/ROI/最终推荐 | 老板资料重基线后不可信 | 旧产物信任地图降级 |

## 8. 当前仍不够的地方

1. OpenTelemetry 只安装并登记，还没有在 DeepSeek/API/仿真任务里写 span。
2. Figma/Product Design 还没有用于真正的新工作台设计文件。
3. 多 agent 角色还没有进入生产链路；当前只有契约和对象层。
4. POI_TGI_Calculator 还没有作为可开关辅助模块接入当前 UI。
5. 真实人物仿真准确性仍缺真实客流、轨迹、消费、转化率、运营时间、容量、补货和收益成本校准。
6. 需要周期性重查 2026 之后的新论文和官方工具版本；不能把 2026-06-04 的审计当永久最新。

## 9. 下一步落地动作

1. 把本审计清单纳入 `verify_project_implementation.py` 和交接文件。
2. 给 DeepSeek/API/仿真任务加 OpenTelemetry span：输入对象、模型、工具、错误、输出状态。
3. 建立“人物仿真任务入口”：选择 persona / behavior / choice_probability / validation_target，预检后再运行。
4. 将 POI/TGI 作为 `poi_context` 和 `choice_probability.factor_inputs`，不是最终结论。
5. 新一轮 UI 大改时使用 Product Design/Figma 生成对象链路和设计系统规则，但不照搬插件输出。
6. 每次新增工具或论文，都要追加本清单：来源、先进性、落地位置、风险、决策。

## 10. 本轮外部依据

- Playwright Trace Viewer：记录浏览器 trace，可在本地或 CI 后查看。
- Playwright ARIA snapshot：用于检查可访问语义和 agent 可读结构。
- OpenTelemetry GenAI semantic conventions：用于 AI/LLM/agent trace 命名和属性。
- Hiromitsu1207/POI_TGI_Calculator：同事供需缺口辅助仓库。
- AgentSociety：LLM-native agent simulation platform。
- MobiVerse：hybrid domain-specific generator + LLM urban mobility simulation。
- CAMS：CityGPT-powered agentic framework for urban human mobility simulation。

