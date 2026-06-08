# 园内候选 POI 复核清单报告

## 结论

- OSM polygon 内候选：26 条。
- 按公园统计：{'城市绿心森林公园': 15, '奥林匹克森林公园': 11}
- 复核优先级：{'P0_missing_business_fields': 4, 'P0_pdf_seed_boundary_match': 3, 'P1_key_category': 6, 'P2_normal_field_review': 13}
- 来源强度：{'amap_boundary_only': 23, 'pdf_seed_plus_amap_boundary': 3}
- 高德经营字段状态：{'amap_business_fields_partial': 4, 'amap_business_fields_sufficient_for_p1_review': 22}
- 字段覆盖：rating 26/26，opentime 23/26，tel 22/26，cost_yuan 15/26。

## 按业态统计

- 总体：{'coffee': 2, 'cold_drink': 6, 'convenience_retail': 4, 'fast_food': 9, 'restaurant': 1, 'sports_supply': 6}
- 城市绿心森林公园：{'coffee': 1, 'cold_drink': 5, 'convenience_retail': 2, 'fast_food': 7, 'sports_supply': 1}
- 奥林匹克森林公园：{'coffee': 1, 'cold_drink': 1, 'convenience_retail': 2, 'fast_food': 2, 'restaurant': 1, 'sports_supply': 5}

## 口径限制

- 本清单只包含 OSM polygon 内候选，不是最终可经营点位清单。
- `candidate_use_status` 全部保持为 `p1_in_park_candidate_not_final_supply`。
- 仍需核验：实际营业状态、入口/节点步行可达、是否属于园方可运营/可授权资产、现场限制条件。
- 高德营业时间、电话、评分和人均消费是公开 POI 字段，可作为 P1 复核线索，不能替代现场或经营方确认。

## 输出文件

- `70_outputs/processed_tables/poi_supply_in_park_candidate_review.csv`
