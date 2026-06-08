# 当前最高优先级决策索引（2026-06-07）

- 先看 DEC-096：真实校准输入必须进入报告 JSON、Markdown、DOCX 和浏览器报告页；不能只停在预检、prompt 或 job request。
- 先看 DEC-095：真实校准输入必须分层进入预检、资料资产、DeepSeek prompt 和仿真 job request；收入/消费、设备价格代理、竞品价格和方案假设不得混用。
- 先看 DEC-094：采用/锁定人物场景和收入/价格带必须进入结构化仿真干跑和网页结果；不能停在报告、prompt、按钮或预检计数。
- 先看 DEC-093：采用/锁定人物场景必须进入报告、DOCX/Markdown 和 DeepSeek prompt；不能只改变按钮、预检计数或对象链状态。
- 先看 DEC-092：收入/消费价格带必须作为人物场景结构化变量进入预检和对象链；采用/锁定场景必须影响任务输入，不能只改变按钮状态。
- 先看 DEC-091：人物仿真衍生特征不能只检查 1000+ 行数；必须同时检查中文可读、收入/预算、时间天气、空间节点、需求触发、供给动作、用户控制、DeepSeek 边界和“具体建议替代裸分”。
- 先看 DEC-090：奥森报告交付必须是 DOCX 待复核工作稿；收入、周边人口、目标人群、时间天气、地理、许可、财务和舆情等真实世界维度必须进入节点实施评审和总门禁，不能用北京市均值替代奥森局部判断。
- 先看 DEC-089：资料与空间底座属于最终蓝图，不是旧资料导入页美化；本地证据、PDF、高德 POI、CAD、老板资料和上传资料必须作为仿真输入底座呈现，非地图页不得后台加载高德地图引擎。
- 先看 DEC-088：页面改动不能只做结构/文件门禁，必须补人类路径门禁；重复入口、旧缓存资源和证据文件泄露 key 参数都必须被自动拦住。
- 先看 DEC-087：当前网页不是整站重做完成，而是旧 P6 壳上的过渡重基线；下一步必须页面级重构，迁移已验证底座，废弃旧叙事。
- 先看 DEC-086：Codex 资源充足时必须承担开发期主架构、主推理、主验证和最终复核；最终市场化网站不得内置 Codex，生产端 AI 只能使用 DeepSeek。
- 先看 DEC-085：安装/学习/插件调用必须变成可复跑验证和总门禁；必要时大改页面，不再用旧补丁掩盖主线变化。
- 先看 DEC-084：当前旧页面不再作为最终形态继续补丁化；保留 API/对象链底座，页面层按“全局对象链路”分阶段重做。
- 先看 DEC-083：全项目上下文和老板模型落点必须可复跑审计；继续实现前先承认哪些只是 partial，不得把“读过论文/列过模型”当落地。
- 先看 DEC-082：方法、工具、插件、论文和同事成果必须进入审计清单，不能再用“已学习/已参考/已使用”一句话带过。
- 先看 DEC-081：门禁本身必须升级为高级 AI/UX/逻辑风险门禁；不能再只靠文件存在、行数和旧 Selenium smoke test 宣称完成。
- 先看 DEC-080：先进 AI 学习吸收必须外化为对象能力层、agent 可读 UI、检查点调度、多 agent 角色分层和旧产物信任地图；不能只把旧页面重新包装。

# DEC-096 真实校准输入必须进入报告交付链路

- 日期：2026-06-07
- 决策：真实校准输入不能只进入预检、DeepSeek prompt 或仿真 job request，还必须进入报告 JSON、Markdown、DOCX 和浏览器报告页。用户和同事打开报告时必须能看到这些输入如何约束收入、消费、竞品价格、方案假设和待补数据。
- 原因：用户明确指出收入水平、目标人群、周围人口、时间天气、竞品价格等真实世界因素必须进入最终分析。若校准输入只停在后台，报告仍会像静态文案，无法证明真实资料影响了交付材料。
- 当前实现：`90_p6_expert_dashboard/app.py` 新增 `attach_real_calibration_context()`；`60_model/simulation/demand_gap.py` 的 Markdown 报告新增“真实校准输入与使用边界”；`60_model/simulation/report_docx.py` 的 DOCX 工作稿新增同名章节和分层表格；`90_p6_expert_dashboard/static/app.js` 的报告页新增“校准输入”摘要卡和“真实校准输入与使用边界”区块。
- 展示规则：报告正文必须使用人话层级：官方宏观边界、本地大数据画像、设备价格代理、竞品价格线索、本地需求热度线索、方案假设待复核；不得向客户裸露 `source_strength` 等机器字段。
- 验证：`report_feature_scene_context_validation_20260607.py` 检查 API report、报告接口、DOCX、Markdown 和前端代码；`osen_report_browser_validation_20260606.py` 检查 Chrome 报告页可见真实校准输入；总门禁最新 `checks=1162 failures=0`。
- 边界：这证明校准输入进入报告交付链路，不证明最终街道收入、真实成交转化、ROI、收益排名或投资定案完成。

# DEC-095 真实校准输入必须分层进入预检、Prompt 和任务请求

- 日期：2026-06-07
- 决策：奥森真实校准输入必须作为单独输入层进入资料资产、仿真任务预检、DeepSeek prompt 和 `/api/simulation/jobs` request。收入/消费、设备价格代理、竞品价格、TGI 偏好和 PPT 方案假设必须分层记录、分层使用，不能混成一个静态“收入水平”或“项目已可定案”的结论。
- 原因：用户进一步指出收入水平、周围人口、目标人群、时间、天气、地理、竞品价格等都必须覆盖，否则分析不准确。收入和消费能力会影响客单价、价格敏感性、转化率、供给优先级、营业时段、补货/排队和实施风险；如果没有分层输入，系统会把宏观数据、代理变量和方案假设误用成最终判断。
- 当前实现：`30_extraction/scripts/build_osen_real_calibration_inputs_20260607.py` 生成 14 条校准输入，并输出 `70_outputs/processed_tables/osen_real_calibration_inputs_20260607.csv`、`40_quality_evidence/osen_real_calibration_inputs_20260607.json`、`40_quality_evidence/osen_real_calibration_inputs_20260607.md`。`90_p6_expert_dashboard/app.py` 新增 `real_calibration_context()`；`/api/simulation/task-preflight` 返回 `real_calibration_context`、`real_calibration_input_count` 和检查项 `osen_real_calibration_inputs`；本地资料资产新增“奥森真实校准输入”；`make_prompt()` 带入真实校准输入；`/api/simulation/jobs` request 记录校准输入数量、ID、来源层级和 usage rule。
- 分层规则：官方北京市收入/消费只能作宏观边界；本地 TGI 和手机价格分段只能作人群偏好/消费能力代理；热门 POI 客单只能作竞品价格线索；PPT 高峰日、消费者占比和转化率只能作待复核方案假设。任何一层都不能单独推出最终收益、最终排名、最终 ROI 或投资定案。
- 验证：`build_osen_real_calibration_inputs_20260607.py` 输出 `status=pass rows=14`；`simulation_task_entry_preflight_validation_20260605.py`、`simulation_feature_scene_dry_run_validation_20260607.py`、`simulation_feature_scene_browser_validation_20260607.py` 均通过；最新总门禁 `checks=1161 failures=0`。
- 下一步：把真实校准输入继续推进到结构化仿真结果和 DOCX 报告正文，并做“新增资料 -> 输入包变化 -> 预检变化 -> 干跑变化 -> 报告变化”的闭环验证。

# DEC-094 采用人物场景与收入价格带必须进入结构化仿真干跑

- 日期：2026-06-07
- 决策：用户采用或锁定的人物场景，以及其中的收入水平、消费价格带、时段、天气、空间节点、需求触发和供给动作，必须进入结构化仿真干跑结果。它们不能只停留在报告、DeepSeek prompt、按钮状态、预检计数或对象链摘要。
- 原因：用户明确指出“还有收入水平”和“涵盖层面必须多”，否则分析不准确。收入/价格带会影响供给组匹配、客单价假设、转化率敏感性、补货/排队/关闭时间和真实实施建议；如果不进入仿真检查结果，平台仍然会退回静态报告。
- 当前实现：`60_model/simulation/engine.py` 的 `run_structural_simulation()` 接收 `feature_scenes`，并输出 `feature_scene_context`、`scenario_pressure`、`feature_scene_count`、`matched_feature_scene_count`。`60_model/db/schema.sql` 和 `60_model/db/store.py` 已持久化这些字段。`90_p6_expert_dashboard/app.py` 创建仿真任务时把 `selected_feature_derivative_inputs(limit=12)` 写入 request 和仿真结果，CSV 导出包含人物场景与场景压力 JSON。
- 前端要求：`90_p6_expert_dashboard/static/app.js/css` 必须展示“人物场景压力摘要”和“场景命中 / 场景动作”。客服端不得裸露 `needs_review/not_final`、`sample_city_green_heart`、英文业态或 `P3-GATE` 等内部字段；这些必须映射为业务文案。
- 验证：`simulation_feature_scene_dry_run_validation_20260607.py`、`simulation_feature_scene_browser_validation_20260607.py`、`simulation_task_entry_preflight_validation_20260605.py`、`object_chain_rebaseline_validation_20260605.py` 均通过。浏览器证据为 `40_quality_evidence/simulation_feature_scene_browser_validation_20260607.json` 和 `40_quality_evidence/simulation_feature_scene_browser_validation_20260607/simulation_feature_scene.png`。最新总门禁 `checks=1155 failures=0`。
- 边界：这仍是受控结构化干跑，不是完整真实仿真、最终客群占比、最终 ROI、最终排名或投资定案。正式结论仍需奥森周边收入/人口、真实客流、竞品价格、交易/转化、许可消防和 CAD/GIS 校准。

# DEC-093 采用/锁定人物场景必须进入报告和 DeepSeek prompt

- 日期：2026-06-07
- 决策：用户采用或锁定的人物场景不能只影响按钮状态、预检计数或对象链摘要，必须进入报告生成、DOCX/Markdown 交付和 DeepSeek prompt。报告必须显示场景编号、收入/价格带、时段/天气/空间、需求触发、建议动作和待补证据。
- 原因：用户指出“使用起来的问题”和“收入水平”会影响分析准确性。如果采用场景只停留在 UI 控制层，后续报告仍会按旧静态逻辑生成，无法证明用户控制真的进入业务结论材料。
- 当前实现：`90_p6_expert_dashboard/app.py` 新增 `controlled_feature_scene_context()` 和 `attach_controlled_feature_scene_context()`；`make_prompt()` 带入“用户采用/锁定的人物场景输入”。`60_model/simulation/demand_gap.py` 的 Markdown 报告和 `60_model/simulation/report_docx.py` 的 DOCX 工作稿新增“人物场景输入与收入价格带”。前端报告页新增“人物场景”摘要卡和人物场景业务卡片。
- 验证：`90_p6_expert_dashboard/qa/report_feature_scene_context_validation_20260607.py` 通过 API、DOCX、Markdown 和 prompt 检查；Browser 证据 `40_quality_evidence/report_feature_scene_context_browser_20260607.json/png` 确认报告页真实可见、收入/价格带可见、禁词为空、console error=0。最新总门禁 `checks=1143 failures=0`。
- 边界：这些采用/锁定场景仍是待复核输入，不是真实客群占比、最终收益、最终排名或完整仿真结果。正式定案仍需周边收入人口、客流、竞品价格、转化、交易、审批和 CAD/GIS 校准数据。

# DEC-092 收入/消费价格带必须进入人物场景预检和对象链

- 日期：2026-06-07
- 决策：收入水平不能只作为报告段落或人群画像背景出现，必须成为人物场景覆盖池的结构化变量，并进入仿真任务预检、项目综合 AI 上下文和全局对象链。用户采用或锁定的人物场景必须进入 `feature_scene_inputs`，影响预检检查项和顶部计数。
- 原因：用户明确补充“还有收入水平”，并指出真实分析必须覆盖更多层面。收入/消费能力会改变价格带、客单价、转化率、目标人群、供给动作、试点优先级和真实世界实施风险；若只写在文字里，后续系统无法筛选、控制、验证或让报告引用。
- 当前实现：`30_extraction/scripts/build_person_simulation_feature_derivatives.py` 已新增 `income_segment_id/name`、`income_price_band`、`income_sensitivity_note`、`income_evidence_hint`；验证器要求 `income_segment_id >= 5`。`90_p6_expert_dashboard/app.py` 已让 `/api/simulation/feature-derivatives` 返回收入字段，`/api/simulation/task-preflight` 返回 `feature_scene_inputs` 和 `controlled_feature_scene_count`，并新增预检项 `controlled_feature_scenes`。对象链新增 `feature_derivative_scene`。前端场景卡展示收入段、消费价格带和“收入与价格怎么影响判断”。
- 验证：`simulation_task_entry_preflight_validation_20260605.py`、`object_chain_rebaseline_validation_20260605.py`、浏览器证据 `feature_derivative_income_control_browser_20260607.json/png` 均通过；最新总门禁 `checks=1132 failures=0`。
- 边界：这不是最终收入模型或真实收益结论。正式校准仍需奥森周边街道级收入、居住/办公/游客来源、真实客流、交易/转化、竞品价格和天气/时段数据。

