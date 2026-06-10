from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "40_quality_evidence" / "page_layer_rebuild_validation_20260605"
OUT_JSON = ROOT / "40_quality_evidence" / "page_layer_rebuild_validation_20260605.json"

FORBIDDEN_VISIBLE_WORDS = [
    "外部" + "预览",
    "仅地图" + "预览",
    "后端草案分",
    "debug",
    "raw",
    "payload",
    "smoke test",
    "API contract",
    "ConnectError",
    "traceback",
    "needs_review",
    "not_final",
    "external" + "_preview_only",
]


def choose_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_server(process: subprocess.Popen[str], base_url: str, timeout: float = 22.0) -> None:
    deadline = time.time() + timeout
    last_error = ""
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"uvicorn exited early: {process.returncode}")
        try:
            with httpx.Client(timeout=1.2, trust_env=False) as client:
                response = client.get(f"{base_url}/api/dashboard")
            if response.status_code == 200:
                return
            last_error = f"status={response.status_code} body={response.text[:240]!r}"
        except Exception as exc:  # noqa: BLE001
            last_error = f"{type(exc).__name__}: {exc}"
        time.sleep(0.35)
    raise RuntimeError(f"server not ready: {last_error}")


def check(name: str, passed: bool, evidence: Any) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    port = choose_free_port()
    base_url = f"http://127.0.0.1:{port}"
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app:app",
            "--app-dir",
            "90_p6_expert_dashboard",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    checks: list[dict[str, Any]] = []
    console_errors: list[str] = []
    screenshots: dict[str, str] = {}
    server_stdout = ""
    server_stderr = ""

    try:
        wait_for_server(server, base_url)
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.on("console", lambda msg: console_errors.append(f"{msg.type}: {msg.text}") if msg.type == "error" else None)

            page.goto(base_url, wait_until="domcontentloaded")
            page.locator("#overviewPrimaryActions").wait_for(state="visible", timeout=8000)
            overview_path = OUT_DIR / "overview_chain_command.png"
            page.screenshot(path=str(overview_path), full_page=True)
            screenshots["overview"] = str(overview_path.relative_to(ROOT)).replace("\\", "/")

            overview_text = page.locator("body").inner_text(timeout=5000)
            for label in ["全局仿真链路台", "全局对象链", "当前推进事项", "对象链路矩阵", "系统链路状态"]:
                checks.append(check(f"overview_visible_{label}", label in overview_text, label))
            checks.append(check("primary_actions_present", page.locator(".primary-action-card").count() >= 3, page.locator(".primary-action-card").count()))
            checks.append(check("object_chain_cards_present", page.locator(".object-chain-card").count() >= 8, page.locator(".object-chain-card").count()))
            checks.append(check("object_chain_evidence_folded", page.locator(".object-chain-evidence[open]").count() == 0, page.locator(".object-chain-evidence[open]").count()))

            visible_forbidden = [word for word in FORBIDDEN_VISIBLE_WORDS if word in overview_text]
            checks.append(check("overview_no_backend_words", not visible_forbidden, visible_forbidden))
            checks.append(check("overview_not_default_taohuayuan", "桃花源白房子" not in overview_text, "桃花源白房子" in overview_text))

            page.locator("button.side-nav-item[data-view='ai']").click()
            page.locator("#aiWorkspaceView.active #chatMessages").wait_for(state="visible", timeout=8000)
            page.evaluate(
                """() => {
                    addChatMessage(
                      "assistant",
                      "我理解的项目状态\\n当前系统还在把资料、人群状态、行为程序、选择概率和验证目标串成一条可复核链路。\\n\\n目前可以判断的事\\n可以先推进资料采用、行为程序复核和验证目标设置。\\n\\n现在还不能判断的事\\n没有闭合真实客流、转化率、收益成本和运营授权前，不能写最终推荐。\\n\\n下一步建议\\n先锁定可用资料，再让 AI 围绕项目综合生成工作稿。",
                      "页面层验证插入的模拟回答"
                    );
                }"""
            )
            ai_path = OUT_DIR / "ai_workspace_reading_width.png"
            page.screenshot(path=str(ai_path), full_page=True)
            screenshots["ai_workspace"] = str(ai_path.relative_to(ROOT)).replace("\\", "/")

            ai_text = page.locator("body").inner_text(timeout=5000)
            ai_bad_words = [word for word in FORBIDDEN_VISIBLE_WORDS if word in ai_text]
            checks.append(check("ai_default_project_scope", page.locator("#aiModeBadge").inner_text(timeout=3000).strip() == "项目综合", page.locator("#aiModeBadge").inner_text(timeout=3000).strip()))
            old_node_token = "当前节点 " + "N" + "-001"
            checks.append(check("ai_not_default_first_node", old_node_token not in ai_text and "桃花源白房子" not in ai_text, {"has_n001": old_node_token in ai_text, "has_taohuayuan": "桃花源白房子" in ai_text}))
            checks.append(check("ai_no_backend_words", not ai_bad_words, ai_bad_words))

            assistant_box = page.locator(".chat-message.assistant").last.bounding_box()
            composer_box = page.locator(".ai-composer").bounding_box()
            checks.append(check("assistant_message_width_desktop", bool(assistant_box and assistant_box["width"] >= 1040), assistant_box))
            checks.append(check("composer_width_desktop", bool(composer_box and composer_box["width"] >= 1120), composer_box))

            rail_before = page.locator("#aiWorkspaceView").evaluate("(el) => el.classList.contains('rail-collapsed')")
            page.locator("#aiRailToggle").click()
            rail_after = page.locator("#aiWorkspaceView").evaluate("(el) => el.classList.contains('rail-collapsed')")
            checks.append(check("ai_rail_toggle_changes_state", rail_before != rail_after, {"before": rail_before, "after": rail_after}))
            checks.append(check("new_chat_visible", page.locator("#newAiSessionBtn").is_visible(), "newAiSessionBtn"))
            checks.append(check("report_button_stateful", page.locator("#generateChatReportBtn").is_visible(), "generateChatReportBtn"))

            browser.close()
    finally:
        server.terminate()
        try:
            server_stdout, server_stderr = server.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server_stdout, server_stderr = server.communicate(timeout=5)

    status = "pass" if all(item["passed"] for item in checks) and not console_errors else "fail"
    report = {
        "validator": "page_layer_rebuild_validation_20260605.py",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": status,
        "check_count": len(checks),
        "failure_count": sum(1 for item in checks if not item["passed"]),
        "base_url": base_url,
        "screenshots": screenshots,
        "console_errors": console_errors,
        "server_stdout_tail": server_stdout[-1000:],
        "server_stderr_tail": server_stderr[-2000:],
        "checks": checks,
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"status={status}")
    print(f"wrote={OUT_JSON.relative_to(ROOT)}")
    for label, path in screenshots.items():
        print(f"{label}={path}")
    if status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
