# 先进 AI 产品验证体系重基线（2026-06-04）

> 状态：验证方法重基线。  
> 目的：回应“检查方法也很旧，导致用户发现的问题测试看不出来”。  
> 结论：旧 Selenium / 静态门禁 / 截图 smoke test 只能作为底层检查，不能再作为“人类可用、AI 可信、仿真逻辑正确”的充分证据。

## 1. 旧检查为什么不够

过去的检查偏向：

- 页面能打开。
- 按钮能点击。
- 截图不空白。
- console 没错误。
- 字段存在。
- 总门禁行数通过。

这些能发现白屏、语法、接口和基础交互错误，但发现不了：

- 业务逻辑矛盾。
- AI 输出看起来有道理但范围错误。
- 用户能点完但不知道为什么。
- 旧文件被新 UI 包装成新结论。
- 报告像 AI 日志。
- 按钮诱导用户一键生成/采用/删除。
- AI 工作台缺少检查点。
- 页面不具备 agent 可读结构，自动化测试只能粗暴点。
- 地图/资料/节点/AI 之间的状态串联断裂。

因此验证必须升级为“AI 产品 / agentic workflow / 人机协作”验证。

## 2. 新验证体系

### 2.1 五层验证

| 层级 | 检查什么 | 工具 |
|---|---|---|
| 结构层 | schema、对象 ID、状态字段、用户可控动作、旧产物信任标签 | Python、jsonschema、pydantic、静态扫描 |
| API 层 | CRUD、锁定不可删、报告生成条件、错误不清空 | httpx / FastAPI TestClient / Selenium API 脚本 |
| 浏览器层 | DOM、ARIA snapshot、焦点、可见文本、布局尺寸、console、trace | Playwright 1.60、Chrome、Selenium 4.44 |
| agentic 层 | 检查点、动作后果、可回退、用户监督、危险动作、agent 可读 selector | Playwright trace、ARIA snapshot、data-action/data-object-id 扫描 |
| AI/报告层 | 范围是否正确、是否引用对象、是否有反例/缺口、是否把草稿当结论 | LLM-as-draft + 本地规则 + 人工复核 |

### 2.2 新增必查项

1. agent 可读性。
   - 关键对象必须有稳定 ID。
   - 关键动作必须有 `id`、`data-view`、`data-action`、`data-object-id` 或同等级 hook。
   - 不能只靠按钮文字和视觉位置。

2. 监督检查点。
   - 资料解析、仿真任务、报告生成、删除、覆盖、采用、锁定必须有中间状态或明确后果。
   - 多步 AI 任务不能一键到底。

3. AI 风险语言。
   - UI 不得出现 `raw`、`payload`、`debug`、`traceback`、`needs_review`、`not_final`、`external_preview_only` 等内部词。
   - AI 输出必须能表达“当前能判断 / 不能判断 / 需补资料 / 待复核 / 下一步动作”。

4. 可反驳解释。
   - 节点和报告不能只给结论。
   - 必须包含依据、缺口、反例或禁止判断。

5. 视觉可用性。
   - 不只看截图是否存在，还要检查文本密度、输入框/输出框尺寸、可见区域是否过挤、按钮层级是否诱导。

6. 旧产物污染。
   - 检查页面和报告是否出现旧 P4、旧 ROI、旧最终排名、旧裸分数和旧端口。
   - 检查旧 `needs_review` 是否被映射为业务可读文案，而不是直接暴露。

7. Trace 证据。
   - 重要验证不再只留一张截图。
   - 必须保留 action trace、ARIA snapshot、console/pageerror、截图和结构化 JSON。

## 3. 新工具栈

| 工具 | 用法 | 为什么引入 |
|---|---|---|
| Playwright 1.60 | 多页面 trace、ARIA snapshot、浏览器状态和截图 | 比旧 Selenium smoke test 更适合记录可复查浏览器轨迹 |
| Selenium 4.44 | 保留旧回归和用户要求的反复点击 | 已安装且可用，适合继续做兼容性与历史 10 轮 |
| OpenTelemetry SDK 1.42 | 后续记录 AI/仿真任务 trace 和 span | 让 AI/工具/仿真链路可观察，而不是只看最终结果 |
| Python 3.12 | API、schema、报告、数据检查 | 项目主工作流 |
| Browser/Chrome DevTools | 人眼和真实浏览器检查 | 重要 UI 改动必须看真实页面 |

## 4. 当前新增验证脚本

新增：

- `90_p6_expert_dashboard/qa/advanced_agentic_workflow_validation_20260604.py`

输出：

- `40_quality_evidence/advanced_agentic_workflow_validation_20260604.json`
- `40_quality_evidence/advanced_agentic_workflow_validation_20260604.md`
- `40_quality_evidence/advanced_agentic_workflow_trace_20260604.zip`
- `40_quality_evidence/advanced_agentic_workflow_aria_overview_20260604.yml`
- 多张页面截图

这个脚本的目标不是“把所有问题压成 0”，而是用更先进的方法把以前看不见的问题抓出来，避免再把旧 smoke test 当完成证据。

## 5. 对后续开发的硬要求

- 改 UI 后必须跑基础语法、总门禁和至少一个浏览器高级审计。
- 重大 AI 工作台改动必须保留 trace zip。
- 如果高级审计输出 `needs_work`，不代表代码坏了，但必须把发现写进下一步。
- 只有当结构层、API 层、浏览器层、agentic 层和 AI/报告层都能解释清楚，才允许说“这轮验证充分”。

## 6. 参考方向

- Playwright `aria_snapshot` 和 trace viewer：用于结构化浏览器证据。
- Selenium 4 BiDi / WebDriver：用于现有 Selenium 兼容与浏览器自动化。
- OpenTelemetry GenAI / trace 思路：用于未来记录 AI、工具和仿真任务链路。
- CHI 2026 GUI agent / user oversight / dark pattern 论文：用于检查用户监督、危险动作和诱导设计。
- IUI/AAAI/npj AI 2026 LLM-driven simulation / self-corrective simulation 论文：用于检查仿真任务是否只是文本输出，还是有可复核对象链。
