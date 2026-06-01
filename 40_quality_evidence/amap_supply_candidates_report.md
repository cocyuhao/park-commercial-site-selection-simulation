# 高德供给候选表报告

## 结果

- 高德去重供给候选：227 条。
- 按公园统计：{'城市绿心森林公园': 16, '奥林匹克森林公园': 211}
- 按距离圈层统计：{'1001-1500m': 38, '1501-3000m': 180, '501-1000m': 9}
- PDF 种子匹配状态：{'matched_pdf_seed': 3, 'not_in_pdf_seed': 224}
- 按业态统计（去重 POI 可归入多个查询业态）：{'coffee': 26, 'cold_drink': 30, 'convenience_retail': 28, 'cultural_creative': 5, 'fast_food': 32, 'night_dining_bar': 25, 'restaurant': 25, 'sports_supply': 26, 'tea_drink': 25, 'yoga_pilates': 31}

## 口径

- 本表按 `park_id + amap_poi_id` 去重，减少同一 POI 被多个关键词重复命中的问题。
- `min_distance_m` 是高德返回的该 POI 到查询中心点最小距离，不是步行路径距离。
- `in_park_status` 仍为 `needs_boundary_filter`，需要公园边界或入口/节点坐标进一步过滤。
- `pdf_seed_match_status` 仅表示名称层面的粗匹配，不表示供给数量已经闭合。

## 输出文件

- `70_outputs/processed_tables/poi_supply_candidates_amap.csv`
