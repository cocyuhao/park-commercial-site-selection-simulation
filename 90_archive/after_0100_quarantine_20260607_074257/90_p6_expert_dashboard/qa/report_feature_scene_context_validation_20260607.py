from __future__ import annotations

import json
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "90_p6_expert_dashboard"
QUALITY_DIR = ROOT / "40_quality_evidence"
REPORT_JSON = QUALITY_DIR / "report_feature_scene_context_validation_20260607.json"
REPORT_MD = QUALITY_DIR / "report_feature_scene_context_validation_20260607.md"

sys.path.insert(0, str(APP_DIR))
import app  # noqa: E402


def check(condition: bool, check_id: str, message: str, *, evidence: Any = "") -> dict[str, Any]:
    return {
        "check_id": check_id,
        "status": "pass" if condition else "fail",
        "message": message,
        "evidence": evidence,
    }


def docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
    return xml


def main() -> int:
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    original_feature_controls = app.SIMULATION_FEATURE_CONTROL_FILE.read_text(encoding="utf-8") if app.SIMULATION_FEATURE_CONTROL_FILE.exists() else None
    client = TestClient(app.app)
    checks: list[dict[str, Any]] = []
    derivative_id = ""
    report_payload: dict[str, Any] = {}
    docx_path: Path | None = None

    try:
        feature_response = client.get("/api/simulation/feature-derivatives?limit=12")
        checks.append(check(feature_response.status_code == 200, "API-FEATURE-POOL", "人物场景覆盖池接口可用。", evidence=feature_response.status_code))
        feature_payload = feature_response.json()
        first_item = next((item for item in feature_payload.get("items", []) if item.get("derivative_id")), {})
        derivative_id = str(first_item.get("derivative_id") or "")
        checks.append(check(bool(derivative_id), "API-FEATURE-ID", "可选代表场景存在稳定编号。", evidence=derivative_id))
        checks.append(
            check(
                bool(first_item.get("income_segment_name")) and bool(first_item.get("income_price_band")),
                "API-FEATURE-INCOME-FIELDS",
                "代表场景带出收入段和消费价格带。",
                evidence={key: first_item.get(key) for key in ["income_segment_name", "income_price_band"]},
            )
        )

        if derivative_id:
            use_response = client.patch(f"/api/simulation/feature-derivatives/{derivative_id}", json={"action": "use", "note": "QA 报告输入链路验证"})
            lock_response = client.patch(f"/api/simulation/feature-derivatives/{derivative_id}", json={"action": "lock"})
            checks.append(check(use_response.status_code == 200 and lock_response.status_code == 200, "API-FEATURE-CONTROL", "代表场景可被采用并锁定。", evidence={"use": use_response.status_code, "lock": lock_response.status_code}))

            dashboard = client.get("/api/dashboard").json()
            report_payload = dashboard.get("demand_supply", {}).get("report", {})
            context = report_payload.get("controlled_feature_scene_context") or {}
            calibration_context = report_payload.get("real_calibration_context") or {}
            context_ids = [item.get("derivative_id") for item in context.get("items", [])]
            checks.extend(
                [
                    check(int(context.get("count", 0)) >= 1 and derivative_id in context_ids, "API-REPORT-CONTEXT", "采用/锁定的人物场景进入 dashboard 报告上下文。", evidence={"count": context.get("count"), "ids": context_ids[:5]}),
                    check(bool(context.get("income_segments")) and bool(context.get("price_bands")), "API-REPORT-INCOME-PRICE", "报告上下文汇总收入段和消费价格带。", evidence={"income_segments": context.get("income_segments"), "price_bands": context.get("price_bands")}),
                    check(int(calibration_context.get("count", 0)) >= 10, "API-REPORT-REAL-CALIBRATION", "真实校准输入进入 dashboard 报告上下文。", evidence={"count": calibration_context.get("count"), "strengths": calibration_context.get("source_strength_counts", {})}),
                    check(any("收入" in item and "价格" in item for item in report_payload.get("simulation_readiness", {}).get("can_run_now", [])), "API-REPORT-READINESS-IMPACT", "采用场景改变报告的可运行事项说明。", evidence=report_payload.get("simulation_readiness", {}).get("can_run_now", [])[:4]),
                    check(any("真实校准输入" in item or "宏观收入" in item or "设备价格代理" in item for item in report_payload.get("simulation_readiness", {}).get("can_run_now", [])), "API-REPORT-CALIBRATION-READINESS", "真实校准输入改变报告的可运行事项说明。", evidence=report_payload.get("simulation_readiness", {}).get("can_run_now", [])[:6]),
                    check(any("收入段" in item or "价格带" in item for item in report_payload.get("next_actions", [])[:3]), "API-REPORT-NEXT-ACTION-IMPACT", "采用场景改变当前推进事项。", evidence=report_payload.get("next_actions", [])[:3]),
                    check(any("真实校准输入" in item or "竞品客单" in item for item in report_payload.get("next_actions", [])[:4]), "API-REPORT-CALIBRATION-NEXT-ACTION", "真实校准输入进入当前推进事项。", evidence=report_payload.get("next_actions", [])[:4]),
                ]
            )

            prompt = app.make_prompt(app.load_dashboard(), "priority", None)
            checks.extend(
                [
                    check("用户采用/锁定的人物场景输入" in prompt, "PROMPT-FEATURE-CONTEXT", "DeepSeek 讨论优先级 prompt 带入采用/锁定场景上下文。", evidence=prompt[:500]),
                    check("收入水平" in prompt and "消费价格带" in prompt, "PROMPT-INCOME-PRICE-RULE", "DeepSeek prompt 明确收入水平和消费价格带必须作为约束变量。", evidence="收入水平/消费价格带"),
                    check(derivative_id in prompt, "PROMPT-FEATURE-ID", "DeepSeek prompt 带入被采用场景编号。", evidence=derivative_id),
                ]
            )

            report_response = client.get("/api/reports/site-selection")
            checks.append(check(report_response.status_code == 200, "API-SITE-REPORT", "报告生成接口可用。", evidence=report_response.status_code))
            report_api_payload = report_response.json()
            report_context = report_api_payload.get("report", {}).get("controlled_feature_scene_context") or {}
            report_calibration_context = report_api_payload.get("report", {}).get("real_calibration_context") or {}
            checks.append(check(derivative_id in [item.get("derivative_id") for item in report_context.get("items", [])], "API-SITE-REPORT-CONTEXT", "报告生成接口返回采用场景上下文。", evidence=report_context.get("items", [])[:2]))
            checks.append(check(int(report_calibration_context.get("count", 0)) >= 10, "API-SITE-REPORT-REAL-CALIBRATION", "报告生成接口返回真实校准输入上下文。", evidence={"count": report_calibration_context.get("count"), "items": report_calibration_context.get("items", [])[:2]}))

            docx_value = report_api_payload.get("docx", {}).get("docx", "")
            docx_path = Path(docx_value) if docx_value else None
            docx_exists = bool(docx_path and docx_path.exists() and docx_path.is_file())
            checks.append(check(docx_exists and docx_path.stat().st_size > 40_000 if docx_exists else False, "DOCX-WRITTEN", "DOCX 报告已生成且文件体量正常。", evidence={"path": str(docx_path) if docx_path else "", "bytes": docx_path.stat().st_size if docx_exists and docx_path else 0}))
            if docx_exists and docx_path:
                text = docx_text(docx_path)
                checks.extend(
                    [
                        check("人物场景输入" in text, "DOCX-FEATURE-SECTION", "DOCX 包含人物场景输入章节。", evidence="人物场景输入"),
                        check("收入/价格带" in text and "收入水平" in text, "DOCX-INCOME-PRICE", "DOCX 包含收入/价格带口径。", evidence="收入/价格带"),
                        check(derivative_id in text or str(first_item.get("title", "")) in text, "DOCX-FEATURE-ITEM", "DOCX 包含被采用代表场景。", evidence=derivative_id),
                        check("真实校准输入" in text and "官方宏观边界" in text and "设备价格代理" in text, "DOCX-REAL-CALIBRATION-SECTION", "DOCX 包含真实校准输入分层章节。", evidence="真实校准输入/官方宏观边界/设备价格代理"),
                    ]
                )

            md_path = ROOT / "80_delivery" / "site_selection_gap_report_latest.md"
            md_text = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
            checks.extend(
                [
                    check("人物场景输入与收入价格带" in md_text, "MD-FEATURE-SECTION", "Markdown 报告包含人物场景输入章节。", evidence=str(md_path)),
                    check(derivative_id in md_text, "MD-FEATURE-ID", "Markdown 报告包含被采用代表场景编号。", evidence=derivative_id),
                    check("真实校准输入与使用边界" in md_text and "官方宏观边界" in md_text and "设备价格代理" in md_text, "MD-REAL-CALIBRATION-SECTION", "Markdown 报告包含真实校准输入分层章节。", evidence=str(md_path)),
                ]
            )
    finally:
        if original_feature_controls is None:
            if app.SIMULATION_FEATURE_CONTROL_FILE.exists():
                app.SIMULATION_FEATURE_CONTROL_FILE.unlink()
        else:
            app.SIMULATION_FEATURE_CONTROL_FILE.write_text(original_feature_controls, encoding="utf-8")

    app_js_text = (APP_DIR / "static" / "app.js").read_text(encoding="utf-8")
    styles_text = (APP_DIR / "static" / "styles.css").read_text(encoding="utf-8")
    checks.extend(
        [
            check("controlled_feature_scene_context" in app_js_text and "人物场景输入与收入价格带" in app_js_text, "UI-REPORT-FEATURE-CONTEXT", "前端报告页读取并展示人物场景上下文。"),
            check("real_calibration_context" in app_js_text and "真实校准输入与使用边界" in app_js_text, "UI-REPORT-REAL-CALIBRATION", "前端报告页读取并展示真实校准输入上下文。"),
            check(".report-feature-scene-grid" in styles_text, "UI-REPORT-FEATURE-STYLE", "前端报告页有人物场景卡片样式。"),
        ]
    )

    failures = [item for item in checks if item["status"] != "pass"]
    output = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "pass" if not failures else "fail",
        "failure_count": len(failures),
        "derivative_id": derivative_id,
        "docx_path": str(docx_path) if docx_path else "",
        "checks": checks,
        "scope": "验证采用/锁定人物场景是否进入报告、DOCX、Markdown 和 DeepSeek prompt；不证明完整仿真已完成。",
    }
    REPORT_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# 报告人物场景输入链路验证（2026-06-07）",
        "",
        f"- 状态：{output['status']}",
        f"- 失败数：{output['failure_count']}",
        f"- 验证场景：{derivative_id}",
        "- 边界：本验证只证明用户采用/锁定的人物场景进入报告和 AI prompt，不证明完整人群仿真完成。",
        "",
        "## 检查项",
    ]
    for item in checks:
        lines.append(f"- `{item['check_id']}` {item['status']}: {item['message']} {item['evidence']}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": output["status"], "failure_count": output["failure_count"], "json": str(REPORT_JSON), "md": str(REPORT_MD)}, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
