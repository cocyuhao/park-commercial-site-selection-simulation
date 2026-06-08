# 奥森综合报告验证

- 生成日期：2026-06-06
- 报告 Markdown：C:\Users\Yy199\Desktop\仿真设计\80_delivery\site_selection_gap_report_latest.md
- 报告 JSON：C:\Users\Yy199\Desktop\仿真设计\80_delivery\site_selection_gap_report_latest.json
- 通过项：14
- 失败项：0

## 检查明细

- `pass` report_files_written: {'md': 'C:\\Users\\Yy199\\Desktop\\仿真设计\\80_delivery\\site_selection_gap_report_latest.md', 'json': 'C:\\Users\\Yy199\\Desktop\\仿真设计\\80_delivery\\site_selection_gap_report_latest.json'}
- `pass` report_length: 37434
- `pass` node_count: 6
- `pass` all_nodes_named: ['桃花源白房子', '奥运廉洁主题展馆', '12#西分区', '南门地下预埋空间', '南门露天剧场', '10#2A03']
- `pass` business_advice_present: ['修正建议', '当前推进事项', 'CAD / 图纸处理', '不能声明最终节点排序', '控制点校准', '资质']
- `pass` human_text_clean: []
- `pass` evidence_highlights: 18
- `pass` cad_converted_two_drawings: ['osen_north_t5', 'osen_south_t5']
- `pass` cad_anchor_terms: ['南入口', '2A03', '露天剧场', '廉洁馆', '公园南门']
- `pass` north_pdf_proxy_hit: {'generated_at': '2026-06-05T17:40:18', 'source_file': 'CAD图及其计划\\奥森北园(字体放大)-改造建筑示意-Model(1).pdf', 'method': 'PyMuPDF text + vector drawing scan; used as readable proxy for north CAD drawing.', 'page_summaries': [{'page': 1, 'text_length': 1766, 'text_line_count': 492, 'vector_drawing_count': 249061}], 'hits': [{'page': 1, 'text': '项目1：桃花源白房子（155㎡）', 'keywords': ['桃花源', '白房子'], 'bbox': [466.4, 546.0713, 515.4359, 549.5739]}], 'use_boundary': 'PDF is a readable drawing proxy. It helps locate labels and cross-check DWG conversion, but does not replace georeferenced CAD/GIS calibration.'}
- `pass` deepseek_runtime_ok: {'PASS': 4, 'WARN': 0, 'FAIL': 0, 'SKIP': 0}
- `pass` pdf_table_runtime_ok: {'PASS': 4, 'WARN': 0, 'FAIL': 0, 'SKIP': 0}
- `pass` amap_runtime_ok: {'run_at': '2026-06-06T14:49:37Z', 'endpoint': 'v5/place/text', 'status': 'ok', 'query_summary': {'keywords': '奥林匹克森林公园', 'region': '北京', 'city_limit': 'true', 'page_size': '1'}, 'amap_status': '1', 'amap_info': 'OK', 'result_count': 1, 'notes': 'Real Amap API call succeeded if status is ok. Key is not stored.'}
- `pass` json_method_trace_internal_only: ['report_id', 'title', 'generated_at', 'output_status', 'not_final', 'source_upload_count', 'gap_status', 'summary', 'executive_summary', 'method_basis', 'method_trace', 'expert_review_basis', 'source_foundation', 'original_plan_reading', 'current_judgements', 'revision_advice', 'simulation_readiness', 'top_gaps', 'nodes', 'next_actions']

## 使用边界

- 本报告是工作稿，不是最终 ROI、最终排序或完整人群仿真结果。
- CAD 已转 DXF 并能抽取锚点，但仍需控制点校准后才能进入 GIS 路径级仿真。
- DeepSeek 只承担低成本草稿和候选生成，最终报告仍需人工/高能力 agent 复核。
