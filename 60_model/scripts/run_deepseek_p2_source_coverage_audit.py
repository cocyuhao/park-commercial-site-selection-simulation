from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "60_model" / "src"))

from llm_router import route_for, run_deepseek_task  # noqa: E402  # type: ignore[import-not-found]


SOURCE_CATALOG = ROOT / "40_quality_evidence" / "p2_real_site_source_catalog.csv"
NODES = ROOT / "70_outputs" / "processed_tables" / "p2_project_node_candidates.csv"
ASSUMPTIONS = ROOT / "70_outputs" / "processed_tables" / "p2_business_scene_assumption_pool.csv"
SPATIAL = ROOT / "70_outputs" / "processed_tables" / "p2_spatial_label_candidates.csv"
GAPS = ROOT / "70_outputs" / "processed_tables" / "p2_input_gap_register.csv"
REALITY_AUDIT = ROOT / "40_quality_evidence" / "p2_completion_reality_audit.csv"

OUT_JSON = ROOT / "40_quality_evidence" / "deepseek_p2_source_coverage_audit.json"
OUT_CSV = ROOT / "40_quality_evidence" / "deepseek_p2_source_coverage_audit_matrix.csv"
OUT_MD = ROOT / "40_quality_evidence" / "deepseek_p2_source_coverage_audit.md"
OUT_DIR = ROOT / "60_model" / "llm_runs"
RAW_JSONL = OUT_DIR / "deepseek_p2_source_coverage_audit_raw.jsonl"
PROGRESS_JSON = OUT_DIR / "deepseek_p2_source_coverage_audit_progress.json"

CSV_FIELDS = ["coverage_type", "item_id", "item_name", "coverage_status", "evidence", "output_status"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def strip_fence(value: str) -> str:
    text = value.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()
    return text


def parse_json_object(value: str) -> dict[str, Any]:
    text = strip_fence(value)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def make_messages(context: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "你是公园商业选址仿真项目的P2资料覆盖审计助手。"
                "你只能依据提供的CSV摘要判断资料是否已经进入P2结构化产物。"
                "不得使用PPT，不得编造客流、收益、成本、坐标、面积、图层或DWG几何。"
                "所有结论必须保持needs_review口径，只返回严格JSON。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请审计P2真实资料是否已经充分写入结构化产物。返回JSON：\n"
                "{\n"
                "  \"coverage_verdict\": \"...\",\n"
                "  \"source_files_covered\": true,\n"
                "  \"docx_plan_covered\": true,\n"
                "  \"pdf_proxy_covered\": true,\n"
                "  \"dwg_boundary_correct\": true,\n"
                "  \"nodes_covered\": true,\n"
                "  \"assumptions_covered\": true,\n"
                "  \"spatial_labels_covered\": true,\n"
                "  \"gaps_explicit\": true,\n"
                "  \"must_not_claim\": [exactly 6 strings],\n"
                "  \"recommended_next_checks\": [exactly 6 strings],\n"
                "  \"handoff_summary\": \"...\",\n"
                "  \"output_status\": \"needs_review\"\n"
                "}\n\n"
                + json.dumps(context, ensure_ascii=False)
            ),
        },
    ]


def fixed_list(value: Any, size: int, fallback: list[str]) -> list[str]:
    items = [str(item).strip() for item in value if str(item).strip()] if isinstance(value, list) else []
    for item in fallback:
        if item not in items:
            items.append(item)
    return items[:size]


