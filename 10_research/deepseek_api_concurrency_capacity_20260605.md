# DeepSeek API 并发与仿真接入判断（2026-06-05）

> 状态：外部官方资料核验 + 本项目架构判断。  
> 用途：回答“一个 DeepSeek API 是否够大规模仿真使用”，并约束后续实现不要把 LLM 当逐游客仿真引擎。

## 1. 官方资料核验

来源：

- DeepSeek 官方 Rate Limit & Isolation：`https://api-docs.deepseek.com/quick_start/rate_limit/`
- DeepSeek 官方 Models & Pricing：`https://api-docs.deepseek.com/quick_start/pricing/`

官方当前口径：

- 并发按账号计算，不按 API Key 计算。
- `deepseek-v4-pro` 账号并发限制为 500。
- `deepseek-v4-flash` 账号并发限制为 2500。
- 一个请求从发出到模型响应结束，占用一个并发连接。
- 超过并发限制会返回 HTTP 429。
- 需要更高并发时，应提交 capacity expansion request，由 DeepSeek 根据业务需求匹配并发。
- `user_id` 可做业务侧用户隔离，但常规账号下所有 `user_id` 仍合并计算账号并发。

## 2. 对本项目的判断

一条 API Key 本身不是关键瓶颈，账号级并发和调用设计才是关键。

当前阶段：

- 够用。我们只应让 DeepSeek 做资料摘要、候选人群状态、行为程序草稿、结果解释和报告草稿。
- 不应每个虚拟游客都调用一次 DeepSeek。

大规模仿真阶段：

- 不能靠 DeepSeek 实时驱动每个 agent。
- 主仿真必须由本地 Python / schema / 规则 / 空间与运营约束执行。
- DeepSeek 只在批处理层生成可缓存、可复核的候选程序或解释。

## 3. 推荐架构

1. 批量生成：按“人群 × 场景 × 节点 × 时间段”生成行为程序候选，而不是逐游客生成。
2. 缓存复用：同一批行为程序、状态解释和报告摘要可缓存，除非输入资料变化。
3. 本地执行：路径、队列、概率、供需缺口、运营约束和 Monte Carlo 在本地运行。
4. 限流队列：DeepSeek 调用统一进入队列，记录任务类型、模型、输入摘要、输出状态、错误和重试。
5. 429 策略：遇到 429 退避重试；持续出现 429 再申请账号 capacity expansion。
6. 模型分层：低风险批量草稿可用 `deepseek-v4-flash`；复杂解释和重要摘要再用 `deepseek-v4-pro`。

## 4. 用户是否需要现在申请更多 API

暂时不建议通过“多申请 API Key”解决并发，因为官方并发按账号计算。

更合理的准备是：

- 确认当前 DeepSeek 账号余额。
- 了解 capacity expansion request 入口。
- 等本地系统有真实批处理吞吐测试后，再决定是否申请扩容。
- 若未来要生产化，准备备用模型或备用供应商，但不能让备用供应商改变“本地主仿真 + LLM 受限语义工人”的架构。

## 5. 工程落点

需要落地：

- DeepSeek 调用队列和缓存。
- API 429 / timeout / empty content 的结构化错误记录。
- `user_id` 不包含隐私信息，只使用项目/会话级匿名 ID。
- OpenTelemetry span 记录模型、任务、对象数量、输出状态和错误类型，不记录完整 prompt 和 Key。
- 门禁禁止逐游客实时调用 DeepSeek。

本文件不代表 DeepSeek 已完成接入优化；它只是并发和架构边界。