# DEC-091 人物仿真衍生特征必须检查可读性、覆盖面和行动建议

- 日期：2026-06-07
- 决策：`person_simulation_feature_derivatives_1000_20260604.csv` 不能再只以“行数达到 1000+”作为通过条件。它必须是可复跑生成的 UTF-8 中文覆盖池，并覆盖人群状态、收入/预算、时段、天气/节假日、空间节点、需求触发、供给动作、用户采用/放弃/锁定、DeepSeek 禁止边界和具体修改建议。
- 原因：本轮发现旧 CSV 虽有 1200 行，但中文内容已损坏为 `??`，旧总门禁仍因只数行数而通过。这会污染后续人物仿真、节点解释和报告可信度，也违背用户反复强调的“不能空想、要考虑收入和真实世界多维因素”。
- 当前实现：新增 `30_extraction/scripts/build_person_simulation_feature_derivatives.py`，重新生成 1200 条可读场景；新增 `30_extraction/scripts/verify_person_simulation_feature_derivatives_20260607.py`，验证行数、列、乱码、业务关键词、DeepSeek 边界、用户控制和具体建议。`90_p6_expert_dashboard/app.py` 已把“人物仿真覆盖池”接入资料底座和仿真任务预检，前端显示其进入对象与使用边界；并新增 `/api/simulation/feature-derivatives` 与 PATCH 控制接口，用户可对代表场景采用、放弃、恢复、锁定和解锁。
- 覆盖结果：当前覆盖 `persona_id=8`、`income_segment_id=5`、`time_band_id=6`、`weather_id=5`、`node_context_id=6`、`demand_trigger_id=10`、`candidate_supply_action_id=21`，并明确收入/预算、消费价格带、客单价、转化率、补货、关闭时间和现场观察等数据需求。
- 门禁：`30_extraction/scripts/verify_project_implementation.py` 已接入新的 feature derivative 验证报告、浏览器可见性证据、浏览器用户控制证据和收入/价格带控制证据。最新总门禁 `checks=1132 failures=0`。
- 边界：这只是人物仿真场景/特征覆盖池，不是最终仿真结果，不代表 ROI、最终排名、最终收益或完整 P3/P4 校准已完成。

# DEC-090 奥森报告交付以 DOCX 待复核工作稿为准，收入与真实世界实施评审进入总门禁

- 日期：2026-06-07
- 决策：奥森综合报告当前交付形态是可复核 DOCX 工作稿，而不是最终投资、收益、排名或施工结论。报告必须显示收入/消费边界、周边人口与收入、目标人群、时间天气、地理可达、空间工程、消防安全、许可合规、运营财务、舆情社区接受和仿真数据校准等真实世界维度。
- 原因：用户指出“收入水平”以及天气、地理、新闻、居住区、目标人群、时间因素等都必须纳入，否则分析不准确。此前裸分数或泛泛建议容易误导业务方，以为节点已经可以直接排序或投资。
- 当前实现：`60_model/simulation/demand_gap.py` 为每个节点生成 `implementation_review`，包含目标客群、需求触发、收入与价格带、时间天气、周边补证、空间适配、三套实施方案、推荐路径、风险控制、会改变判断的证据和仿真输入。`60_model/simulation/report_docx.py` 生成 DOCX 工作稿，`90_p6_expert_dashboard/app.py` 支持 `/api/reports/site-selection/download?format=docx`。
- 收入口径：`10_research/osen_real_world_context_sources_20260607.md` 记录北京市统计局/国家统计局北京调查总队 2025 收入、消费和服务消费数据。该数据只能作为全市上位消费能力边界，不能替代奥森周边街道级收入、居住/办公/游客来源和竞品价格。
- 交付与验证：DOCX 路径 `80_delivery/osen_integrated_site_selection_report_20260606.docx`，隔离 LibreOffice 渲染 18 页，浏览器截图 `40_quality_evidence/osen_report_browser_validation_20260606/report_view.png`。`verify_osen_docx_delivery_20260606.py` 通过 11 项检查，`verify_project_implementation.py` 最新 `checks=1109 failures=0`。
- 边界：进入正式报告前必须继续补齐奥森周边 1-3 公里人口/收入/消费层级、真实客流、分时段/天气转化、竞品客单、成本收益、审批许可、消防结构、医疗/演出/食品边界和 CAD 控制点 GIS 校准。

# DEC-089 资料与空间底座是新蓝图切片，不是旧上传页补丁

- 日期：2026-06-05
- 决策：`资料与空间底座` 必须作为最终 AI 仿真决策系统的输入工作区保留并重构，不再只是旧“资料导入”页面。它承接证据台账、PDF 原生表格、高德 POI、CAD/图纸、老板方法资料、策划资料和网页上传资料，并明确每类资料进入哪个对象：人群状态、行为程序、选择概率、空间语境、验证目标或报告依据。
- 原因：用户指出当前最大问题是新老平衡不清，只处理旧东西却没有设计新东西。老板资料和统一方法矩阵要求从 `资料证据 -> 人群状态 -> 行为程序 -> 选择概率 -> 空间语境 -> 验证目标 -> 预检 -> 报告` 形成工作链；Flowus/AI 设计学习也要求先定产品调性和真实工作流，再做页面原型，而不是把资料当文件列表展示。
- 当前实现：`uploadView` 顶部新增 `source-foundation-panel`，显示 4 个底座摘要和 8 类本地底座资产卡。每张卡显示“进入对象”和“使用边界”，并把机器字段映射为业务文案。前端读取 `/api/dashboard` 的 `simulation_task_preflight.local_data_assets`，不是在页面写死数字。
- 旧耦合修复：`renderAll()` 不再无条件调用 `renderMap()`。非地图页只展示空间语境摘要，不后台加载高德 JS、静态地图或高德 key；进入 `mapView` 时才初始化地图。
- 验证：新增 `30_extraction/scripts/verify_source_space_foundation_20260605.py`，输出 `40_quality_evidence/source_space_foundation_validation_20260605.json/md`；Chrome 运行态证据为 `40_quality_evidence/source_space_foundation_browser_runtime_20260605.json` 和 `40_quality_evidence/source_space_foundation_upload_lazy_map_20260605.png`。最新总门禁 `py -3.12 30_extraction\scripts\verify_project_implementation.py` 输出 `checks=1049 failures=0`。
- 边界：这证明资料与空间底座切片已经进入新蓝图，不证明完整报告链路或完整仿真已完成。证据台账/PDF 表格/POI 数量是否随新增资料完整变化，应排在“平台能完整跑出一份报告”之后做闭环验证。

# DEC-088 页面改动必须补人类路径门禁，不能只靠结构验证

- 日期：2026-06-05
- 决策：以后任何用户可见页面改动，不能只检查文件存在、静态词、截图或组件结构；必须加入至少一条“真实人类路径”验证，覆盖同一页面重复入口、按钮语义是否重复、详情区是否悄悄切换模式、浏览器是否加载新静态版本、证据文件是否含 key/token/API 参数形态。
- 原因：用户指出节点详情中每个节点下方仍出现“新增节点”，而左上已有新增入口。根因是旧 `renderNodeForm(node)` 无条件渲染，导致不可编辑节点也出现新增表单；旧门禁未覆盖“同一动作重复出现”这种基础使用问题。
- 当前修复：`renderNodeForm(node)` 已改为：无节点时才渲染新增表单；可编辑节点才渲染“编辑当前节点”；不可编辑节点详情不渲染表单。顶部 `quickNewNodeBtn` 继续作为唯一新增入口。
- 缓存修复：`index.html` 静态资源版本更新为 `20260605-workflow`，避免浏览器继续加载旧 `app.js/css` 造成误判。
- 证据安全修复：浏览器运行态证据 `workflow_nav_node_detail_runtime_20260605.json` 不再保存高德脚本 URL 或 `key=` 参数，只保留脱敏加载状态和布尔值。
- 验证：新增 `30_extraction/scripts/verify_workflow_navigation_20260605.py`，输出 `40_quality_evidence/workflow_navigation_validation_20260605.json/md`；已接入总门禁。最新 `py -3.12 30_extraction\scripts\verify_project_implementation.py` 输出 `checks=1038 failures=0`。

# DEC-086 开发期 Codex 主导与生产网站 DeepSeek-only 角色分离

- 日期：2026-06-05
- 决策：开发期不再把“节省模型成本”作为 Codex 工作质量的约束。Codex / 高能力主 agent 应放手承担资料深读、论文筛选、方法设计、约束编写、反例检查、工程实现、浏览器验证、门禁和最终复核；但最终面向市场的网站不得使用 Codex 作为内置 AI，生产运行 AI 只能搭载 DeepSeek。
- 原因：用户已明确当前 Codex 资源充足，但最终网站要考虑上市场和成本结构，不能依赖 Codex。DeepSeek 便宜适合产品内批量摘要、候选状态、候选行为程序、解释和报告润色；Codex 只在开发、审查、门禁和交接阶段使用。
- 保留：网页端搭载 DeepSeek，并应通过 schema、队列、缓存、429 退避、OpenTelemetry、`draft/needs_review` 和用户采用/放弃/锁定机制使用。
- 禁止：不得让 DeepSeek 逐游客实时驱动仿真、给最终排名、给最终收益、写 checked 证据、覆盖用户锁定对象，或替代 Codex 对老板资料/论文/方法边界的复核。
- 生产边界：不得在最终网站 UI、后端路由、配置文案或市场交付材料中宣称/依赖 Codex 内置能力；Codex 产物只能转化为本地规则、schema、校验、提示词约束、报告模板和 DeepSeek 调用契约。
- 当前落实：`30_extraction/scripts/build_person_simulation_accuracy_requirements.py` 已新增 `ACC-009 高能力主控` 和 `CTRL-CODEX-PRIMARY` 来源；后续总门禁会检查该治理要求存在。
- 先看 DEC-079：全局 AI 仿真决策系统设计重基线；旧界面需要按“目标 -> 对象 -> 依据 -> 动作 -> 复核 -> 报告”重组，不再围绕页面、裸分数或技术门禁堆叠。
- 先看 DEC-078：Codex 自身强化作为主线防偏航层插入；它服务 P6 对象池和人物仿真，不另开支线。
- 先看 DEC-074：老板资料和外部论文必须落地为系统对象、字段、门禁、adapter 或验证目标；用户说的“模仿人类”只指 UI/可用性测试，不是方法层判断“像不像人”。
- DEC-077 已被 DEC-078 修正：现在允许先插入防偏航层，但必须验证后回到 P6 对象池。
- 先看 DEC-076：现代 AI 仿真主线已补强，经典 Huff/Logit/Gravity/Social Force 降级为因子，主线改为轻量领域生成器 + 空间/运营约束 + LLM 个体修正/解释 + schema/校准/人工门禁。
- 先看 DEC-072 和 `10_research/boss_method_materials_20260604/full_system_rebaseline_20260604.md`：老板资料触发的是系统级重构，不是缺口补丁。
- 旧 DeepSeek 输出已按 DEC-073 纳入 metadata-only envelope；通过验证不代表旧内容可用。
- 先看 DEC-070 / DEC-071：老板六份方法资料触发全项目方法重基线；仿真输出从裸分数转向优先级、依据、建议和缺口。
- 在 DeepSeek 任务契约和旧文件可信度审计完成前，不得继续把旧 P4、ROI、最终排名、最终推荐或节点分数写成已完成事实。
- 老板资料必须全盘吸收后再工程化，不再按“缺什么补什么”的补丁思路推进。

# DEC-087 当前网页是过渡重基线；下一步进入页面级重构

