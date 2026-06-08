# 2026-06-03 同事地图/资料/节点链路已局部吸收，准备提交 GitHub
- 当前正在做：用户已确认需要把同事负责的地图/资料/节点成果和本地 AI 工作台/报告/视觉成果合并后推送 GitHub；仍禁止整仓覆盖式同步。
- 上次停在：远端 main 只读源码包已下载并比对，最新远端提交为 `9815493c16e0e5bf3536cf73c22828328b61e8f4`；本地已吸收同事核心链路，并保留本地 AI 工作台、节点优先级解析、地图空白兜底和 Selenium 证据。
- 已导入同事证据：`40_quality_evidence/地图_资料_节点_验证报告_20260603.md`、`40_quality_evidence/地图_资料_节点_验证报告_20260603_任务二至六.md`、`40_quality_evidence/selenium_map_material_node_overview_20260603.json`。
- 关键决定：同事报告中的旧端口、本机路径、动态 DOM 失败和高德授权失败只作为历史证据；当前最终结论以本地 `40_quality_evidence/remote_integration_execution_report_20260603.md` 和 `selenium_visual_integration_20260603` 证据为准。
- 当前实现：地图 POI/节点列表、loading 竞态保护、搜索错误人话提示、节点新增/编辑/删除/计划生成、项目总览状态、AI 默认项目综合、报告生成、节点优先级建议均已接入；地图主路径仍是高德 JS 交互地图，静态高德底图只在 JS Key/security code 不完整导致空白时兜底。
- 当前验证：`node --check` 通过；`py_compile` 通过；Selenium 10 轮完整回归 `round_count=10 failure_count=0`。
- 当前边界：P3 未闭合前，所有输出仍为 `needs_review / not_final`；节点分数只表示讨论优先级，不是最终推荐。

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
