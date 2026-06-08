# 全项目上下文与历史遗留风险审计（2026-06-05）

- 生成时间：2026-06-05T09:23:17
- 项目文件数：949，可文本扫描文件：738，总大小：373472960 bytes
- 老板原始资料：6 / 6 已找到
- Git 待处理行数：199，未接入 telemetry 草稿：True

## 1. 结论

- 项目不是缺资料，而是历史产物多、旧口径多、方向变化大；继续实现前必须用脚本分层，而不是靠聊天记忆。
- 老板六份资料原件已齐，关键吸收文档存在；后续应复核这些文档是否真正进入 schema、UI、DeepSeek 契约和门禁。
- 旧风险词命中很多，其中不少是正确的警戒语；真正危险的是用户可见界面或结果文件继续把 dry-run、最终推荐、ROI、裸分数写成事实。
- 刚刚创建的 `60_model/src/telemetry.py` 还没有接入主链，当前只能算草稿，不能写成已落地。

## 2. 文件分层

- `40_quality_evidence`：327 个文件
- `60_model`：141 个文件
- `50_external_gis`：113 个文件
- `10_research`：98 个文件
- `90_p6_expert_dashboard`：91 个文件
- `70_outputs`：51 个文件
- `30_extraction`：41 个文件
- `80_delivery`：29 个文件
- `00_control`：15 个文件
- `老板资料`：6 个文件
- `20_raw_data`：5 个文件
- `CAD图及其计划`：4 个文件
- `.claude`：1 个文件
- `.env`：1 个文件
- `.env.example`：1 个文件
- `.gitattributes`：1 个文件
- `.gitignore`：1 个文件
- `.vscode`：1 个文件
- `_check_fill_rate.py`：1 个文件
- `_check_good_table_content.py`：1 个文件
- `_check_olympic_fill.py`：1 个文件
- `_check_ppt_and_ledger.py`：1 个文件
- `_finalize_p0_audit.py`：1 个文件
- `_fix_codex_behavior.py`：1 个文件
- `_update_audit_report.py`：1 个文件
- `_verify_ppt.py`：1 个文件
- `_verify_raw.py`：1 个文件
- `_write_agents_md.py`：1 个文件
- `AGENTS.md`：1 个文件
- `ARCHITECTURE.md`：1 个文件
- `CONTEXT.md`：1 个文件
- `findings.md`：1 个文件
- `handoff_next_chat.md`：1 个文件
- `KEYS.md`：1 个文件
- `next_chat_prompt.md`：1 个文件
- `progress.md`：1 个文件
- `README.md`：1 个文件
- `requirements.txt`：1 个文件
- `setup.sh`：1 个文件
- `task_plan.md`：1 个文件

## 3. 老板资料覆盖

- 六份老板原始资料均已找到。
- `10_research/boss_method_materials_20260604/full_system_rebaseline_20260604.md`：存在，13080 bytes
- `10_research/boss_method_materials_20260604/unified_simulation_method_matrix_20260604.md`：存在，11446 bytes
- `10_research/boss_method_materials_20260604/simulation_accuracy_plan_20260604.md`：存在，6365 bytes
- `10_research/boss_method_materials_20260604/boss_model_inventory_20260604.md`：存在，11173 bytes
- `10_research/boss_method_materials_20260604/method_absorption_landing_register_20260604.md`：存在，9182 bytes
- `10_research/boss_method_materials_20260604/deepseek_constrained_simulation_design_20260604.md`：存在，3435 bytes
- `10_research/boss_method_materials_20260604/legacy_file_trust_audit_20260604.md`：存在，8120 bytes

## 4. 旧风险词命中

- `complete_simulation_claim`：329 处
- `final_claim`：579 处
- `roi_revenue_claim`：341 处
- `legacy_dry_run`：224 处
- `raw_internal_ui`：4238 处
- `score_overclaim`：168 处
- `deepseek_boundary`：7059 处

## 5. 用户可见风险样例

