# 历史问题全仓暴露面审计

- 生成时间：2026-06-09T09:55:44
- 扫描文件数：1192
- 跳过超大文本数：16
- 命中总数：21338
- 严重度：{"context": 7290, "low": 3175, "medium": 2473, "archive": 8400}
- 暴露面：{"durable_context": 7290, "other": 3175, "active_code": 2387, "delivery_internal": 735, "customer_visible": 86, "archive": 7170, "model_run_archive": 495}

## 当前高风险命中

- 无

## 高命中文件

- `40_quality_evidence/agent_editor_influence_surface_audit_20260609.json` {"context": 2110}
- `30_extraction/tables/pdf_table_evidence_candidates_deepseek.csv` {"low": 1184}
- `30_extraction/scripts/verify_project_implementation.py` {"medium": 734}
- `90_archive/pre_rollback_after_0100_snapshot_20260607_074108/30_extraction/scripts/verify_project_implementation.py` {"archive": 722}
- `30_extraction/tables/pdf_evidence_candidate_review_queue.csv` {"low": 592}
- `40_quality_evidence/verification/implementation_verification_20260526.csv` {"context": 431}
- `40_quality_evidence/verification/implementation_verification_20260526.md` {"context": 416}
- `progress.md` {"context": 366}
- `90_archive/pre_rollback_after_0100_snapshot_20260607_074108/progress.md` {"archive": 358}
- `90_archive/pre_rollback_after_0100_snapshot_20260607_074108/40_quality_evidence/verification/implementation_verification_20260526.csv` {"archive": 357}
- `90_archive/pre_rollback_after_0100_snapshot_20260607_074108/40_quality_evidence/verification/implementation_verification_20260526.md` {"archive": 342}
- `30_extraction/tables/pdf_table_topic_draft_deepseek.csv` {"low": 329}
- `90_archive/runtime_cache_before_cleanup_20260608/20260608_173537/ai_sessions.json` {"archive": 311}
- `handoff_next_chat.md` {"context": 292}
- `90_archive/pre_rollback_after_0100_snapshot_20260607_074108/handoff_next_chat.md` {"archive": 286}
- `90_archive/runtime_cache_before_cleanup_20260608/20260608_173537/simulation_objects.json` {"archive": 284}
- `90_archive/codex_rollback_snapshot_20260607_072523/90_p6_expert_dashboard__app.py` {"archive": 253}
- `90_archive/pre_rollback_after_0100_snapshot_20260607_074108/90_archive/codex_rollback_snapshot_20260607_072523/90_p6_expert_dashboard__app.py` {"archive": 253}
- `90_archive/pre_rollback_after_0100_snapshot_20260607_074108/90_p6_expert_dashboard/app.py` {"archive": 253}
- `findings.md` {"context": 250}

## 解释规则

- `archive`：归档历史，不能直接恢复成当前事实。
- `context`：交接/证据中的历史记录，允许存在但需要标清当前边界。
- `medium/high`：当前代码、客户可见文件或运行入口中需要复核或修复。
