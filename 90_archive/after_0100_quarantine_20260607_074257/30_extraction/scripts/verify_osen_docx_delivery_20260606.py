from __future__ import annotations

import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "90_p6_expert_dashboard"
OUT_JSON = ROOT / "40_quality_evidence" / "osen_docx_delivery_validation_20260606.json"
OUT_MD = ROOT / "40_quality_evidence" / "osen_docx_delivery_validation_20260606.md"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


DOCX_PATH = ROOT / "80_delivery" / "osen_integrated_site_selection_report_20260606.docx"
REPORT_JSON = ROOT / "80_delivery" / "site_selection_gap_report_latest.json"
RENDER_JSON = ROOT / "40_quality_evidence" / "osen_report_docx_render_20260606.json"
AUDIT_JSON = ROOT / "40_quality_evidence" / "osen_integrated_report_docx_audit_20260606.json"
RESEARCH_SUMMARY = ROOT / "10_research" / "expert_implementation_knowledge_20260607" / "expert_implementation_summary.json"
REAL_WORLD_SOURCES = ROOT / "10_research" / "osen_real_world_context_sources_20260607.md"

FORBIDDEN_DOCX_TERMS = [
    "needs_review",
    "not_final",
    "output_status",
    "validation_status",
    "debug",
    "payload",
    "traceback",
    "ConnectError",
    "external_preview_only",
    "API contract",
    "smoke test",
    "DeepSeek",
]

REQUIRED_DOCX_TERMS = [
    "专家评审底座",
    "收入与消费上位边界",
    "周边人口与收入",
    "方案比较",
    "时间、天气与季节",
    "哪些证据会改变判断",
    "下载",
]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def docx_text(path: Path) -> str:
    if not path.exists():
        return ""
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
    return re.sub(r"<[^>]+>", "", xml)


def main() -> None:
    payload = app.load_dashboard()
    report = payload["demand_supply"]["report"]
    app.write_report_files(report, app.REPORT_DIR)
    app.write_site_selection_docx(report, app.REPORT_DIR)

    client = TestClient(app.app)
    response = client.get("/api/reports/site-selection/download?format=docx")

    report_json = read_json(REPORT_JSON)
    render = read_json(RENDER_JSON)
    audit = read_json(AUDIT_JSON)
    research = read_json(RESEARCH_SUMMARY)
    text = docx_text(DOCX_PATH)
    nodes = report_json.get("nodes", [])

    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, evidence: Any) -> None:
        checks.append({"name": name, "status": "pass" if passed else "fail", "evidence": evidence})

    add("docx_exists_and_size", DOCX_PATH.exists() and DOCX_PATH.stat().st_size >= 45_000, DOCX_PATH.stat().st_size if DOCX_PATH.exists() else 0)
    add("docx_audit_pass", audit.get("status") == "pass", audit.get("structural_audit", {}))
    add("render_pass", render.get("status") == "pass" and render.get("page_count", 0) >= 10, {"status": render.get("status"), "page_count": render.get("page_count")})
    add("web_docx_download", response.status_code == 200 and len(response.content) >= 45_000, {"status_code": response.status_code, "bytes": len(response.content)})
    add("expert_research_volume", research.get("completed_query_count") == 80 and research.get("screened_count", 0) >= 1000, {"completed": research.get("completed_query_count"), "screened": research.get("screened_count")})
    add("real_world_sources_recorded", REAL_WORLD_SOURCES.exists() and "居民人均可支配收入" in REAL_WORLD_SOURCES.read_text(encoding="utf-8"), str(REAL_WORLD_SOURCES))
    add("income_dimension_in_report", "周边人口与收入" in json.dumps(report_json, ensure_ascii=False) and "收入与价格带" in text, "income and price band present")
    add("each_node_has_three_options", len(nodes) == 6 and all(len((node.get("implementation_review") or {}).get("options", [])) >= 3 for node in nodes), [len((node.get("implementation_review") or {}).get("options", [])) for node in nodes])
    add("each_node_has_decision_changing_evidence", all((node.get("implementation_review") or {}).get("evidence_that_changes_decision") for node in nodes), len(nodes))
    add("no_forbidden_docx_terms", not any(term in text for term in FORBIDDEN_DOCX_TERMS), [term for term in FORBIDDEN_DOCX_TERMS if term in text])
    add("required_docx_terms", all(term in text for term in REQUIRED_DOCX_TERMS if term != "下载"), [term for term in REQUIRED_DOCX_TERMS if term in text])

    summary = dict(Counter(check["status"] for check in checks))
    result = {
        "generated_at": "2026-06-07",
        "summary": summary,
        "checks": checks,
        "paths": {
            "docx": str(DOCX_PATH),
            "report_json": str(REPORT_JSON),
            "render_json": str(RENDER_JSON),
            "audit_json": str(AUDIT_JSON),
            "real_world_sources": str(REAL_WORLD_SOURCES),
        },
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_lines = [
        "# 奥森 DOCX 交付验证",
        "",
        f"- 通过项：{summary.get('pass', 0)}",
        f"- 失败项：{summary.get('fail', 0)}",
        f"- DOCX：`{DOCX_PATH}`",
        f"- 渲染报告：`{RENDER_JSON}`",
        f"- 收入/消费证据：`{REAL_WORLD_SOURCES}`",
        "",
        "## 检查明细",
        "",
    ]
    for check in checks:
        md_lines.append(f"- `{check['status']}` {check['name']}: {check['evidence']}")
    OUT_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    print(f"checks={len(checks)} failures={summary.get('fail', 0)}")
    failures = [check for check in checks if check["status"] == "fail"]
    if failures:
        for failure in failures:
            print(f"FAIL {failure['name']}: {failure['evidence']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