- 日期：2026-06-05
- 决策：当前 `90_p6_expert_dashboard` 不能被描述为“整站已经重新做完”。它是旧 P6 页面壳上的过渡重基线：对象链、AI 项目综合、仿真任务预检、DeepSeek-only 边界和验证体系已经接入，但旧的并列 view、panel 结构、节点/地图/资料/报告/AI 分区仍然存在。下一步必须做页面级信息架构重构，而不是继续小修旧壳。
- 原因：用户质疑成立。老板六份资料、Flowus/AI 设计学习和 2026 仿真论文都要求系统围绕“资料 -> 人群状态 -> 行为程序 -> 选择概率 -> 空间语境 -> 验证目标 -> 节点推进 -> AI 共识 -> 报告”工作；旧页面的主叙事仍容易让用户看到一堆并列模块，误以为是传统项目管理面板。
- 当前证据：新增 `30_extraction/scripts/audit_page_rebuild_strategy_20260605.py`，输出 `40_quality_evidence/page_rebuild_strategy_audit_20260605.json/md`，状态为 `requires_page_level_rebuild`。审计明确：`full_website_redone=false`、当前是 `过渡重基线`、旧壳仍在、下一步应迁移已验证底座并废弃旧叙事。
- 技能依据：`10_research/ui_skill_design_system_audit_20260605.md` 已记录本机 `ui-ux-pro-max`、`playwright`、`playwright-interactive`、`web-design-guidelines` 的状态；本轮采用 Data-Dense Dashboard、高可读状态、active state、aria-live、可访问反馈和响应式布局作为下一版页面约束。
- 保留：FastAPI/API、对象链 payload、资料池状态、人群状态/行为程序/选择概率/验证目标对象、仿真任务预检、DeepSeek-only 生产边界、Playwright/axe/Lighthouse/OTel 证据链。
- 重构：左侧导航和旧 view 切换应重组为流程型工作区；资料池和方法对象池合并为对象链工作区；AI 工作台成为项目综合/节点分析的持续沟通区；节点、地图、报告作为对象链下游，不再和 AI/资料割裂。
- 废弃或隐藏：旧项目总览死文案、裸分数/最终推荐/ROI/完整仿真完成口径、后端词泄露、静态地图等同真实仿真的误导、旧 dry-run 或 DeepSeek 草稿被写成最终判断。
- 验证：`verify_project_implementation.py` 已接入 UI 技能证据和页面重构裁决审计；后续总门禁必须确认该裁决存在且状态为 `requires_page_level_rebuild`。

# DEC-085 学习/安装必须落成可复跑工具、页面改造和总门禁

- 日期：2026-06-05
- 决策：以后不能把“学过、装过、调用过插件”当作完成。凡是对页面层、AI 工作台、仿真链路或验证体系有影响的学习和工具，必须至少落成一种可复跑资产：设计施工图、代码实现、QA 脚本、证据报告、总门禁检查或交接约束。必要时允许大改页面，不用旧壳小补丁掩盖主线变化。
- 原因：用户指出此前最大风险是“安装了却不用、学习了但忘记、做事像空想”。这次复核证明该担忧成立：旧门禁能让部分可访问性语义问题和未落地 Lighthouse 脚本溜过去。
- 当前落地：新增 `00_control/page_layer_rebuild_blueprint_20260605.md`；新增并运行 `page_layer_rebuild_validation_20260605.py`、`axe_accessibility_probe.mjs`、`lighthouse_user_flow_probe.mjs`、`otel_fastapi_trace_probe_20260605.py`；新增 `audit_advanced_capability_and_legacy_methods_20260605.py`。
- 验证：页面层验证 `status=pass failure_count=0`；axe 三视图违规数 0；Lighthouse 用户流 3 步通过并生成 HTML 报告；OTel 生成 9 个 span 且 3 个 API 均 200；先进能力审计 `status=pass failure_count=0`；总门禁 `py -3.12 30_extraction\scripts\verify_project_implementation.py` 最新 `checks=1003 failures=0`。
- 边界：这证明当前“强化层”已经落地，不证明整个地图/节点/仿真最终完成。后续地图、节点、报告或仿真入口若继续大改，也必须补对应的对象链验证、浏览器截图、可访问性/性能/trace 证据和总门禁。

# DEC-084 保留对象链底座，页面层按新主线分阶段重做

- 日期：2026-06-05
- 决策：当前 `90_p6_expert_dashboard` 的旧页面壳不再作为最终形态继续零散补丁化。保留已经跑通的后端 API、资料导入、AI 会话、对象池、地图入口和报告入口；页面层以后按“全局对象链路”分阶段重做，而不是围绕旧状态卡、旧节点列表和旧说明书式布局继续美化。
- 原因：用户再次指出昨天给出的 Flowus 三页、老板方法资料和外部学习没有真正进入页面设计，继续修旧页面会回到“学了但不用”的问题。这个判断成立：旧页面虽然能运行，但主叙事仍容易停留在项目总览/节点/地图/资料/AI 分区，而新系统应围绕 `资料 -> 人群状态 -> 行为程序 -> 选择概率 -> 空间语境 -> 验证目标 -> 节点推进 -> AI 共识 -> 报告` 的对象链工作。
- 当前落地：新增 `10_research/evidence_based_direction_reset_20260605.md`，真实 Chrome 读取三份 Flowus 页面并保存到 `10_research/flowus_design_learning_20260605/`；新增 `/api/object-chain` 与 dashboard `object_chain` payload；前端新增“对象链路矩阵”；新增 `object_chain_rebaseline_validation_20260605.*` 和浏览器验证 `object_chain_browser_validation_20260605.json/png`。
- 验证：`/api/object-chain` 返回 10 类对象，summary 为 `usable=3 draft=6 blocked=1`；对象链验证 `status=pass failure_count=0`；浏览器验证 `status=pass failure_count=0 console_errors=[]`，截图为 `40_quality_evidence/object_chain_browser_validation_20260605/object_chain_overview.png`。
- 边界：对象链矩阵只是重做前的缺口底座，不是最终 UI。它用于证明新主线的数据和动作能跑通；后续仍需重做第一屏、AI 工作台、资料池、节点池和仿真入口的视觉与交互。
- 下一步：先基于对象链设计新的第一屏/AI 工作台/资料池信息架构，再进行页面级重做；每次页面重做前必须写明采用了哪些 Flowus/老板资料/2026 文献证据，拒绝了哪些旧惯性，并跑浏览器验证。

# DEC-083 全项目上下文与老板模型落点必须可复跑审计

- 日期：2026-06-05
- 决策：新增 `30_extraction/scripts/audit_project_context_and_legacy_risks.py` 与 `30_extraction/scripts/audit_method_model_landing_coverage.py`，输出 `project_context_legacy_risk_audit_20260605.*` 和 `method_model_landing_coverage_20260605.*`，并纳入 `verify_project_implementation.py` 与主线启动上下文。
- 原因：用户指出昨天虽然学习了很多，但担心没有真正研究老板模型、没有吸收昨天外部资料、历史旧文件仍会污染判断。这个担忧成立：当前项目 900+ 文件、旧风险词命中上万处，不能靠聊天记忆管理。
- 当前证据：全项目审计显示项目文件 943、可文本扫描 732、老板原始资料 6/6 齐、Git 待处理行 193、旧风险词 12323 次；模型落点审计显示 `covered=4 partial=5 missing=0`。
- 关键判断：昨天资料不是白读，但大量模型仍是 partial。ROTE/behavior program、HumanLM/persona state、RL+LLM 宏观/微观验证、DeepSeek 队列与 trace 都还没充分落成产品能力。
- DeepSeek 并发边界：新增 `10_research/deepseek_api_concurrency_capacity_20260605.md`，记录官方账号级并发口径。不得用多 API Key 作为架构方案，也不得逐游客实时调用 DeepSeek。
- 下一步：优先把 partial 模型落成系统能力：人群状态对象池、行为程序对象池、DeepSeek 队列/缓存/trace、验证目标前置条件和旧风险词用户可见清理。

# DEC-082 方法、工具、插件、论文使用必须审计，不得一句话带过

- 日期：2026-06-04
- 决策：新增 `10_research/method_tool_plugin_audit_20260604.md`，并纳入 `verify_project_implementation.py` 的 required files 与 `advanced_gate`。后续每个方法、工具、插件、论文、同事成果都必须记录来源、为什么用、是否足够先进、本项目落点、风险和决策。
- 原因：用户指出“先进、全面、强大”不能被一句话糊弄；上一轮问题的根源之一是工具/论文/插件学习没有被追问是否真的落地，也没有区分采用、选择性吸收、降级、暂缓和拒用。
- 当前实现：审计清单已覆盖 Playwright、OpenTelemetry、Selenium、Chrome/Browser/DevTools、DuckDB/Polars、SimPy、SALib/Optuna、Mesa/Mesa-Geo、OSMnx/MovingPandas、DeepSeek、AgentSociety、MobiVerse、CAMS、POI_TGI_Calculator、Product Design/Figma、Documents/Presentations/Spreadsheets、GitHub/Superpowers 等条目。
- 边界：这不是“列了就完成”。审计清单明确 OpenTelemetry span、Product Design/Figma 设计文件、POI/TGI 辅助接入、人物仿真任务入口仍未实装；这些是下一步要落地的任务。
- 下一步：先保持该审计清单与门禁同步，再继续 OpenTelemetry 可观察性、人物仿真任务入口、POI/TGI 因子接入和全局 AI 工作台重构。

# DEC-081 高级 AI/UX/逻辑风险门禁成为主线门禁的一部分

- 日期：2026-06-04
- 决策：新增 `10_research/advanced_ai_validation_rebaseline_20260604.md` 和 `90_p6_expert_dashboard/qa/advanced_agentic_workflow_validation_20260604.py`，把验证体系从旧式“能打开/能点击/文件存在/行数正确”升级为浏览器 trace、ARIA snapshot、agent 可读 hook、信息密度、AI 范围完整性、监督检查点、旧产物泄露、证据边界和可观察性检查。
- 原因：用户指出“先进”不只是框架，检查方法也旧；上一轮用户能看到很多问题而自动化看不出来，说明旧门禁不能证明人类可用、AI 可信、逻辑更好。这个担忧成立。
- 当前实现：已安装并登记 `playwright>=1.60.0`、`opentelemetry-sdk>=1.42.1`，保留 `selenium>=4.44.0` 兼容。高级 QA 生成 `advanced_agentic_workflow_validation_20260604.json/md`、trace zip、ARIA yml 和 7 张视图截图；风险 taxonomy 覆盖 10 类：human_visual、agent_readability、ai_scope_integrity、oversight_checkpoint、legacy_leakage、state_coupling、evidence_traceability、observability、ai_output_risk、accessibility_semantics。
- 验证：高级 QA 最新 `status=pass findings=0`，`missing_hook_count=0`，资料页 `text_len=4364`，trace 约 2.9MB，ARIA 7062 bytes；`verify_project_implementation.py` 已新增 advanced_gate，完整门禁 `checks=917 failures=0`，`start_codex_mainline.ps1 -FullGate` 通过。
- 边界：高级 QA 通过不代表最终系统完成；它只证明当前迁移基线可观察、可审计、没有明显旧词泄露和 agent 可读缺口。后续每次大改仍需扩展 taxonomy，而不是把这份脚本当一劳永逸。
- 下一步：把“用过什么、为什么用、是否足够先进、哪里还不够”整理成可审计方法/工具清单，继续主线的全局 AI 工作台、资料/方法对象池、仿真任务入口和报告链路落地。

# DEC-080 先进 AI 学习必须外化为能力系统，不得只重包旧工作台

- 日期：2026-06-04
- 决策：新增 `10_research/advanced_ai_learning_absorption_register_20260604.md` 作为先进学习吸收台账。后续设计和实现不能只把 Huff/Logit/门禁/对象池/报告草稿重新包装成“先进系统”，必须外化为对象能力层、agent 可读 UI、检查点调度、多 agent 角色分层、可反驳解释和旧产物信任地图。
- 原因：用户指出当前重基线仍显得“考虑少、不够先进、像老东西”，并担心之前学习内容在上下文压缩中遗忘。这个判断成立：仅有全局口径和对象池还不足以体现 2026 agentic workflow、human oversight、computer-use agent 风险、可视分析仿真和决策协作的进步。
- 当前实现：台账已明确旧方向和新方向差异；吸收 Agentic information systems、When Should Users Check、Dark Patterns Meet GUI Agents、SCSimulator、MCP-SIM、RESPOND、ToolSmith 等资料；把先进性落到 `project_scope/source_material/method_object/persona_state/behavior_program/choice_probability/spatial_node/poi_context/simulation_task/validation_target/ai_session/report_draft/legacy_artifact` 等对象。
- 边界：新资料只作为工程判断和约束，不盲目引入新框架；多 agent 不是数量堆叠，必须按 planner/extractor/simulator/validator/explainer/reviewer 等角色通过对象和 schema 交换信息。
- 下一步：将该台账纳入总门禁；继续重构 AI 工作台、资料池/方法对象池和仿真任务入口；随后建立全仓库旧产物信任地图。

# DEC-079 全局 AI 仿真决策系统设计重基线；旧界面需按对象链路大改

