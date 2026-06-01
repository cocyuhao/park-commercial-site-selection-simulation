# OSM 公园边界抓取报告

## 结论

- 已保存边界 feature：2 个。
- 输出 GeoJSON：`50_external_gis/boundaries/osm_park_boundaries.geojson`。
- 抓取日志：`50_external_gis/boundaries/osm_park_boundary_fetch_log.csv`。

## 边界来源

- 来源：OpenStreetMap via Nominatim。
- 坐标系：WGS84 lon/lat。
- 许可提示：OpenStreetMap 数据使用 ODbL；后续报告或交付若复用边界，需要保留 OSM attribution。
- 口径限制：OSM 边界不是官方规划红线，P1 阶段只作为公开地图边界核验材料。

## 明细

- 城市绿心森林公园：results=1，selected=way/779532223，geojson=Polygon。
- 奥林匹克森林公园：results=1，selected=way/33616744，geojson=Polygon。
