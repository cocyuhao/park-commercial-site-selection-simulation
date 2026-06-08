# DeepSeek 受限任务契约（2026-06-04）

> 状态：工程契约草案。  
> 目的：把“DeepSeek 便宜但不够稳”的判断落成可执行边界。  
> 适用范围：资料整理、画像状态草稿、行为程序草稿、节点解释草稿、报告语言草稿。  
> 禁止范围：checked 证据、最终仿真、最终排序、ROI、最终商业推荐。

## 1. 总原则

DeepSeek 在本项目中不是总设计师，而是低成本语义工人。它可以扩大整理速度，但每一次输出都必须经过本地 schema、规则校验、证据引用检查和人工/Codex 复核。

老板六份资料给出的共同约束是：不要让 LLM 直接替代真实校准。ROTE 提醒我们行为必须是可解释程序；HumanLM 提醒我们要对齐人的内部状态；SSR 提醒我们不要直接打 Likert 分；RL+LLM 社区仿真提醒我们微观行为和宏观统计都要验证。因此 DeepSeek 只能站在这些方法链条中的草稿层。

官方依据：DeepSeek 当前 API 兼容 OpenAI/Anthropic 调用格式，`base_url` 为 `https://api.deepseek.com`，模型示例包含 `deepseek-v4-pro` / `deepseek-v4-flash`；官方 JSON Output 文档要求设置 `response_format={"type":"json_object"}`、在 prompt 中包含 json 和示例，并提示 JSON Output 仍可能偶发空内容。因此本项目不能只相信“开了 JSON 模式”，必须继续保留本地校验和失败降级。

参考：

- `https://api-docs.deepseek.com/`
- `https://api-docs.deepseek.com/guides/json_mode/`

## 2. DeepSeek 可以做的任务

| 任务 | 输入 | 输出 | 状态 | 复核方式 |
|---|---|---|---|---|
| 资料摘要 | PDF/DOCX 表格、段落、文件名、页码 | 结构化摘要、疑似指标、证据候选 | `draft` | 本地脚本回查页码、字段、单位 |
| 证据候选抽取 | 原文片段、表格行、上下文 | `evidence_candidate[]` | `needs_review` | Codex/人工决定是否入账 checked |
| 画像状态草稿 | 项目人群、TGI、客流、场景描述 | `persona_state_draft[]` | `draft` | schema 校验 + 与真实数据一致性检查 |
| 行为程序草稿 | 画像状态、空间节点、时间段、限制条件 | `behavior_program_draft[]` | `draft` | 本地规则检查，不可直接运行成最终仿真 |
| 节点解释草稿 | 节点属性、POI、边界、资料缺口 | 理由、建议、补证动作、优先级 | `needs_review` | 前端只显示人话，不显示模型字段 |
| 报告语言草稿 | 已复核事实、对话摘要、缺口清单 | 商业工作稿段落 | `needs_review` | 禁止新增无来源结论 |
| 微观合理性草评 | 某个行为序列、状态、约束 | 合理/可疑/不合理与原因 | `draft` | 只能辅助 ROTE/HumanLM/RL 规则，不是最终裁判 |

## 3. DeepSeek 禁止做的任务

- 不得生成 `checked` 证据。
- 不得决定最终节点排名。
- 不得给出最终 ROI、投资回收期、收益预测。
- 不得声称“完整仿真已完成”。
- 不得把 P3 未闭合的数据缺口用想象补齐。
- 不得直接给用户展示裸分数或神秘综合分。
- 不得把模型输出当成真实客流、真实消费或真实路径。
- 不得把奥森/绿心资料硬套到青年湖、公园外部地点或其他项目。
- 不得把 `raw json`、`payload`、`debug`、`traceback`、`needs_review` 等内部词裸露给客户界面。

## 4. 标准输出 envelope

所有 DeepSeek 输出必须套一层 envelope，便于本地校验和降级。

```json
{
  "task_id": "string",
  "task_type": "source_summary | evidence_candidate | persona_state | behavior_program | node_explanation | report_draft | micro_reasonableness",
  "output_status": "draft",
  "source_refs": [
    {
      "source_file": "string",
      "page_or_slide": "string",
      "evidence_id": "optional string",
      "quote_or_table_ref": "string"
    }
  ],
  "assumptions": ["string"],
  "uncertainties": ["string"],
  "needs_human_review": true,
  "items": []
}
```

规则：

- `output_status` 只能是 `draft` 或 `needs_review`。
- `source_refs` 不能为空；没有来源只能进入“待补资料”。
- `assumptions` 必须显式列出，不能藏在正文里。
- `items` 必须由任务 schema 决定，不能自由发挥。
- JSON 解析失败、字段缺失、状态越权时直接降级为失败，不进入页面主结论。

## 5. 画像状态 schema

来源：HumanLM 的 state alignment 思路，但不训练模型，只学习状态结构。

