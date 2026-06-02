# Codex 双人协作分工

## 当前同步基线

- 远端仓库：`https://github.com/cocyuhao/park-commercial-site-selection-simulation`
- 当前本地基线：`d43db1c60f9976f04399de43058d1ee36378a65f`
- 基线提交：`Polish park simulation UI workflow`
- 同步原则：每轮开始先同步 `origin/main`，再开自己的工作分支或明确自己的文件边界。

## 分工原则

两个人都有 Codex，不按“一个人写后端、一个人写前端”的老派方式固定到死，而是按系统风险和验证责任分泳道。

| 泳道 | 负责人 | Codex 主要做什么 | 不要做什么 |
|---|---|---|---|
| A. 数据与后端契约 | 同事优先 | SQLite schema、FastAPI API、simulation dry-run、上传解析入池、字段状态解释 | 不改前端视觉和交互布局，除非只为接口自测加极小入口 |
| B. 专家工作台与交互 | 本机当前优先 | 页面任务流、地图/节点/AI 工作台、表格展示、浏览器验证、可用性修复 | 不在前端重新计算评分，不绕过后端 `needs_review / not_final` 口径 |
| C. 证据链与门禁 | 谁发版谁负责 | 跑 `verify_project_implementation.py`、检查 Key 泄露、确认输出状态、更新交接 | 不把 DeepSeek/AI 草稿直接升为 checked/final |
| D. 真实校准/P3 输入 | 双方协作，Codex 主导门禁 | DWG 转换工作单、真实客流、转化率、收益成本、运营授权缺口闭合 | 不用 PPT 或 AI 猜测回填真实校准 |
| E. GitHub 同步与发布 | 当轮提交者 | 拉取远端、解决冲突、提交、推送、记录 commit 与验证结果 | 不提交 `.env`、运行日志、无关缓存或半成品截图 |

## 每轮开始动作

```powershell
cd "C:\Users\Yy199\Desktop\仿真设计"
powershell -NoProfile -ExecutionPolicy Bypass -File .\00_control\sync_from_github_main.ps1
```

该脚本会优先执行 `git fetch + git reset --hard origin/main`，失败时用 `gh auth token` 做认证 fetch，再失败才使用 GitHub ZIP 镜像兜底；同时会安装/更新 `requirements.txt` 中的 Python 依赖，并运行最小门禁。

如果只想查看远端最新提交，使用：

```powershell
gh api -X GET "repos/cocyuhao/park-commercial-site-selection-simulation/commits?per_page=5"
```

## 文件边界

当轮修改前先声明本轮泳道，优先只动相关文件：

- 后端契约：`90_p6_expert_dashboard/app.py`、`60_model/db/`、`60_model/simulation/`、`60_model/scripts/import_existing_outputs.py`
- 前端交互：`90_p6_expert_dashboard/static/`、必要的 `90_p6_expert_dashboard/qa/`
- 证据/数据：`30_extraction/`、`40_quality_evidence/`、`50_external_gis/`、`70_outputs/processed_tables/`
- 控制与交接：`00_control/`、`progress.md`、`findings.md`、`handoff_next_chat.md`、`next_chat_prompt.md`、`CONTEXT.md`

跨泳道修改允许，但必须在交接里写清楚原因、验证命令和剩余风险。

## 合并前验证

最小门禁：

```powershell
node --check 90_p6_expert_dashboard\static\app.js
py -3.12 -m py_compile 90_p6_expert_dashboard\app.py 60_model\db\store.py 60_model\simulation\engine.py 60_model\simulation\validators.py
py -3.12 30_extraction\scripts\verify_project_implementation.py
```

涉及网页体验时，再启动本地服务并用浏览器确认：

```powershell
py -3.12 60_model\scripts\import_existing_outputs.py
py -3.12 -m uvicorn app:app --host 127.0.0.1 --port 8000 --app-dir 90_p6_expert_dashboard
```

## 当前禁止升级的结论

- `simulation dry-run` 不是正式 P4 仿真。
- `P4 feedback draft` 不是最终推荐。
- DeepSeek、上传解析、地图 POI、评分解释都保持 `needs_review / not_final`。
- DWG 未完成可信转换前，不输出面积、图层、坐标、动线或最终空间结论。

## 冲突处理

1. 先同步远端最新提交，确认谁的提交在前。
2. 如果冲突发生在同一泳道，后提交者负责修复并补验证。
3. 如果冲突跨泳道，优先保留后端契约和证据门禁，再调整前端展示。
4. 不确定时不要靠聊天猜结论，先跑本地接口/门禁，再写交接。
