# 数据质量报告

## 当前状态

已完成 P0 初始化、P1 前置抽取和第一批证据入账。当前质量报告记录资料可抽取性、证据强弱和第一批台账状态。

## 检查维度

| 维度 | 检查内容 | 状态 |
|---|---|---|
| 完整性 | 文件是否可读取、页数/幻灯片数是否正常、文本是否为空 | 初步通过 |
| 一致性 | PPT 结论是否能回查 PDF 或其他强证据 | 待检查 |
| 单位 | 人次、金额、比例、TGI、时间口径是否明确 | 待检查 |
| 异常值 | 全 0、异常峰值、疑似截断、重复页 | 待检查 |
| 可追溯性 | 关键数字是否进入 evidence ledger | 第一批通过 |
| 外部补数 | POI、路径、边界、竞品是否记录 API 参数和抓取时间 | 高德候选和空间预过滤已生成，边界/现场核验待完成 |

## 多方法核验

已运行 `30_extraction/scripts/run_verification_suite.py`，结果：

- 24 项完整性/一致性检查：23 项通过，1 项警告。
- 唯一警告：`evidence_ledger.csv` 目前没有正式指标行。
- 373 个页面/幻灯片完成数值密度扫描。
- 334 个疑似表格/结构化数据候选被记录。

已运行 `30_extraction/scripts/extract_pdf_native_tables.py`，结果：

- PDF 原生表格抽取成功，共 329 张表。
- 城市绿心 PDF：88 张表。
- 奥森 PDF：241 张表。
- 全部表格抽取状态为 `ok`。

## 抽取结果

| 资料 | 结果 |
|---|---|
| 城市绿心 PDF | 93 页，全部有文本，总文本长度 31881 |
| 奥森 PDF | 250 页，全部有文本，总文本长度 79960 |
| 城市绿心 PPT | 15 页，含 28 个图片对象 |
| 奥森 PPT | 15 页，含 17 个图片对象 |

## 第一批证据入账

已运行 `30_extraction/scripts/build_first_evidence_ledger.py`，结果：

- `40_quality_evidence/evidence_ledger.csv` 已写入 52 条指标。
- 37 条来自 PDF 报告或 PDF 原生表格，标记为 `source_report_pdf/checked`。
- 15 条来自 PPT 方案页，其中 13 条标记为 `presentation_assumption/needs_review`，2 条标记为 `presentation_assumption/conflict`。
- 已生成 `40_quality_evidence/first_evidence_ledger_report.md`。
- 已生成 `40_quality_evidence/ppt_assumption_review.csv` 和 `ppt_assumption_review.md`，完成 15 条 PPT 假设初步核验。

## POI 供给底表初版

已运行 `30_extraction/scripts/build_poi_supply_base.py`，结果：

- `50_external_gis/poi_supply/pdf_hot_visit_poi_seed_raw.csv` 已写入 34 条 PDF 区域内热门到访 POI 种子行。
- `70_outputs/processed_tables/poi_supply_base.csv` 已写入 20 条去重后的 P1 初版供给底表记录。
- 初版供给底表全部标记为 `needs_amap_or_field_verification`，不能直接作为最终园内供给数量。
- 已生成 `40_quality_evidence/poi_supply_base_report.md`。

已准备高德 POI 查询：

