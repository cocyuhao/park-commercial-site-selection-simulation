# GPT 管理者 + DeepSeek 执行者架构

## 角色分工

本项目采用“主 agent 管理、DeepSeek 执行”的混合模型架构。

| 角色 | 负责内容 | 不负责内容 |
|---|---|---|
| 主 agent / Codex 或等价高能力模型 | 项目判断、方法选择、证据门禁、风险控制、最终结论、交接更新、任务拆分 | 大量重复草稿和低风险批处理不应全部亲自做 |
| DeepSeek Pro | 页面分类、表格主题分类、证据候选草稿、README 摘要、报告段落初稿、个性化需求和仿真场景草稿、低风险批量整理 | 最终真实性判断、正式证据入账、商业结论、凭据处理、GitHub 远程写入、概率/收益/排序的最终裁决 |
| 本地 Python | 抽取、清洗、统计、质量检查、证据台账写入、GIS/POI/路径 API 调用、概率仿真、收益测算、候选点排序 | 主观商业解释和报告润色 |
| GitHub/gh | fork、索引仓库、清单上传、远端验证 | 不决定哪些源码可以混入主项目 |

## DeepSeek-first 默认策略

从 2026-05-26 起，默认采用 DeepSeek-first：

1. 能拆解、能复核、可用脚本验证的任务，先交给 DeepSeek 做理解、方案、草稿、代码草案、核验表和失败原因分析。
2. 中等难度任务也可以先交给 DeepSeek，只要输出进入 `draft` 或 `needs_review`，并保留本地可复跑验证。
3. Codex 默认不亲自完成大段整理、批量分类、报告草稿和一般性实现方案；Codex 负责调度 DeepSeek、本地执行、关键补丁和阶段门禁。
4. 落地门禁可以交给 DeepSeek 做“预审”和“解释”，但最终通过/失败应落在本地脚本 exit code、行数、字段、状态和固定门禁值上，避免门禁变成不可复跑的口头判断。
5. 如果 DeepSeek 给出代码草稿，Codex 只负责最小必要落地、编译/运行和验证，不重写整套方案。
6. 在用户没有明确要求进入 P2 前，P1 收口后的批量整理、待核验清单整编、交接同步和失败原因分析仍默认优先交给 DeepSeek 或本地脚本；P2 启动和后续建模仍由 Codex 或等价高能力主 agent 主导。

## 调度原则

1. 主 agent 先定义任务边界、输入文件、输出状态和复核门禁。
2. DeepSeek 只接收低到中风险任务，输出必须是 `draft` 或 `needs_review`。
3. DeepSeek 输出不得直接写入 `evidence_ledger.csv` 的 `checked` 行。
4. 任何 DeepSeek 结果进入正式材料前，必须经过本地脚本、证据 ID 或人工规则复核。
5. 主 agent 保留最终否决权，尤其是数据真实性、选址结论、收益测算和风险判断。
6. 人群概率仿真采用“Python 计算 + DeepSeek 辅助解释”：DeepSeek 可以提出待测场景，不能替代随机仿真、概率校准和最终排序。

## 当前任务路由

权威路由表：

- `60_model/configs/llm_task_routing.csv`

运行代码：

- `60_model/src/llm_router.py`

真实调用 smoke test：

- `60_model/scripts/run_deepseek_smoke_test.py`

调用记录：

- `60_model/llm_runs/deepseek_smoke_test_latest.json`

## 下一步应如何用 DeepSeek

优先把这些任务交给 DeepSeek：

1. 对 329 张 PDF 原生表格做主题分类草稿。
2. 对 PDF/PPT 页面做客流、画像、TGI、POI、消费、收益、缺口标签。
3. 从表格中生成“候选证据”草稿，但不直接入账。
4. 对 `tech-shrimp` 高相关仓库 README 做摘要和可借鉴点初判。
5. 把用户临时提出的个性化需求整理成结构化场景草稿，例如人群、时间、天气、动机、消费触发和风险点。
6. 对 P0 工作单、入口/节点候选、补字段清单、现场核验问题等做批量整理，输出人工核验包草稿。

## 上下文投喂边界

为节约主 agent / GPT-5.5 使用量，DeepSeek 可以接收更完整的项目上下文，包括：

- `progress.md`、`handoff_next_chat.md`、`task_plan.md`、`findings.md` 等交接文件；
- `evidence_ledger.csv`、POI 候选表、入口/节点候选表、路径复核表等中间表；
- 质量报告、DeepSeek 既有 draft/needs_review 输出、本地复核队列；
- 低风险脚本结构和字段 schema。

但凭据处理仍由本地 Python 完成：

- DeepSeek API 调用脚本可以通过本地 `.env` 或进程环境变量读取 `DEEPSEEK_API_KEY`。
- 高德脚本可以通过本地 `.env` 或进程环境变量读取 `AMAP_WEB_SERVICE_KEY`。
- 不把 `.env` 的真实内容作为 prompt 上下文发送给模型，也不把真实 Key 写入 raw 输出、CSV、JSON、Markdown 报告或交接文件。
- 如果 DeepSeek 需要调用外部 API，应由本地脚本读取凭据并封装请求，DeepSeek 只接收脱敏结果或结构化输入。

不应交给 DeepSeek：

1. 判断某个数字是否为事实；
2. 判断商家最终应该开在哪里；
3. 写入最终报告结论；
4. 操作 Key、GitHub 写入或外部 API 凭据；
5. 修改验证脚本的安全边界；
6. 直接输出概率、收益、排序或最终仿真结论。

## 人群仿真分工计划

- P2：只有在用户明确要求启动时，才由本地 Python + Codex 建立游客分群、需求触发、选择概率和缺口计算原型；DeepSeek 只辅助整理场景草稿。
- P3：接入真实目标公园后，用真实入口、客流、POI、经营字段和用户偏好校准参数。
- P4：本地 Python 执行游客 Agent 仿真，输出 baseline、候选方案、压力场景和敏感性分析。
- P5：DeepSeek 可以根据已通过门禁的结构化结果起草解释，但最终报告只引用 checked 证据和已复核模型输出。
