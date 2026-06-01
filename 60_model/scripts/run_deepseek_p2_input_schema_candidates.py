from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "60_model" / "src"))

from llm_router import route_for, run_deepseek_task  # noqa: E402  # type: ignore[import-not-found]


DOCX_SEMANTICS = ROOT / "70_outputs" / "processed_tables" / "p2_docx_project_semantic_draft_deepseek.csv"
PDF_LABELS = ROOT / "70_outputs" / "processed_tables" / "p2_pdf_spatial_label_draft_deepseek.csv"
INPUT_REQUIREMENTS = ROOT / "70_outputs" / "processed_tables" / "p2_simulation_input_requirements.csv"
SOURCE_CATALOG = ROOT / "40_quality_evidence" / "p2_real_site_source_catalog.csv"

OUT_NODES = ROOT / "70_outputs" / "processed_tables" / "p2_project_node_candidates.csv"
OUT_ASSUMPTIONS = ROOT / "70_outputs" / "processed_tables" / "p2_business_scene_assumption_pool.csv"
OUT_SPATIAL = ROOT / "70_outputs" / "processed_tables" / "p2_spatial_label_candidates.csv"
OUT_GAPS = ROOT / "70_outputs" / "processed_tables" / "p2_input_gap_register.csv"

REPORT = ROOT / "40_quality_evidence" / "deepseek_p2_input_schema_candidates_report.md"
OUT_DIR = ROOT / "60_model" / "llm_runs"
RAW_JSONL = OUT_DIR / "deepseek_p2_input_schema_candidates_raw.jsonl"
PROGRESS_JSON = OUT_DIR / "deepseek_p2_input_schema_candidates_progress.json"

NODE_FIELDS = [
    "node_id",
    "source_project_name",
    "node_name",
    "area_sqm",
    "primary_positioning",
    "candidate_business_formats",
    "scene_assumptions",
    "cooperation_mode",
    "source_semantic_ids",
    "input_status",
    "p2_use",
    "output_status",
    "executor",
    "llm_task_id",
]

ASSUMPTION_FIELDS = [
    "assumption_id",
    "source_project_name",
    "assumption_type",
    "assumption_text",
    "source_semantic_ids",
    "model_input_domain",
    "calibration_need",
    "quality_gate",
    "output_status",
    "executor",
    "llm_task_id",
]

SPATIAL_FIELDS = [
    "spatial_label_candidate_id",
    "source_label_id",
    "label_text",
    "label_type",
    "spatial_role",
    "geometry_status",
    "source_file",
    "page",
    "p2_use",
    "output_status",
    "executor",
    "llm_task_id",
]

GAP_FIELDS = [
    "gap_id",
    "input_domain",
    "gap_name",
    "current_status",
    "blocking_level",
    "why_it_matters",
    "next_action",
    "allowed_placeholder",
    "quality_gate",
    "output_status",
    "executor",
    "llm_task_id",
]

DEFAULT_GAPS = [
    ("geometry", "DWG geometry/layers/areas/paths", "pending_conversion", "blocking_for_geometry", "没有可信转换产物前不能计算面积、坐标、图层或动线。", "获取 DXF/GeoJSON/SVG 或可信 CAD 转换输出。", "no"),
    ("spatial_nodes", "North/south park comparable spatial nodes", "partial_pdf_proxy_only", "important", "当前只有北园 PDF 文本标签，南园 DWG 未解析，南北园空间不可直接比较。", "先完成 DWG 转换或人工图纸节点表。", "yes_pending_review"),
    ("visitor_flow", "Real visitor flow by entrance/node/time", "not_provided", "blocking_for_simulation_calibration", "仿真需要客流权重和时间分布，当前资料包不提供。", "链接 evidence_ledger 或后续官方/现场数据。", "yes_blank"),
    ("conversion_rate", "Business-format conversion rates", "not_provided", "blocking_for_revenue", "没有转化率不能从人流推导消费。", "先建立假设池并标注待校准。", "yes_assumption_needs_review"),
    ("revenue_cost", "Revenue/cost/rent/share parameters", "not_provided", "blocking_for_financial_model", "收益测算不能用 PPT 默认回填。", "等待运营数据或明确合同/租金假设。", "yes_blank"),
    ("operation_authorization", "Operator authorization and lease feasibility", "not_confirmed", "important", "方案可落地性取决于经营授权、租期、物业边界。", "按项目节点逐项核验授权和租赁边界。", "yes_pending_review"),
    ("regulatory", "Construction/renovation permission", "not_confirmed", "important", "阳光房、玻璃顶、夜间经营等涉及审批和政策边界。", "列入现场/管理方核验清单。", "yes_pending_review"),
    ("demand_fit", "Demand evidence for planned formats", "not_linked_to_checked_evidence", "important", "DOCX 是方案文本，仍需与客流/TGI/POI/消费证据对齐。", "把业态假设映射到 evidence_ledger 指标。", "yes_needs_review"),
    ("competition_supply", "In-park and nearby supply baseline for target park", "not_built_for_real_site", "important", "缺少真实奥森目标区供给底表会影响缺口判断。", "基于高德/现场/图纸节点建立目标公园供给候选。", "yes_blank"),
    ("model_gate", "P2 schema review and final gate", "not_started", "blocking_for_full_simulation", "候选表仍是 needs_review，不能直接跑完整仿真。", "本地脚本复核 schema、状态和禁止结论。", "no"),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: str(row.get(field, "") or "") for field in fields})


