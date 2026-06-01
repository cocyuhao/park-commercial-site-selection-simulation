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


DOCX_TEXT = ROOT / "30_extraction" / "p2_real_site" / "osen_project_plan_text.txt"
PDF_TEXT = ROOT / "30_extraction" / "p2_real_site" / "osen_north_cad_pdf_text.txt"
SOURCE_CATALOG = ROOT / "40_quality_evidence" / "p2_real_site_source_catalog.csv"
INPUT_REQUIREMENTS = ROOT / "70_outputs" / "processed_tables" / "p2_simulation_input_requirements.csv"

OUT_DIR = ROOT / "60_model" / "llm_runs"
RAW_JSONL = OUT_DIR / "deepseek_p2_real_site_semantic_raw.jsonl"
PROGRESS_JSON = OUT_DIR / "deepseek_p2_real_site_semantic_progress.json"

OUT_DOCX = ROOT / "70_outputs" / "processed_tables" / "p2_docx_project_semantic_draft_deepseek.csv"
OUT_PDF = ROOT / "70_outputs" / "processed_tables" / "p2_pdf_spatial_label_draft_deepseek.csv"
GENERATION_REPORT = ROOT / "40_quality_evidence" / "deepseek_p2_real_site_semantic_report.md"

DOCX_FIELDS = [
    "semantic_id",
    "source_id",
    "source_file",
    "project_name",
    "area_sqm",
    "semantic_type",
    "category",
    "extracted_value",
    "source_excerpt",
    "p2_use",
    "quality_status",
    "output_status",
    "executor",
    "llm_task_id",
]

PDF_FIELDS = [
    "label_id",
    "source_id",
    "source_file",
    "page",
    "label_text",
    "label_type",
    "p2_spatial_use",
    "geometry_status",
    "source_excerpt",
    "quality_status",
    "output_status",
    "executor",
    "llm_task_id",
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


def clamp(text: str, limit: int) -> str:
    value = re.sub(r"\n{3,}", "\n\n", text.strip())
    if len(value) <= limit:
        return value
    half = limit // 2
    return value[:half] + "\n\n...[middle omitted]...\n\n" + value[-half:]


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


def source_by_type(rows: list[dict[str, str]], source_type: str) -> dict[str, str]:
    for row in rows:
        if row.get("source_type") == source_type:
            return row
    return {}


def make_messages(context: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "你是公园商业选址仿真项目的 P2 真实资料语义拆解助手。"
                "你只能基于提供的 DOCX/PDF 抽取文本生成结构化草稿。"
                "不得使用 PPT，不得编造客流、收益、成本、转化率、面积或几何。"
                "DWG 未转换前，所有几何/图层/面积/坐标/动线必须保持 pending_conversion。"
                "输出必须是严格 JSON 对象，不要 Markdown，不要代码块。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请把 P2 真实资料拆成两个数组：docx_semantics 和 pdf_spatial_labels。\n"
                "每个 docx_semantics 元素必须包含字段：project_name, area_sqm, semantic_type, category, "
                "extracted_value, source_excerpt, p2_use, quality_status。\n"
                "semantic_type 只能从 project_scope/business_format/spatial_node/scene_assumption/cooperation_mode/"
                "renovation_suggestion/benchmark_case/risk_or_constraint 中选择。\n"
                "quality_status 只能是 needs_review。\n"
                "请尽量覆盖 DOCX 中所有明确项目，不少于 18 条。\n\n"
                "每个 pdf_spatial_labels 元素必须包含字段：page, label_text, label_type, p2_spatial_use, "
                "geometry_status, source_excerpt, quality_status。\n"
                "label_type 只能从 road/parking/sports/facility/service/building/recreation/water_green/bridge_or_gate/other 中选择。\n"
                "geometry_status 必须是 pdf_text_label_only_pending_dwg_conversion。\n"
                "quality_status 只能是 needs_review。\n"
                "请提取北园 PDF 中可用于后续空间核对的标签，不少于 18 条。\n\n"
                "必须返回 JSON：{\"docx_semantics\": [...], \"pdf_spatial_labels\": [...], "
                "\"summary\": {\"output_status\": \"needs_review\", \"p2_boundary\": \"...\"}}\n\n"
                "上下文 JSON：\n"
                + json.dumps(context, ensure_ascii=False)
            ),
        },
    ]


