# Agent / 编辑器影响面审计 2026-06-09

- 状态：review
- 扫描根：8
- 扫描文件：4544
- 命中：3746
- high：0
- severity：{'info': 2213, 'medium': 1180, 'archive': 306, 'context': 47}
- area：{'project_workspace': 3319, 'codex_global': 54, 'agents_global': 1, 'claude_global': 1, 'codex_vscode': 8, 'vscode_user': 360, 'cursor_user': 3}

## 高风险当前影响源
- 未发现 high 当前影响源。

## 解释
- 本报告用于区分“无害历史记录”和“会影响当前项目的新旧冲突面”。
- 不建议删除 session/history/rollout；应优先改写项目交接文件、全局记忆补丁、测试夹具和客户可见产物。
