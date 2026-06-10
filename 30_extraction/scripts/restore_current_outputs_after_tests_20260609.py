from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient

from cleanup_active_dashboard_caches_20260608 import main as cleanup_active_caches


ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_DIR = ROOT / "90_p6_expert_dashboard"
REPORT_PATH = ROOT / "40_quality_evidence" / "post_test_current_output_restore_20260609.json"


def j(*parts: str) -> str:
    return "".join(parts)


RISK_TERMS = [
    j("补", "齐"),
    j("补", "证"),
    j("补", "资料"),
    j("待", "补"),
    j("补", "数"),
    j("请", "补"),
    j("训练", "资料"),
    j("外部", "预览"),
    j("仅地图", "预览"),
    j("external", "_preview_only"),
    j("N", "-001"),
    "QA UI 自动化节点",
]


def text_risk_counts(path: Path) -> dict[str, int]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return {term: text.count(term) for term in RISK_TERMS if term in text}


def regenerate_site_selection_report() -> dict[str, object]:
    sys.path.insert(0, str(DASHBOARD_DIR))
    import app  # pylint: disable=import-error,import-outside-toplevel

    with TestClient(app.app) as client:
        response = client.get("/api/reports/site-selection")
        response.raise_for_status()
        payload = response.json()
    paths = [
        ROOT / "80_delivery" / "site_selection_gap_report_latest.md",
        ROOT / "80_delivery" / "site_selection_gap_report_latest.json",
    ]
    return {
        "status_code": response.status_code,
        "report_id": payload.get("report", {}).get("report_id"),
        "outputs": [
            {
                "path": str(path.relative_to(ROOT)),
                "bytes": path.stat().st_size,
                "risk_counts": text_risk_counts(path),
            }
            for path in paths
        ],
    }


def main() -> None:
    cleanup_active_caches()
    regenerated = regenerate_site_selection_report()
    output_risks = [row["risk_counts"] for row in regenerated["outputs"]]
    status = "pass" if all(not risks for risks in output_risks) else "needs_action"
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "purpose": "测试后恢复当前活动输出：先清活动缓存，再重生客户可见报告，防止 QA 节点或旧口径留在交付文件里。",
        "regenerated_report": regenerated,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if status != "pass":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
