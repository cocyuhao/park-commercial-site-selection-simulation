# 仿真设计项目协作规则 (AGENTS.md)

> **适用范围**：本文件供所有 AI agent（Codex、Copilot、Claude 等）和人工协作者使用。
> 任何新会话或新 agent 接入均必须先完整阅读本文件，再开始执行。

---

## 零、Codex / Agent 快速接入（必读）

### 当前本地环境（Windows，优先遵循）

```powershell
cd "C:\Users\Yy199\Desktop\仿真设计"
py 60_model\scripts\verify_deepseek_api.py
py 30_extraction\scripts\verify_pdf_tables.py
```

### Linux 容器 / CI（仅在对应环境下使用）

```bash
# 首次接入时运行一次即可
bash setup.sh
source .venv/bin/activate
```

### 填写凭据

```bash
# .env 文件（setup.sh 已自动从 .env.example 复制）
# 手动填入真实 Key：
# DEEPSEEK_API_KEY=sk-xxxx
# AMAP_WEB_SERVICE_KEY=xxxx
```

### 健康验证（每次接入后先跑这两条）

```bash
python 60_model/scripts/verify_deepseek_api.py
python 30_extraction/scripts/verify_pdf_tables.py
```

### 核心可读文件清单

| 文件 | 说明 |
|------|------|
| `progress.md` | 当前进展和 TODO |
| `handoff_next_chat.md` | 上一个 agent 的交接记录 |
| `task_plan.md` | 完整任务计划 |
| `findings.md` | 关键发现和结论 |
| `00_control/decisions.md` | 架构决策记录 |
| `00_control/plugin_routing.md` | 插件路由规则 |
| `40_quality_evidence/evidence_ledger.csv` | 证据台账（52 条）|
| `30_extraction/tables/pdf_native_tables.jsonl` | 329 张 PDF 表格 |

### 你可以执行的任务类型

1. **读取和分析**：读取上面列出的文件，理解项目状态
2. **写代码**：按本文档约定编写 Python 脚本（见第五节、第十二节）
3. **运行脚本**：激活 `.venv` 后运行 `python <script>`
4. **更新文档**：更新 `progress.md`、`findings.md`、`handoff_next_chat.md`
5. **需要高能力主 agent / Codex 主导的任务**：见第十一节

---

## 一、默认语言

- 计划、进度、解释和最终答复默认使用**简体中文**。
- 代码、命令、字段名、路径、API 参数、错误文本保持**原文（英文）**。

---

## 二、项目定位

本目录是 **"公园商业选址仿真与经营决策系统"** 的长期工作区，不是一次性报告目录。
目标：基于客流数据、GIS、消费偏好和竞品分析，对目标公园的商业业态缺口和选址机会做定量评估，最终交付选址报告和决策建议。

---

## 三、启动顺序

每次开始非简单任务时，按顺序读取：

1. `progress.md`
2. `handoff_next_chat.md`
3. `task_plan.md`
4. `findings.md`
5. `00_control/decisions.md`
6. `00_control/plugin_routing.md`

---

## 四、当前项目阶段

| 阶段 | 状态 | 说明 |
|------|------|------|
| P0 项目初始化 | 完成 | 目录结构、规则、schema、脚本框架 |
| P1 样例资料拆解 | 已收口 | 证据台账、DeepSeek 草稿链路、P1 质量报告和 20260526 全量门禁已完成 |
| P2 方法原型 | 已闭环 | 已完成真实资料索引、DOCX/PDF 语义拆解、输入 schema 候选、DeepSeek 完成度审计和 persona/需求触发/评分公式/API 契约草案；全部仍为 `needs_review` 方法原型 |
| P3 真实公园校准 | 未开始 | 需闭合 DWG 几何、真实客流、转化率、收益/成本、运营授权等输入 |
| P4 缺口计算与仿真 | 未开始 | 完整 Agent/GIS 仿真、路径、压力测试和候选优化尚未开始 |
| P5 报告交付 | 未开始 | |

