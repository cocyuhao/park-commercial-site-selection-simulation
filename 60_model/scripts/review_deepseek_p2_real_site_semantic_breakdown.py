from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCX_ROWS = ROOT / "70_outputs" / "processed_tables" / "p2_docx_project_semantic_draft_deepseek.csv"
PDF_ROWS = ROOT / "70_outputs" / "processed_tables" / "p2_pdf_spatial_label_draft_deepseek.csv"
PROGRESS_JSON = ROOT / "60_model" / "llm_runs" / "deepseek_p2_real_site_semantic_progress.json"
OUT_REVIEW = ROOT / "40_quality_evidence" / "deepseek_p2_real_site_semantic_review.csv"
REPORT = ROOT / "40_quality_evidence" / "deepseek_p2_real_site_semantic_review.md"

REVIEW_FIELDS = ["check_id", "status", "severity", "finding", "evidence"]
DOCX_TYPES = {
    "project_scope",
    "business_format",
    "spatial_node",
    "scene_assumption",
    "cooperation_mode",
    "renovation_suggestion",
    "benchmark_case",
    "risk_or_constraint",
}
PDF_TYPES = {
    "road",
    "parking",
    "sports",
    "facility",
    "service",
    "building",
    "recreation",
    "water_green",
    "bridge_or_gate",
    "other",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def ok(condition: bool) -> str:
    return "pass" if condition else "fail"


def add(rows: list[dict[str, str]], status: str, severity: str, finding: str, evidence: str) -> None:
    rows.append(
        {
            "check_id": f"P2-SEMANTIC-REVIEW-{len(rows) + 1:03d}",
            "status": status,
            "severity": severity,
            "finding": finding,
            "evidence": evidence,
        }
    )


def main() -> None:
    docx = read_csv(DOCX_ROWS) if DOCX_ROWS.exists() else []
    pdf = read_csv(PDF_ROWS) if PDF_ROWS.exists() else []
    progress = json.loads(PROGRESS_JSON.read_text(encoding="utf-8-sig")) if PROGRESS_JSON.exists() else {}
    review: list[dict[str, str]] = []

    docx_statuses = Counter(row.get("output_status", "") for row in docx)
    pdf_statuses = Counter(row.get("output_status", "") for row in pdf)
    docx_exec = Counter(row.get("executor", "") for row in docx)
    pdf_exec = Counter(row.get("executor", "") for row in pdf)
    docx_tasks = Counter(row.get("llm_task_id", "") for row in docx)
    pdf_tasks = Counter(row.get("llm_task_id", "") for row in pdf)
    docx_types = {row.get("semantic_type", "") for row in docx}
    pdf_types = {row.get("label_type", "") for row in pdf}
    geometry_statuses = Counter(row.get("geometry_status", "") for row in pdf)
    docx_projects = {row.get("project_name", "") for row in docx if row.get("project_name", "")}
    required_docx_keywords = ["桃花源", "奥运廉洁主题展馆", "中医", "烘焙"]
    required_pdf_labels = ["停车场", "运动场", "篮球场", "足球场", "花海"]
    pdf_label_text = "\n".join(row.get("label_text", "") for row in pdf)

    add(review, ok(len(docx) >= 18), "error", f"DOCX semantic rows={len(docx)}", str(DOCX_ROWS))
    add(review, ok(len(pdf) >= 18), "error", f"PDF spatial label rows={len(pdf)}", str(PDF_ROWS))
    add(review, ok(docx_statuses == {"needs_review": len(docx)}), "error", f"DOCX output statuses={dict(docx_statuses)}", str(DOCX_ROWS))
    add(review, ok(pdf_statuses == {"needs_review": len(pdf)}), "error", f"PDF output statuses={dict(pdf_statuses)}", str(PDF_ROWS))
    add(review, ok(docx_exec == {"deepseek": len(docx)} and pdf_exec == {"deepseek": len(pdf)}), "error", f"executors docx={dict(docx_exec)}, pdf={dict(pdf_exec)}", "executor")
    add(review, ok(docx_tasks == {"LLM-017": len(docx)} and pdf_tasks == {"LLM-017": len(pdf)}), "error", f"task ids docx={dict(docx_tasks)}, pdf={dict(pdf_tasks)}", "llm_task_id")
    add(review, ok(docx_types <= DOCX_TYPES), "error", f"DOCX semantic types={sorted(docx_types)}", "semantic_type")
    add(review, ok(pdf_types <= PDF_TYPES), "error", f"PDF label types={sorted(pdf_types)}", "label_type")
    add(review, ok(geometry_statuses == {"pdf_text_label_only_pending_dwg_conversion": len(pdf)}), "error", f"PDF geometry statuses={dict(geometry_statuses)}", "geometry_status")
    add(review, ok(all(any(keyword in project for project in docx_projects) or any(keyword in row.get("extracted_value", "") for row in docx) for keyword in required_docx_keywords)), "error", f"DOCX required themes checked={required_docx_keywords}", "docx themes")
    add(review, ok(all(label in pdf_label_text for label in required_pdf_labels)), "error", f"PDF required labels checked={required_pdf_labels}", "pdf labels")
    add(review, ok(progress.get("output_status") == "needs_review"), "error", f"progress output_status={progress.get('output_status')}", str(PROGRESS_JSON))

    write_csv(OUT_REVIEW, review)
    status_counts = Counter(row["status"] for row in review)
    REPORT.write_text(
        "\n".join(
            [
                "# DeepSeek P2 真实资料语义拆解本地复核报告",
                "",
                "## 结论",
                "",
                f"- 复核项状态：{dict(sorted(status_counts.items()))}",
                f"- DOCX 语义拆解行数：{len(docx)}。",
                f"- PDF 空间标签行数：{len(pdf)}。",
                "- 所有输出仍为 `needs_review`，不得直接进入 checked 证据或完整仿真建模。",
                "- PDF 标签仅为文本线索，DWG 几何仍保持 pending_conversion。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    failures = [row for row in review if row["status"] == "fail"]
    print(f"wrote p2 semantic review rows={len(review)} to {OUT_REVIEW}")
    print(f"wrote review report to {REPORT}")
    print(f"failures={len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
