# DeepSeek 入口/节点语义初筛报告

## 结论

- 输入节点：45 条。
- 输出状态：{'draft': 45}
- 语义类型：{'internal_facility_node': 8, 'nearby_commercial_or_wrong_match': 6, 'park_area_centroid_or_generic': 3, 'parking_access_node': 24, 'transit_or_station_node': 4}
- 路径使用优先级：{'P1_valid_visit_node_candidate': 29, 'P2_context_or_internal_node': 10, 'P3_low_confidence_or_wrong_match': 6}
- DeepSeek 批次：6 个。

## 口径限制

- 本结果由 DeepSeek 生成，只能作为 `draft`。
- 不能作为官方入口清单或最终可达性结论。
- 后续必须由本地规则、现场或官方资料确认。

## 输出文件

- `50_external_gis/amap_routes/amap_p0_entrance_node_semantic_draft_deepseek.csv`
- `60_model/llm_runs/deepseek_entrance_node_semantic_raw.jsonl`
