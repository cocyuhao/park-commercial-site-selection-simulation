# 当前最高优先级启动提示（2026-06-07）：客户版奥森 DOCX 已接入网页下载链路

新对话启动后先读本段，并以本段覆盖下方旧提示。当前用户最关心的不是继续同步同事、不是继续扩网页逻辑，而是：基于本文件夹已经给出的全部数据、策划案、图纸和方法资料，输出一份可给客户看的奥森商业决策 `.docx`。不要再让报告出现“请补资料/训练资料/内部证据链/API/网页平台/本地路径”等内容。

当前权威交付：

- 客户版 DOCX：`80_delivery/osen_business_decision_report_20260607.docx`
- 客户版 Markdown：`80_delivery/osen_business_decision_report_20260607.md`
- 内部依据 JSON：`40_quality_evidence/osen_business_decision_report_basis_20260607.json`
- 内部证据映射：`40_quality_evidence/osen_platform_report_evidence_map_20260607.json`
- 实际 8081 下载审计：`40_quality_evidence/actual_8081_client_report_audit_20260607.json`
- 渲染总览：`40_quality_evidence/osen_business_report_docx_render_20260607/contact_sheet.png`
- 本地网页首页：`http://127.0.0.1:8081/`
- 网页 DOCX 下载：`http://127.0.0.1:8081/api/reports/site-selection/download?format=docx`

已验证：

- 真实 8081 下载返回 HTTP 200。
- 下载 DOCX 大小 45,822 字节。
- 客户禁用词审计 `banned_hit_count=0`。
- 章节完整性通过：Word 标题 14 个，缺失章节为空。
- LibreOffice 转 PDF 与 PyMuPDF 渲染已产出 7 页 PNG 和 contact sheet；此前提示块孤页问题已修复。

继续工作硬规则：

- 客户报告只写“基于现有资料的判断、预测、调整、落地顺序和执行边界”。
- 不写“让客户补充资料/训练资料/内部方法/模型调试/文件路径/API 链路”。
- 若确有不确定性，只能表达为“实施校准、现场复核、试运营监测、许可边界”，并给出可执行动作。
- 网站 UI 和逻辑问题周一再系统改；本段只锁定 DOCX 生成、网页下载和客户版内容口径。

# 当前最高优先级启动提示（2026-06-07）：奥森 DOCX 与网页报告已交付，先核验再继续

新对话启动后先读本段。当前用户最关心的是：可打开网页和可拿走 `.docx` 是否已经完成。当前权威交付已生成并验证：

- DOCX：`80_delivery/osen_prediction_adjustment_report_20260607.docx`
- 网页报告：`90_p6_expert_dashboard/static/osen_prediction_adjustment_report_20260607.html`
- 网页下载 DOCX：`90_p6_expert_dashboard/static/osen_prediction_adjustment_report_20260607.docx`
- 网页依据链：`90_p6_expert_dashboard/static/osen_prediction_adjustment_report_basis_20260607.json`
- 本地 URL：`http://127.0.0.1:8081/static/osen_prediction_adjustment_report_20260607.html`
- 工作台首页：`http://127.0.0.1:8081/`

当前报告已做两项文档可读性修复：第一页生成时间不重复；人群行为预测由密集表格改成角色卡。网页报告顶部有“下载 DOCX 报告”和“查看依据链”。

验证证据：

- `40_quality_evidence/osen_prediction_adjustment_delivery_validation_20260607.json`
- `40_quality_evidence/osen_prediction_web_report_browser_20260607.png`
- `40_quality_evidence/osen_prediction_adjustment_docx_render_20260607/contact_sheet.png`
- `40_quality_evidence/libreoffice_bootstrap_repair_20260607.json`

LibreOffice 说明：`C:\Program Files\LibreOffice\program\bootstrap.ini` 文件本身未被改动；默认用户 profile 损坏导致启动失败。旧 profile 已备份为 `%APPDATA%\LibreOffice\4_backup_codex_bootstrap_repair_20260607_081444`，新 profile 已生成，转换验证通过。

继续任何非小修改前，必须先读 `10_research/osen_prediction_recent_literature_guard_20260607.md`，并补足“本地材料依据 + 近年外部依据 + 采用/拒用理由 + 项目落点 + 验证方法”，不要空想式修改。

# 当前最高优先级启动提示覆盖（2026-06-07）：先做已给材料驱动的奥森预测调整报告

进入新对话后先继承这一条，而不是下方旧的“人物仿真准确性上下文”提示：用户要求彻底回到本地已给材料驱动的奥森商业改造预测与调整报告。不要再围绕同事同步、补资料主线或旧准确性补丁打转。用户能给的资料已经给了，必须用本文件夹里的 PDF 数据、策划 DOCX、CAD/DWG/PDF 图纸、老板方法资料、证据台账、人物仿真特征池和 POI/TGI 数据进行仿真推演、节点调整、组合推进和试运营设计。

每次非小修改前必须有依据链：本地资料依据、今年或最近年份外部网页/论文/官方文档依据、为什么这样改适合本项目、改完如何验证。优先 2026 年，其次 2025 年；不能只说“学过/参考过/理解了”，不能空想式补丁。先读 `10_research/osen_prediction_recent_literature_guard_20260607.md`，缺资料就继续检索并补进该文件。

当前交付路径：

- `80_delivery/osen_prediction_adjustment_report_20260607.docx`
- `90_p6_expert_dashboard/static/osen_prediction_adjustment_report_20260607.html`
- `40_quality_evidence/osen_report_repair_evidence_basis_20260607.md`
- `10_research/osen_prediction_recent_literature_guard_20260607.md`
- `40_quality_evidence/osen_prediction_adjustment_delivery_validation_20260607.json`
- 本地 URL：`http://127.0.0.1:8081/static/osen_prediction_adjustment_report_20260607.html`

# 当前最高优先级启动提示补充（2026-06-07）：先继承人物仿真准确性上下文

继续本项目时先读：

1. `progress.md` 顶部“人物仿真准确性升级”
2. `findings.md` 顶部“人物仿真干跑结果已带准确性上下文”
3. `handoff_next_chat.md` 顶部同名交接
4. `00_control/decisions.md` 中 DEC-099
5. `40_quality_evidence/simulation_feature_scene_dry_run_validation_20260607.json`
6. `40_quality_evidence/simulation_feature_scene_browser_validation_20260607.json`

当前新事实：

- 人物仿真 dry-run 结果行已经新增 `accuracy_context` 和 `calibration_constraints`。
- 准确性约束覆盖收入与消费能力、竞品价格与供给、时段与天气转化、空间边界与可达、经营字段与运维。
- 结果行引用 ORCI 真实校准输入，并保留 DeepSeek 只能做候选解释、不能做最终判断的边界。
- 网页“仿真检查”表有“准确性”列，人物场景压力摘要有“准确性约束”。
- 最新总门禁：`checks=1168 failures=0`。

