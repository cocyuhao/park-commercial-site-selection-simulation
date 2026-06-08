# 老板方法重基线后的旧文件可信度审计（2026-06-04）

> 状态：第一版审计清单。  
> 目的：在继续实现前，先判断旧文件哪些仍可信、哪些需要降级、哪些必须重写。  
> 核心结论：可复跑证据和工具仍有价值；“完整仿真已完成”类结论不可信；DeepSeek 草稿、节点分数和 P4 口径必须降级。

## 1. 审计原则

老板六份方法资料把项目从“POI/TGI 缺口 + 页面展示”推向“证据层 + 人群状态 + 行为程序 + 空间选择 + 消费转化 + 宏观校准 + 报告解释”。因此旧文件不能按以前的完成标准继续使用。

本审计只判断可信度，不删除文件。

分级：

- A：仍可信，可作为底座。
- B：可继续用，但必须改口径。
- C：只保留为草稿候选。
- D：必须降级或重写。
- E：新方向缺失，需要新增。

## 2. A 仍可信：证据底座与可复跑工具

| 文件/目录 | 保留原因 | 使用边界 |
|---|---|---|
| `40_quality_evidence/evidence_ledger.csv` | 证据台账是项目可追溯底座 | 只相信有来源、有状态、可回查的行；DeepSeek 不能直接写 checked |
| `30_extraction/tables/pdf_native_tables.jsonl` | PDF 表格抽取结果可复跑、可回查 | 表格抽取不是商业结论 |
| `30_extraction/scripts/verify_pdf_tables.py` | 验证表格抽取质量 | 只能证明抽取链路，不证明仿真完成 |
| `60_model/scripts/verify_deepseek_api.py` | API 健康验证 | 只能证明 API 可用，不证明 DeepSeek 输出可信 |
| `50_external_gis/scripts/run_amap_smoke_test.py` | 高德 API 烟雾测试 | 只能证明服务可用，不证明 POI 足够或地图逻辑完整 |
| `.env` 规则与 key 不落盘约束 | 安全底线 | 继续严格保留 |
| `AGENTS.md` | 当前协作规则和边界 | 需按本轮重基线持续补充 |

## 3. B 可继续用但必须改口径：产品壳与验证证据

| 文件/目录 | 可用部分 | 必须改口径 |
|---|---|---|
| `90_p6_expert_dashboard/` | AI 工作台、资料池、项目总览、报告入口是可用产品壳 | 不能说仿真已完成；只能说是交互工作台原型 |
| `90_p6_expert_dashboard/static/app.js` | 视觉、折叠、节点优先级解释、报告按钮状态 | 不得把前端状态卡当真实模型结论 |
| `90_p6_expert_dashboard/app.py` | API 聚合、缓存、报告生成、地图兜底 | API 输出仍需 `needs_review/not_final` 边界 |
| `40_quality_evidence/selenium_*` | 浏览器/交互验证证据 | Selenium 证明页面可用，不证明真实人群仿真准确 |
| `40_quality_evidence/*视觉验证报告*` | 人眼/UI 质量证据 | 只属于产品体验验证 |
| `README.md` / `CONTEXT.md` / `ARCHITECTURE.md` | 项目说明可保留 | 需避免继续沿用旧 P4 完成口径 |

## 4. C 草稿候选：可吸收但不能当完成

| 文件/目录 | 草稿价值 | 风险 |
|---|---|---|
| `70_outputs/processed_tables/p2_persona_state_profiles_20260604.csv` | 可作为 HumanLM 状态 schema 的雏形 | 未经真实数据校准 |
| `70_outputs/processed_tables/p2_behavior_program_templates_20260604.csv` | 可作为 ROTE 行为程序的雏形 | 不能直接运行成最终行为 |
| `70_outputs/processed_tables/p2_simulation_validation_targets_20260604.csv` | 可作为验证指标清单雏形 | 指标需要真实几何/客流/轨迹/消费数据闭合 |
| `60_model/simulation/persona_behavior.py` | 可作为 schema/验证思路草稿 | 不能作为主仿真引擎扩写 |
| `60_model/llm_runs/*` | 可追踪 DeepSeek 输出历史 | 只能用于复核和改写，不可直接入账 |
| `80_delivery/ai_chat_reports/CHAT-*.md` | 可以看报告格式和测试路径 | 多数是测试报告，不是客户正式交付 |

## 5. D 必须降级或重写：旧完成声明与神秘分数

