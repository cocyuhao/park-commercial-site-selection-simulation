# 人物仿真衍生特征验证（2026-06-07）

- 状态：pass
- 失败数：0
- CSV：`70_outputs/processed_tables/person_simulation_feature_derivatives_1000_20260604.csv`
- 行数：1200
- 字节：2275733

## 维度覆盖

| 维度 | 唯一值数量 |
|---|---:|
| persona_id | 8 |
| income_segment_id | 5 |
| time_band_id | 6 |
| weather_id | 5 |
| node_context_id | 6 |
| demand_trigger_id | 10 |
| candidate_supply_action_id | 21 |

## 检查项

| 检查 | 结果 | 说明 |
|---|---|---|
| row_count_at_least_1000 | pass | rows=1200 |
| required_columns_present | pass | columns=['derivative_id', 'persona_id', 'persona_name', 'persona_core_need', 'income_segment_id', 'income_segment_name', 'income_price_band', 'income_sensitivity_note', 'income_evidence_hint', 'time_band_id', 'time_band_name', 'time_range', 'weather_id', 'weather_name', 'weather_effect', 'node_context_id', 'node_context_name', 'node_role', 'demand_trigger_id', 'demand_trigger_name', 'candidate_supply_action_id', 'candidate_supply_action_name', 'priority_label', 'user_control_needed', 'data_needed', 'deepseek_role', 'why_it_matters'] |
| coverage_persona_id | pass | persona_id=8 minimum=8 |
| coverage_income_segment_id | pass | income_segment_id=5 minimum=5 |
| coverage_time_band_id | pass | time_band_id=6 minimum=6 |
| coverage_weather_id | pass | weather_id=5 minimum=5 |
| coverage_node_context_id | pass | node_context_id=6 minimum=6 |
| coverage_demand_trigger_id | pass | demand_trigger_id=10 minimum=10 |
| coverage_candidate_supply_action_id | pass | candidate_supply_action_id=21 minimum=14 |
| no_mojibake_markers | pass | bad_rows=[] total=0 |
| required_cells_non_empty | pass | empty_counts={} |
| business_terms_covered | pass | missing_terms=[] |
| deepseek_boundary_every_row | pass | bad_rows=[] total=0 |
| user_control_every_row | pass | bad_rows=[] total=0 |
| specific_recommendation_not_raw_score | pass | bad_rows=[] total=0 |

## 边界

This validates a scenario/feature coverage pool, not final simulation accuracy.