# 高德 POI 抓取复查报告

## 结论

- 检查项：16 条。
- 状态统计：{'needs_review': 3, 'pass': 13}
- 阻塞问题：0 条。
- 需关注项：3 条。

## 关键发现

- [info] 接口日志 26 条；状态分布 {'1': 26}；info 分布 {'OK': 26}。
- [warning] 零结果周边查询 8 条：cg_tea;cg_restaurant;cg_cultural_creative;cg_souvenir;cg_yoga;cg_pilates;cg_bar;os_souvenir。
- [warning] 达到单页上限 25 条的查询 9 条，后续可能需要分页：os_coffee;os_tea;os_cold_drink;os_fast_food;os_restaurant;os_convenience;os_sports_supply;os_yoga;os_bar。
- [info] 清洗 POI 行 270 条；按公园 {'城市绿心森林公园': 17, '奥林匹克森林公园': 253}。
- [info] 按业态 {'coffee': 26, 'cold_drink': 30, 'convenience_retail': 28, 'cultural_creative': 5, 'fast_food': 32, 'night_dining_bar': 25, 'restaurant': 25, 'sports_supply': 26, 'tea_drink': 25, 'yoga_pilates': 48}。
- [info] 按公园去重后的 Amap POI ID 数：227。
- [warning] 同一公园同一业态内重复 POI ID 17 个。
- [info] rating 有值 267 条。
- [info] cost_yuan 有值 186 条。
- [info] opentime_today 有值 232 条。
- [info] opentime_week 有值 235 条。
- [info] tel 有值 212 条。

## 口径

- 本轮是 P1 小批量 POI 抓取，不等于最终完整供给清单。
- `distance_m` 为高德周边搜索返回距离，仍需结合公园边界和入口/节点做园内/周边过滤。
- 查询达到单页上限的业态后续需要分页或缩小半径复查。

## 输出文件

- `50_external_gis/amap_poi/amap_fetch_log.csv`
- `50_external_gis/amap_poi/amap_poi_clean.csv`
- `70_outputs/processed_tables/poi_supply_base_amap.csv`
- `40_quality_evidence/amap_poi_fetch_review.csv`