启动后先运行：

```powershell
py -3.12 30_extraction\scripts\verify_project_implementation.py
```

下一步优先做：

1. 把准确性上下文推进到 DOCX 报告的仿真结果章节。
2. 按用户真实 CAD/策划资料跑一版成熟 DOCX 工作稿；收入、人口、天气、竞品、客流、支付、许可消防必须分层标注证据和缺口。
3. 保持生产端 DeepSeek-only；Codex 只作为开发期主设计、验证和复核。
4. 不要 push GitHub，除非用户明确要求。

# 当前最高优先级启动提示补充（2026-06-07）：先继承真实校准补充输入闭环

继续本项目时先读：

1. `progress.md` 顶部“真实校准补充输入闭环”
2. `findings.md` 顶部“真实校准补充输入闭环已跑通”
3. `handoff_next_chat.md` 顶部同名交接
4. `00_control/decisions.md` 中 DEC-097 与 DEC-098
5. `40_quality_evidence/real_calibration_supplement_loop_validation_20260607.json`
6. `40_quality_evidence/real_calibration_supplement_loop_validation_20260607/report_with_supplement.png`

当前新事实：

- 新增/替换真实校准资料已可端到端影响校准输入包、预检、仿真 job request、报告 JSON/Markdown/DOCX 和 Chrome 报告页。
- QA 专门验证了“周边收入与消费能力补充”，更新后的“月可支配收入 14800 元/人；休闲餐饮客单 55-85 元”在报告页可见。
- 用户补充资料会优先展示，并用“用户补充校准输入”这种人话标签，不得给客户显示 `local_user_supplement`。
- QA 后基线恢复干净：正式校准包 14 条、无 QA 收入样本残留。
- 最新总门禁：`checks=1168 failures=0`。
- 本机本地 HTTP 验证要绕过系统代理：`httpx.Client(trust_env=False)`。否则访问 `127.0.0.1:8081` 可能出现假 502。

启动后先运行：

```powershell
py -3.12 30_extraction\scripts\verify_project_implementation.py
```

下一步优先做：

1. 按用户真实 CAD/策划资料跑出一版成熟 DOCX 工作稿；不要空想，所有收入、人口、天气、竞品、客流、支付、许可消防都要分层标注证据和缺口。
2. 继续把真实校准输入推进到结构化仿真结果字段，形成可解释的“建议 / 缺口 / 待复核 / 修改动作”。
3. 保持生产端 DeepSeek-only；Codex 只作为开发期主设计、验证和复核。
4. 不要 push GitHub，除非用户明确要求。

# 当前最高优先级启动提示补充（2026-06-07）：先继承真实校准输入报告链路

继续本项目时先读：

1. `progress.md` 顶部“报告链路升级”
2. `findings.md` 顶部“真实校准输入已进入报告 JSON、Markdown、DOCX 和浏览器报告页”
3. `handoff_next_chat.md` 顶部同名交接
4. `00_control/decisions.md` 中 DEC-096
5. `40_quality_evidence/report_feature_scene_context_validation_20260607.json`
6. `40_quality_evidence/osen_report_browser_validation_20260606.json`
7. `40_quality_evidence/osen_report_browser_validation_20260606/report_view.png`

当前新事实：

- 14 条真实校准输入已经进入报告 JSON、Markdown、DOCX 和浏览器报告页。
- 报告页可见“真实校准输入与使用边界”，并用人话显示官方宏观边界、设备价格代理、竞品价格线索和方案假设待复核。
- 最新总门禁：`checks=1162 failures=0`。

启动后先运行：

```powershell
py -3.12 30_extraction\scripts\verify_project_implementation.py
```

下一步优先做：

1. 做新增资料闭环验证：改/增一条真实校准资料，确认输入包、预检、干跑、报告 JSON/MD/DOCX、浏览器页都变化。
2. 把真实校准输入继续推进到结构化仿真结果字段，而不只停留在报告和 request。
3. 继续保持生产端 DeepSeek-only；Codex 只作为开发期主设计、验证和复核。
4. 不要 push GitHub，除非用户明确要求。

# 当前最高优先级启动提示补充（2026-06-07）：先继承真实校准输入层

继续本项目时先读：

1. `progress.md` 顶部“真实校准输入升级”
2. `findings.md` 顶部“真实校准输入已分层入库”
3. `handoff_next_chat.md` 顶部同名交接
4. `00_control/decisions.md` 中 DEC-095
5. `40_quality_evidence/osen_real_calibration_inputs_20260607.md`
6. `40_quality_evidence/osen_real_calibration_inputs_20260607.json`
7. `90_p6_expert_dashboard/qa/simulation_task_entry_preflight_validation_20260605.py`

当前新事实：

- 真实校准输入已经有 14 条，并进入资料资产、仿真任务预检、DeepSeek prompt 和仿真 job request。
- 收入水平必须分层处理：官方宏观收入/消费是上位边界，本地设备价格是弱代理，PPT 转化率和高峰日是待复核方案假设。
- 预检顶部已经显示“校准输入”，当前为 14。
- 最新总门禁：`checks=1161 failures=0`。

启动后先运行：

```powershell
py -3.12 30_extraction\scripts\verify_project_implementation.py
```

下一步优先做：

1. 把真实校准输入继续推进到结构化仿真结果与 DOCX 报告正文，不只停留在 preflight/request/prompt。
2. 做“新增资料 -> 校准输入包 -> 预检 -> 干跑 -> 报告”的闭环验证。
3. 补真实世界数据：奥森周边 1-3 公里人口/收入/办公/居住/学校/游客来源、竞品价格、分时段客流、天气转化、交易/转化、许可消防、CAD/GIS 控制点。
4. 继续保持生产端 DeepSeek-only；Codex 只作为开发期主设计、验证和复核。
5. 不要 push GitHub，除非用户明确要求。

# 当前最高优先级启动提示补充（2026-06-07）：先继承结构化仿真干跑中的人物场景与收入价格带

继续本项目时先读：

1. `progress.md` 顶部“仿真干跑升级”
2. `findings.md` 顶部“采用/锁定人物场景已进入结构化仿真干跑”
3. `handoff_next_chat.md` 顶部同名交接
4. `00_control/decisions.md` 中 DEC-094
5. `40_quality_evidence/simulation_feature_scene_dry_run_validation_20260607.md`
6. `40_quality_evidence/simulation_feature_scene_browser_validation_20260607.json`
7. `40_quality_evidence/simulation_feature_scene_browser_validation_20260607/simulation_feature_scene.png`

当前新事实：