- `50_external_gis/amap_poi/amap_poi_query_plan.csv` 已写入 24 条查询计划，覆盖 2 个样例公园和 10 类业态。
- `50_external_gis/scripts/fetch_amap_poi.py` 已通过编译检查和 dry-run。
- 本地已有 `50_external_gis/amap_poi/amap_fetch_log.csv`，26 条接口日志全部 OK。
- 本地已有 `50_external_gis/amap_poi/amap_poi_clean.csv`，270 条清洗 POI。
- 本地已有 `70_outputs/processed_tables/poi_supply_candidates_amap.csv`，227 条按 `park_id + amap_poi_id` 去重的高德供给候选。
- 当前 `AMAP_WEB_SERVICE_KEY` 未配置时只能 dry-run 或处理本地已抓取文件，不能刷新或分页补抓。
- 已修正 PDF POI 名称清洗规则，保留英文品牌词间空格；`grid coffee(奥林匹克森林公园店)` 已恢复正确名称。
- 已运行 `30_extraction/scripts/review_poi_supply_base.py`，输出 `40_quality_evidence/poi_supply_review.csv/md`；13 项检查全部通过，阻塞问题 0 条，警告问题 0 条。
- 已运行 `50_external_gis/scripts/build_amap_spatial_precheck.py`，输出 `70_outputs/processed_tables/poi_supply_candidates_amap_spatial_precheck.csv`、`50_external_gis/amap_poi/amap_refetch_followup_plan.csv` 和 `40_quality_evidence/amap_spatial_precheck_report.md`。
- 空间预过滤 227 条记录全部保留为 `do_not_use_as_in_park_supply_yet`；当前不能作为最终园内供给数量。
- 高德补抓/复核计划 17 条：9 条达到单页上限，8 条零结果。
- 已运行 `50_external_gis/scripts/fetch_osm_park_boundaries.py`，输出 `50_external_gis/boundaries/osm_park_boundaries.geojson`、`osm_park_boundary_fetch_log.csv` 和 `40_quality_evidence/osm_boundary_report.md`。
- 已运行 `50_external_gis/scripts/build_amap_boundary_filter.py`，输出 `70_outputs/processed_tables/poi_supply_candidates_amap_boundary_filter.csv` 和 `40_quality_evidence/amap_boundary_filter_report.md`。
- OSM polygon 边界过滤结果：227 条候选中 26 条在 polygon 内，201 条在 polygon 外；其中城市绿心 15 条在内，奥森 11 条在内。
- OSM 边界来自公开地图，不是官方规划红线；高德 GCJ-02 坐标已近似转换为 WGS84 后过滤，仍存在坐标转换和边界口径误差。
- 已运行 `50_external_gis/scripts/build_in_park_candidate_review.py`，输出 `70_outputs/processed_tables/poi_supply_in_park_candidate_review.csv` 和 `40_quality_evidence/in_park_candidate_review_report.md`。
- 园内候选复核清单包含 26 条 OSM polygon 内候选，全部保持为 `p1_in_park_candidate_not_final_supply`。
- 园内候选字段覆盖：rating 26/26，opentime 23/26，tel 22/26，cost_yuan 15/26；7 条为 P0 优先复核项。
- 已运行 `50_external_gis/scripts/build_p0_in_park_followup_worklist.py`，输出 `70_outputs/processed_tables/poi_supply_p0_followup_worklist.csv` 和 `40_quality_evidence/p0_in_park_followup_worklist_report.md`。
- 已运行 `50_external_gis/scripts/fetch_amap_p0_routes.py`，输出 `50_external_gis/amap_routes/amap_p0_route_fetch_log.csv`、`amap_p0_route_results.csv`、`70_outputs/processed_tables/poi_supply_p0_route_access_review.csv` 和 `40_quality_evidence/p0_route_access_review_report.md`。
- P0 路径核验 7 条均返回高德 `status=1/ok`；中心点代理步行距离范围 1219-2552 米，步行时间范围 975-2042 秒。
- 路径日志参数摘要不含高德 Key；所有 P0 路径复核记录仍保持 `can_enter_p2_supply_after_route=no`。
- 最新落实性验证脚本已覆盖空间预过滤、补抓计划、OSM 边界、边界过滤结果、园内候选复核清单和 P0 路径结果，当前 118 项检查通过、失败 0。

## 当前风险

- PPT 中图片对象较多，且方案页包含推演结论，仍需回查 PDF 或其他强证据。
- 关键词扫描只负责定位，不等于完成指标真实性确认。
- `evidence_ledger.csv` 已有第一批指标，但 PPT 收益和缺口行仍是待核验假设。
- PDF 表格虽然已抽出，但还需要清洗左右栏、空行和图表坐标轴干扰。
- PDF 指标目前只完成抽取一致性核验，还没有确认腾讯报告原始口径、样本定义和异常值。
- 城市绿心 PPT 的“咖啡厅覆盖度仅 1.35%”存在口径问题，不能按目标客群覆盖度使用。
- 奥森 PPT 的“精品咖啡仅 2 家”和“瑜伽/普拉提 0 家”已标记为冲突待核验。
- POI 供给底表当前仍是 PDF 热门到访种子，不等于完整供给清单；需要高德 POI 和现场清单补齐坐标、边界、距离和营业状态。
- 高德空间预过滤只是复核优先级排序，缺少真实公园 polygon、入口节点或现场清单前，不得把预过滤状态升级为结论。
- OSM polygon 内候选是 P1 边界过滤候选，不是最终可经营点位；还需要营业状态、入口/路径可达性、经营授权和现场条件核验。
- 园内候选复核清单仍缺入口/路径 API 或现场可达性结果，也缺运营授权确认，不能直接进入最终报告结论。
- P0 路径结果使用公园中心点代理，不是真实入口或游线节点；可达性结论仍需真实入口/节点或现场核验。

## 门禁

如果关键指标存在红色风险，不得进入最终结论，只能进入“待确认清单”。供给数量进入 P2 缺口计算前，必须来自 `evidence_ledger.csv`、边界过滤后的 POI 核验表或明确人工假设表。
