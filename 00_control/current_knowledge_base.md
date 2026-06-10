# 当前知识库入口（每轮必读）

更新时间：2026-06-09 21:50

## 当前结论

本项目已经建立近年资料知识库、仿真栈通用 Mega、计算与模型 Mega、部署级核心库和可调用的模型计算知识包。后续不允许只凭经验改仿真、DeepSeek 约束、收益预测、节点解释或客户报告；必须先查本入口列出的核心库与模型包。

当前状态要分层看，不能把所有资料混成一锅：

- 主筛选库：`23,091` 条，作为方法与背景参考。
- 部署级核心库：`3,085` 条，作为当前实现和提示词约束的优先依据。
- 方法参考库：`17,306` 条，能启发模型结构，但不能直接写进客户结论。
- 剔除/暂不使用：`2,700` 条，主要是偏题、过泛或不适合当前商业仿真的资料。
- 模型计算知识包：`4,405` 条，`13` 个模型层，作为仿真、校准、收益、不确定性和 LLM 约束修改前的可调用入口。

## 两条 Mega 的真实状态

### 仿真栈通用 Mega

验证文件：`40_quality_evidence/simulation_stack_mega_supplement_verification_20260609.json`

- 查询矩阵：`3,264` 条，其中近年优先 `3,240`，经典理论 `24`。
- 原始候选：`54,580` 条。
- 筛选入库：`5,821` 条。
- 并入后主筛选库曾推进到：`21,852` 条。
- 当前验证状态：`needs_action`。
- 未闭合原因：`classic_reference_total=0`，经典理论部分没有按预期入库；Crossref 存在 429 限流。

结论：它不是没跑，而是没有完全闭环。它已经贡献了大量通用仿真资料，但不能被说成“最高标准已完成”。

### 计算与模型 Mega

验证文件：`40_quality_evidence/computation_model_mega_supplement_verification_20260609.json`

- 查询矩阵：`5,440` 条，其中近年优先 `5,200`，经典理论 `240`。
- 原始候选：`54,333` 条。
- 筛选入库：`3,096` 条。
- 经典理论参考：`936` 条。
- 并入后主筛选库：`23,091` 条。
- 当前验证状态：`needs_action`。
- 未闭合原因：OpenAlex 当前预算为 0 或接口限流，本轮主要由 Crossref 贡献，不能算多源完全闭环。

结论：计算与模型 Mega 已完成一轮抓取、筛选、合并和模型包构建，但仍需要 OpenAlex/其他源恢复后补跑，才叫最高标准闭合。

## 必读文件

1. `40_quality_evidence/recent_knowledge_base_verification_20260609.json`
2. `40_quality_evidence/recent_knowledge_core_verification_20260609.json`
3. `40_quality_evidence/model_computation_knowledge_pack_verification_20260609.json`
4. `40_quality_evidence/simulation_stack_mega_supplement_verification_20260609.json`
5. `40_quality_evidence/computation_model_mega_supplement_verification_20260609.json`
6. `10_research/recent_knowledge_base_20260609/model_computation_stack_playbook_20260609.md`
7. `10_research/recent_knowledge_base_20260609/integrated_simulation_architecture_blueprint_20260609.md`
8. `10_research/recent_knowledge_base_20260609/curated_core_quality_report_20260609.md`
9. `10_research/recent_knowledge_base_20260609/knowledge_theme_playbooks_20260609.json`
10. `40_quality_evidence/model_computation_query_examples_20260609.json`
11. `40_quality_evidence/current_knowledge_base_integration_verification_20260609.json`

## 可调用入口

查询部署级核心库：

```powershell
py -3.12 30_extraction\scripts\query_recent_knowledge_base_20260609.py --query "ABM visitor flow Monte Carlo revenue" --limit 8
```

查询模型计算知识包：

```powershell
py -3.12 30_extraction\scripts\query_model_computation_knowledge_20260609.py --query "ABM pedestrian queue capacity visitor heatmap" --limit 5
py -3.12 30_extraction\scripts\query_model_computation_knowledge_20260609.py --query "Monte Carlo 收益 P95 天气 转化率" --limit 5
py -3.12 30_extraction\scripts\query_model_computation_knowledge_20260609.py --query "离散选择 目的地 消费 价格敏感" --limit 5
```

