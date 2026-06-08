# 远端 main 只读差异与本地融合方案

日期：2026-06-03  
仓库：`https://github.com/cocyuhao/park-commercial-site-selection-simulation`  
本地 HEAD：`4e5cb7b8712572211e74f0296e29fac44a947372`  
原则：本轮只读远端，不完全同步、不覆盖本地、不推 GitHub。

## 1. 获取方式

普通 `git ls-remote`、`gh api` 在本机网络环境下不稳定，已改用 GitHub codeload 只读下载远端 `main` 源码包到临时目录：

`C:\Users\Yy199\AppData\Local\Temp\park_remote_main_readonly_20260603\park-commercial-site-selection-simulation-main`

该目录只用于比对，不作为本地工作区同步源。

## 2. 三方差异结论

已生成机器差异清单：

`40_quality_evidence/remote_main_readonly_diff_20260603.json`

关键数字：

- 远端文件数：548。
- 远端相对本地 HEAD 变化文件：36。
- 本地相对 HEAD 已跟踪变化文件：17。
- 本地未跟踪验证/报告产物：138。
- 远端和本地共同触碰文件：8。

共同触碰文件：

- `90_p6_expert_dashboard/app.py`
- `90_p6_expert_dashboard/static/app.js`
- `90_p6_expert_dashboard/static/index.html`
- `90_p6_expert_dashboard/static/styles.css`
- `findings.md`
- `handoff_next_chat.md`
- `next_chat_prompt.md`
- `progress.md`

结论：不能直接 `reset`、`robocopy /MIR`、ZIP 镜像同步，也不建议直接 `git merge` 后手工乱解冲突。应按功能块移植。

## 3. 远端新增重点

远端文档显示同事主要完成两块：

### 地图专项

远端交接称已完成：

- 空间地图改为真实高德 JS API 2.0。
- 支持高德原生拖拽、滚轮缩放、按钮缩放。
- 项目位置、候选节点、商业 POI、搜索结果做了视觉区分。
- 点击 POI 有信息卡。
- 右侧新增 POI 结果列表。
- 搜索失败隐藏后端异常原文，保留用户输入。

远端新增/相关代码点：

- `@app.get("/api/amap/js-config")`
- `map_search_error_detail`
- 前端 `fitAmapView`
- 前端 `mapContextPayload`
- 前端 `renderMapErrorPanel`
- 前端 `renderMapResultList`
- 前端 `renderPoiInfoCard`
- 前端 `selectPoi`
- DOM：`mapErrorPanel`
- DOM：`mapResultList`

### 资料 / 节点 / 总览联动

远端新增/相关代码点：

- `@app.post("/api/nodes")`
- `@app.patch("/api/nodes/{node_id}")`
- `@app.delete("/api/nodes/{node_id}")`
- `@app.post("/api/nodes/generate-from-plan")`
- `load_node_drafts`
- `normalize_node_draft`
- `build_plan_node_drafts`
- 前端 `renderNodeForm`
- 前端 `nodePayloadFromForm`
- DOM：`oneClickPlanImportBtn`
- DOM：`quickGeneratePlanNodesBtn`
- DOM：`quickNewNodeBtn`

这些内容对用户此前“节点无法增加”“资料导入后自动分节点”“地图 loading 竞态”的抱怨是有价值的，应该吸收。

## 4. 本地必须保留的内容

本地刚完成并通过严格验证的内容不能被远端覆盖：

- AI 工作台默认项目综合，不默认 N-001。
- AI 输出文案人话化：`humanize_report_text`、`suppress_project_node_ids`、`humanizeAiText`。
- AI 上下文不声称读完全部资料：`local_source_inventory`、`load_local_source_briefs`、`summarize_gap_context`。
- 项目总览 6 张动态状态卡：`renderOverviewStatusCards`、`overviewStatusCards`。
- AI 左侧栏折叠：`aiRailToggle`。
- 输入框随模式切换提示：`updateChatPlaceholder`。
- 输入框工具条中的 `composerReportBtn`。
- 生成报告有效对话门槛，前端和后端都要保留。
- 节点详情 8 个折叠区、报告页折叠区、宽阅读区和输入框比例。
- 本地严格 Selenium v3：10 轮、150 动作、失败 0。

## 5. 研究依据

合并策略参考了软件工程协作冲突研究，而不是只靠直觉：