- 日期：2026-06-04
- 决策：本项目后续 UI/UX、AI 工作台、资料池、节点推进、仿真任务和报告生成统一按 `10_research/global_ai_simulation_design_rebaseline_20260604.md` 执行。系统定位不是单一“公园商业决策工作台”，而是全局“AI 驱动仿真决策系统”；页面只是对象和工作流的呈现层。
- 原因：用户指出原界面存在功能、设计、视觉和使用逻辑矛盾；老板资料和 2026 外部资料也显示旧的“节点分数 / 门禁 / 草案平铺 / 独立 AI 问答框”不适合当前方向。继续美化旧页面会保留错误主叙事。
- 当前实现：已用 Selenium 真实抽取 3 份 Flowus AI 设计资料；新增 `ai_design_2026_openalex_raw_20260604.json`、`ai_design_2026_semantic_scholar_raw_20260604.json`、`global_ai_simulation_design_rebaseline_20260604.md`；P6 已开始把 `choice_probability` / `simulation_validation_target` 落为用户可控对象池，并把节点用户可见逻辑从裸分数切到 `priority_stage`、`priority_summary`、`priority_recommendations`、`priority_basis`。
- 边界：Flowus、论文、插件和 skill 只能作为判断材料，不得照搬。2026 资料优先，但仍需按本项目目标裁剪；2025 或更早资料只能作为补充。
- 下一步：项目总览改为全局推进台；资料池、节点池和 AI 工作台按对象链路重构；所有新增 UI 必须显示真实数据状态和可执行动作。

# DEC-078 Codex 自身强化作为主线防偏航层插入

- 日期：2026-06-04
- 决策：Codex 自身强化允许现在做，但只能作为仿真主线内的防偏航层。它的产物必须服务于新对话快速恢复、旧口径冲突清理、门禁启动和 P6 对象池继续推进，不得替代当前仿真主线。
- 原因：用户指出长对话和上下文压缩会让新会话像“降智”，而此前“等主线完成再增强”的口径可能导致下一轮继续跑歪。更稳的做法是在主线里插入一层可运行的启动和校验入口。
- 当前实现：新增 `00_control/codex_mainline_guardrails.md`、`00_control/start_codex_mainline.ps1`、`30_extraction/scripts/build_codex_mainline_context.py`；生成 `40_quality_evidence/codex_mainline_context_20260604.md/json` 后继续 P6 对象池。完整入口已验证：`missing_files=0 stale_top_phrases=0`，交接编码 `failures=0`，总门禁 `checks=849 failures=0`。
- 边界：防偏航层不能变成泛泛学习、插件堆叠或配置折腾；不得覆盖老板资料重基线、DeepSeek 低能力边界、P6 对象池下一步。
- 下一步：验证入口脚本和总门禁，然后继续实现 P6 仿真对象池 API/UI。

# DEC-077 主线优先；已被 DEC-078 修正为“主线内插入防偏航层”

- 日期：2026-06-04
- 决策：当前优先级是继续仿真主线，把 `choice_probability` 和 `simulation_validation_target` 接入 P6 用户可控对象池。此决策的“强化排后”部分已被 DEC-078 修正：可以先做防偏航层，但只能作为主线保护插入。
- 原因：用户指出此前被打断后主线思路会断，并且新对话体验像“降智”。这些确实需要治理，但不能抢占当前仿真主线。
- 当前实现：新增 `adapt_choice_probability_and_validation_targets.py`；生成 36 条 `choice_probability` 候选和 10 条 `simulation_validation_target`；两个 envelope 契约验证通过；总门禁 `checks=838 failures=0`。
- 边界：所有选择概率候选保持 `probability_value=null` 和 `needs_review`；验证目标用于阻止旧 dry-run 或 LLM 草稿被误写成完整仿真。
- 下一步：P6 页面必须支持用户新增、编辑、采用、放弃、删除、锁定这两类对象。防偏航层验证完成后继续该任务。

# DEC-076 现代 AI 仿真方法补强；经典模型降级为因子

- 日期：2026-06-04
- 决策：本项目方法主线从“经典 GIS/选址公式 + LLM 解释”调整为“轻量领域生成器 + 空间/运营约束 + LLM 个体修正/解释 + schema/校准/人工门禁”。Huff/Gravity/Logit/Social Force 等经典方法继续保留，但只作为 `choice_probability` 或空间运动的可解释因子，不再作为系统主叙事。
- 原因：用户指出此前方法学习偏古早，现代 AI 城市仿真、LLM agent、大规模调度、混合生成器和现代数据工程吸收不足。OpenAlex 本轮检索命中 AgentSociety、AI Metropolis、CAMS、MobiVerse、CitySim、GATSim 等现代资料，足以支撑主线修正。
- 当前实现：新增 `modern_practical_method_rescreen_20260604.md`、`modern_method_openalex_search_20260604.json`、`verify_modern_sim_stack.py`、`modern_sim_stack_verification_20260604.json/md`；安装并验证 DuckDB、Polars、jsonschema、Pydantic、GeoPandas、Shapely、NetworkX、OSMnx、MovingPandas、Mesa、Mesa-Geo、SimPy、SALib、Optuna；`requirements.txt` 已同步。
- 边界：DeepSeek 仍只能做低成本语义工人，生成 `draft/needs_review` 候选、解释、反例和报告草稿；不得做最终仿真、checked 证据、ROI、最终排名或最终商业结论。
- 暂缓：Ray、MATSim、SUMO、AnyLogic、Unreal 暂不强行引入；等真实路网、活动链、校准数据和规模压力出现后再决策。
- 验证：现代栈验证 `packages=14 failures=0`；总门禁 `checks=804 failures=0`。

# DEC-074 方法吸收必须落成工程对象；“模仿人类”仅属于 UI 可用性测试

- 日期：2026-06-04
- 决策：老板六份资料和外部论文不得只写成“参考过/读过”。每个可采用方法必须至少落成一种工程资产：系统对象、schema 字段、DeepSeek 契约、adapter、验证指标、UI 可编辑对象或禁用边界。
- 澄清：用户要求“模仿人类”是指后续 Selenium/Browser/智能体像真实业务用户一样操作网页，验证页面是否顺手、是否误导、是否符合业务人员习惯；不是方法层用“像不像真人”作为完成标准。
- 当前实现：新增 `method_absorption_landing_register_20260604.md`、`choice_probability.schema.json`、`simulation_validation_target.schema.json`；扩展 `person_simulation_control.schema.json`、`deepseek_task_contract.schema.json`、`validate_deepseek_contract_output.py` 和 `verify_project_implementation.py`。
- 边界：DeepSeek 可以生成 `choice_probability`、`simulation_validation_target`、`state_behavior_consistency` 候选，但必须 `draft/needs_review`，不得写 checked、final、ROI、最终排名、最终推荐或覆盖用户锁定对象。
- 验证：P4 节点解释契约验证 `status=pass failure_count=0`；交接编码健康 `failures=0`；总实现门禁 `checks=796 failures=0`。
- 后续：继续写任务专用 adapter，并把选择概率与验证目标接入 P6 用户可编辑对象池。

# DEC-075 PowerShell/终端中文乱码已专项治理，不能每轮临时绕

- 日期：2026-06-04
- 决策：对 Windows PowerShell 5.1 中文乱码做一次性治理，而不是每轮临时加 `PYTHONIOENCODING` 或 `-Encoding UTF8`。
- 原因：根因是 Windows PowerShell 5.1 普通 `Get-Content` 默认按 ANSI/GBK 读取无 BOM UTF-8 文件，导致中文 Markdown 显示为 `鑰佹澘...`。项目文件本身不是坏的。
- 当前实现：已更新用户级 profile `C:\Users\Yy199\Documents\WindowsPowerShell\profile.ps1`，保留 conda 初始化，并设置 `[Console]::InputEncoding`、`[Console]::OutputEncoding`、`$OutputEncoding` 为 UTF-8；同时给 `Get-Content/Set-Content/Add-Content/Out-File/Export-Csv` 设置默认 `Encoding=UTF8`。
- 验证：新 PowerShell 会话中 `Console/Input/OutputEncoding=utf-8/65001`、`chcp=65001`；普通 `Get-Content progress.md`、`Get-Content findings.md`、`Get-Content method_absorption_landing_register_20260604.md` 均直接显示中文；交接编码健康 `failures=0`，总门禁 `checks=796 failures=0`。
- 边界：该修复只改用户级 PowerShell profile，不改项目文件编码，不删除 conda 初始化，不影响 `.env` 或项目依赖。

# DEC-072 老板方法资料触发系统级重构，而非缺口补充

- 日期：2026-06-04
- 决策：将 `10_research/boss_method_materials_20260604/full_system_rebaseline_20260604.md` 作为当前最高优先级方法主控文件。老板六份资料和外部论文必须被全盘吸收到证据层、人群潜在状态、行为程序、空间运动、消费选择、运营约束、宏观校准和 UI/报告复核链路中。
- 原因：用户明确纠正此前理解仍偏浅，不能把论文当“缺什么补什么”的参考；仿真工作量和方向已经改变，旧文件中的完成声明可能不再可信。
- 当前处理：旧证据底座可保留；P6 只视为产品壳；P2 persona/behavior/validation CSV 只视为草稿候选；旧 DeepSeek 输出必须 envelope 适配或降级；P4 完整仿真、ROI、最终排序、最终推荐和节点裸分数统一重审。
- 禁止：不得跳过全盘吸收直接补 UI、直接推 GitHub、直接把 DeepSeek 草稿或旧 dry-run 写成仿真完成。
- 下一步：先按主控文件给旧 P2/P3/P4/P6 产物打可信度标签，再做 DeepSeek adapter、人物状态/行为程序 CRUD 和节点解释重构。

# DEC-073 旧 DeepSeek 输出只做 metadata-only envelope 纳管

- 日期：2026-06-04
- 决策：`60_model/llm_runs` 中 35 个旧 DeepSeek 输出统一通过 `60_model/scripts/adapt_deepseek_legacy_outputs.py` 包装为 `source_summary` envelope，状态固定为 `needs_review`，并写入 `60_model/llm_runs/contract_envelopes/legacy_*.json`。
- 原因：旧输出生成于老板方法重基线之前，不符合新契约；但直接丢弃会丢失历史上下文，直接使用又会污染人物仿真和报告判断。
- 边界：这些 envelope 只包装文件元数据，不验证旧内容语义；通过 `validate_deepseek_contract_output.py` 只证明纳入审计，不证明旧 P2/P3/P4 草稿可用。
- 禁止：不得把旧 envelope 当 checked 证据、最终排名、ROI、完整仿真、运营决策或节点最终建议。
- 下一步：若要使用旧内容，必须写任务专用 adapter，重新抽取 `persona_state`、`behavior_program`、`node_explanation` 或 `report_draft`，并通过对应 schema 和本地复核。

# DEC-068 P6 节点判断以推进优先级和建议为主，分数降为辅助解释

- 日期：2026-06-03
- 决策：节点清单和详情主视觉不再突出裸分数，改为显示“推进优先级 + 具体建议”；分数只保留在“优先级解析与建议”中，解释当前资料条件下为什么先推、先补证或暂缓推荐。
- 原因：裸分数会让用户误以为系统已经给出精确定量排名；当前 P3 门禁未闭合，分数只能表示讨论优先级，最重要的是告诉业务方下一步该补什么、怎么推进。
- 当前实现：后端返回 `score_recommendations` 和 `score_breakdown`；前端 `renderScoreAnalysis()` 展示评分用途、当前建议、基础判断、资料门禁、字段缺口、POI 和边界可信度。
- 边界：不得把 `discussion_score_draft` 写成最终选址分、ROI、收益预测或最终排名。
- 后续校验：`node --check`、`py_compile` 和 Selenium 10 轮回归通过；截图 `40_quality_evidence/selenium_visual_integration_20260603/node_priority_visual_after_fix.png`。

# DEC-067 双人 Codex 合并采用只读远端、三方对比和局部吸收

- 日期：2026-06-03
- 决策：同事远端成果不做整仓覆盖；先只读下载 GitHub main 源码包，与本地 HEAD 和当前工作区做三方对比，再按功能块局部吸收。
- 原因：本地已有大量 AI 工作台、报告、视觉、地图兜底、Selenium 证据和交接文档改动；整仓同步会覆盖本地成果并放大冲突。
- 当前实现：已导入同事三份地图/资料/节点验证证据；同事地图/节点/资料链路中可用部分已并入本地，并由本地更严格的视觉和 Selenium 验证覆盖旧结论。
- 边界：远端报告中的旧端口、本机路径、动态 DOM 失败和高德授权失败记录只作为历史证据，不作为当前最终结论。
- 后续校验：融合报告见 `40_quality_evidence/remote_integration_execution_report_20260603.md`。

# DEC-066 P6 空间地图优先使用高德 JS，必要时使用高德静态图兜底

