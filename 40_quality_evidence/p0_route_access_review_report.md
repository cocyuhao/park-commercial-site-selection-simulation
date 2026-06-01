# P0 园内候选路径可达复核报告

## 结论

- P0 路径核验项：7 条。
- 高德 API 状态：{'1': 7}
- 路径可达状态：{'amap_center_proxy_route_returned_needs_entrance_validation': 7}
- 按公园统计：{'城市绿心森林公园': 1, '奥林匹克森林公园': 6}
- 步行距离范围：1219-2552 米。
- 步行时间范围：975-2042 秒。

## 口径限制

- origin 使用高德公园中心点代理，不是真实入口、停车场、地铁站或游线节点。
- 路径结果只用于 P1 可达性初筛；进入 P2 前仍需真实入口/节点路径或现场核验。
- 所有记录 `can_enter_p2_supply_after_route` 仍为 `no`，因为运营授权和入口口径尚未闭合。
- 日志和原始返回不包含高德 Key。

## 输出文件

- `50_external_gis/amap_routes/amap_p0_route_fetch_log.csv`
- `50_external_gis/amap_routes/amap_p0_route_results.csv`
- `70_outputs/processed_tables/poi_supply_p0_route_access_review.csv`
