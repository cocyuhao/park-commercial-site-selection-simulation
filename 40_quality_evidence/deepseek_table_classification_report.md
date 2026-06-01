# DeepSeek PDF 表格主题分类草稿报告

## 结论

- 输入表格：329 张。
- 已分类表格：329 张。
- DeepSeek 已完成批次：44 个。
- 输出状态：{'draft': 329}
- 主题分布：{'commercial_supply': 9, 'consumption_spending': 12, 'demographic_profile': 42, 'empty_or_visual_noise': 35, 'origin_residence_work': 24, 'other': 4, 'poi_hot_visit': 38, 'tgi_preference': 161, 'time_peak': 1, 'visitor_flow': 3}
- 置信度分布：{'high': 307, 'medium': 22}

## 口径限制

- 本结果由 DeepSeek 生成，只能作为 `draft`。
- 分类只基于 `pdf_native_tables_summary.csv` 的 sample、页码、行列数等摘要，不读取完整表格语义。
- 不得直接写入 `evidence_ledger.csv`，后续必须用 PDF 表格原文、本地规则和抽样复核确认。
- 本报告不包含 DeepSeek Key。

## 输出文件

- `30_extraction/tables/pdf_table_topic_draft_deepseek.csv`
- `60_model/llm_runs/deepseek_table_classification_raw.jsonl`
