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
OUT_DIR = ROOT / "40_quality_evidence" / "simulation_object_pool_persona_behavior_browser_20260605"
OUT_JSON = ROOT / "40_quality_evidence" / "simulation_object_pool_persona_behavior_browser_20260605.json"


def choose_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_server(process: subprocess.Popen[str], base_url: str, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    last_error = ""
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"uvicorn exited early: {process.returncode}")
        try:
            with httpx.Client(timeout=1.0, trust_env=False) as client:
                response = client.get(f"{base_url}/api/dashboard")
            if response.status_code == 200:
                return
            last_error = f"status={response.status_code} body={response.text[:240]!r}"
        except Exception as exc:  # noqa: BLE001
            last_error = f"{type(exc).__name__}: {exc}"
        time.sleep(0.4)
    raise RuntimeError(f"server not ready: {last_error}")


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
    console_warnings: list[str] = []
    screenshot_path = OUT_DIR / "object_pool_persona_behavior.png"
    server_stdout = ""
    server_stderr = ""
    try:
        wait_for_server(server, base_url)
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.on("console", lambda msg: console_errors.append(f"{msg.type}: {msg.text}") if msg.type == "error" else None)
            page.on("console", lambda msg: console_warnings.append(f"{msg.type}: {msg.text}") if msg.type == "warning" else None)
            page.goto(f"{base_url}/#data", wait_until="networkidle")
            page.locator("#simulationObjectPool").wait_for(state="visible", timeout=8000)
            page.screenshot(path=str(screenshot_path), full_page=True)

            visible_text = page.locator("body").inner_text(timeout=5000)
            for label in ["人群状态画像", "行为程序", "选择概率候选", "仿真验证目标"]:
                checks.append({"name": f"visible_{label}", "passed": label in visible_text, "evidence": label})
            for button_id in ["addPersonaStateObjectBtn", "addBehaviorProgramObjectBtn", "addChoiceObjectBtn", "addValidationObjectBtn"]:
                checks.append({"name": f"button_{button_id}", "passed": page.locator(f"#{button_id}").is_visible(), "evidence": button_id})

            page.locator("#addPersonaStateObjectBtn").click()
            persona_value = page.locator("#simObjectType").input_value()
            checks.append({"name": "persona_button_sets_type", "passed": persona_value == "persona_state", "evidence": persona_value})
            page.locator("#cancelSimObjectBtn").click()

            page.locator("#addBehaviorProgramObjectBtn").click()
            behavior_value = page.locator("#simObjectType").input_value()
            checks.append({"name": "behavior_button_sets_type", "passed": behavior_value == "behavior_program", "evidence": behavior_value})
            page.locator("#cancelSimObjectBtn").click()

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
        "validator": "simulation_object_pool_persona_behavior_browser_20260605.py",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": status,
        "check_count": len(checks),
        "failure_count": sum(1 for item in checks if not item["passed"]),
        "console_errors": console_errors,
        "console_warnings": console_warnings,
        "base_url": base_url,
        "screenshot": str(screenshot_path.relative_to(ROOT)).replace("\\", "/"),
        "server_stdout_tail": server_stdout[-1000:],
        "server_stderr_tail": server_stderr[-2000:],
        "checks": checks,
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"status={status}")
    print(f"wrote={OUT_JSON.relative_to(ROOT)}")
    print(f"screenshot={screenshot_path.relative_to(ROOT)}")
    if status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
