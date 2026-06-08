from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "90_p6_expert_dashboard"
OUT_JSON = ROOT / "40_quality_evidence" / "simulation_object_pool_persona_behavior_validation_20260605.json"
OUT_MD = ROOT / "40_quality_evidence" / "simulation_object_pool_persona_behavior_validation_20260605.md"

sys.path.insert(0, str(APP_DIR))

from app import load_dashboard, load_simulation_objects  # noqa: E402


def add(checks: list[dict[str, Any]], name: str, passed: bool, evidence: str) -> None:
    checks.append({"name": name, "passed": passed, "evidence": evidence})


def main() -> None:
    checks: list[dict[str, Any]] = []
    items = load_simulation_objects()
    type_counts = Counter(str(item.get("object_type") or "") for item in items)
    dashboard = load_dashboard()
    dashboard_items = dashboard.get("simulation_objects", [])
    index_html = (APP_DIR / "static" / "index.html").read_text(encoding="utf-8")
    app_js = (APP_DIR / "static" / "app.js").read_text(encoding="utf-8")

    add(checks, "has_persona_state_objects", type_counts.get("persona_state", 0) >= 6, f"persona_state={type_counts.get('persona_state', 0)}")
    add(checks, "has_behavior_program_objects", type_counts.get("behavior_program", 0) >= 7, f"behavior_program={type_counts.get('behavior_program', 0)}")
    add(checks, "keeps_choice_probability_objects", type_counts.get("choice_probability", 0) >= 1, f"choice_probability={type_counts.get('choice_probability', 0)}")
    add(checks, "keeps_validation_target_objects", type_counts.get("simulation_validation_target", 0) >= 1, f"simulation_validation_target={type_counts.get('simulation_validation_target', 0)}")
    add(checks, "dashboard_exposes_objects", len(dashboard_items) >= len(items), f"dashboard={len(dashboard_items)} objects={len(items)}")
    add(checks, "frontend_has_four_type_options", all(term in index_html for term in ["persona_state", "behavior_program", "choice_probability", "simulation_validation_target"]), "index select contains four object types")
    add(checks, "frontend_has_add_buttons", all(term in index_html for term in ["addPersonaStateObjectBtn", "addBehaviorProgramObjectBtn", "addChoiceObjectBtn", "addValidationObjectBtn"]), "index buttons include four add actions")
    add(checks, "frontend_labels_human_readable", all(term in app_js for term in ["人群状态画像", "行为程序", "选择概率候选", "仿真验证目标"]), "JS labels are business-readable")
    add(checks, "frontend_action_controls_retained", all(term in app_js for term in ["data-sim-object-action=\"use\"", "data-sim-object-action=\"discard\"", "data-sim-object-action=\"delete\"", "data-sim-object-edit"]), "adopt discard delete edit controls retained")

    status = "pass" if all(item["passed"] for item in checks) else "fail"
    report = {
        "validator": "simulation_object_pool_persona_behavior_validation_20260605.py",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": status,
        "check_count": len(checks),
        "failure_count": sum(1 for item in checks if not item["passed"]),
        "type_counts": dict(type_counts),
        "checks": checks,
        "basis": [
            "10_research/boss_method_materials_20260604/deepseek_constrained_simulation_design_20260604.md",
            "40_quality_evidence/method_model_landing_coverage_20260605.md",
            "70_outputs/processed_tables/p2_persona_state_profiles_20260604.csv",
            "70_outputs/processed_tables/p2_behavior_program_templates_20260604.csv",
        ],
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 人群状态与行为程序对象池验证（2026-06-05）",
        "",
        f"- 状态：{status}",
        f"- 检查项：{report['check_count']}",
        f"- 失败项：{report['failure_count']}",
        "",
        "## 依据",
        "",
        "- 老板资料要求先落静态状态画像、行为程序和验证目标，再接 DeepSeek JSON 编译脚本。",
        "- 覆盖审计指出 `persona_state` / `behavior_program` 仍是 partial，需要进入前端对象池。",
        "- 本轮只把这两类对象接入已有对象池，不重写仿真算法，不声称完成真实仿真。",
        "",
        "## 检查明细",
        "",
    ]
    for item in checks:
        mark = "pass" if item["passed"] else "fail"
        lines.append(f"- `{mark}` {item['name']}：{item['evidence']}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"status={status}")
    print(f"wrote={OUT_JSON.relative_to(ROOT)}")
    print(f"wrote={OUT_MD.relative_to(ROOT)}")
    if status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
