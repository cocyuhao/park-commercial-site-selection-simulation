# P0 入口/节点代理路径复核报告

## 结论

- 入口/节点候选：45 条，按公园统计：{'城市绿心森林公园': 11, '奥林匹克森林公园': 34}。
- 路径请求结果：28 条，状态：{'entrance_or_node_proxy_route_returned_needs_field_validation': 28}。
- P0 工作项最佳入口/节点路径：7 条，状态：{'entrance_or_node_proxy_route_returned_needs_field_validation': 7}。
- 最短入口/节点代理步行距离范围：3-344 米。
- 最短入口/节点代理步行时间范围：2-275 秒。

## 口径限制

- 入口/节点来自高德文本搜索，不是官方入口清单。
- 本结果优于“公园中心点代理路径”，但仍只是 P1 代理核验。
- `can_enter_p2_supply_after_entrance_route` 全部保持 `no`，因为运营授权和现场确认尚未闭合。
- 输出和日志不保存高德 Key。

## 输出文件

- `50_external_gis/amap_routes/p0_entrance_node_query_plan.csv`
- `50_external_gis/amap_routes/amap_p0_entrance_node_candidates.csv`
- `50_external_gis/amap_routes/amap_p0_entrance_node_route_results.csv`
- `70_outputs/processed_tables/poi_supply_p0_entrance_route_review.csv`