- 用户采用/锁定的人物场景已经进入结构化仿真干跑，不只是报告、prompt、按钮状态或预检计数。
- 结果行包含 `feature_scene_context`、`scenario_pressure`、`feature_scene_count`、`matched_feature_scene_count`。
- `scenario_pressure` 必须继续保留收入段、消费价格带、时段、天气、空间节点、需求触发和场景动作。
- 网页结果页已显示“人物场景压力摘要”和“场景命中 / 场景动作”。
- 客服端不应显示 `needs_review/not_final`、`sample_city_green_heart`、英文业态、`P3-GATE` 等内部字段；总门禁已经要求用户可见 AI 边界人话化。
- 最新总门禁：`checks=1155 failures=0`。

启动后先运行：

```powershell
py -3.12 30_extraction\scripts\verify_project_implementation.py
```

下一步优先做：

1. 补真实数据闭环：奥森周边 1-3 公里收入/人口/居住办公/游客来源、竞品价格、分时段客流、天气转化、交易/转化、审批许可、消防与 CAD/GIS 控制点。
2. 做“新增资料 -> 抽取/对象链 -> 预检 -> 仿真干跑 -> 报告变化”的闭环验证。
3. 继续把收入水平从“场景压力”推进到真实价格敏感度、客单价、转化率和收益成本校准，但不能在缺数据时写成最终结论。
4. 继续保持生产端 DeepSeek-only；Codex 只作为开发期主设计、验证和复核。
5. 不要 push GitHub，除非用户明确要求。

# 当前最高优先级启动提示补充（2026-06-07）：先继承采用场景进入报告与 DeepSeek prompt

继续本项目时先读：

1. `progress.md` 顶部“报告输入链路升级”
2. `findings.md` 顶部“采用/锁定人物场景已进入报告、DOCX、Markdown 和 DeepSeek prompt”
3. `00_control/decisions.md` 中 DEC-093
4. `40_quality_evidence/report_feature_scene_context_validation_20260607.md`
5. `40_quality_evidence/report_feature_scene_context_browser_20260607.json`
6. `90_p6_expert_dashboard/qa/report_feature_scene_context_validation_20260607.py`

当前新事实：

- 用户采用/锁定的人物场景已经进入 `demand_supply.report.controlled_feature_scene_context`。
- 报告会展示场景编号、收入/价格带、时段/天气/空间、建议动作和待补证据。
- DOCX 与 Markdown 均新增“人物场景输入与收入价格带”章节。
- DeepSeek prompt 已带入“用户采用/锁定的人物场景输入”，并要求把收入水平、消费价格带、时段、天气、空间节点和需求触发作为约束变量。
- 报告页 Browser 证据确认：人物场景区域可见、1 条采用/锁定场景进入报告、收入/价格带可见、console error=0。
- 最新总门禁：`checks=1143 failures=0`。

启动后先运行：

```powershell
py -3.12 30_extraction\scripts\verify_project_implementation.py
```

下一步优先做：

1. 补真实数据闭环：奥森周边 1-3 公里收入/人口/居住办公/游客来源、竞品价格、分时段客流、天气转化、交易/转化数据。
2. 做“新增资料 -> 抽取/对象链 -> 预检 -> 报告变化”的闭环验证，确认上传资料会改变报告和场景输入。
3. 继续保持生产端 DeepSeek-only；Codex 只作为开发期主设计、验证和复核，不得成为最终网站内置 AI。
4. 不要 push GitHub，除非用户明确要求。

# 当前最高优先级启动提示补充（2026-06-07）：先继承收入/消费价格带结构化接入

继续本项目时先读：

1. `progress.md` 顶部“人物场景控制升级”
2. `findings.md` 中“收入/消费价格带已从文本提示升级为人物场景结构化变量”
3. `40_quality_evidence/feature_derivative_income_control_browser_20260607.json`
4. `40_quality_evidence/person_simulation_feature_derivatives_validation_20260607.md`
5. `90_p6_expert_dashboard/qa/simulation_task_entry_preflight_validation_20260605.py`

当前新事实：

- 人物场景覆盖池已新增结构化收入/消费价格带字段：`income_segment_id/name`、`income_price_band`、`income_sensitivity_note`、`income_evidence_hint`。
- 覆盖池验证新增 `income_segment_id=5`，当前 `status=pass failure_count=0`。
- `/api/simulation/task-preflight` 已带出 `feature_scene_inputs` 和 `controlled_feature_scene_count`；采用/锁定场景会影响预检，不再只是按钮状态。
- 全局对象链新增 `feature_derivative_scene`。
- 浏览器证据 `feature_derivative_income_control_browser_20260607.json/png` 已确认：收入/价格可见、采用/锁定后计数变 1、预检项已满足、console error=0。
- 最新总门禁：`checks=1132 failures=0`。

启动后先运行：

```powershell
py -3.12 30_extraction\scripts\verify_project_implementation.py
```

下一步优先做：

1. 让采用/锁定的人物场景进一步影响报告草稿解释和 DeepSeek 任务输入摘要。
2. 补奥森周边 1-3 公里收入/人口/居住办公/游客来源、竞品价格、真实交易和天气/时段转化数据。
3. 做“新增资料 -> 覆盖池/对象链 -> 预检 -> 报告变化”的闭环验证。
4. 继续保持生产端 DeepSeek-only；不要 push GitHub，除非用户明确要求。

# 当前最高优先级启动提示补充（2026-06-07）：先继承人物仿真覆盖池修复和 DEC-091

继续本项目时先读：

1. `00_control/decisions.md` 中 DEC-091
2. `40_quality_evidence/person_simulation_feature_derivatives_validation_20260607.md`
3. `30_extraction/scripts/build_person_simulation_feature_derivatives.py`
4. `30_extraction/scripts/verify_person_simulation_feature_derivatives_20260607.py`
5. `40_quality_evidence/person_simulation_accuracy_requirements_20260605.md`

当前新事实：

- `person_simulation_feature_derivatives_1000_20260604.csv` 曾经中文损坏为 `??`，旧门禁只看 1200 行所以漏检。
- 现在已重新生成 1200 条 UTF-8 中文场景，覆盖收入/预算、天气/节假日、时段、空间节点、需求触发、供给动作、DeepSeek 边界、用户采用/放弃/锁定和具体建议。
- 新验证报告 `person_simulation_feature_derivatives_validation_20260607.json/md` 当前 `status=pass failure_count=0`。
- 网页链路已接入：资料底座可见“人物仿真覆盖池”，仿真任务预检包含 `person_simulation_feature_derivatives` 检查项。
- 浏览器可见性证据：`40_quality_evidence/person_feature_pool_browser_visible_20260607.json`，上传页和任务预检均可见，console error=0。
- 用户控制链路已接入：`/api/simulation/feature-derivatives` 和 PATCH 接口支持代表场景采用、放弃、恢复、锁定、解锁；浏览器证据 `40_quality_evidence/feature_derivative_user_control_browser_20260607.json` 已通过。
- 总门禁最新：`checks=1128 failures=0`。
- 边界：这是人物仿真覆盖池，不是最终仿真结论；不能写成 ROI、最终收益、最终排名或完整 P4 已完成。