当前工作焦点：P2 方法原型收口后的 P3 前置缺口管理、真实资料转换/校准计划和可复跑交接维护；继续默认采用 DeepSeek-first 处理低/中风险草稿与批量整理，但真实校准、完整仿真建模、关键代码、最终门禁和结论仍由 Codex / 高能力主 agent 主导。

---

## 五、Python 运行环境

### 解释器

| 属性 | 值 |
|------|-----|
| 正确解释器 | `C:\\Users\\Yy199\\AppData\\Local\\Programs\\Python\\Python312\\python.exe` |
| Python 版本 | 3.12.2 (CPython, 官方安装) |
| 禁止使用 | 裸 `python`（映射 Anaconda 3.11.7） |
| 推荐写法 | `py` 启动器（已映射到 3.12）或完整路径 |
| 虚拟环境 | 无 .venv，直接用系统 Python 3.12 |

### 运行脚本的标准命令

```powershell
cd "C:\\Users\\Yy199\\Desktop\\仿真设计"
py script_path.py
```

### 已安装的核心包（Python 3.12）

| 包 | 版本 | 用途 |
|----|------|------|
| pdfplumber | 0.11.9 | PDF 表格抽取（第二引擎） |
| PyMuPDF (fitz) | 1.27.2.3 | PDF 原生表格（主引擎）、文本层 |
| openai | 2.38.0 | DeepSeek API（OpenAI 兼容接口） |
| pandas | 3.0.3 | 数据处理 |
| numpy | 2.4.6 | 数值计算 |
| httpx | 0.28.1 | HTTP 探测 |
| aiohttp | 3.13.5 | 异步 HTTP |
| tiktoken | 0.13.0 | token 计数 |
| shapely | 2.1.2 | 空间几何计算 |
| matplotlib | 3.10.9 | 图表 |
| scipy | 1.17.1 | 统计 |
| python-dotenv | 1.2.2 | .env 加载 |
| tabulate | 0.10.0 | 表格格式化输出 |
| openpyxl | 3.1.5 | Excel 读写 |
| python-pptx | 1.0.2 | PPT 文本抽取 |
| Pillow | 12.1.1 | 图像处理 |

安装缺失包：

```powershell
py -m pip install <package> -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 六、验证与测试命令

### API 健康验证

```powershell
cd "C:\\Users\\Yy199\\Desktop\\仿真设计"
py 60_model\\scripts\\verify_deepseek_api.py
# 输出: 40_quality_evidence/verify_deepseek_api_report.json
# 输出: 40_quality_evidence/postman_deepseek_collection.json
```

### PDF 表格质量验证

```powershell
py 30_extraction\\scripts\\verify_pdf_tables.py
# 输出: 40_quality_evidence/verify_pdf_tables_report.json
```

### DeepSeek 烟雾测试

```powershell
py 60_model\\scripts\\run_deepseek_smoke_test.py
# 输出: 60_model/llm_runs/deepseek_smoke_test_latest.json
```

### 高德 API 烟雾测试

```powershell
py 50_external_gis\\scripts\\run_amap_smoke_test.py
# 需要 AMAP_WEB_SERVICE_KEY 环境变量
```

---

## 七、环境变量与凭据配置

### .env 文件模板（项目根目录）

```dotenv
# DeepSeek API Key
DEEPSEEK_API_KEY=