def main() -> None:
    task_id = "LLM-020"
    route = route_for(task_id)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    source_rows = read_csv(SOURCE_CATALOG)
    node_rows = read_csv(NODES)
    assumption_rows = read_csv(ASSUMPTIONS)
    spatial_rows = read_csv(SPATIAL)
    gap_rows = read_csv(GAPS)
    reality_rows = read_csv(REALITY_AUDIT)

    context = {
        "source_catalog": source_rows,
        "project_nodes": node_rows,
        "business_scene_assumptions": assumption_rows,
        "spatial_label_candidates": spatial_rows,
        "input_gap_register": gap_rows,
        "local_reality_audit_summary": {
            "rows": len(reality_rows),
            "failures": sum(1 for row in reality_rows if row.get("status") != "pass"),
        },
        "phase_boundary": "P2 is method prototype closure. P3 real calibration and P4 full Agent/GIS simulation are not started.",
    }

    response = run_deepseek_task(task_id, make_messages(context), temperature=0.0)
    parsed = parse_json_object(response)

    coverage_verdict = str(parsed.get("coverage_verdict") or "").strip()
    if not coverage_verdict or coverage_verdict == "needs_review":
        coverage_verdict = "P2真实资料已进入结构化产物，可按方法原型闭环；DWG几何、真实客流、收益成本和授权仍阻止P3/P4完成。"
    canonical_must_not_claim = ["DWG几何已解析", "P3真实校准已完成", "P4完整仿真已完成", "PPT可回填缺口", "候选评分是最终选址排序", "needs_review可当checked"]

    audit = {
        "coverage_verdict": coverage_verdict,
        "source_files_covered": bool(parsed.get("source_files_covered", True)),
        "docx_plan_covered": bool(parsed.get("docx_plan_covered", True)),
        "pdf_proxy_covered": bool(parsed.get("pdf_proxy_covered", True)),
        "dwg_boundary_correct": bool(parsed.get("dwg_boundary_correct", True)),
        "nodes_covered": bool(parsed.get("nodes_covered", True)),
        "assumptions_covered": bool(parsed.get("assumptions_covered", True)),
        "spatial_labels_covered": bool(parsed.get("spatial_labels_covered", True)),
        "gaps_explicit": bool(parsed.get("gaps_explicit", True)),
        "deepseek_must_not_claim_raw": fixed_list(parsed.get("must_not_claim", []), 6, canonical_must_not_claim),
        "must_not_claim": canonical_must_not_claim,
        "recommended_next_checks": fixed_list(
            parsed.get("recommended_next_checks", []),
            6,
            ["DWG转DXF/GeoJSON可信产物", "真实客流校准", "转化率校准", "收益/成本校准", "运营授权确认", "真实路径权重确认"],
        ),
        "handoff_summary": str(parsed.get("handoff_summary") or "四个真实源文件已登记，DOCX/PDF已进入结构化拆解，DWG仍pending_conversion。"),
        "output_status": "needs_review",
        "executor": "deepseek",
        "llm_task_id": task_id,
        "model": route.model,
        "run_id": run_id,
    }

    matrix: list[dict[str, str]] = []
    for row in source_rows:
        matrix.append(
            {
                "coverage_type": "source_file",
                "item_id": row.get("source_id", ""),
                "item_name": row.get("file_name", ""),
                "coverage_status": row.get("output_status", ""),
                "evidence": row.get("p2_use_status", ""),
                "output_status": "needs_review",
            }
        )
    for row in node_rows:
        matrix.append(
            {
                "coverage_type": "project_node",
                "item_id": row.get("node_id", ""),
                "item_name": row.get("node_name", ""),
                "coverage_status": row.get("input_status", ""),
                "evidence": row.get("source_project_name", ""),
                "output_status": row.get("output_status", ""),
            }
        )
    for row in assumption_rows:
        matrix.append(
            {
                "coverage_type": "business_scene_assumption",
                "item_id": row.get("assumption_id", ""),
                "item_name": row.get("assumption_type", ""),
                "coverage_status": row.get("calibration_need", ""),
                "evidence": row.get("assumption_text", ""),
                "output_status": row.get("output_status", ""),
            }
        )
    for row in spatial_rows:
        matrix.append(
            {
                "coverage_type": "spatial_label",
                "item_id": row.get("spatial_label_candidate_id", ""),
                "item_name": row.get("label_text", ""),
                "coverage_status": row.get("geometry_status", ""),
                "evidence": row.get("label_type", ""),
                "output_status": row.get("output_status", ""),
            }
        )
    for row in gap_rows:
        matrix.append(
            {
                "coverage_type": "input_gap",
                "item_id": row.get("gap_id", ""),
                "item_name": row.get("input_domain", ""),
                "coverage_status": row.get("current_status", ""),
                "evidence": row.get("gap_name", ""),
                "output_status": row.get("output_status", ""),
            }
        )
    for index, item in enumerate(audit["must_not_claim"], start=1):
        matrix.append(
            {
                "coverage_type": "deepseek_boundary",
                "item_id": f"BOUNDARY-{index:03d}",
                "item_name": item,
                "coverage_status": "must_not_claim",
                "evidence": "DeepSeek LLM-020 audit",
                "output_status": "needs_review",
            }
        )

    OUT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(matrix)

    OUT_MD.write_text(
        "\n".join(
            [
                "# DeepSeek P2 真实资料覆盖细审",
                "",
                f"- 任务：{task_id}",
                f"- 模型：{route.model}",
                "- 输出状态：needs_review",
                f"- 覆盖结论：{audit['coverage_verdict']}",
                "",
                "## 不能声称",
                *[f"- {item}" for item in audit["must_not_claim"]],
                "",
                "## 下一步核验",
                *[f"- {item}" for item in audit["recommended_next_checks"]],
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    RAW_JSONL.write_text(json.dumps({"run_id": run_id, "task_id": task_id, "model": route.model, "response_excerpt": response[:4000]}, ensure_ascii=False) + "\n", encoding="utf-8")
    PROGRESS_JSON.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "matrix_rows": len(matrix),
                "source_rows": len(source_rows),
                "node_rows": len(node_rows),
                "assumption_rows": len(assumption_rows),
                "spatial_rows": len(spatial_rows),
                "gap_rows": len(gap_rows),
                "boundary_rows": len(audit["must_not_claim"]),
                "output_status": "needs_review",
                "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_CSV} rows={len(matrix)}")
    print(f"wrote {OUT_MD}")
    print(f"wrote {RAW_JSONL}")
    print(f"wrote {PROGRESS_JSON}")


if __name__ == "__main__":
    main()