启动后先运行：

```powershell
py -3.12 30_extraction\scripts\verify_project_implementation.py
```

若继续主线，优先做：

1. 继续把“已采用/已锁定人物场景”推进到仿真任务输入组合，让它真正影响对象链、预检和报告解释。
2. 补奥森周边 1-3 公里人口、收入、客流、竞品价格和天气/时段转化数据。
3. 做“新增资料 -> 覆盖池/对象链 -> 报告变化”的闭环验证。
4. 不要 push GitHub，除非用户明确要求。

# 当前最高优先级启动提示补充（2026-06-07）：先继承奥森 DOCX 工作稿和收入/真实世界门禁

继续本项目时先读：

1. `progress.md` 顶部“奥森综合报告工作稿已跑通”
2. `findings.md` 顶部“奥森 DOCX 工作稿已跑通”
3. `10_research/osen_real_world_context_sources_20260607.md`
4. `10_research/expert_implementation_review_framework_20260607.md`
5. `10_research/expert_implementation_knowledge_20260607/expert_implementation_summary.json`
6. `40_quality_evidence/osen_docx_delivery_validation_20260606.md`
7. `40_quality_evidence/osen_report_browser_validation_20260606.json`
8. `00_control/decisions.md` 中最新 DEC-090

当前新事实：

- 奥森综合报告已能由平台生成 DOCX 工作稿：`80_delivery/osen_integrated_site_selection_report_20260606.docx`。
- 报告已纳入收入、消费、服务消费、周边人口与收入、目标人群、时间天气、地理可达、消防许可、财务招商和舆情社区接受等真实世界维度。
- 每个节点已有三套实施方案和“哪些证据会改变判断”，不再以裸分数作为用户主结论。
- 网页报告页可下载 DOCX，浏览器验证和截图已通过。
- 当前仍是待复核工作稿，不是最终投资结论。北京市收入/消费数据只能作为上位边界，不能替代奥森周边局部收入和客群数据。

启动后先运行：

```powershell
py -3.12 30_extraction\scripts\verify_project_implementation.py
```

若继续主线，优先做：

1. 补奥森周边 1-3 公里人口、收入、居住/办公/学校/游客来源、真实客流和竞品价格数据。
2. 做“新增资料 -> 抽取/入账 -> 对象链变化 -> 报告变化”的闭环验证。
3. 做 CAD 控制点/GIS 校准，让当前图纸锚点从工程坐标走向可量测空间路径。
4. 继续保持生产端 DeepSeek-only；不要把 Codex 内置进最终网站。
5. 不要 push GitHub，除非用户明确要求。

# 当前最高优先级启动提示补充（2026-06-05）：先继承资料与空间底座新切片

继续本项目时先读：

1. `00_control/decisions.md` 中 DEC-089 / DEC-088 / DEC-087
2. `40_quality_evidence/source_space_foundation_validation_20260605.md`
3. `40_quality_evidence/source_space_foundation_browser_runtime_20260605.json`
4. `40_quality_evidence/source_space_foundation_upload_lazy_map_20260605.png`
5. `00_control/mainline_execution_map_20260605.md`

当前新事实：

- 用户纠偏成立：不能只处理旧东西，必须在蓝图中判断旧模块是否该保留/重构/隐藏/废弃。
- `资料与空间底座` 已被判定为最终蓝图切片，不是旧上传页美化。
- 前端新增底座工作区：4 个摘要 + 8 类底座资产卡，显示“进入对象”和“使用边界”。
- 数字来自后端 `/api/dashboard` 的 `simulation_task_preflight.local_data_assets`，不是前端写死；但新增资料后的全链路变化检查排在完整报告跑通之后。
- 非地图页不再后台加载高德 JS/静态地图/key；Chrome 验证 `#upload` 只有本地请求，`hasAmapScriptElement=false`，`hasAmapGlobal=false`。
- 最新总门禁：`checks=1049 failures=0`。

启动后先运行：

```powershell
py -3.12 30_extraction\scripts\verify_project_implementation.py
```

下一步优先做：

1. 先让平台完整跑出一份报告。
2. 然后验证新增资料是否能改变证据台账/PDF/对象链/报告。
3. 不要继续修旧资料导入页边角；任何页面工作都要先说明它在最终蓝图里的位置。
4. 不要 push GitHub，除非用户明确要求。

# 当前最高优先级启动提示补充（2026-06-05）：旧产物只能选择性迁移

继续时先读：

1. `00_control/decisions.md` 中 DEC-088 / DEC-087 / DEC-086 / DEC-085
2. `40_quality_evidence/workflow_navigation_validation_20260605.md`
3. `40_quality_evidence/workflow_nav_node_detail_runtime_20260605.json`
4. `40_quality_evidence/page_rebuild_strategy_audit_20260605.md`
5. `progress.md` 顶部“旧产物选择性使用，不得默认继承”

当前新事实：

- 过去很多旧页面、旧检查、旧交互和旧文案可能来自旧方向或空想补丁，不能默认信任。
- 节点详情重复“新增节点”是旧残留，已修复：顶部新增是唯一新增入口；详情区只在可编辑节点显示“编辑当前节点”；不可编辑节点不显示表单。
- 静态版本已更新为 `20260605-workflow`，浏览器运行态证据已确认 `formCount=0` 且不保存高德 `key=` 参数。
- 新门禁 `verify_workflow_navigation_20260605.py` 已接入总门禁。
- 最新总门禁：`checks=1038 failures=0`。

启动后先运行：

```powershell
py -3.12 30_extraction\scripts\verify_project_implementation.py
```

下一步做页面/节点/资料池/AI 工作台时，先把相关旧产物标成 `保留 / 重构 / 隐藏 / 废弃`，再实现；不要继续把旧 P6 壳当最终设计。

# 当前最高优先级启动提示补充（2026-06-05）：先继承人物仿真准确性矩阵

继续本项目时先读：

1. `40_quality_evidence/person_simulation_accuracy_requirements_20260605.md`
2. `40_quality_evidence/method_model_landing_coverage_20260605.md`
3. `10_research/boss_method_materials_20260604/simulation_accuracy_plan_20260604.md`
4. `10_research/boss_method_materials_20260604/modern_practical_method_rescreen_20260604.md`
5. `10_research/deepseek_api_concurrency_capacity_20260605.md`

当前新事实：

