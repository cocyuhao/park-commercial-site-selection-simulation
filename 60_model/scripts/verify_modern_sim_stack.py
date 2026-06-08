from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "40_quality_evidence" / "modern_sim_stack_verification_20260604.json"
OUT_MD = ROOT / "40_quality_evidence" / "modern_sim_stack_verification_20260604.md"

REQUIRED_PACKAGES = [
    {
        "module": "duckdb",
        "dist": "duckdb",
        "group": "modern_data_engine",
        "purpose": "SQL-on-files and reproducible intermediate tables for large simulation runs.",
    },
    {
        "module": "polars",
        "dist": "polars",
        "group": "modern_data_engine",
        "purpose": "Fast columnar data transforms for scenario grids and evidence joins.",
    },
    {
        "module": "jsonschema",
        "dist": "jsonschema",
        "group": "contract_gate",
        "purpose": "Local schema validation for LLM outputs and handoff artifacts.",
    },
    {
        "module": "pydantic",
        "dist": "pydantic",
        "group": "contract_gate",
        "purpose": "Typed runtime models for simulation objects and API envelopes.",
    },
    {
        "module": "geopandas",
        "dist": "geopandas",
        "group": "geospatial",
        "purpose": "Vector geospatial dataframes for boundaries, POI layers, and spatial joins.",
    },
    {
        "module": "shapely",
        "dist": "shapely",
        "group": "geospatial",
        "purpose": "Geometry operations for boundaries, buffers, distances, and validity checks.",
    },
    {
        "module": "networkx",
        "dist": "networkx",
        "group": "geospatial",
        "purpose": "Graph representation for routes, entrances, and walkable network prototypes.",
    },
    {
        "module": "osmnx",
        "dist": "osmnx",
        "group": "geospatial",
        "purpose": "Street-network acquisition and routing prototypes; not a substitute for Amap/DWG validation.",
    },
    {
        "module": "movingpandas",
        "dist": "movingpandas",
        "group": "trajectory",
        "purpose": "Trajectory objects and movement-analysis vocabulary for later real track calibration.",
    },
    {
        "module": "mesa",
        "dist": "mesa",
        "group": "agent_simulation",
        "purpose": "Python agent-based modeling prototype layer for personas and behavior programs.",
    },
    {
        "module": "mesa_geo",
        "dist": "mesa-geo",
        "group": "agent_simulation",
        "purpose": "Geospatial ABM extension; candidate bridge between agents and map geometries.",
    },
    {
        "module": "simpy",
        "dist": "simpy",
        "group": "event_simulation",
        "purpose": "Discrete-event queues for service, waiting, stockout, and operating-hour constraints.",
    },
    {
        "module": "SALib",
        "dist": "SALib",
        "group": "calibration",
        "purpose": "Sensitivity analysis for deciding which uncertain inputs matter most.",
    },
    {
        "module": "optuna",
        "dist": "optuna",
        "group": "calibration",
        "purpose": "Parameter search and calibration once field observations or reliable proxies exist.",
    },
]

INTENTIONALLY_DEFERRED = [
    {
        "name": "Ray",
        "reason": "Useful for very large distributed agent execution, but heavy for current local P2/P3 validation.",
    },
    {
        "name": "MATSim / SUMO",
        "reason": "Good external engines for mature transport simulation, but require clean road network, demand, and calibration data first.",
    },
    {
        "name": "AnyLogic / Unreal",
        "reason": "Can support high-fidelity demos later, but would distract from evidence, schema, and calibration gates now.",
    },
]


def probe_package(item: dict[str, str]) -> dict[str, str]:
    code = f"""
from __future__ import annotations
import importlib
import importlib.metadata
import warnings
warnings.filterwarnings("ignore")
module = {item["module"]!r}
dist = {item["dist"]!r}
importlib.import_module(module)
print(importlib.metadata.version(dist))
"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return {
            **item,
            "status": "fail",
            "version": "",
            "detail": "import timed out after 30s",
        }

    output = (result.stdout or "").strip()
    detail = (result.stderr or "").strip()
    return {
        **item,
        "status": "pass" if result.returncode == 0 and output else "fail",
        "version": output.splitlines()[-1] if output else "",
        "detail": detail[:500],
    }


def write_report(rows: list[dict[str, str]]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    status_counts = Counter(row["status"] for row in rows)
    group_counts = Counter(row["group"] for row in rows if row["status"] == "pass")
    overall = "pass" if status_counts.get("fail", 0) == 0 else "fail"
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": overall,
        "package_count": len(rows),
        "status_counts": dict(status_counts),
        "pass_group_counts": dict(group_counts),
        "packages": rows,
        "intentionally_deferred": INTENTIONALLY_DEFERRED,
        "architecture_note": (
            "Modern local stack is ready for evidence-bound hybrid simulation: domain generator, "
            "geospatial constraints, agent/event prototypes, sensitivity/calibration, and strict LLM contracts."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 现代仿真与数据栈验证报告（2026-06-04）",
        "",
        "## 结论",
        "",
        f"- 总状态：`{overall}`",
        f"- 包数量：{len(rows)}",
        f"- 状态统计：{dict(status_counts)}",
        "",
        "## 已验证能力",
        "",
    ]
    for row in rows:
        lines.append(
            f"- `{row['status']}` `{row['module']}` {row['version']}：{row['purpose']}"
        )

    lines.extend(
        [
            "",
            "## 本轮不强行引入的重型组件",
            "",
        ]
    )
    for item in INTENTIONALLY_DEFERRED:
        lines.append(f"- `{item['name']}`：{item['reason']}")

    lines.extend(
        [
            "",
            "## 使用边界",
            "",
            "- 这些包证明本地具备现代仿真原型与校准能力，不代表完整仿真已经完成。",
            "- DeepSeek 仍只能生成 `draft/needs_review` 候选，必须经过 schema、规则、证据和人工复核。",
            "- Huff/Logit/Gravity 等经典方法只作为选择概率的可解释因子，不再作为系统主叙事。",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = [probe_package(item) for item in REQUIRED_PACKAGES]
    write_report(rows)
    failures = [row for row in rows if row["status"] == "fail"]
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    print(f"packages={len(rows)} failures={len(failures)}")
    if failures:
        for row in failures:
            print(f"FAIL {row['module']}: {row['detail']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
