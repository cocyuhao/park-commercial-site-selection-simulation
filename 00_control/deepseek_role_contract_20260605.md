# DeepSeek 职责边界合同（2026-06-05）

> 用途：防止本项目把 DeepSeek 的低成本语言能力误用成仿真主脑、最终裁判或逐游客实时引擎。

## 1. 当前确定结论

DeepSeek 在本项目只承担两个主要角色：

1. **行为程序编译器**：按“人群 × 场景 × 节点 × 时间段”把资料、画像、触发条件和节点上下文整理成结构化行为程序草稿。
2. **结果解释器**：把本地 Python / schema / 规则 / 空间与运营约束算出的结果，解释成业务人员能看懂的依据、缺口、待补资料和推进事项。

DeepSeek 不是：

- 逐个虚拟游客的实时决策引擎。
- 最终选址裁判。
- checked 证据来源。
- ROI、收益预测、最终排序或最终推荐生成器。
- 老板方法资料、外部论文、Codex 判断和本地仿真的替代品。

## 2. 为什么这么定

依据来自三类资料：

- 老板六份方法资料：HumanLM 强调状态对齐；ROTE 强调可执行行为程序；社区仿真资料强调微观行为和宏观统计校准；这些都要求先有状态、行为、验证目标和复核，不支持让 LLM 逐游客自由编故事。
- 本地控制文件：`00_control/model_orchestration.md` 与 `00_control/llm_routing.md` 均规定 DeepSeek 只能做低/中风险草稿，输出必须是 `draft` 或 `needs_review`。
- DeepSeek 官方文档：并发按账号计算，`deepseek-v4-pro` 500 并发、`deepseek-v4-flash` 2500 并发；超限返回 HTTP 429；更高并发应申请 capacity expansion，不应靠多 key 设计主架构。

## 3. 正确链路

1. 资料、证据、PPT 写法、老板模型和外部论文先进入对象池、schema、验证目标和缺口登记。
2. DeepSeek 批量生成 `needs_review` 行为程序、场景草稿、解释草稿或报告草稿。
3. 本地 Python 将行为程序编译成可复跑参数、概率、约束、路径、队列、供需缺口和敏感性分析。
4. 本地脚本、证据 ID、浏览器/自动化验证和人工复核决定是否能进入更高可信状态。
5. DeepSeek 只能在最后把已复核或待复核结果写成业务语言，不得提升结论等级。

## 4. 当前工程落点

已做：

- `60_model/src/llm_router.py` 增加缓存指纹、调用日志、429/timeout/connection 分类、重试、OpenTelemetry trace 入口、本地小并发闸门和逐游客调用拦截。
- `60_model/schemas/deepseek_task_contract.schema.json` 增加 `review_required=true` 强制字段。
- `60_model/scripts/verify_deepseek_orchestration.py` 离线验证 DeepSeek 受限调用层，不调用真实 API。
- `40_quality_evidence/deepseek_orchestration_validation_20260605.md/json` 记录验证结果。

仍未完成：

- 行为程序对象池还没有完整 CRUD。
- 人群状态对象池还没有完整进入前端工作流。
- 宏观验证指标还没有真实计算。
- DeepSeek 调用层只是受限入口，不等于完整仿真架构完成。
- 2026 全局架构基线仍需要继续检索和筛选更多近年论文、工程资料和 AI 产品设计资料。

## 5. 执行纪律

- PowerShell 命令不得再使用 `&&` 这类在当前 shell 不稳定的串联写法；重要命令分开执行，或使用 PowerShell 原生命令结构。
- 插件和 skill 只能作为增强能力，不作为单点依赖；凡是会影响项目判断的插件、skill 或网页资料，都必须有本地文件、截图、JSON、trace 或门禁证据。
- 不能把“学习过”“记录过”“落地过”混成一件事。以后必须区分：
  - learned：读过并形成摘要。
  - selected：判断适合本项目。
  - landed：进入 schema / UI / adapter / script / gate。
  - verified：有可复跑验证或浏览器证据。

