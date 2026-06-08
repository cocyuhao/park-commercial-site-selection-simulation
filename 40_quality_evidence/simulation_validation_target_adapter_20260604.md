# simulation_validation_target adapter 报告（2026-06-04）

## 口径

本轮把 P2 验证目标草稿转成可复核对象，覆盖状态-行为链、路线可达、选择概率、时间序列、宏观分布和业务决策。它们用于阻止旧 dry-run 或 LLM 草稿被误写成完整仿真。

- 验证目标数：10
- DuckDB 复核 CSV 行数：10
- Schema 失败数：0
- Envelope：`60_model/llm_runs/contract_envelopes/simulation_validation_target_from_p2_20260604.json`
- CSV：`70_outputs/processed_tables/simulation_validation_target_from_p2_20260604.csv`

## 下一步

- 把这些验证目标接到 P6 资料/仿真门禁面板。
- 优先补 `visitor_flow_time`、`route_choice`、`conversion_rate` 和 `geometry`，否则不能宣称真实仿真完成。
