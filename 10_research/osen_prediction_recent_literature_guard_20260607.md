# 奥森预测调整与网页修改：近年资料依据护栏（2026-06-07）

> 本文件用于纠正“未学习就修改”的风险。后续每一次报告、网页、仿真、评分、DeepSeek、GIS/CAD 或验证改动，必须先查本文件或补充同类依据，再动手。

## 1. 本轮用户硬约束

- 不能只说“学过/参考过/理解了”，必须真正检索、阅读、筛选，并把资料落到项目实现。
- 所有非小修都要有依据链：本地材料 + 近年外部资料 + 采用/拒用理由 + 项目落点 + 验证方法。
- 近年资料是硬要求，不是“必要时”。优先 2026 年，其次 2025 年；只有缺少高质量资料时才使用 2024 或经典基础文献。
- 外部资料不能替代用户已给材料。奥森报告必须先使用本地 PDF、策划案、CAD/图纸、老板方法、证据台账、人物特征池和 POI/TGI 数据做预测与调整。

## 2. 本轮已检索的近年资料与落地规则

| 主题 | 资料 | 年份 | 结论要点 | 本项目落点 | 不允许的误用 |
|---|---|---:|---|---|---|
| 商业选址多准则决策 | Scientific Reports: `An integrated multi-criteria decision framework for outlet mall location selection using fuzzy DEMATEL-DANP-VIKOR` https://www.nature.com/articles/s41598-026-42895-0 | 2026 | 零售/综合商业选址不应只看单一分数，应把战略准则、空间分析和行为经济因素组合。 | 节点不再裸分；先写理由、约束、风险，再映射为优先级和试运营动作。 | 不得把 VIKOR/DEMATEL 名词塞进报告装专业；没有本地专家权重时不能伪造精确权重。 |
| 商业客流与社会经济/建成环境 | Scientific Reports: `Structural equation modeling approach to evaluate effects of socio-economic and built environment factors on trip generation rates of commercial land use` https://www.nature.com/articles/s41598-026-43632-3 | 2026 | 商业到访/出行生成受社会经济和建成环境共同影响。 | 报告中的价格带、客流和节点建议必须同时看收入/消费、时段、空间位置、业态和交通/可达，不单靠宏观收入。 | 不得用北京市收入单独推出奥森具体客单或收益。 |
| 人流覆盖型选址 | `Massive Retail Location Choice as a Human-Flow-Covering Problem` https://arxiv.org/abs/2410.20378 / 2026 Geographical Analysis 版本检索结果 | 2024/2026 | 商业点位应覆盖真实人流轨迹，而不是只按静态地理距离。 | 奥森报告中优先级要看南门/草坪/入口/湖边/地下空间对人流路径的承接；后续仿真要把路径覆盖作为指标。 | 不能在没有精确轨迹时声称已优化覆盖，只能做基于现有数据的预测与试运营验证。 |
| 零售选址 POI/TGI | Journal of Retailing and Consumer Services: `Retail store location screening: A machine learning-based approach` https://www.sciencedirect.com/science/article/abs/pii/S0969698923003715 | 2024 | POI、竞品和 TGI 可用于候选店初筛，尤其适合缺少完整门店数据时。 | 奥森现有咖啡 TGI、冷饮 TGI、瑜伽 TGI、热门 POI 客单可以进入预测底座。 | 不能让 POI/TGI 单独决定最终排名；它们是因子和线索。 |
| 零售消费者轨迹仿真 | Scientific Reports: `Interaction-aware agent-based simulation of customer trajectories in retail stores with transformer architectures` https://www.nature.com/articles/s41598-025-22885-4 | 2025 | 消费者路径行为需要考虑相邻人、拥挤和时序轨迹，适合数字孪生/布局评估。 | 后续奥森人物仿真不能只写“亲子/白领”标签，要有触发、路径、停留、排队、放弃和天气/时段。 | 没有传感器级轨迹时不能伪装成精确路径仿真。 |
| 零售中心 ABM | SSRN: `Exploring Retail Competition and Consumer Behaviour: An Agent-Based Model of Metropolitan Retail Centres` https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6753765 | 2026 | 零售 ABM 应把异质家庭/客群、可达性、中心构成和敏感性分析结合。 | 奥森报告必须按多类人群和节点组合推进；建议里要出现保守/推荐/激进情景和敏感风险。 | 不得只给单一“最佳方案”。 |
| LLM 消费者数字孪生 | SSRN: `Predicting Behaviors with LLM-Powered Digital Twins of Consumers` https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5256223 | 2025 | LLM 消费者仿真应由个人特质和上下文共同约束。 | DeepSeek 只能做候选解释/草稿，必须被人群状态、预算、时段、天气、空间和证据约束。 | 不得让 DeepSeek 直接决定最终概率、最终收益或最终排名。 |
| LLM 多智能体消费者仿真 | arXiv: `LLM-Based Multi-Agent System for Simulating and Analyzing Marketing and Consumer Behavior` https://arxiv.org/abs/2510.18155 | 2025 | LLM 多智能体可建模消费者决策和社会动态，但需要沙盒和评价。 | 奥森人物仿真可以用 LLM 生成候选行为程序，但必须有结构化 schema、可复核字段和人工锁定。 | 不能把 LLM 输出当真实消费者研究。 |
| 个性化行为模拟 | arXiv: `Customer-R1: Personalized Simulation of Human Behaviors via RL-based LLM Agent in Online Shopping` https://arxiv.org/abs/2510.07230 | 2025 | LLM 行为仿真可做逐步决策，但需要强化/评价约束。 | 当前不训练 RL；报告只采用“行为步骤 + 评价约束”的思想，落在 ROTE 和试运营指标。 | 不能声称已完成 RL 训练或真实用户级个性化。 |
| AI Agent UX | Microsoft Learn: `Human-centered Design for Agents` https://learn.microsoft.com/en-us/agents/design-guidelines/human-centered-design | 2026 | Agent 界面应有一致控件、生命周期模式、错误恢复和用户信心设计。 | AI 工作台、报告页、资料池应清楚显示状态、依据、可撤回/可下载/可复核入口。 | 不能把“AI 自动做完”包装成成熟产品。 |
| Agentic UI 设计 | UXmatters: `Next-Gen Agentic AI in UX Design` https://www.uxmatters.com/mt/archives/2026/03/next-gen-agentic-ai-in-ux-design-evolving-the-double-diamond-process.php | 2026 | Agentic UX 重点是信任、控制和持续交互。 | 页面中要有“打开网页报告/下载 DOCX/查看依据链”，让用户掌控输出，而不是只看 AI 结论。 | 不得让界面看起来专业但用户无法介入。 |
| AI Agent 可观测性 | OpenTelemetry: `Semantic conventions for generative AI systems` https://opentelemetry.io/docs/specs/semconv/gen-ai/ | 2026/当前文档 | GenAI/Agent 需要标准化事件、异常、指标、模型 span 和 agent span。 | 后续验证不能只写“通过”；要记录工具调用、输入输出、错误、截图、下载和用户复核状态。 | 不得声称已完整接入 OTel，除非代码和导出验证都完成。 |
| Human-AI 交互基本原则 | Microsoft Research: `Guidelines for Human-AI Interaction` https://www.microsoft.com/en-us/research/?p=564561 | 经典但仍适用 | AI 系统要说明能做什么、做得多可靠、用户如何调用/忽略/纠正。 | 报告页必须说明依据、状态和复核边界；AI 工作台必须给用户纠正和生成报告的控制点。 | 不能用“待复核”吓退用户，也不能隐藏边界。 |

