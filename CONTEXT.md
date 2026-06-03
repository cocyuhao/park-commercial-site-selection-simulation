# 2026-06-03 高德 JS 地图真实可用改造
- 当前正在做：已完成空间地图专项改造，页面主路径改为真实高德 JS API 2.0 地图，不再用静态图假装地图。
- 上次停在：地图可显示高德 canvas、项目位置、候选节点、商业 POI、搜索结果和右侧结果列表；点击 POI 有信息卡。
- 关键决定：地图搜索失败统一显示产品话术，不显示后端异常原文；失败时保留输入，地图不崩；候选节点可跟随当前搜索项目生成待复核位置草案，但不套用奥森评分。
- 当前验证：`node --check` 通过；`py -m py_compile` 通过；Selenium + Chrome 10 轮点击测试通过，失败 0；失败搜索场景通过。
- 当前报告：`40_quality_evidence/地图_资料_节点_验证报告_20260603.md`。
- 当前边界：地图点位仍是待复核位置关系，不是 DWG 坐标、面积、图层或真实动线；未把高德 Key 写入代码或报告。

# 2026-06-03 地图 loading、资料链、节点与总览联动
- 当前正在做：已完成任务二至六的产品链路改造，范围限定在地图、资料导入、节点生成和项目总览。
- 上次停在：地图 loading 竞态 3 轮 Selenium 通过；资料支持项目计划一键入口和分项用途；节点支持新增、编辑、删除、启停和从项目计划生成待复核草案；总览动态展示决策前置条件。
- 关键决定：资料采用后不再强制弹出右侧抽屉，避免遮挡后续操作；节点表单编辑时暂停自动刷新，避免用户输入被清空。
- 当前验证：`py -m py_compile 90_p6_expert_dashboard\app.py` 通过；`node --check 90_p6_expert_dashboard\static\app.js` 通过；Selenium 竞态 3/3 通过，完整 10 轮已执行但仍有动态 DOM 和本地高德 JS Key 授权失败项。
- 当前报告：`40_quality_evidence/地图_资料_节点_验证报告_20260603_任务二至六.md`；Selenium JSON：`40_quality_evidence/selenium_map_material_node_overview_20260603.json`。

# 2026-06-03 GitHub 最新更新已导入
- 当前正在做：已从 GitHub `origin/main` 快进同步到最新提交 `4e5cb7b Improve AI workbench sessions and report flow`。
- 上次停在：本地原先位于 `74b6aeb`，工作区干净，确认后执行 `git fetch origin main --prune` 和 `git merge --ff-only origin/main`。
- 关键决定：只做快进同步，不创建分支、不重置历史；当前机器 `py` 指向 Python 3.13，缺少依赖时按 `requirements.txt` 补齐。
- 当前验证：DeepSeek API 验证 `PASS=4 FAIL=0`；PDF 表格验证 `PASS=4 FAIL=0`。
- 当前边界：验证脚本更新了 `40_quality_evidence/verify_deepseek_api_report.json` 和 `40_quality_evidence/postman_deepseek_collection.json`，属于本轮验证产物。

# 2026-06-02 TGI/POI 供需缺口改动已恢复
- 当前正在做：已把丢失的 TGI/POI 供需缺口和分析报告功能重新写回磁盘，并重启 `http://127.0.0.1:8765/`。
- 上次停在：用户发现页面还能看，但磁盘文件不在；原因是旧 uvicorn 进程仍在内存里跑旧代码，磁盘工作区没有保存这些改动。
- 关键决定：资料池只读取网页外部上传资料，不再自动把 `CAD图及其计划` 中的奥森样例文件当成用户项目。
- 当前实现：`60_model/simulation/demand_gap.py`、`/api/supply-gap`、`/api/visitor-simulation`、`/api/reports/site-selection`、前端“分析报告”页和资料闭合中心缺口面板已恢复。
- 当前验证：`node --check` 通过；`py -m py_compile` 通过；API 烟测 `passed=5 failed=0`；浏览器 `#report` 页确认显示“分析报告”和 2 个下载入口。
- 当前边界：缺少外部上传客流/TGI资料时，缺口计算只显示阻塞，不用内置奥森资料硬算。

# 2026-06-02 B/C/D 验收入口
- 主报告：`80_delivery/codex_bcd_validation_and_tool_report_20260602.md`。
- 本地服务：`http://127.0.0.1:8000` 已跑通。
- 核心门禁：`checks=725 failures=0`；PDF 表格验证 PASS；AMap 烟测 `status=ok`；真实 Key 值扫描 `findings=0`。
- 浏览器验证：Codex Browser 窄屏视图切换、地图搜索、前端仿真、AI 工作台均通过；Chrome 1440x1000 截图在 `90_p6_expert_dashboard/qa/browser_desktop_map_20260602.png`。
- WARN：DeepSeek `/v1/models` 本轮出现 1 次 SSL EOF，但业务 chat、JSON 输出、历史样本重现通过。
- 边界：P3 未闭合前，全部输出仍为 `needs_review / not_final`，不得给最终排序、收益预测、ROI 或最终推荐。

# 当前上下文

- 当前正在做：本地已完全同步到 GitHub `main` 最新提交 `d43db1c60f9976f04399de43058d1ee36378a65f`，提交信息为 `Polish park simulation UI workflow`。
- 同步方式：先用 GitHub API 确认远端最新提交，再 `git fetch origin main`，最后 `git reset --hard origin/main`；本地 `.env` 保留且未提交。
- 依赖补充：已按 `requirements.txt` 执行 `py -3.12 -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`，新增/升级 `python-multipart==0.0.30`。
- 协作补充：新增 `00_control/team_codex_division.md`，按双人 Codex 泳道分工，不再依赖老派固定前后端分工；新增 `00_control/sync_from_github_main.ps1`，把同步、依赖补齐和门禁验证固化为一条命令。
- 关键决定：P3 门禁未闭合前，仿真只输出 `needs_review / not_final` 的检查结果，不输出最终排序、收益预测或推荐结论；外部地点只做地图预览，不套用奥森评分。
- 当前验证：`node --check 90_p6_expert_dashboard\static\app.js` 通过；`py -3.12 -m py_compile 90_p6_expert_dashboard\app.py 60_model\db\store.py 60_model\simulation\engine.py 60_model\simulation\validators.py` 通过；`py -3.12 30_extraction\scripts\verify_project_implementation.py` 输出 `checks=725 failures=0`。
