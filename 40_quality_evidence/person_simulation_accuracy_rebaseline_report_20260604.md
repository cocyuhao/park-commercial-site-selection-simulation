# 人物仿真准确性重基线验证报告（2026-06-04）

## 1. 本轮目标

用户明确要求：人物仿真是主线，供需缺口和同事方案只能选择性吸收；DeepSeek 可以便宜地辅助生成草稿，但必须受约束；网页要让用户掌握增删改查和采用/弃用自主权。

## 2. 已生成产物

| 产物 | 用途 | 状态 |
|---|---|---|
| `10_research/person_simulation_accuracy_knowledge_base_20260604.md` | 人物仿真准确性知识库 | 已生成 |
| `10_research/poi_tgi_calculator_selective_absorption_20260604.md` | 同事 POI/TGI 仓库选择性吸收报告 | 已生成 |
| `60_model/schemas/person_simulation_control.schema.json` | 用户可编辑仿真对象 schema | 已生成并 JSON 解析通过 |
| `70_outputs/processed_tables/person_simulation_feature_derivatives_1000_20260604.csv` | 1000+ 衍生场景/变量覆盖池 | 已生成 1200 行 |
| `40_quality_evidence/deepseek_llm_runs_contract_inventory_20260604.json/csv` | 旧 DeepSeek 输出契约适配清单 | 已生成 |

## 3. 同事仓库只读吸收

来源：`https://github.com/Hiromitsu1207/POI_TGI_Calculator`

只读下载到临时目录，没有覆盖本地仓库。

可吸收：

- `gap_index = (demand - supply) / (abs(demand) + abs(supply))`
- observed supply / inferred supply 分层
- preference text -> TGI-like indicator
- tourist profile -> demand profile 的草稿思路
- operation suggestions 作为动作草稿

不吸收：

- 不复制 OpenAI agent 主系统。
- 不把 POI/TGI 计算器替代人物仿真。
- 不把 priority 或 gap score 当最终推荐。
- 不把 LLM 解析 PDF 的输出直接当事实。

## 4. 人物仿真准确性判断

准确性提升来自以下链条：

```text
资料状态
-> 人群状态
-> 行为程序
-> 时间/空间路线
-> 需求触发
-> 供给层
-> 选择概率
-> 运营动作
-> 收益参数
-> 真实校准
-> 用户控制
```

DeepSeek 只能参与草稿生成、语义整理、解释和报告润色，不能做最终判断。

## 5. 验证

- `60_model/schemas/person_simulation_control.schema.json` JSON 解析通过。
- `70_outputs/processed_tables/person_simulation_feature_derivatives_1000_20260604.csv` 行数：1200。
- `30_extraction/scripts/review_handoff_and_encoding_health.py`：`failures=0`。
- `30_extraction/scripts/verify_project_implementation.py`：`checks=725 failures=0`。
- `git diff --check`：无空白错误，仅 Windows CRLF 提示。

## 6. 下一步

1. 在 P6 dashboard 增加“人物仿真配置/假设管理”抽屉。
2. 把 `person_simulation_control.schema.json` 接入资料池、人群画像、行为程序、时间场景、空间节点、供给设施和校准目标。
3. 从 1200 行衍生场景中抽样生成 Selenium/单元测试。
4. 将旧 DeepSeek 输出适配为新 envelope 后再进入人物仿真主线。

