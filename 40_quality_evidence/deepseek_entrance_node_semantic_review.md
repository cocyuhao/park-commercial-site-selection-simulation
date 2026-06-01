# DeepSeek 入口/节点语义初筛本地复核报告

## 结论

- 复核项状态：{'pass': 10}
- 本地规则优先级：{'P0_manual_check_gate_or_entrance': 20, 'P1_manual_check_parking_access': 7, 'P2_context_node_or_possible_wrong_match': 9, 'P3_unclear_manual_check': 9}
- 最终使用门禁：{'candidate_access_node_needs_official_or_field_confirmation': 20, 'do_not_use_as_access_node_until_manual_review': 18, 'secondary_access_node_needs_field_confirmation': 7}

## P0 人工核验样例

- NODE-CAND-0010 城市绿心森林公园 城市绿心森林公园P6停车场(出入口) -> P0_manual_check_gate_or_entrance
- NODE-CAND-0013 奥林匹克森林公园 奥林匹克森林公园-南门站 -> P0_manual_check_gate_or_entrance
- NODE-CAND-0015 奥林匹克森林公园 奥林匹克森林公园-西门站 -> P0_manual_check_gate_or_entrance
- NODE-CAND-0038 奥林匹克森林公园 奥林匹克森林公园北园-体育园地面停车场(出入口) -> P0_manual_check_gate_or_entrance
- NODE-CAND-0034 奥林匹克森林公园 奥林匹克森林公园北园-南门站游乐车电瓶车售票处 -> P0_manual_check_gate_or_entrance
- NODE-CAND-0030 奥林匹克森林公园 奥林匹克森林公园北园东门1号停车场 -> P0_manual_check_gate_or_entrance
- NODE-CAND-0029 奥林匹克森林公园 奥林匹克森林公园北园东门1号停车场(入口) -> P0_manual_check_gate_or_entrance
- NODE-CAND-0031 奥林匹克森林公园 奥林匹克森林公园北园东门1号停车场(出口) -> P0_manual_check_gate_or_entrance
- NODE-CAND-0035 奥林匹克森林公园 奥林匹克森林公园北园北门地面停车场 -> P0_manual_check_gate_or_entrance
- NODE-CAND-0025 奥林匹克森林公园 奥林匹克森林公园北园北门地面停车场(出入口) -> P0_manual_check_gate_or_entrance
- NODE-CAND-0026 奥林匹克森林公园 奥林匹克森林公园北园南门停车场(入口) -> P0_manual_check_gate_or_entrance
- NODE-CAND-0027 奥林匹克森林公园 奥林匹克森林公园北园西门停车场 -> P0_manual_check_gate_or_entrance
- NODE-CAND-0028 奥林匹克森林公园 奥林匹克森林公园北园西门停车场(入口) -> P0_manual_check_gate_or_entrance
- NODE-CAND-0021 奥林匹克森林公园 奥林匹克森林公园南园-东门站 -> P0_manual_check_gate_or_entrance
- NODE-CAND-0023 奥林匹克森林公园 奥林匹克森林公园南园东门停车场 -> P0_manual_check_gate_or_entrance
- NODE-CAND-0022 奥林匹克森林公园 奥林匹克森林公园南园东门停车场(出入口) -> P0_manual_check_gate_or_entrance
- NODE-CAND-0014 奥林匹克森林公园 奥林匹克森林公园南园南门观光车售票厅 -> P0_manual_check_gate_or_entrance
- NODE-CAND-0018 奥林匹克森林公园 奥林匹克森林公园南园西门停车场 -> P0_manual_check_gate_or_entrance
- NODE-CAND-0017 奥林匹克森林公园 奥林匹克森林公园南园西门停车场(出入口) -> P0_manual_check_gate_or_entrance
- NODE-CAND-0016 奥林匹克森林公园 奥林匹克森林公园南门东侧地面停车场 -> P0_manual_check_gate_or_entrance

## 口径限制

- DeepSeek 结果仍为 `draft`。
- 本地规则只做字符串/类型初筛，不等于官方入口确认。
- 所有节点进入路径或供给判断前仍需现场或官方资料确认。

## 输出文件

- `50_external_gis/amap_routes/amap_p0_entrance_node_semantic_review_queue.csv`
- `40_quality_evidence/deepseek_entrance_node_semantic_review.csv`
