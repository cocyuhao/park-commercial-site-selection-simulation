# POI 供给底表 P1 初版报告

## 结果

- PDF 区域内热门到访 POI 种子行：34 条。
- 去重后的初版供给底表：20 条。
- 按公园统计：{'城市绿心公园': 4, '奥林匹克森林公园': 16}
- 按标准业态统计：{'coffee': 3, 'convenience_retail': 1, 'family_recreation': 1, 'family_restaurant': 1, 'food_dining': 6, 'retail': 3, 'sports_service': 1, 'sports_supply': 3, 'yoga_pilates': 1}

## 口径

- 当前表只使用 PDF 中明确为“区域内范围内”的热门到访地点表。
- 城市绿心仅纳入第 9 页区域内美食类热门到访表；后续需用高德补咖啡、零售、文创、运动等完整供给。
- 奥森纳入工作人口和流动人口两组区域内商业相关表，并按 POI 名称去重。
- 该表是供给核验种子，不是最终园内供给结论；是否在园内、是否营业、距离入口/节点多远，均需高德或现场清单闭合。

## 输出文件

- `50_external_gis/poi_supply/pdf_hot_visit_poi_seed_raw.csv`
- `70_outputs/processed_tables/poi_supply_base.csv`
