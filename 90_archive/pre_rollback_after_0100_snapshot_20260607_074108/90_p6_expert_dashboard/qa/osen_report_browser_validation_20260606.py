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
OUT_DIR = ROOT / "40_quality_evidence" / "osen_report_browser_validation_20260606"
OUT_JSON = ROOT / "40_quality_evidence" / "osen_report_browser_validation_20260606.json"

FORBIDDEN_VISIBLE_WORDS = [
    "needs_review",
    "not_final",
    "output_status",
    "debug",
    "payload",
    "traceback",
    "ConnectError",
    "external_preview_only",
]

REQUIRED_VISIBLE_TERMS = [
    "奥森商业改造综合评估与修正建议工作稿",
    "专家评审底座",
    "收入边界",
    "消费支出",
    "服务消费",
    "周边人口与收入",
    "桃花源白房子",
    "南门地下预埋空间",
    "南门露天剧场",
    "真实校准输入与使用边界",
    "官方宏观边界",
    "设备价格代理",
    "人物场景输入与收入价格带",
    "当前推进事项",
    "控制点校准",
]


def choose_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_server(process: subprocess.Popen[str], base_url: str, timeout: float = 24.0) -> None:
    deadline = time.time() + timeout
    last_error = ""
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"uvicorn exited early: {process.returncode}")
        try:
            with httpx.Client(timeout=1.5, trust_env=False) as client:
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
    screenshot_path = OUT_DIR / "report_view.png"
    server_stdout = ""
    server_stderr = ""

    try:
        wait_for_server(server, base_url)
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.on("console", lambda msg: console_errors.append(f"{msg.type}: {msg.text}") if msg.type == "error" else None)
            page.goto(base_url, wait_until="domcontentloaded")
            page.locator("[data-view='report']").first.click()
            page.locator("#reportView.active").wait_for(state="visible", timeout=8000)
            page.wait_for_timeout(300)
            page.screenshot(path=str(screenshot_path), full_page=True)

            body_text = page.locator("body").inner_text(timeout=8000)
            hero_box = page.locator(".business-report-hero").bounding_box()
            report_sections = page.locator(".report-section").count()
            download_href = page.locator("#downloadReportDraftBtn").get_attribute("href")
            option_count = page.locator(".report-option-list span").count()

            visible_missing = [term for term in REQUIRED_VISIBLE_TERMS if term not in body_text]
            forbidden_found = [term for term in FORBIDDEN_VISIBLE_WORDS if term in body_text]

            checks.append(check("required_terms_visible", not visible_missing, visible_missing))
            checks.append(check("docx_download_link", bool(download_href and "format=docx" in download_href), download_href))
            checks.append(check("node_options_visible", option_count >= 6, option_count))
            checks.append(check("old_report_title_removed", "供需缺口与节点改进报告" not in body_text, "供需缺口与节点改进报告" in body_text))
            checks.append(check("no_backend_words_visible", not forbidden_found, forbidden_found))
            checks.append(check("report_sections_present", report_sections >= 4, report_sections))
            checks.append(check("real_calibration_visible", all(term in body_text for term in ["真实校准输入与使用边界", "官方宏观边界", "设备价格代理"]), body_text[:1600]))
            checks.append(check("hero_readable_width", bool(hero_box and 720 <= hero_box["width"] <= 1280), hero_box))
            checks.append(check("screenshot_written", screenshot_path.exists() and screenshot_path.stat().st_size > 50_000, {"path": str(screenshot_path.relative_to(ROOT)).replace("\\", "/"), "bytes": screenshot_path.stat().st_size if screenshot_path.exists() else 0}))
            checks.append(check("console_clean", not console_errors, console_errors))
            browser.close()
    finally:
        server.terminate()
        try:
            server_stdout, server_stderr = server.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server_stdout, server_stderr = server.communicate(timeout=5)

    status = "pass" if all(item["passed"] for item in checks) else "fail"
    report = {
        "validator": "osen_report_browser_validation_20260606.py",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": status,
        "check_count": len(checks),
        "failure_count": sum(1 for item in checks if not item["passed"]),
        "base_url": base_url,
        "screenshot": str(screenshot_path.relative_to(ROOT)).replace("\\", "/"),
        "console_errors": console_errors,
        "server_stdout_tail": server_stdout[-1000:],
        "server_stderr_tail": server_stderr[-2000:],
        "checks": checks,
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"status={status}")
    print(f"wrote={OUT_JSON.relative_to(ROOT)}")
    print(f"screenshot={screenshot_path.relative_to(ROOT)}")
    if status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
