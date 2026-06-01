from __future__ import annotations

import csv
import json
import shutil
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

import fitz


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR_MARKER = "CAD"
EXTRACTION_DIR = ROOT / "30_extraction" / "p2_real_site"
QUALITY_DIR = ROOT / "40_quality_evidence"
OUTPUT_TABLE_DIR = ROOT / "70_outputs" / "processed_tables"

DOCX_TEXT = EXTRACTION_DIR / "osen_project_plan_text.txt"
DOCX_PROFILE = EXTRACTION_DIR / "osen_project_plan_profile.json"
PDF_TEXT = EXTRACTION_DIR / "osen_north_cad_pdf_text.txt"
PDF_PAGES = EXTRACTION_DIR / "osen_north_cad_pdf_pages.csv"
SOURCE_CATALOG = QUALITY_DIR / "p2_real_site_source_catalog.csv"
INPUT_WORKLIST = OUTPUT_TABLE_DIR / "p2_real_site_input_worklist.csv"
SIM_INPUT_REQUIREMENTS = OUTPUT_TABLE_DIR / "p2_simulation_input_requirements.csv"
PREP_REPORT = QUALITY_DIR / "p2_real_site_preparation_report.md"

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

DWG_VERSIONS = {
    "AC1006": "AutoCAD R10",
    "AC1009": "AutoCAD R11/R12",
    "AC1012": "AutoCAD R13",
    "AC1014": "AutoCAD R14",
    "AC1015": "AutoCAD 2000/2000i/2002",
    "AC1018": "AutoCAD 2004/2005/2006",
    "AC1021": "AutoCAD 2007/2008/2009",
    "AC1024": "AutoCAD 2010/2011/2012",
    "AC1027": "AutoCAD 2013/2014/2015/2016/2017",
    "AC1032": "AutoCAD 2018/2019/2020/2021/2022/2023/2024/2025",
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def find_source_dir() -> Path:
    candidates = [
        path
        for path in ROOT.iterdir()
        if path.is_dir() and SOURCE_DIR_MARKER in path.name and any(child.suffix.lower() in {".docx", ".pdf", ".dwg"} for child in path.iterdir())
    ]
    if not candidates:
        raise FileNotFoundError("Cannot locate P2 source directory with DOCX/PDF/DWG files.")
    if len(candidates) > 1:
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def text_from_paragraph(paragraph: ET.Element) -> str:
    chunks = [node.text or "" for node in paragraph.findall(".//w:t", NS)]
    return "".join(chunks).strip()


def extract_docx_text(path: Path) -> dict[str, object]:
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    body = root.find("w:body", NS)
    if body is None:
        raise ValueError("DOCX document.xml has no body.")

    lines: list[str] = []
    paragraph_count = 0
    table_count = 0
    headings: list[str] = []

    for child in body:
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            text = text_from_paragraph(child)
            if text:
                paragraph_count += 1
                style_node = child.find(".//w:pStyle", NS)
                style = style_node.attrib.get(f"{{{NS['w']}}}val", "") if style_node is not None else ""
                if style.lower().startswith("heading") or style.startswith("标题"):
                    headings.append(text)
                    lines.append(f"# {text}")
                else:
                    lines.append(text)
        elif tag == "tbl":
            table_count += 1
            lines.append(f"[TABLE {table_count}]")
            for row in child.findall(".//w:tr", NS):
                cells = []
                for cell in row.findall("./w:tc", NS):
                    cell_text = " ".join(filter(None, (text_from_paragraph(p) for p in cell.findall("./w:p", NS))))
                    cells.append(cell_text)
                if any(cells):
                    lines.append("\t".join(cells))

    text = "\n".join(lines).strip() + "\n"
    DOCX_TEXT.write_text(text, encoding="utf-8")

    keywords = ["商业", "业态", "节点", "北园", "南园", "改造", "游客", "运营", "服务", "场景", "入口", "停车", "体育", "咖啡", "餐饮"]
    counts = {keyword: text.count(keyword) for keyword in keywords}
    profile = {
        "source_file": rel(path),
        "output_status": "extracted_local",
        "text_output": rel(DOCX_TEXT),
        "bytes": path.stat().st_size,
        "character_count": len(text),
        "nonempty_line_count": sum(1 for line in text.splitlines() if line.strip()),
        "paragraph_count": paragraph_count,
        "table_count": table_count,
        "heading_count": len(headings),
        "headings_sample": headings[:30],
        "keyword_counts": counts,
        "p2_use": [
            "project_objective",
            "planning_scope",
            "business_format_assumptions",
            "node_or_scene_assumptions",
            "input_gap_check",
        ],
        "limitations": [
            "DOCX text is planning material, not final measured operation data.",
            "Numbers or claims still need evidence catalog linkage before final recommendations.",
        ],
    }
    DOCX_PROFILE.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return profile


def extract_pdf_pages(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    text_parts: list[str] = []
    with fitz.open(path) as doc:
        for page_index, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            blocks = page.get_text("blocks")
            image_count = len(page.get_images(full=True))
            try:
                drawing_count = len(page.get_drawings())
            except Exception:
                drawing_count = -1
            rect = page.rect
            rows.append(
                {
                    "page": page_index,
                    "width_pt": round(rect.width, 2),
                    "height_pt": round(rect.height, 2),
                    "rotation": page.rotation,
                    "text_length": len(text),
                    "text_line_count": len([line for line in text.splitlines() if line.strip()]),
                    "text_block_count": len(blocks),
                    "image_count": image_count,
                    "vector_drawing_count": drawing_count,
                    "has_extractable_text": "yes" if text else "no",
                    "page_use_status": "cad_readable_proxy" if text or drawing_count else "needs_visual_review",
                }
            )
            text_parts.append(f"\n\n===== PAGE {page_index} =====\n{text}")
    PDF_TEXT.write_text("\n".join(text_parts).strip() + "\n", encoding="utf-8")
    write_csv(PDF_PAGES, rows)
    return rows


def read_dwg_header(path: Path) -> tuple[str, str]:
    with path.open("rb") as f:
        header = f.read(6).decode("ascii", errors="replace")
    return header, DWG_VERSIONS.get(header, "unknown_dwg_version")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def file_modified_iso(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def build_catalog(source_dir: Path, docx_profile: dict[str, object], pdf_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    converter_candidates = ["ODAFileConverter", "accoreconsole", "dwg2dxf"]
    available_converters = [name for name in converter_candidates if shutil.which(name)]
    rows: list[dict[str, object]] = []

    source_files = [path for path in source_dir.iterdir() if not path.name.startswith("~$")]
    for index, path in enumerate(sorted(source_files, key=lambda p: p.name), start=1):
        if not path.is_file() or path.suffix.lower() not in {".docx", ".pdf", ".dwg"}:
            continue
        source_id = f"P2SRC-{index:03d}"
        suffix = path.suffix.lower()
        base = {
            "source_id": source_id,
            "source_file": rel(path),
            "file_name": path.name,
            "source_type": suffix.lstrip("."),
            "bytes": path.stat().st_size,
            "modified_time": file_modified_iso(path),
            "output_status": "",
            "extraction_method": "",
            "primary_output": "",
            "secondary_output": "",
            "page_or_record_count": "",
            "dwg_header": "",
            "dwg_version": "",
            "source_strength": "",
            "p2_use_status": "",
            "limitation": "",
        }
        if suffix == ".docx":
            base.update(
                {
                    "output_status": "extracted_local",
                    "extraction_method": "docx_zip_xml_text",
                    "primary_output": rel(DOCX_TEXT),
                    "secondary_output": rel(DOCX_PROFILE),
                    "page_or_record_count": docx_profile.get("nonempty_line_count", ""),
                    "source_strength": "planning_material",
                    "p2_use_status": "use_for_objective_scope_and_assumption_breakdown",
                    "limitation": "Not measured operation data; claims need evidence linkage before final recommendation.",
                }
            )
        elif suffix == ".pdf":
            base.update(
                {
                    "output_status": "extracted_local",
                    "extraction_method": "pymupdf_text_and_page_profile",
                    "primary_output": rel(PDF_TEXT),
                    "secondary_output": rel(PDF_PAGES),
                    "page_or_record_count": len(pdf_rows),
                    "source_strength": "cad_pdf_proxy",
                    "p2_use_status": "use_as_north_cad_readable_proxy_before_dwg_conversion",
                    "limitation": "PDF is a readable proxy for the north CAD drawing; geometry must not be treated as parsed DWG geometry.",
                }
            )
        elif suffix == ".dwg":
            header, version = read_dwg_header(path)
            base.update(
                {
                    "output_status": "pending_conversion",
                    "extraction_method": "dwg_header_only",
                    "page_or_record_count": 1,
                    "dwg_header": header,
                    "dwg_version": version,
                    "source_strength": "cad_source_file",
                    "p2_use_status": "pending_conversion_before_geometry_or_layer_use",
                    "limitation": "No DWG geometry/layer parsing has been performed. Available converters on PATH: "
                    + (", ".join(available_converters) if available_converters else "none"),
                }
            )
        rows.append(base)
    write_csv(SOURCE_CATALOG, rows)
    return rows


def build_worklist(catalog_rows: list[dict[str, object]], docx_profile: dict[str, object], pdf_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    row_by_type = {row["source_type"]: row for row in catalog_rows}
    dwg_rows = [row for row in catalog_rows if row["source_type"] == "dwg"]
    docx_id = row_by_type.get("docx", {}).get("source_id", "")
    pdf_id = row_by_type.get("pdf", {}).get("source_id", "")
    rows = [
        {
            "work_item_id": "P2-WORK-001",
            "source_id": docx_id,
            "work_category": "project_scope",
            "work_item": "Extract planning objective, target park scope, and project positioning from DOCX.",
            "current_status": "ready_for_semantic_breakdown",
            "output_status": "needs_review",
            "blocking_level": "important",
            "next_action": "Use extracted text to draft objective/scope assumptions, then review against source lines.",
            "evidence_output": rel(DOCX_TEXT),
        },
        {
            "work_item_id": "P2-WORK-002",
            "source_id": docx_id,
            "work_category": "business_format",
            "work_item": "Break down planned formats, nodes, scenes, and operational assumptions from DOCX.",
            "current_status": "ready_for_semantic_breakdown",
            "output_status": "needs_review",
            "blocking_level": "important",
            "next_action": "Generate a structured assumption pool; keep assumptions separate from measured evidence.",
            "evidence_output": rel(DOCX_PROFILE),
        },
        {
            "work_item_id": "P2-WORK-003",
            "source_id": pdf_id,
            "work_category": "north_cad_proxy",
            "work_item": "Use north CAD PDF text/page profile as readable proxy for drawing pages.",
            "current_status": "ready_for_manual_page_review",
            "output_status": "needs_review",
            "blocking_level": "important",
            "next_action": "Review high-text and high-vector pages, identify candidate nodes/labels to map after DWG conversion.",
            "evidence_output": rel(PDF_PAGES),
        },
    ]
    for offset, row in enumerate(dwg_rows, start=4):
        rows.append(
            {
                "work_item_id": f"P2-WORK-{offset:03d}",
                "source_id": row["source_id"],
                "work_category": "dwg_conversion",
                "work_item": f"Convert or inspect DWG geometry/layers for {row['file_name']}.",
                "current_status": "pending_conversion",
                "output_status": "pending_conversion",
                "blocking_level": "blocking_for_geometry_not_for_text_index",
                "next_action": "Install/use trusted DWG converter or request DXF/PDF export; do not claim geometry parsing before conversion.",
                "evidence_output": rel(SOURCE_CATALOG),
            }
        )
    rows.extend(
        [
            {
                "work_item_id": "P2-WORK-006",
                "source_id": f"{docx_id};{pdf_id}",
                "work_category": "input_gap_check",
                "work_item": "Check whether current real-site materials support simulation inputs without PPT.",
                "current_status": "prepared",
                "output_status": "needs_review",
                "blocking_level": "important",
                "next_action": "Use p2_simulation_input_requirements.csv as the gate before building the simulation prototype.",
                "evidence_output": rel(SIM_INPUT_REQUIREMENTS),
            },
            {
                "work_item_id": "P2-WORK-007",
                "source_id": docx_id,
                "work_category": "project_drift_check",
                "work_item": "Compare real project objective against existing park commercial simulation objective.",
                "current_status": "prepared",
                "output_status": "needs_review",
                "blocking_level": "important",
                "next_action": "Confirm whether the objective remains site selection simulation or shifts to renovation/project planning support.",
                "evidence_output": rel(PREP_REPORT),
            },
        ]
    )
    write_csv(INPUT_WORKLIST, rows)
    return rows


def build_requirements(catalog_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    catalog_by_type = defaultdict_list(catalog_rows, "source_type")
    docx_ids = ";".join(row["source_id"] for row in catalog_by_type.get("docx", []))
    pdf_ids = ";".join(row["source_id"] for row in catalog_by_type.get("pdf", []))
    dwg_ids = ";".join(row["source_id"] for row in catalog_by_type.get("dwg", []))
    rows = [
        {
            "requirement_id": "P2-REQ-001",
            "input_domain": "project_scope",
            "input_field": "target_area_and_project_objective",
            "source_support": docx_ids,
            "current_status": "available_as_planning_text",
            "planned_transform": "semantic_extract_then_human_review",
            "quality_gate": "must cite DOCX source lines and mark assumptions separately",
            "notes": "Used to check whether the project objective shifts from generic site-selection simulation.",
        },
        {
            "requirement_id": "P2-REQ-002",
            "input_domain": "spatial_nodes",
            "input_field": "candidate_building_or_activity_nodes",
            "source_support": f"{pdf_ids};{dwg_ids}",
            "current_status": "partial_pdf_proxy_pending_dwg_conversion",
            "planned_transform": "manual_page_review_then_dwg_or_dxf_geometry_parse",
            "quality_gate": "DWG geometry/layers must remain pending until converter output exists",
            "notes": "North PDF can provide labels/page profile; north/south DWG geometry not parsed yet.",
        },
        {
            "requirement_id": "P2-REQ-003",
            "input_domain": "business_formats",
            "input_field": "planned_formats_and_scene_assumptions",
            "source_support": docx_ids,
            "current_status": "available_as_assumption_source",
            "planned_transform": "assumption_pool_with_output_status_needs_review",
            "quality_gate": "do not write into checked evidence without independent confirmation",
            "notes": "PPT is intentionally excluded from this P2 preparation main line.",
        },
        {
            "requirement_id": "P2-REQ-004",
            "input_domain": "geometry",
            "input_field": "site_boundaries_layers_areas_paths",
            "source_support": dwg_ids,
            "current_status": "pending_conversion",
            "planned_transform": "DWG to DXF/SVG/GeoJSON or trusted CAD export",
            "quality_gate": "must record converter/tool/version and output file before geometry use",
            "notes": "No geometry calculation has been performed in this step.",
        },
        {
            "requirement_id": "P2-REQ-005",
            "input_domain": "simulation_parameters",
            "input_field": "visitor_flow_conversion_rate_revenue_cost",
            "source_support": "",
            "current_status": "not_provided_by_real_site_cad_plan_package",
            "planned_transform": "link to evidence_ledger or future measured/official data",
            "quality_gate": "blank values stay blank; no PPT backfill by default",
            "notes": "Current package mainly supports scope, plan assumptions, and spatial preparation, not demand/revenue calibration.",
        },
        {
            "requirement_id": "P2-REQ-006",
            "input_domain": "quality_gate",
            "input_field": "source_catalog_and_input_worklist",
            "source_support": ";".join(row["source_id"] for row in catalog_rows),
            "current_status": "available",
            "planned_transform": "verify_project_implementation.py gate",
            "quality_gate": "source catalog 4 rows, worklist 7 rows, requirements 6 rows, DWG pending_conversion preserved",
            "notes": "This requirement keeps P2 preparation separate from full simulation execution.",
        },
    ]
    write_csv(SIM_INPUT_REQUIREMENTS, rows)
    return rows


def defaultdict_list(rows: list[dict[str, object]], key: str) -> dict[str, list[dict[str, object]]]:
    result: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        result.setdefault(str(row.get(key, "")), []).append(row)
    return result


def write_report(
    source_dir: Path,
    catalog_rows: list[dict[str, object]],
    docx_profile: dict[str, object],
    pdf_rows: list[dict[str, object]],
    worklist_rows: list[dict[str, object]],
    requirement_rows: list[dict[str, object]],
) -> None:
    status_counts = Counter(row["output_status"] for row in catalog_rows)
    dwg_rows = [row for row in catalog_rows if row["source_type"] == "dwg"]
    pdf_text_total = sum(int(row["text_length"]) for row in pdf_rows)
    lines = [
        "# P2 真实资料准备报告",
        "",
        "## 结论",
        "",
        "- 本轮进入的是 `P2 准备`，不是完整仿真建模。",
        "- 已对 `CAD图及其计划` 中的 DOCX、PDF、DWG 建立可追踪输入索引。",
        "- DOCX 已完成文本抽取，可用于项目目标、策划内容、业态/节点/场景假设拆解。",
        "- 北园 PDF 已完成文本抽取和页面画像，可作为北园 CAD 的可读代理。",
        "- DWG 仅完成文件级登记和版本头识别，几何/图层解析状态保持 `pending_conversion`。",
        "- 本轮 P2 主线不使用 PPT；PPT 后续仅在明确需要时作为弱假设或待核验线索。",
        "",
        "## 输入资料",
        "",
        f"- 来源目录：`{rel(source_dir)}`",
        f"- 文件数：{len(catalog_rows)}",
        f"- 状态统计：{dict(status_counts)}",
        "",
        "## 抽取结果",
        "",
        f"- DOCX 文本：`{rel(DOCX_TEXT)}`，字符数 {docx_profile.get('character_count')}，非空行 {docx_profile.get('nonempty_line_count')}。",
        f"- DOCX 画像：`{rel(DOCX_PROFILE)}`。",
        f"- PDF 文本：`{rel(PDF_TEXT)}`，页数 {len(pdf_rows)}，可抽取文本总长度 {pdf_text_total}。",
        f"- PDF 页面画像：`{rel(PDF_PAGES)}`。",
        f"- 资料目录：`{rel(SOURCE_CATALOG)}`。",
        f"- P2 输入工作单：`{rel(INPUT_WORKLIST)}`，{len(worklist_rows)} 条。",
        f"- P2 仿真输入需求表：`{rel(SIM_INPUT_REQUIREMENTS)}`，{len(requirement_rows)} 条。",
        "",
        "## DWG 状态",
        "",
    ]
    for row in dwg_rows:
        lines.append(
            f"- `{row['file_name']}`：header `{row['dwg_header']}`，版本 `{row['dwg_version']}`，状态 `{row['output_status']}`。"
        )
    lines.extend(
        [
            "",
            "## P2 使用边界",
            "",
            "- 可以使用：DOCX 目标与策划文本、PDF 页面标签/文字、DWG 文件存在性和版本头。",
            "- 暂不可使用：DWG 几何面积、图层、坐标、动线长度、建筑边界和南北园可比空间量。",
            "- 仍需补充：可信 DWG 转换结果、节点/建筑/业态结构化表、真实客流/转化/收益/成本校准数据。",
            "- 下一步建议：先做 DOCX 语义拆解和 PDF 页面对照复核，再决定是否安装/使用 DWG 转换器。",
            "",
        ]
    )
    PREP_REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    EXTRACTION_DIR.mkdir(parents=True, exist_ok=True)
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_TABLE_DIR.mkdir(parents=True, exist_ok=True)

    source_dir = find_source_dir()
    files = [path for path in source_dir.iterdir() if not path.name.startswith("~$")]
    docx_files = [path for path in files if path.suffix.lower() == ".docx" and not path.name.startswith("~$")]
    pdf_files = [path for path in files if path.suffix.lower() == ".pdf"]
    if len(docx_files) != 1:
        raise RuntimeError(f"Expected exactly 1 DOCX, found {len(docx_files)}.")
    if len(pdf_files) != 1:
        raise RuntimeError(f"Expected exactly 1 PDF, found {len(pdf_files)}.")

    docx_profile = extract_docx_text(docx_files[0])
    pdf_rows = extract_pdf_pages(pdf_files[0])
    catalog_rows = build_catalog(source_dir, docx_profile, pdf_rows)
    worklist_rows = build_worklist(catalog_rows, docx_profile, pdf_rows)
    requirement_rows = build_requirements(catalog_rows)
    write_report(source_dir, catalog_rows, docx_profile, pdf_rows, worklist_rows, requirement_rows)

    print(f"wrote {rel(DOCX_TEXT)} bytes={DOCX_TEXT.stat().st_size}")
    print(f"wrote {rel(DOCX_PROFILE)} bytes={DOCX_PROFILE.stat().st_size}")
    print(f"wrote {rel(PDF_TEXT)} bytes={PDF_TEXT.stat().st_size}")
    print(f"wrote {rel(PDF_PAGES)} rows={len(pdf_rows)}")
    print(f"wrote {rel(SOURCE_CATALOG)} rows={len(catalog_rows)}")
    print(f"wrote {rel(INPUT_WORKLIST)} rows={len(worklist_rows)}")
    print(f"wrote {rel(SIM_INPUT_REQUIREMENTS)} rows={len(requirement_rows)}")
    print(f"wrote {rel(PREP_REPORT)} bytes={PREP_REPORT.stat().st_size}")


if __name__ == "__main__":
    main()
