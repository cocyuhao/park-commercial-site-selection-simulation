# 第一批证据入账报告

## 结果

- 已写入 `40_quality_evidence/evidence_ledger.csv`：52 条指标。
- 证据类型统计：{'source_report_pdf': 37, 'presentation_assumption': 15}
- 校验状态统计：{'checked': 37, 'needs_review': 13, 'conflict': 2}

## 覆盖范围

- 客流：城市绿心年总到访、日峰值、时均峰值；奥森日峰值和时均峰值。
- TGI：餐饮消费、咖啡厅、美食/冷饮等与商业业态相关的画像指标。
- POI：PDF 原生表格中的区域内美食类热门到访 POI 及人均消费。
- 收益：PPT 方案中的年收益、投资额、回收期，均标记为 `presentation_assumption`。
- 供需缺口：PPT 方案中的缺口数量和供给现状，均标记为 `needs_review`。
- PPT 复核补充：追加婚育、酒店、旅游景点、瑜伽、普拉提、咖啡相关 PDF 支持指标。

## 后续核验重点

- PDF 指标目前只完成抽取一致性核验，仍需确认腾讯报告口径和样本定义。
- PPT 收益和缺口指标不能直接进入最终结论，需回查财务参数、真实经营数据和高德 POI。
- 双栏 PDF 表格后续要继续标准化拆分，避免左右栏混行影响批量入账。
