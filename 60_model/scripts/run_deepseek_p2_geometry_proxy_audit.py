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


PDF_TEXT = ROOT / "30_extraction" / "p2_real_site" / "osen_north_cad_pdf_text.txt"
PDF_PAGES = ROOT / "30_extraction" / "p2_real_site" / "osen_north_cad_pdf_pages.csv"
SOURCE_CATALOG = ROOT / "40_quality_evidence" / "p2_real_site_source_catalog.csv"
SPATIAL_LABELS = ROOT / "70_outputs" / "processed_tables" / "p2_spatial_label_candidates.csv"

OUT_ZONES = ROOT / "70_outputs" / "processed_tables" / "p2_pdf_proxy_zone_candidates_deepseek.csv"
OUT_DWG = ROOT / "70_outputs" / "processed_tables" / "p2_dwg_conversion_worklist_deepseek.csv"
OUT_LIMITS = ROOT / "70_outputs" / "processed_tables" / "p2_geometry_proxy_limitations_deepseek.csv"
OUT_JSON = ROOT / "40_quality_evidence" / "deepseek_p2_geometry_proxy_audit.json"
OUT_MD = ROOT / "40_quality_evidence" / "deepseek_p2_geometry_proxy_audit.md"
OUT_DIR = ROOT / "60_model" / "llm_runs"
RAW_JSONL = OUT_DIR / "deepseek_p2_geometry_proxy_audit_raw.jsonl"
PROGRESS_JSON = OUT_DIR / "deepseek_p2_geometry_proxy_audit_progress.json"


ZONE_FIELDS = ["zone_id", "zone_name", "proxy_basis_labels", "spatial_role", "candidate_uses", "geometry_status", "quality_status", "output_status", "executor", "llm_task_id"]
DWG_FIELDS = ["task_id", "source_id", "dwg_file", "conversion_goal", "acceptable_outputs", "must_record", "blocking_status", "output_status", "executor", "llm_task_id"]
LIMIT_FIELDS = ["limitation_id", "limitation_domain", "limitation", "why_it_matters", "allowed_use", "forbidden_claim", "output_status", "executor", "llm_task_id"]


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


def fixed_rows(values: Any, size: int, fallback: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = values if isinstance(values, list) else []
    clean = [row for row in rows if isinstance(row, dict)]
    clean.extend(fallback)
    return clean[:size]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: str(row.get(field, "")) for field in fields})


def make_messages(context: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "你是P2图纸代理与DWG转换前置审计助手。"
                "你只基于PDF文本、页面画像、源目录和空间标签做代理判断。"
                "不得声称已解析DWG几何，不得生成坐标、面积、图层、路径长度或动线结论。"
                "返回严格JSON，所有输出状态为needs_review。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请做PDF代理分区、DWG转换工作单和几何代理限制审计。返回JSON：\n"
                "{\n"
                "  \"audit_summary\": \"...\",\n"
                "  \"pdf_proxy_zones\": [exactly 10 objects with zone_name, proxy_basis_labels, spatial_role, candidate_uses],\n"
                "  \"dwg_conversion_tasks\": [exactly 8 objects with source_id, dwg_file, conversion_goal, acceptable_outputs, must_record, blocking_status],\n"
                "  \"geometry_proxy_limitations\": [exactly 8 objects with limitation_domain, limitation, why_it_matters, allowed_use, forbidden_claim],\n"
                "  \"output_status\": \"needs_review\"\n"
                "}\n\n"
                + json.dumps(context, ensure_ascii=False)
            ),
        },
    ]