- 日期：2026-06-03
- 决策：空间地图优先使用高德 JS API 展示拖拽、缩放、标记和结果列表；当本地缺少正式 JS Key 安全配置导致底图空白时，使用 `/api/amap/static-map` 返回的高德静态图作为可见底图兜底，同时保留标记和控件。
- 原因：用户明确指出空白地图不可接受；仅凭 `amapReady=true` 或 canvas 存在不能证明用户看到了地图。当前 `.env` 只有 Web Service key fallback，缺少正式 `AMAP_JS_API_KEY` / `AMAP_JS_SECURITY_CODE` 时需要产品级兜底。
- 当前实现：前端预加载静态高德 PNG；在 `using_web_service_key_as_fallback` 或缺少 `security_code` 时显示静态底图，并隐藏空白 JS 瓦片层。
- 边界：底图、POI 和候选节点仍为待复核位置关系，不代表 DWG 坐标、面积、图层或真实动线；不得在代码或报告中泄露完整 Key。
- 后续校验：截图 `40_quality_evidence/selenium_visual_integration_20260603/map_visual_after_fallback.png`；Selenium 10 轮通过。

# DEC-065 P6 供需缺口必须由外部上传资料驱动

- 日期：2026-06-02
- 决策：P6 的 TGI/POI 供需缺口中，TGI 必须来自网页外部上传的客流/TGI资料，POI 来自当前地图上下文高德 POI；未上传项目资料时，方案节点保持空状态。
- 原因：用户明确指出未上传项目的网站应为空，不能一下载项目就把奥森资料当成用户项目；资料应由外部上传，而不是后端自动调用。
- 当前实现：新增 `60_model/simulation/demand_gap.py`、`/api/supply-gap`、`/api/visitor-simulation`、`/api/reports/site-selection`；前端新增“分析报告”页、资料闭合中心缺口面板和节点详情 TGI/POI 缺口块。
- 边界：DWG/DOCX/PDF 上传解析仍只是待复核候选；缺口和报告不得升级为最终推荐、最终排序、收益预测或 checked 证据。

# DEC-064 P6 前端草案评分只消费后端契约字段

- 日期：2026-06-02
- 决策：P6 专家驾驶舱前端不再自行根据 gate、POI、边界和仿真结果重算草案分；前端只展示后端返回的 `discussion_score_draft`、`score_status`、`score_label`、`score_explanation`。
- 原因：员工A/员工B 分工要求后端负责数据闭环和分组逻辑，前端负责展示与专家工作流；重复计算会导致外部地图地点误套奥森节点评分。
- 影响：外部地点统一显示为 `external_preview_only` / 地图预览；节点详情和仿真面板优先展示 `missing_required_fields`、`why_blocked`、`next_data_needed`。
- 边界：该分数仍为 `needs_review / not_final`，不得转写为最终排序、收益预测、ROI 或推荐结论。

# DEC-063 P6 后端契约统一与 dry-run 解释字段

- 日期：2026-06-02
- 决策：员工A后端接口统一返回 `output_status`、`not_final`、`status_label`、`source_hint`、`evidence_hint`，并把节点草案评分和 dry-run 阻塞解释放到后端生成；前端可继续保留旧字段，后续逐步切换到后端字段。
- 原因：前端自行猜字段和计算分数会导致 A/B 职责冲突；dry-run 只返回数量不能解释为什么不能最终化；外部地图搜索地点不能套用奥森训练节点评分。
- 实现：`/api/dashboard` 增加 `api_contract` 和节点评分解释；`/api/data/*`、`/api/uploads`、`/api/upload-candidates`、`/api/simulation/*` 增加统一语义字段；`simulation_results` 增加 `group_context`、`why_blocked`、`missing_required_fields`、`next_data_needed`；上传资料、解析候选和 gate input 同步落 SQLite。
- 边界：后端草案分仅用于讨论，`score_status=external_preview_only` 时只能做地图预览；dry-run 仍不得输出 ROI、收益预测、最终排序或最终推荐。
- 后续校验：本轮 `py_compile`、接口 smoke、AMap tips smoke 和项目总门禁均通过；最新总门禁为 `checks=725 failures=0`。

# 决策日志

