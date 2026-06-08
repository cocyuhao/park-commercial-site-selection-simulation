# 高级 agentic 工作流验证报告（2026-06-04）

- 状态：`pass`
- URL：`http://127.0.0.1:8000/?qa=advanced-agentic-validation`
- Playwright：`1.60.0`
- Chrome：`C:\Program Files\Google\Chrome\Application\chrome.exe`
- 发现数：0
- trace：`40_quality_evidence/advanced_agentic_workflow_trace_20260604.zip`

## 风险 taxonomy

- `human_visual`：阅读宽度、信息密度、折叠、第一屏负担和输入/输出框比例。
- `agent_readability`：关键控件是否有稳定 id、aria-label 或 data-* hook，避免自动化只能靠文案猜。
- `ai_scope_integrity`：默认是否是项目综合，是否误塞第一个节点或旧固定节点。
- `oversight_checkpoint`：采用、删除、生成报告、运行检查等动作是否留有监督点和后果提示。
- `legacy_leakage`：旧状态词、旧裸分、旧报告、debug/API 语言是否泄露到客服界面。
- `state_coupling`：地图/资料/节点/AI/报告之间切换时是否保留上下文，不被异步加载抹掉。
- `evidence_traceability`：报告和节点说明是否区分依据、缺口、待复核和下一步动作。
- `observability`：是否留下 trace、ARIA、console、network、截图和结构化 JSON 证据。
- `ai_output_risk`：AI 文案是否像日志、是否过度自信、是否缺少反例/不能判断边界。
- `accessibility_semantics`：控件语义、可访问名称和焦点路径是否足够让人和 agent 都读懂。

## 发现

- 无。

## 页面覆盖

- `overview`：title=`AI 仿真决策系统`，text_len=1451，issues=[]，screenshot=`40_quality_evidence/advanced_agentic_workflow_overview_20260604.png`
- `upload`：title=`AI 仿真决策系统`，text_len=1223，issues=[]，screenshot=`40_quality_evidence/advanced_agentic_workflow_upload_20260604.png`
- `data`：title=`AI 仿真决策系统`，text_len=4364，issues=[]，screenshot=`40_quality_evidence/advanced_agentic_workflow_data_20260604.png`
- `nodes`：title=`AI 仿真决策系统`，text_len=1951，issues=[]，screenshot=`40_quality_evidence/advanced_agentic_workflow_nodes_20260604.png`
- `map`：title=`AI 仿真决策系统`，text_len=1530，issues=[]，screenshot=`40_quality_evidence/advanced_agentic_workflow_map_20260604.png`
- `ai`：title=`AI 仿真决策系统`，text_len=355，issues=[]，screenshot=`40_quality_evidence/advanced_agentic_workflow_ai_20260604.png`
- `report`：title=`AI 仿真决策系统`，text_len=584，issues=[]，screenshot=`40_quality_evidence/advanced_agentic_workflow_report_20260604.png`

## 结构化检查

- 控件数：232
- 按钮数：214
- 缺少稳定 hook 的按钮/链接数：0
- AI 工作台布局：`{'viewport': {'width': 1440, 'height': 1000}, 'chat_messages': {'x': 336, 'y': 220.046875, 'width': 1070, 'height': 619.953125}, 'ai_composer': {'x': 372, 'y': 840, 'width': 998, 'height': 124}, 'overview_status_cards': None, 'simulation_object_pool': None, 'map_canvas': None, 'report_body': None}`
- 静态前端扫描：`{'files': ['90_p6_expert_dashboard/static/index.html', '90_p6_expert_dashboard/static/app.js', '90_p6_expert_dashboard/static/styles.css'], 'banned_term_hits': [], 'allowed_mapping_hits': [], 'note': 'Internal status terms are allowed only in mapping/prompt boundary code. User-visible text is checked separately through browser snapshots.'}`

## 解释

本报告不是旧式 smoke test。`needs_work` 表示高级检查发现了下一步应修的问题，不等同于页面不可用。
它用于补足 Selenium 反复点击、静态门禁和截图检查看不出来的 agentic workflow / 人类监督 / 结构可读性问题。
