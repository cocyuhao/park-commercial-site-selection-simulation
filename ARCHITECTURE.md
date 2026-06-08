# 架构说明

## 文件职责

- `90_p6_expert_dashboard/app.py`：FastAPI 后端入口，提供网页、上传、AI、高德、数据和仿真任务接口。
- `90_p6_expert_dashboard/static/`：本地网页前端，包含专家 AI 工作台、空间地图、资料导入、节点清单、资料闭合中心、分析报告和结构化仿真干跑入口。
- `60_model/db/schema.sql`：SQLite 数据库表结构。
- `60_model/db/store.py`：数据库初始化、CSV 导入、任务和结果读写。
- `60_model/scripts/init_db.py`：初始化本地 SQLite 数据库。
- `60_model/scripts/import_existing_outputs.py`：把现有 POI 和 P3 gate CSV 导入数据库。
- `60_model/simulation/engine.py`：结构化仿真干跑骨架。
- `60_model/simulation/demand_gap.py`：外部上传客流/TGI资料、当前高德 POI 供给、供需缺口和报告生成。
- `60_model/simulation/validators.py`：请求和结果校验，禁止当前阶段输出 ROI。
- `50_external_gis/scripts/`：高德、OSM、路径和供给候选处理脚本。
- `70_outputs/processed_tables/`：结构化中间结果。

## 调用关系

`app.py` 启动时调用 `store.import_existing_outputs()`，把现有 CSV 导入 SQLite。

创建仿真任务时，`app.py` 先写入 `simulation_jobs`，再调用 `simulation.engine.run_structural_simulation()`，最后把结果写入 `simulation_results`。

生成供需缺口时，`app.py` 调用 `simulation.demand_gap`：先读取网页上传资料生成 TGI，再读取当前地图 POI 生成供给画像，最后生成缺口列表和报告。

空间地图由 `app.py` 提供高德 JS 配置、搜索上下文和周边 POI 数据。前端优先使用高德 JS 地图渲染标记、拖拽和缩放；当本地缺少正式 `AMAP_JS_API_KEY` / `AMAP_JS_SECURITY_CODE` 导致 JS 底图空白时，前端保留高德标记和控件，同时使用 `/api/amap/static-map` 的高德静态图作为可见底图兜底。历史 POI 结果仍可由 `50_external_gis/` 脚本生成，数据库只导入当前已存在的结构化结果。

## 关键决定

- 当前只做结构化干跑，不输出最终排序、收益预测或推荐结论。
- SQLite 文件是本地运行态产物，已加入 `.gitignore`，可由导入脚本重建。
- P3 gate 未闭合前，所有仿真接口返回都必须保持 `needs_review / not_final`。
- 未上传外部项目资料时，方案节点保持空状态；内置奥森资料只能作为样例基线，不能伪装成用户上传项目。
- 节点分数不作为页面主判断；前端主视觉显示推进优先级和具体建议，分数只作为折叠解释中的辅助信号，不得转写为最终排名。
- 并行 Codex 协作不做整仓覆盖；采用只读远端、三方对比、局部吸收、验证后提交。
