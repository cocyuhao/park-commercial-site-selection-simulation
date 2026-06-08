from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "90_p6_expert_dashboard"
QUALITY_DIR = ROOT / "40_quality_evidence"
REPORT_JSON = QUALITY_DIR / "simulation_task_entry_preflight_validation_20260605.json"
REPORT_MD = QUALITY_DIR / "simulation_task_entry_preflight_validation_20260605.md"

sys.path.insert(0, str(APP_DIR))
import app  # noqa: E402


def read_csv_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return sum(1 for _ in csv.DictReader(f))


def read_jsonl_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        return sum(1 for _ in f)


def check(condition: bool, check_id: str, message: str, *, evidence: str = "") -> dict[str, Any]:
    return {
        "check_id": check_id,
        "status": "pass" if condition else "fail",
        "message": message,
        "evidence": evidence,
    }


def main() -> int:
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    original_task = app.SIMULATION_TASK_FILE.read_text(encoding="utf-8") if app.SIMULATION_TASK_FILE.exists() else None
    original_feature_controls = app.SIMULATION_FEATURE_CONTROL_FILE.read_text(encoding="utf-8") if app.SIMULATION_FEATURE_CONTROL_FILE.exists() else None
    client = TestClient(app.app)
    checks: list[dict[str, Any]] = []

    local_counts = {
        "evidence_ledger": read_csv_count(ROOT / "40_quality_evidence" / "evidence_ledger.csv"),
        "pdf_native_tables": read_jsonl_count(ROOT / "30_extraction" / "tables" / "pdf_native_tables.jsonl"),
        "amap_poi_candidates": read_csv_count(ROOT / "70_outputs" / "processed_tables" / "poi_supply_candidates_amap.csv"),
        "in_park_followup": read_csv_count(ROOT / "70_outputs" / "processed_tables" / "poi_supply_p0_followup_worklist_enriched.csv"),
        "persona_state": read_csv_count(ROOT / "70_outputs" / "processed_tables" / "p2_persona_state_profiles_20260604.csv"),
        "behavior_program": read_csv_count(ROOT / "70_outputs" / "processed_tables" / "p2_behavior_program_templates_20260604.csv"),
        "choice_probability": read_csv_count(ROOT / "70_outputs" / "processed_tables" / "choice_probability_from_p2_p4_20260604.csv"),
        "validation_target": read_csv_count(ROOT / "70_outputs" / "processed_tables" / "simulation_validation_target_from_p2_20260604.csv"),
        "feature_derivatives": read_csv_count(ROOT / "70_outputs" / "processed_tables" / "person_simulation_feature_derivatives_1000_20260604.csv"),
        "real_calibration_inputs": read_csv_count(ROOT / "70_outputs" / "processed_tables" / "osen_real_calibration_inputs_20260607.csv"),
        "boss_sources": read_csv_count(ROOT / "10_research" / "boss_method_materials_20260604" / "source_manifest.csv"),
        "cad_plan_files": len(list((ROOT / "CAD图及其计划").glob("*"))),
        "boss_folder_files": len(list((ROOT / "老板资料").glob("*"))),
    }
    checks.extend(
        [
            check(local_counts["evidence_ledger"] >= 200, "DATA-EVIDENCE-LEDGER", "证据台账可读取且数量足以支撑预检入口。", evidence=str(local_counts["evidence_ledger"])),
            check(local_counts["pdf_native_tables"] >= 300, "DATA-PDF-TABLES", "PDF 表格抽取结果可读取。", evidence=str(local_counts["pdf_native_tables"])),
            check(local_counts["amap_poi_candidates"] >= 200, "DATA-AMAP-POI", "高德 POI 候选表可读取。", evidence=str(local_counts["amap_poi_candidates"])),
            check(local_counts["boss_sources"] == 6 and local_counts["boss_folder_files"] == 6, "DATA-BOSS-MATERIALS", "老板六份方法资料原件和归档清单一致。", evidence=json.dumps({"manifest": local_counts["boss_sources"], "folder": local_counts["boss_folder_files"]}, ensure_ascii=False)),
            check(local_counts["cad_plan_files"] >= 4, "DATA-CAD-PLAN", "策划文案和 CAD/PDF 图纸资料已在项目目录。", evidence=str(local_counts["cad_plan_files"])),
            check(local_counts["persona_state"] >= 1 and local_counts["behavior_program"] >= 1, "OBJECT-PERSONA-BEHAVIOR", "人群状态和行为程序候选已落盘。", evidence=json.dumps({"persona": local_counts["persona_state"], "behavior": local_counts["behavior_program"]}, ensure_ascii=False)),
            check(local_counts["choice_probability"] >= 1 and local_counts["validation_target"] >= 1, "OBJECT-CHOICE-VALIDATION", "选择概率和验证目标候选已落盘。", evidence=json.dumps({"choice": local_counts["choice_probability"], "validation": local_counts["validation_target"]}, ensure_ascii=False)),
            check(local_counts["feature_derivatives"] >= 1000, "DATA-FEATURE-DERIVATIVES", "人物仿真衍生场景覆盖池可读取。", evidence=str(local_counts["feature_derivatives"])),
            check(local_counts["real_calibration_inputs"] >= 10, "DATA-OSEN-REAL-CALIBRATION", "奥森真实校准输入包可读取。", evidence=str(local_counts["real_calibration_inputs"])),
        ]
    )

    try:
        get_response = client.get("/api/simulation/task-preflight")
        checks.append(check(get_response.status_code == 200, "API-GET-PREFLIGHT", "仿真任务预检 GET 接口可用。", evidence=str(get_response.status_code)))
        preflight = get_response.json()
        asset_labels = {item.get("label") for item in preflight.get("local_data_assets", [])}
        check_ids = {item.get("check_id") for item in preflight.get("preflight_checks", [])}
        feature_pool = preflight.get("feature_derivative_pool", {})
        real_calibration = preflight.get("real_calibration_context", {})
        real_strengths = real_calibration.get("source_strength_counts", {})
        checks.extend(
            [
                check("奥森策划资料" in asset_labels and "CAD / 图纸资料" in asset_labels, "API-ASSET-CAD-PLAN", "预检入口显示策划文案与 CAD/图纸资料用途。", evidence=json.dumps(sorted(asset_labels), ensure_ascii=False)),
                check("人物仿真覆盖池" in asset_labels, "API-ASSET-FEATURE-DERIVATIVES", "预检入口显示人物仿真覆盖池，避免 1000+ 衍生特征只藏在后台。", evidence=json.dumps(sorted(asset_labels), ensure_ascii=False)),
                check("奥森真实校准输入" in asset_labels, "API-ASSET-REAL-CALIBRATION", "预检入口显示奥森真实校准输入，避免收入/竞品/转化只停在报告里。", evidence=json.dumps(sorted(asset_labels), ensure_ascii=False)),
                check("planning_and_cad_integration" in check_ids, "API-CHECK-CAD-PLAN", "预检包含策划文案与 CAD 结合检查项。", evidence=json.dumps(sorted(check_ids), ensure_ascii=False)),
                check("person_simulation_feature_derivatives" in check_ids, "API-CHECK-FEATURE-DERIVATIVES", "预检包含人物仿真覆盖池检查项。", evidence=json.dumps(sorted(check_ids), ensure_ascii=False)),
                check("controlled_feature_scenes" in check_ids, "API-CHECK-CONTROLLED-FEATURE-SCENES", "预检包含已采用/锁定人物场景检查项。", evidence=json.dumps(sorted(check_ids), ensure_ascii=False)),
                check("osen_real_calibration_inputs" in check_ids, "API-CHECK-REAL-CALIBRATION", "预检包含奥森真实校准输入检查项。", evidence=json.dumps(sorted(check_ids), ensure_ascii=False)),
                check(feature_pool.get("total_count", 0) >= 1000 and len(feature_pool.get("items", [])) >= 4, "API-FEATURE-POOL-IN-PREFLIGHT", "预检 payload 带出可操作代表场景，而不只是后台文件。", evidence=json.dumps({"total": feature_pool.get("total_count"), "visible": len(feature_pool.get("items", []))}, ensure_ascii=False)),
                check(int(feature_pool.get("coverage", {}).get("income_segments", 0)) >= 5, "API-FEATURE-INCOME-COVERAGE", "预检覆盖池显式包含收入/消费价格带维度。", evidence=json.dumps(feature_pool.get("coverage", {}), ensure_ascii=False)),
                check(
                    int(real_calibration.get("count", 0)) >= 10
                    and real_strengths.get("official_macro_boundary", 0) >= 1
                    and real_strengths.get("local_device_price_proxy", 0) >= 1
                    and real_strengths.get("local_poi_price_signal", 0) >= 1
                    and real_strengths.get("plan_assumption_needs_review", 0) >= 1,
                    "API-REAL-CALIBRATION-LAYERED",
                    "预检 payload 带出分层真实校准输入：官方宏观、本地画像/代理、竞品价格和方案假设不混用。",
                    evidence=json.dumps({"count": real_calibration.get("count"), "strengths": real_strengths}, ensure_ascii=False),
                ),
                check("production_ai_boundary" in check_ids, "API-CHECK-DEEPSEEK-ONLY", "预检包含生产 DeepSeek-only 边界检查项。", evidence=json.dumps(sorted(check_ids), ensure_ascii=False)),
                check(preflight.get("full_simulation_status") == "blocked_for_full_simulation", "API-FULL-SIM-BLOCKED", "缺真实校准和 P3 门禁时，接口阻止完整仿真声明。", evidence=str(preflight.get("full_simulation_status"))),
                check(preflight.get("dry_run_status") == "select_objects_first", "API-OBJECTS-FIRST", "对象未选择齐时，接口要求先选择对象。", evidence=str(preflight.get("dry_run_status"))),
            ]
        )

        feature_response = client.get("/api/simulation/feature-derivatives")
        checks.append(check(feature_response.status_code == 200, "API-GET-FEATURE-DERIVATIVES", "人物场景覆盖池 API 可读取。", evidence=str(feature_response.status_code)))
        feature_payload = feature_response.json()
        first_item = (feature_payload.get("items") or [{}])[0]
        first_id = first_item.get("derivative_id")
        checks.append(check(bool(first_id), "API-FEATURE-FIRST-ID", "覆盖池代表场景带有稳定场景编号。", evidence=str(first_id)))
        checks.append(check(bool(first_item.get("income_segment_name")) and bool(first_item.get("income_price_band")), "API-FEATURE-INCOME-FIELDS", "覆盖池代表场景带出收入段和消费价格带字段。", evidence=json.dumps({k: first_item.get(k) for k in ["income_segment_name", "income_price_band"]}, ensure_ascii=False)))
        if first_id:
            use_response = client.patch(f"/api/simulation/feature-derivatives/{first_id}", json={"action": "use"})
            use_payload = use_response.json()
            used_item = next((item for item in use_payload.get("items", []) if item.get("derivative_id") == first_id), {})
            lock_response = client.patch(f"/api/simulation/feature-derivatives/{first_id}", json={"action": "lock"})
            lock_payload = lock_response.json()
            locked_item = next((item for item in lock_payload.get("items", []) if item.get("derivative_id") == first_id), {})
            impact_preflight = client.get("/api/simulation/task-preflight").json()
            feature_inputs = impact_preflight.get("feature_scene_inputs") or []
            impact_check = next((item for item in impact_preflight.get("preflight_checks", []) if item.get("check_id") == "controlled_feature_scenes"), {})
            restore_response = client.patch(f"/api/simulation/feature-derivatives/{first_id}", json={"action": "restore"})
            checks.extend(
                [
                    check(use_response.status_code == 200 and used_item.get("adoption_status") == "已采用", "API-FEATURE-USE", "代表场景可以被用户采用。", evidence=json.dumps(used_item, ensure_ascii=False)[:500]),
                    check(lock_response.status_code == 200 and locked_item.get("user_locked") is True, "API-FEATURE-LOCK", "代表场景可以被用户锁定。", evidence=json.dumps(locked_item, ensure_ascii=False)[:500]),
                    check(int(impact_preflight.get("controlled_feature_scene_count", 0)) >= 1 and any(item.get("derivative_id") == first_id for item in feature_inputs), "API-FEATURE-INPUT-IMPACT", "采用/锁定后代表场景进入预检输入。", evidence=json.dumps({"count": impact_preflight.get("controlled_feature_scene_count"), "ids": [item.get("derivative_id") for item in feature_inputs[:5]]}, ensure_ascii=False)),
                    check(impact_check.get("status") == "pass", "API-FEATURE-CHECK-PASS-AFTER-CONTROL", "采用/锁定后已采用人物场景检查项变为已满足。", evidence=json.dumps(impact_check, ensure_ascii=False)[:500]),
                    check(restore_response.status_code == 200, "API-FEATURE-RESTORE", "代表场景可以恢复为暂未采用。", evidence=str(restore_response.status_code)),
                ]
            )

        available = preflight.get("available_objects", {})
        selected_ids: list[str] = []
        for object_type in app.SIMULATION_TASK_OBJECT_TYPES:
            items = available.get(object_type) or []
            if items:
                selected_ids.append(items[0]["object_id"])
        post_response = client.post(
            "/api/simulation/task-preflight",
            json={
                "task_name": "QA 预检任务",
                "selected_object_ids": selected_ids,
                "scenario_note": "验证对象组合后仍不宣称完整仿真。",
                "run_mode": "preflight",
            },
        )
        checks.append(check(post_response.status_code == 200, "API-POST-PREFLIGHT", "仿真任务预检 POST 接口可保存选择。", evidence=str(post_response.status_code)))
        post_payload = post_response.json()
        selected_counts = post_payload.get("selected_counts", {})
        selected_all_types = all(int(selected_counts.get(object_type, 0)) >= 1 for object_type in app.SIMULATION_TASK_OBJECT_TYPES)
        checks.extend(
            [
                check(selected_all_types, "API-SELECT-ALL-TYPES", "预检可组合人群、行为、选择概率和验证目标四类对象。", evidence=json.dumps(selected_counts, ensure_ascii=False)),
                check(post_payload.get("dry_run_status") == "ready_for_structural_precheck", "API-DRY-RUN-READY", "四类对象选择后只放行结构化预检，不放行完整仿真。", evidence=str(post_payload.get("dry_run_status"))),
                check(post_payload.get("full_simulation_status") == "blocked_for_full_simulation", "API-POST-FULL-STILL-BLOCKED", "对象齐备后仍因真实校准/P3 门禁阻止完整仿真。", evidence=str(post_payload.get("full_simulation_status"))),
            ]
        )

        dashboard_response = client.get("/api/dashboard")
        checks.append(check(dashboard_response.status_code == 200, "API-DASHBOARD", "dashboard 仍可加载，并包含预检 payload。", evidence=str(dashboard_response.status_code)))
        dashboard_payload = dashboard_response.json()
        checks.append(check(bool(dashboard_payload.get("simulation_task_preflight")), "API-DASHBOARD-PREFLIGHT", "dashboard 已带出仿真任务预检数据。"))
    finally:
        if original_task is None:
            if app.SIMULATION_TASK_FILE.exists():
                app.SIMULATION_TASK_FILE.unlink()
        else:
            app.SIMULATION_TASK_FILE.write_text(original_task, encoding="utf-8")
        if original_feature_controls is None:
            if app.SIMULATION_FEATURE_CONTROL_FILE.exists():
                app.SIMULATION_FEATURE_CONTROL_FILE.unlink()
        else:
            app.SIMULATION_FEATURE_CONTROL_FILE.write_text(original_feature_controls, encoding="utf-8")

    index_text = (APP_DIR / "static" / "index.html").read_text(encoding="utf-8")
    app_js_text = (APP_DIR / "static" / "app.js").read_text(encoding="utf-8")
    styles_text = (APP_DIR / "static" / "styles.css").read_text(encoding="utf-8")
    visible_preflight_parts = [
        str(preflight.get("human_summary") or ""),
        str(preflight.get("deepseek_role") or ""),
    ]
    for item in preflight.get("preflight_checks", []):
        visible_preflight_parts.extend(
            [
                str(item.get("label") or ""),
                str(item.get("detail") or ""),
                str(item.get("next_action") or ""),
            ]
        )
    for item in preflight.get("local_data_assets", []):
        visible_preflight_parts.extend(
            [
                str(item.get("label") or ""),
                str(item.get("status") or ""),
                str(item.get("use_scope") or ""),
            ]
        )
    visible_preflight_text = "\n".join(visible_preflight_parts)
    checks.extend(
        [
            check("仿真任务入口" in index_text and "simulationTaskPreflight" in index_text, "UI-PREFLIGHT-SECTION", "前端存在仿真任务入口区域。"),
            check("saveSimulationTaskPreflight" in app_js_text and "selectAdoptedTaskObjects" in app_js_text, "UI-PREFLIGHT-ACTIONS", "前端存在保存预检、使用已采用对象等操作。"),
            check("人物场景控制" in app_js_text and "data-feature-derivative-action" in app_js_text, "UI-FEATURE-POOL-ACTIONS", "前端存在人物场景采用、放弃、锁定操作。"),
            check("income_segment_name" in app_js_text and "income_price_band" in app_js_text, "UI-FEATURE-INCOME-FIELDS", "前端人物场景显示收入段和消费价格带。"),
            check(".simulation-task-panel" in styles_text and ".task-type-grid" in styles_text, "UI-PREFLIGHT-LAYOUT", "仿真任务入口有独立全宽面板和对象选择布局。"),
            check(".feature-pool" in styles_text and ".feature-scenario-card" in styles_text, "UI-FEATURE-POOL-LAYOUT", "人物场景控制区有独立视觉层。"),
            check(
                "production_ai_boundary" in check_ids
                and "AI" in visible_preflight_text
                and "工作稿" in visible_preflight_text
                and "最终概率、排名或收益" in visible_preflight_text
                and "needs_review" not in visible_preflight_text
                and "not_final" not in visible_preflight_text,
                "TEXT-AI-BOUNDARY-HUMANIZED",
                "用户可见预检文案明确生产 AI 边界，且不暴露内部状态词。",
            ),
            check("完整仿真" in visible_preflight_text and "阻止" in visible_preflight_text, "TEXT-NO-FINAL-CLAIM", "预检文案明确完整仿真仍被阻止，不写成最终结论。"),
        ]
    )

    failures = [item for item in checks if item["status"] != "pass"]
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "pass" if not failures else "fail",
        "failure_count": len(failures),
        "local_counts": local_counts,
        "checks": checks,
        "scope": "仿真任务入口只验证资料依据、对象组合和运行前预检；不证明完整人物仿真已经完成。",
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 仿真任务入口预检验证报告（2026-06-05）",
        "",
        f"- 状态：{report['status']}",
        f"- 失败数：{report['failure_count']}",
        "- 结论：本验证只证明入口有本地资料依据、能组合四类对象、能阻止完整仿真误声明；不证明完整仿真完成。",
        "",
        "## 本地依据计数",
    ]
    for key, value in local_counts.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## 检查项"])
    for item in checks:
        lines.append(f"- `{item['check_id']}` {item['status']}: {item['message']} {item['evidence']}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "failure_count": report["failure_count"], "json": str(REPORT_JSON), "md": str(REPORT_MD)}, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