def strip_fence(text: str) -> str:
    value = text.strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?", "", value, flags=re.IGNORECASE).strip()
        value = re.sub(r"```$", "", value).strip()
    return value


def parse_json_object(text: str) -> dict[str, Any]:
    value = strip_fence(text)
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        start = value.find("{")
        end = value.rfind("}")
        if start >= 0 and end > start:
            return json.loads(value[start : end + 1])
        raise


def make_messages(context: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "你是 P2 输入 schema 候选表整理助手。"
                "你只能基于提供的 needs_review 草稿生成下一层候选输入表。"
                "不得使用 PPT，不得编造客流、收益、成本、坐标、面积或 DWG 几何。"
                "所有输出必须保持 needs_review 或 pending_conversion 语义。"
                "只输出严格 JSON，不输出 Markdown。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请基于上下文生成 P2 候选输入 schema 草稿。必须返回 JSON 对象，字段如下：\n"
                "{\n"
                "  \"project_node_candidates\": [... exactly 6],\n"
                "  \"business_scene_assumptions\": [... exactly 12],\n"
                "  \"spatial_label_candidates\": [... exactly 22],\n"
                "  \"input_gaps\": [... exactly 10],\n"
                "  \"summary\": {\"output_status\": \"needs_review\"}\n"
                "}\n\n"
                "project_node_candidates 每项字段：source_project_name,node_name,area_sqm,primary_positioning,"
                "candidate_business_formats,scene_assumptions,cooperation_mode,source_semantic_ids,input_status,p2_use。\n"
                "business_scene_assumptions 每项字段：source_project_name,assumption_type,assumption_text,source_semantic_ids,"
                "model_input_domain,calibration_need,quality_gate。\n"
                "spatial_label_candidates 每项字段：source_label_id,label_text,label_type,spatial_role,geometry_status,source_file,page,p2_use。"
                "geometry_status 必须是 pdf_text_label_only_pending_dwg_conversion。\n"
                "input_gaps 每项字段：input_domain,gap_name,current_status,blocking_level,why_it_matters,next_action,"
                "allowed_placeholder,quality_gate。\n\n"
                "上下文 JSON：\n" + json.dumps(context, ensure_ascii=False)
            ),
        },
    ]


