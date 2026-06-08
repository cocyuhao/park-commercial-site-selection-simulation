from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "90_p6_expert_dashboard"
QUALITY_DIR = ROOT / "40_quality_evidence"
REPORT_JSON = QUALITY_DIR / "simulation_feature_scene_dry_run_validation_20260607.json"
REPORT_MD = QUALITY_DIR / "simulation_feature_scene_dry_run_validation_20260607.md"
DB_PATH = ROOT / "60_model" / "db" / "simulation.sqlite3"

sys.path.insert(0, str(APP_DIR))
import app  # noqa: E402


def check(condition: bool, check_id: str, message: str, *, evidence: Any = "") -> dict[str, Any]:
    return {
        "check_id": check_id,
        "status": "pass" if condition else "fail",
        "message": message,
        "evidence": evidence,
    }


def cleanup_job(job_id: str) -> None:
    if not job_id or not DB_PATH.exists():
        return
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM simulation_results WHERE job_id = ?", (job_id,))
        conn.execute("DELETE FROM simulation_jobs WHERE job_id = ?", (job_id,))


def main() -> int:
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    original_feature_controls = app.SIMULATION_FEATURE_CONTROL_FILE.read_text(encoding="utf-8") if app.SIMULATION_FEATURE_CONTROL_FILE.exists() else None
    client = TestClient(app.app)
    checks: list[dict[str, Any]] = []
    derivative_id = ""
    job_id = ""
    hit_rows: list[dict[str, Any]] = []

    try:
        feature_response = client.get("/api/simulation/feature-derivatives?limit=1")
        checks.append(check(feature_response.status_code == 200, "API-FEATURE-POOL", "人物场景覆盖池可读取。", evidence=feature_response.status_code))
        feature_payload = feature_response.json()
        first = (feature_payload.get("items") or [{}])[0]
        derivative_id = str(first.get("derivative_id") or "")
        checks.append(check(bool(derivative_id), "API-FEATURE-ID", "代表场景存在稳定编号。", evidence=derivative_id))
        checks.append(check(bool(first.get("income_segment_name")) and bool(first.get("income_price_band")), "API-FEATURE-INCOME-PRICE", "代表场景含收入段和价格带。", evidence={key: first.get(key) for key in ["income_segment_name", "income_price_band"]}))

        if derivative_id:
            use_response = client.patch(f"/api/simulation/feature-derivatives/{derivative_id}", json={"action": "use", "note": "QA 仿真干跑输入验证"})
            lock_response = client.patch(f"/api/simulation/feature-derivatives/{derivative_id}", json={"action": "lock"})
            checks.append(check(use_response.status_code == 200 and lock_response.status_code == 200, "API-FEATURE-CONTROL", "代表场景可临时采用并锁定。", evidence={"use": use_response.status_code, "lock": lock_response.status_code}))

            job_response = client.post(
                "/api/simulation/jobs",
                json={"scenario_name": "qa_feature_scene_dry_run", "seed": 20260607, "iterations": 25},
            )
            checks.append(check(job_response.status_code == 200, "API-SIM-JOB-CREATE", "仿真干跑 job 可创建。", evidence=job_response.status_code))
            job_payload = job_response.json()
            job = job_payload.get("job", {})
            job_id = str(job.get("job_id") or "")
            request_json = json.loads(job.get("request_json") or "{}")
            checks.extend(
                [
                    check(bool(job_id), "API-SIM-JOB-ID", "仿真 job 返回稳定编号。", evidence=job_id),
                    check(request_json.get("feature_scene_input_count") == 1, "JOB-REQUEST-FEATURE-COUNT", "job request 记录采用/锁定人物场景数量。", evidence=request_json),
                    check(derivative_id in request_json.get("feature_scene_input_ids", []), "JOB-REQUEST-FEATURE-ID", "job request 记录采用/锁定场景编号。", evidence=request_json.get("feature_scene_input_ids")),
                    check(int(request_json.get("real_calibration_input_count") or 0) >= 10, "JOB-REQUEST-REAL-CALIBRATION-COUNT", "job request 记录真实校准输入数量。", evidence=request_json.get("real_calibration_input_count")),
                    check(
                        request_json.get("real_calibration_strength_counts", {}).get("official_macro_boundary", 0) >= 1
                        and request_json.get("real_calibration_strength_counts", {}).get("local_device_price_proxy", 0) >= 1
                        and request_json.get("real_calibration_strength_counts", {}).get("local_poi_price_signal", 0) >= 1
                        and request_json.get("real_calibration_strength_counts", {}).get("plan_assumption_needs_review", 0) >= 1,
                        "JOB-REQUEST-REAL-CALIBRATION-LAYERS",
                        "job request 记录官方宏观、本地代理、竞品价格和方案假设的分层摘要。",
                        evidence=request_json.get("real_calibration_strength_counts", {}),
                    ),
                ]
            )

            results_response = client.get(f"/api/simulation/jobs/{job_id}/results")
            checks.append(check(results_response.status_code == 200, "API-SIM-RESULTS", "仿真结果可读取。", evidence=results_response.status_code))
            result_payload = results_response.json()
            items = result_payload.get("items") or []
            hit_rows = [row for row in items if int(row.get("matched_feature_scene_count") or 0) > 0]
            first_hit = hit_rows[0] if hit_rows else {}
            pressure = first_hit.get("scenario_pressure") or {}
            accuracy = first_hit.get("accuracy_context") or {}
            constraints = first_hit.get("calibration_constraints") or []
            accuracy_text = json.dumps(accuracy, ensure_ascii=False)
            checks.extend(
                [
                    check(len(items) >= 1, "RESULT-ROW-COUNT", "干跑至少产生一行结构化结果。", evidence=len(items)),
                    check(len(hit_rows) >= 1, "RESULT-FEATURE-MATCH", "至少一个 POI/供给组命中采用人物场景。", evidence={"hit_count": len(hit_rows), "total": len(items)}),
                    check(bool(first_hit.get("feature_scene_context")), "RESULT-FEATURE-CONTEXT", "命中结果行保存人物场景摘要。", evidence=first_hit.get("feature_scene_context", [])[:1]),
                    check(bool(pressure.get("income_segments")) and bool(pressure.get("price_bands")), "RESULT-INCOME-PRICE-PRESSURE", "命中结果行保存收入段和消费价格带压力。", evidence={key: pressure.get(key) for key in ["income_segments", "price_bands"]}),
                    check(bool(pressure.get("time_bands")) and bool(pressure.get("weathers")), "RESULT-TIME-WEATHER-PRESSURE", "命中结果行保存时段和天气压力。", evidence={key: pressure.get(key) for key in ["time_bands", "weathers"]}),
                    check(bool(pressure.get("operation_rules")), "RESULT-OPERATION-RULES", "命中结果行保存建议动作/运营规则。", evidence=pressure.get("operation_rules")),
                    check(bool(accuracy.get("calibration_input_count")) and bool(accuracy.get("constraints")), "RESULT-ACCURACY-CONTEXT", "命中结果行保存准确性上下文和校准约束。", evidence={"count": accuracy.get("calibration_input_count"), "readiness": accuracy.get("readiness_label")}),
                    check("收入与消费能力" in accuracy_text and "竞品价格与供给" in accuracy_text and "时段与天气转化" in accuracy_text, "RESULT-ACCURACY-LEVERS", "准确性上下文覆盖收入、竞品和时段天气。", evidence=[item.get("name") for item in constraints]),
                    check("DeepSeek 只能" in accuracy_text and "最终收益" in accuracy_text, "RESULT-DEEPSEEK-BOUNDARY", "准确性上下文保留 DeepSeek 不能最终判断的边界。", evidence=accuracy.get("deepseek_boundary")),
                    check(any((item.get("calibration_id") or "").startswith("ORCI-") for item in accuracy.get("calibration_evidence", [])), "RESULT-CALIBRATION-EVIDENCE", "准确性上下文引用真实校准输入编号。", evidence=accuracy.get("calibration_evidence", [])[:2]),
                    check(any("客群占比" in item or "价格敏感度" in item for item in first_hit.get("next_data_needed", [])), "RESULT-NEXT-DATA-SCENE", "下一步资料需求包含客群占比/价格敏感度/转化等场景校准。", evidence=first_hit.get("next_data_needed", [])),
                    check(any("not final population shares" in item for item in first_hit.get("warnings", [])), "RESULT-NOT-FINAL-WARNING", "结果行明确采用场景不是最终客群占比。", evidence=first_hit.get("warnings", [])),
                    check(not any("roi" in row for row in items), "RESULT-NO-ROI", "当前干跑不输出 ROI 或最终收益。"),
                ]
            )

            export_response = client.get(f"/api/simulation/jobs/{job_id}/export?format=csv")
            export_text = export_response.text
            checks.extend(
                [
                    check(export_response.status_code == 200, "EXPORT-CSV", "CSV 导出接口可用。", evidence=export_response.status_code),
                    check("feature_scene_context" in export_text and "scenario_pressure" in export_text, "EXPORT-CSV-FEATURE-FIELDS", "CSV 导出包含人物场景上下文字段。"),
                    check("accuracy_context" in export_text and "calibration_constraints" in export_text, "EXPORT-CSV-ACCURACY-FIELDS", "CSV 导出包含准确性上下文和校准约束字段。"),
                ]
            )
    finally:
        if original_feature_controls is None:
            if app.SIMULATION_FEATURE_CONTROL_FILE.exists():
                app.SIMULATION_FEATURE_CONTROL_FILE.unlink()
        else:
            app.SIMULATION_FEATURE_CONTROL_FILE.write_text(original_feature_controls, encoding="utf-8")
        cleanup_job(job_id)

    app_js_text = (APP_DIR / "static" / "app.js").read_text(encoding="utf-8")
    styles_text = (APP_DIR / "static" / "styles.css").read_text(encoding="utf-8")
    checks.extend(
        [
            check("matched_feature_scene_count" in app_js_text and "人物场景压力摘要" in app_js_text, "UI-SIM-FEATURE-FIELDS", "前端仿真结果读取并展示场景命中。"),
            check("accuracy_context" in app_js_text and "准确性约束" in app_js_text, "UI-SIM-ACCURACY-FIELDS", "前端仿真结果展示准确性约束。"),
            check(".simulation-pressure" in styles_text, "UI-SIM-PRESSURE-STYLE", "前端仿真结果有人物场景压力样式。"),
        ]
    )

    failures = [item for item in checks if item["status"] != "pass"]
    output = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "pass" if not failures else "fail",
        "failure_count": len(failures),
        "derivative_id": derivative_id,
        "job_id": job_id,
        "matched_result_count": len(hit_rows),
        "checks": checks,
        "scope": "验证采用/锁定人物场景是否进入结构化仿真干跑输入、结果、导出和前端展示；不证明完整真实仿真完成。",
    }
    REPORT_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# 人物场景进入仿真干跑验证（2026-06-07）",
        "",
        f"- 状态：{output['status']}",
        f"- 失败数：{output['failure_count']}",
        f"- 验证场景：{derivative_id}",
        f"- 命中结果行：{len(hit_rows)}",
        "- 边界：本验证只证明采用/锁定人物场景进入结构化干跑，不证明真实客群占比、收益或完整仿真完成。",
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
