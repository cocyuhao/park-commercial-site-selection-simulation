# 外部 GIS 和地图数据

本目录用于保存高德 API、公开地图、边界、路径和竞品数据。

子目录：

- `amap_poi/`：高德 POI 原始返回和清洗结果。
- `amap_routes/`：步行路线、距离、时间。
- `boundaries/`：公园边界、候选多边形。
- `competitors/`：园外竞品和商圈。
- `poi_supply/`：从 PDF 或现场清单整理出的供给核验种子。

规则：

- 运行前必须从环境变量读取 `AMAP_WEB_SERVICE_KEY`。
- 每次 API 调用必须记录时间、接口、参数摘要、状态和结果条数。
- 不保存完整 Key。
- 坐标系、距离单位、时间单位必须写清楚。

当前 P1 已准备：

- `poi_supply/pdf_hot_visit_poi_seed_raw.csv`
- `amap_poi/amap_poi_query_plan.csv`
- `scripts/fetch_amap_poi.py`
- `amap_poi/amap_fetch_log.csv`
- `amap_poi/amap_poi_clean.csv`
- `amap_poi/amap_refetch_followup_plan.csv`
- `boundaries/osm_park_boundaries.geojson`
- `boundaries/osm_park_boundary_fetch_log.csv`
- `scripts/build_amap_supply_candidates.py`
- `scripts/build_amap_spatial_precheck.py`
- `scripts/fetch_osm_park_boundaries.py`
- `scripts/build_amap_boundary_filter.py`
- `scripts/build_in_park_candidate_review.py`
- `scripts/build_p0_in_park_followup_worklist.py`
- `scripts/fetch_amap_p0_routes.py`
- `../70_outputs/processed_tables/poi_supply_candidates_amap.csv`
- `../70_outputs/processed_tables/poi_supply_candidates_amap_spatial_precheck.csv`
- `../70_outputs/processed_tables/poi_supply_candidates_amap_boundary_filter.csv`
- `../70_outputs/processed_tables/poi_supply_in_park_candidate_review.csv`
- `../70_outputs/processed_tables/poi_supply_p0_followup_worklist.csv`
- `../70_outputs/processed_tables/poi_supply_p0_route_access_review.csv`
- `amap_routes/amap_p0_route_fetch_log.csv`
- `amap_routes/amap_p0_route_results.csv`

当前口径：

- 高德候选表是 P1 候选底表，不是最终园内供给结论。
- 空间预过滤只基于中心点距离、POI 名称/地址文本和 PDF 种子匹配；所有记录仍需真实边界、入口节点或现场清单核验。
- OSM 边界来自公开地图，坐标系为 WGS84；高德 POI 坐标近似从 GCJ-02 转 WGS84 后再做 polygon 过滤。
- OSM 边界不是官方规划红线，`inside_osm_polygon` 仍需现场营业、路径可达和运营授权核验。
- 园内候选复核清单只用于 P1 核验排队，`candidate_use_status` 仍为非最终供给。
- P0 路径核验使用高德公园中心点作为代理 origin，不是真实入口或游线节点；只能作为 P1 初筛。
- 复用 OSM 边界到报告或交付时需要保留 OpenStreetMap attribution。
- 未配置 `AMAP_WEB_SERVICE_KEY` 时只能 dry-run 或处理本地已抓取文件，不能分页补抓。