```json
{
  "persona_id": "PERS-DRAFT-001",
  "segment_name": "string",
  "state_status": "draft",
  "purpose": ["散步", "亲子", "通勤绕行", "约会", "运动", "游客"],
  "time_pressure": "low | medium | high | unknown",
  "budget_sensitivity": "low | medium | high | unknown",
  "fatigue_level": "low | medium | high | unknown",
  "companion_context": "alone | couple | family | friends | group | unknown",
  "detour_tolerance": "low | medium | high | unknown",
  "queue_tolerance": "low | medium | high | unknown",
  "risk_notes": ["string"],
  "evidence_refs": ["E-0001"],
  "missing_inputs": ["string"]
}
```

禁用：

- 不允许只有“年轻白领/亲子家庭”这种浅画像。
- 不允许无证据地填满所有状态。
- 不允许把画像状态直接转成消费金额。

## 6. 行为程序 schema

来源：ROTE 的“把他人心理建模成代码/程序”的思想。本项目不直接训练 ROTE，而是把行为写成可审查程序。

```json
{
  "program_id": "BHV-DRAFT-001",
  "persona_id": "PERS-DRAFT-001",
  "trigger_context": {
    "time_window": "string",
    "weather": "unknown | hot | cold | rain | comfortable",
    "crowd_level": "unknown | low | medium | high",
    "location_state": "entry | path | lakefront | activity_node | exit | unknown"
  },
  "state_preconditions": ["string"],
  "candidate_actions": [
    {
      "action": "approach | pass_by | purchase | rest | detour | leave | compare",
      "condition": "string",
      "expected_signal": "string",
      "failure_condition": "string"
    }
  ],
  "transition_notes": ["string"],
  "source_refs": ["string"],
  "validation_needed": ["trajectory_data", "field_observation", "transaction_proxy"]
}
```

禁用：

- 不允许写“用户会喜欢所以购买”这种空泛因果。
- 不允许把行为程序直接当真实路径。
- 不允许无空间约束、无时间约束、无失败条件。

## 7. 节点解释 schema

来源：SSR 反对直接打分；节点判断先输出自然语言理由，再映射推进动作。

```json
{
  "node_id": "N-006",
  "mode": "project | node",
  "priority_label": "优先推进 | 补资料后判断 | 仅空间观察 | 暂缓",
  "why_now": ["string"],
  "specific_advice": ["string"],
  "evidence_support": ["string"],
  "evidence_gaps": ["string"],
  "review_actions": ["string"],
  "score_if_any": {
    "value": null,
    "meaning": "仅解释讨论优先级，不代表最终排名",
    "hidden_by_default": true
  }
}
```

页面规则：

- 主视觉显示 `priority_label`、`specific_advice`、`evidence_gaps`、`review_actions`。
- 分数若存在，默认折叠。
- 不向客户显示 `draft`、`needs_review`、`schema`、`payload` 等词。

## 8. 报告草稿 schema

报告必须像业务工作稿，而不是 AI 日志。

```json
{
  "report_type": "project_brief | node_brief | evidence_gap_brief",
  "title": "string",
  "summary": ["现在能确认什么"],
  "key_basis": ["来自哪些资料"],
  "current_gaps": ["哪些数据不够"],
  "review_required": ["哪些只是草案"],
  "next_actions": ["下一步做什么"],
  "appendix_refs": ["对话记录或资料引用"]
}
```

语言规则：

- 少用“综上所述”“赋能”“闭环”等空泛表达。
- 不写模型自夸。
- 结论先写能确认的事，再写不能确认的事。
- 建议必须具体到“补什么资料/谁复核/复核后能解锁什么判断”。

## 9. 失败降级

| 失败类型 | 处理 |
|---|---|
| JSON 解析失败 | 丢弃主结论，只保留原始输出到调试日志，不进客户界面 |
| 缺少 `source_refs` | 降级为“待补资料”，不得显示为判断 |
| 出现 `checked/final/ranking/ROI` 等越权词 | 标记 contract violation |
| 输出裸分数但无解释 | 丢弃分数，只保留文本草稿待复核 |
| 把外部项目资料套用到当前项目 | 标记范围冲突，要求用户确认项目范围 |
| 与 evidence ledger 冲突 | 标记 conflict，不自动修正 |

## 10. 本地验证门禁

后续应补脚本：

- `60_model/scripts/validate_deepseek_contract_output.py`
- `60_model/schemas/deepseek_task_contract.schema.json`
- `60_model/schemas/persona_state.schema.json`
- `60_model/schemas/behavior_program.schema.json`
- `60_model/schemas/node_explanation.schema.json`

最低检查：

1. 字段完整。
2. 状态只允许 `draft/needs_review`。
3. 来源引用存在。
4. 禁止词未越权。
5. 不泄露 key。
6. 不把内部字段展示到前端。
7. 输出能被稳定 JSON 解析。

## 11. 对当前项目的立即影响

- 旧 DeepSeek 输出全部降级为草稿候选。
- 当前 `p2_persona_state_profiles_20260604.csv`、`p2_behavior_program_templates_20260604.csv`、`p2_simulation_validation_targets_20260604.csv` 只能作为 schema 原型候选。
- `60_model/simulation/persona_behavior.py` 不应继续扩写成主引擎，直到本契约和旧文件审计完成。
- P6 页面如果调用 DeepSeek，只能展示“AI 整理稿”和“待复核建议”，不能展示最终结论。
