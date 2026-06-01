# 高德候选 POI 边界过滤报告

## 结论

- 输入候选：227 条。
- OSM polygon 边界状态：{'inside_osm_polygon': 26, 'outside_osm_polygon': 201}
- P1 供给使用状态：{'boundary_filtered_in_park_candidate_needs_field_review': 26, 'boundary_filtered_surrounding_supply_candidate': 201}

## 按公园统计

- 城市绿心森林公园：{'inside_osm_polygon': 15, 'outside_osm_polygon': 1}
- 奥林匹克森林公园：{'inside_osm_polygon': 11, 'outside_osm_polygon': 200}

## OSM polygon 内候选按业态统计

- 城市绿心森林公园：{'coffee': 1, 'cold_drink': 5, 'convenience_retail': 2, 'fast_food': 7, 'sports_supply': 1}
- 奥林匹克森林公园：{'coffee': 1, 'cold_drink': 1, 'convenience_retail': 2, 'fast_food': 2, 'restaurant': 1, 'sports_supply': 5}

## 口径限制

- 高德 POI 坐标默认为 GCJ-02，本脚本近似转换为 WGS84 后与 OSM polygon 做点在面内判断。
- OSM 边界来自公开地图，不是官方规划红线；P1 可用于候选过滤和复核优先级，不作为最终经营结论。
- `inside_osm_polygon` 只表示公开地图 polygon 内候选，仍需现场营业状态、入口/路径可达和运营授权核验。
- `outside_osm_polygon` 可作为周边竞品/外溢供给候选，不应直接计入园内供给。

## 输出文件

- `70_outputs/processed_tables/poi_supply_candidates_amap_boundary_filter.csv`