- `90_p6_expert_dashboard/static/app.js:85` [deepseek_boundary] nodeDraftReview: statusToken("node", "draft", "review", "required"),
- `90_p6_expert_dashboard/static/app.js:122` [score_overclaim] const direct = Number(node?.discussion_score_draft);
- `90_p6_expert_dashboard/static/app.js:122` [deepseek_boundary] const direct = Number(node?.discussion_score_draft);
- `90_p6_expert_dashboard/static/app.js:132` [deepseek_boundary] if (node?.score_status === "node_draft_review_required") return "待复核草案";
- `90_p6_expert_dashboard/static/app.js:139` [deepseek_boundary] if (node?.score_status === "node_draft_review_required") return "资料未闭合，先作为讨论草案";
- `90_p6_expert_dashboard/static/app.js:142` [final_claim] return "仅表示当前资料条件下的推进优先级，不是最终推荐";
- `90_p6_expert_dashboard/static/app.js:147` [deepseek_boundary] if (node?.score_status === "node_draft_review_required") return "资料未闭合";
- `90_p6_expert_dashboard/static/app.js:281` [raw_internal_ui] const payload = await response.json();
- `90_p6_expert_dashboard/static/app.js:282` [raw_internal_ui] state.simulationJobs = payload.items || [];
- `90_p6_expert_dashboard/static/app.js:622` [deepseek_boundary] const isEditable = node?.source === "manual_node_draft" || node?.source === "project_plan_import";
- `90_p6_expert_dashboard/static/app.js:632` [deepseek_boundary] <label class="node-enabled"><input id="nodeEnabledInput" type="checkbox" ${!isEditable || node.enabled !== false ? "checked" : ""} /> 启用节点</label>
- `90_p6_expert_dashboard/static/app.js:1321` [raw_internal_ui] const payload = state.data?.demand_supply || {};
- `90_p6_expert_dashboard/static/app.js:1322` [raw_internal_ui] const tgi = payload.tgi || {};
- `90_p6_expert_dashboard/static/app.js:1323` [raw_internal_ui] const supply = payload.supply || {};
- `90_p6_expert_dashboard/static/app.js:1324` [raw_internal_ui] const gap = payload.gap || {};
- `90_p6_expert_dashboard/static/app.js:1331` [raw_internal_ui] <span>客流资料：${payload.visitor_sources?.count || 0} 份</span>
- `90_p6_expert_dashboard/static/app.js:1341` [raw_internal_ui] <span><b>${esc(payload.visitor_sources?.count || 0)}</b><em>客流资料</em></span>
- `90_p6_expert_dashboard/static/app.js:1597` [raw_internal_ui] const payload = await response.json();
- `90_p6_expert_dashboard/static/app.js:1598` [raw_internal_ui] if (!response.ok) throw new Error(payload.detail || `仿真对象保存失败：${response.status}`);
- `90_p6_expert_dashboard/static/app.js:1612` [raw_internal_ui] const payload = await response.json();

## 6. 风险样例摘录