- 人物仿真准确性不再只是口头方案，已落成 `person_simulation_accuracy_requirements_20260605.*`。
- 该矩阵把老板资料和近期论文转成 9 条工程约束：人群状态、行为程序、活动链与路线、选择概率、运营动作、宏观校准、DeepSeek 调用、用户监督、高能力主控。
- 2026-06-05 已补 DEC-086：开发期 Codex 可作为主 agent 做设计、约束、验证和复核；最终市场化网站不得内置 Codex，生产端 AI 只能使用 DeepSeek。
- 旧模型覆盖审计已纠偏：最新 `covered=8 partial=1 missing=0`；不要再引用旧 `covered=4 partial=5` 作为当前状态。
- persona_state / behavior_program 已进入对象池；下一步不是“再证明有对象”，而是让仿真任务入口能选择、组合、预检这些对象。
- 最新总门禁：`py -3.12 30_extraction\scripts\verify_project_implementation.py` 输出 `checks=1014 failures=0`。

启动后先运行：

```powershell
py -3.12 30_extraction\scripts\verify_project_implementation.py
```

下一步优先做：

1. 仿真任务入口：选择 persona_state / behavior_program / choice_probability / validation_target。
2. 运行前预检：缺真实客流、路径、转化率、收益成本、运营授权时，只能 dry-run / needs_review。
3. DeepSeek 队列与 trace：批处理、缓存、429 退避、任务级 OTel，不逐游客调用。

# 当前最高优先级启动提示补充（2026-06-05）：先继承 DEC-085 和现代验证链

继续时先读：

1. `00_control/decisions.md` 中 DEC-085 / DEC-084 / DEC-083 / DEC-082 / DEC-081
2. `00_control/page_layer_rebuild_blueprint_20260605.md`
3. `40_quality_evidence/advanced_capability_and_legacy_method_audit_20260605.md`
4. `40_quality_evidence/page_layer_rebuild_validation_20260605.json`
5. `40_quality_evidence/axe_accessibility_probe_20260605.json`
6. `40_quality_evidence/lighthouse_user_flow_20260605.json`
7. `40_quality_evidence/otel_fastapi_trace_probe_20260605.json`

当前新事实：

- 用户要求“必要时大改，不再旧补丁化；安装/学习/插件必须真正使用”。该要求已写成 DEC-085。
- 页面层首屏已改为“全局仿真链路台”，不是旧项目说明页；AI 工作台默认“项目综合”，不默认 N-001 / 桃花源白房子。
- Node QA 栈已安装且使用：axe + Playwright + Lighthouse；Python OTel 栈已安装且使用。
- 最新总门禁：`py -3.12 30_extraction\scripts\verify_project_implementation.py` 输出 `checks=1003 failures=0`。
- 人工 Chrome 截图路径：`40_quality_evidence/manual_chrome_overview_20260605.png`、`40_quality_evidence/manual_chrome_ai_20260605.png`。

启动后优先运行：

```powershell
py -3.12 30_extraction\scripts\verify_project_implementation.py
```

做页面或工作台改动后至少运行：

```powershell
py -3.12 90_p6_expert_dashboard\qa\page_layer_rebuild_validation_20260605.py
npm run qa:axe        # cwd=90_p6_expert_dashboard\qa
npm run qa:lighthouse # cwd=90_p6_expert_dashboard\qa
py -3.12 90_p6_expert_dashboard\qa\otel_fastapi_trace_probe_20260605.py
py -3.12 30_extraction\scripts\audit_advanced_capability_and_legacy_methods_20260605.py
```

下一步继续主线时，不要重新证明“要不要先进”；直接把未完成的页面/资料池/节点/地图/报告/仿真任务入口按对象链和老板模型落点继续做，并为每个大改补证据和总门禁。

# 当前最高优先级启动提示补充（2026-06-05）：先读全项目审计和模型落点覆盖

继续时先读：

1. `40_quality_evidence/project_context_legacy_risk_audit_20260605.md`
2. `40_quality_evidence/method_model_landing_coverage_20260605.md`
3. `10_research/deepseek_api_concurrency_capacity_20260605.md`
4. `10_research/method_tool_plugin_audit_20260604.md`
5. `00_control/decisions.md` 中 DEC-083 / DEC-082 / DEC-081

当前新事实：

- 项目文件 `943`，可文本扫描 `732`，老板资料 `6/6` 齐。
- 旧风险词 `12323` 次，不等于全是 bug，但证明历史遗留必须脚本治理。
- 老板模型/外部论文落点：`covered=4 partial=5 missing=0`。接下来不要再泛泛说“研究过”，要补 partial 的落地能力。
- DeepSeek 并发按账号，不按 API Key；不得逐游客实时调用 DeepSeek。
- `60_model/src/telemetry.py` 是未接入草稿，不能宣称完成。

下一步优先级：

1. 跑门禁确认 DEC-083 证据仍在。
2. 处理模型落点 partial：人群状态对象池、行为程序对象池、DeepSeek 队列/缓存/trace、宏观验证目标 UI。
3. 清理用户可见旧风险词，只保留人话状态，不暴露内部字段。

# 明天启动第一优先级（2026-06-04 下班前保存）

用户关机前的小闭环已经完成到“方法/工具/插件/论文审计清单”这一步。新对话不要从聊天记录猜，先读：

1. `10_research/method_tool_plugin_audit_20260604.md`
2. `handoff_next_chat.md` 顶部“不要丢失先进性审计这条线”
3. `progress.md` 顶部“方法/工具/插件/论文审计已落地为门禁资产”
4. `findings.md` 顶部“方法/工具/插件/论文审计清单已纳入门禁”
5. `00_control/decisions.md` 中 DEC-082 / DEC-081 / DEC-080 / DEC-079

先运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\00_control\start_codex_mainline.ps1
```

然后确认：

```powershell
py -3.12 30_extraction\scripts\verify_project_implementation.py
```

下一步不要重新讨论“是否要先进”，直接继续把审计清单中的未完成项落地：OpenTelemetry span、人物仿真任务入口、POI/TGI 辅助因子接入、Product Design/Figma 或等价设计系统产物、全局 AI 工作台重构。不要 GitHub push，除非用户明说。

# 当前最高优先级启动提示补充（2026-06-04）：先继承高级 AI/UX/逻辑风险门禁

继续 `C:\Users\Yy199\Desktop\仿真设计` 时，先读：

1. `10_research/advanced_ai_validation_rebaseline_20260604.md`
2. `40_quality_evidence/advanced_agentic_workflow_validation_20260604.md`
3. `40_quality_evidence/advanced_agentic_workflow_validation_20260604.json`
4. `90_p6_expert_dashboard/qa/advanced_agentic_workflow_validation_20260604.py`
5. `00_control/decisions.md` 中 DEC-081 / DEC-080 / DEC-079

用户最新担忧：不仅框架可能旧，检查方法、判断来源、论文/工具吸收方式也可能旧。不能再用一句“已学习/已参考/已测试”带过。每个工具、论文、插件和方法都要回答：为什么用、是否足够先进、在本项目落到哪里、还有什么风险。

当前已落地：
- Playwright 1.60 + Chrome trace + ARIA snapshot + 7 视图截图。
- OpenTelemetry SDK 1.42 已安装，后续用于 AI/仿真链路 trace，不只看最终输出。
- Selenium 4.44 保留兼容，不再作为高级可用性的唯一证据。
- 高级 QA 风险 taxonomy 覆盖 10 类：human_visual、agent_readability、ai_scope_integrity、oversight_checkpoint、legacy_leakage、state_coupling、evidence_traceability、observability、ai_output_risk、accessibility_semantics。
- 最新高级 QA：`status=pass findings=0`。
- 总门禁已新增 `advanced_gate`，最新 `checks=917 failures=0`。

启动后先运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\00_control\start_codex_mainline.ps1
```

