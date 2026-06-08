# DeepSeek 旧输出 envelope 适配报告（2026-06-04）

本报告由 `60_model/scripts/adapt_deepseek_legacy_outputs.py` 生成。

## 口径

生成的 envelope 只包装旧文件元数据，状态统一为 `needs_review`，用途是把旧 DeepSeek 输出纳入新契约审计。它不证明旧内容语义正确，不证明旧 P2/P3/P4 草稿可用，也不允许升级为 checked 证据、最终排名、ROI 或完整仿真。

## 汇总

- 旧文件数：35
- latest_json: 2
- progress_json: 16
- raw_jsonl: 17

## 下一步

- 对 `source_summary` envelope 做契约验证。
- 需要使用旧内容时，再写任务专用 adapter：persona_state、behavior_program、node_explanation 或 report_draft。
- 专用 adapter 通过前，旧输出只能作为历史和复核线索。
