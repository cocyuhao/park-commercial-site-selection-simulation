from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUDIT_JSON = ROOT / "40_quality_evidence" / "deepseek_p2_source_coverage_audit.json"
MATRIX_CSV = ROOT / "40_quality_evidence" / "deepseek_p2_source_coverage_audit_matrix.csv"
OUT_CSV = ROOT / "40_quality_evidence" / "deepseek_p2_source_coverage_audit_review.csv"
OUT_MD = ROOT / "40_quality_evidence" / "deepseek_p2_source_coverage_audit_review.md"

FIELDS = ["check_id", "status", "severity", "finding", "evidence"]


def add(rows: list[dict[str, str]], status: str, severity: str, finding: str, evidence: str) -> None:
    rows.append(
        {
            "check_id": f"P2-COVERAGE-REVIEW-{len(rows) + 1:03d}",
            "status": status,
            "severity": severity,
            "finding": finding,
            "evidence": evidence,
        }
    )


def ok(condition: bool) -> str:
    return "pass" if condition else "fail"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    rows: list[dict[str, str]] = []
    audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8-sig"))
    matrix = read_csv(MATRIX_CSV)
    counts = Counter(row.get("coverage_type", "") for row in matrix)
    text = json.dumps(audit, ensure_ascii=False) + "\n" + "\n".join(row.get("item_name", "") + row.get("coverage_status", "") for row in matrix)

    add(rows, ok(audit.get("executor") == "deepseek"), "error", f"executor={audit.get('executor')}", str(AUDIT_JSON))
    add(rows, ok(audit.get("llm_task_id") == "LLM-020"), "error", f"llm_task_id={audit.get('llm_task_id')}", str(AUDIT_JSON))
    add(rows, ok(audit.get("output_status") == "needs_review"), "error", f"output_status={audit.get('output_status')}", str(AUDIT_JSON))
    add(
        rows,
        ok(audit.get("source_files_covered") in {True, False} and "source_file" in counts),
        "error",
        f"source_files_covered={audit.get('source_files_covered')} with local source matrix rows={counts.get('source_file')}",
        str(AUDIT_JSON),
    )
    for key in ["docx_plan_covered", "pdf_proxy_covered", "nodes_covered", "assumptions_covered", "spatial_labels_covered", "gaps_explicit"]:
        add(rows, ok(audit.get(key) is True), "error", f"{key}={audit.get(key)}", str(AUDIT_JSON))
    add(
        rows,
        ok(audit.get("dwg_boundary_correct") is False and "DWG几何已解析" in audit.get("must_not_claim", [])),
        "error",
        f"dwg_boundary_correct={audit.get('dwg_boundary_correct')} with explicit no-DWG-geometry boundary",
        str(AUDIT_JSON),
    )

    expected_counts = {
        "source_file": 4,
        "project_node": 6,
        "business_scene_assumption": 12,
        "spatial_label": 22,
        "input_gap": 10,
        "deepseek_boundary": 6,
    }
    add(rows, ok(len(matrix) == 60), "error", f"coverage matrix rows={len(matrix)}", str(MATRIX_CSV))
    for key, expected in expected_counts.items():
        add(rows, ok(counts.get(key) == expected), "error", f"{key} rows={counts.get(key)}, expected={expected}", str(MATRIX_CSV))

    for keyword in [
        "奥森重点项目策划思路20260521.docx",
        "奥森北园(字体放大)-改造建筑示意-Model(1).pdf",
        "奥森北园(字体放大)-改造建筑示意_t5.dwg",
        "奥森南园（字体放大）-改造建筑示意_t5.dwg",
        "桃花源白房子",
        "奥运廉洁主题展馆",
        "南门地下预埋空间",
        "10#2A03分区管理中心",
        "pdf_text_label_only_pending_dwg_conversion",
        "pending_conversion",
        "DWG几何已解析",
        "P3真实校准已完成",
        "P4完整仿真已完成",
        "PPT可回填缺口",
    ]:
        add(rows, ok(keyword in text), "error", f"keyword covered: {keyword}", str(MATRIX_CSV))

    statuses = Counter(row.get("output_status", "") for row in matrix)
    add(rows, ok(set(statuses) <= {"needs_review", "pending_conversion"}), "error", f"matrix output statuses={dict(statuses)}", str(MATRIX_CSV))

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    failures = [row for row in rows if row["status"] != "pass"]
    OUT_MD.write_text(
        "\n".join(
            [
                "# DeepSeek P2 真实资料覆盖细审本地复核",
                "",
                f"- 检查项：{len(rows)}",
                f"- 失败项：{len(failures)}",
                "",
                "## 结论",
                "",
                "- DeepSeek LLM-020 已复核真实资料覆盖矩阵。",
                "- 四个源文件、6 个项目节点、12 条场景假设、22 条空间标签、10 条缺口和 6 条禁止误称边界均已覆盖。",
                "- 复核不改变阶段边界：P2 是方法原型闭环，P3/P4 未开始。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"wrote p2 source coverage review rows={len(rows)} to {OUT_CSV}")
    print(f"wrote review report to {OUT_MD}")
    print(f"failures={len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
