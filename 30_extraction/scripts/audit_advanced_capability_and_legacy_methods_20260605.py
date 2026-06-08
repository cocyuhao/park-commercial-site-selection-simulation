from __future__ import annotations

import json
import subprocess
import sys
import shutil
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "40_quality_evidence" / "advanced_capability_and_legacy_method_audit_20260605.json"
OUT_MD = ROOT / "40_quality_evidence" / "advanced_capability_and_legacy_method_audit_20260605.md"


PYTHON_PACKAGES = [
    "playwright",
    "selenium",
    "opentelemetry-sdk",
    "opentelemetry-distro",
    "opentelemetry-instrumentation-fastapi",
    "opentelemetry-instrumentation-httpx",
    "fastapi",
    "uvicorn",
    "httpx",
]

NODE_PACKAGES = [
    "@axe-core/playwright",
    "@playwright/test",
    "lighthouse",
]

EVIDENCE_FILES = {
    "flowus": ROOT / "10_research" / "flowus_design_learning_20260605" / "flowus_153eefbc_snapshot.txt",
    "boss_rebaseline": ROOT / "10_research" / "boss_method_materials_20260604" / "full_system_rebaseline_20260604.md",
    "boss_inventory": ROOT / "10_research" / "boss_method_materials_20260604" / "boss_model_inventory_20260604.md",
    "advanced_register": ROOT / "10_research" / "advanced_ai_learning_absorption_register_20260604.md",
    "direction_reset": ROOT / "10_research" / "evidence_based_direction_reset_20260605.md",
    "page_blueprint": ROOT / "00_control" / "page_layer_rebuild_blueprint_20260605.md",
    "page_validation": ROOT / "40_quality_evidence" / "page_layer_rebuild_validation_20260605.json",
    "axe_validation": ROOT / "40_quality_evidence" / "axe_accessibility_probe_20260605.json",
    "lighthouse_user_flow": ROOT / "40_quality_evidence" / "lighthouse_user_flow_20260605.json",
    "lighthouse_user_flow_html": ROOT / "40_quality_evidence" / "lighthouse_user_flow_20260605" / "p6_dashboard_user_flow.html",
    "otel_trace_probe": ROOT / "40_quality_evidence" / "otel_fastapi_trace_probe_20260605.json",
    "context_risk_audit": ROOT / "40_quality_evidence" / "project_context_legacy_risk_audit_20260605.json",
    "method_coverage": ROOT / "40_quality_evidence" / "method_model_landing_coverage_20260605.json",
}

OFFICIAL_REFERENCES = [
    {
        "topic": "Playwright accessibility testing",
        "url": "https://playwright.dev/docs/accessibility-testing",
        "adoption": "用 axe-core/ARIA/浏览器截图补充旧 Selenium 点击检查；官方也提醒自动化只能发现一部分问题。",
    },
    {
        "topic": "Playwright trace viewer",
        "url": "https://playwright.dev/docs/trace-viewer",
        "adoption": "保留可回放 trace，避免只看最终截图。",
    },
    {
        "topic": "OpenTelemetry Python instrumentation",
        "url": "https://opentelemetry.io/docs/languages/python/instrumentation/",
        "adoption": "把 FastAPI、HTTPX 和 AI/API 调用纳入 span，而不是只看页面是否打开。",
    },
    {
        "topic": "@axe-core/playwright",
        "url": "https://github.com/dequelabs/axe-core-npm/tree/develop/packages/playwright",
        "adoption": "补自动可访问性扫描，但不得当成完整人类视觉验收。",
    },
    {
        "topic": "Lighthouse user flows",
        "url": "https://web.dev/articles/lighthouse-user-flows",
        "adoption": "补交互过程性能和可用性证据，不只测首屏。",
    },
]


def package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # noqa: BLE001
        return {"_error": f"{type(exc).__name__}: {exc}"}


