# P0 待核验清单本地审计报告

## 结论

- 审计项状态：{'pass': 13}
- 清单类型分布：{'p0_poi_business_and_authorization': 7, 'primary_access_node_field_check': 20, 'secondary_parking_or_visit_node_field_check': 7}
- 7 条业务核验项缺失经营字段分布：{'contact': 4, 'cost_yuan': 5, 'opening_hours': 3}
- 当前 34 条清单都仍不能在本地直接关单；本轮能做的是结构核验、去歧义和现场执行优化。

## 本地已核验事实

- 7 条业务核验项与 enriched P0 工作单一一对应。
- 7 条业务核验项的缺失经营字段与当前工作单保持一致。
- 7 条 P0 路径记录都只有中心点代理步行结果，仍不能替代真实入口或节点路径。
- 27 条节点类清单全部仍属于官方或现场确认范围，当前不能在本地改成已确认入口。

## 交接细节提醒

- 本轮未发现新的结构性警告项。

## 现场执行建议

- duplicate node clusters for field visit batching={'城市绿心森林公园:P6停车场': 2, '奥林匹克森林公园:北园东门1号停车场': 3, '奥林匹克森林公园:北园体育园地面停车场': 2, '奥林匹克森林公园:北园北门地面停车场': 2, '奥林匹克森林公园:北园西门停车场': 2, '奥林匹克森林公园:南园东门停车场': 2, '奥林匹克森林公园:南园西门停车场': 2}

## 输出文件

- `40_quality_evidence/p0_field_verification_checklist_local_review.csv`
- `40_quality_evidence/p0_field_verification_checklist_local_review.md`