重大 UI/AI/仿真任务改动后至少运行：

```powershell
py -3.12 90_p6_expert_dashboard\qa\advanced_agentic_workflow_validation_20260604.py
py -3.12 30_extraction\scripts\verify_project_implementation.py
```

下一步不是继续打磨旧页面审美，而是：
1. 建立“方法/工具/论文/插件使用审计清单”，让先进性和取舍可追问、可替换、可门禁。
2. 继续全局 AI 工作台、资料/方法对象池、仿真任务入口和报告链路落地。
3. 每次改动都用高级 QA 拦截旧词泄露、agent 不可读、信息密度、AI 范围错绑和监督缺失。

# 当前最高优先级启动提示补充（2026-06-04）：全局 AI 仿真决策系统重基线

继续本项目时，优先读：

1. `00_control/codex_mainline_guardrails.md`
2. `40_quality_evidence/codex_mainline_context_20260604.md`
3. `10_research/global_ai_simulation_design_rebaseline_20260604.md`
4. `10_research/advanced_ai_learning_absorption_register_20260604.md`
5. `40_quality_evidence/flowus_ai_design_probe_20260604/flowus_probe_report.json`
6. `10_research/ai_design_2026_openalex_raw_20260604.json`
7. `40_quality_evidence/simulation_object_pool_api_validation_20260604.json`
8. `40_quality_evidence/global_ai_design_rebaseline_overview_validation_20260604.json`
9. `00_control/decisions.md` 中 DEC-080 / DEC-079 / DEC-078 / DEC-077 / DEC-076 / DEC-074

用户最新要求：系统不应只叫“公园商业决策工作台”。正确总定位是“AI 驱动仿真决策系统”；公园商业选址只是当前场景。Codex 自身强化可以插入主线，但只能作为“防偏航层”，用来防止旧完成度、旧 DeepSeek 草稿、旧分数、同事辅助成果和上下文压缩把系统带回旧方向。

启动后先运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\00_control\start_codex_mainline.ps1
```

已验证完整入口：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\00_control\start_codex_mainline.ps1 -FullGate
```

当前主线状态：
- 36 条 `choice_probability` 候选已生成，全部 `needs_review`，`probability_value=null`，不编造概率。
- 10 条 `simulation_validation_target` 已生成，覆盖状态-行为链、路线可达、选择概率、时间序列、宏观分布和业务决策。
- 两个 envelope 契约验证均通过。
- `advanced_ai_learning_absorption_register_20260604.md` 已把先进性从“好看 UI”升级为对象能力层、agent 可读 UI、检查点调度、多 agent 角色分层、可反驳解释和旧产物信任地图。
- 这两类对象已接入 UI/API 对象池，支持新增、编辑、采用、放弃、锁定、解锁、删除；验证见 `40_quality_evidence/simulation_object_pool_api_validation_20260604.json` 和 `40_quality_evidence/simulation_object_pool_browser_validation_20260604.json/png`。
- 节点可见逻辑已从裸分数改为“推进优先级 + 依据 + 具体建议”。
- 首页口径已从旧项目总览改为“全局推进台”，浏览器验证见 `40_quality_evidence/global_ai_design_rebaseline_overview_validation_20260604.json/png`。

下一步：
- 按 `10_research/global_ai_simulation_design_rebaseline_20260604.md` 继续重构专家 AI 工作台、资料池/方法对象池、仿真任务入口和报告链路。
- 建立旧产物信任地图：仍可信、需降级、仅历史参考、应废弃，重点审计旧“完整仿真”“最终推荐”“ROI”“裸分数”“已完成”。
- 页面展示时不能说“仿真完成”，只能说“候选/待复核/资料阻塞/推进动作/需要补证”。
- 暂不推送 GitHub，除非用户明确要求。

# 当前最高优先级启动提示补充（2026-06-04）：现代 AI 仿真方法已补强

继续 `C:\Users\Yy199\Desktop\仿真设计` 时，先读：

1. `10_research/boss_method_materials_20260604/modern_practical_method_rescreen_20260604.md`
2. `40_quality_evidence/modern_sim_stack_verification_20260604.md`
3. `10_research/boss_method_materials_20260604/method_absorption_landing_register_20260604.md`
4. `00_control/decisions.md` 中 DEC-076 / DEC-074 / DEC-072

最新用户纠偏：此前方法学习偏古早，不能只靠 Huff/Logit/Gravity/Social Force 这类经典方法。当前已改为现代混合仿真主线：轻量领域生成器 + 空间/运营约束 + LLM 个体修正/解释 + schema/校准/人工门禁。

已安装并验证现代栈：DuckDB、Polars、jsonschema、Pydantic、GeoPandas、Shapely、NetworkX、OSMnx、MovingPandas、Mesa、Mesa-Geo、SimPy、SALib、Optuna。验证报告 `packages=14 failures=0`；总门禁 `checks=804 failures=0`。

下一步不要再写泛泛学习总结，也不要回到裸分数。继续做：
- `choice_probability` adapter：用人群、行为程序、节点、供给、时段、资料引用和现代数据栈生成优先级、解释、建议、缺口。
- `simulation_validation_target` adapter：把路线可达、状态-行为一致性、时序/分布/业务决策验证变成可复核目标。
- 后续 P6 接入这些对象时必须支持用户新增、编辑、采用、放弃、删除、锁定。

# 当前最高优先级启动提示补充（2026-06-04）：方法落地与 PowerShell 乱码后续治理

继续 `C:\Users\Yy199\Desktop\仿真设计` 时，先记住用户最新纠偏：

- “模仿人类”是 UI/可用性测试方法，指 Selenium/Browser/智能体像真实业务用户一样反复操作网页；不是方法层判断“像不像真人”。
- 方法层要先全盘吸收老板六份资料和外部论文，再落成系统对象、字段、门禁、adapter、验证指标和禁用边界。
- 不要再只写“参考过论文”。每个可用方法必须进入对象、字段、门禁、adapter 或后续任务。