| ID | 日期 | 决策 | 原因 | 风险 | 后续校验 |
|---|---|---|---|---|---|
| DEC-001 | 2026-05-22 | 将本目录建设为长期项目工作区，而不是一次性报告目录 | 项目跨多轮、数据多源、需要交接和复跑 | 前期文档量增加 | 新会话能按交接文件继续 |
| DEC-002 | 2026-05-22 | PDF/PPT 样例先用于方法训练，不作为最终目标公园 | 用户明确说明真实目标公园后续再给 | 样例结论不能直接迁移 | 所有样例结论标注为训练样例 |
| DEC-003 | 2026-05-22 | 本地 Python 作为主线，插件作为分工增强 | 数据抽取、建模、复跑更稳定 | 后续可能需要补库 | 缺库时先查官方文档再安装 |
| DEC-004 | 2026-05-22 | PPT 默认弱证据，PDF/GIS/用户原始数据优先 | PPT 常是包装后的方案页，可能含估算 | 可能遗漏 PPT 中有价值信息 | PPT 数字必须回查强证据 |
| DEC-005 | 2026-05-22 | 高德 Key 不写入代码和文档，只用环境变量 | 防止泄露敏感凭据 | 运行前需设置环境变量 | 最终做敏感信息扫描 |
| DEC-006 | 2026-05-22 | 缺口识别采用需求强度、供给覆盖、外溢风险和落地可行性的组合分数 | 单看 POI 数量不专业，无法解释收益 | 初始权重需校准 | 用样例资料和真实项目数据迭代权重 |
| DEC-007 | 2026-05-22 | 原始样例文件统一归档到 `20_raw_data/`，脚本只从标准目录读取 | 防止根目录混乱，保证后续可复跑 | 已移动文件路径，旧路径不再有效 | `data_catalog.csv` 已记录新路径 |
| DEC-008 | 2026-05-22 | 第一批证据入账使用可复跑脚本生成，并把 PDF 指标和 PPT 假设分开标注 | 便于追溯来源，避免手工复制和强弱证据混淆 | 脚本规则仍是首批人工规则，覆盖面有限 | 后续扩展第二批指标时继续复核脚本和台账 |
| DEC-009 | 2026-05-22 | PPT 假设复核单独输出 `ppt_assumption_review.csv/md`，不把部分支持直接升级为事实 | PPT 中存在口径混用和供给数量冲突，直接改成事实会污染结论 | 需要额外文件维护核验状态 | 后续用高德 POI、现场清单和经营数据逐项闭合 |
| DEC-010 | 2026-05-22 | PPT 假设后续只作为可选线索，必要时可直接无视 | 现有 PPT 假设质量不足，继续围绕 PPT 验证会拖慢证据链建设 | 可能遗漏 PPT 中少量有用线索 | 只吸收能被 PDF/GIS/经营数据支持的内容 |
| DEC-011 | 2026-05-22 | 供给底表采用“两层口径”：PDF 区域内热门到访 POI 只作种子，高德/现场核验后才升级为有效供给 | PDF 热门到访表不是完整商户清单，但可作为高德核验的起点 | 初版供给数量可能低估或含非园内点位 | 用高德 POI 坐标、距离、边界和营业状态补齐 |
| DEC-012 | 2026-05-23 | 接入 DeepSeek 作为低成本批处理辅助模型，Key 只读 `DEEPSEEK_API_KEY` 环境变量 | 用户希望降低 GPT-5.5 成本，把简单或量大的任务交给 DeepSeek | 模型输出可能幻觉或污染证据链 | DeepSeek 输出只允许为 `draft/needs_review`，正式入账必须本地脚本和 Codex 复核 |
| DEC-013 | 2026-05-23 | 将 LLM 任务细分写入 `llm_task_routing.csv`，按风险和量级选择执行者 | 防止“什么都交给便宜模型”导致关键结论不可靠 | 路由表需要随项目迭代更新 | 每次新增模型任务时先写路由，再执行 |
| DEC-014 | 2026-05-23 | `tech-shrimp` 仓库先做盘点和许可证评估，不直接导入远程仓库 | 当前 GitHub 插件初始化失败，且用户未提供目标仓库；外部仓库导入涉及许可证和来源保留 | 用户期望“全部拿进仓库”，可能需要后续确认目标仓库 | 等目标仓库 `owner/name` 和 GitHub 权限可用后，用 vendor/submodule 策略执行 |
| DEC-015 | 2026-05-23 | 用 GitHub 原生 fork + 索引仓库归档 `tech-shrimp` 资源，不把外部源码混入仿真项目主线 | 用户授权继续打开/使用 GitHub 权限；fork 能保留 upstream 关系，索引仓库能集中记录用途和许可证 | 1 个仓库因 GitHub HTTP 451 失败；fork 不等于本项目依赖 | 后续只从 MIT/Apache-2.0 且确实有用的仓库中提炼最小可用模式 |
| DEC-016 | 2026-05-24 | 将 `verify_project_implementation.py` 作为每阶段结束前的落实性门禁 | 用户要求确认每一步真实落地且无明显 bug；手工口头确认不够可靠 | 验证脚本本身也可能漏检，需要随项目演进更新 | 每次新增关键文件、外部操作或模型任务时同步扩展验证脚本 |
| DEC-017 | 2026-05-25 | 本地 `.env` 保存运行凭据，主 agent 管理、DeepSeek Pro 执行低风险批量任务 | 用户明确希望 GPT-5.5 作为管理者，把简单或量大任务交给 DeepSeek；同时要求 Key 交接可用 | `.env` 泄露会造成凭据风险，DeepSeek 输出可能被误用 | `.env` 已加入 `.gitignore`；验证脚本允许 `.env` 有 Key 但禁止其他文件泄露；DeepSeek 输出必须为 draft/needs_review |
| DEC-017 | 2026-05-25 | 高德候选表先做“空间预过滤”，不把中心距离或文本命中当作最终园内边界判定 | 当前没有真实公园 polygon、入口节点或现场清单；直接判定园内会污染后续缺口计算 | 预过滤可能误分园内外，只能用于排序复核优先级 | 所有预过滤记录保持 `do_not_use_as_in_park_supply_yet`，补真实边界或现场核验后再升级 |
| DEC-018 | 2026-05-25 | P1 阶段可用 OpenStreetMap/Nominatim polygon 做公开地图边界过滤，但必须记录 OSM attribution、坐标系转换和非官方边界限制 | 当前缺少官方边界，OSM 能提供可复跑公开 polygon，能明显改进高德候选园内/周边初筛 | OSM 非官方规划红线，高德 GCJ-02 到 OSM WGS84 转换有近似误差 | `inside_osm_polygon` 只能作为边界过滤候选，仍需现场营业、路径可达和运营授权核验 |
| DEC-019 | 2026-05-25 | P0 园内候选可先用“高德公园中心点代理路径”做可达性初筛，但不得等同于真实入口/节点路径 | 当前缺少真实入口、停车场、地铁站和游线节点；中心点代理能先发现明显不可达风险 | 中心点代理可能高估或低估真实游客步行距离 | 路径结果标记为 `amap_center_proxy_route_returned_needs_entrance_validation`，进入 P2 前必须补真实入口/节点或现场核验 |
| DEC-020 | 2026-05-25 | DeepSeek 可承担 P1 表格分类和证据候选抽取的慢速批处理，但只产出 `draft/needs_review`，不直接入账 | 用户明确允许 DeepSeek 长时间运行；329 张表和 P0 表格候选适合低风险重复抽取 | DeepSeek 可能误抽、漏抽或把热门到访误当完整供给 | 用本地复核队列、PDF 原表回查和 `verify_project_implementation.py` 门禁控制；第二批入账必须由 Codex/Python 确认 |
| DEC-021 | 2026-05-25 | 第二批证据入账只采用本地脚本按 PDF 原生表头和原始行确认的画像/消费/TGI指标 | DeepSeek 候选中存在误分类，如把出游月份覆盖度当 time_peak；直接入账会污染证据链 | 第二批仍可能受 PDF 双栏抽取结构影响，且画像指标可能被误解释为客流或供给 | `second_evidence_ledger_review.csv` 记录新增/跳过；报告引用前抽样看原 PDF；画像指标不得当作客流峰值、供给数量或收益 |
| DEC-022 | 2026-05-25 | P0 路径核验从“公园中心点代理”扩展到“高德入口/节点代理”，但仍不作为最终入口或供给结论 | 中心点代理路径过粗，入口/停车场/园内节点能更接近游客访问路径 | 高德文本搜索返回的节点可能是停车场、场馆、站点或非官方入口，仍可能误导 | 入口/节点路径只用于 P1 代理核验；`can_enter_p2_supply_after_entrance_route` 保持 `no`，后续需官方/现场入口和运营授权 |
| DEC-020 | 2026-05-25 | 最终仿真路线采用“本地 Python 计算 + DeepSeek 辅助判断”，先写入计划，暂不落实代码 | 用户希望接入 DeepSeek 判断，同时保留可复跑、可解释、可审计的仿真计算 | DeepSeek 可能把假设说成事实，或替代模型结果做最终判断 | P2 只让 Python 做概率原型；DeepSeek 只产出 `draft/needs_review` 场景和解释，最终排序、收益和结论必须由证据链与本地计算复核 |
| DEC-021 | 2026-05-25 | 人群需求必须进入概率仿真路线：P2 做分群/选择概率原型，P4 再做游客 Agent 仿真 | 单纯供需公式不能解释人的差异、突发购买、场景触发和个性化需求 | 参数不足时复杂仿真会伪精确 | 先建 persona、需求触发、概率参数、随机种子和敏感性分析；没有校准数据时只输出假设场景 |
| DEC-022 | 2026-05-25 | Postman 放在 P2 的 API 契约规划和 P4 的仿真 API 回归测试中，P1 不作为主线落实 | 用户希望接入 Postman，但当前仍在 P1 证据链阶段，过早落实会分散主线 | collection 或环境文件可能泄露 Key，或把工具测试误当证据 | Postman 只保存变量名和脱敏参数摘要；真实 Key 仍从 `.env`/环境变量读取；优先 Postman CLI，Newman 仅作兼容备选 |
| DEC-023 | 2026-05-25 | 最终交付新增 P6“专家网站化交付”，把模型、地图、证据、场景和报告变成行业专家可交互使用的网站 | 用户明确提出最终需要一个网站来使用这些成果，且面向行业专家 | 过早建站会包装不稳定结论，或把视觉效果误当分析能力 | P1-P5 先稳定证据、模型和结论；P6 再做专家决策驾驶舱、GIS 地图、场景实验室和导出验收 |
| DEC-024 | 2026-05-25 | 专家网站第一屏采用决策驾驶舱，不采用营销落地页或泛泛 hero | 行业专家需要快速看推荐、证据完整度、风险、参数和可追溯链路 | 如果按普通官网做，会降低专业可信度和复核效率 | 第一屏必须展示项目对象、推荐排序、收益/风险区间、证据状态和主要待核验项 |
| DEC-025 | 2026-05-25 | Flowus 学到的“去 AI 味”方法只作为设计流程，不替代证据链和模型门禁 | Flowus 页面强调人定义灵魂、AI 辅助生成、用真实素材和动效提高质感；这适合 P6 网站设计 | 直接照搬参考网站可能偏离公园商业选址专家场景 | 后续流程采用灵感参考 -> 人定义专家工作流 -> 原型 -> AI 辅助实现 -> 浏览器验证 -> 专家验收 |
| DEC-026 | 2026-05-26 | 将 P6 网站建议单独沉淀为 `00_control/p6_expert_website_design_brief.md`，未来进入 P6 前必须读取 | 用户明确指出本轮是建议讨论而非实践，需要把学到的东西提炼成后续可调用文档 | 如果只留在聊天记录里，后续实现容易遗漏 Flowus 学习、专家定位和非营销页边界 | `task_plan.md`、`progress.md`、`handoff_next_chat.md` 和 `next_chat_prompt.md` 均记录该文档入口 |
| DEC-027 | 2026-05-26 | DeepSeek 可对 P0 入口/节点候选做语义初筛，但最终访问节点门禁必须由本地规则、Codex 和官方/现场核验决定 | 45 条高德入口/节点候选属于低风险批量语义归类任务，适合交给 DeepSeek 节省人工筛查时间 | 高德文本搜索节点可能是停车场、场馆、商业点、园内设施或暂停营业点；DeepSeek 可能误把上下文节点当入口 | LLM-011 输出只允许 `draft`；20 条 P0 候选和 7 条次级候选均需官方/现场确认，18 条低置信候选在人工复核前不得使用；`can_enter_p2_supply` 继续保持 `no` |
| DEC-028 | 2026-05-26 | 为节约主模型用量，DeepSeek 可接收更完整的项目上下文并承担 P0 核验包等繁琐整理任务，但凭据仍由本地脚本读取和封装 | 用户明确希望把大量简单功能交给 DeepSeek，并允许其了解项目上下文；P0 工作单、入口节点和现场问题整理适合低风险批处理 | 若直接投喂真实 `.env` 内容或让模型自由处理 Key，raw 输出和交接文件可能被凭据污染 | DeepSeek 可读取交接文件、证据台账和中间表；真实 Key 不作为 prompt 内容发送，仍由本地 Python 从 `.env`/环境变量读取；LLM-012 输出为 `needs_review`，P2 门禁固定不放行 |
| DEC-029 | 2026-05-26 | 默认采用 DeepSeek-first：中等难度和门禁预审也先交给 DeepSeek，Codex 主要负责指挥、计划、本地执行和最终可复跑门禁 | 用户明确希望降低 Codex 本体使用量，Codex 不应继续亲自做大量实现和审查 | 如果完全用 LLM 口头判断门禁，结果不可复跑且难以追踪 | LLM-013 负责项目上下文同步和任务分解；DeepSeek 可做门禁预审和失败解释，但通过/失败仍用本地脚本 exit code、行数、字段和状态门禁固化 |
| DEC-030 | 2026-05-26 | P0 经营字段局部补齐不放行 P2，仍需入口/节点和运营授权闭合 | DS-FIRST-002 已补齐部分高德经营字段，但 P0 仍存在真实入口/节点和运营授权阻塞项 | 若把字段补齐误解为供给确认，会提前污染 P2 缺口计算 | `poi_supply_p0_followup_worklist_enriched.csv` 的 `can_enter_p2_supply` 保持 `no`；DS-FIRST-003 生成现场核验清单，最新落实性验证纳入该门禁 |
| DEC-031 | 2026-05-26 | P1 后续不再循环追补缺失经营字段，空值保留并以现有数据继续推进 | 用户指出继续追补会让流程陷入循环；当前目标是完成本段整理和质量报告，而不是把所有字段补齐 | 空值会降低部分估算精度，需要在报告和模型输入中明确标注 | DS-FIRST-004 质量报告必须列出空值和待核验项；后续模型按空值/缺失处理，不再因单个经营字段缺失阻塞当前段 |
| DEC-032 | 2026-05-26 | 项目级落实性验证升级到 `implementation_verification_20260526.*`，并把 `LLM-016`/P1 质量报告草稿链路纳入 360 项全量门禁 | DS-FIRST-005 需要确认 DS-FIRST-004 未引入回退，同时把最新任务队列和草稿复核文件纳入项目级门禁 | 若验证报告继续沿用旧文件名或遗漏新链路，会导致阶段收口缺少可复跑证明 | `verify_project_implementation.py` 已覆盖 `LLM-016`、新草稿/复核文件和最新队列；最新结果为 360 项检查全部通过 |
| DEC-033 | 2026-05-26 | 历史 `implementation_verification_*` 报告不再参与当前轮次的 mojibake 占位符扫描 | 历史验证报告会反射旧扫描结果，若继续参与当前扫描，会把旧产物中的占位字符串误判为新故障 | 若豁免范围过大，可能掩盖真实乱码问题 | 目前仅豁免 `40_quality_evidence/verification/implementation_verification_*` 自生成历史报告，其余文本文件仍继续扫描 |
| DEC-034 | 2026-05-26 | 将当前阶段状态正式记为“P1 已收口/阶段完成，但当前不进入 P2” | P1 草稿、复核、任务队列和 20260526 全量门禁都已完成，且用户明确要求不要再为缺失字段反复追补 | 若误解为“可直接进入 P2”，会把未闭合入口/授权事项带入后续阶段 | 真实入口/节点、运营授权和部分经营字段继续保留为待核验清单；后续若要继续推进，先询问用户方向，不擅自进入 P2 |
| DEC-035 | 2026-05-26 | P1 收口后的低中风险整理继续默认 DeepSeek-first，P2 启动与主线建模保留给 Codex / 高能力主 agent | 用户明确提出不着急进入 P2，希望继续降低 Codex 消耗，但等真正进入 P2 时仍由 Codex 主导 | 如果把“多用 DeepSeek”扩展到 P2 启动和主线建模，可能会弱化阶段判断和最终门禁 | P1 收口后的待核验清单整编、交接细化、失败原因分析继续优先 DeepSeek 或本地脚本；P2 只有在用户明确要求时才启动 |
| DEC-036 | 2026-05-26 | Windows/PowerShell 中禁止沿用 Bash heredoc 和中文路径内联拼接，P2 准备改到新对话启动 | 本轮卡住的直接原因是 `py - <<'PY'` 不适配 PowerShell，且中文路径在命令传递链路中可能被替换为问号占位 | 若继续在当前对话强行跑 P2，容易留下半成品和混乱交接 | 已删除未执行的 P2 半成品脚本；新对话先复跑 `verify_project_implementation.py`，再用相对路径/本地脚本处理 CAD 与策划资料 |
| DEC-037 | 2026-05-26 | P2 启动先限定为真实资料准备索引：DOCX/PDF 可抽取为待复核输入，DWG 在无可信转换产物前保持 `pending_conversion`，PPT 不进入 P2 主线 | 用户明确要求新对话开始 P2 准备但不要直接跑完整仿真；当前资料包能支持目标/策划/节点/场景假设拆解，但不能直接支撑几何、客流、收益和成本仿真 | 若把 PDF 标签或 DWG 文件存在性误读成几何解析，会污染后续空间模型；若用 PPT 默认回填，会把弱假设带入 P2 主线 | `build_p2_real_site_input_index.py` 和 8 个 P2 准备产物已纳入 `verify_project_implementation.py`；当前门禁为 `checks=392 failures=0`，DWG 解析前不得生成面积/图层/坐标/动线结论 |
| DEC-038 | 2026-05-28 | P2 准备继续推进到 DeepSeek 语义拆解：DOCX 形成项目/业态/场景假设草稿，PDF 形成空间标签草稿，但全部保持 `needs_review` | 用户明确指出 P2 准备不能停在索引层，需要开始操作并落实方案和图纸内容；DOCX/PDF 文本适合低风险语义拆解 | DeepSeek 可能把方案假设写成事实，或把 PDF 文本标签误当几何；若不设门禁会污染 P2 输入 schema | 新增 LLM-017、运行/复核脚本和两个草稿表；本地复核 12 项通过，最新 `verify_project_implementation.py` 为 `checks=422 failures=0`；DWG 仍 pending_conversion，PPT 不进入主线 |
| DEC-039 | 2026-05-28 | P2 准备可把 DeepSeek 语义草稿转为结构化输入 schema 候选表，但关键缺口域和最终门禁必须由本地规则固定 | 用户要求继续进入 P2 操作并尽量多用 DeepSeek；项目节点、业态/场景假设、空间标签和输入缺口适合 DeepSeek 先整理为可复核候选表 | DeepSeek 可能把 `conversion_rate`、`revenue_cost`、`operation_authorization`、`model_gate` 等关键仿真门禁泛化改名，导致后续 schema 缺口被吞掉 | 新增 LLM-018、4 张候选输入表和本地复核脚本；本地归一化固定 10 个缺口域，20 项复核通过；该轮门禁结果已被 DEC-040/041 的最新全量门禁覆盖；全部输出仍为 `needs_review`，不直接跑完整仿真 |
| DEC-040 | 2026-05-28 | P2 按方法原型口径闭环，P3 真实校准和 P4 完整 Agent/GIS 仿真仍未开始 | `task_plan.md` 对 P2 的定义是方法原型、概率选择原型、第一版公式、persona/场景参数和 API 契约草案；用户要求一口气推进 P2，但当前仍缺 DWG 几何、真实客流、转化率、收益/成本和运营授权 | 若把 P2 方法原型误写成完整仿真，会污染最终选址结论；若把候选评分当最终排序，会误导交付 | 新增 LLM-019 审计、5 张 P2 方法原型表、P2 方法报告和本地复核；该轮门禁已被 DEC-042 最新全量门禁覆盖；所有 P2 方法原型输出仍为 `needs_review` |
| DEC-041 | 2026-05-28 | 交接文件和 Agent 阶段口径纳入健康门禁，防止乱码占位和旧 P2 状态再次造成误会 | 用户明确担心大项目中因文件未更新、历史乱码或旧交接导致后续 agent 误解 | 若只在聊天里说明，不写入门禁，后续仍可能回到“P2 暂不启动”或把问号占位误判为真实路径/乱码 | 新增 `review_handoff_and_encoding_health.py` 和 `handoff_encoding_health_review.csv/md`；`AGENTS.md`、`task_plan.md`、`progress.md`、`findings.md`、`handoff_next_chat.md`、`next_chat_prompt.md`、`decisions.md` 均纳入检查 |
| DEC-042 | 2026-05-28 | P2 完成真实性必须有专项审计，不只依赖总门禁或聊天结论 | 用户要求仔细检查 P2 是否真的完成，以及 DOCX/PDF/DWG 这些真实资料是否已经写入；同时担心交接文件和乱码残留造成误会 | 若只看旧 gate 或只在聊天里回答，后续 agent 仍可能误解为资料未落实、P2 未完成或完整仿真已完成 | 新增 `review_p2_completion_reality.py` 和 `p2_completion_reality_audit.csv/md`，41 项全部通过；新增 LLM-020 DeepSeek 覆盖细审，60 行矩阵、本地复核 33 项通过；该轮门禁已被 DEC-043 最新全量门禁覆盖 |
| DEC-043 | 2026-05-28 | 图纸代理与DWG转换前置优先交给 DeepSeek 草稿审计，本地脚本只固定边界和门禁 | 用户明确要求尽可能使用 DeepSeek 处理几何解析/PDF代理等重活，减少 Codex 本体消耗；但当前没有可信 DWG 转换器或 DXF/GeoJSON 导出 | 若让 DeepSeek 直接声称 DWG 几何解析，会制造虚假坐标、面积、图层和动线；若完全不处理图纸代理，又浪费用户提供的重要资料 | 新增 LLM-021，生成 10 行 PDF 代理分区、8 行 DWG 转换工作单、8 行几何代理限制；本地复核 23 项通过，DWG 统一保持 `pending_conversion`；最新全量门禁为 `checks=589 failures=0` |
| DEC-044 | 2026-05-28 | P3 对 P4 完整仿真结论构成硬前置，但 P4 骨架/API/测试/配置可与 P3 并行准备 | P3 的 DWG 转换边界、真实客流、转化率、收益成本、运营授权和模型放行门禁会决定 P4 仿真可信度；用户要求先确认路线并执行 P3 前置，同时尽可能多用 DeepSeek | 若把 P4 并行准备误解为可提前运行完整仿真，会产生虚假排序、收益预测、坐标面积推断或最终推荐 | 新增 LLM-022、P3/P4 路线表、DWG 转换工作单、校准数据需求表、P2 到 P3 映射表和 P4 骨架清单；所有输出为 `needs_review`，DWG 仍为 `pending_conversion`；最新总门禁为 `checks=635 failures=0` |
| DEC-045 | 2026-05-28 | P3 当前闭合到“校准执行包准备完成、等待真实来源”的稳态，而不是宣称真实校准完成 | 用户希望一口气推进 P3，但当前没有新增真实客流、转化率、收益成本、运营授权或可信 DWG 转换产物；继续伪推进会污染 P4 | 若把执行包误写成校准完成，会导致 P4 提前输出虚假排序、收益预测或空间结论 | 新增 LLM-023、P3 证据请求/验收标准/假设边界/阻塞项/gate 状态表和本地复核；所有输出保持 `needs_review`，核心 gate 仍未 closed/passed |
| DEC-046 | 2026-05-29 | 回滚其他 AI 生成的 P4 完整仿真产物，保留 P4 仅可做 skeleton/API/mock tests/config 的边界 | 外部 P4 在 P3 gate 未闭合时生成 ROI 排名、收益预测、推荐优先级和 P4 完成总结，违反 P3 是 P4 结论硬前置的项目规则 | 若保留这些产物，会污染后续报告、排序和财务判断；若无记录删除，后续 agent 可能重复生成 | 新增 LLM-024 DeepSeek 审计，结论 `decision=rollback`；删除不合格 P4 脚本和输出，并将其缺席纳入总门禁，最新结果 `checks=690 failures=0` |
| DEC-047 | 2026-05-29 | 允许基于现有资料生成 P4 feedback draft，但不得写成 checked/final 完整仿真结论 | 用户澄清最开始提供的策划书/CAD/PDF 资料足以支撑反馈草案；缺失数据可以保留为空或占位，先让合作方看到草案并补数据 | 若继续禁止所有 P4，会阻塞反馈闭环；若把反馈草案写成最终结论，则污染正式选址判断 | 新增 LLM-025 和 P4 feedback draft 三张表，本地复核 17 项通过；输出必须保持 `needs_review`、`feedback_draft_not_final_ranking` |
| DEC-048 | 2026-05-29 | P6 先落地为本地 FastAPI + 静态前端专家决策驾驶舱，而不是营销页或完整最终系统 | 用户当前最需要的是可操作网页模型，用于展示和操作公园商业选址方案；现有 P2/P4 feedback draft 和 P3 gate 足以支撑原型 | 若做成营销页会偏离专家使用；若包装成最终系统会污染 P4/P5 结论 | 新增 `90_p6_expert_dashboard/`，页面读取真实 CSV，浏览器截图验证，最新总门禁 `checks=725 failures=0` |
| DEC-049 | 2026-05-29 | 项目级总门禁默认检查既有 DeepSeek 产物，不再每次重跑所有 `run_deepseek_*` 脚本 | P4 feedback draft 后全量门禁曾因 DeepSeek 重跑链过长超时；用户要求优先检查既有产物、减少不必要重跑 | 若默认不重跑，可能漏掉上游 prompt 变化后的再生成差异 | `verify_project_implementation.py` 默认跳过 DeepSeek 重生成，设置 `VERIFY_RERUN_DEEPSEEK=1` 才强制重跑；本轮总门禁 `checks=725 failures=0` |
| DEC-050 | 2026-05-29 | P6 页面按用户参考图重构为密集型专家决策平台，并把 AI 入口固定为可连续对话的专家反馈栏 | 用户明确指出早期页面与概念图差距过大，且未来会持续提供位置图、真实反馈数据和专家意见；系统必须支持专家像使用 DeepSeek/豆包网页版一样输入意见并推动模型假设修改 | 若只做静态摘要或营销式页面，专家无法有效反馈；若把 AI 输出包装成结论，会违反 P4 feedback draft 边界 | `90_p6_expert_dashboard/static/index.html`、`styles.css`、`app.js` 已重构；`POST /api/ai/chat` 已真实调用 DeepSeek 并返回 `needs_review`；Chrome 截图 `qa_reference_style.png` 验证；总门禁 `checks=725 failures=0` |
| DEC-051 | 2026-05-29 | P6 的地图与 AI 对话能力采用“后端代理 + 左侧独立专家工作台”方案 | 用户明确指出页面应更接近参考图的专家决策平台，并且 AI 入口应像 DeepSeek/豆包网页版一样可持续对话；同时 AMap Key 不能暴露在前端 | 若前端直连高德会泄露 Key；若 AI 只做右侧摘要，专家无法持续反馈；若地图失败无兜底，页面会出现无效空白 | `90_p6_expert_dashboard/app.py` 已提供 `/api/amap/static-map` 后端代理和 SVG 兜底；`static/index.html`/`app.js` 已提供左侧“专家 AI 工作台”；验证结果为 `/api/dashboard status=200 nodes=6 amap_points=60`、总门禁 `checks=725 failures=0` |
| DEC-052 | 2026-05-29 | PPTX 图片可作为 P6 视觉素材候选，但不得作为节点实景或 checked 证据 | 用户指出项目资料中应该有图片；检查发现 PPTX 内有 media 图片，可用于提升原型视觉可信度 | PPT 图片可能是概念图或包装图，若误写成真实节点图片会污染证据链 | 已抽取 9 张图片到 `90_p6_expert_dashboard/static/assets/ppt_media/`，页面标注“PPT 素材候选 / 仅作视觉参考”；所有结论边界仍为 `needs_review / not_final` |
# DEC-053 P6 员工 B 可操作驾驶舱优先

