# LLM 分工路由

## 目标

在保证真实性和可审计的前提下降低成本：简单、重复、量大的任务优先交给 DeepSeek；高风险、最终判断和安全相关任务保留给 Codex / 高能力主 agent、本地脚本和人工规则。

## 凭据规则

- DeepSeek Key 只从 `DEEPSEEK_API_KEY` 环境变量读取。
- 不写入 `.env.example` 以外的任何具体值。
- 不在日志、报告、CSV、JSON 中打印 Key。
- 批处理脚本只记录模型名、任务名、输入摘要、输出路径、状态，不记录原始 Key。

## 模型选择

| 模型 | 用途 | 默认状态 |
|---|---|---|
| `deepseek-v4-pro` | 大量低到中风险分析、分类、草稿、结构化辅助 | 默认 DeepSeek 模型 |
| `deepseek-v4-flash` | 极低风险的快速摘要、标签建议、重复内容归类 | 可选 |
| Codex / 高能力主 agent | 证据链规则、最终结论、高风险代码、架构和安全判断，以及 P2 是否启动 | 保留 |
| 本地 Python | 抽取、清洗、核验、可复跑计算、数值统计 | 主线 |

## 任务细分

| 任务 | 量级 | 风险 | 默认执行者 | 输出状态 | 复核方式 |
|---|---:|---|---|---|---|
| PDF/PPT 原始文本抽取 | 大 | 中 | 本地 Python | checked | 页数/长度/表格核验 |
| 页面主题分类 | 大 | 低 | DeepSeek Pro | draft | 关键词和抽样复核 |
| 表格候选分类 | 大 | 低 | DeepSeek Pro | draft | PyMuPDF 表格摘要 + 抽样 |
| 表格左右栏拆分规则建议 | 中 | 中 | DeepSeek Pro | draft | 本地脚本验证 |
| 证据候选草稿 | 大 | 中 | DeepSeek Pro | needs_review | 写入前人工/规则核验 |
| `evidence_ledger.csv` 正式入账 | 中 | 高 | 本地 Python + Codex 复核 | checked | 来源页、单位、原文片段 |
| PPT 假设回查 | 中 | 高 | Codex + 本地脚本 | checked/needs_review | PDF/GIS/公式对照 |
| 高德 POI 抓取 | 中 | 高 | 本地 Python | raw/checked | API 日志、坐标、距离 |
| POI 分类标签草稿 | 大 | 中 | DeepSeek Pro | draft | 高德 typecode 和抽样复核 |
| 供需缺口计算 | 中 | 高 | 本地 Python | checked | 参数表和敏感性分析 |
| 报告段落初稿 | 大 | 低 | DeepSeek Pro | draft | 证据 ID 对照 |
| 最终报告结论 | 小 | 高 | Codex/人工规则 | checked | 证据链完整性 |
| GitHub 仓库 README 摘要 | 大 | 低 | DeepSeek Pro | draft | 许可证和用途人工复核 |
| GitHub 远程写入/导入 | 小 | 高 | GitHub 插件/Codex，需目标仓库 | checked | 保留 LICENSE/来源/commit |

## 使用边界

- DeepSeek 可以帮忙“整理、分类、起草”，不能代替真实性核验。
- 所有 DeepSeek 结果必须在文件名或字段中标注 `draft`。
- 没有证据 ID 的 DeepSeek 报告段落不能进入最终材料。
- 外部仓库代码不能因为模型建议就直接并入主项目。
- 在用户没有明确要求进入 P2 前，P1 收口后的批量整理、待核验清单整编和交接细化继续默认优先交给 DeepSeek 或本地脚本，不自动切到 P2 主线。
