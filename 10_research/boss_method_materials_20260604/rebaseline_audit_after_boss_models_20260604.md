# 老板模型全盘吸收后的阶段可信度重估（2026-06-04）

> 状态：重估报告。  
> 目的：老板资料改变了仿真目标的尺度和方法要求，因此旧的“已完成”不能直接沿用。  
> 结论：当前仓库很多成果仍有价值，但需要重新分级；“可展示/可交互/可干跑”不等于“仿真完成”。

## 1. 为什么必须重估

老板六份资料带来的变化不是小补丁，而是上层方法变化：

- 要从“POI/TGI 缺口 + 页面展示”升级为“人群状态 + 行为程序 + 空间运动 + 消费选择 + 真实校准 + 报告解释”。
- DeepSeek 只能做候选/解释/语义批处理，不能做主仿真。
- 节点评价不能靠神秘分数，必须解释行为、建议和补证动作。
- 完整仿真必须有真实几何、客流、转化、收益/成本、运营授权和验证指标。

因此旧文件要按新标准重新看：

- 已完成语法/接口/页面，不等于已完成方法。
- 已完成 DeepSeek 草稿，不等于已完成模型。
- 已完成 dry-run，不等于已完成 P4 仿真。
- 已完成 Selenium，不等于已完成人类行为仿真验证。

## 2. 当前可信分级

| 分级 | 含义 | 可继续使用方式 |
|---|---|---|
| A 仍可信 | 原始证据、checked 数据、可复跑脚本、明确 dry-run 边界 | 可作为底座 |
| B 可信但需改口径 | 页面、接口、P6 工作台、报告生成、Selenium 证据 | 可作为产品壳和验证证据，但不能证明仿真完成 |
| C 仅草稿候选 | DeepSeek 输出、P2/P3/P4 草稿表、评分/优先级原型 | 只能作为待复核输入 |
| D 需降级或重写 | 旧 P4 完成声明、裸 ROI/排名/神秘分数 | 不得作为当前事实 |
| E 新方向待补 | 人群状态模型、行为程序库、空间运动模型、消费选择模型、宏观验证 | 后续需要重新设计 |

## 3. 旧文件/模块重估

### A 仍可信

| 文件/模块 | 当前判断 | 原因 |
|---|---|---|
| `40_quality_evidence/evidence_ledger.csv` | 仍可信，但只信 `checked` 行 | 证据链仍是底座 |
| `30_extraction/tables/pdf_native_tables.jsonl` | 仍可信 | PDF 表格抽取底稿，不是模型结论 |
| 高德/OSM POI 与边界候选表 | 仍可信为候选 | 已明确非最终园内供给 |
| `30_extraction/scripts/verify_project_implementation.py` | 仍可信为门禁脚本 | 但需扩展新方法门禁 |
| `.env` 读取和 key 不落盘规则 | 仍可信 | 安全边界不变 |

### B 可信但需改口径

| 文件/模块 | 当前判断 | 需要修正 |
|---|---|---|
| `90_p6_expert_dashboard/` | 可作为专家工作台原型 | 不能包装成完整仿真系统 |
| AI 工作台/报告生成 | 可作为沟通和草稿整理工具 | 需要接入状态/行为/资料引用，不只是聊天 |
| Selenium 10 轮/截图证据 | 可作为产品交互验证 | 不能当作行为仿真准确性验证 |
| 地图静态兜底 | 可作为不空白的产品兜底 | 不能替代真实高德 JS 交互和空间仿真 |
| 节点优先级解释 | 方向正确 | 需要从“分数扣分”升级为“行为-建议-补证”解释 |

### C 仅草稿候选

