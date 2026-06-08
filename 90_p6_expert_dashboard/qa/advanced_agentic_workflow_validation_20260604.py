from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "40_quality_evidence"
URL = "http://127.0.0.1:8000/?qa=advanced-agentic-validation"
CHROME_EXE = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

OUT_JSON = OUT_DIR / "advanced_agentic_workflow_validation_20260604.json"
OUT_MD = OUT_DIR / "advanced_agentic_workflow_validation_20260604.md"
TRACE_ZIP = OUT_DIR / "advanced_agentic_workflow_trace_20260604.zip"
ARIA_OVERVIEW = OUT_DIR / "advanced_agentic_workflow_aria_overview_20260604.yml"

BANNED_VISIBLE_TERMS = [
    "raw",
    "payload",
    "debug",
    "traceback",
    "ConnectError",
    "external_preview_only",
    "needs_review",
    "not_final",
    "后端草案分",
    "仿真干跑",
    "外部预览",
    "仅地图预览",
]

RISK_TAXONOMY = {
    "human_visual": "阅读宽度、信息密度、折叠、第一屏负担和输入/输出框比例。",
    "agent_readability": "关键控件是否有稳定 id、aria-label 或 data-* hook，避免自动化只能靠文案猜。",
    "ai_scope_integrity": "默认是否是项目综合，是否误塞第一个节点或旧固定节点。",
    "oversight_checkpoint": "采用、删除、生成报告、运行检查等动作是否留有监督点和后果提示。",
    "legacy_leakage": "旧状态词、旧裸分、旧报告、debug/API 语言是否泄露到客服界面。",
    "state_coupling": "地图/资料/节点/AI/报告之间切换时是否保留上下文，不被异步加载抹掉。",
    "evidence_traceability": "报告和节点说明是否区分依据、缺口、待复核和下一步动作。",
    "observability": "是否留下 trace、ARIA、console、network、截图和结构化 JSON 证据。",
    "ai_output_risk": "AI 文案是否像日志、是否过度自信、是否缺少反例/不能判断边界。",
    "accessibility_semantics": "控件语义、可访问名称和焦点路径是否足够让人和 agent 都读懂。",
}

VIEW_SEQUENCE = [
    ("overview", "全局推进台"),
    ("upload", "资料导入"),
    ("data", "方法对象池"),
    ("nodes", "节点清单"),
    ("map", "空间地图"),
    ("ai", "专家 AI 工作台"),
    ("report", "分析报告"),
]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def scan_controls(page) -> dict[str, Any]:
    controls = page.evaluate(
        """() => {
          const isVisible = (el) => {
            const style = window.getComputedStyle(el);
            const rect = el.getBoundingClientRect();
            return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
          };
          return Array.from(document.querySelectorAll("button,a,input,textarea,select")).filter(isVisible).map((el) => {
            const thirdParty = Boolean(el.closest(".amap-logo, .amap-copyright, .amap-mcode, .amap-controlbar"));
            const dataset = {};
            for (const [key, value] of Object.entries(el.dataset || {})) dataset[key] = value;
            const rect = el.getBoundingClientRect();
            return {
              tag: el.tagName.toLowerCase(),
              text: (el.innerText || el.value || el.getAttribute("aria-label") || el.getAttribute("placeholder") || "").trim().slice(0, 80),
              id: el.id || "",
              role: el.getAttribute("role") || "",
              ariaLabel: el.getAttribute("aria-label") || "",
              dataset,
              className: String(el.className || "").slice(0, 120),
              thirdParty,
              width: Math.round(rect.width),
              height: Math.round(rect.height)
            };
          });
        }"""
    )
    missing_hooks = []
    duplicate_labels: dict[str, int] = {}
    dangerous_controls = []
    for item in controls:
        if item["tag"] not in {"button", "a"}:
            continue
        if item.get("thirdParty"):
            continue
        label = item["ariaLabel"] or item["text"] or item["id"]
        if label:
            duplicate_labels[label] = duplicate_labels.get(label, 0) + 1
        has_hook = bool(item["id"] or item["ariaLabel"] or item["dataset"])
        if not has_hook:
            missing_hooks.append(item)
        if any(term in label for term in ["删除", "放弃", "覆盖", "生成报告", "运行检查", "采用"]):
            dangerous_controls.append(
                {
                    "label": label,
                    "id": item["id"],
                    "ariaLabel": item["ariaLabel"],
                    "dataset": item["dataset"],
                    "has_hook": has_hook,
                }
            )
    duplicate_ambiguous = [
        {"label": label, "count": count}
        for label, count in duplicate_labels.items()
        if count > 3 and label not in {"采用", "放弃", "锁定", "编辑", "删除"}
    ]
    return {
        "count": len(controls),
        "missing_hook_count": len(missing_hooks),
        "missing_hook_samples": missing_hooks[:12],
        "duplicate_ambiguous_labels": duplicate_ambiguous[:12],
        "dangerous_controls": dangerous_controls[:24],
        "button_count": sum(1 for item in controls if item["tag"] == "button"),
    }


