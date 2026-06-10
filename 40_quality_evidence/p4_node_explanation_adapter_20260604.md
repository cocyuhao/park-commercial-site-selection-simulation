# P4 节点解释 adapter 报告（2026-06-04）

本报告由 `60_model/scripts/adapt_p4_node_explanations.py` 生成。

## 口径

旧 P4 节点分数和排名语言已降级为 `node_explanation` 草稿。主输出是优先级、依据、具体建议、证据缺口和复核动作；旧分数只保留在 `score_if_any` 中，并默认隐藏。

- 节点数：6
- Envelope：`60_model/llm_runs/contract_envelopes/p4_node_explanation_from_legacy_20260604.json`
- CSV：`70_outputs/processed_tables/p4_node_explanation_from_legacy_20260604.csv`

## 下一步

- 前端节点详情和报告生成优先读取 `specific_advice`、`evidence_gaps`、`review_actions`。
- 复核 persona_state 和 behavior_program 后，再把节点解释升级为 `state -> behavior -> demand -> advice` 完整链条。
- 不得把旧讨论分当最终排序或收益预测。