- 日期：2026-06-01
- 决策：P6 当前优先服务“员工 B”使用场景，即策划/公园专家可通过鼠标点击和文字输入完成节点查看、地图查看、补数据、AI 对话和专家意见记录。
- 约束：首页不放 P3 gate 流程条；复杂闸门和接口状态放入单独页面；提示必须可点击跳转，不得只是静态说明。
- 实时性：原型阶段采用保存/发送后刷新 dashboard + 页面可见时 60 秒轮询；正式阶段可由员工 A 或后续任务升级为 SSE/WebSocket。
- 边界：P4 feedback draft、DeepSeek 输出、AMap POI 示意仍为待复核草案，不得升级为最终推荐、最终排序、最终收益预测或 checked 证据。

# DEC-054 P6 接口真实性标注

- 日期：2026-06-01
- 决策：P6 页面必须显式标注数据/API 真实接入状态，区分本地 CSV 真读取、DeepSeek 后端代理、AMap POI 历史抓取表、AMap 静态图代理和兜底 SVG。
- 原因：用户指出此前“看起来接入但不确定是否真实”，容易误导专家。
- 当前事实：`/api/integration/status` 已提供状态；AMap 静态图当前返回非图片状态 `USER_KEY_RECYCLED`，因此只能显示本地兜底底图，不宣称真实高德底图已成功渲染。
- 安全：真实 Key 继续只允许从 `.env` 或环境变量由后端读取，不进入前端、JSON、Markdown、日志或交接文件。

# DEC-055 P6 上传优先与可部署路线

- 日期：2026-06-01
- 决策：P6 后续按“上传资料驱动”的专家工具推进，而不是把训练资料和节点写死在前端。网页上传方案、图纸、图片和数据表后，进入待解析资料池，再由 AI 生成待复核节点/点位/缺口候选，最后由人工确认。
- 原因：用户明确要求未来专家和合作方会现场上传位置图、方案和真实数据；系统必须让不会复杂后台操作的人通过鼠标和文字完成工作。
- 当前实现：已新增 `资料导入` 页面、`/api/uploads`、`/api/gate-inputs`，并自动列出 `CAD图及其计划` 中的既有 PDF/DWG/DOCX。
- 风险：上传入口完成不等于文件解析和几何转换完成；DWG 仍必须保持 `pending_conversion`，直到有可信 DXF/GeoJSON/SVG/PDF 导出和人工复核。
- 后续校验：下一阶段需要补齐上传后 AI 解析、候选入池、人工复核、状态实时更新和可部署架构。

# DEC-056 P6 高德地图安全接入边界

- 日期：2026-06-01
- 决策：P6 不能把高德 Web Service Key 直接下发到前端。若要实现接近高德地图的拖拽/缩放交互，应采用浏览器端受限 JS Key + 安全密钥代理，或继续由后端代理地图能力。
- 原因：用户希望地图接近高德/百度/苹果地图体验，但项目已有安全规则要求真实 Key 只在 `.env` 或环境变量中读取。
- 当前事实：旧 Key 曾返回 `USER_KEY_RECYCLED`；2026-06-01 用户提供的新 Web Service Key 已按规则放入本地 `.env`，后端 `/api/amap/static-map` 已返回 `image/png` 静态图。该事实只代表静态图代理可用，不代表高德 JS 交互地图已完成。
- 风险：若用无效或类型不匹配的 Key，地图仍会降级；若把服务端 Key 放前端，会造成凭据泄露。
- 后续校验：更换/申请有效 Key 后，必须用浏览器截图和接口状态共同确认真实地图渲染、拖拽、缩放和图层切换可用。

# DEC-057 P6 重构必须研究先行

- 日期：2026-06-01
- 决策：P6 后续涉及 AI 工作台、地图、上传闭环、专家资料闭合等重要交互时，必须先写研究/审计记录，再实现页面，不允许继续凭感觉叠加按钮和提示词。
- 原因：用户明确指出当前界面质感和交互不像成熟 AI/地图平台，很多交互无意义且写死。
- 当前实现：新增 `00_control/p6_ai_map_interaction_research.md`，记录已查看资料、访问限制、应复制模式、应删除交互和下一步实现优先级。
- 后续校验：每次完成重要交互重构后，必须提供浏览器截图、接口状态和项目门禁结果。

# DEC-058 P6 AI 工作台采用单 Composer

- 日期：2026-06-01
- 决策：专家 AI 工作台采用单一 Composer：一个输入框承载文字、位置描述、专家意见和附件上传；发送时自动登记待复核专家输入并调用 DeepSeek。
- 原因：成熟 AI 产品通常不让用户在多个输入框、提示词按钮和保存/发送按钮之间做选择；用户明确要求像 Codex/DeepSeek 公共平台一样使用。
- 当前实现：已删除独立位置说明框、提示词按钮和保存专家意见按钮；新增附件选择、附件 chip、Enter 发送、Shift+Enter 换行、发送即保存。
- 边界：所有 AI 输出仍为 `needs_review / not_final`，不得进入 checked/final 结论。

# DEC-059 P6 地图上下文必须随项目地点变化

