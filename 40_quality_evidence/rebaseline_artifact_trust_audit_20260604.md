# 老板方法重基线后的旧产物可信度审计（2026-06-04）

本报告由 `60_model/scripts/audit_rebaseline_artifacts.py` 生成。它不删除旧文件，只按新主控方法给旧产物打标签，防止旧 dry-run、DeepSeek 草稿、测试报告和裸分数继续被误读为已完成仿真。

## 汇总

- A_底座可信: 2 项
- B_产品壳可用: 1 项
- B_需改口径: 1 项
- C_历史草稿: 48 项
- C_测试痕迹: 25 项
- C_草稿候选: 4 项
- D_必须降级: 4 项
- E_需新增: 2 项

## 关键结论

- A 类可以继续作为资料和工具底座，但不能直接证明商业结论。
- B 类是产品壳或结构化 dry-run，必须改口径。
- C 类只能作为草稿候选或历史记录，必须进入 schema/envelope 后复核。
- D 类必须降级，尤其是 P4 草稿、裸分数、排名和收益相关内容。
- E 类是新方向缺失对象，必须补齐后才能声称人物仿真链路推进。

## 明细

| artifact | exists | trust | required_action |
|---|---:|---|---|
| `40_quality_evidence/evidence_ledger.csv` | true | A_底座可信 | 后续新增证据继续按 evidence_id 和 verification_status 入账。 |
| `30_extraction/tables/pdf_native_tables.jsonl` | true | A_底座可信 | 继续用 verify_pdf_tables.py 作为抽取门禁。 |
| `90_p6_expert_dashboard` | true | B_产品壳可用 | 接入人群状态和行为程序 CRUD，并隐藏旧测试/后端文案。 |
| `60_model/simulation/engine.py` | true | B_需改口径 | 不得输出完整仿真、最终排序、ROI 或最终推荐。 |
| `60_model/llm_runs/deepseek_entrance_node_semantic_progress.json` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_entrance_node_semantic_raw.jsonl` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_evidence_candidates_progress.json` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_evidence_candidates_raw.jsonl` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p0_detail_query_plan_progress.json` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p0_detail_query_plan_raw.jsonl` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p0_field_verification_checklist_progress.json` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p0_field_verification_checklist_raw.jsonl` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p0_verification_package_progress.json` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p0_verification_package_raw.jsonl` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p1_quality_report_progress.json` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p1_quality_report_raw.jsonl` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p2_completion_readiness_audit_progress.json` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p2_completion_readiness_audit_raw.jsonl` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p2_geometry_proxy_audit_progress.json` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p2_geometry_proxy_audit_raw.jsonl` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p2_input_schema_candidates_progress.json` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p2_input_schema_candidates_raw.jsonl` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p2_real_site_semantic_progress.json` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p2_real_site_semantic_raw.jsonl` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p2_source_coverage_audit_progress.json` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p2_source_coverage_audit_raw.jsonl` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p3_calibration_execution_package_progress.json` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p3_calibration_execution_package_raw.jsonl` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p3_prework_package_progress.json` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p3_prework_package_raw.jsonl` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p4_feedback_draft_progress.json` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p4_feedback_draft_raw.jsonl` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_p4_premature_audit_raw.jsonl` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_project_context_sync_latest.json` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_project_context_sync_progress.json` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_project_context_sync_raw.jsonl` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_smoke_test_latest.json` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_table_classification_progress.json` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `60_model/llm_runs/deepseek_table_classification_raw.jsonl` | true | C_历史草稿 | 通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。 |
| `70_outputs/processed_tables/p2_docx_project_semantic_draft_deepseek.csv` | true | C_历史草稿 | 进入 envelope 后重新抽样检查，不得入 checked。 |
| `70_outputs/processed_tables/p2_dwg_conversion_worklist_deepseek.csv` | true | C_历史草稿 | 进入 envelope 后重新抽样检查，不得入 checked。 |
| `70_outputs/processed_tables/p2_geometry_proxy_limitations_deepseek.csv` | true | C_历史草稿 | 进入 envelope 后重新抽样检查，不得入 checked。 |
| `70_outputs/processed_tables/p2_pdf_proxy_zone_candidates_deepseek.csv` | true | C_历史草稿 | 进入 envelope 后重新抽样检查，不得入 checked。 |
| `70_outputs/processed_tables/p2_pdf_spatial_label_draft_deepseek.csv` | true | C_历史草稿 | 进入 envelope 后重新抽样检查，不得入 checked。 |
| `70_outputs/processed_tables/p3_calibration_acceptance_criteria_deepseek.csv` | true | C_历史草稿 | 保持 gate pending，直到真实资料或现场复核闭合。 |
| `70_outputs/processed_tables/p3_calibration_blocker_register_deepseek.csv` | true | C_历史草稿 | 保持 gate pending，直到真实资料或现场复核闭合。 |
| `70_outputs/processed_tables/p3_calibration_data_requirements_deepseek.csv` | true | C_历史草稿 | 保持 gate pending，直到真实资料或现场复核闭合。 |
| `70_outputs/processed_tables/p3_calibration_evidence_request_worklist_deepseek.csv` | true | C_历史草稿 | 保持 gate pending，直到真实资料或现场复核闭合。 |
| `70_outputs/processed_tables/p3_dwg_conversion_work_order_deepseek.csv` | true | C_历史草稿 | 保持 gate pending，直到真实资料或现场复核闭合。 |
| `70_outputs/processed_tables/p3_p2_to_calibration_field_mapping_deepseek.csv` | true | C_历史草稿 | 保持 gate pending，直到真实资料或现场复核闭合。 |
| `70_outputs/processed_tables/p3_p4_route_decision_deepseek.csv` | true | C_历史草稿 | 保持 gate pending，直到真实资料或现场复核闭合。 |
| `70_outputs/processed_tables/p3_scenario_assumption_limits_deepseek.csv` | true | C_历史草稿 | 保持 gate pending，直到真实资料或现场复核闭合。 |
| `80_delivery/ai_chat_reports/CHAT-20260602175743-0001.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603094810-0004.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603114927-0004.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603115010-0005.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603115039-0007.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603115614-0008.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603115710-0009.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603115819-0010.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603115920-0011.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603120028-0012.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603120120-0013.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603120226-0014.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603120313-0015.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603120411-0016.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603120523-0017.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603120804-0018.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603120858-0019.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603120951-0020.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603121046-0021.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603121145-0022.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603121236-0023.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603121336-0024.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603121429-0025.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603121528-0026.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `80_delivery/ai_chat_reports/CHAT-20260603121638-0027.md` | true | C_测试痕迹 | 正式报告生成时要重新按商业报告结构和证据状态输出。 |
| `70_outputs/processed_tables/p2_behavior_program_templates_20260604.csv` | true | C_草稿候选 | 逐行映射到 schema，补 source_refs、missing_inputs 和 adoption_state。 |
| `70_outputs/processed_tables/p2_persona_state_profiles_20260604.csv` | true | C_草稿候选 | 逐行映射到 schema，补 source_refs、missing_inputs 和 adoption_state。 |
| `70_outputs/processed_tables/p2_simulation_validation_targets_20260604.csv` | true | C_草稿候选 | 逐行映射到 schema，补 source_refs、missing_inputs 和 adoption_state。 |
| `60_model/simulation/persona_behavior.py` | true | C_草稿候选 | 映射到 persona_state / behavior_program schema 后再进入 UI。 |
| `70_outputs/processed_tables/p4_feedback_data_request_to_partner_deepseek.csv` | true | D_必须降级 | 移除或折叠裸排名/裸分数，重写为优先级、依据、建议和缺口。 |
| `70_outputs/processed_tables/p4_feedback_node_priority_draft_deepseek.csv` | true | D_必须降级 | 移除或折叠裸排名/裸分数，重写为优先级、依据、建议和缺口。 |
| `70_outputs/processed_tables/p4_feedback_scenario_matrix_draft_deepseek.csv` | true | D_必须降级 | 移除或折叠裸排名/裸分数，重写为优先级、依据、建议和缺口。 |
| `70_outputs/processed_tables/p4_parallel_skeleton_backlog_deepseek.csv` | true | D_必须降级 | 移除或折叠裸排名/裸分数，重写为优先级、依据、建议和缺口。 |
| `choice_probability.schema.json` | false | E_需新增 | 新增选择概率 schema，连接状态、行为、空间成本、排队、价格、竞品和证据。 |
| `macro_validation_plan.md` | false | E_需新增 | 定义 SARIMA/SSIM/KL/DTW/峰谷/现场复核等验证目标与数据缺口。 |