重建与合并：

```powershell
py -3.12 30_extraction\scripts\build_recent_knowledge_base_20260609.py
py -3.12 30_extraction\scripts\build_simulation_stack_supplement_20260609.py
py -3.12 30_extraction\scripts\build_computation_model_mega_supplement_20260609.py
py -3.12 30_extraction\scripts\curate_recent_knowledge_core_20260609.py
py -3.12 30_extraction\scripts\build_model_computation_knowledge_pack_20260609.py
```

如果 Mega 已抓取完，只需要复用现有原始数据：

```powershell
py -3.12 30_extraction\scripts\build_computation_model_mega_supplement_20260609.py --reuse-existing
py -3.12 30_extraction\scripts\curate_recent_knowledge_core_20260609.py
py -3.12 30_extraction\scripts\build_model_computation_knowledge_pack_20260609.py
```

## 使用规则

- 修改仿真架构、报告提示词、DeepSeek 约束、UI 报告生成、节点解释、收益预测前，必须先查询核心库或模型计算知识包。
- 老板三层示例只作为方向种子，不是最终架构。正式架构见 `integrated_simulation_architecture_blueprint_20260609.md`。
- DeepSeek 是低成本语义工人，不是总设计师；它只能做候选、解释、JSON 草案和异常兜底。
- 客户报告只写基于已有资料的判断、预测和调整；不能写训练资料、内部路径、API、调试日志或让客户补材料的措辞。
- 方法参考库可以启发模型结构，但不能直接支撑客户结论。
- 全量筛选库只能作为检索背景；部署级核心库和模型计算知识包才是修改前优先读取的入口。
- 经典理论只能做方法骨架和边界，不得绕过本项目证据链得出客户结论。

## 可扩充规则

新增主题时，先扩查询矩阵，再重跑构建、二次筛选和模型包。扩充必须满足：

- 保留 `query_matrix`、`raw`、`screened`、`classic_reference`、`verification` 五类产物。
- 至少记录来源、查询语句、年份、标题、DOI/URL、引用量或来源质量字段。
- 偏题领域必须降级或剔除，不能为了数量污染模型包。
- OpenAlex、Crossref、Semantic Scholar、arXiv 等来源至少要有一个可复跑失败记录；失败不能掩盖，必须写入验证 JSON。
- 生成后必须运行查询样例，确认知识包真的可被调用，而不是只堆文件。
- 当前查询样例证据：`40_quality_evidence/model_computation_query_examples_20260609.json`，结论是查询链路可用；ABM 命中强相关，Monte Carlo/离散选择部分命中只能作为方法参考，不能直接进入客户结论。

## 正式融合架构摘要

当前架构不是三层，而是 13 个可操作模型层：

1. 证据输入与数据治理
2. CAD/GIS/路径空间底座
3. 客群画像与合成人口
4. 活动链与目的地选择
5. 受约束 LLM Agent 决策
6. ABM/人群轨迹与热力图
7. 离散事件、排队与容量
8. 收益、客单价、转化率与业态组合
9. Monte Carlo、不确定性与敏感性
10. 贝叶斯/统计校准与模型验证
11. 设施选址与多目标优化
12. 可解释报告与审计
13. 运行观测、回归测试和风险门禁

老板给出的 Persona、Mesa/ABM、Monte Carlo 只分别进入其中的第 3、5/6、9 层，并且需要被本项目证据链和核心知识库扩展。

## 当前未闭合事项

- 仿真栈通用 Mega 的经典理论部分仍需补跑，不能再说已经最高标准闭合。
- 计算与模型 Mega 需要等 OpenAlex 预算/限流恢复后补跑多源抓取。
- `verify_project_implementation.py` 仍需要把新知识库入口、模型包和 Mega 状态纳入门禁，避免新会话只看到旧的 180 条状态。
- 后续进入仿真代码或客户报告前，要先用模型计算知识包查询，并把查询样例写入证据文件。
