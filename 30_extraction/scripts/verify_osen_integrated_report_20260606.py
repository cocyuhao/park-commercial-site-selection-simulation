from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "90_p6_expert_dashboard"
OUT_JSON = ROOT / "40_quality_evidence" / "osen_integrated_report_validation_20260606.json"
OUT_MD = ROOT / "40_quality_evidence" / "osen_integrated_report_validation_20260606.md"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import app  # noqa: E402


FORBIDDEN_HUMAN_TEXT = [
    "needs_review",
    "not_final",
    "output_status",
    "geometry",
    "visitor_flow",
    "conversion_rate",
    "revenue_cost",
    "operation_authorization",
    "model_gate",
    "debug",
    "payload",
    "traceback",
    "ConnectError",
    "external" + "_preview_only",
    "API contract",
    "smoke test",
]

NODE_TERMS = [
    "桃花源白房子",
    "奥运廉洁主题展馆",
    "12#西分区",
    "南门地下预埋空间",
    "南门露天剧场",
    "10#2A03",
]

ADVICE_TERMS = [
    "修正建议",
    "当前推进事项",
    "CAD / 图纸处理",
    "不能声明最终节点排序",
    "控制点校准",
    "资质",
]

CAD_ANCHORS = ["南入口", "2A03", "露天剧场", "廉洁馆", "公园南门"]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    payload = app.load_dashboard()
    report = payload["demand_supply"]["report"]
    paths = app.write_report_files(report, app.REPORT_DIR)
    md_path = Path(paths["md"])
    json_path = Path(paths["json"])
    text = md_path.read_text(encoding="utf-8")
    report_json = read_json(json_path)
    cad = read_json(ROOT / "40_quality_evidence" / "cad_dxf_analysis_20260605.json")
    cad_pdf = read_json(ROOT / "40_quality_evidence" / "cad_pdf_proxy_analysis_20260605.json")
    deepseek = read_json(ROOT / "40_quality_evidence" / "verify_deepseek_api_report.json")
    pdf_tables = read_json(ROOT / "40_quality_evidence" / "verify_pdf_tables_report.json")
    amap = read_json(ROOT / "50_external_gis" / "amap_smoke_tests" / "amap_smoke_test_latest.json")

    cad_results = cad.get("results", [])
    all_anchor_text = json.dumps(cad_results, ensure_ascii=False)
    pdf_hits = json.dumps(cad_pdf, ensure_ascii=False)

    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, evidence: Any) -> None:
        checks.append({"name": name, "status": "pass" if passed else "fail", "evidence": evidence})

    add("report_files_written", md_path.exists() and json_path.exists(), {"md": str(md_path), "json": str(json_path)})
    add("report_length", len(text.encode("utf-8")) >= 12000, len(text.encode("utf-8")))
    add("node_count", len(report.get("nodes", [])) == 6, len(report.get("nodes", [])))
    add("all_nodes_named", all(term in text for term in NODE_TERMS), [term for term in NODE_TERMS if term in text])
    add("business_advice_present", all(term in text for term in ADVICE_TERMS), [term for term in ADVICE_TERMS if term in text])
    add("human_text_clean", not any(term in text for term in FORBIDDEN_HUMAN_TEXT), [term for term in FORBIDDEN_HUMAN_TEXT if term in text])
    add("evidence_highlights", len(report.get("source_foundation", {}).get("evidence_highlights", [])) >= 12, len(report.get("source_foundation", {}).get("evidence_highlights", [])))
    add("cad_converted_two_drawings", sum(1 for row in cad_results if row.get("dxf_bytes", 0) > 0) >= 2, [row.get("cad_id") for row in cad_results])
    add("cad_anchor_terms", all(term in all_anchor_text for term in CAD_ANCHORS), [term for term in CAD_ANCHORS if term in all_anchor_text])
    add("north_pdf_proxy_hit", "桃花源白房子" in pdf_hits, cad_pdf)
    add("deepseek_runtime_ok", deepseek.get("overall_verdict") == "PASS", deepseek.get("summary", {}))
    add("pdf_table_runtime_ok", pdf_tables.get("overall_verdict") == "PASS", pdf_tables.get("summary", {}))
    add("amap_runtime_ok", amap.get("status") == "ok" and amap.get("amap_status") == "1", amap)
    add("json_method_trace_internal_only", "method_trace" in report_json and "method_trace" not in text, list(report_json.keys()))

    result = {
        "generated_at": "2026-06-06",
        "report_paths": paths,
        "summary": dict(Counter(check["status"] for check in checks)),
        "checks": checks,
        "human_readable_constraints": {
            "final_report_boundary": "work draft, not final ROI or final ranking",
            "cad_boundary": "DXF anchors available; GIS control point calibration still required",
            "llm_boundary": "DeepSeek is a production draft worker, not the final reviewer",
        },
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# 奥森综合报告验证",
        "",
        f"- 生成日期：{result['generated_at']}",
        f"- 报告 Markdown：{paths['md']}",
        f"- 报告 JSON：{paths['json']}",
        f"- 通过项：{result['summary'].get('pass', 0)}",
        f"- 失败项：{result['summary'].get('fail', 0)}",
        "",
        "## 检查明细",
        "",
    ]
    for check in checks:
        lines.append(f"- `{check['status']}` {check['name']}: {check['evidence']}")
    lines.extend(
        [
            "",
            "## 使用边界",
            "",
            "- 本报告是工作稿，不是最终 ROI、最终排序或完整人群仿真结果。",
            "- CAD 已转 DXF 并能抽取锚点，但仍需控制点校准后才能进入 GIS 路径级仿真。",
            "- DeepSeek 只承担低成本草稿和候选生成，最终报告仍需人工/高能力 agent 复核。",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    failures = [check for check in checks if check["status"] == "fail"]
    print(f"checks={len(checks)} failures={len(failures)}")
    if failures:
        for failure in failures:
            print(f"FAIL {failure['name']}: {failure['evidence']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
