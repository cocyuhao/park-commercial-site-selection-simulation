# 插件和工具路由

## 路由原则

- 主线用本地 Python，保证可复跑和可审计。
- 插件只在它能提高真实性、效率、验证或交付质量时调用。
- 凭据和外部 API 使用必须可追踪、可关闭、可复现。

## 能力分工

| 场景 | 首选能力 | 使用方式 | 不使用条件 |
|---|---|---|---|
| PDF/PPT 抽取 | 本地 Python、`data-analysis` | PyMuPDF、python-pptx 抽文本和元数据 | 不把全量内容塞进对话 |
| 数据质量检查 | 本地 Python、`data-analysis` | 空值、重复、单位、异常、口径检查 | 不跳过质量报告 |
| 方法和风险选择 | `decision-hygiene` | 记录关键选择、替代方案和风险 | 不为了新奇选择工具 |
| 高德 POI/路径 | 高德 Web 服务 API | 地理编码、POI、步行路径、竞品补数 | Key 未配置或目标公园未明确时不批量调用 |
| 专家网站/交互看板 | `Build Web Apps`、`frontend-design` | P6 做决策驾驶舱、GIS 地图、场景实验室、证据追溯、参数调节和导出界面 | 数据底稿、API 契约和模型口径未稳定前不做视觉包装 |
| 浏览器核验 | `Browser`/Chrome | 检查本地看板、地图、交互状态 | 无前端产物时不调用 |
| UI 灵感和原型 | Flowus 学习材料、Mobbin、60fps、Spotted in Prod、Figma/Pencil | 学习信息架构、动效节奏和质感；先由人定义专家工作流，再让 AI 辅助生成 | 不直接照搬设计，不让 AI 替代行业判断 |
| 地图和空间可视化 | MapLibre GL JS、deck.gl | 后期展示边界、入口/节点、POI、步行圈层、热力层、流线和仿真轨迹 | 边界、坐标和 POI 口径未标注来源时不进入专家结论 |
| 图表和专家表格 | Apache ECharts、TanStack Table | 展示收益区间、敏感性、概率分布、证据清单和模型输入表 | 不用图表掩盖证据不足；表格字段未定义前不做复杂筛选 |
| 表格交付 | `Spreadsheets` 或本地 CSV/XLSX | 生成可审计底稿 | 简单 CSV 优先本地生成 |
| 报告交付 | `Documents` | 最终报告成稿 | 数据未核验前不生成正式报告 |
| PPT 交付 | `Presentations` | 最终汇报 deck | 不用 PPT 替代分析底稿 |
| API 契约和回归测试 | Postman / Postman CLI | P2 开始记录本地模型 API、DeepSeek smoke test、高德 smoke test 的请求契约；P4 扩展为仿真 API 回归测试 | P1 不作为主线工具；不在 collection 或环境文件中保存真实 Key |
| 安全检查 | `Codex Security` 或本地扫描 | 检查 Key、敏感信息、输出泄露 | 小范围本地文件可先用本地扫描 |
| 外部资料查证 | Web 官方文档/GitHub | API、库、方法论、版本新鲜度 | 不用过时记忆替代官方资料 |
| GitHub 远端操作 | GitHub 插件，失败时用 `gh` CLI | 仓库盘点、fork、索引仓库、清单上传 | 写入前先确认账号、目标、许可证和来源保留 |

## 高德 API 使用约定

- 运行前从环境变量读取 `AMAP_WEB_SERVICE_KEY`。
- 每次请求记录 API 名称、时间、参数摘要、状态码、结果条数。
- 原始返回保存到 `50_external_gis/`，清洗表保存到 `70_outputs/processed_tables/`。
- 不在日志中打印完整 Key。

## 安装补库原则

缺少 Mesa、SimPy、OR-Tools、OSMnx 等库时：

1. 先查官方文档和活跃维护状态。
2. 优先使用项目本地虚拟环境。
3. 记录安装决策到 `00_control/decisions.md`。
4. 安装后写入依赖文件或环境说明。

## Postman 使用约定

- Postman 属于 API 契约、联调和回归验证工具，不属于证据真实性来源。
- P2 只规划 collection 结构：本地模型 API、DeepSeek smoke test、高德 smoke test、参数校验和错误场景。
- P4 再把 collection 扩展为仿真服务回归测试，覆盖 baseline、候选方案、压力场景和异常输入。
- P6 可把 Postman collection/report 作为专家网站验收附件，但不能在网站或导出文件中保存真实 Key。
- collection、environment、report 中只能保存变量名和脱敏参数摘要，不保存真实 `DEEPSEEK_API_KEY` 或 `AMAP_WEB_SERVICE_KEY`。
- 命令行优先使用 Postman CLI；如需兼容旧 collection 或 CI 生态，再评估 Newman。

## DeepSeek 低成本批处理路由

DeepSeek 作为低成本辅助模型接入，但只处理简单、重复、量大的中间任务。具体规则见：

- `00_control/llm_routing.md`
- `60_model/configs/llm_task_routing.csv`
- `60_model/src/llm_router.py`

默认模型：

- `deepseek-v4-pro`：批量分类、证据候选草稿、报告初稿、README 摘要。
- `deepseek-v4-flash`：可选低风险摘要。

禁止交给 DeepSeek：

- 最终商业结论；
- 正式证据入账；
- 凭据处理；
- 高风险代码合并；
- GitHub 远程写入；
- 数据真实性最终裁定。

DeepSeek 输出必须标注为 `draft` 或 `needs_review`，进入证据链前必须复核。

## GitHub 操作补充

本轮 GitHub 插件初始化失败，已使用本机 `gh` CLI 和活动账号 `cocyuhao` 完成 `tech-shrimp` 仓库归档。后续 GitHub 操作优先顺序：

1. 先尝试 GitHub 插件；
2. 插件失败时使用 `gh` CLI；
3. 对外部仓库优先使用 GitHub 原生 fork 或索引仓库；
4. 不把无许可证或用途不明的外部源码复制到本项目主线。