### complete_simulation_claim
- `00_control/codex_mainline_guardrails.md:29` 7. 不允许旧 dry-run、旧分数、旧报告或旧 UI 文案被误写成完整仿真。
- `00_control/codex_mainline_guardrails.md:58` - 不要把旧 `P4 完整仿真`、旧裸分数、旧 dry-run 当完成。
- `00_control/decisions.md:80` - 边界：所有选择概率候选保持 `probability_value=null` 和 `needs_review`；验证目标用于阻止旧 dry-run 或 LLM 草稿被误写成完整仿真。
- `00_control/decisions.md:117` - 当前处理：旧证据底座可保留；P6 只视为产品壳；P2 persona/behavior/validation CSV 只视为草稿候选；旧 DeepSeek 输出必须 envelope 适配或降级；P4 完整仿真、ROI、最终排序、最终推荐和节点裸分数统一重审。
- `00_control/decisions.md:127` - 禁止：不得把旧 envelope 当 checked 证据、最终排名、ROI、完整仿真、运营决策或节点最终建议。
- `00_control/decisions.md:226` | DEC-037 | 2026-05-26 | P2 启动先限定为真实资料准备索引：DOCX/PDF 可抽取为待复核输入，DWG 在无可信转换产物前保持 `pending_conversion`，PPT 不进入 P2 主线 | 用户明确要求新对话开始 P2 准备但不要直接跑完整仿真；当前资料包能支持目标/策划/节点/场景假设拆解，但不能直接支撑几何、客流、收益和成本仿真 | 若把 PDF 标签或 DWG 文件存在性误读成几何解析，会污
- `00_control/decisions.md:228` | DEC-039 | 2026-05-28 | P2 准备可把 DeepSeek 语义草稿转为结构化输入 schema 候选表，但关键缺口域和最终门禁必须由本地规则固定 | 用户要求继续进入 P2 操作并尽量多用 DeepSeek；项目节点、业态/场景假设、空间标签和输入缺口适合 DeepSeek 先整理为可复核候选表 | DeepSeek 可能把 `conversion_rate`、`revenue_cost`、`operation
- `00_control/decisions.md:229` | DEC-040 | 2026-05-28 | P2 按方法原型口径闭环，P3 真实校准和 P4 完整 Agent/GIS 仿真仍未开始 | `task_plan.md` 对 P2 的定义是方法原型、概率选择原型、第一版公式、persona/场景参数和 API 契约草案；用户要求一口气推进 P2，但当前仍缺 DWG 几何、真实客流、转化率、收益/成本和运营授权 | 若把 P2 方法原型误写成完整仿真，会污染最终选址结论；若把候选评分当
### final_claim
- `00_control/codex_mainline_guardrails.md:57` - 不要让 DeepSeek 决定最终仿真、最终排名、ROI 或 checked 证据。
- `00_control/decisions.md:15` - 在 DeepSeek 任务契约和旧文件可信度审计完成前，不得继续把旧 P4、ROI、最终排名、最终推荐或节点分数写成已完成事实。
- `00_control/decisions.md:89` - 边界：DeepSeek 仍只能做低成本语义工人，生成 `draft/needs_review` 候选、解释、反例和报告草稿；不得做最终仿真、checked 证据、ROI、最终排名或最终商业结论。
- `00_control/decisions.md:99` - 边界：DeepSeek 可以生成 `choice_probability`、`simulation_validation_target`、`state_behavior_consistency` 候选，但必须 `draft/needs_review`，不得写 checked、final、ROI、最终排名、最终推荐或覆盖用户锁定对象。
- `00_control/decisions.md:117` - 当前处理：旧证据底座可保留；P6 只视为产品壳；P2 persona/behavior/validation CSV 只视为草稿候选；旧 DeepSeek 输出必须 envelope 适配或降级；P4 完整仿真、ROI、最终排序、最终推荐和节点裸分数统一重审。
- `00_control/decisions.md:127` - 禁止：不得把旧 envelope 当 checked 证据、最终排名、ROI、完整仿真、运营决策或节点最终建议。
- `00_control/decisions.md:136` - 边界：不得把 `discussion_score_draft` 写成最终选址分、ROI、收益预测或最终排名。
- `00_control/decisions.md:163` - 边界：DWG/DOCX/PDF 上传解析仍只是待复核候选；缺口和报告不得升级为最终推荐、最终排序、收益预测或 checked 证据。
### roi_revenue_claim
- `00_control/codex_mainline_guardrails.md:57` - 不要让 DeepSeek 决定最终仿真、最终排名、ROI 或 checked 证据。
- `00_control/decisions.md:15` - 在 DeepSeek 任务契约和旧文件可信度审计完成前，不得继续把旧 P4、ROI、最终排名、最终推荐或节点分数写成已完成事实。
- `00_control/decisions.md:89` - 边界：DeepSeek 仍只能做低成本语义工人，生成 `draft/needs_review` 候选、解释、反例和报告草稿；不得做最终仿真、checked 证据、ROI、最终排名或最终商业结论。
- `00_control/decisions.md:99` - 边界：DeepSeek 可以生成 `choice_probability`、`simulation_validation_target`、`state_behavior_consistency` 候选，但必须 `draft/needs_review`，不得写 checked、final、ROI、最终排名、最终推荐或覆盖用户锁定对象。
- `00_control/decisions.md:117` - 当前处理：旧证据底座可保留；P6 只视为产品壳；P2 persona/behavior/validation CSV 只视为草稿候选；旧 DeepSeek 输出必须 envelope 适配或降级；P4 完整仿真、ROI、最终排序、最终推荐和节点裸分数统一重审。
- `00_control/decisions.md:127` - 禁止：不得把旧 envelope 当 checked 证据、最终排名、ROI、完整仿真、运营决策或节点最终建议。
- `00_control/decisions.md:136` - 边界：不得把 `discussion_score_draft` 写成最终选址分、ROI、收益预测或最终排名。
- `00_control/decisions.md:163` - 边界：DWG/DOCX/PDF 上传解析仍只是待复核候选；缺口和报告不得升级为最终推荐、最终排序、收益预测或 checked 证据。
### legacy_dry_run
- `00_control/codex_mainline_guardrails.md:29` 7. 不允许旧 dry-run、旧分数、旧报告或旧 UI 文案被误写成完整仿真。
- `00_control/codex_mainline_guardrails.md:58` - 不要把旧 `P4 完整仿真`、旧裸分数、旧 dry-run 当完成。
- `00_control/decisions.md:80` - 边界：所有选择概率候选保持 `probability_value=null` 和 `needs_review`；验证目标用于阻止旧 dry-run 或 LLM 草稿被误写成完整仿真。
- `00_control/decisions.md:118` - 禁止：不得跳过全盘吸收直接补 UI、直接推 GitHub、直接把 DeepSeek 草稿或旧 dry-run 写成仿真完成。
- `00_control/decisions.md:173` # DEC-063 P6 后端契约统一与 dry-run 解释字段
- `00_control/decisions.md:176` - 决策：员工A后端接口统一返回 `output_status`、`not_final`、`status_label`、`source_hint`、`evidence_hint`，并把节点草案评分和 dry-run 阻塞解释放到后端生成；前端可继续保留旧字段，后续逐步切换到后端字段。
- `00_control/decisions.md:177` - 原因：前端自行猜字段和计算分数会导致 A/B 职责冲突；dry-run 只返回数量不能解释为什么不能最终化；外部地图搜索地点不能套用奥森训练节点评分。
- `00_control/decisions.md:179` - 边界：后端草案分仅用于讨论，`score_status=external_preview_only` 时只能做地图预览；dry-run 仍不得输出 ROI、收益预测、最终排序或最终推荐。
### raw_internal_ui
- `00_control/codex_mainline_guardrails.md:26` 4. 保持 `choice_probability` 和 `simulation_validation_target` 均为 `needs_review`。
- `00_control/decisions.md:80` - 边界：所有选择概率候选保持 `probability_value=null` 和 `needs_review`；验证目标用于阻止旧 dry-run 或 LLM 草稿被误写成完整仿真。
- `00_control/decisions.md:89` - 边界：DeepSeek 仍只能做低成本语义工人，生成 `draft/needs_review` 候选、解释、反例和报告草稿；不得做最终仿真、checked 证据、ROI、最终排名或最终商业结论。
- `00_control/decisions.md:99` - 边界：DeepSeek 可以生成 `choice_probability`、`simulation_validation_target`、`state_behavior_consistency` 候选，但必须 `draft/needs_review`，不得写 checked、final、ROI、最终排名、最终推荐或覆盖用户锁定对象。
- `00_control/decisions.md:124` - 决策：`60_model/llm_runs` 中 35 个旧 DeepSeek 输出统一通过 `60_model/scripts/adapt_deepseek_legacy_outputs.py` 包装为 `source_summary` envelope，状态固定为 `needs_review`，并写入 `60_model/llm_runs/contract_envelopes/legacy_*.json`。
- `00_control/decisions.md:170` - 影响：外部地点统一显示为 `external_preview_only` / 地图预览；节点详情和仿真面板优先展示 `missing_required_fields`、`why_blocked`、`next_data_needed`。
- `00_control/decisions.md:171` - 边界：该分数仍为 `needs_review / not_final`，不得转写为最终排序、收益预测、ROI 或推荐结论。
- `00_control/decisions.md:176` - 决策：员工A后端接口统一返回 `output_status`、`not_final`、`status_label`、`source_hint`、`evidence_hint`，并把节点草案评分和 dry-run 阻塞解释放到后端生成；前端可继续保留旧字段，后续逐步切换到后端字段。
### score_overclaim
- `00_control/codex_mainline_guardrails.md:58` - 不要把旧 `P4 完整仿真`、旧裸分数、旧 dry-run 当完成。
- `00_control/decisions.md:7` - 先看 DEC-079：全局 AI 仿真决策系统设计重基线；旧界面需要按“目标 -> 对象 -> 依据 -> 动作 -> 复核 -> 报告”重组，不再围绕页面、裸分数或技术门禁堆叠。
- `00_control/decisions.md:14` - 先看 DEC-070 / DEC-071：老板六份方法资料触发全项目方法重基线；仿真输出从裸分数转向优先级、依据、建议和缺口。
- `00_control/decisions.md:61` - 当前实现：已用 Selenium 真实抽取 3 份 Flowus AI 设计资料；新增 `ai_design_2026_openalex_raw_20260604.json`、`ai_design_2026_semantic_scholar_raw_20260604.json`、`global_ai_simulation_design_rebaseline_20260604.md`；P6 已开始把 `choice_probabili
- `00_control/decisions.md:117` - 当前处理：旧证据底座可保留；P6 只视为产品壳；P2 persona/behavior/validation CSV 只视为草稿候选；旧 DeepSeek 输出必须 envelope 适配或降级；P4 完整仿真、ROI、最终排序、最终推荐和节点裸分数统一重审。
- `00_control/decisions.md:133` - 决策：节点清单和详情主视觉不再突出裸分数，改为显示“推进优先级 + 具体建议”；分数只保留在“优先级解析与建议”中，解释当前资料条件下为什么先推、先补证或暂缓推荐。
- `00_control/decisions.md:134` - 原因：裸分数会让用户误以为系统已经给出精确定量排名；当前 P3 门禁未闭合，分数只能表示讨论优先级，最重要的是告诉业务方下一步该补什么、怎么推进。
- `00_control/decisions.md:136` - 边界：不得把 `discussion_score_draft` 写成最终选址分、ROI、收益预测或最终排名。
### deepseek_boundary
- `00_control/codex_mainline_guardrails.md:7` 本项目已经进入长上下文、多 agent、多轮同步状态。风险不是“少写一个总结”，而是新对话或新 agent 容易把旧完成度、旧分数、旧 DeepSeek 草稿、同事辅助代码和老板方法资料混成一团，导致主线重新跑歪。
- `00_control/codex_mainline_guardrails.md:25` 3. 保持 DeepSeek 低成本语义工人定位。
- `00_control/codex_mainline_guardrails.md:26` 4. 保持 `choice_probability` 和 `simulation_validation_target` 均为 `needs_review`。
- `00_control/codex_mainline_guardrails.md:57` - 不要让 DeepSeek 决定最终仿真、最终排名、ROI 或 checked 证据。
- `00_control/credential_handoff.md:19` - DeepSeek 脚本只从 `DEEPSEEK_API_KEY` 读取 Key。
- `00_control/credential_handoff.md:27` - 本地 `.env` 已保存高德和 DeepSeek 凭据；
- `00_control/decisions.md:13` - 旧 DeepSeek 输出已按 DEC-073 纳入 metadata-only envelope；通过验证不代表旧内容可用。
- `00_control/decisions.md:15` - 在 DeepSeek 任务契约和旧文件可信度审计完成前，不得继续把旧 P4、ROI、最终排名、最终推荐或节点分数写成已完成事实。

## 7. 下一步建议

1. 先把本审计加入门禁和交接，避免后续新对话忘记全项目风险。
2. 对用户可见风险样例逐项确认：前端可以保留人话状态，但不能出现内部词或最终化口径。
3. 对老板资料吸收文档做一次“落点覆盖”检查：schema、adapter、UI、DeepSeek 契约、验证脚本是否都有对应项。
4. 决定 `60_model/src/telemetry.py`：要么接入并验证，要么标记为未接入草稿，不能让它漂在主线外。
