# DeepSeek PDF 表格证据候选草稿报告

## 结论

- 输入 P0 表格：63 张。
- 已覆盖表格：63 张。
- 证据候选草稿：592 条。
- DeepSeek 批次：63 个。
- 输出状态：{'needs_review': 592}
- 候选类型：{'commercial_supply': 86, 'consumption_spending': 149, 'poi_hot_visit': 325, 'time_peak': 10, 'visitor_flow': 22}
- 置信度：{'high': 561, 'medium': 31}

## 口径限制

- 本结果由 DeepSeek 生成，只能作为 `needs_review`。
- 不能直接写入 `40_quality_evidence/evidence_ledger.csv`。
- 后续入账必须回查 `pdf_native_tables.jsonl`、PDF 页码、单位、字段含义和重复项。
- 若候选为热门 POI/到访指数，仍不等于完整供给清单。

## 输出文件

- `30_extraction/tables/pdf_table_evidence_candidates_deepseek.csv`
- `60_model/llm_runs/deepseek_evidence_candidates_raw.jsonl`
- `60_model/llm_runs/deepseek_evidence_candidates_progress.json`
