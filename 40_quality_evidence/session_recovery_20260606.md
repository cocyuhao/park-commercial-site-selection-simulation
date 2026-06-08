# 关机后能力恢复证据

- 生成日期：2026-06-06
- 通过项：8
- 失败项：0

## 检查明细

- `pass` plugins_enabled: {'count': 62, 'marketplaces': {'openai-primary-runtime': 3, 'openai-curated': 51, 'openai-bundled': 2, 'community': 2, 'yy199-curated': 4}}
- `pass` ui_ux_pro_max_available: {'path': 'C:\\Users\\Yy199\\.codex\\skills\\ui-ux-pro-max\\SKILL.md', 'exists': True, 'bytes': 10612}
- `pass` skill_inventory_available: {'count': 203}
- `pass` qa_node_stack_available: [{'path': '90_p6_expert_dashboard/qa/package.json', 'exists': True, 'bytes': 337}, {'path': '90_p6_expert_dashboard/qa/package-lock.json', 'exists': True, 'bytes': 97508}]
- `pass` deepseek_api_pass: {'PASS': 4, 'WARN': 0, 'FAIL': 0, 'SKIP': 0}
- `pass` pdf_table_gate_pass: {'PASS': 4, 'WARN': 0, 'FAIL': 0, 'SKIP': 0}
- `pass` amap_smoke_pass: {'run_at': '2026-06-06T14:49:37Z', 'endpoint': 'v5/place/text', 'status': 'ok', 'query_summary': {'keywords': '奥林匹克森林公园', 'region': '北京', 'city_limit': 'true', 'page_size': '1'}, 'amap_status': '1', 'amap_info': 'OK', 'result_count': 1, 'notes': 'Real Amap API call succeeded if status is ok. Key is not stored.'}
- `pass` mainline_context_pass: {'missing_count': 0, 'context_bytes': {'path': '40_quality_evidence/codex_mainline_context_20260604.json', 'exists': True, 'bytes': 6857}}

## 说明

- Chrome DevTools MCP was reconnected in the current session after clearing the isolated chrome-devtools-mcp profile.
- Playwright, axe, and Lighthouse are project QA dependencies under 90_p6_expert_dashboard/qa.
- ui-ux-pro-max is not listed in the current skill menu, but its SKILL.md remains installed and is treated as a manual routing capability for UI decisions.
