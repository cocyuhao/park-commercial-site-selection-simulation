# DeepSeek 受限调用层验证（2026-06-05）

- 状态：pass
- 检查项：8
- 失败项：0

## 结论

- DeepSeek 现在被约束为低成本语义工人，不是逐游客仿真引擎。
- 批处理任务默认可缓存；运行时聊天默认不缓存，避免跨上下文误复用。
- 调用层已经具备 429/timeout/connection 分类、重试参数、调用日志和 OpenTelemetry trace 入口。
- 本地运行时增加小并发闸门，避免网页或脚本把多个 DeepSeek 请求无控制地同时打出去。
- 契约要求 `needs_human_review=true` 和 `review_required=true`，防止流畅文本被误当事实。

## 检查明细

- `pass` stable_fingerprint：fp1=3b4f69202d90 fp3=37399ab46d22
- `pass` batch_cache_default：LLM-001 should default to local cache because it is low-risk batch work.
- `pass` runtime_chat_cache_disabled：LLM-026 runtime chat should not silently reuse answers across contexts.
- `pass` final_decision_not_deepseek：LLM-006 executor=codex risk=high
- `pass` per_visitor_call_blocked：DeepSeek cannot be used as a real-time model call inside each virtual visitor loop.
- `pass` router_has_retry_cache_trace_terms：missing=[]
- `pass` telemetry_import_ok：telemetry module import ok
- `pass` contract_forces_review_required：required=['assumptions', 'items', 'needs_human_review', 'output_status', 'review_required', 'source_refs', 'task_id', 'task_type', 'uncertainties']
