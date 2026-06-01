# PPT 假设核验报告

## 结论

- 已核验 PPT 假设指标：15 条。
- 核验状态统计：{'unsupported_financial_assumption': 5, 'formula_consistent_but_inputs_unverified': 4, 'unsupported_business_assumption': 2, 'partial_support_with_scope_gaps': 2, 'conflict_needs_external_validation': 2}
- 财务类指标目前只能确认公式内部一致，不能确认输入真实。
- 城市绿心 PPT 的“咖啡厅覆盖度仅 1.35%”存在口径问题：PDF 原生表格显示 1.35% 是北京市大盘值，目标客群覆盖度是 3.26%，TGI=241。
- 奥森 PPT 的“精品咖啡仅 2 家”和“瑜伽/普拉提 0 家”已标记为冲突待核验，因为 PDF 热门到访表已有相反线索。

## 优先核验项

1. 高德 POI：按园区边界过滤咖啡、茶饮、瑜伽/普拉提、文创、餐酒和冷饮点位。
2. 经营数据：现有商户收入、租金、分成、客单价和转化率。
3. 小时客流：补出 17-22 时段占比，不能只用 17 时峰值替代夜间流量结论。
4. 供需缺口：把 PPT 的 5 个缺口拆成需求证据、供给证据、空间证据和财务证据四列。

## 输出文件

- `40_quality_evidence/ppt_assumption_review.csv`
