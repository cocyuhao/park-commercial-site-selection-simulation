# 远端局部融合与视觉工作台验证报告（2026-06-03）

## 1. 执行边界

- 未执行 GitHub 全量同步、未 reset、未 robocopy、未 push。
- 远端 main 仅通过 codeload ZIP 只读解包，对比后局部吸收同事的地图、资料、节点链路成果。
- 本地保留 AI 工作台、报告生成、项目总览视觉、资料池视觉、折叠、字体和留白改造。
- 本次主要改动集中在 `90_p6_expert_dashboard/app.py`、`static/app.js`、`static/index.html`、`static/styles.css`，新增 Selenium 验证脚本。

## 2. 融合内容

- 后端接入节点草案接口：新增、更新、删除、从项目计划生成草案。
- Dashboard 返回 `overview_status`：项目计划、地图定位、节点草案、POI、AI 上下文、报告可生成状态。
- 前端节点清单支持“新增节点 / 从项目计划生成”，详情区可编辑手动节点草案。
- 地图侧栏新增 POI/节点结果列表，点击 POI 会更新右侧详情；切换“全部 / 商业 POI / 候选节点”不会清空 loading 状态。
- 地图失败文案从技术错误改成人话提示，不直接展示 `ConnectError`。
- 修复节点详情折叠块 HTML：`<details>` 不再错误闭合为 `</section>`。
- AI 工作台保持默认“项目综合”，不默认锁定 N-001，也不默认显示“桃花源白房子”。

## 3. 地图空白修复

检查发现：

- `/api/amap/js-config` 可返回 key，但当前缺少 `AMAP_JS_SECURITY_CODE`，且使用 Web Service key 作为 JS key fallback。
- 浏览器 DOM 中 AMap canvas 存在，`amapReady=true`，但用户视角截图仍可能是一片浅色空白。
- `/api/amap/static-map` 本身可返回 PNG，说明后端静态图可用。

处理：

- 在地图渲染时预加载静态高德 PNG。
- 当 JS 配置缺少正式安全码或使用 Web Service key fallback 时，保留 AMap 标记/控件层，同时让静态高德底图作为可见底图兜底。
- 配置完整 JS key + security code 后，仍优先真实 AMap JS 底图。

证据截图：

- `40_quality_evidence/selenium_visual_integration_20260603/map_visual_after_fallback.png`
- 该截图显示真实底图、候选节点、POI 点和右侧结果列表，不再空白。

## 4. 验证结果

命令：

- `node --check 90_p6_expert_dashboard/static/app.js`
- `py -3.12 -m py_compile 90_p6_expert_dashboard/app.py`
- `py -3.12 -m py_compile 90_p6_expert_dashboard/qa/selenium_visual_integration_20260603.py`
- `py -3.12 90_p6_expert_dashboard/qa/selenium_visual_integration_20260603.py`

结果：

- JS 语法通过。
- Python 编译通过。
- API 冒烟通过：`/api/dashboard`、`/api/amap/js-config`、`/api/nodes` 创建/删除。
- Selenium 10 轮通过：`round_count=10`、`failure_count=0`。
- 自动测试节点已清理：`leftover_test_nodes=0`。

补充修正：

- 节点清单不再把裸分数作为主视觉，改为“推进优先级 + 第一条建议”。
- 节点详情新增“优先级解析与建议”：说明评分用途、当前建议、基础判断、资料门禁、字段缺口、POI、边界可信度。
- 分数保留为折叠解析中的辅助信息，只表示当前资料条件下的讨论优先级，不作为最终选址排名或推荐。
- 修正后再次执行 Selenium 10 轮，仍为 `round_count=10`、`failure_count=0`。

补充截图：

- `40_quality_evidence/selenium_visual_integration_20260603/node_priority_visual_after_fix.png`

Selenium 报告：

- `40_quality_evidence/selenium_visual_integration_20260603/selenium_visual_integration_20260603.json`

关键截图：

- AI 工作台：`40_quality_evidence/selenium_visual_integration_20260603/ai_workspace_visual.png`
- 地图兜底后：`40_quality_evidence/selenium_visual_integration_20260603/map_visual_after_fallback.png`
- 10 轮截图目录：`40_quality_evidence/selenium_visual_integration_20260603/`

