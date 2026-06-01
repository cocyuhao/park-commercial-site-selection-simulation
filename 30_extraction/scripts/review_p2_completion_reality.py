from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_CSV = ROOT / "40_quality_evidence" / "p2_completion_reality_audit.csv"
OUT_MD = ROOT / "40_quality_evidence" / "p2_completion_reality_audit.md"

FIELDS = ["check_id", "status", "severity", "finding", "evidence"]


def add(rows: list[dict[str, str]], status: str, severity: str, finding: str, evidence: str) -> None:
    rows.append(
        {
            "check_id": f"P2-REALITY-{len(rows) + 1:03d}",
            "status": status,
            "severity": severity,
            "finding": finding,
            "evidence": evidence,
        }
    )


def ok(condition: bool) -> str:
    return "pass" if condition else "fail"


def read_csv(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value)


def main() -> None:
    rows: list[dict[str, str]] = []

    catalog = read_csv("40_quality_evidence/p2_real_site_source_catalog.csv")
    worklist = read_csv("70_outputs/processed_tables/p2_real_site_input_worklist.csv")
    requirements = read_csv("70_outputs/processed_tables/p2_simulation_input_requirements.csv")
    docx_semantics = read_csv("70_outputs/processed_tables/p2_docx_project_semantic_draft_deepseek.csv")
    nodes = read_csv("70_outputs/processed_tables/p2_project_node_candidates.csv")
    assumptions = read_csv("70_outputs/processed_tables/p2_business_scene_assumption_pool.csv")
    pdf_labels = read_csv("70_outputs/processed_tables/p2_spatial_label_candidates.csv")
    gaps = read_csv("70_outputs/processed_tables/p2_input_gap_register.csv")
    method_scores = read_csv("70_outputs/processed_tables/p2_candidate_method_readiness_scores.csv")

    profile = json.loads(text("30_extraction/p2_real_site/osen_project_plan_profile.json"))
    plan_text = text("30_extraction/p2_real_site/osen_project_plan_text.txt")
    pdf_text = text("30_extraction/p2_real_site/osen_north_cad_pdf_text.txt")
    agent_text = text("AGENTS.md")
    handoff_text = text("handoff_next_chat.md")

    add(rows, ok(len(catalog) == 4), "error", f"source catalog rows={len(catalog)}", "40_quality_evidence/p2_real_site_source_catalog.csv")
    expected_files = {
        "奥森重点项目策划思路20260521.docx",
        "奥森北园(字体放大)-改造建筑示意-Model(1).pdf",
        "奥森北园(字体放大)-改造建筑示意_t5.dwg",
        "奥森南园（字体放大）-改造建筑示意_t5.dwg",
    }
    add(rows, ok({row["file_name"] for row in catalog} == expected_files), "error", "all four user-provided source files registered", "40_quality_evidence/p2_real_site_source_catalog.csv")
    status_counts = Counter(row["output_status"] for row in catalog)
    add(rows, ok(status_counts == {"extracted_local": 2, "pending_conversion": 2}), "error", f"source status counts={dict(status_counts)}", "40_quality_evidence/p2_real_site_source_catalog.csv")
    dwg_rows = [row for row in catalog if row["source_type"] == "dwg"]
    add(rows, ok(len(dwg_rows) == 2 and all(row["dwg_header"] == "AC1018" for row in dwg_rows)), "error", f"DWG headers={[row['dwg_header'] for row in dwg_rows]}", "40_quality_evidence/p2_real_site_source_catalog.csv")
    add(rows, ok(all("No DWG geometry/layer parsing" in row["limitation"] for row in dwg_rows)), "error", "DWG geometry is explicitly not claimed", "40_quality_evidence/p2_real_site_source_catalog.csv")

    add(rows, ok(profile.get("nonempty_line_count") == 183), "error", f"DOCX nonempty_line_count={profile.get('nonempty_line_count')}", "30_extraction/p2_real_site/osen_project_plan_profile.json")
    add(rows, ok(profile.get("table_count") == 7), "error", f"DOCX table_count={profile.get('table_count')}", "30_extraction/p2_real_site/osen_project_plan_profile.json")
    for keyword in ["奥森重点项目策划思路", "桃花源", "奥运廉洁主题展馆", "南门地下预埋", "保底租金+营业额抽成"]:
        add(rows, ok(keyword in plan_text), "error", f"DOCX text contains {keyword}", "30_extraction/p2_real_site/osen_project_plan_text.txt")

    compact_pdf_text = compact(pdf_text)
    for keyword in ["林萃", "北五环辅路", "停车场", "足球场", "篮球场", "花海"]:
        add(rows, ok(keyword in compact_pdf_text), "error", f"PDF text contains {keyword} after whitespace normalization", "30_extraction/p2_real_site/osen_north_cad_pdf_text.txt")

    add(rows, ok(len(worklist) == 7), "error", f"worklist rows={len(worklist)}", "70_outputs/processed_tables/p2_real_site_input_worklist.csv")
    add(rows, ok(len(requirements) == 6), "error", f"input requirement rows={len(requirements)}", "70_outputs/processed_tables/p2_simulation_input_requirements.csv")
    add(rows, ok(len(docx_semantics) == 21 and {row["executor"] for row in docx_semantics} == {"deepseek"}), "error", "DOCX semantic DeepSeek rows=21", "70_outputs/processed_tables/p2_docx_project_semantic_draft_deepseek.csv")
    add(rows, ok(len(nodes) == 6), "error", f"project node rows={len(nodes)}", "70_outputs/processed_tables/p2_project_node_candidates.csv")
    node_names = {row["node_name"] for row in nodes}
    expected_nodes = {"桃花源白房子", "奥运廉洁主题展馆", "12#西分区管理中心", "南门地下预埋空间", "南门露天剧场", "10#2A03分区管理中心"}
    add(rows, ok(node_names == expected_nodes), "error", f"project nodes={sorted(node_names)}", "70_outputs/processed_tables/p2_project_node_candidates.csv")
    add(rows, ok(len(assumptions) == 12), "error", f"business scene assumptions rows={len(assumptions)}", "70_outputs/processed_tables/p2_business_scene_assumption_pool.csv")
    assumption_text = "\n".join(row["assumption_text"] for row in assumptions)
    for keyword in ["婚礼", "咖啡", "疗愈", "Live House", "折扣", "草坪市集", "中医诊疗"]:
        add(rows, ok(keyword in assumption_text), "error", f"assumption coverage contains {keyword}", "70_outputs/processed_tables/p2_business_scene_assumption_pool.csv")

    add(rows, ok(len(pdf_labels) == 22), "error", f"spatial label rows={len(pdf_labels)}", "70_outputs/processed_tables/p2_spatial_label_candidates.csv")
    add(rows, ok({row["geometry_status"] for row in pdf_labels} == {"pdf_text_label_only_pending_dwg_conversion"}), "error", "PDF labels are not treated as geometry", "70_outputs/processed_tables/p2_spatial_label_candidates.csv")
    add(rows, ok(len(gaps) == 10), "error", f"gap register rows={len(gaps)}", "70_outputs/processed_tables/p2_input_gap_register.csv")
    required_gap_domains = {"geometry", "visitor_flow", "conversion_rate", "revenue_cost", "operation_authorization", "model_gate"}
    add(rows, ok(required_gap_domains <= {row["input_domain"] for row in gaps}), "error", "blocking P3/P4 gaps remain explicit", "70_outputs/processed_tables/p2_input_gap_register.csv")
    add(rows, ok(all(row["output_status"] == "needs_review" for row in nodes + assumptions + gaps + method_scores)), "error", "P2 derived outputs remain needs_review", "70_outputs/processed_tables")
    add(rows, ok(all("geometry" in row["blocking_gaps"] and "visitor_flow" in row["blocking_gaps"] for row in method_scores)), "error", "method scores preserve geometry and visitor-flow blockers", "70_outputs/processed_tables/p2_candidate_method_readiness_scores.csv")

    add(rows, ok("P2 方法原型 | 已闭环" in agent_text), "error", "AGENTS phase is P2 method prototype closed", "AGENTS.md")
    add(rows, ok("P3 真实公园校准 | 未开始" in agent_text), "error", "AGENTS keeps P3 not started", "AGENTS.md")
    add(rows, ok("已仔细研究过 DOCX 计划书和北园 PDF/CAD 可读代理" in handoff_text), "error", "handoff records source-study boundary", "handoff_next_chat.md")
    add(rows, ok("checks=589 failures=0" in handoff_text), "error", "handoff records latest full gate", "handoff_next_chat.md")

    failures = [row for row in rows if row["status"] != "pass"]
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    OUT_MD.write_text(
        "\n".join(
            [
                "# P2 完成真实性专项审计",
                "",
                f"- 检查项：{len(rows)}",
                f"- 失败项：{len(failures)}",
                "",
                "## 结论",
                "",
                "- P2 真实资料准备、语义拆解、输入缺口登记和方法原型已经完成并可复跑。",
                "- 四个用户提供的真实源文件均已登记；DOCX/PDF 已抽取，两个 DWG 明确保留 pending_conversion。",
                "- 6 个项目节点、12 条业务/场景假设、22 条北园 PDF 空间标签和 10 条输入缺口已经写入结构化产物。",
                "- 当前完成的是 P2 方法原型；P3 真实校准和 P4 完整仿真仍未开始。",
                "",
                "## 关键边界",
                "",
                "- 没有可信 DWG 转换产物前，不得生成面积、坐标、图层、动线或南北园几何对比结论。",
                "- 所有 DeepSeek 派生表和方法评分仍为 needs_review，不能直接作为最终选址排序。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"wrote p2 completion reality audit rows={len(rows)} to {OUT_CSV}")
    print(f"wrote audit report to {OUT_MD}")
    print(f"failures={len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
