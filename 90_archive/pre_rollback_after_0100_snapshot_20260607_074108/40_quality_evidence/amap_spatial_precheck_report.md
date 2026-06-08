# 高德候选 POI 空间预过滤报告

## 结论

- 输入候选：227 条。
- 空间预过滤状态：{'edge_or_adjacent_needs_boundary_confirmation': 25, 'near_core_needs_boundary_confirmation': 2, 'park_context_needs_boundary_confirmation': 31, 'pdf_seed_matched_needs_boundary_confirmation': 3, 'surrounding_competition_candidate': 166}
- 供给使用状态：{'do_not_use_as_in_park_supply_yet': 227}
- 补抓/复核计划：17 条，按问题类型 {'page_size_cap': 9, 'zero_result': 8}。

## 按公园统计

- 城市绿心森林公园：{'edge_or_adjacent_needs_boundary_confirmation': 3, 'park_context_needs_boundary_confirmation': 13}
- 奥林匹克森林公园：{'edge_or_adjacent_needs_boundary_confirmation': 22, 'near_core_needs_boundary_confirmation': 2, 'park_context_needs_boundary_confirmation': 18, 'pdf_seed_matched_needs_boundary_confirmation': 3, 'surrounding_competition_candidate': 166}

## 需补抓或复核查询

- 达到单页上限：os_coffee;os_tea;os_cold_drink;os_fast_food;os_restaurant;os_convenience;os_sports_supply;os_yoga;os_bar。
- 零结果查询：cg_tea;cg_restaurant;cg_cultural_creative;cg_souvenir;cg_yoga;cg_pilates;cg_bar;os_souvenir。

## 口径限制

- 本报告不是最终园内/园外判定；当前没有真实公园 polygon 或现场清单。
- `spatial_precheck_status` 只基于高德中心点距离、POI 名称/地址文本和 PDF 种子匹配做预过滤。
- 所有记录的 `supply_use_status` 均保持为 `do_not_use_as_in_park_supply_yet`，后续必须经过边界、入口节点或现场核验后才能进入缺口计算。
- 达到单页上限的查询需要高德 Key 支持分页补抓；零结果查询需要换关键词或人工复核，不能直接证明该业态不存在。

## 输出文件

- `70_outputs/processed_tables/poi_supply_candidates_amap_spatial_precheck.csv`
- `50_external_gis/amap_poi/amap_refetch_followup_plan.csv`
