# POI_TGI_Calculator 选择性吸收报告（2026-06-04）

> 来源：`https://github.com/Hiromitsu1207/POI_TGI_Calculator`  
> 获取方式：GitHub codeload ZIP 只读下载到临时目录。  
> 结论：可吸收供需缺口计算和 TGI/POI 分层思想；不能替代本项目人物仿真主线。

## 1. 仓库结构观察

临时路径：

`%TEMP%/poi_tgi_calculator_main/POI_TGI_Calculator-main`

主要模块：

- `app/calculators/gap_calculator.py`
- `app/calculators/supply_calculator.py`
- `app/calculators/service_demand_calculator.py`
- `app/calculators/spillover_calculator.py`
- `app/agents/tourist_agent.py`
- `app/agents/operator_agent.py`
- `app/services/analysis_orchestrator.py`
- `app/services/preference_indicator_service.py`
- `app/services/llm_report_parser.py`
- `app/services/openai_json_client.py`
- `tests/test_supply_gap_logic.py`

## 2. 可吸收点

### 2.1 标准化缺口指数

仓库使用：

```python
gap_index = (demand_score - supply_score) / (abs(demand_score) + abs(supply_score))
```

价值：

- 比裸 `demand - supply` 更适合跨业态比较。
- 能减少“大需求业态天然差值大”的误导。

本项目吸收方式：

- 可作为供需缺口辅助指标。
- 不作为最终排名。
- 页面默认不展示成“分数”，而展示为“缺口强度/优先级解释”。

### 2.2 observed supply 与 inferred supply 分离

仓库把真实 POI 供给和规则推断的服务设施供给分开。

价值：

- 避免把“系统觉得应该有厕所/饮水点”当成真实供给。
- 适合我们的资料真实性规则。

本项目吸收方式：

- 资料池和报告中明确显示：
  - 真实 POI 供给。
  - 推断设施供给。
  - 用户手动录入供给。
  - 待复核供给。

### 2.3 preference text -> indicator

仓库有 `PreferenceIndicatorService`，可以把用户自然语言偏好转成类似 TGI 指标。

价值：

- 符合用户要求：不要把界面写死，要让用户可以输入自己的判断。

本项目吸收方式：

- 作为“用户偏好资料”入口。
- 必须套 DeepSeek 受限契约。
- 输出状态只能是 `draft/needs_review`。
- 用户可以采用、修改、弃用。

### 2.4 tourist profile -> demand profile

仓库的 `TouristAgent` 先生成 TGI，再转需求。

价值：

- 可以作为需求层草稿。

本项目限制：

- 当前 tourist profile 太薄，主要是年龄、收入、出行目的、同行、停留时长。
- 我们必须扩展为 HumanLM 风格状态：目的、疲劳、预算、同行、绕行、排队、天气、时间压力。

### 2.5 operation suggestion

仓库能从 gap items 生成运营建议。

价值：

- 适合从“缺口”走向“动作”。

本项目限制：

- 必须接入时间层、空间层、行为程序和用户控制。
- 比如饮水机不能只因为“饮水缺口”就建议增设，还要看清晨/夜间、补货、容量、关闭时间、路线、设备运维。

## 3. 不可照搬点

| 问题 | 原因 | 本项目处理 |
|---|---|---|
| 把 LLM tourist TGI 当主仿真 | 人物状态太薄，容易生成漂亮但不准的需求 | 只作为需求草稿 |
| 把 P0/P1/P2 priority 当最终推荐 | 缺 P3 真实校准 | 页面改为推进优先级 |
| 直接用 OpenAI agent | 本项目当前用户希望接 DeepSeek，但 DeepSeek 不够稳 | 统一走 DeepSeek 契约 |
| PDF 解析后直接出结论 | 资料可信度和范围可能不一致 | 进入资料池待复核 |
| 只靠 POI 计算供给 | 公园内部设施、临时摊位、运营时间、容量都可能缺失 | 加用户 CRUD 和现场复核 |
| 只看业态缺口 | 用户真实目标是人物仿真驱动选址、收益、时间 | POI/TGI 只是其中一层 |

## 4. 与本项目主线的正确关系

```text
人物状态
  -> 行为程序
  -> 时间/空间路线
  -> 需求触发
  -> 业态/服务需求
  -> POI/TGI 供需缺口
  -> 运营动作/设施方案
  -> 收益/时间/补货/关闭策略
  -> 真实数据校准
```

同事仓库覆盖的是中间的：

```text
业态/服务需求 -> POI/TGI 供需缺口 -> 运营/空间建议草稿
```

它没有完整覆盖：

- 人物状态。
- 行为程序。
- 时段变化。
- 路线选择。
- 排队/容量。
- 收益校准。
- 用户可控假设管理。

## 5. 建议吸收为本地工程任务

新增/改造任务：

1. 把 `gap_index` 公式写入本地供需缺口说明，但标注为辅助指标。
2. 本地 `supply_profile` 拆成 `observed_supply / inferred_supply / user_supply / candidate_supply`。
3. 新增“用户偏好文本 -> 指标草稿”入口，输出必须走 DeepSeek contract。
4. 将 POI/TGI 缺口作为人物仿真的需求层，不作为人物仿真主线。
5. 把运营建议改成“时段 + 节点 + 人群状态 + 供给能力 + 补证动作”结构。

## 6. 当前不吸收代码

本轮不复制同事仓库代码到本地项目。

原因：

- 本地已有 P6 dashboard 和 DeepSeek 契约。
- 同事仓库依赖 OpenAI agent，不符合本轮 DeepSeek 受限路线。
- 直接复制会制造重复后端结构。
- 当前更需要吸收方法和公式，而不是替换系统。