必须先读新增文件：
1. `10_research/boss_method_materials_20260604/method_absorption_landing_register_20260604.md`
2. `10_research/boss_method_materials_20260604/method_selection_evaluation_20260604.md`
3. `60_model/schemas/choice_probability.schema.json`
4. `60_model/schemas/simulation_validation_target.schema.json`
5. `60_model/schemas/person_simulation_control.schema.json`
6. `60_model/schemas/deepseek_task_contract.schema.json`
7. `60_model/scripts/validate_deepseek_contract_output.py`

最新状态：
- `choice_probability` 和 `simulation_validation_target` schema 已新增。
- DeepSeek contract 已允许 `choice_probability`、`simulation_validation_target`、`state_behavior_consistency`，但仍只能 `draft/needs_review`。
- `verify_project_implementation.py` 已纳入这些 schema、方法落地台账和 P4 节点解释降级检查。
- 最新验证：P4 契约 `status=pass failure_count=0`；handoff 编码健康 `failures=0`；总门禁 `checks=796 failures=0`。

下一步：
1. 写 `choice_probability` 任务 adapter，把旧 POI/TGI、节点、persona/program 草稿中可用内容转成选择概率候选。
2. 写 `simulation_validation_target` 任务 adapter，把老板资料中的 SARIMA/SSIM/KL/DTW/宏观一致性和状态-行为-证据链检查转成验证目标候选。
3. 接入 P6 用户可控对象池，支持新增、编辑、采用、放弃、删除、锁定。
4. PowerShell/终端中文乱码已专项处理。根因是 Windows PowerShell 5.1 默认按 ANSI/GBK 读取无 BOM UTF-8 文件。已更新 `C:\Users\Yy199\Documents\WindowsPowerShell\profile.ps1`，设置 UTF-8 控制台/输出编码，并给 `Get-Content/Set-Content/Add-Content/Out-File/Export-Csv` 设置 UTF-8 默认参数。新会话验证 `chcp=65001`，普通 `Get-Content` 可直接显示中文。

# 当前最高优先级启动提示（2026-06-04）：老板方法重基线优先

请继续 `C:\Users\Yy199\Desktop\仿真设计`。第一任务不是同步 GitHub，不是推送，不是继续修 UI，也不是直接扩写仿真代码。用户最新纠正是：老板给的六份方法资料会改变整个仿真方向和工作量，旧文件里的很多“已完成”可能不再可信。

启动后先读并吸收：

1. `AGENTS.md`
2. `progress.md`
3. `findings.md`
4. `handoff_next_chat.md`
5. `00_control/decisions.md`
6. `10_research/boss_method_materials_20260604/full_system_rebaseline_20260604.md`
7. `10_research/boss_method_materials_20260604/boss_model_inventory_20260604.md`
8. `10_research/boss_method_materials_20260604/rebaseline_audit_after_boss_models_20260604.md`
9. `10_research/boss_method_materials_20260604/unified_simulation_method_matrix_20260604.md`
10. `10_research/boss_method_materials_20260604/external_paper_screening_20260604.md`
11. `10_research/boss_method_materials_20260604/deepseek_task_contracts_20260604.md`
12. `10_research/boss_method_materials_20260604/legacy_file_trust_audit_20260604.md`

必须坚持：
- 老板资料不是“补缺口资料”，而是上层方法约束。
- 当前主控口径以 `full_system_rebaseline_20260604.md` 为准：项目已经从“POI/TGI 缺口 + AI 工作台”重定性为“证据驱动的人群潜在状态与行为程序仿真系统”。
- 论文不能只写“读过”；每篇都要转成系统对象、验证指标、禁用边界或风险控制。
- 旧 P4 完整仿真、最终排名、ROI、最终推荐、裸分数展示必须降级或重审。
- DeepSeek 只能做受限语义工人，不能做总设计师、最终裁判、checked 证据或最终商业结论。
- DeepSeek 任务契约、旧文件可信度审计、4 个 schema 和本地校验脚本已经建立；`60_model/llm_runs` 35 个旧输出文件已通过 `adapt_deepseek_legacy_outputs.py` 包装成 metadata-only envelope，并通过 `validate_deepseek_contract_output.py` 验证。
- 注意：旧 envelope 通过不代表旧内容可信，只代表纳入审计；如果要使用旧内容，必须继续写任务专用 adapter，重新抽取 `persona_state`、`behavior_program`、`node_explanation` 或 `report_draft`。
- 最新落实性门禁是 `checks=750 failures=0`。

当前关键产物：

- `10_research/boss_method_materials_20260604/full_system_rebaseline_20260604.md`
- `40_quality_evidence/rebaseline_artifact_trust_audit_20260604.md`
- `40_quality_evidence/deepseek_legacy_envelope_adapter_20260604.md`
- `40_quality_evidence/deepseek_legacy_envelope_validation_20260604.json`

下一步优先级：

1. 不要重复做 metadata-only adapter；继续做任务专用 adapter。
2. 优先从旧 P2/P4 草稿中抽取 `node_explanation`，把裸分数/排名降级成优先级、依据、具体建议、补证动作。
3. 再从 1200 条衍生场景和 schema 做 P6 人物仿真配置 CRUD。

# 下一轮启动提示：远端 b75396b 已选择性吸收，本地成果优先

请继续 `C:\Users\Yy199\Desktop\仿真设计`。当前任务不是完整同步 GitHub main，也不是把同事代码覆盖到本地；远端 `b75396b66c5988ba3640b8060660a8f2b7d7cdb8` 已经只读比较，并且只选择性吸收低冲突改进。

启动后先读：

1. `AGENTS.md`
2. `progress.md`
3. `findings.md`
4. `handoff_next_chat.md`
5. `00_control/decisions.md`
6. `40_quality_evidence/remote_selective_sync_b75396b_20260604.md`
7. `40_quality_evidence/remote_main_readonly_diff_b75396b_20260604.json`

当前关键状态：

- 远端 main 最新已确认：`b75396b66c5988ba3640b8060660a8f2b7d7cdb8`，提交信息 `Stabilize dashboard workflow gates`。
- 本轮没有全量覆盖、没有 `git reset`、没有 force sync、没有推送 GitHub。
- 已选择性吸收：
  - 上传资料用途归一化。
  - 节点草案去重。
  - 生成报告按钮状态联动。
- 必须保留本地胜出逻辑：
  - 地图静态兜底和 fallback tiles，避免地图空白。
  - 节点优先级解析、扣分来源和“现在建议怎么做”。
  - 报告人类化文案，不把 `report_path` 作为主要 UI。
  - 最新 47 行 handoff 编码门禁和 `checks=725 failures=0` 项目门禁。