def collect_layout(page) -> dict[str, Any]:
    selectors = {
        "viewport": None,
        "chat_messages": "#chatMessages",
        "ai_composer": "#aiComposer",
        "overview_status_cards": "#overviewStatusCards",
        "simulation_object_pool": "#simulationObjectPool",
        "map_canvas": "#mapCanvas",
        "report_body": "#reportBody",
    }
    layout: dict[str, Any] = {
        "viewport": page.evaluate("() => ({ width: window.innerWidth, height: window.innerHeight })")
    }
    for name, selector in selectors.items():
        if selector is None:
            continue
        box = page.locator(selector).bounding_box(timeout=2000) if page.locator(selector).count() else None
        layout[name] = box
    return layout


def visible_text_issues(text: str) -> list[str]:
    found = [term for term in BANNED_VISIBLE_TERMS if term in text]
    issues = [f"visible_internal_term:{term}" for term in found]
    if "AI 仿真决策系统" not in text:
        issues.append("missing_global_system_title")
    if "公园商业选址场景" not in text and "当前场景：公园商业选址" not in text:
        issues.append("missing_current_scenario_label")
    return issues


def classify_ai_language(text: str) -> dict[str, Any]:
    markers = {
        "too_ai_like": ["综上所述", "作为一个AI", "根据以上分析", "以下是", "建议您"],
        "has_action_language": ["下一步", "补充", "复核", "采用", "暂缓", "判断"],
        "has_uncertainty_boundary": ["不能判断", "待复核", "缺口", "证据", "依据"],
    }
    return {
        key: [term for term in terms if term in text]
        for key, terms in markers.items()
    }


