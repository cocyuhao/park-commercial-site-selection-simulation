# 人物场景进入仿真干跑验证（2026-06-07）

- 状态：pass
- 失败数：0
- 验证场景：PSD-0001
- 命中结果行：7
- 边界：本验证只证明采用/锁定人物场景进入结构化干跑，不证明真实客群占比、收益或完整仿真完成。

## 检查项
- `API-FEATURE-POOL` pass: 人物场景覆盖池可读取。 200
- `API-FEATURE-ID` pass: 代表场景存在稳定编号。 PSD-0001
- `API-FEATURE-INCOME-PRICE` pass: 代表场景含收入段和价格带。 {'income_segment_name': '基础预算/公共服务优先', 'income_price_band': '0-30元即时补给或免费基础服务'}
- `API-FEATURE-CONTROL` pass: 代表场景可临时采用并锁定。 {'use': 200, 'lock': 200}
- `API-SIM-JOB-CREATE` pass: 仿真干跑 job 可创建。 200
- `API-SIM-JOB-ID` pass: 仿真 job 返回稳定编号。 SIM-20260607064738-60607
- `JOB-REQUEST-FEATURE-COUNT` pass: job request 记录采用/锁定人物场景数量。 {'scenario_name': 'qa_feature_scene_dry_run', 'seed': 20260607, 'iterations': 25, 'feature_scene_input_count': 1, 'feature_scene_input_ids': ['PSD-0001'], 'feature_scene_usage_rule': '只把用户已采用或已锁定的人物场景作为结构化干跑输入；未采用的覆盖池组合不自动进入任务。', 'real_calibration_input_count': 14, 'real_calibration_input_ids': ['ORCI-001', 'ORCI-002', 'ORCI-003', 'ORCI-101', 'ORCI-102', 'ORCI-103', 'ORCI-104', 'ORCI-105', 'ORCI-106', 'ORCI-107', 'ORCI-108', 'ORCI-201'], 'real_calibration_strength_counts': {'official_macro_boundary': 3, 'local_bigdata_profile': 3, 'local_device_price_proxy': 2, 'local_poi_price_signal': 2, 'local_poi_demand_signal': 1, 'plan_assumption_needs_review': 3}, 'real_calibration_usage_rule': '官方宏观边界、本地大数据画像/代理变量、PPT方案假设必须分层使用，不能混成最终结论。'}
- `JOB-REQUEST-FEATURE-ID` pass: job request 记录采用/锁定场景编号。 ['PSD-0001']
- `JOB-REQUEST-REAL-CALIBRATION-COUNT` pass: job request 记录真实校准输入数量。 14
- `JOB-REQUEST-REAL-CALIBRATION-LAYERS` pass: job request 记录官方宏观、本地代理、竞品价格和方案假设的分层摘要。 {'official_macro_boundary': 3, 'local_bigdata_profile': 3, 'local_device_price_proxy': 2, 'local_poi_price_signal': 2, 'local_poi_demand_signal': 1, 'plan_assumption_needs_review': 3}
- `API-SIM-RESULTS` pass: 仿真结果可读取。 200
- `RESULT-ROW-COUNT` pass: 干跑至少产生一行结构化结果。 22
- `RESULT-FEATURE-MATCH` pass: 至少一个 POI/供给组命中采用人物场景。 {'hit_count': 7, 'total': 22}
- `RESULT-FEATURE-CONTEXT` pass: 命中结果行保存人物场景摘要。 [{'derivative_id': 'PSD-0001', 'title': '晨练/跑步人群 · 清晨 · 口渴/补水', 'persona_name': '晨练/跑步人群', 'income_segment_name': '基础预算/公共服务优先', 'income_price_band': '0-30元即时补给或免费基础服务', 'time_band_name': '清晨', 'time_range': '05:30-08:30', 'weather_name': '舒适天气', 'node_context_name': '入口/闸口', 'demand_trigger_name': '口渴/补水', 'candidate_supply_action_name': '饮水机/直饮水点', 'data_needed': '真实客流、时段分布、天气/节假日记录、周边人口与收入水平、消费支出、客单价、转化率、竞品 POI、步行距离、排队时长、库存/补货、营业关闭时间、现场观察和用户访谈。'}]
- `RESULT-INCOME-PRICE-PRESSURE` pass: 命中结果行保存收入段和消费价格带压力。 {'income_segments': ['基础预算/公共服务优先'], 'price_bands': ['0-30元即时补给或免费基础服务']}
- `RESULT-TIME-WEATHER-PRESSURE` pass: 命中结果行保存时段和天气压力。 {'time_bands': ['清晨'], 'weathers': ['舒适天气']}
- `RESULT-OPERATION-RULES` pass: 命中结果行保存建议动作/运营规则。 ['饮水机/直饮水点']
- `RESULT-ACCURACY-CONTEXT` pass: 命中结果行保存准确性上下文和校准约束。 {'count': 14, 'readiness': '关键门禁未闭合'}
- `RESULT-ACCURACY-LEVERS` pass: 准确性上下文覆盖收入、竞品和时段天气。 ['收入与消费能力', '竞品价格与供给', '时段与天气转化', '空间边界与可达', '经营字段与运维']
- `RESULT-DEEPSEEK-BOUNDARY` pass: 准确性上下文保留 DeepSeek 不能最终判断的边界。 DeepSeek 只能补充候选解释、缺口和草稿，不得给最终概率、最终排名、最终收益或覆盖用户锁定对象。
- `RESULT-CALIBRATION-EVIDENCE` pass: 准确性上下文引用真实校准输入编号。 [{'calibration_id': 'ORCI-001', 'layer': '官方宏观边界', 'indicator_name': '北京市居民人均可支配收入', 'segment': '全市居民', 'period': '2025', 'value': '89090', 'simulation_use': '约束价格带和支付能力讨论的上位边界。', 'cannot_claim': '不能当作奥森周边街道级收入，也不能证明某节点高客单成立。', 'next_data_needed': '补奥森周边 1-3 公里街道/社区收入、居住办公结构和游客来源。'}, {'calibration_id': 'ORCI-002', 'layer': '官方宏观边界', 'indicator_name': '北京市居民人均消费支出', 'segment': '全市居民', 'period': '2025', 'value': '50667', 'simulation_use': '约束文娱、亲子、康养、轻餐等业态的价格带讨论。', 'cannot_claim': '不能替代项目周边真实消费结构和园内实际转化。', 'next_data_needed': '补竞品客单价、园内交易、支付笔数、分时段转化率。'}]
- `RESULT-NEXT-DATA-SCENE` pass: 下一步资料需求包含客群占比/价格敏感度/转化等场景校准。 ['补齐 P3 gate: geometry / visitor_flow / conversion_rate / revenue_cost / operation_authorization / model_gate', '补齐经营字段: 人均消费/成本字段', '补齐采用人物场景对应的客群占比、分时段客流、价格敏感度、真实成交转化和竞品价格', '复核场景动作对应的营业关闭、补货、排队和天气应对规则']
- `RESULT-NOT-FINAL-WARNING` pass: 结果行明确采用场景不是最终客群占比。 ['P3-GATE-001: geometry not closed', 'P3-GATE-002: visitor_flow not closed', 'P3-GATE-003: conversion_rate not closed', 'P3-GATE-004: revenue_cost not closed', 'P3-GATE-005: operation_authorization not closed', 'P3-GATE-006: model_gate not closed', 'user-controlled feature scenes are used as needs_review dry-run inputs, not final population shares', 'candidate group has missing business fields', 'feature-scene pressure requires real flow, conversion, price and weather calibration']
- `RESULT-NO-ROI` pass: 当前干跑不输出 ROI 或最终收益。 
- `EXPORT-CSV` pass: CSV 导出接口可用。 200
- `EXPORT-CSV-FEATURE-FIELDS` pass: CSV 导出包含人物场景上下文字段。 
- `EXPORT-CSV-ACCURACY-FIELDS` pass: CSV 导出包含准确性上下文和校准约束字段。 
- `UI-SIM-FEATURE-FIELDS` pass: 前端仿真结果读取并展示场景命中。 
- `UI-SIM-ACCURACY-FIELDS` pass: 前端仿真结果展示准确性约束。 
- `UI-SIM-PRESSURE-STYLE` pass: 前端仿真结果有人物场景压力样式。 
