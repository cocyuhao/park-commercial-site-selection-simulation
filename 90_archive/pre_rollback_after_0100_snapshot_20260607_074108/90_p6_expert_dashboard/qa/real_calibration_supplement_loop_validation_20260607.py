from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "90_p6_expert_dashboard"
QUALITY_DIR = ROOT / "40_quality_evidence"
OUT_JSON = QUALITY_DIR / "real_calibration_supplement_loop_validation_20260607.json"
OUT_MD = QUALITY_DIR / "real_calibration_supplement_loop_validation_20260607.md"
OUT_DIR = QUALITY_DIR / "real_calibration_supplement_loop_validation_20260607"

sys.path.insert(0, str(APP_DIR))
import app  # noqa: E402


def check(condition: bool, check_id: str, message: str, *, evidence: Any = "") -> dict[str, Any]:
    return {
        "check_id": check_id,
        "status": "pass" if condition else "fail",
        "message": message,
        "evidence": evidence,
    }


def docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
    return xml


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
            last_error = f"status={response.status_code}"
        except Exception as exc:  # noqa: BLE001
            last_error = f"{type(exc).__name__}: {exc}"
        time.sleep(0.35)
    raise RuntimeError(f"server not ready: {last_error}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    original_supplements = app.REAL_CALIBRATION_SUPPLEMENT_FILE.read_text(encoding="utf-8") if app.REAL_CALIBRATION_SUPPLEMENT_FILE.exists() else None
    checks: list[dict[str, Any]] = []
    supplement_id = ""
    screenshot_path = OUT_DIR / "report_with_supplement.png"
    server_stdout = ""
    server_stderr = ""

    try:
        client = TestClient(app.app)
        baseline = client.get("/api/simulation/task-preflight").json()
        baseline_count = int(baseline.get("real_calibration_input_count") or 0)
        baseline_supplement_count = int((baseline.get("real_calibration_context") or {}).get("supplement_count") or 0)

        create_payload = {
            "dimension": "income_spending_power",
            "indicator_name": "周边收入与消费能力补充",
            "segment": "奥森周边 1-3 公里目标人群",
            "period": "用户补充 / 待复核",
            "value": "月可支配收入 13500 元/人；休闲餐饮客单 45-75 元",
            "unit": "待复核",
            "source_strength": "local_user_supplement",
            "simulation_use": "用于约束目标人群支付能力、客单价上限、套餐组合和高低价格带配比。",
            "cannot_claim": "不能写成已核验街道收入或真实成交客单。",
            "next_data_needed": "补社区/街道收入来源、样本口径、竞品真实客单、支付笔数和分人群消费结构。",
            "source_file": "QA 临时补充资料",
            "source_page_or_slide": "qa",
            "raw_text_snippet": "QA 临时补充：奥森周边收入与消费能力样本，待真实来源复核。",
            "note": "QA closed-loop supplement; restored after validation.",
        }
        created = client.post("/api/simulation/real-calibration-supplements", json=create_payload)
        checks.append(check(created.status_code == 200, "API-SUPPLEMENT-CREATE", "可新增真实校准补充输入。", evidence=created.status_code))
        created_payload = created.json()
        supplement_id = created_payload.get("item", {}).get("supplement_id", "")
        checks.append(check(bool(supplement_id), "API-SUPPLEMENT-ID", "新增补充输入有稳定编号。", evidence=supplement_id))

        after_create = client.get("/api/simulation/task-preflight").json()
        after_context = after_create.get("real_calibration_context") or {}
        checks.extend(
            [
                check(int(after_create.get("real_calibration_input_count") or 0) == baseline_count + 1, "PREFLIGHT-COUNT-CHANGED", "预检校准输入数量随新增资料增加。", evidence={"before": baseline_count, "after": after_create.get("real_calibration_input_count")}),
                check(int(after_context.get("supplement_count") or 0) == baseline_supplement_count + 1, "PREFLIGHT-SUPPLEMENT-COUNT", "预检上下文记录补充输入数量。", evidence={"before": baseline_supplement_count, "after": after_context.get("supplement_count")}),
                check(any(item.get("indicator_name") == "周边收入与消费能力补充" for item in after_context.get("items", [])), "PREFLIGHT-SUPPLEMENT-ITEM", "新增补充输入进入预检上下文。", evidence=after_context.get("items", [])[:3]),
            ]
        )

        patched = client.patch(
            f"/api/simulation/real-calibration-supplements/{supplement_id}",
            json={
                "value": "月可支配收入 14800 元/人；休闲餐饮客单 55-85 元",
                "raw_text_snippet": "QA 临时更新：周边收入与客单区间提高，仍待真实来源复核。",
            },
        )
        checks.append(check(patched.status_code == 200, "API-SUPPLEMENT-PATCH", "可更新真实校准补充输入并重建。", evidence=patched.status_code))
        after_patch = client.get("/api/simulation/task-preflight").json()
        after_patch_text = json.dumps(after_patch.get("real_calibration_context", {}), ensure_ascii=False)
        checks.append(check("月可支配收入 14800 元/人" in after_patch_text, "PREFLIGHT-PATCH-VISIBLE", "更新后的补充数值进入预检上下文。", evidence="月可支配收入 14800 元/人"))

        job = client.post("/api/simulation/jobs", json={"scenario_name": "qa_real_calibration_supplement_loop", "seed": 20260607, "iterations": 12})
        checks.append(check(job.status_code == 200, "JOB-CREATED", "可基于新增校准输入创建仿真干跑任务。", evidence=job.status_code))
        job_payload = job.json()
        request_json = job_payload.get("job", {}).get("request_json") or {}
        if isinstance(request_json, str):
            request_json = json.loads(request_json)
        checks.append(check(int(request_json.get("real_calibration_input_count") or 0) == baseline_count + 1, "JOB-REQUEST-COUNT-CHANGED", "仿真 job request 记录新增后的校准输入数量。", evidence=request_json.get("real_calibration_input_count")))

        report_response = client.get("/api/reports/site-selection")
        checks.append(check(report_response.status_code == 200, "REPORT-GENERATED", "报告接口可基于新增输入重新生成。", evidence=report_response.status_code))
        report_payload = report_response.json()
        report_context = report_payload.get("report", {}).get("real_calibration_context") or {}
        report_text = json.dumps(report_context, ensure_ascii=False)
        checks.append(check("月可支配收入 14800 元/人" in report_text, "REPORT-JSON-SUPPLEMENT", "报告 JSON 包含更新后的补充校准输入。", evidence=report_context.get("items", [])[:3]))

        md_path = ROOT / "80_delivery" / "site_selection_gap_report_latest.md"
        md_text = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
        checks.append(check("周边收入与消费能力补充" in md_text and "月可支配收入 14800 元/人" in md_text, "REPORT-MD-SUPPLEMENT", "Markdown 报告包含补充校准输入。", evidence=str(md_path.relative_to(ROOT))))

        docx_path = ROOT / "80_delivery" / "osen_integrated_site_selection_report_20260606.docx"
        docx_exists = docx_path.exists() and docx_path.stat().st_size > 40_000
        docx_content = docx_text(docx_path) if docx_exists else ""
        checks.append(check(docx_exists and "周边收入与消费能力补充" in docx_content and "月可支配收入 14800 元/人" in docx_content, "REPORT-DOCX-SUPPLEMENT", "DOCX 报告包含补充校准输入。", evidence={"exists": docx_exists, "bytes": docx_path.stat().st_size if docx_path.exists() else 0}))

        port = choose_free_port()
        base_url = f"http://127.0.0.1:{port}"
        server = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app:app", "--app-dir", "90_p6_expert_dashboard", "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            wait_for_server(server, base_url)
            console_errors: list[str] = []
            with sync_playwright() as p:
                browser = p.chromium.launch(channel="chrome", headless=True)
                page = browser.new_page(viewport={"width": 1440, "height": 1000})
                page.on("console", lambda msg: console_errors.append(f"{msg.type}: {msg.text}") if msg.type == "error" else None)
                page.goto(base_url, wait_until="domcontentloaded")
                page.locator("[data-view='report']").first.click()
                page.locator("#reportView.active").wait_for(state="visible", timeout=8000)
                page.wait_for_timeout(300)
                body_text = page.locator("body").inner_text(timeout=8000)
                page.screenshot(path=str(screenshot_path), full_page=True)
                checks.extend(
                    [
                        check("周边收入与消费能力补充" in body_text, "BROWSER-SUPPLEMENT-VISIBLE", "浏览器报告页可见补充校准指标。", evidence=body_text[:1600]),
                        check("月可支配收入 14800 元/人" in body_text, "BROWSER-PATCHED-VALUE-VISIBLE", "浏览器报告页可见更新后的补充数值。", evidence="月可支配收入 14800 元/人"),
                        check(not console_errors, "BROWSER-CONSOLE-CLEAN", "浏览器报告页无控制台错误。", evidence=console_errors),
                        check(screenshot_path.exists() and screenshot_path.stat().st_size > 100_000, "BROWSER-SCREENSHOT-WRITTEN", "浏览器截图已保存。", evidence={"path": str(screenshot_path.relative_to(ROOT)), "bytes": screenshot_path.stat().st_size if screenshot_path.exists() else 0}),
                    ]
                )
                browser.close()
        finally:
            server.terminate()
            try:
                server_stdout, server_stderr = server.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server_stdout, server_stderr = server.communicate(timeout=5)

    finally:
        if original_supplements is None:
            if app.REAL_CALIBRATION_SUPPLEMENT_FILE.exists():
                app.REAL_CALIBRATION_SUPPLEMENT_FILE.unlink()
        else:
            app.REAL_CALIBRATION_SUPPLEMENT_FILE.write_text(original_supplements, encoding="utf-8")
        try:
            app.rebuild_real_calibration_outputs()
            restore_client = TestClient(app.app)
            restore_client.get("/api/reports/site-selection")
        except Exception as exc:  # noqa: BLE001
            checks.append(check(False, "RESTORE-REBUILD", "恢复原始补充输入后重建失败。", evidence=f"{type(exc).__name__}: {exc}"))

    failures = [item for item in checks if item["status"] != "pass"]
    output = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "pass" if not failures else "fail",
        "failure_count": len(failures),
        "supplement_id": supplement_id,
        "screenshot": str(screenshot_path.relative_to(ROOT)).replace("\\", "/") if screenshot_path.exists() else "",
        "checks": checks,
        "server_stdout_tail": server_stdout[-1000:],
        "server_stderr_tail": server_stderr[-2000:],
        "scope": "验证新增/更新真实校准补充输入会改变输入包、预检、仿真 job request、报告 JSON/MD/DOCX 和浏览器页；测试后恢复原始补充文件。",
    }
    OUT_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# 真实校准补充输入闭环验证（2026-06-07）",
        "",
        f"- 状态：{output['status']}",
        f"- 失败数：{output['failure_count']}",
        f"- 截图：`{output['screenshot']}`",
        "",
        "## 检查项",
    ]
    for item in checks:
        lines.append(f"- `{item['status']}` {item['check_id']}：{item['message']}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": output["status"], "failure_count": output["failure_count"], "json": str(OUT_JSON), "md": str(OUT_MD)}, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
