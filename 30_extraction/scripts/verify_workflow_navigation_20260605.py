from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "40_quality_evidence" / "workflow_navigation_validation_20260605.json"
OUT_MD = ROOT / "40_quality_evidence" / "workflow_navigation_validation_20260605.md"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def check_contains(text: str, terms: list[str]) -> dict[str, object]:
    missing = [term for term in terms if term not in text]
    return {"passed": not missing, "missing": missing, "terms": terms}


def main() -> None:
    index_html = read("90_p6_expert_dashboard/static/index.html")
    app_js = read("90_p6_expert_dashboard/static/app.js")
    styles_css = read("90_p6_expert_dashboard/static/styles.css")

    checks = [
        {
            "id": "WORKFLOW_NAV_REPLACES_FLAT_SIDE_NAV",
            "passed": "workflow-nav" in index_html and "side-nav-item" not in index_html,
            "evidence": {
                "workflow_stage_count": index_html.count("data-workflow-stage"),
                "side_nav_item_in_index": index_html.count("side-nav-item"),
            },
        },
        {
            "id": "FIVE_STAGE_IA_PRESENT",
            **check_contains(
                index_html,
                ["全局链路台", "资料与空间底座", "人物仿真工坊", "节点与候选点", "决策解释与报告"],
            ),
        },
        {
            "id": "DRILLDOWN_TARGETS_PRESENT",
            **check_contains(
                index_html,
                [
                    'data-scroll-target="simulationObjectPool"',
                    'data-scroll-target="simulationTaskPreflight"',
                    'id="simulationObjectPool"',
                    'id="simulationTaskPreflight"',
                ],
            ),
        },
        {
            "id": "DEEP_LINK_AND_SCROLL_LOGIC_PRESENT",
            **check_contains(
                app_js,
                ["VALID_VIEWS", "focusWorkflowTarget", "scrollTarget", 'hash.split(":")', "workflow-focus-target"],
            ),
        },
        {
            "id": "ACTIVE_STAGE_LOGIC_PRESENT",
            **check_contains(
                app_js,
                ["data-workflow-stage", "workflowViews", "workflow-main", "workflow-subnav"],
            ),
        },
        {
            "id": "VISUAL_SYSTEM_PRESENT",
            **check_contains(
                styles_css,
                [
                    ".workflow-nav",
                    ".workflow-stage.active",
                    ".workflow-main",
                    ".workflow-subnav button.active",
                    ".workflow-focus-target",
                    "@media (max-width: 760px)",
                ],
            ),
        },
        {
            "id": "NODE_DETAIL_DOES_NOT_DUPLICATE_CREATE_FORM",
            "passed": 'if (!isCreate && !isEditable) return "";' in app_js
            and 'id="quickNewNodeBtn"' in index_html
            and "编辑当前节点" in app_js
            and "清空新增" in app_js,
            "evidence": {
                "non_editable_guard": app_js.count('if (!isCreate && !isEditable) return "";'),
                "quick_new_button_in_index": index_html.count('id="quickNewNodeBtn"'),
                "edit_current_label": app_js.count("编辑当前节点"),
                "cache_buster": "20260605-workflow" in index_html,
            },
        },
        {
            "id": "DESIGN_SKILL_EVIDENCE_EXISTS",
            "passed": (ROOT / "10_research" / "ui_skill_design_system_audit_20260605.md").exists()
            and (ROOT / "10_research" / "web_design_guidelines_audit_20260605.md").exists(),
            "evidence": [
                "10_research/ui_skill_design_system_audit_20260605.md",
                "10_research/web_design_guidelines_audit_20260605.md",
            ],
        },
    ]

    failure_count = sum(1 for check in checks if not check["passed"])
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "pass" if failure_count == 0 else "fail",
        "scope": "验证页面从平铺侧栏进入流程型工作区导航；不证明完整网站重做完成。",
        "checks": checks,
        "failure_count": failure_count,
        "source_files": [
            "90_p6_expert_dashboard/static/index.html",
            "90_p6_expert_dashboard/static/app.js",
            "90_p6_expert_dashboard/static/styles.css",
        ],
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 工作流导航验证 2026-06-05",
        "",
        f"- 状态：{payload['status']}",
        f"- 失败数：{failure_count}",
        f"- 范围：{payload['scope']}",
        "",
        "## 检查项",
    ]
    for check in checks:
        mark = "PASS" if check["passed"] else "FAIL"
        lines.append(f"- {mark} `{check['id']}`")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": payload["status"], "failure_count": failure_count}, ensure_ascii=False))


if __name__ == "__main__":
    main()