- Kasi & Sarma 的 Cassandra 研究强调并行开发中直接/间接冲突需要提前识别，并用任务依赖和文件依赖减少冲突。
- Nelson 等关于 merge conflict 生命周期的研究指出，开发者需要监控、规划、执行和评估合并结果，不能只依赖文本合并。
- Brun 等 Crystal/早期冲突检测研究说明，越早发现冲突，越容易在变更仍小的时候协调解决。
- Accioly / Borba 等半结构化冲突研究显示，很多冲突来自同一方法或相邻代码区域的独立编辑，这正对应本次双方同时改 `app.py`、`app.js`、`index.html`、`styles.css`。
- GitHub Docs 也区分了可在网页解决和必须在本地 clone 中处理的冲突；本次属于必须本地仔细处理的类型。

参考链接：

- Cassandra: Proactive Conflict Minimization through Optimized Task Scheduling: `https://digitalcommons.unl.edu/cseconfwork/275/`
- Early detection of collaboration conflicts and risks / Crystal: `https://homes.cs.washington.edu/~mernst/pubs/vc-conflicts-tse2013-abstract.html`
- Understanding semi-structured merge conflict characteristics: `https://pauloborba.cin.ufpe.br/publication/2018understanding_semi-structured_merge_conflict_characteristics_in_open-source_java_projects/`
- GitHub Docs - About merge conflicts: `https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/addressing-merge-conflicts/about-merge-conflicts`

## 6. 推荐融合策略

### A. 不直接同步

禁止：

- `git reset --hard origin/main`
- `robocopy /MIR`
- 直接把远端 ZIP 覆盖本地
- 直接接受远端版本覆盖四个 dashboard 文件

原因：会丢掉本地已经验证过的 AI 工作台、报告生成、折叠和总览视觉。

### B. 按功能块手工移植

第一批建议吸收远端“后端能力”，因为冲突风险较低且可独立验证：

1. `NodeDraftRequest`
2. `load_node_drafts`
3. `save_node_drafts`
4. `normalize_node_draft`
5. `build_plan_node_drafts`
6. `/api/nodes` 新增、更新、删除
7. `/api/nodes/generate-from-plan`
8. `/api/amap/js-config`
9. `map_search_error_detail`

第二批再吸收前端“地图/节点交互”：

1. `mapErrorPanel`
2. `mapResultList`
3. POI 信息卡与结果列表
4. 真实高德 JS 初始化和 `resize / setFitView`
5. 节点编辑表单
6. 一键从项目计划生成节点草案

第三批做善后整合：

1. 把远端 `overviewStatusList` 融入本地 `overviewStatusCards`，不要退回远端较粗的状态列表。
2. 保留本地“待补资料与决策动作”命名。
3. 保留本地 AI 左栏、输入框、报告按钮和折叠体系。
4. 将远端所有机器文案映射为用户文案，不暴露 `ConnectError`、`debug`、`raw`、`payload` 等。

## 7. 高风险点

- 远端 `currentNode()` 仍会 fallback 到第一个节点；如果带进 AI 工作台，可能恢复用户讨厌的“默认 N-001”问题。融合时必须只允许节点页/地图节点入口使用 fallback，AI 项目综合不能用。
- 远端报告里说完整 10 轮仍有动态 DOM 和本地高德 JS Key 授权失败项，所以地图功能吸收后必须在本机重新跑 Selenium，不可照单全收。
- 远端新增 `requirements.txt` 的 `selenium>=4.44.0` 可以吸收，本地已安装 4.44.0。
- 远端把部分中文路径文件表现为“删除旧乱码路径 + 新增正常中文路径”，这是路径编码修复，不应当被误判为删除资料。
- 本地有大量 cache 和 Selenium 生成报告，融合前应只保护真正需要的代码和报告，不要把运行态 cache 当业务代码。

## 8. 建议验证顺序

每一批移植后都跑：

```powershell
node --check 90_p6_expert_dashboard\static\app.js
py -3.12 -m py_compile 90_p6_expert_dashboard\app.py
```

全部移植后再跑：

- `/api/dashboard` HTTP 200。
- `/api/amap/js-config` 不泄露完整 Key，只返回前端必要配置。
- `/api/nodes` CRUD。
- `/api/nodes/generate-from-plan`。
- AI 工作台默认项目综合，不默认 N-001。
- 生成报告空对话拦截。
- 地图搜索失败不显示机器错误。
- Selenium 至少 10 轮，覆盖地图、资料、节点、AI、报告、总览。

## 9. 下一步建议

先从远端后端接口移植开始，再接前端 DOM 和函数。不要一次改完四个文件后才测；每批都要留截图和 JSON 证据。
