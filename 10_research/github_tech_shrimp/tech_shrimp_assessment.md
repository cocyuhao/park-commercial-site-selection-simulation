# tech-shrimp GitHub 仓库初步评估

## 当前结论

- GitHub 公开页面显示 `tech-shrimp` 有 `Repositories 22`。
- GitHub REST API 首次请求返回 `public_repos=25`，后续匿名 API 请求触发 rate limit。
- 因为公开页面和 API 结果存在数量差异，本文件暂按“公开页面可见仓库 + API 首次返回的补充仓库”合并盘点，不视为最终导入清单。
- GitHub 插件本轮初始化失败，后续改用本机已登录的 `gh` CLI 和活动账号 `cocyuhao` 操作。
- 已使用 GitHub 原生 fork 将 24 个 `tech-shrimp` 公开仓库归档到 `cocyuhao` 账号。
- `tech-shrimp/WechatMoments` fork 失败，GitHub 返回 `HTTP 451: Repository access blocked`，不应绕过。
- 已创建索引仓库 [cocyuhao/tech-shrimp-open-source-archive](https://github.com/cocyuhao/tech-shrimp-open-source-archive)，保存清单、fork 结果和评估。
- 当前项目目录不是 git 仓库；没有把外部源码混入本项目主线。

## 与本项目相关性

| 相关性 | 仓库 | 语言 | Stars | License | 类别 | 来源 | 采用建议 |
|---|---|---:|---:|---|---|---|---|
| high | [tech-shrimp/GithubActionSample](https://github.com/tech-shrimp/GithubActionSample) | Python | 295 | MIT | automation_or_agent_skill | web_page_api | 可参考 GitHub Actions 和 agent 自动化流程；许可证复核后可 vendor |
| high | [tech-shrimp/agent-skills-examples](https://github.com/tech-shrimp/agent-skills-examples) | Python | 142 | MIT | automation_or_agent_skill | web_page_api | 可参考技能封装、任务分发和 agent 工作流；许可证复核后可 vendor |
| medium | [tech-shrimp/docker_installer](https://github.com/tech-shrimp/docker_installer) |  | 3172 | NOASSERTION | devops_container | web_page_api | 可参考部署思路；无明确许可证前不复制源码 |
| medium | [tech-shrimp/docker_image_pusher](https://github.com/tech-shrimp/docker_image_pusher) |  | 2901 | Apache-2.0 | devops_container | web_page_api | 可参考镜像推送和部署自动化；保留 LICENSE 后可 vendor |
| medium | [tech-shrimp/gemini-playground](https://github.com/tech-shrimp/gemini-playground) | JavaScript | 986 | MIT | model_gateway_or_playground | web_page_api | 可参考多模型 playground 和低成本模型调用界面 |
| medium | [tech-shrimp/gemini-balance-lite](https://github.com/tech-shrimp/gemini-balance-lite) | JavaScript | 781 | MIT | model_gateway_or_playground | web_page_api | 可参考模型网关、负载均衡和低成本模型路由 |
| medium | [tech-shrimp/deno-api-proxy](https://github.com/tech-shrimp/deno-api-proxy) | TypeScript | 448 | NOASSERTION | model_gateway_or_playground | web_page | 只做架构参考；无明确许可证前不复制源码 |
| medium | [tech-shrimp/grok-playground](https://github.com/tech-shrimp/grok-playground) | HTML | 412 | MIT | model_gateway_or_playground | web_page_api | 可参考模型体验页面和轻量前端交互 |
| medium | [tech-shrimp/gemini-proxy](https://github.com/tech-shrimp/gemini-proxy) | JavaScript | 262 | NOASSERTION | model_gateway_or_playground | web_page_api | 只做网关形态参考；无明确许可证前不复制源码 |
| medium | [tech-shrimp/qwen_autogui](https://github.com/tech-shrimp/qwen_autogui) | Python | 47 | NOASSERTION | model_gateway_or_playground | web_page | 可研究 GUI/agent 自动化思路；无明确许可证前不复制源码 |
| medium | [tech-shrimp/remotion_videos](https://github.com/tech-shrimp/remotion_videos) | Python | 27 | NOASSERTION | media_extraction_or_delivery | web_page_api | 后期可参考报告视频化；P1 阶段暂不需要 |
| medium | [tech-shrimp/x-article-auto-publisher-skill](https://github.com/tech-shrimp/x-article-auto-publisher-skill) | Python | 26 | NOASSERTION | automation_or_agent_skill | web_page_api | 可参考技能化发布流程；无明确许可证前不复制源码 |
| medium | [tech-shrimp/video_2_markdown_doubao](https://github.com/tech-shrimp/video_2_markdown_doubao) | Python | 11 | NOASSERTION | media_extraction_or_delivery | web_page_api | 后期可参考视频/音频/Markdown 转换；P1 阶段暂不需要 |
| low | [tech-shrimp/WechatMoments](https://github.com/tech-shrimp/WechatMoments) | Python | 1291 | Apache-2.0 | wechat_content | api_only_before_rate_limit | 与公园仿真主线弱相关；只做目录记录 |
| low | [tech-shrimp/me](https://github.com/tech-shrimp/me) |  | 931 | MIT | other | web_page_api_license_discrepancy | 个人主页/资料类，暂不导入 |
| low | [tech-shrimp/FreeWechatPush](https://github.com/tech-shrimp/FreeWechatPush) | Python | 97 | MIT | wechat_content | web_page_api | 与主线弱相关；只做目录记录 |
| low | [tech-shrimp/tech-shrimp](https://github.com/tech-shrimp/tech-shrimp) |  | 31 | NOASSERTION | other | web_page_api | 与主线弱相关；只做目录记录 |
| low | [tech-shrimp/hear_bird](https://github.com/tech-shrimp/hear_bird) | TypeScript | 5 | NOASSERTION | other | web_page_api | 与主线弱相关；只做目录记录 |
| low | [tech-shrimp/pet_care](https://github.com/tech-shrimp/pet_care) | TypeScript | 3 | NOASSERTION | other | web_page | 与主线弱相关；只做目录记录 |
| low | [tech-shrimp/open-code-test](https://github.com/tech-shrimp/open-code-test) | TypeScript | 0 | NOASSERTION | other | web_page | 测试仓库，暂不导入 |
| low | [tech-shrimp/ai-docs](https://github.com/tech-shrimp/ai-docs) |  | 0 | NOASSERTION | docs_or_content | web_page | 文档仓库，先保留链接 |
| low | [tech-shrimp/admiral](https://github.com/tech-shrimp/admiral) | TypeScript | 0 | Other | other | web_page_fork | fork 仓库，默认不导入 |
| low | [tech-shrimp/git_test](https://github.com/tech-shrimp/git_test) |  | 0 | NOASSERTION | other | api_only_before_rate_limit | 测试仓库，暂不导入 |
| low | [tech-shrimp/remote_test](https://github.com/tech-shrimp/remote_test) |  | 0 | NOASSERTION | other | api_only_before_rate_limit | 测试仓库，暂不导入 |
| low | [tech-shrimp/git](https://github.com/tech-shrimp/git) |  | 0 | NOASSERTION | other | api_only_before_rate_limit | 测试仓库，暂不导入 |

## 导入边界

- 必须先获得目标 GitHub 仓库 `owner/name`，并确认有写入权限。
- 必须逐仓库保留原始 URL、commit、LICENSE、README 和来源说明。
- `NOASSERTION` 或许可证不明的仓库，只保留链接、摘要和用途判断，不复制源码。
- MIT/Apache-2.0 仓库也不能直接混入主项目逻辑，建议放在 `vendor/tech-shrimp/<repo>` 或使用 submodule。
- 不建议把所有仓库“平铺进主项目”；更合理的是建立 `vendor` 目录或单独归档仓库，并在本项目只引用真正有用的脚本/模式。

## 当前优先级

1. 优先研究 `agent-skills-examples`，用于改进本项目的任务拆分、技能封装和交接自动化。
2. 优先研究 `GithubActionSample`，用于后续自动化核验、生成报告、敏感信息扫描和定期跑数。
3. 中等优先级研究 `gemini-balance-lite`、`gemini-proxy`、`deno-api-proxy`、`gemini-playground`、`grok-playground`，用于理解低成本模型网关和多模型路由，但不直接替代本项目的 `llm_router.py`。
4. `docker_*` 仓库可作为后期环境封装参考，不影响 P1 数据真实性核验主线。
5. `remotion_videos`、`video_2_markdown_doubao` 可作为后期交付表达参考，当前不进入 P1 主线。