- 日期：2026-06-01
- 决策：P6 地图不能写死奥森中心点。用户或上传资料改变项目地点时，应通过高德服务更新地图中心、静态底图和上下文 POI。
- 原因：最终系统会被用于不同公园/不同方案位置；地图若固定在奥森，会让专家误判。
- 当前实现：新增 `POST /api/amap/context`，用高德关键字查询更新 `map_context.json`；同时调用高德周边查询写入 `map_context_pois.json`。
- 边界：当前仍是高德静态底图 + 自定义交互层，不是完整高德 JS API；所有 POI 均为 `needs_review`。

# DEC-060 P6 上传解析候选需人工确认入池

- 日期：2026-06-01
- 决策：上传资料或内置资料经 AI 解析后，只能生成待复核候选；必须人工确认后才写入资料闭合输入池。
- 原因：用户希望上传方案和位置资料后生成点位/数据，但项目真实性规则要求 AI 不得直接形成 checked 证据或最终结论。
- 当前实现：新增 `/api/uploads/{upload_id}/parse` 与 `/api/upload-candidates/{candidate_id}/confirm`；确认后写入 P3 gate input，状态仍为 `needs_review / not_final`。
- 边界：PDF/CAD 文本解析不能替代 DWG 可信转换，不能生成坐标、面积、图层或动线结论。
# DEC-061 P6 地图轮廓采用通用公开 polygon / POI 外包线策略

- 日期：2026-06-01
- 决策：P6 地图搜索不针对单一公园写死。任意地点搜索后，后端先用高德 Web Service 更新中心点与周边 POI，再按“既有 OSM polygon -> Nominatim 实时 polygon -> 高德周边 POI convex hull -> 可见范围估算”的顺序生成地图范围层。
- 原因：用户明确指出圆形范围和样例化搜索不符合地图产品使用习惯；未来项目地点会变化，系统必须随任意搜索词动态响应。
- 实现：新增 `map_boundary.json` 缓存；公开 OSM polygon 做 WGS84 -> GCJ-02 近似转换后叠加到高德静态底图；无 polygon 的非公园/片区搜索使用 POI 点云外包线作为讨论范围。
- 风险：OSM/Nominatim polygon 不是官方规划红线；POI hull 只是讨论外包线，不是边界；GCJ-02 转换存在近似误差。
- 边界：页面必须标注“公开轮廓/讨论范围外包线 · 待复核”；不得据此输出 DWG 坐标、面积、图层、动线、最终推荐或 checked 证据。

# DEC-062 P6 GitHub 同步与评分口径

- 日期：2026-06-01
- 决策：团队协作时先从 GitHub 同步伙伴更新，合并后再完成本轮地图/评分修正，验证通过后再推回仓库；不得上传半成品运行缓存或截图。
- 原因：伙伴已新增数据库层和 simulation dry-run API，P6 不能继续只展示固定 CSV 分数；同时用户要求团队内部通过 GitHub 协作。
- 实现：保留伙伴 `60_model/db`、`60_model/simulation` 和 `/api/simulation/jobs` 能力；P6 前端显示“实时草案分”，结合 P3 gate、dry-run 缺口、POI 数量和边界状态扣分。
- 边界：实时草案分只在奥森项目上下文显示；外部地点搜索只作为地图预览，不套用奥森评分。dry-run 仍为 `needs_review / not_final`，不输出 ROI、收益预测或最终排序。

# DEC-063 双人 Codex 泳道协作

- 日期：2026-06-02
- 决策：团队协作按“数据与后端契约、专家工作台与交互、证据链与门禁、真实校准/P3 输入、GitHub 同步与发布”五条泳道分工，而不是固定老派前后端人肉分工。
- 原因：双方都有 Codex，适合让每个人带一个 agent 负责完整泳道的设计、实现、验证和交接；固定前后端切分容易造成接口重复计算、评分口径冲突和同步混乱。
- 当前落实：新增 `00_control/team_codex_division.md`；本地已同步到 `d43db1c60f9976f04399de43058d1ee36378a65f`，并补齐 `requirements.txt` 中缺失的 `python-multipart==0.0.30`。
- 边界：跨泳道修改必须写清原因和验证命令；发版者必须跑 JS 语法、Python 编译和 `verify_project_implementation.py`，且不得提交 `.env`、运行日志、无关缓存或半成品截图。

# DEC-064 GitHub 同步必须工具化兜底

- 日期：2026-06-02
- 决策：新增 `00_control/sync_from_github_main.ps1` 作为每轮同步入口，优先普通 `git fetch/reset`，再用 `gh auth token` 认证 fetch，最后才用 GitHub ZIP 镜像兜底；同步后自动安装 `requirements.txt` 并运行最小项目门禁。
- 原因：本机普通 HTTPS fetch 偶发不稳，手工 `gh api` 重定向 ZIP 曾破坏二进制；若不工具化，文件越多越容易留下半同步状态。
- 安全：脚本保留 `.git` 和本地 `.env`，不把真实凭据写入仓库；ZIP 兜底会校验 `50 4B 03 04` 文件头后再解压。
- 边界：若 ZIP 兜底触发，文件层可同步，但 Git 元数据仍建议后续重新跑 fetch；正常协作优先以 `git fetch/reset` 成功为准。

# DEC-065 GitHub main b75396b 只读比较后选择性吸收

- 日期：2026-06-04
- 决策：对远端 `b75396b66c5988ba3640b8060660a8f2b7d7cdb8` 不做全量镜像覆盖，只吸收低冲突且能增强本地工作流的部分：上传用途归一化、节点草案去重、报告按钮状态联动。
- 原因：远端 29 个改动文件全部与本地改动重叠；本地已经有更成熟的 AI 工作台、报告语言、地图兜底、节点优先级解析和 `checks=725 failures=0` 门禁。全量覆盖会回退用户已指出并修过的问题。
- 保留本地胜出项：`prepareStaticBasemap`/`fallback-tiles` 地图兜底、`score_recommendations`/`score_breakdown` 节点解析、`humanize_report_text` 报告人类化、47 行 handoff 编码门禁和 725 项项目门禁。
- 证据：`40_quality_evidence/remote_selective_sync_b75396b_20260604.md`、`40_quality_evidence/remote_main_readonly_diff_b75396b_20260604.json`、`40_quality_evidence/selenium_visual_integration_20260603/selenium_visual_integration_20260603.json`。
# DEC-070 2026-06-04 老板六份方法资料触发全项目方法重基线

## 决策

老板新给的六份方法资料不是“补缺口参考”，而是本项目仿真路线的上层方法约束。它们会直接改变 P2/P3/P4 的判断边界，因此旧文件里的“已完成”“完整仿真”“可用排序”“打分结果”等结论必须重新审计；在重基线完成前，一律只能视为 draft / needs_review / dry-run。

## 理由

这些资料共同指向同一方向：不能让 LLM 直接编故事、直接打分、直接给最终选址；必须把仿真拆成可解释的画像状态、行为程序、空间选择、供需转化、宏观校准和证据复核。老板资料中的 ROTE、HumanLM、SSR、RL+LLM 社区仿真、SARIMA/SSIM/KL/DTW 等方法都对系统设计有直接价值，不能只按当前缺口抽取几条建议。

## 约束

- `60_model/simulation/engine.py` 当前仍是结构化 dry-run，不代表完整仿真。
- 旧 P4 完成口径、ROI/最终排名/最终推荐、裸分数展示必须降级或重写。
- DeepSeek 可以做低成本候选生成、语义整理、解释草稿和报告润色，但不得作为总设计师、最终评审、checked 证据来源或最终仿真裁判。
- 后续实现前必须先完成老板模型全盘吸收、旧文件可信度审计和 DeepSeek 任务契约设计。

# DEC-071 2026-06-04 仿真输出从“分数”转向“优先级、依据、建议、缺口”

## 决策

节点和项目判断的主视觉不再以裸分数为核心。界面和报告应优先呈现：推进优先级、为什么这样判断、需要补什么证据、下一步具体怎么做，以及哪些判断仍待复核。分数如保留，只能作为内部辅助指标，并必须解释口径、证据来源和不确定性。

## 理由

用户指出“分数只是指出问题，没有给建议”，这暴露了系统方向偏差。面向业务方的仿真系统不是考试打分器，而是决策工作台。老板资料也支持这一点：SSR 强调先生成语义意图再映射判断，HumanLM 强调状态对齐，ROTE 强调可执行行为程序，社区仿真强调微观行为与宏观统计校准。直接给分会掩盖证据缺口和行动路径。

## 约束

- 所有节点解释必须包含具体建议和复核动作。
- 不得把 DeepSeek 输出的分数写成事实。
- 报告语言应服务于人类业务判断，而不是展示模型字段。

# DEC-097 2026-06-07 真实校准补充输入必须端到端闭环并优先展示

## 决策

真实校准输入不再只由固定基线文件提供。平台必须支持用户新增、更新、删除补充校准资料；补充资料必须进入校准输入包、预检、仿真 job request、报告 JSON、Markdown、DOCX 和浏览器报告页，并在上下文中优先展示。

## 理由

用户持续强调收入水平、消费能力、周边人口、时间天气、竞品价格和真实世界因素会不断补充。如果系统只读取固定 14 条基线，后续真实资料会被淹没，报告也会继续像一次性草稿。优先展示用户补充资料可以让最新、最关键、最贴近项目现场的资料先被业务方看到。

## 约束

- 用户补充资料统一为 `ORCI-S### / local_user_supplement / needs_review`。
- 客户界面、Markdown 和 DOCX 只能显示“用户补充校准输入”等人话标签，不得裸露 `local_user_supplement`。
- 补充资料不能直接变成 checked 证据、最终收入、最终转化、最终收益、最终排名或投资定案。
- 每次修改补充资料后必须重建校准输入包，并通过闭环验证。

## 证据

- `90_p6_expert_dashboard/qa/real_calibration_supplement_loop_validation_20260607.py`
- `40_quality_evidence/real_calibration_supplement_loop_validation_20260607.json`
- `40_quality_evidence/real_calibration_supplement_loop_validation_20260607/report_with_supplement.png`

# DEC-098 2026-06-07 本地 HTTP 健康检查必须绕过系统代理

## 决策

本机验证 `127.0.0.1`、`localhost` 和本地 uvicorn 服务时，默认使用 `httpx.Client(trust_env=False)`、curl no-proxy 或等价方式绕过系统代理。不要把 `httpx` 默认 `trust_env=True` 返回的本地 502 直接判断为后端失败。

## 理由

本轮发现 live `http://127.0.0.1:8081/api/dashboard` 在 `httpx` 默认读取系统代理时返回空 502，但 uvicorn 日志没有请求记录；改用 `trust_env=False` 后同一 live 服务返回 200。此前多次 PowerShell / 本地接口误判，很可能与系统代理或环境变量有关。

## 约束

- 本地服务健康检查必须报告是否禁用了代理。
- 如果 `trust_env=True` 失败而 `trust_env=False` 通过，应记录为工具链/代理问题，不应绕回业务代码修补。
- 对真实外网 API 仍需按实际网络环境验证，不得把 no-proxy 规则误用于高德、GitHub、DeepSeek 等外部服务结论。

# DEC-099 2026-06-07 人物仿真结果必须输出准确性上下文

## 决策

结构化人物仿真 dry-run 的每个结果行必须输出 `accuracy_context` 和 `calibration_constraints`，把用户采用人物场景、真实校准输入、供需缺口、空间边界、经营字段和 DeepSeek 边界放到同一组可读字段里。

## 理由

用户要求的是“提高人物仿真准确性的方案”，不是只生成 1000 条场景，也不是只在报告里写收入和天气。真正能提高准确性的，是让每条结果说明：当前依据了哪些收入/消费/竞品/天气/空间/经营约束，还缺哪些数据，哪些只是上位边界，哪些不能被 DeepSeek 最终化。

## 约束

- `accuracy_context` 必须覆盖收入与消费能力、竞品价格与供给、时段与天气转化、空间边界与可达、经营字段与运维。
- 必须引用 ORCI 等真实校准输入编号，不能只写抽象建议。
- 必须保留 DeepSeek 边界：只能出候选解释、缺口和草稿，不得给最终概率、最终排名、最终收益或覆盖用户锁定对象。
- UI 和 CSV 导出必须可见这些字段。
- 这仍是 dry-run，不得宣称完整真实仿真、真实客群占比、最终 ROI 或最终选址排名已完成。

## 证据

- `40_quality_evidence/simulation_feature_scene_dry_run_validation_20260607.json`
- `40_quality_evidence/simulation_feature_scene_browser_validation_20260607.json`
- `40_quality_evidence/simulation_feature_scene_browser_validation_20260607/simulation_feature_scene.png`