## 3. 当前报告和网页应立即受这些资料约束

1. 奥森报告主文必须是预测与调整，不是“请用户补资料”。
2. 六节点建议必须先写人群行为、空间条件、价格带、运营时段和试运营动作，再写风险。
3. 分数不应作为核心表达；应使用“第一批低改造试点 / 第二批资质合作试点 / 分区样板 / 暂缓满铺”等业务优先级。
4. DeepSeek 只能承担低成本语义工人角色：候选解释、草稿、字段补全、理由整理；不能当总设计师。
5. 网页必须能让用户看到依据链和下载 DOCX，不让旧报告入口和新报告互相打架。
6. 验证必须包含：DOCX 内容抽取、禁用词扫描、HTTP 200、浏览器截图、控制台错误检查和交接文件更新。

## 4. 本轮实际启用/使用的工具记录

| 工具/能力 | 实际用途 | 证据 |
|---|---|---|
| Web 搜索 | 检索 2026/2025 选址、ABM、LLM 消费者仿真、Agent UX、OTel GenAI 资料 | 本文件第 2 节链接 |
| Documents/DOCX skill | 按 `.docx` 创建/校验规则生成和验证 Word 报告 | `80_delivery/osen_prediction_adjustment_report_20260607.docx` |
| Browser 插件 + Node REPL | 打开本地网页、截图、读 DOM、查控制台 | `40_quality_evidence/osen_prediction_report_browser_20260607.png`、`dashboard_report_view_prediction_after_fix_20260607.png` |
| Python 3.12 | 读取 CSV/JSON/DOCX、生成报告、校验内容和禁用词 | `80_delivery/scripts/build_osen_prediction_adjustment_report_20260607.py` |
| FastAPI/TestClient/HTTPX | 验证 `/` 和静态报告页面 200 返回 | `40_quality_evidence/osen_prediction_adjustment_delivery_validation_20260607.json` |
| 本地证据台账与 CAD 分析 | 提供奥森真实数据、图纸锚点和节点策划依据 | `40_quality_evidence/evidence_ledger.csv`、`cad_dxf_analysis_20260605.json` |

## 5. 后续修改前检查清单

- 是否已读取本地材料：PDF 指标、策划 DOCX、CAD/DWG/PDF、老板方法、人物特征池、POI/TGI？
- 是否已检索 2026/2025 资料，并筛选出与本项目强相关的内容？
- 是否明确写出“采用什么、拒用什么、为什么”？
- 是否把资料落成字段、页面、报告章节、模型约束或验证项？
- 是否避免了旧错误：空想、硬打分、同事主线、补资料主文、DeepSeek 越权、只看宏观收入？
- 是否完成验证并保存证据？