def scan_static_frontend() -> dict[str, Any]:
    files = [
        ROOT / "90_p6_expert_dashboard" / "static" / "index.html",
        ROOT / "90_p6_expert_dashboard" / "static" / "app.js",
        ROOT / "90_p6_expert_dashboard" / "static" / "styles.css",
    ]
    banned = ["external_preview_only", "needs_review", "not_final", "ConnectError", "traceback", "外部预览", "仅地图预览"]
    mapping_markers = [
        "function visibleStatus",
        "function humanizeAiText",
        "function priorityCaption",
        "function scoreMeaning",
        "function priorityLabel",
        "output_status:",
        "data_hint:",
    ]
    hits = []
    allowed_mapping_hits = []
    for path in files:
        lines = path.read_text(encoding="utf-8").splitlines()
        text = "\n".join(lines)
        for term in banned:
            if term in text:
                for line_no, line in enumerate(lines, 1):
                    if term not in line:
                        continue
                    context = "\n".join(lines[max(0, line_no - 10):min(len(lines), line_no + 10)])
                    item = {"file": rel(path), "line": line_no, "term": term, "excerpt": line.strip()[:160]}
                    if any(marker in context for marker in mapping_markers):
                        allowed_mapping_hits.append(item)
                    else:
                        hits.append(item)
    return {
        "files": [rel(path) for path in files],
        "banned_term_hits": hits,
        "allowed_mapping_hits": allowed_mapping_hits[:32],
        "note": "Internal status terms are allowed only in mapping/prompt boundary code. User-visible text is checked separately through browser snapshots.",
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# 高级 agentic 工作流验证报告（2026-06-04）",
        "",
        f"- 状态：`{payload['status']}`",
        f"- URL：`{payload['url']}`",
        f"- Playwright：`{payload['tool_versions']['playwright']}`",
        f"- Chrome：`{payload['tool_versions']['chrome_executable']}`",
        f"- 发现数：{len(payload['findings'])}",
        f"- trace：`{payload['trace']}`",
        "",
        "## 风险 taxonomy",
        "",
    ]
    for key, value in payload["risk_taxonomy"].items():
        lines.append(f"- `{key}`：{value}")
    lines.extend([
        "",
        "## 发现",
        "",
    ])
    if payload["findings"]:
        for item in payload["findings"]:
            lines.append(f"- `{item['category']}`：{item['message']} ({item.get('evidence', '')})")
    else:
        lines.append("- 无。")
    lines.extend(["", "## 页面覆盖", ""])
    for view in payload["views"]:
        lines.append(
            f"- `{view['view']}`：title=`{view['title']}`，text_len={view['text_len']}，"
            f"issues={view['visible_text_issues']}，screenshot=`{view['screenshot']}`"
        )
    lines.extend(["", "## 结构化检查", ""])
    lines.append(f"- 控件数：{payload['control_scan']['count']}")
    lines.append(f"- 按钮数：{payload['control_scan']['button_count']}")
    lines.append(f"- 缺少稳定 hook 的按钮/链接数：{payload['control_scan']['missing_hook_count']}")
    lines.append(f"- AI 工作台布局：`{payload['ai_layout']}`")
    lines.append(f"- 静态前端扫描：`{payload['static_frontend_scan']}`")
    lines.extend(["", "## 解释", ""])
    lines.append("本报告不是旧式 smoke test。`needs_work` 表示高级检查发现了下一步应修的问题，不等同于页面不可用。")
    lines.append("它用于补足 Selenium 反复点击、静态门禁和截图检查看不出来的 agentic workflow / 人类监督 / 结构可读性问题。")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    console: list[dict[str, str]] = []
    page_errors: list[str] = []
    network_errors: list[str] = []
    screenshots: list[str] = []
    findings: list[dict[str, str]] = []
    views: list[dict[str, Any]] = []
    per_view_control_scans: dict[str, Any] = {}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=str(CHROME_EXE), headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()
        page.on("console", lambda msg: console.append({"type": msg.type, "text": msg.text}))
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.on(
            "requestfailed",
            lambda request: network_errors.append(f"{request.method} {request.url} {request.failure or ''}") if "127.0.0.1:8000" in request.url else None,
        )

        page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        page.locator("body").wait_for(timeout=10000)
        page.wait_for_timeout(1800)

        aria = page.locator("body").aria_snapshot(timeout=10000)
        ARIA_OVERVIEW.write_text(aria, encoding="utf-8")

        for view, label in VIEW_SEQUENCE:
            try:
                page.locator(f'.side-nav-item[data-view="{view}"]').click(timeout=6000)
                page.wait_for_timeout(700)
            except PlaywrightTimeoutError:
                findings.append({"category": "navigation", "message": f"cannot open view {view}", "evidence": label})
            text = page.locator("body").inner_text(timeout=10000)
            issues = visible_text_issues(text)
            screenshot_path = OUT_DIR / f"advanced_agentic_workflow_{view}_20260604.png"
            page.screenshot(path=str(screenshot_path), full_page=False)
            screenshots.append(rel(screenshot_path))
            if issues:
                findings.append({"category": "visible_text", "message": f"{view} has visible text issues", "evidence": ",".join(issues)})
            if len(text) > 5000:
                findings.append(
                    {
                        "category": "information_density",
                        "message": f"{view} exposes too much text in one working surface",
                        "evidence": f"text_len={len(text)}",
                    }
                )
            if view == "data" and len(text) > 5000 and "展开" not in text and "收起" not in text:
                findings.append(
                    {
                        "category": "collapse_debt",
                        "message": "method/data object pool is still too expanded for human scanning",
                        "evidence": f"text_len={len(text)}, no visible expand/collapse affordance",
                    }
                )
            if view == "ai":
                if "N-001" in text or "桃花源白房子" in text:
                    findings.append(
                        {
                            "category": "ai_scope_integrity",
                            "message": "AI workbench still appears tied to a fixed first node",
                            "evidence": "visible N-001 or 桃花源白房子",
                        }
                    )
                language_scan = classify_ai_language(text)
                if language_scan["too_ai_like"]:
                    findings.append(
                        {
                            "category": "ai_output_risk",
                            "message": "AI workbench visible copy contains generic AI-like phrases",
                            "evidence": ",".join(language_scan["too_ai_like"]),
                        }
                    )
            if view == "report":
                report_scan = classify_ai_language(text)
                if not report_scan["has_uncertainty_boundary"]:
                    findings.append(
                        {
                            "category": "evidence_traceability",
                            "message": "report view lacks visible evidence/uncertainty boundary language",
                            "evidence": "missing 不能判断/待复核/缺口/证据/依据",
                        }
                    )
            per_view_control_scans[view] = scan_controls(page)
            views.append(
                {
                    "view": view,
                    "label": label,
                    "title": page.title(),
                    "url": page.url,
                    "text_len": len(text),
                    "visible_text_issues": issues,
                    "screenshot": rel(screenshot_path),
                }
            )

        page.locator('.side-nav-item[data-view="ai"]').click(timeout=6000)
        page.wait_for_timeout(700)
        ai_layout = collect_layout(page)
        chat_box = ai_layout.get("chat_messages") or {}
        composer_box = ai_layout.get("ai_composer") or {}
        if chat_box and chat_box.get("width", 0) < 640:
            findings.append({"category": "human_visual", "message": "AI output area is narrow for desktop reading", "evidence": f"chat_width={chat_box.get('width')}"})
        if composer_box and composer_box.get("width", 0) < 640:
            findings.append({"category": "human_visual", "message": "AI composer is narrow for desktop input", "evidence": f"composer_width={composer_box.get('width')}"})

        control_scan = {
            "count": sum(item["count"] for item in per_view_control_scans.values()),
            "button_count": sum(item["button_count"] for item in per_view_control_scans.values()),
            "missing_hook_count": sum(item["missing_hook_count"] for item in per_view_control_scans.values()),
            "missing_hook_samples": [
                sample
                for item in per_view_control_scans.values()
                for sample in item["missing_hook_samples"]
            ][:12],
            "duplicate_ambiguous_labels": [
                sample
                for item in per_view_control_scans.values()
                for sample in item["duplicate_ambiguous_labels"]
            ][:24],
            "dangerous_controls": [
                sample
                for item in per_view_control_scans.values()
                for sample in item["dangerous_controls"]
            ][:48],
            "by_view": per_view_control_scans,
        }
        if control_scan["missing_hook_count"] > 0:
            findings.append(
                {
                    "category": "agent_readability",
                    "message": "some visible buttons/links lack stable id/data/aria hooks for agentic validation",
                    "evidence": f"missing_hook_count={control_scan['missing_hook_count']}",
                }
            )
        if control_scan["duplicate_ambiguous_labels"]:
            findings.append(
                {
                    "category": "agent_readability",
                    "message": "some repeated control labels may be ambiguous for agents and keyboard users",
                    "evidence": json.dumps(control_scan["duplicate_ambiguous_labels"][:5], ensure_ascii=False),
                }
            )
        risky_without_hook = [item for item in control_scan["dangerous_controls"] if not item["has_hook"]]
        if risky_without_hook:
            findings.append(
                {
                    "category": "oversight_checkpoint",
                    "message": "dangerous or consequential controls lack stable hooks",
                    "evidence": json.dumps(risky_without_hook[:5], ensure_ascii=False),
                }
            )

        page.locator('.side-nav-item[data-view="data"]').click(timeout=6000)
        page.wait_for_timeout(700)
        data_text = page.locator("body").inner_text(timeout=10000)
        for required in ["新增选择候选", "新增验证目标", "采用", "放弃", "锁定"]:
            if required not in data_text:
                findings.append({"category": "oversight_checkpoint", "message": f"method object pool missing oversight action text: {required}", "evidence": "data view"})
        if "默认显示" not in data_text or "展开全部对象" not in data_text:
            findings.append(
                {
                    "category": "human_visual",
                    "message": "method object pool should announce its collapsed default and expansion path",
                    "evidence": "missing 默认显示/展开全部对象",
                }
            )

        page.locator('.side-nav-item[data-view="ai"]').click(timeout=6000)
        page.wait_for_timeout(700)
        ai_text = page.locator("body").inner_text(timeout=10000)
        for required in ["新对话", "项目综合", "生成报告"]:
            if required not in ai_text:
                findings.append({"category": "ai_workbench", "message": f"AI workbench missing expected control: {required}", "evidence": "ai view"})

        context.tracing.stop(path=str(TRACE_ZIP))
        browser.close()

    relevant_console = [item for item in console if item["type"] in {"error", "warning"}]
    external_console_warnings = [
        item for item in relevant_console
        if item["type"] == "warning" and "Canvas2D" in item["text"] and "willReadFrequently" in item["text"]
    ]
    app_console = [item for item in relevant_console if item not in external_console_warnings]
    if app_console:
        findings.append({"category": "console", "message": "browser console has app warnings/errors", "evidence": str(app_console[:5])})
    if page_errors:
        findings.append({"category": "page_error", "message": "page runtime errors captured", "evidence": str(page_errors[:5])})
    if network_errors:
        findings.append({"category": "network", "message": "local network request failures captured", "evidence": str(network_errors[:5])})
    static_frontend_scan = scan_static_frontend()
    if static_frontend_scan["banned_term_hits"]:
        findings.append(
            {
                "category": "legacy_leakage",
                "message": "static frontend still contains internal/stale terms that must be mapped before user display",
                "evidence": json.dumps(static_frontend_scan["banned_term_hits"][:12], ensure_ascii=False),
            }
        )
    if not TRACE_ZIP.exists() or TRACE_ZIP.stat().st_size < 100_000:
        findings.append({"category": "observability", "message": "Playwright trace is missing or too small", "evidence": rel(TRACE_ZIP)})
    if not ARIA_OVERVIEW.exists() or ARIA_OVERVIEW.stat().st_size < 1_000:
        findings.append({"category": "accessibility_semantics", "message": "ARIA snapshot is missing or too small", "evidence": rel(ARIA_OVERVIEW)})

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "needs_work" if findings else "pass",
        "url": URL,
        "tool_versions": {
            "playwright": "1.60.0",
            "chrome_executable": str(CHROME_EXE),
            "selenium_retained": "4.44.0",
            "opentelemetry_sdk": "1.42.1",
        },
        "method": [
            "Playwright trace with screenshots/snapshots/sources",
            "ARIA snapshot for agent-readable structure",
            "visible text internal-term scan",
            "stable hook scan for agentic validation",
            "human visual layout bounds for AI workbench",
            "oversight checkpoint text checks",
            "hidden-risk taxonomy: scope integrity, legacy leakage, state coupling, evidence traceability, AI output risk",
        ],
        "risk_taxonomy": RISK_TAXONOMY,
        "views": views,
        "control_scan": control_scan,
        "ai_layout": ai_layout,
        "static_frontend_scan": static_frontend_scan,
        "console": relevant_console,
        "external_console_warnings": external_console_warnings,
        "page_errors": page_errors,
        "network_errors": network_errors,
        "findings": findings,
        "trace": rel(TRACE_ZIP),
        "aria_snapshot": rel(ARIA_OVERVIEW),
        "screenshots": screenshots,
        "interpretation": "needs_work is a productive status: advanced validation found follow-up issues that older smoke tests would miss.",
    }
    write_json(OUT_JSON, payload)
    write_markdown(payload)
    print(f"wrote {rel(OUT_JSON)}")
    print(f"wrote {rel(OUT_MD)}")
    print(f"status={payload['status']} findings={len(findings)}")


if __name__ == "__main__":
    main()
