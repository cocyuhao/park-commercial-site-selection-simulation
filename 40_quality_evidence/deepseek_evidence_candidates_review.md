# DeepSeek 证据候选本地复核报告

## 结论

- 复核项状态：{'pass': 12}
- 候选复核优先级：{'P0_flow_or_peak_numeric_check': 32, 'P0_spending_numeric_check': 123, 'P1_poi_hot_visit_row_check': 325, 'P1_supply_context_check': 86, 'P2_low_priority_or_no_candidate': 26}
- 候选类型：{'commercial_supply': 86, 'consumption_spending': 149, 'poi_hot_visit': 325, 'time_peak': 10, 'visitor_flow': 22}

## P0 回查样例

- EV-CAND-0363 TBL-00058 p62 time_peak 人群覆盖度 城市绿心公园=53.59%%
- EV-CAND-0364 TBL-00058 p62 time_peak 人群覆盖度 城市绿心公园=51.69%%
- EV-CAND-0365 TBL-00058 p62 time_peak 人群覆盖度 城市绿心公园=49.53%%
- EV-CAND-0366 TBL-00058 p62 time_peak 人群覆盖度 城市绿心公园=49.42%%
- EV-CAND-0367 TBL-00058 p62 time_peak 人群覆盖度 城市绿心公园=40.17%%
- EV-CAND-0368 TBL-00058 p62 time_peak 人群覆盖度 城市绿心公园=39.29%%
- EV-CAND-0369 TBL-00058 p62 time_peak 人群覆盖度 城市绿心公园=36.14%%
- EV-CAND-0370 TBL-00058 p62 time_peak 人群覆盖度 城市绿心公园=36.00%%
- EV-CAND-0371 TBL-00058 p62 time_peak 人群覆盖度 城市绿心公园=28.82%%
- EV-CAND-0372 TBL-00058 p62 time_peak 人群覆盖度 城市绿心公园=15.59%%
- EV-CAND-0469 TBL-00194 p116 visitor_flow 人群覆盖度 北苑路北-北京市=3.40%%
- EV-CAND-0470 TBL-00194 p116 visitor_flow 人群覆盖度 回龙观-北京市=8.02%%
- EV-CAND-0471 TBL-00194 p116 visitor_flow 人群覆盖度 大屯-北京市=2.37%%
- EV-CAND-0472 TBL-00194 p116 visitor_flow 人群覆盖度 天通苑-北京市=4.85%%
- EV-CAND-0473 TBL-00194 p116 visitor_flow 人群覆盖度 奥林匹克公园-北京市=7.69%%
- EV-CAND-0474 TBL-00194 p116 visitor_flow 人群覆盖度 学清路-北京市=2.84%%
- EV-CAND-0475 TBL-00194 p116 visitor_flow 人群覆盖度 永丰-北京市=2.50%%
- EV-CAND-0476 TBL-00194 p116 visitor_flow 人群覆盖度 永泰庄-北京市=3.02%%
- EV-CAND-0477 TBL-00194 p116 visitor_flow 人群覆盖度 立水桥南-北京市=3.12%%
- EV-CAND-0478 TBL-00194 p116 visitor_flow 人群覆盖度 西三旗-北京市=3.44%%

## 口径限制

- DeepSeek 证据候选仍为 `needs_review`，不是已核验证据。
- `pdf_evidence_candidate_review_queue.csv` 只是回查排序，不代表可直接入账。
- 进入 `evidence_ledger.csv` 前必须确认 PDF 原表、页码、单位、主体和重复项。

## 输出文件

- `30_extraction/tables/pdf_evidence_candidate_review_queue.csv`
- `40_quality_evidence/deepseek_evidence_candidates_review.csv`
