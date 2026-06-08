# 报告人物场景输入链路验证（2026-06-07）

- 状态：pass
- 失败数：0
- 验证场景：PSD-0001
- 边界：本验证只证明用户采用/锁定的人物场景进入报告和 AI prompt，不证明完整人群仿真完成。

## 检查项
- `API-FEATURE-POOL` pass: 人物场景覆盖池接口可用。 200
- `API-FEATURE-ID` pass: 可选代表场景存在稳定编号。 PSD-0001
- `API-FEATURE-INCOME-FIELDS` pass: 代表场景带出收入段和消费价格带。 {'income_segment_name': '基础预算/公共服务优先', 'income_price_band': '0-30元即时补给或免费基础服务'}
- `API-FEATURE-CONTROL` pass: 代表场景可被采用并锁定。 {'use': 200, 'lock': 200}
- `API-REPORT-CONTEXT` pass: 采用/锁定的人物场景进入 dashboard 报告上下文。 {'count': 1, 'ids': ['PSD-0001']}
- `API-REPORT-INCOME-PRICE` pass: 报告上下文汇总收入段和消费价格带。 {'income_segments': ['基础预算/公共服务优先'], 'price_bands': ['0-30元即时补给或免费基础服务']}
- `API-REPORT-REAL-CALIBRATION` pass: 真实校准输入进入 dashboard 报告上下文。 {'count': 14, 'strengths': {'official_macro_boundary': 3, 'local_bigdata_profile': 3, 'local_device_price_proxy': 2, 'local_poi_price_signal': 2, 'local_poi_demand_signal': 1, 'plan_assumption_needs_review': 3}}
- `API-REPORT-READINESS-IMPACT` pass: 采用场景改变报告的可运行事项说明。 ['按策划书节点生成讨论级报告和修改建议。', '按 CAD 标签建立南园项目锚点清单。', '按证据台账识别咖啡、冷饮、瑜伽、餐饮消费和到访峰值等需求线索。', '按用户已采用/锁定的人物场景，做讨论级收入水平、消费价格带、时段天气和节点动作敏感性审查。']
- `API-REPORT-CALIBRATION-READINESS` pass: 真实校准输入改变报告的可运行事项说明。 ['按策划书节点生成讨论级报告和修改建议。', '按 CAD 标签建立南园项目锚点清单。', '按证据台账识别咖啡、冷饮、瑜伽、餐饮消费和到访峰值等需求线索。', '按用户已采用/锁定的人物场景，做讨论级收入水平、消费价格带、时段天气和节点动作敏感性审查。', '按 14 条真实校准输入，分层讨论收入/消费边界、本地画像、设备价格代理、竞品客单和方案假设。']
- `API-REPORT-NEXT-ACTION-IMPACT` pass: 采用场景改变当前推进事项。 ['把真实校准输入逐层补证：先补奥森周边 1-3 公里收入水平、消费能力、人口结构和竞品客单，再补分时段客流、天气转化、真实支付与许可消防。', '围绕已采用/锁定人物场景逐项补证：收入段、价格带、访问时段、天气条件、到达路径、替代供给和真实转化。', '用南门、露天剧场、2A03、廉洁馆等 CAD 锚点做一次图纸到地图的控制点校准，输出可复核 GeoJSON。']
- `API-REPORT-CALIBRATION-NEXT-ACTION` pass: 真实校准输入进入当前推进事项。 ['把真实校准输入逐层补证：先补奥森周边 1-3 公里收入水平、消费能力、人口结构和竞品客单，再补分时段客流、天气转化、真实支付与许可消防。', '围绕已采用/锁定人物场景逐项补证：收入段、价格带、访问时段、天气条件、到达路径、替代供给和真实转化。', '用南门、露天剧场、2A03、廉洁馆等 CAD 锚点做一次图纸到地图的控制点校准，输出可复核 GeoJSON。', '对六个节点分别补齐客流入口、停留时长、转化率、客单价、租金/分成、装修和运营成本。']
- `PROMPT-FEATURE-CONTEXT` pass: DeepSeek 讨论优先级 prompt 带入采用/锁定场景上下文。 你是公园商业选址专家驾驶舱的 DeepSeek AI 草稿助手。只能输出 needs_review / not_final 的反馈草案解释。不得输出最终推荐、最终排序、收益预测、坐标、面积推断、DWG 几何结论或 checked 证据。必须说明为什么当前只是 feedback draft，并列出缺失数据。如果用户已采用或锁定人物场景，必须把收入水平、消费价格带、时段、天气、空间节点和需求触发作为约束变量；不能把这些场景当真实客群占比或最终仿真结果。如果使用真实校准输入，必须区分官方宏观边界、本地大数据画像/代理变量和PPT方案假设；不得把设备价格代理或PPT假设写成街道级收入、真实成交或最终收益。
请用中文解释多个节点的讨论优先级，只能叫讨论优先级，不能叫最终排名。
输出 JSON，字段为 output_status, boundary_notice, priority_discussion, missing_data, partner_questions。
节点草案：[{"node_id": "P2-NODE-001", "node_name": "桃花源白房子", "area_sq
- `PROMPT-INCOME-PRICE-RULE` pass: DeepSeek prompt 明确收入水平和消费价格带必须作为约束变量。 收入水平/消费价格带
- `PROMPT-FEATURE-ID` pass: DeepSeek prompt 带入被采用场景编号。 PSD-0001
- `API-SITE-REPORT` pass: 报告生成接口可用。 200
- `API-SITE-REPORT-CONTEXT` pass: 报告生成接口返回采用场景上下文。 [{'derivative_id': 'PSD-0001', 'title': '晨练/跑步人群 · 清晨 · 口渴/补水', 'persona_name': '晨练/跑步人群', 'income_segment_name': '基础预算/公共服务优先', 'income_price_band': '0-30元即时补给或免费基础服务', 'income_sensitivity_note': '价格敏感度高，优先判断是否应做公益性饮水、座椅、卫生间、导视和低价透明补给。', 'time_band_name': '清晨', 'time_range': '05:30-08:30', 'weather_name': '舒适天气', 'node_context_name': '入口/闸口', 'demand_trigger_name': '口渴/补水', 'candidate_supply_action_name': '饮水机/直饮水点', 'why_it_matters': '晨练/跑步人群在清晨、舒适天气、入口/闸口遇到“口渴/补水”时，若收入/消费口径按“基础预算/公共服务优先（0-30元即时补给或免费基础服务）”处理，建议优先评估“饮水机/直饮水点”。判断必须结合收入/预算、同行关系、路径成本、供给真实性和运营承接能力，输出应是可执行修改建议而不是裸分。', 'data_needed': '真实客流、时段分布、天气/节假日记录、周边人口与收入水平、消费支出、客单价、转化率、竞品 POI、步行距离、排队时长、库存/补货、营业关闭时间、现场观察和用户访谈。', 'status_label': '已采用 / 已锁定'}]
- `API-SITE-REPORT-REAL-CALIBRATION` pass: 报告生成接口返回真实校准输入上下文。 {'count': 14, 'items': [{'calibration_id': 'ORCI-001', 'dimension': 'macro_income', 'indicator_name': '北京市居民人均可支配收入', 'segment': '全市居民', 'period': '2025', 'value': '89090', 'unit': '元/人/年', 'source_strength': 'official_macro_boundary', 'simulation_use': '约束价格带和支付能力讨论的上位边界。', 'cannot_claim': '不能当作奥森周边街道级收入，也不能证明某节点高客单成立。', 'next_data_needed': '补奥森周边 1-3 公里街道/社区收入、居住办公结构和游客来源。'}, {'calibration_id': 'ORCI-002', 'dimension': 'macro_consumption', 'indicator_name': '北京市居民人均消费支出', 'segment': '全市居民', 'period': '2025', 'value': '50667', 'unit': '元/人/年', 'source_strength': 'official_macro_boundary', 'simulation_use': '约束文娱、亲子、康养、轻餐等业态的价格带讨论。', 'cannot_claim': '不能替代项目周边真实消费结构和园内实际转化。', 'next_data_needed': '补竞品客单价、园内交易、支付笔数、分时段转化率。'}]}
- `DOCX-WRITTEN` pass: DOCX 报告已生成且文件体量正常。 {'path': 'C:\\Users\\Yy199\\Desktop\\仿真设计\\80_delivery\\osen_integrated_site_selection_report_20260606.docx', 'bytes': 57500}
- `DOCX-FEATURE-SECTION` pass: DOCX 包含人物场景输入章节。 人物场景输入
- `DOCX-INCOME-PRICE` pass: DOCX 包含收入/价格带口径。 收入/价格带
- `DOCX-FEATURE-ITEM` pass: DOCX 包含被采用代表场景。 PSD-0001
- `DOCX-REAL-CALIBRATION-SECTION` pass: DOCX 包含真实校准输入分层章节。 真实校准输入/官方宏观边界/设备价格代理
- `MD-FEATURE-SECTION` pass: Markdown 报告包含人物场景输入章节。 C:\Users\Yy199\Desktop\仿真设计\80_delivery\site_selection_gap_report_latest.md
- `MD-FEATURE-ID` pass: Markdown 报告包含被采用代表场景编号。 PSD-0001
- `MD-REAL-CALIBRATION-SECTION` pass: Markdown 报告包含真实校准输入分层章节。 C:\Users\Yy199\Desktop\仿真设计\80_delivery\site_selection_gap_report_latest.md
- `UI-REPORT-FEATURE-CONTEXT` pass: 前端报告页读取并展示人物场景上下文。 
- `UI-REPORT-REAL-CALIBRATION` pass: 前端报告页读取并展示真实校准输入上下文。 
- `UI-REPORT-FEATURE-STYLE` pass: 前端报告页有人物场景卡片样式。 