| 文件/模块 | 当前判断 | 用法 |
|---|---|---|
| `70_outputs/processed_tables/p2_persona_parameter_prototype.csv` | 老方法 persona 原型 | 可参考，不足以支撑 HumanLM 状态层 |
| `p2_persona_state_profiles_20260604.csv` | 新增草稿 | 待审，不能视为完成 |
| `p2_behavior_program_templates_20260604.csv` | 新增草稿 | 待审，需与 ROTE/FSM/schema 对齐 |
| `p2_simulation_validation_targets_20260604.csv` | 新增草稿 | 待审，需扩展 SARIMA/SSIM/KL/DTW 等 |
| 所有 `*_deepseek.csv/json/md` | DeepSeek 草稿 | 只能作为候选和整理，不是事实 |
| `p4_feedback_*_deepseek.csv` | 反馈草案 | 可用于讨论，不可当 P4 完整仿真 |

### D 需降级或重写

| 文件/模块 | 问题 | 处理 |
|---|---|---|
| `findings.md` 中 2026-05-28 “P4完整仿真完成事实”章节 | 与后续 rollback 和老板资料方法冲突 | 必须以后续 rollback 和本轮重估为准，后续可改标题为“已判定不可信的历史 P4 声明” |
| `progress.md` 中 “P4完整仿真已完成”历史段落 | 会误导新 agent | 必须在文件顶部持续纠偏 |
| 任何 ROI、最终排序、最终推荐表达 | P3 未闭合，且新方法要求更高 | 禁止主流程使用 |
| 裸 `discussion_score` 作为主视觉 | 用户已明确指出意义不详 | 只能折叠成辅助解释或逐步替换为优先级 |

### E 新方向待补

| 新模块 | 来源 | 为什么必须补 |
|---|---|---|
| `persona_state_schema` | HumanLM | 不再接受浅 persona |
| `behavior_program_schema` | ROTE/FSM | 不再接受 LLM 临场编故事 |
| `choice_probability_schema` | SSR/logit/Huff | 不再接受直接打分 |
| `spatial_movement_gate` | Social Force/RVO/MATSim | 地图不等于空间仿真 |
| `macro_validation_plan` | 社区仿真 SARIMA/SSIM/KL/DTW | 没有校准就没有完整仿真 |
| `deepseek_task_contracts` | DeepSeek 低智能约束 | 每个低成本任务都要本地验证 |

## 4. 对阶段状态的重新判断

| 阶段 | 旧口径 | 新重估 |
|---|---|---|
| P1 证据链 | 基本可信 | 仍可信，但要继续区分 checked / needs_review |
| P2 方法原型 | 曾认为闭环 | 只能说旧方法原型闭环；在老板模型标准下需要扩展重开 |
| P3 校准 | 等真实来源 | 仍未闭合，且重要性上升 |
| P4 仿真 | 历史上曾误称完成，后 rollback | 当前未完成；只能有 feedback draft / dry-run |
| P6 工作台 | 可用原型 | 可保留为产品壳，但需要接入新模型链路 |

## 5. 新门禁建议

后续 `verify_project_implementation.py` 应新增检查：

- 不允许当前文件出现未被纠偏的“P4 完整仿真已完成”作为当前事实。
- 新增模型资料必须出现在 `10_research/boss_method_materials_20260604/` 的方法报告中。
- `persona_state_schema`、`behavior_program_schema`、`validation_target_schema` 完成前，不得声明人物仿真完成。
- DeepSeek 输出不得生成 `final_ranking`、`roi_forecast`、`checked_evidence`、`simulation_complete`。
- 节点主页面不得把分数作为最高层判断。

## 6. 当前最重要的工作顺序

1. 先更新 durable 交接文件，保护新方向。
2. 再完成 DeepSeek 受限任务契约。
3. 再审查并改写旧 P2/P4 评分和仿真原型。
4. 最后才继续 UI 或代码实现。

## 7. 一句话结论

老板资料让项目从“能跑的专家驾驶舱原型”升级为“要能解释人的状态、行为、空间、消费和校准的仿真系统”。所以旧成果不是全部作废，但必须重新分级：能作为底座的留下，能作为草稿的标草稿，误称完成的降级，缺失的新模型链路要重做。