def normalize_docx_rows(items: list[dict[str, Any]], source: dict[str, str], task_id: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, item in enumerate(items, 1):
        semantic_type = str(item.get("semantic_type", "")).strip()
        category = str(item.get("category", "")).strip()
        extracted_value = str(item.get("extracted_value", "")).strip()
        scene_tokens = [
            "婚礼",
            "摄影",
            "亲子",
            "团建",
            "研学",
            "沙龙",
            "冷餐会",
            "Live House",
            "夜晚",
            "音乐演出",
            "草坪",
            "市集",
            "野餐",
            "沉浸式",
            "RPG",
            "疗愈",
        ]
        if semantic_type == "business_format" and (
            "活动" in category or any(token in extracted_value for token in scene_tokens)
        ):
            semantic_type = "scene_assumption"
        rows.append(
            {
                "semantic_id": f"P2-DOCX-SEM-{idx:03d}",
                "source_id": source.get("source_id", "P2SRC-004"),
                "source_file": source.get("source_file", ""),
                "project_name": str(item.get("project_name", "")).strip(),
                "area_sqm": str(item.get("area_sqm", "")).strip(),
                "semantic_type": semantic_type,
                "category": category,
                "extracted_value": extracted_value,
                "source_excerpt": str(item.get("source_excerpt", "")).strip()[:240],
                "p2_use": str(item.get("p2_use", "")).strip() or "assumption_pool_needs_review",
                "quality_status": "needs_review",
                "output_status": "needs_review",
                "executor": "deepseek",
                "llm_task_id": task_id,
            }
        )
    return rows


def normalize_pdf_rows(items: list[dict[str, Any]], source: dict[str, str], task_id: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, item in enumerate(items, 1):
        rows.append(
            {
                "label_id": f"P2-PDF-LABEL-{idx:03d}",
                "source_id": source.get("source_id", "P2SRC-001"),
                "source_file": source.get("source_file", ""),
                "page": str(item.get("page", "1") or "1"),
                "label_text": str(item.get("label_text", "")).strip(),
                "label_type": str(item.get("label_type", "")).strip(),
                "p2_spatial_use": str(item.get("p2_spatial_use", "")).strip() or "spatial_label_candidate_needs_manual_review",
                "geometry_status": "pdf_text_label_only_pending_dwg_conversion",
                "source_excerpt": str(item.get("source_excerpt", "")).strip()[:240],
                "quality_status": "needs_review",
                "output_status": "needs_review",
                "executor": "deepseek",
                "llm_task_id": task_id,
            }
        )
    return rows


def run() -> None:
    task_id = "LLM-017"
    route = route_for(task_id)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    catalog = read_csv(SOURCE_CATALOG)
    requirements = read_csv(INPUT_REQUIREMENTS)
    docx_source = source_by_type(catalog, "docx")
    pdf_source = source_by_type(catalog, "pdf")
    context = {
        "project": "公园商业选址仿真与经营决策系统",
        "phase": "P2 准备，不是完整仿真建模",
        "guardrails": [
            "PPT 不进入 P2 主线。",
            "DWG 未转换前保持 pending_conversion。",
            "真实客流、收益、成本、转化率没有来源时保持空值。",
            "DeepSeek 输出只允许 needs_review 草稿。",
        ],
        "sources": catalog,
        "input_requirements": requirements,
        "docx_text": clamp(DOCX_TEXT.read_text(encoding="utf-8-sig", errors="replace"), 12000),
        "north_cad_pdf_text": clamp(PDF_TEXT.read_text(encoding="utf-8-sig", errors="replace"), 7000),
    }

    response = run_deepseek_task(task_id, make_messages(context), temperature=0.0)
    parsed = parse_json_object(response)
    docx_rows = normalize_docx_rows(list(parsed.get("docx_semantics", [])), docx_source, task_id)
    pdf_rows = normalize_pdf_rows(list(parsed.get("pdf_spatial_labels", [])), pdf_source, task_id)

    write_csv(OUT_DOCX, docx_rows, DOCX_FIELDS)
    write_csv(OUT_PDF, pdf_rows, PDF_FIELDS)
    RAW_JSONL.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "task_id": task_id,
                "task_name": route.task_name,
                "executor": route.default_executor,
                "model": route.model,
                "output_status": route.output_status,
                "input_paths": [
                    str(DOCX_TEXT.relative_to(ROOT)).replace("\\", "/"),
                    str(PDF_TEXT.relative_to(ROOT)).replace("\\", "/"),
                    str(SOURCE_CATALOG.relative_to(ROOT)).replace("\\", "/"),
                    str(INPUT_REQUIREMENTS.relative_to(ROOT)).replace("\\", "/"),
                ],
                "docx_rows": len(docx_rows),
                "pdf_rows": len(pdf_rows),
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
                "docx_semantic_rows": len(docx_rows),
                "pdf_spatial_label_rows": len(pdf_rows),
                "output_status": route.output_status,
                "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    GENERATION_REPORT.write_text(
        "\n".join(
            [
                "# DeepSeek P2 真实资料语义拆解生成报告",
                "",
                "## 结论",
                "",
                "- 输出状态：needs_review。",
                f"- DOCX 语义拆解行数：{len(docx_rows)}。",
                f"- PDF 空间标签行数：{len(pdf_rows)}。",
                "- 本轮只做 P2 准备语义草稿，不做完整仿真建模。",
                "- DWG 仍保持 pending_conversion，不产生几何、面积、坐标、图层或动线结论。",
                "- PPT 不进入本轮 P2 主线。",
                "",
                "## 输出",
                "",
                f"- `{str(OUT_DOCX.relative_to(ROOT)).replace(chr(92), '/')}`",
                f"- `{str(OUT_PDF.relative_to(ROOT)).replace(chr(92), '/')}`",
                f"- `{str(RAW_JSONL.relative_to(ROOT)).replace(chr(92), '/')}`",
                f"- `{str(PROGRESS_JSON.relative_to(ROOT)).replace(chr(92), '/')}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote docx rows={len(docx_rows)} to {OUT_DOCX}")
    print(f"wrote pdf rows={len(pdf_rows)} to {OUT_PDF}")
    print(f"wrote report to {GENERATION_REPORT}")


if __name__ == "__main__":
    run()
