from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "40_quality_evidence" / "page_rebuild_strategy_audit_20260605.json"
OUT_MD = ROOT / "40_quality_evidence" / "page_rebuild_strategy_audit_20260605.md"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def contains_all(text: str, terms: list[str]) -> bool:
    return all(term in text for term in terms)


def count_terms(text: str, terms: list[str]) -> dict[str, int]:
    return {term: text.count(term) for term in terms}


def main() -> None:
    index_html = read("90_p6_expert_dashboard/static/index.html")
    app_js = read("90_p6_expert_dashboard/static/app.js")
    styles_css = read("90_p6_expert_dashboard/static/styles.css")
    blueprint = read("00_control/page_layer_rebuild_blueprint_20260605.md")
    rebaseline = read("10_research/boss_method_materials_20260604/full_system_rebaseline_20260604.md")
    simulation_entry = read("10_research/simulation_task_entry_evidence_reinforcement_20260605.md")

    page_layer_validation = json.loads(read("40_quality_evidence/page_layer_rebuild_validation_20260605.json"))
    object_chain_validation = json.loads(read("40_quality_evidence/object_chain_rebaseline_validation_20260605.json"))
    preflight_validation = json.loads(read("40_quality_evidence/simulation_task_entry_preflight_validation_20260605.json"))

    new_chain_terms = [
        "全局仿真链路台",
        "对象链路矩阵",
        "当前推进事项",
        "仿真任务入口",
        "项目综合",
        "DeepSeek",
    ]
    old_shell_terms = [
        "节点清单",
        "空间地图",
        "资料导入",
        "方法对象池",
        "分析报告",
        "专家 AI 工作台",
        "panel",
        "side-nav-item",
    ]
    forbidden_user_terms = [
        "debug",
        "traceback",
        "ConnectError",
        "external_preview_only",
    ]
    internal_terms_to_hide = ["raw", "payload"]

    visible_surface = "\n".join([index_html, app_js])
    old_counts = count_terms(visible_surface, old_shell_terms)
    user_visible_source = index_html
    forbidden_counts = count_terms(user_visible_source, forbidden_user_terms)
    internal_identifier_counts = count_terms(visible_surface, internal_terms_to_hide)

    checks = [
        {
            "id": "NEW-CHAIN-LANDED",
            "passed": contains_all(visible_surface, new_chain_terms),
            "evidence": {term: visible_surface.count(term) for term in new_chain_terms},
        },
        {
            "id": "PAGE-VALIDATION-PASS",
            "passed": page_layer_validation.get("status") == "pass" and int(page_layer_validation.get("failure_count", 99)) == 0,
            "evidence": {
                "status": page_layer_validation.get("status"),
                "failure_count": page_layer_validation.get("failure_count"),
            },
        },
        {
            "id": "OBJECT-CHAIN-PASS",
            "passed": object_chain_validation.get("status") == "pass" and int(object_chain_validation.get("failure_count", 99)) == 0,
            "evidence": {
                "object_count": object_chain_validation.get("object_count"),
                "summary": object_chain_validation.get("summary"),
            },
        },
        {
            "id": "PREFLIGHT-PASS-BUT-NOT-FINAL-SIMULATION",
            "passed": preflight_validation.get("status") == "pass"
            and "不证明完整人物仿真已经完成" in preflight_validation.get("scope", ""),
            "evidence": {
                "status": preflight_validation.get("status"),
                "scope": preflight_validation.get("scope"),
            },
        },
        {
            "id": "OLD-SHELL-STILL-PRESENT",
            "passed": sum(1 for value in old_counts.values() if value > 0) >= 6,
            "evidence": old_counts,
        },
        {
            "id": "NO_FORBIDDEN_VISIBLE_LEAK_IN_STATIC_SURFACE",
            "passed": all(value == 0 for value in forbidden_counts.values()),
            "evidence": {
                "visible_static_text": forbidden_counts,
                "internal_identifiers_allowed_but_must_not_render": internal_identifier_counts,
            },
        },
        {
            "id": "BOSS-REBASELINE-REQUIRES-SYSTEM-LAYER",
            "passed": contains_all(
                rebaseline,
                [
                    "人群潜在状态层",
                    "行为程序层",
                    "空间运动层",
                    "消费选择和供需层",
                    "校准和验证层",
                ],
            ),
            "evidence": "full_system_rebaseline_20260604.md",
        },
        {
            "id": "BLUEPRINT-SAYS-NOT-PATCHING",
            "passed": "本轮不再继续给旧 P6 页面打补丁" in blueprint and "对象链" in blueprint,
            "evidence": "page_layer_rebuild_blueprint_20260605.md",
        },
        {
            "id": "RECENT-SIMULATION-LEARNING-BOUNDARY",
            "passed": contains_all(simulation_entry, ["MobileCity", "M2LSimu", "完整仿真被阻止", "不嵌入 Codex"]),
            "evidence": "simulation_task_entry_evidence_reinforcement_20260605.md",
        },
        {
            "id": "CSS-STILL-LEGACY-PANEL-DOMINANT",
            "passed": visible_surface.count("panel") > 40 and styles_css.count(".object-chain") > 5,
            "evidence": {
                "panel_reference_count": visible_surface.count("panel"),
                "object_chain_count": styles_css.count(".object-chain"),
            },
        },
        {
            "id": "UI_UX_PRO_MAX_DESIGN_SYSTEM_USED",
            "passed": (ROOT / "10_research" / "ui_skill_design_system_audit_20260605.md").exists(),
            "evidence": "10_research/ui_skill_design_system_audit_20260605.md",
        },
    ]

    status = "requires_page_level_rebuild" if all(check["passed"] for check in checks) else "audit_failed"

    migration_inventory = {
        "keep_as_verified_backend_or_data_base": [
            "FastAPI dashboard/object-chain payload",
            "资料池上传、采用、放弃、删除的后端状态",
            "人群状态、行为程序、选择概率、验证目标对象数据",
            "仿真任务预检接口和完整仿真阻止边界",
            "DeepSeek-only 生产端角色约束",
            "Playwright/axe/Lighthouse/OTel/高级 QA 证据链",
        ],
        "refactor_into_new_workflow_surface": [
            "左侧导航和旧 view 切换应重组为全局工作流步骤",
            "全局推进台应成为任务编排首页，而不是多个 panel 的集合",
            "资料池和方法对象池应合并为可采用/锁定/反驳的对象链工作区",
            "AI 工作台应成为项目综合与节点分析的持续沟通区，而不是独立问答页",
            "节点、地图、报告应作为对象链下游工作区，不再并列成旧页面栏目",
        ],
        "retire_or_hide_from_user_surface": [
            "旧项目总览式死文案",
            "裸分数、最终推荐、ROI 或完整仿真完成口径",
            "raw/debug/payload/traceback/ConnectError 等后端词",
            "把静态地图兜底误写成真实自由地图仿真",
            "把旧 dry-run 或 DeepSeek 草稿写成最终业务判断",
        ],
    }

    next_information_architecture = [
        {
            "step": "01 全局链路台",
            "purpose": "显示资料、状态、行为、选择、空间、验证、报告的整体进度和阻塞项。",
            "source_basis": ["Flowus 设计学习", "page_layer_rebuild_blueprint", "object_chain API"],
        },
        {
            "step": "02 资料与空间底座",
            "purpose": "集中处理老板资料、策划文案、CAD/图纸、PDF 表格、高德 POI 和用户上传资料。",
            "source_basis": ["老板资料 6/6", "CAD/策划资料", "evidence_ledger", "AMap POI"],
        },
        {
            "step": "03 人物仿真对象工坊",
            "purpose": "让用户管理人群状态、行为程序、选择概率和验证目标，DeepSeek 只能生成候选。",
            "source_basis": ["ROTE", "HumanLM", "MobileCity", "M2LSimu"],
        },
        {
            "step": "04 仿真任务预检",
            "purpose": "组合对象并检查真实校准、宏观验证、空间几何和运营数据缺口。",
            "source_basis": ["simulation_task_preflight", "P3 gate", "human oversight"],
        },
        {
            "step": "05 决策解释与报告工作稿",
            "purpose": "只在平台链路可回放后生成工作报告，明确已确认、待复核和禁止判断。",
            "source_basis": ["DeepSeek-only", "checked evidence rules", "商业报告语言规则"],
        },
    ]

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "answer_to_user_question": {
            "full_website_redone": False,
            "current_page_state": "旧 P6 壳上的过渡重基线，已接入对象链和预检，但不是最终页面级重做。",
            "engineering_decision": "继续修旧壳会和新主线冲突；下一步应页面级重构，迁移已验证底座，废弃旧叙事。",
        },
        "checks": checks,
        "migration_inventory": migration_inventory,
        "next_information_architecture": next_information_architecture,
        "evidence_files": [
            "00_control/page_layer_rebuild_blueprint_20260605.md",
            "10_research/boss_method_materials_20260604/full_system_rebaseline_20260604.md",
            "10_research/simulation_task_entry_evidence_reinforcement_20260605.md",
            "40_quality_evidence/page_layer_rebuild_validation_20260605.json",
            "40_quality_evidence/object_chain_rebaseline_validation_20260605.json",
            "40_quality_evidence/simulation_task_entry_preflight_validation_20260605.json",
        ],
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 页面是否重做的当前裁决审计（2026-06-05）",
        "",
        "## 结论",
        "",
        "- 结论：还没有完成整站级重做。",
        "- 当前状态：旧 P6 页面壳上的过渡重基线，已接入对象链、AI 项目综合、仿真任务预检和验证体系。",
        "- 工程判断：旧壳不能作为最终产品继续修补；下一步应页面级重构，迁移已验证底座，废弃旧叙事。",
        "",
        "## 为什么不是继续小修",
        "",
        "- 新链路已经存在：全局仿真链路台、对象链路矩阵、仿真任务入口、项目综合 AI。",
        "- 旧壳也仍存在：节点清单、空间地图、资料导入、方法对象池、报告、AI 工作台仍按旧 view 并列。",
        "- 这说明当前是过渡状态：能跑、能验证，但信息架构还没有完全跟上老板资料和现代仿真主线。",
        "",
        "## 检查结果",
        "",
    ]
    for check in checks:
        mark = "PASS" if check["passed"] else "FAIL"
        lines.append(f"- {mark} `{check['id']}`：{json.dumps(check['evidence'], ensure_ascii=False)}")

    lines.extend(["", "## 迁移判断", ""])
    for title, items in migration_inventory.items():
        lines.append(f"### {title}")
        for item in items:
            lines.append(f"- {item}")
        lines.append("")

    lines.extend(["## 下一版信息架构", ""])
    for item in next_information_architecture:
        lines.append(f"- **{item['step']}**：{item['purpose']} 依据：{', '.join(item['source_basis'])}")

    lines.extend(["", "## 证据文件", ""])
    for path in payload["evidence_files"]:
        lines.append(f"- `{path}`")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": status, "checks": len(checks), "json": str(OUT_JSON), "md": str(OUT_MD)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