# 高德 Web 服务 Key
AMAP_WEB_SERVICE_KEY=
```

### 安全规则（硬性约束）

- Key 只从环境变量或 `.env` 读取，不得硬编码在任何 .py、.csv、.json、.md 文件中。
- `.env` 已加入 `.gitignore`，禁止 commit。
- 日志中打印 Key 只允许显示前4后4掩码（如 `sk-b8...23ad`）。
- 脚本的 `load_local_env()` 函数自动处理 `.env` 加载（见 `60_model/src/llm_router.py`）。

---

## 八、核心数据文件 Schema

### 30_extraction/tables/pdf_native_tables.jsonl

每行一个 JSON 对象，共 329 张表：

```json
{
  "table_id": "TBL-00001",
  "source_file": "20_raw_data/pdf/xxx.pdf",
  "page": 1,
  "table_index": 1,
  "bbox": [x0, y0, x1, y1],
  "row_count": 11,
  "column_count": 6,
  "rows": [["cell", "cell"], ...]
}
```

### 40_quality_evidence/evidence_ledger.csv

| 字段 | 说明 |
|------|------|
| evidence_id | E-0001 起编 |
| indicator_name | 指标名称（中文） |
| value | 数值 |
| unit | 单位 |
| source_file | 来源文件相对路径 |
| page_or_slide | 页码或幻灯片号 |
| raw_text_snippet | 原文片段（≤200字） |
| extraction_method | 抽取方式 |
| confidence | high / medium / low / estimate |
| verification_status | checked / needs_review / conflict / draft |
| source_type | source_report_pdf / presentation_assumption / gis_api / model_estimate |

规则：DeepSeek 输出 verification_status 只能为 draft 或 needs_review，不得写入 checked。

### 60_model/llm_runs/deepseek_table_classification_raw.jsonl

```json
{
  "input_table_ids": ["TBL-00059", ...],
  "response_excerpt": "[{\"table_id\": \"TBL-00059\", \"topic_draft\": \"tgi_preference\", ...}]"
}
```

共 44 行，已处理 127 条非噪声分类。

---

## 九、脚本目录清单

### 30_extraction/scripts/

| 脚本 | 功能 |
|------|------|
| extract_pdf_native_tables.py | PyMuPDF 抽取 PDF 原生表格 → pdf_native_tables.jsonl |
| build_first_evidence_ledger.py | 从 JSONL+CSV 生成第一批证据台账 |
| build_poi_supply_base.py | 从 PDF 热门到访表生成供给种子底表 |
| review_poi_supply_base.py | 复查供给底表和高德查询计划 |
| review_p0_field_verification_checklist.py | 本地审计 34 条待核验清单，识别可本地确认的结构问题和仍需现场/官方核验的事项 |
| review_ppt_assumptions.py | PPT 假设事实回查 |
| verify_pdf_tables.py | PDF 表格质量 4 方法综合验证 |

### 50_external_gis/scripts/

| 脚本 | 功能 |
|------|------|
| fetch_amap_poi.py | 高德 POI 搜索 API 批量抓取 |
| fetch_amap_p0_routes.py | P0 候选的步行路径验证 |
| fetch_osm_park_boundaries.py | OSM Nominatim 获取公园 polygon |
| build_amap_boundary_filter.py | 基于高德/OSM 边界过滤候选 |
| build_amap_spatial_precheck.py | 空间预过滤（不替代实地核验） |
| build_amap_supply_candidates.py | 生成高德供给候选表 |
| build_in_park_candidate_review.py | 园内候选复核 |
| build_p0_in_park_followup_worklist.py | P0 候选待核验任务清单 |
| rebuild_amap_poi_clean_from_raw.py | 从原始高德数据重建清洗表 |
| review_amap_poi_fetch.py | 高德抓取质量复查 |
| run_amap_smoke_test.py | 高德 API 烟雾测试 |

### 60_model/scripts/

| 脚本 | 功能 |
|------|------|
| run_deepseek_smoke_test.py | DeepSeek API 基础烟雾测试 |
| run_deepseek_table_classification.py | 批量表格主题分类（draft 输出） |
| review_deepseek_table_classification.py | 分类结果复查 |
| verify_deepseek_api.py | DeepSeek API 4 方法综合验证 + Postman 集合 |

### 60_model/src/

| 文件 | 导出函数 |
|------|------|
| llm_router.py | deepseek_client(), load_local_env(), route_for(), run_deepseek_task(), load_routes() |

---

## 十、模型与 API 约定

### DeepSeek API

- Base URL: `https://api.deepseek.com`
- 使用 OpenAI SDK，设置 `base_url="https://api.deepseek.com"`
- 可用模型：`deepseek-v4-pro`（默认），`deepseek-v4-flash`（可选低风险）
- 所有 DeepSeek 输出字段中必须含 `output_status: "draft"` 或 `"needs_review"`