## 5. 文献和资料吸收

本次没有把论文当作装饰，而是抽取对当前实现有直接约束的原则：

- Human-AI interaction：AI 工作台要显示当前能力边界、允许用户新建会话、保留历史、给出可纠正的上下文，而不是把系统判断强加给用户。
- Explainable AI / decision support：回答区要按“状态、依据、缺口、下一步”组织；技术状态默认折叠。
- Dashboard / BI decision support：总览不应是死文案，必须有可变化状态卡和下一步动作。
- GIS / retail site selection：地图不是装饰，应支持位置、POI、节点、结果列表之间的联动。
- Merge-conflict research：并行 Codex 协作时不要整仓覆盖，应先做只读三方对比、识别重叠文件、局部移植和验证。

参考资料（部分）：

1. Guidelines for Human-AI Interaction, CHI 2019: https://colab.ws/articles/10.1145%2F3290605.3300233
2. Microsoft Research: AAAI 2020 Tutorial - Guidelines for Human-AI Interaction: https://www.microsoft.com/en-us/research/articles/aaai-2020-tutorial-guidelines-for-human-ai-interaction/
3. Developing user-centered system design guidelines for explainable AI: https://link.springer.com/article/10.1007/s10462-025-11363-y
4. Design Principles for User Interfaces in AI-Based Decision Support Systems: https://link.springer.com/article/10.1007/s10796-021-10234-5
5. Formalizing Explanation Design through Interaction Patterns in Human-AI Decision Support: https://journals.sagepub.com/doi/full/10.3233/FAIA250644
6. How Human-Centered Explainable AI Interface Are Designed and Evaluated: https://arxiv.org/abs/2403.14496
7. Explanation User Interfaces: A Systematic Literature Review: https://arxiv.org/abs/2505.20085
8. From Explainable to Interactive AI: https://arxiv.org/abs/2405.15051
9. Reconciling business intelligence, analytics and decision support systems: https://www.sciencedirect.com/science/article/pii/S0167923621000701
10. Business intelligence and cognitive loads: Proposition of a dashboard adoption model: https://www.sciencedirect.com/science/article/pii/S0169023X2400034X
11. A Dashboard to Support Management of Business Analytics Capabilities: https://www.tandfonline.com/doi/abs/10.1080/12460125.2015.994335
12. Visualizing statistical linked knowledge for decision support: https://journals.sagepub.com/doi/10.3233/SW-160225
13. The retail site location decision process using GIS and AHP: https://www.sciencedirect.com/science/article/pii/S0143622813000714
14. User Interfaces for Geographic Information: https://library.esri.com/docs/5853.pdf
15. Predicting merge conflicts considering social and technical assets: https://link.springer.com/article/10.1007/s10664-023-10395-8
16. Predicting Merge Conflicts in Collaborative Software Development: https://arxiv.org/abs/1907.06274
17. Towards accurate recommendations of merge conflicts resolution strategies: https://www.sciencedirect.com/science/article/abs/pii/S0950584923001878
18. Towards Semi-Automated Merge Conflict Resolution: https://conf.researchr.org/details/ease-2024/ease-2024-papers/9/Towards-Semi-Automated-Merge-Conflict-Resolution-Is-It-Easier-Than-We-Expected-
19. Program Merge Conflict Resolution via Neural Transformers: https://arxiv.org/abs/2109.00084
20. Can Program Synthesis be Used to Learn Merge Conflict Resolutions?: https://arxiv.org/abs/2103.02004
21. An empirical investigation into merge conflicts and their effect on software quality: https://ics.uci.edu/~iftekha/pdf/J4.pdf
22. AgenticFlict: Merge Conflicts in AI Coding Agent Pull Requests: https://arxiv.org/abs/2604.03551

## 6. 仍需注意

- 当前本地 `.env` 缺少正式 `AMAP_JS_API_KEY` / `AMAP_JS_SECURITY_CODE`，所以地图采用“JS 控件 + 静态高德底图兜底”。这不是最终理想状态，但比空白地图可用。
- `overview_status.can_generate_review_report=false`，因为当前没有已采用项目计划。上传并采用项目计划后，报告可生成状态才应变为可用。
- 本次未 push GitHub，避免与同事远端提交冲突。
