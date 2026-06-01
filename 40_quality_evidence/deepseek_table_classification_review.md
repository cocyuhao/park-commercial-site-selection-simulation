# DeepSeek 表格分类本地复核报告

## 结论

- 复核项状态：{'pass': 8}
- 复核队列优先级：{'P0_second_evidence_candidate': 63, 'P1_context_or_followup_candidate': 227, 'P2_low_priority_review': 4, 'P3_skip_or_low_value': 35}
- 证据候选状态：{'candidate_for_second_evidence_review': 63, 'context_candidate_needs_sampling': 227, 'not_evidence_noise_or_empty': 35, 'unclear_needs_sampling': 4}
- 主题分布：{'commercial_supply': 9, 'consumption_spending': 12, 'demographic_profile': 42, 'empty_or_visual_noise': 35, 'origin_residence_work': 24, 'other': 4, 'poi_hot_visit': 38, 'tgi_preference': 161, 'time_peak': 1, 'visitor_flow': 3}

## P0 复核样例

- TBL-00005 p9 poi_hot_visit
- TBL-00006 p10 poi_hot_visit
- TBL-00007 p11 commercial_supply
- TBL-00008 p12 commercial_supply
- TBL-00009 p13 commercial_supply
- TBL-00010 p14 poi_hot_visit
- TBL-00011 p15 poi_hot_visit
- TBL-00012 p16 poi_hot_visit
- TBL-00013 p17 poi_hot_visit
- TBL-00014 p18 poi_hot_visit
- TBL-00015 p19 poi_hot_visit
- TBL-00016 p20 poi_hot_visit
- TBL-00017 p21 poi_hot_visit
- TBL-00018 p22 poi_hot_visit
- TBL-00019 p23 poi_hot_visit
- TBL-00020 p24 poi_hot_visit
- TBL-00021 p25 poi_hot_visit
- TBL-00022 p26 poi_hot_visit
- TBL-00023 p27 poi_hot_visit
- TBL-00024 p28 poi_hot_visit

## 口径限制

- DeepSeek 分类只能作为 `draft`；本地复核只检查结构完整性和复核优先级。
- `P0_second_evidence_candidate` 代表优先复核，不代表已经入账或真实。
- 第二批入账仍需回到 `pdf_native_tables.jsonl` 和 PDF 原文确认字段、单位、页码、口径。

## 输出文件

- `30_extraction/tables/pdf_table_review_queue.csv`
- `40_quality_evidence/deepseek_table_classification_review.csv`