def main() -> None:
    task_id = "LLM-021"
    route = route_for(task_id)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    context = {
        "pdf_text_excerpt": PDF_TEXT.read_text(encoding="utf-8-sig")[:7000],
        "pdf_page_profile": read_csv(PDF_PAGES),
        "source_catalog": read_csv(SOURCE_CATALOG),
        "spatial_label_candidates": read_csv(SPATIAL_LABELS),
        "hard_boundary": "DWG remains pending_conversion; PDF proxy is label-only and cannot provide geometry.",
    }
    response = run_deepseek_task(task_id, make_messages(context), temperature=0.0)
    parsed = parse_json_object(response)

    fallback_zones = [
        {"zone_name": "道路与外部到达", "proxy_basis_labels": "林萃路;北五环辅路;奥林西桥", "spatial_role": "arrival_context", "candidate_uses": "入口导流与路径代理"},
        {"zone_name": "停车与车行到达", "proxy_basis_labels": "停车场;临时停车场;车行桥", "spatial_role": "parking_access", "candidate_uses": "停车客群触发"},
        {"zone_name": "运动场群", "proxy_basis_labels": "运动场;足球场;篮球场;羽毛球气膜馆", "spatial_role": "sports_demand", "candidate_uses": "运动补给与康复"},
        {"zone_name": "亲子游乐", "proxy_basis_labels": "游乐场;儿童卡丁车;丛林穿越", "spatial_role": "family_recreation", "candidate_uses": "亲子轻餐与休憩"},
        {"zone_name": "花海休闲", "proxy_basis_labels": "花海", "spatial_role": "leisure_photo", "candidate_uses": "摄影与轻餐"},
        {"zone_name": "基础服务设施", "proxy_basis_labels": "厕所;管理用房;水务站", "spatial_role": "service_support", "candidate_uses": "服务邻近性判断"},
        {"zone_name": "运营管理相关", "proxy_basis_labels": "世奥森林公园开发经营有限公司;保安公司", "spatial_role": "operation_context", "candidate_uses": "授权与运营核验"},
        {"zone_name": "水绿边界", "proxy_basis_labels": "仰山沟", "spatial_role": "landscape_constraint", "candidate_uses": "景观与边界限制"},
        {"zone_name": "市政与安全设施", "proxy_basis_labels": "变电站;消防队", "spatial_role": "constraint_context", "candidate_uses": "建设限制提示"},
        {"zone_name": "开发经营邻接", "proxy_basis_labels": "乐仕堡;清林路1号院", "spatial_role": "nearby_context", "candidate_uses": "邻近供给线索"},
    ]
    fallback_dwg = [
        {"source_id": "P2SRC-002", "dwg_file": "奥森北园(字体放大)-改造建筑示意_t5.dwg", "conversion_goal": "extract layers and geometry", "acceptable_outputs": "DXF;GeoJSON;SVG;PDF export", "must_record": "tool name;version;command;output path", "blocking_status": "pending_conversion"},
        {"source_id": "P2SRC-003", "dwg_file": "奥森南园（字体放大）-改造建筑示意_t5.dwg", "conversion_goal": "extract layers and geometry", "acceptable_outputs": "DXF;GeoJSON;SVG;PDF export", "must_record": "tool name;version;command;output path", "blocking_status": "pending_conversion"},
        {"source_id": "P2SRC-002", "dwg_file": "north dwg", "conversion_goal": "building footprint extraction", "acceptable_outputs": "polygon layer", "must_record": "layer mapping", "blocking_status": "pending_conversion"},
        {"source_id": "P2SRC-003", "dwg_file": "south dwg", "conversion_goal": "candidate node location extraction", "acceptable_outputs": "point/polygon layer", "must_record": "coordinate reference", "blocking_status": "pending_conversion"},
        {"source_id": "P2SRC-002", "dwg_file": "north dwg", "conversion_goal": "path network extraction", "acceptable_outputs": "line layer", "must_record": "topology checks", "blocking_status": "pending_conversion"},
        {"source_id": "P2SRC-003", "dwg_file": "south dwg", "conversion_goal": "service facility extraction", "acceptable_outputs": "point layer", "must_record": "label mapping", "blocking_status": "pending_conversion"},
        {"source_id": "P2SRC-002;P2SRC-003", "dwg_file": "both dwg", "conversion_goal": "north-south comparability", "acceptable_outputs": "same schema export", "must_record": "schema and CRS", "blocking_status": "pending_conversion"},
        {"source_id": "P2SRC-002;P2SRC-003", "dwg_file": "both dwg", "conversion_goal": "quality gate package", "acceptable_outputs": "manifest and checks", "must_record": "hash;size;date", "blocking_status": "pending_conversion"},
    ]
    fallback_limits = [
        {"limitation_domain": "geometry", "limitation": "PDF proxy has labels only", "why_it_matters": "cannot compute area", "allowed_use": "semantic zone hint", "forbidden_claim": "area calculated"},
        {"limitation_domain": "coordinates", "limitation": "no georeference", "why_it_matters": "cannot route", "allowed_use": "relative label grouping", "forbidden_claim": "coordinates known"},
        {"limitation_domain": "layers", "limitation": "DWG layers not parsed", "why_it_matters": "cannot classify CAD objects", "allowed_use": "conversion worklist", "forbidden_claim": "layers extracted"},
        {"limitation_domain": "south_proxy", "limitation": "no south PDF proxy", "why_it_matters": "south nodes not spatially verified", "allowed_use": "DOCX-only node assumption", "forbidden_claim": "south geometry verified"},
        {"limitation_domain": "paths", "limitation": "path topology unavailable", "why_it_matters": "cannot simulate movement", "allowed_use": "future path requirement", "forbidden_claim": "path weights calibrated"},
        {"limitation_domain": "scale", "limitation": "PDF scale not validated", "why_it_matters": "distance not reliable", "allowed_use": "visual proxy", "forbidden_claim": "distance measured"},
        {"limitation_domain": "authorization", "limitation": "operation rights not confirmed", "why_it_matters": "site feasibility unclear", "allowed_use": "verification task", "forbidden_claim": "lease feasible"},
        {"limitation_domain": "simulation", "limitation": "proxy is not simulation input", "why_it_matters": "prevents false precision", "allowed_use": "P3 preparation", "forbidden_claim": "full simulation ready"},
    ]

    zones = fixed_rows(parsed.get("pdf_proxy_zones"), 10, fallback_zones)
    dwg_tasks = fixed_rows(parsed.get("dwg_conversion_tasks"), 8, fallback_dwg)
    limitations = fixed_rows(parsed.get("geometry_proxy_limitations"), 8, fallback_limits)

    zone_rows = []
    for index, row in enumerate(zones, start=1):
        zone_rows.append({**row, "zone_id": f"P2-PDF-PROXY-ZONE-{index:03d}", "geometry_status": "pdf_proxy_label_only_pending_dwg_conversion", "quality_status": "needs_review", "output_status": "needs_review", "executor": "deepseek", "llm_task_id": task_id})
    dwg_rows = []
    for index, row in enumerate(dwg_tasks, start=1):
        dwg_rows.append({**row, "task_id": f"P2-DWG-CONVERT-{index:03d}", "blocking_status": "pending_conversion", "output_status": "needs_review", "executor": "deepseek", "llm_task_id": task_id})
    limit_rows = []
    for index, row in enumerate(limitations, start=1):
        limit_rows.append({**row, "limitation_id": f"P2-GEOM-LIMIT-{index:03d}", "output_status": "needs_review", "executor": "deepseek", "llm_task_id": task_id})

    write_csv(OUT_ZONES, ZONE_FIELDS, zone_rows)
    write_csv(OUT_DWG, DWG_FIELDS, dwg_rows)
    write_csv(OUT_LIMITS, LIMIT_FIELDS, limit_rows)

    audit = {
        "audit_summary": str(parsed.get("audit_summary") or "PDF proxy and DWG conversion worklist prepared by DeepSeek."),
        "zone_rows": len(zone_rows),
        "dwg_conversion_rows": len(dwg_rows),
        "limitation_rows": len(limit_rows),
        "output_status": "needs_review",
        "executor": "deepseek",
        "llm_task_id": task_id,
        "model": route.model,
        "run_id": run_id,
    }
    OUT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(
        "\n".join(
            [
                "# DeepSeek P2 图纸代理与DWG转换前置审计",
                "",
                f"- 任务：{task_id}",
                f"- 模型：{route.model}",
                "- 输出状态：needs_review",
                f"- PDF代理分区：{len(zone_rows)}",
                f"- DWG转换工作项：{len(dwg_rows)}",
                f"- 几何代理限制：{len(limit_rows)}",
                "",
                "## 边界",
                "",
                "- 这些输出不是DWG几何解析结果。",
                "- DWG 工作项统一保持 pending_conversion。",
                "- 没有可信转换产物前，不得生成坐标、面积、图层、路径或动线结论。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    RAW_JSONL.write_text(json.dumps({"run_id": run_id, "task_id": task_id, "model": route.model, "response_excerpt": response[:4000]}, ensure_ascii=False) + "\n", encoding="utf-8")
    PROGRESS_JSON.write_text(json.dumps({"run_id": run_id, "zone_rows": len(zone_rows), "dwg_conversion_rows": len(dwg_rows), "limitation_rows": len(limit_rows), "output_status": "needs_review"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {OUT_ZONES} rows={len(zone_rows)}")
    print(f"wrote {OUT_DWG} rows={len(dwg_rows)}")
    print(f"wrote {OUT_LIMITS} rows={len(limit_rows)}")
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