def rows_by_project(docx_rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in docx_rows:
        project = row.get("project_name", "").strip()
        if project:
            grouped[project].append(row)
    return dict(grouped)


def compact(values: list[str], limit: int = 240) -> str:
    text = "；".join(dict.fromkeys(value.strip() for value in values if value and value.strip()))
    return text[:limit]


def fallback_nodes(docx_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    nodes: list[dict[str, str]] = []
    for project, rows in rows_by_project(docx_rows).items():
        ids = [row.get("semantic_id", "") for row in rows]
        scope = [row.get("extracted_value", "") for row in rows if row.get("semantic_type") == "project_scope"]
        formats = [row.get("extracted_value", "") for row in rows if row.get("semantic_type") == "business_format"]
        scenes = [row.get("extracted_value", "") for row in rows if row.get("semantic_type") == "scene_assumption"]
        cooperation = [row.get("extracted_value", "") for row in rows if row.get("semantic_type") == "cooperation_mode"]
        area_match = re.search(r"(\d+(?:\.\d+)?)\s*㎡", " ".join(scope))
        nodes.append(
            {
                "source_project_name": project,
                "node_name": project,
                "area_sqm": area_match.group(1) if area_match else "",
                "primary_positioning": compact(scope, 220),
                "candidate_business_formats": compact(formats, 220),
                "scene_assumptions": compact(scenes, 220),
                "cooperation_mode": compact(cooperation, 180),
                "source_semantic_ids": ";".join(ids),
                "input_status": "needs_review_from_docx_semantics",
                "p2_use": "project_node_candidate_for_schema_review",
            }
        )
    return nodes


def normalize_nodes(items: list[dict[str, Any]], docx_rows: list[dict[str, str]], task_id: str) -> list[dict[str, str]]:
    fallback = fallback_nodes(docx_rows)
    by_name = {str(item.get("source_project_name") or item.get("node_name") or ""): item for item in items}
    rows: list[dict[str, str]] = []
    for base in fallback:
        item = by_name.get(base["source_project_name"], {})
        merged = {**base, **{key: str(value) for key, value in item.items() if value not in (None, "")}}
        rows.append(
            {
                "node_id": f"P2-NODE-{len(rows) + 1:03d}",
                "source_project_name": merged.get("source_project_name", ""),
                "node_name": merged.get("node_name", merged.get("source_project_name", "")),
                "area_sqm": merged.get("area_sqm", ""),
                "primary_positioning": merged.get("primary_positioning", "")[:300],
                "candidate_business_formats": merged.get("candidate_business_formats", "")[:300],
                "scene_assumptions": merged.get("scene_assumptions", "")[:300],
                "cooperation_mode": merged.get("cooperation_mode", "")[:220],
                "source_semantic_ids": merged.get("source_semantic_ids", ""),
                "input_status": "needs_review_from_docx_semantics",
                "p2_use": "project_node_candidate_for_schema_review",
                "output_status": "needs_review",
                "executor": "deepseek",
                "llm_task_id": task_id,
            }
        )
    return rows[:6]


def fallback_assumptions(docx_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected_types = {"scene_assumption", "business_format", "cooperation_mode", "renovation_suggestion", "risk_or_constraint"}
    rows = [row for row in docx_rows if row.get("semantic_type") in selected_types]
    result: list[dict[str, str]] = []
    for row in rows:
        result.append(
            {
                "source_project_name": row.get("project_name", ""),
                "assumption_type": row.get("semantic_type", ""),
                "assumption_text": row.get("extracted_value", ""),
                "source_semantic_ids": row.get("semantic_id", ""),
                "model_input_domain": "business_formats_and_scenes",
                "calibration_need": "needs_evidence_or_operator_review",
                "quality_gate": "remain_needs_review_until_confirmed",
            }
        )
    return result


def normalize_assumptions(items: list[dict[str, Any]], docx_rows: list[dict[str, str]], task_id: str) -> list[dict[str, str]]:
    candidates = [{key: str(value) for key, value in item.items()} for item in items]
    fallback = fallback_assumptions(docx_rows)
    while len(candidates) < 12 and fallback:
        candidates.append(fallback.pop(0))
    rows: list[dict[str, str]] = []
    for item in candidates[:12]:
        rows.append(
            {
                "assumption_id": f"P2-ASSUMP-{len(rows) + 1:03d}",
                "source_project_name": item.get("source_project_name", ""),
                "assumption_type": item.get("assumption_type", ""),
                "assumption_text": item.get("assumption_text", "")[:360],
                "source_semantic_ids": item.get("source_semantic_ids", ""),
                "model_input_domain": item.get("model_input_domain", "business_formats_and_scenes"),
                "calibration_need": item.get("calibration_need", "needs_evidence_or_operator_review"),
                "quality_gate": item.get("quality_gate", "remain_needs_review_until_confirmed"),
                "output_status": "needs_review",
                "executor": "deepseek",
                "llm_task_id": task_id,
            }
        )
    return rows


def normalize_spatial(items: list[dict[str, Any]], pdf_rows: list[dict[str, str]], task_id: str) -> list[dict[str, str]]:
    item_by_label = {str(item.get("source_label_id", "")): item for item in items}
    rows: list[dict[str, str]] = []
    for row in pdf_rows:
        item = item_by_label.get(row.get("label_id", ""), {})
        rows.append(
            {
                "spatial_label_candidate_id": f"P2-SPATIAL-{len(rows) + 1:03d}",
                "source_label_id": row.get("label_id", ""),
                "label_text": str(item.get("label_text") or row.get("label_text", "")),
                "label_type": str(item.get("label_type") or row.get("label_type", "")),
                "spatial_role": str(item.get("spatial_role") or row.get("p2_spatial_use", ""))[:240],
                "geometry_status": "pdf_text_label_only_pending_dwg_conversion",
                "source_file": row.get("source_file", ""),
                "page": row.get("page", "1"),
                "p2_use": "spatial_label_candidate_for_manual_mapping",
                "output_status": "needs_review",
                "executor": "deepseek",
                "llm_task_id": task_id,
            }
        )
    return rows


def normalize_gaps(items: list[dict[str, Any]], task_id: str) -> list[dict[str, str]]:
    incoming_by_domain: dict[str, dict[str, str]] = {}
    for item in items:
        normalized_item = {key: str(value) for key, value in item.items()}
        domain = normalized_item.get("input_domain", "").strip()
        if domain and domain not in incoming_by_domain:
            incoming_by_domain[domain] = normalized_item

    normalized: list[dict[str, str]] = []
    for domain, name, status, blocking, why, action, placeholder in DEFAULT_GAPS:
        item = incoming_by_domain.get(domain, {})
        normalized.append(
            {
                "input_domain": domain,
                "gap_name": item.get("gap_name") or name,
                "current_status": item.get("current_status") or status,
                "blocking_level": item.get("blocking_level") or blocking,
                "why_it_matters": item.get("why_it_matters") or why,
                "next_action": item.get("next_action") or action,
                "allowed_placeholder": item.get("allowed_placeholder") or placeholder,
                "quality_gate": item.get("quality_gate") or "must_remain_explicit_before_full_simulation",
            }
        )
    rows: list[dict[str, str]] = []
    for item in normalized:
        rows.append(
            {
                "gap_id": f"P2-GAP-{len(rows) + 1:03d}",
                "input_domain": item.get("input_domain", ""),
                "gap_name": item.get("gap_name", ""),
                "current_status": item.get("current_status", ""),
                "blocking_level": item.get("blocking_level", ""),
                "why_it_matters": item.get("why_it_matters", "")[:300],
                "next_action": item.get("next_action", "")[:260],
                "allowed_placeholder": item.get("allowed_placeholder", ""),
                "quality_gate": item.get("quality_gate", "must_remain_explicit_before_full_simulation"),
                "output_status": "needs_review",
                "executor": "deepseek",
                "llm_task_id": task_id,
            }
        )
    return rows


def run() -> None:
    task_id = "LLM-018"
    route = route_for(task_id)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    docx_rows = read_csv(DOCX_SEMANTICS)
    pdf_rows = read_csv(PDF_LABELS)
    context = {
        "project": "公园商业选址仿真与经营决策系统",
        "phase": "P2 准备 schema 候选表，不是完整仿真建模",
        "guardrails": [
            "所有输出保持 needs_review。",
            "PPT 不进入 P2 主线。",
            "PDF 标签不等于 DWG 几何。",
            "缺失客流/收益/成本/转化率保持缺口，不回填。",
        ],
        "source_catalog": read_csv(SOURCE_CATALOG),
        "input_requirements": read_csv(INPUT_REQUIREMENTS),
        "docx_semantics": docx_rows,
        "pdf_spatial_labels": pdf_rows,
    }
    response = run_deepseek_task(task_id, make_messages(context), temperature=0.0)
    parsed = parse_json_object(response)

    node_rows = normalize_nodes(list(parsed.get("project_node_candidates", [])), docx_rows, task_id)
    assumption_rows = normalize_assumptions(list(parsed.get("business_scene_assumptions", [])), docx_rows, task_id)
    spatial_rows = normalize_spatial(list(parsed.get("spatial_label_candidates", [])), pdf_rows, task_id)
    gap_rows = normalize_gaps(list(parsed.get("input_gaps", [])), task_id)

    write_csv(OUT_NODES, node_rows, NODE_FIELDS)
    write_csv(OUT_ASSUMPTIONS, assumption_rows, ASSUMPTION_FIELDS)
    write_csv(OUT_SPATIAL, spatial_rows, SPATIAL_FIELDS)
    write_csv(OUT_GAPS, gap_rows, GAP_FIELDS)

    RAW_JSONL.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "task_id": task_id,
                "task_name": route.task_name,
                "executor": route.default_executor,
                "model": route.model,
                "output_status": route.output_status,
                "node_rows": len(node_rows),
                "assumption_rows": len(assumption_rows),
                "spatial_rows": len(spatial_rows),
                "gap_rows": len(gap_rows),
                "response_excerpt": response[:5000],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    PROGRESS_JSON.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "node_rows": len(node_rows),
                "assumption_rows": len(assumption_rows),
                "spatial_rows": len(spatial_rows),
                "gap_rows": len(gap_rows),
                "output_status": route.output_status,
                "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    REPORT.write_text(
        "\n".join(
            [
                "# DeepSeek P2 输入 schema 候选表生成报告",
                "",
                "## 结论",
                "",
                "- 输出状态：needs_review。",
                f"- 项目节点候选：{len(node_rows)} 条。",
                f"- 业态/场景假设池：{len(assumption_rows)} 条。",
                f"- 空间标签候选：{len(spatial_rows)} 条。",
                f"- 输入缺口登记：{len(gap_rows)} 条。",
                "- 本轮仍是 P2 准备，不做完整仿真建模。",
                "- DWG 几何保持 pending_conversion；PPT 不进入主线。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote nodes={len(node_rows)} to {OUT_NODES}")
    print(f"wrote assumptions={len(assumption_rows)} to {OUT_ASSUMPTIONS}")
    print(f"wrote spatial={len(spatial_rows)} to {OUT_SPATIAL}")
    print(f"wrote gaps={len(gap_rows)} to {OUT_GAPS}")
    print(f"wrote report to {REPORT}")


if __name__ == "__main__":
    run()
