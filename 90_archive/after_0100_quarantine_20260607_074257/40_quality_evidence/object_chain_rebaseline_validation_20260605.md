# 对象链路复位验证（2026-06-05）

- status: `pass`
- object_count: `11`
- summary: `{"total_items": 11, "usable_count": 4, "draft_count": 6, "needs_input_count": 0, "blocked_count": 1}`

## 检查
- PASS `http_200`: 200
- PASS `required_object_keys`: []
- PASS `summary_matches_items`: {"total_items": 11, "usable_count": 4, "draft_count": 6, "needs_input_count": 0, "blocked_count": 1}
- PASS `has_state_behavior_choice_validation_chain`: ["ai_session", "behavior_program", "choice_probability", "feature_derivative_scene", "node_progress", "persona_state", "project_scope", "report_draft", "source_material", "spatial_context", "validation_target"]
- PASS `feature_scene_exposes_income_control`: [{"object_key": "feature_derivative_scene", "label": "人物场景假设", "count": 1200, "adopted_count": 0, "locked_count": 0, "status_label": "覆盖池可用，待采用代表场景", "readiness": "draft", "next_action": "采用或锁定能代表真实人群的场景，并复核收入/价格带、天气、时段、空间和供给动作。", "evidence_refs": ["70_outputs/processed_tables/person_simulation_feature_derivatives_1000_20260604.csv", "90_p6_expert_dashboard/cache/simulation_feature_derivative_controls.json"], "view": "data", "action_label": "看场景"}]
- PASS `has_blocked_or_draft_truth`: ["usable", "usable", "draft", "draft", "draft", "draft", "usable", "blocked", "draft", "usable", "draft"]
- PASS `visible_text_has_no_backend_words`: []
- PASS `source_points_to_direction_reset`: "evidence_based_direction_reset_20260605"
