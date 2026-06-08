from __future__ import annotations

import json
import socket
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "40_quality_evidence" / "simulation_feature_scene_browser_validation_20260607"
OUT_JSON = ROOT / "40_quality_evidence" / "simulation_feature_scene_browser_validation_20260607.json"
APP_CACHE = ROOT / "90_p6_expert_dashboard" / "cache"
FEATURE_CONTROL_FILE = APP_CACHE / "simulation_feature_derivative_controls.json"
TASK_FILE = APP_CACHE / "simulation_task_entry.json"
DB_PATH = ROOT / "60_model" / "db" / "simulation.sqlite3"

FORBIDDEN_VISIBLE_WORDS = [
    "needs_review",
    "not_final",
    "output_status",
    "payload",
    "traceback",
    "ConnectError",
    "external_preview_only",
]


def choose_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_server(process: subprocess.Popen[str], base_url: str, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    last_error = ""
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"uvicorn exited early: {process.returncode}")
        try:
            with httpx.Client(timeout=2.0, trust_env=False) as client:
                response = client.get(f"{base_url}/api/dashboard")
            if response.status_code == 200:
                return
            last_error = f"status={response.status_code} body={response.text[:200]!r}"
        except Exception as exc:  # noqa: BLE001
            last_error = f"{type(exc).__name__}: {exc}"
        time.sleep(0.35)
    raise RuntimeError(f"server not ready: {last_error}")


