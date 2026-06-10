# choice_probability adapter 报告（2026-06-04）

## 口径

本轮把 P2 人群状态、P2 行为程序和 P4 节点解释转成选择概率候选。所有 `probability_value` 保持空值，状态为 `needs_review`，因为真实客流、路线、排队、转化率、收益成本和授权仍未闭合。

- 候选数：36
- DuckDB 复核 CSV 行数：36
- Schema 失败数：0
- Envelope：`60_model/llm_runs/contract_envelopes/choice_probability_from_p2_p4_20260604.json`
- CSV：`70_outputs/processed_tables/choice_probability_from_p2_p4_20260604.csv`

## 下一步

- 接入 P6 对象池，允许用户采用、放弃、编辑、锁定这些候选。
- 真实客流和转化率完成复核后，再用 SALib/Optuna 做敏感性和校准，不直接让 DeepSeek 给概率。
