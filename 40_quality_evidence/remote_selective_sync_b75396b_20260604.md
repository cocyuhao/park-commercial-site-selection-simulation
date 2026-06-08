# 2026-06-04 GitHub main 选择性同步报告

## 1. 远端状态

- 仓库：`cocyuhao/park-commercial-site-selection-simulation`
- 远端 main：`b75396b66c5988ba3640b8060660a8f2b7d7cdb8`
- 提交信息：`Stabilize dashboard workflow gates`
- 提交时间：`2026-06-03T09:33:13Z`
- 本地基线：`4e5cb7b8712572211e74f0296e29fac44a947372`

本轮没有执行全量覆盖、`git reset` 或强制同步。先下载远端源码包到临时目录，只读比较后再选择性吸收。

## 2. 只读比较结论

比较报告：`40_quality_evidence/remote_main_readonly_diff_b75396b_20260604.json`

- 远端文件数：548
- 本地工作区文件数：729
- 远端相对本地 HEAD 改动文件：29
- 本地相对本地 HEAD 改动文件：370
- 双方重叠改动文件：29
- 远端新增、本地不存在文件：0

这说明远端本次不是新增一批独立模块，而是在 AI 工作台、地图、节点、门禁和交接文件上与本地大量重叠。若直接镜像同步，会覆盖掉本地已经补过的 AI 工作台、人类化报告、地图兜底、节点优先级解析和 725 项门禁修正。

## 3. 本轮吸收的远端思路

### 3.1 资料用途归一化

吸收远端“上传资料分类更稳定”的方向，并在本地改成更适合业务人员理解的文案：

- `项目计划`
- `地图/CAD/平面图`
- `客流/TGI`
- `POI/竞品`
- `经营收益/成本`
- `现场照片/截图`
- `其他`

同时兼容旧文案，例如 `方案文件`、`CAD / 图纸`、`现场图片 / 位置图`、`客流数据`。

### 3.2 节点草案去重

吸收远端“从项目计划生成节点后不要反复堆重复草案”的方向。现在 `node_drafts.json` 读写都会按 `node_id / node_name / location_description / business_direction` 形成稳定 key 去重，避免用户多次点击后节点清单变脏。

### 3.3 报告按钮状态联动

吸收远端“生成报告按钮应随当前会话和 AI 忙闲状态变化”的方向。现在前端会在切换会话、新建对话、发送消息和渲染上下文时统一刷新按钮状态。

## 4. 明确保留本地胜出的部分

### 4.1 不回退地图兜底

保留本地 `prepareStaticBasemap`、`showStaticBasemapBehindAmap`、`fallback-tiles` 等逻辑。远端版本缺少这部分，如果覆盖会增加“地图一片空白”的风险。

### 4.2 不回退节点解析

保留本地 `score_recommendations`、`score_breakdown` 和前端 `renderScoreAnalysis`。用户已经指出“分数意义不详，建议更重要”，本地版本已经把分数改成“讨论优先级 + 具体补证建议”，不应退回只有问题提示的版本。

### 4.3 不回退报告文案

保留本地 `humanize_report_text` 和报告生成反馈。远端会把 `report_path` 作为主要 UI 文案暴露给用户，本地改为“报告已生成，可查看/下载”，更符合客服端产品。

### 4.4 不回退门禁基线

保留本地 47 行 handoff encoding health 和 `checks=725 failures=0` 当前门禁。远端仍停留在较旧的 43 行口径，覆盖会让已修正的门禁倒退。

## 5. 修改文件

- `90_p6_expert_dashboard/app.py`
  - 新增上传用途归一化。
  - 新增节点草案去重。
  - 保存上传索引和节点草案时统一清洗。
- `90_p6_expert_dashboard/static/app.js`
  - 新增报告按钮状态刷新函数。
  - 新建会话、切换上下文、发送消息时同步更新报告按钮。

## 6. 验证结果

| 验证项 | 结果 | 证据 |
|---|---:|---|
| JS 语法 | 通过 | `node --check 90_p6_expert_dashboard/static/app.js` |
| Python 编译 | 通过 | `py -3.12 -m py_compile 90_p6_expert_dashboard/app.py ...` |
| API 逻辑烟雾 | 通过 | 上传归一化 3 条样例、节点草案 3 条去重为 2 条、`/api/dashboard` TestClient 200 |
| 本地服务 | 通过 | `http://127.0.0.1:8000`，`httpx trust_env=False` 返回首页 200、dashboard 200 |
| handoff 编码门禁 | 通过 | `failures=0` |
| 项目总门禁 | 通过 | `checks=725 failures=0` |
| PDF 表格门禁 | 通过 | `PASS=4 FAIL=0` |
| Selenium 10 轮 | 通过 | `40_quality_evidence/selenium_visual_integration_20260603/selenium_visual_integration_20260603.json`，`round_count=10 failure_count=0` |
| 人眼截图复核 | 通过 | `40_quality_evidence/remote_selective_sync_b75396b_browser_checks_20260604/overview.png`、`ai_workspace.png` |

补充说明：普通 `httpx` 曾因环境代理返回 `502`，使用 `trust_env=False` 后确认本地服务正常。这是本机 HTTP 客户端环境差异，不是网页服务失败。

## 7. 当前判断

同事这次远端提交对“流程稳定”和“状态联动”有价值，但不能全量覆盖本地。正确做法是吸收低冲突的资料归一化、节点草案去重和报告按钮状态联动，同时保留本地已经被用户反复要求并验证过的 AI 工作台、报告语言、地图兜底、节点优先级解析和最新门禁。

本轮未推送 GitHub。若后续需要推送，应先复查工作区待提交文件，排除 `.env`、运行缓存、临时截图和无关 QA 产物。
