# 公园商业选址仿真项目

这是一个公园商业选址决策工具，用来整理证据、接入高德 POI/路径数据、管理待核验项，并为后续仿真和专家驾驶舱提供后端基础。

## 技术架构

- `90_p6_expert_dashboard/`：FastAPI 后端和本地网页驾驶舱。
- `60_model/db/`：SQLite 表结构和数据库读写层。
- `60_model/simulation/`：结构化仿真干跑骨架和结果校验。
- `60_model/simulation/demand_gap.py`：外部客流资料生成 TGI、当前高德 POI 生成供给画像，并计算供需缺口。
- `50_external_gis/`：高德和 OSM 数据抓取、清洗、边界过滤脚本。
- `70_outputs/processed_tables/`：已处理 CSV 数据。

## 本地运行

```powershell
py 60_model\scripts\import_existing_outputs.py
py -m uvicorn app:app --host 127.0.0.1 --port 8000 --app-dir 90_p6_expert_dashboard
```

访问：`http://127.0.0.1:8000`

## 常用验证

```powershell
py -m py_compile 60_model\db\store.py 60_model\simulation\engine.py 90_p6_expert_dashboard\app.py
py 50_external_gis\scripts\run_amap_smoke_test.py
```

## 双人 Codex 协作

团队分工见 `00_control/team_codex_division.md`。每轮开始先同步远端、确认工作泳道，再做本轮修改和验证。

推荐同步命令：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\00_control\sync_from_github_main.ps1
```

## 搜索记录

- 本轮未做外部方案搜索；改进直接基于项目现有 FastAPI、CSV/JSON 产物和员工A职责表落地。
- 2026-06-02 已查看 `https://github.com/Hiromitsu1207/POI_TGI_Calculator`：可参考其 TouristAgent、SupplyCalculator、GapCalculator 的“需求画像 + POI 供给 + 缺口指数”结构；本项目只采用结构思想，所有输出保持 `needs_review / not_final`。

## 已完成功能

- FastAPI 本地驾驶舱。
- 高德 POI、路径、静态图代理的基础接入。
- SQLite 数据库初始化和现有 POI/P3 gate 导入。
- 仿真任务 API：创建任务、查任务、查结果、导出结果。
- TGI/POI 供需缺口接口：读取外部上传客流资料和当前地图 POI，生成待复核缺口。
- 报告接口：供需缺口与节点改进报告可在前端查看，并下载 Markdown/JSON。
- 资料闭合中心前端可运行结构化仿真干跑，并展示待复核结果摘要和导出入口。
- 结构化干跑结果保存 seed、iterations 和 `needs_review / not_final` 状态。
- 资料池只显示网页外部上传资料，不自动把项目目录中的奥森样例文件当成用户上传项目。

## 待办事项

- 接入正式数据库迁移和部署配置。
- 补真实入口/节点、运营授权、转化率、收益成本和 DWG 几何。
- 在 P3 门禁闭合后再实现正式 Agent/GIS 仿真和收益测算。
