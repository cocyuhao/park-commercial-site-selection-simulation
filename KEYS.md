# 项目 API Keys（无安全限制，明文存放）

| 服务 | Key |
|------|-----|
| 高德地图 Web Service API | `[REDACTED_AMAP_WEB_SERVICE_KEY]` |
| DeepSeek API | 见 `.env` |

## 高德 API 常用端点

- POI 搜索：`https://restapi.amap.com/v3/place/text?keywords=...&key=[REDACTED_AMAP_WEB_SERVICE_KEY]`
- POI 详情：`https://restapi.amap.com/v3/place/detail?id=<uid>&key=[REDACTED_AMAP_WEB_SERVICE_KEY]`
- 路径规划：`https://restapi.amap.com/v3/direction/walking?origin=...&destination=...&key=[REDACTED_AMAP_WEB_SERVICE_KEY]`