def backup_text(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def restore_text(path: Path, content: str | None) -> None:
    if content is None:
        if path.exists():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def cleanup_job(job_id: str) -> None:
    if not job_id or not DB_PATH.exists():
        return
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM simulation_results WHERE job_id = ?", (job_id,))
        conn.execute("DELETE FROM simulation_jobs WHERE job_id = ?", (job_id,))


def check(name: str, passed: bool, evidence: Any = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence}


def visible_forbidden_contexts(page: Any, words: list[str]) -> list[dict[str, str]]:
    return page.evaluate(
        """
        (words) => {
          const contexts = [];
          const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
          const seen = new Set();
          while (walker.nextNode()) {
            const el = walker.currentNode;
            const style = window.getComputedStyle(el);
            const rect = el.getBoundingClientRect();
            if (style.display === "none" || style.visibility === "hidden" || rect.width === 0 || rect.height === 0) {
              continue;
            }
            const text = (el.innerText || "").trim();
            if (!text) continue;
            const matched = words.filter((word) => text.includes(word));
            if (!matched.length) continue;
            const key = `${el.tagName}:${el.id || ""}:${el.className || ""}:${text.slice(0, 120)}`;
            if (seen.has(key)) continue;
            seen.add(key);
            contexts.push({
              tag: el.tagName.toLowerCase(),
              id: el.id || "",
              className: String(el.className || ""),
              words: matched.join(","),
              text: text.slice(0, 500),
            });
            if (contexts.length >= 12) break;
          }
          return contexts;
        }
        """,
        words,
    )


def prepare_feature_scene_and_task(base_url: str) -> str:
    with httpx.Client(timeout=10.0, trust_env=False) as client:
        feature_payload = client.get(f"{base_url}/api/simulation/feature-derivatives?limit=1").json()
        derivative_id = feature_payload["items"][0]["derivative_id"]
        client.patch(f"{base_url}/api/simulation/feature-derivatives/{derivative_id}", json={"action": "use", "note": "browser validation"})
        client.patch(f"{base_url}/api/simulation/feature-derivatives/{derivative_id}", json={"action": "lock"})
        preflight = client.get(f"{base_url}/api/simulation/task-preflight").json()
        selected_ids: list[str] = []
        for object_type in ["persona_state", "behavior_program", "choice_probability", "simulation_validation_target"]:
            items = preflight.get("available_objects", {}).get(object_type) or []
            if items:
                selected_ids.append(items[0]["object_id"])
        client.post(
            f"{base_url}/api/simulation/task-preflight",
            json={
                "task_name": "Browser 场景干跑验证",
                "selected_object_ids": selected_ids,
                "scenario_note": "验证采用人物场景是否进入仿真检查。",
                "run_mode": "preflight",
            },
        )
        return derivative_id


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    original_controls = backup_text(FEATURE_CONTROL_FILE)
    original_task = backup_text(TASK_FILE)
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
    job_id = ""
    derivative_id = ""
    screenshot_path = OUT_DIR / "simulation_feature_scene.png"
    server_stdout = ""
    server_stderr = ""

    try:
        wait_for_server(server, base_url)
        derivative_id = prepare_feature_scene_and_task(base_url)
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.on("console", lambda msg: console_errors.append(f"{msg.type}: {msg.text}") if msg.type == "error" else None)
            page.goto(f"{base_url}/?_v=20260607-sim-feature-browser#data", wait_until="domcontentloaded")
            page.locator("#dataView").wait_for(state="visible", timeout=10000)
            page.locator("#runSimulationBtn").click()
            page.locator(".simulation-pressure").wait_for(state="visible", timeout=12000)
            page.screenshot(path=str(screenshot_path), full_page=True)
            body_text = page.locator("#dataView").inner_text(timeout=8000)
            forbidden_contexts = visible_forbidden_contexts(page, FORBIDDEN_VISIBLE_WORDS)
            job_id = page.locator(".simulation-summary b").inner_text(timeout=8000).strip()
            pressure_count = page.locator(".simulation-pressure-grid span").count()
            table_text = page.locator(".simulation-table").inner_text(timeout=8000)
            forbidden_found = [word for word in FORBIDDEN_VISIBLE_WORDS if word in body_text]
            checks.extend(
                [
                    check("feature_scene_visible", "人物场景压力摘要" in body_text, "人物场景压力摘要" in body_text),
                    check("adopted_scene_metric", "采用场景输入" in body_text and "命中供给组" in body_text, body_text[:500]),
                    check("real_calibration_metric", "校准输入" in body_text and "14" in body_text, body_text[:900]),
                    check("income_price_visible", "收入/价格带" in body_text and "0-30元即时补给" in body_text, body_text[:800]),
                    check("accuracy_visible", "准确性约束" in body_text and "收入与消费能力" in body_text, body_text[:1200]),
                    check("operation_visible", "饮水机" in body_text or "自动售卖机" in body_text, body_text[:800]),
                    check("table_scene_columns", "场景命中" in table_text and "场景动作" in table_text and "准确性" in table_text, table_text[:500]),
                    check("job_id_visible", job_id.startswith("SIM-"), job_id),
                    check("pressure_card_count", pressure_count >= 1, pressure_count),
                    check("no_forbidden_words", not forbidden_found, {"words": forbidden_found, "contexts": forbidden_contexts}),
                    check("console_clean", not console_errors, console_errors),
                    check("screenshot_written", screenshot_path.exists() and screenshot_path.stat().st_size > 100_000, {"path": str(screenshot_path.relative_to(ROOT)).replace("\\", "/"), "bytes": screenshot_path.stat().st_size if screenshot_path.exists() else 0}),
                ]
            )
            browser.close()
    finally:
        cleanup_job(job_id)
        restore_text(FEATURE_CONTROL_FILE, original_controls)
        restore_text(TASK_FILE, original_task)
        server.terminate()
        try:
            server_stdout, server_stderr = server.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server_stdout, server_stderr = server.communicate(timeout=5)

    status = "pass" if all(item["passed"] for item in checks) else "fail"
    report = {
        "validator": "simulation_feature_scene_browser_validation_20260607.py",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": status,
        "check_count": len(checks),
        "failure_count": sum(1 for item in checks if not item["passed"]),
        "base_url": base_url,
        "derivative_id": derivative_id,
        "job_id": job_id,
        "screenshot": str(screenshot_path.relative_to(ROOT)).replace("\\", "/"),
        "console_errors": console_errors,
        "server_stdout_tail": server_stdout[-1000:],
        "server_stderr_tail": server_stderr[-2000:],
        "checks": checks,
        "scope": "真实浏览器验证采用人物场景进入仿真检查 UI；不证明完整真实仿真完成。",
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"status={status}")
    print(f"wrote={OUT_JSON.relative_to(ROOT)}")
    print(f"screenshot={screenshot_path.relative_to(ROOT)}")
    if status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