def npm_versions() -> dict[str, str | None]:
    package_json = ROOT / "90_p6_expert_dashboard" / "qa" / "package.json"
    if not package_json.exists():
        return {name: None for name in NODE_PACKAGES}
    try:
        npm_exe = shutil.which("npm") or shutil.which("npm.cmd") or "npm.cmd"
        result = subprocess.run(
            [npm_exe, "list", "--json", "--depth=0"],
            cwd=package_json.parent,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        payload = json.loads(result.stdout or "{}")
        deps = payload.get("dependencies", {})
        return {name: (deps.get(name) or {}).get("version") for name in NODE_PACKAGES}
    except Exception:  # noqa: BLE001
        package_lock = package_json.parent / "package-lock.json"
        if package_lock.exists():
            try:
                payload = json.loads(package_lock.read_text(encoding="utf-8"))
                packages = payload.get("packages", {})
                return {
                    name: (packages.get(f"node_modules/{name}") or {}).get("version")
                    for name in NODE_PACKAGES
                }
            except Exception:  # noqa: BLE001
                pass
        return {name: None for name in NODE_PACKAGES}


def evidence_status() -> dict[str, dict[str, Any]]:
    return {
        name: {
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.exists() else 0,
        }
        for name, path in EVIDENCE_FILES.items()
    }


def build_legacy_method_matrix() -> list[dict[str, str]]:
    return [
        {
            "old_item": "裸节点分数 / 旧 discussion_score",
            "risk": "伪精确，用户无法理解分数来源，容易把草案当排名。",
            "new_role": "降级为内部排序痕迹；用户界面只看推进优先级、依据、建议和待补动作。",
            "replacement_basis": "老板资料 DLR/FLR/SSR；HumanLM；用户关于分数意义不详的纠正。",
        },
        {
            "old_item": "旧 Selenium 全点一遍",
            "risk": "只能证明按钮能点，不能证明视觉、人类理解、可访问性、trace 或 AI 输出边界。",
            "new_role": "保留兼容；高级 QA 改为 Playwright trace + ARIA + axe + Lighthouse user flow + 人工截图复核。",
            "replacement_basis": "Playwright/axe/Lighthouse 官方资料；DEC-081；用户关于检查方法老的纠正。",
        },
        {
            "old_item": "旧 P4 dry-run / 完整仿真说法",
            "risk": "缺 DWG/GIS、真实客流、转化、收益成本和运营授权时不能宣称完整仿真。",
            "new_role": "改为结构化预检和验证目标；通过后也只说明可进入下一轮复核。",
            "replacement_basis": "老板 RL+LLM 社区仿真材料；simulation_validation_target；DEC-072。",
        },
        {
            "old_item": "DeepSeek 一次性草稿",
            "risk": "便宜但不稳，容易迎合和越权生成最终判断。",
            "new_role": "低成本语义工人；只产出候选、解释、报告工作稿，必须 schema/本地校验/人工采用。",
            "replacement_basis": "DeepSeek capacity note；老板资料；DEC-076。",
        },
        {
            "old_item": "静态/兜底地图作为空间证明",
            "risk": "能看不等于能拖拽、能自由定位，更不等于空间仿真。",
            "new_role": "只作降级可见层；真实空间链路仍需高德交互、POI、边界、DWG/GIS 和校准。",
            "replacement_basis": "用户高德截图；空间运动层重基线；DEC-084。",
        },
        {
            "old_item": "旧页面补丁式视觉",
            "risk": "学了资料但仍按旧页面结构推进，导致高级方法没有进入使用路径。",
            "new_role": "按对象链重写页面层；首屏、AI、资料池、节点池都围绕对象和检查点。",
            "replacement_basis": "Flowus 三页；page_layer_rebuild_blueprint_20260605；DEC-084。",
        },
    ]


def build_report() -> dict[str, Any]:
    py_versions = {name: package_version(name) for name in PYTHON_PACKAGES}
    node_versions = npm_versions()
    evidence = evidence_status()
    page_validation = load_json(EVIDENCE_FILES["page_validation"])
    axe_validation = load_json(EVIDENCE_FILES["axe_validation"])
    lighthouse_flow = load_json(EVIDENCE_FILES["lighthouse_user_flow"])
    otel_trace = load_json(EVIDENCE_FILES["otel_trace_probe"])
    page_failures = [
        item
        for item in page_validation.get("checks", [])
        if isinstance(item, dict) and not item.get("passed")
    ]
    axe_view_violations = [
        {
            "view": view.get("view"),
            "violation_count": view.get("violation_count"),
            "violations": view.get("violations"),
        }
        for view in axe_validation.get("views", [])
        if isinstance(view, dict) and view.get("violation_count")
    ]
    lighthouse_failures = [
        item
        for item in lighthouse_flow.get("checks", [])
        if isinstance(item, dict) and not item.get("passed")
    ]
    otel_failures = [
        item
        for item in otel_trace.get("checks", [])
        if isinstance(item, dict) and not item.get("passed")
    ]
    context_audit = load_json(EVIDENCE_FILES["context_risk_audit"])
    model_coverage = load_json(EVIDENCE_FILES["method_coverage"])
    capability_checks = [
        {
            "name": "python_modern_validation_stack",
            "passed": all(py_versions.get(name) for name in [
                "playwright",
                "selenium",
                "opentelemetry-sdk",
                "opentelemetry-distro",
                "opentelemetry-instrumentation-fastapi",
                "opentelemetry-instrumentation-httpx",
            ]),
            "evidence": py_versions,
        },
        {
            "name": "node_accessibility_and_user_flow_stack",
            "passed": all(node_versions.get(name) for name in NODE_PACKAGES),
            "evidence": node_versions,
        },
        {
            "name": "learning_evidence_files_present",
            "passed": all(item["exists"] and item["bytes"] > 500 for item in evidence.values()),
            "evidence": evidence,
        },
        {
            "name": "page_layer_validation_passes",
            "passed": page_validation.get("status") == "pass" and not page_failures,
            "evidence": {
                "status": page_validation.get("status"),
                "failure_count": page_validation.get("failure_count"),
                "screenshots": page_validation.get("screenshots"),
            },
        },
        {
            "name": "axe_accessibility_zero_violations",
            "passed": axe_validation.get("status") == "pass" and not axe_view_violations,
            "evidence": {
                "status": axe_validation.get("status"),
                "failure_count": axe_validation.get("failure_count"),
                "view_violations": axe_view_violations,
            },
        },
        {
            "name": "lighthouse_user_flow_passes",
            "passed": lighthouse_flow.get("status") == "pass" and not lighthouse_failures,
            "evidence": {
                "status": lighthouse_flow.get("status"),
                "failure_count": lighthouse_flow.get("failure_count"),
                "flow_report_html": lighthouse_flow.get("flow_report_html"),
                "steps": [
                    step.get("name")
                    for step in lighthouse_flow.get("steps", [])
                    if isinstance(step, dict)
                ],
            },
        },
        {
            "name": "otel_trace_probe_passes",
            "passed": otel_trace.get("status") == "pass" and not otel_failures,
            "evidence": {
                "status": otel_trace.get("status"),
                "failure_count": otel_trace.get("failure_count"),
                "span_count": otel_trace.get("span_count"),
                "responses": otel_trace.get("responses"),
            },
        },
        {
            "name": "legacy_risk_audit_exists",
            "passed": bool(context_audit) and not context_audit.get("_error"),
            "evidence": {
                "file_count": (context_audit.get("file_inventory") or {}).get("file_count"),
                "text_like_file_count": (context_audit.get("file_inventory") or {}).get("text_like_file_count"),
                "risk_counts": (context_audit.get("legacy_risk_scan") or {}).get("counts"),
            },
        },
        {
            "name": "method_model_coverage_exists",
            "passed": bool(model_coverage) and not model_coverage.get("_error"),
            "evidence": model_coverage.get("status_counts") or {},
        },
    ]
    next_actions = [
        "把 page/axe/Lighthouse/OTel 四类验证纳入 verify_project_implementation.py 总门禁。",
        "继续用同一套验证约束后续页面大改，避免只补旧壳。",
        "把旧方法矩阵写入 handoff 和 findings，避免新对话继续使用裸分数、旧 dry-run 和补丁式视觉。",
        "后续节点和地图链路若大改，也必须补对应的对象链验证脚本和人类视觉截图。",
    ]
    failed_checks = [item for item in capability_checks if not item["passed"]]
    return {
        "auditor": "audit_advanced_capability_and_legacy_methods_20260605.py",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "pass" if not failed_checks else "needs_action",
        "official_references": OFFICIAL_REFERENCES,
        "capability_checks": capability_checks,
        "failure_count": len(failed_checks),
        "page_validation_status": page_validation.get("status"),
        "page_validation_failures": page_failures,
        "axe_validation_status": axe_validation.get("status"),
        "axe_view_violations": axe_view_violations,
        "lighthouse_user_flow_status": lighthouse_flow.get("status"),
        "lighthouse_user_flow_failures": lighthouse_failures,
        "otel_trace_status": otel_trace.get("status"),
        "otel_trace_failures": otel_failures,
        "legacy_method_matrix": build_legacy_method_matrix(),
        "next_actions": next_actions,
    }


def write_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 先进能力与旧方法信任审计（2026-06-05）",
        "",
        f"- status: `{report['status']}`",
        f"- capability_failure_count: `{report['failure_count']}`",
        f"- page_validation_status: `{report.get('page_validation_status')}`",
        f"- axe_validation_status: `{report.get('axe_validation_status')}`",
        f"- lighthouse_user_flow_status: `{report.get('lighthouse_user_flow_status')}`",
        f"- otel_trace_status: `{report.get('otel_trace_status')}`",
        "",
        "## 官方资料与采用点",
    ]
    for ref in report["official_references"]:
        lines.append(f"- [{ref['topic']}]({ref['url']}): {ref['adoption']}")
    lines.extend(["", "## 能力检查"])
    for item in report["capability_checks"]:
        lines.append(f"- {'PASS' if item['passed'] else 'FAIL'} `{item['name']}`: {json.dumps(item['evidence'], ensure_ascii=False)}")
    lines.extend(["", "## 当前页面验证失败"])
    failures = report.get("page_validation_failures") or []
    if not failures:
        lines.append("- 暂无失败项。")
    else:
        for item in failures:
            lines.append(f"- `{item.get('name')}`: {json.dumps(item.get('evidence'), ensure_ascii=False)}")
    lines.extend(["", "## 先进验证结果"])
    lines.append(f"- axe 违规视图：{json.dumps(report.get('axe_view_violations') or [], ensure_ascii=False)}")
    lines.append(f"- Lighthouse 失败项：{json.dumps(report.get('lighthouse_user_flow_failures') or [], ensure_ascii=False)}")
    lines.append(f"- OTel 失败项：{json.dumps(report.get('otel_trace_failures') or [], ensure_ascii=False)}")
    lines.extend(["", "## 旧方法降级/替换矩阵"])
    for row in report["legacy_method_matrix"]:
        lines.append(f"- `{row['old_item']}` -> {row['new_role']}；风险：{row['risk']}；依据：{row['replacement_basis']}")
    lines.extend(["", "## 下一步动作"])
    for index, action in enumerate(report["next_actions"], start=1):
        lines.append(f"{index}. {action}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    report = build_report()
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(write_markdown(report), encoding="utf-8")
    print(f"status={report['status']}")
    print(f"failure_count={report['failure_count']}")
    print(f"wrote={OUT_JSON.relative_to(ROOT)}")
    print(f"wrote={OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