### ALLOWED_TOPICS（表格分类主题集合）

```python
{"visitor_flow", "time_peak", "demographic_profile", "origin_residence_work",
 "tgi_preference", "poi_hot_visit", "consumption_spending", "commercial_supply",
 "revenue_finance", "supply_gap", "empty_or_visual_noise", "other"}
```

### 高德 API

- Key 变量名：`AMAP_WEB_SERVICE_KEY`
- 坐标系：高德使用 GCJ-02，OSM 使用 WGS84，转换时记录误差
- 每次请求记录：API 名称、时间戳、参数摘要、状态码、结果条数

---

## 十一、高能力主 agent / Codex 专属职责

以下任务必须由高能力主 agent / Codex 执行，不得仅靠 DeepSeek 或本地脚本：

| 任务 | 原因 |
|------|------|
| evidence_ledger.csv 正式入账（checked 行）复核 | 需要判断数字真实性和单位一致性 |
| PPT 假设的最终事实回查 | 需要跨文件推理，不能靠关键词 |
| P2 是否启动，以及 P2-P5 的建模/仿真主线推进 | 这是阶段方向决策，必须由用户确认后再由高能力主 agent 主导 |
| 供需缺口计算逻辑审查 | 直接影响最终商业结论 |
| 最终报告结论段落 | 必须证据 ID 完整、无幻觉 |
| 安全扫描（Key 泄露、敏感信息） | 不可信任低能力模型自我审查 |
| 高风险代码合并前审查 | 涉及数据完整性和可复跑性 |
| decisions.md 新决策登记 | 需要项目全局视角 |

---

## 十二、代码风格约定

- Python 3.12，`from __future__ import annotations`
- 路径使用 `pathlib.Path`，`ROOT = Path(__file__).resolve().parents[N]`
- JSON 输出：`ensure_ascii=False, indent=2`
- JSONL 输出：每行 `json.dumps(..., ensure_ascii=False) + "\n"`
- CSV 输出：`encoding="utf-8-sig"`（Windows Excel 兼容）
- 不在生产脚本中打印 Key 完整值，只打印掩码
- 脚本顶部添加 `ROOT` 路径常量，禁止 `os.chdir()`

---

## 十三、真实性规则

- 每个关键数字必须能追溯到 `40_quality_evidence/evidence_ledger.csv`。
- PPT 默认是方案假设或表达材料，不能直接当强证据。
- PDF、用户提供的原始经营数据、高德 POI/路径数据、官方公开资料可作为较强证据，但仍要记录来源和置信度。
- 真实数据、模型估算、人工假设必须分开标注。
- 没有证据链的结论不能进入最终报告。
- DeepSeek 输出只作 draft，进入 checked 前必须 Codex 或本地脚本复核。

---

## 十四、工具和凭据

- 本地 Python 是主工作流，负责抽取、清洗、建模、仿真和输出。
- 高德 Web 服务 Key 只允许放在环境变量或 `.env`，禁止写入代码、报告、日志和最终材料。
- 不要为了显得复杂而堆插件；插件必须服务于数据真实性、建模质量、可视化验证或交付。

---

## 十五、交接要求

每轮有实质进展后，必须更新：

- `progress.md`
- `findings.md`
- `handoff_next_chat.md`
- `next_chat_prompt.md`

重要方法选择或工具选择写入 `00_control/decisions.md`。

---

## 十六、输出目录约定

| 目录 | 内容 |
|------|------|
| `20_raw_data/` | 原始文件（PDF、PPT、图片、Excel） |
| `30_extraction/` | 抽取中间结果（JSONL、文本、表格） |
| `40_quality_evidence/` | 证据链、质量报告、验证报告 |
| `50_external_gis/` | 高德、OSM、空间数据（原始 + 清洗） |
| `60_model/` | 模型代码、配置、LLM 运行记录 |
| `70_outputs/` | 分析结果（处理后表格、图、地图） |
| `80_delivery/` | 最终报告、PPT、答辩材料 |
| `90_archive/` | 废弃版本存档 |
