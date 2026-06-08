# 现代仿真与数据栈验证报告（2026-06-04）

## 结论

- 总状态：`pass`
- 包数量：14
- 状态统计：{'pass': 14}

## 已验证能力

- `pass` `duckdb` 1.5.3：SQL-on-files and reproducible intermediate tables for large simulation runs.
- `pass` `polars` 1.41.2：Fast columnar data transforms for scenario grids and evidence joins.
- `pass` `jsonschema` 4.26.0：Local schema validation for LLM outputs and handoff artifacts.
- `pass` `pydantic` 2.10.5：Typed runtime models for simulation objects and API envelopes.
- `pass` `geopandas` 1.1.3：Vector geospatial dataframes for boundaries, POI layers, and spatial joins.
- `pass` `shapely` 2.1.2：Geometry operations for boundaries, buffers, distances, and validity checks.
- `pass` `networkx` 3.6.1：Graph representation for routes, entrances, and walkable network prototypes.
- `pass` `osmnx` 2.1.0：Street-network acquisition and routing prototypes; not a substitute for Amap/DWG validation.
- `pass` `movingpandas` 0.22.4：Trajectory objects and movement-analysis vocabulary for later real track calibration.
- `pass` `mesa` 3.5.1：Python agent-based modeling prototype layer for personas and behavior programs.
- `pass` `mesa_geo` 0.9.3：Geospatial ABM extension; candidate bridge between agents and map geometries.
- `pass` `simpy` 4.1.2：Discrete-event queues for service, waiting, stockout, and operating-hour constraints.
- `pass` `SALib` 1.5.2：Sensitivity analysis for deciding which uncertain inputs matter most.
- `pass` `optuna` 4.9.0：Parameter search and calibration once field observations or reliable proxies exist.

## 本轮不强行引入的重型组件

- `Ray`：Useful for very large distributed agent execution, but heavy for current local P2/P3 validation.
- `MATSim / SUMO`：Good external engines for mature transport simulation, but require clean road network, demand, and calibration data first.
- `AnyLogic / Unreal`：Can support high-fidelity demos later, but would distract from evidence, schema, and calibration gates now.

## 使用边界

- 这些包证明本地具备现代仿真原型与校准能力，不代表完整仿真已经完成。
- DeepSeek 仍只能生成 `draft/needs_review` 候选，必须经过 schema、规则、证据和人工复核。
- Huff/Logit/Gravity 等经典方法只作为选择概率的可解释因子，不再作为系统主叙事。
