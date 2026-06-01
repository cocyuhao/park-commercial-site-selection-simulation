# tech-shrimp 仓库导入计划

## 当前状态

- 已尝试调用 GitHub 插件，但插件 MCP 初始化失败；后续只读下载 README 也失败。
- 已改用本机已登录的 `gh` CLI，当前活动账号为 `cocyuhao`。
- 已使用认证后的 GitHub API 获取 `tech-shrimp` 公开仓库清单，共 `25` 个。
- 已用 GitHub 原生 fork 将 `24` 个仓库归档到 `cocyuhao` 账号下。
- `tech-shrimp/WechatMoments` fork 失败，GitHub 返回 `HTTP 451: Repository access blocked`，不应绕过。
- 已创建索引仓库 `cocyuhao/tech-shrimp-open-source-archive`，用于保存清单、fork 结果、用途评估和导入边界。
- 当前本地目录不是 git 仓库；没有把外部源码混入本项目主线。

## 输出文件

- `10_research/github_tech_shrimp/tech_shrimp_repos_partial.csv`
- `10_research/github_tech_shrimp/tech_shrimp_repos_partial.json`
- `10_research/github_tech_shrimp/tech_shrimp_repos_gh_api_20260523.csv`
- `10_research/github_tech_shrimp/tech_shrimp_repos_gh_api_20260523.json`
- `10_research/github_tech_shrimp/fork_results_20260523.csv`
- `10_research/github_tech_shrimp/tech_shrimp_assessment.md`
- `10_research/github_tech_shrimp/archive_repo_README.md`

## 导入策略

不建议把外部仓库源码直接混入项目主线。建议二选一：

1. 独立归档仓库：创建一个专门的 GitHub 仓库保存 `tech-shrimp` vendor 镜像和评估报告。
2. 主项目 vendor 目录：在目标仓库中使用 `vendor/tech-shrimp/<repo>`，每个仓库保留 LICENSE、README、SOURCE.md。

## 必须满足的条件

- 用户确认目标 GitHub 仓库 `owner/name`。
- 仓库有明确开源许可证，或用户明确只做私有研究归档。
- 每个导入仓库记录原 URL、原 commit、许可证和用途。
- 无许可证仓库默认只保留链接和摘要，不复制源码。

## 本项目可优先参考

- `agent-skills-examples`：参考 skill/agent 任务封装。
- `GithubActionSample`：参考 GitHub Actions 自动化流程。
- `gemini-balance-lite`、`gemini-proxy`、`gemini-playground`、`grok-playground`：参考模型网关、多模型调用、低成本批处理。
- `docker_image_pusher`、`docker_installer`：参考部署和环境封装。
- `remotion_videos`、`video_2_markdown_doubao`：后期报告/视频/Markdown 交付可参考。

## 下一步

1. 用索引仓库记录本次 fork 和评估结果。
2. 如需在仿真项目中复用代码，只从 MIT/Apache-2.0 且确实有用的仓库中选择最小必要片段。
3. 对 `NOASSERTION` 仓库保持 fork/链接/摘要状态，不复制源码到本项目。
4. 针对 `agent-skills-examples` 和 `GithubActionSample` 做二次阅读，提炼可迁移到本项目的自动化模式。