| 对象 | 问题 | 新处理 |
|---|---|---|
| `task_plan.md` 旧 P4 完成口径 | 写过“P4 完整仿真已完成” | 已在顶部暂停旧口径；后续需重写阶段状态 |
| 旧 `P4 完整仿真` 表述 | 把 dry-run/脚本跑通等同完整仿真 | 降级为旧标准结构跑通 |
| 节点裸分数 | 用户看不懂，且会误导为最终排名 | 改为推进优先级、理由、建议、缺口、复核动作 |
| ROI/收益预测/最终推荐 | 缺真实客流、转化、成本、授权 | 不得输出最终结论 |
| “外部预览”等旧文案 | 客户侧含义不清 | 前端映射成人话 |
| DeepSeek 直接综合判断 | 不稳定且无本地复核 | 必须套契约和 schema |

## 6. E 新方向缺失：必须新增的工程对象

| 工程对象 | 来自方法 | 为什么需要 |
|---|---|---|
| `persona_state.schema.json` | HumanLM | 把人群从标签升级为内部状态 |
| `behavior_program.schema.json` | ROTE | 把行为从文本建议升级为可审查程序 |
| `choice_probability.schema.json` | Huff / Logit / Gravity | 把“可能消费”变成有口径的选择模型 |
| `spatial_movement_gate.md` | Social Force / RVO / MATSim / GIS | 把空间移动、绕行、排队、拥挤纳入边界 |
| `macro_validation_plan.md` | Cities / SARIMA / SSIM / KL / DTW | 把仿真结果和真实统计做对齐 |
| `deepseek_task_contract.schema.json` | DeepSeek 契约 | 限制低能力模型越权 |
| `node_recommendation_explanation.schema.json` | SSR + 用户反馈 | 让节点建议可读、可复核、可行动 |

## 7. 阶段状态重估

| 阶段 | 旧口径 | 新口径 |
|---|---|---|
| P0 | 初始化完成 | 仍可信 |
| P1 | 样例资料拆解完成 | 仍可信，但只代表资料处理底座 |
| P2 | 方法原型收口 | 需要重开，按老板模型扩展状态/行为/选择/验证 schema |
| P3 | 真实公园校准未开始/未闭合 | 更关键；没有 P3，就没有完整 P4 |
| P4 | 曾写完整仿真完成 | 降级为旧标准 dry-run；新 P4 未完成 |
| P5 | 报告交付未开始 | 只能做工作稿，不可做最终商业报告 |
| P6 | 工作台可运行 | 产品壳可用，但模型链路未完整 |

## 8. 对当前工作的直接影响

1. 暂停继续扩写仿真主代码。
2. 先落 `DeepSeek 受限任务契约` 和 schema。
3. 再把旧文件逐个打标签，必要时在文件顶部加状态说明。
4. 所有报告和页面不再用“完整仿真”“最终分”“最终推荐”。
5. 节点界面和报告必须优先提供具体建议，而不是显示一个意义不详的分。

## 8.1 旧 DeepSeek 输出机械清单

已生成：

- `40_quality_evidence/deepseek_llm_runs_contract_inventory_20260604.json`
- `40_quality_evidence/deepseek_llm_runs_contract_inventory_20260604.csv`

机械结果：

- `60_model/llm_runs` 共 35 个旧输出文件。
- 16 个是旧 progress 状态文件。
- 17 个是旧 raw JSONL。
- 2 个是旧 latest JSON。
- 0 个符合新 `deepseek_task_contract` envelope。

结论：资料处理和 DeepSeek 搜索链路不是简单“断掉”，而是旧运行结果都还停留在旧格式。后续必须先写 adapter，把旧 raw/progress/latest 输出转成新 envelope 或明确标记为不可适配，再进入节点、画像、行为程序和报告解释。

## 9. 下一批具体文件状态

已新增：

- `60_model/schemas/deepseek_task_contract.schema.json`
- `60_model/schemas/persona_state.schema.json`
- `60_model/schemas/behavior_program.schema.json`
- `60_model/schemas/node_recommendation_explanation.schema.json`
- `60_model/scripts/validate_deepseek_contract_output.py`

待接入：

- 将旧 `60_model/llm_runs/` 输出转换为 envelope 后跑契约审计。
- 将 `70_outputs/processed_tables/p2_*_20260604.csv` 映射到 schema，并标记不合格/缺字段项。
- 将 P6 节点解释的 `score_recommendations` 与 `score_breakdown` 进一步映射到 `node_recommendation_explanation.schema.json`。

优先重写或加状态头：

- `task_plan.md`
- `60_model/simulation/persona_behavior.py`
- `70_outputs/processed_tables/p2_persona_state_profiles_20260604.csv`
- `70_outputs/processed_tables/p2_behavior_program_templates_20260604.csv`
- `70_outputs/processed_tables/p2_simulation_validation_targets_20260604.csv`
