# 先进能力与旧方法信任审计（2026-06-05）

- status: `pass`
- capability_failure_count: `0`
- page_validation_status: `pass`
- axe_validation_status: `pass`
- lighthouse_user_flow_status: `pass`
- otel_trace_status: `pass`

## 官方资料与采用点
- [Playwright accessibility testing](https://playwright.dev/docs/accessibility-testing): 用 axe-core/ARIA/浏览器截图补充旧 Selenium 点击检查；官方也提醒自动化只能发现一部分问题。
- [Playwright trace viewer](https://playwright.dev/docs/trace-viewer): 保留可回放 trace，避免只看最终截图。
- [OpenTelemetry Python instrumentation](https://opentelemetry.io/docs/languages/python/instrumentation/): 把 FastAPI、HTTPX 和 AI/API 调用纳入 span，而不是只看页面是否打开。
- [@axe-core/playwright](https://github.com/dequelabs/axe-core-npm/tree/develop/packages/playwright): 补自动可访问性扫描，但不得当成完整人类视觉验收。
- [Lighthouse user flows](https://web.dev/articles/lighthouse-user-flows): 补交互过程性能和可用性证据，不只测首屏。

## 能力检查
- PASS `python_modern_validation_stack`: {"playwright": "1.60.0", "selenium": "4.44.0", "opentelemetry-sdk": "1.42.1", "opentelemetry-distro": "0.63b1", "opentelemetry-instrumentation-fastapi": "0.63b1", "opentelemetry-instrumentation-httpx": "0.63b1", "fastapi": "0.115.6", "uvicorn": "0.34.0", "httpx": "0.28.1"}
- PASS `node_accessibility_and_user_flow_stack`: {"@axe-core/playwright": "4.11.3", "@playwright/test": "1.60.0", "lighthouse": "13.3.0"}
- PASS `learning_evidence_files_present`: {"flowus": {"path": "10_research/flowus_design_learning_20260605/flowus_153eefbc_snapshot.txt", "exists": true, "bytes": 12195}, "boss_rebaseline": {"path": "10_research/boss_method_materials_20260604/full_system_rebaseline_20260604.md", "exists": true, "bytes": 13080}, "boss_inventory": {"path": "10_research/boss_method_materials_20260604/boss_model_inventory_20260604.md", "exists": true, "bytes": 11173}, "advanced_register": {"path": "10_research/advanced_ai_learning_absorption_register_20260604.md", "exists": true, "bytes": 12749}, "direction_reset": {"path": "10_research/evidence_based_direction_reset_20260605.md", "exists": true, "bytes": 10212}, "page_blueprint": {"path": "00_control/page_layer_rebuild_blueprint_20260605.md", "exists": true, "bytes": 4917}, "page_validation": {"path": "40_quality_evidence/page_layer_rebuild_validation_20260605.json", "exists": true, "bytes": 2949}, "axe_validation": {"path": "40_quality_evidence/axe_accessibility_probe_20260605.json", "exists": true, "bytes": 1235}, "lighthouse_user_flow": {"path": "40_quality_evidence/lighthouse_user_flow_20260605.json", "exists": true, "bytes": 2477}, "lighthouse_user_flow_html": {"path": "40_quality_evidence/lighthouse_user_flow_20260605/p6_dashboard_user_flow.html", "exists": true, "bytes": 1328370}, "otel_trace_probe": {"path": "40_quality_evidence/otel_fastapi_trace_probe_20260605.json", "exists": true, "bytes": 5696}, "context_risk_audit": {"path": "40_quality_evidence/project_context_legacy_risk_audit_20260605.json", "exists": true, "bytes": 59218}, "method_coverage": {"path": "40_quality_evidence/method_model_landing_coverage_20260605.json", "exists": true, "bytes": 16348}}
- PASS `page_layer_validation_passes`: {"status": "pass", "failure_count": 0, "screenshots": {"overview": "40_quality_evidence/page_layer_rebuild_validation_20260605/overview_chain_command.png", "ai_workspace": "40_quality_evidence/page_layer_rebuild_validation_20260605/ai_workspace_reading_width.png"}}
- PASS `axe_accessibility_zero_violations`: {"status": "pass", "failure_count": 0, "view_violations": []}
- PASS `lighthouse_user_flow_passes`: {"status": "pass", "failure_count": 0, "flow_report_html": "40_quality_evidence/lighthouse_user_flow_20260605/p6_dashboard_user_flow.html", "steps": ["打开全局推进台", "切换 AI、资料池、节点与报告", "报告页与资料池状态快照"]}
- PASS `otel_trace_probe_passes`: {"status": "pass", "failure_count": 0, "span_count": 9, "responses": {"/api/dashboard": 200, "/api/object-chain": 200, "/api/ai/sessions": 200}}
- PASS `legacy_risk_audit_exists`: {"file_count": 949, "text_like_file_count": 738, "risk_counts": {"complete_simulation_claim": 329, "final_claim": 579, "roi_revenue_claim": 341, "legacy_dry_run": 224, "raw_internal_ui": 4238, "score_overclaim": 168, "deepseek_boundary": 7059}}
- PASS `method_model_coverage_exists`: {"covered": 4, "partial": 5, "missing": 0}

## 当前页面验证失败
- 暂无失败项。

## 先进验证结果
- axe 违规视图：[]
- Lighthouse 失败项：[]
- OTel 失败项：[]

## 旧方法降级/替换矩阵
- `裸节点分数 / 旧 discussion_score` -> 降级为内部排序痕迹；用户界面只看推进优先级、依据、建议和待补动作。；风险：伪精确，用户无法理解分数来源，容易把草案当排名。；依据：老板资料 DLR/FLR/SSR；HumanLM；用户关于分数意义不详的纠正。
- `旧 Selenium 全点一遍` -> 保留兼容；高级 QA 改为 Playwright trace + ARIA + axe + Lighthouse user flow + 人工截图复核。；风险：只能证明按钮能点，不能证明视觉、人类理解、可访问性、trace 或 AI 输出边界。；依据：Playwright/axe/Lighthouse 官方资料；DEC-081；用户关于检查方法老的纠正。
- `旧 P4 dry-run / 完整仿真说法` -> 改为结构化预检和验证目标；通过后也只说明可进入下一轮复核。；风险：缺 DWG/GIS、真实客流、转化、收益成本和运营授权时不能宣称完整仿真。；依据：老板 RL+LLM 社区仿真材料；simulation_validation_target；DEC-072。
- `DeepSeek 一次性草稿` -> 低成本语义工人；只产出候选、解释、报告工作稿，必须 schema/本地校验/人工采用。；风险：便宜但不稳，容易迎合和越权生成最终判断。；依据：DeepSeek capacity note；老板资料；DEC-076。
- `静态/兜底地图作为空间证明` -> 只作降级可见层；真实空间链路仍需高德交互、POI、边界、DWG/GIS 和校准。；风险：能看不等于能拖拽、能自由定位，更不等于空间仿真。；依据：用户高德截图；空间运动层重基线；DEC-084。
- `旧页面补丁式视觉` -> 按对象链重写页面层；首屏、AI、资料池、节点池都围绕对象和检查点。；风险：学了资料但仍按旧页面结构推进，导致高级方法没有进入使用路径。；依据：Flowus 三页；page_layer_rebuild_blueprint_20260605；DEC-084。

## 下一步动作
1. 把 page/axe/Lighthouse/OTel 四类验证纳入 verify_project_implementation.py 总门禁。
2. 继续用同一套验证约束后续页面大改，避免只补旧壳。
3. 把旧方法矩阵写入 handoff 和 findings，避免新对话继续使用裸分数、旧 dry-run 和补丁式视觉。
4. 后续节点和地图链路若大改，也必须补对应的对象链验证脚本和人类视觉截图。