- AI 工作台默认项目综合，不默认绑定 `N-001` 或“桃花源白房子”。
- 节点分数只能作为“当前资料条件下的讨论优先级”，不能当最终排名；视觉重点应是建议和补证动作。
- 交接链路必须保留 `LLM-018` 和 `LLM-019` 两个编号，不能在后续文档中删掉。
- 最新实现门禁是 `checks=725 failures=0`；旧门禁基线 `checks=589 failures=0` 只作为历史门禁记录保留。
- DWG 仍是 `pending_conversion`，不能把未转换图纸当作已校准空间证据。

当前验证命令：

```powershell
node --check 90_p6_expert_dashboard\static\app.js
py -3.12 -m py_compile 90_p6_expert_dashboard\app.py 30_extraction\scripts\verify_project_implementation.py 30_extraction\scripts\review_handoff_and_encoding_health.py
py -3.12 30_extraction\scripts\review_handoff_and_encoding_health.py
py -3.12 30_extraction\scripts\verify_project_implementation.py
py -3.12 30_extraction\scripts\verify_pdf_tables.py
py -3.12 90_p6_expert_dashboard\qa\selenium_visual_integration_20260603.py
```

关键证据：

- `40_quality_evidence/remote_selective_sync_b75396b_20260604.md`
- `40_quality_evidence/remote_main_readonly_diff_b75396b_20260604.json`
- `40_quality_evidence/selenium_visual_integration_20260603/selenium_visual_integration_20260603.json`
- `40_quality_evidence/remote_selective_sync_b75396b_browser_checks_20260604/overview.png`
- `40_quality_evidence/remote_selective_sync_b75396b_browser_checks_20260604/ai_workspace.png`

注意：

- 普通 `httpx` 可能受本机代理影响，对 `127.0.0.1:8000` 返回 `502`；本地服务验证使用 `httpx.Client(trust_env=False)` 或 Selenium/Chrome。
- 当前本地 dashboard 服务可用：`http://127.0.0.1:8000`。
- 若下一步要推送 GitHub，先做 secrets 检查和 `git status` 分拣，不要提交 `.env`、运行缓存、临时截图、测试会话报告或无关 QA 产物；不要 force push，除非用户明确再次确认。
# 下一轮 Codex 启动提示：先做老板方法重基线，不要按旧完成度推进

你正在接手 `C:\Users\Yy199\Desktop\仿真设计`。用户刚刚明确纠正：老板新给的六份方法资料不是“补缺口参考”，而是会改变整个仿真方向的上层方法材料。仿真工作量因此显著变大，旧文件里的很多“已完成”都可能只是旧标准下的阶段产物，不能继续当成可信结论。

第一步不要同步 GitHub，不要推送，不要直接改 UI，不要继续实现仿真代码。先读并吸收：

- `AGENTS.md`
- `progress.md`
- `findings.md`
- `handoff_next_chat.md`
- `00_control/decisions.md`
- `10_research/boss_method_materials_20260604/boss_model_inventory_20260604.md`
- `10_research/boss_method_materials_20260604/rebaseline_audit_after_boss_models_20260604.md`
- `10_research/boss_method_materials_20260604/unified_simulation_method_matrix_20260604.md`
- `10_research/boss_method_materials_20260604/external_paper_screening_20260604.md`

必须坚持的判断：

- 老板六份资料方向一致，但不能简单说已经合成一个完整系统；要把它们全盘吸收到同一条可解释、可复核、可校准的仿真路线里。
- `60_model/simulation/engine.py` 当前只是结构化 dry-run，不是完整仿真。
- 旧 P4 完成口径、ROI、最终排名、最终推荐、裸分数展示都需要降级、审计或重写。
- DeepSeek 便宜但不够稳，只能做候选生成、语义整理、解释草稿、报告润色；不能做总设计师、最终裁判、checked 证据、最终排名或仿真完成声明。
- 节点和报告要服务业务决策：推进优先级、依据、具体建议、待补资料、复核动作，比打分更重要。

下一步具体做：

1. 写出 DeepSeek 受限任务契约：输入、输出 schema、白名单字段、失败降级、人工复核、禁止事项。
2. 审计旧 P2/P3/P4/P6 文件可信度，把“仍可信 / 需改文案 / 草稿保留 / 必须降级或重写”列清楚。
3. 把老板资料里的模型落成工程对象：画像状态、行为程序、空间选择、供需转化、宏观校准、证据复核。
4. 完成上述审计后，再决定哪些代码保留、哪些重写、哪些删除。
# 下一轮优先提示：不要把旧网页补丁误认为整站重做

你接手 `C:\Users\Yy199\Desktop\仿真设计`。先读：

- `AGENTS.md`
- `00_control/decisions.md`，尤其 DEC-087
- `40_quality_evidence/page_rebuild_strategy_audit_20260605.md`
- `10_research/ui_skill_design_system_audit_20260605.md`
- `00_control/page_layer_rebuild_blueprint_20260605.md`
- `progress.md`
- `findings.md`
- `handoff_next_chat.md`

当前结论：

- 网站还没有整站级重做完成。
- 当前 `90_p6_expert_dashboard` 是旧 P6 壳上的过渡重基线。
- 新链路已经接入：全局仿真链路台、对象链路矩阵、AI 项目综合、仿真任务入口、DeepSeek-only 生产边界和预检门禁。
- 旧壳仍存在：节点清单、空间地图、资料导入、方法对象池、分析报告、专家 AI 工作台仍按旧 view 并列。
- 所以下一步不是继续小修旧壳，而是页面级信息架构重构。

下一步建议：

1. 先跑 `py -3.12 30_extraction\scripts\verify_project_implementation.py`。
2. 如果通过，按 DEC-087 开始重构第一屏或写页面级重构方案。
3. 下一版页面顺序应是：`全局链路台 -> 资料与空间底座 -> 人物仿真对象工坊 -> 仿真任务预检 -> 决策解释与报告工作稿`。
4. 必须保留 DeepSeek-only 生产边界、完整仿真阻止、老板资料/CAD/证据链入口、采用/放弃/锁定机制。
5. 不要推 GitHub，除非用户明确要求。
# 下一轮建议提示：TestFiles 自动化测试
请先读取 `TestFiles/reports/test_report_20260608_143919.md`。自动化入口为 `py TestFiles\run_all_tests.py`，已覆盖后端 53 个 OpenAPI 接口和前端主要交互。当前唯一失败是报告依据链 JSON 导出在真实 Uvicorn 浏览器路径下返回 502；优先定位 live server 与 TestClient 行为不一致的原因。

# 下一轮建议提示：TestFiles 502 已修复
请先读取 `TestFiles/reports/test_report_20260608_163052.md`。自动化入口为 `py TestFiles\run_all_tests.py`，当前全量结果为 `passed=79 warning=1 failed=0`。502 根因是测试脚本默认 `httpx` 环境传输配置截走本地请求，已通过 `trust_env=False` 修复。
