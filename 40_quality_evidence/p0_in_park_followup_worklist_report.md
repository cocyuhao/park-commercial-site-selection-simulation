# P0 园内候选复核工作单报告

## 结论

- P0 工作项：7 条。
- 按公园统计：{'城市绿心森林公园': 1, '奥林匹克森林公园': 6}
- 复核优先级：{'P0_missing_business_fields': 4, 'P0_pdf_seed_boundary_match': 3}
- 来源强度：{'amap_boundary_only': 4, 'pdf_seed_plus_amap_boundary': 3}
- 缺失经营字段：{'contact': 4, 'cost_yuan': 5, 'opening_hours': 3}
- 高德中心点代理路径已返回：7/7。
- 高德路径 API 阻塞项：0/7。
- 高德 detail/API 或现场补字段项：7/7。

## 口径限制

- 本工作单只用于 P1 复核排队，不是最终园内供给清单。
- 高德路径如已返回，也只是公园中心点代理路线；真实入口/节点路线仍未闭合。
- 当前环境未确认 `AMAP_WEB_SERVICE_KEY` 时，detail 补字段仍需等待后续接口或现场核验。
- `approx_distance_to_osm_boundary_m` 是基于 OSM polygon 的近似几何距离，不是步行距离。
- 所有工作项 `can_enter_p2_supply` 均为 `no`，直到路径可达、实际营业和运营授权闭合。

## 输出文件

- `70_outputs/processed_tables/poi_supply_p0_followup_worklist.csv`
