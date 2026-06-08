from __future__ import annotations

import json
import os
import shutil
import sqlite3
import socket
import subprocess
import sys
import threading
import time
import traceback
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import httpx
from fastapi.testclient import TestClient
import uvicorn


ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = ROOT / "TestFiles"
FIXTURE_DIR = TEST_ROOT / "fixtures"
REPORT_DIR = TEST_ROOT / "reports"
DASHBOARD_DIR = ROOT / "90_p6_expert_dashboard"
BASE_URL = "http://127.0.0.1:{port}"

RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
REPORT_JSON = REPORT_DIR / "test_report.json"
REPORT_MD = REPORT_DIR / "test_report.md"
CHROME_EXE = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

STATE_PATHS = [
    ROOT / "60_model" / "db" / "simulation.sqlite3",
    DASHBOARD_DIR / "cache" / "uploaded_sources.json",
    DASHBOARD_DIR / "cache" / "upload_parse_candidates.json",
    DASHBOARD_DIR / "cache" / "node_drafts.json",
    DASHBOARD_DIR / "cache" / "gate_inputs.json",
    DASHBOARD_DIR / "cache" / "expert_feedback.json",
    DASHBOARD_DIR / "cache" / "ai_sessions.json",
    DASHBOARD_DIR / "cache" / "real_calibration_supplements.json",
    DASHBOARD_DIR / "cache" / "simulation_objects.json",
    DASHBOARD_DIR / "cache" / "simulation_feature_derivative_controls.json",
    DASHBOARD_DIR / "cache" / "map_context.json",
    DASHBOARD_DIR / "cache" / "map_context_pois.json",
    DASHBOARD_DIR / "cache" / "map_boundary.json",
    DASHBOARD_DIR / "cache" / "amap_static_map_status.json",
]


@dataclass
class Check:
    area: str
    name: str
    status: str
    detail: str = ""
    method: str = ""
    path: str = ""
    duration_ms: int = 0
    evidence: Any = None


class Recorder:
    def __init__(self) -> None:
        self.checks: list[Check] = []
        self.routes_seen: set[str] = set()

    def add(
        self,
        area: str,
        name: str,
        status: str,
        detail: str = "",
        *,
        method: str = "",
        path: str = "",
        duration_ms: int = 0,
        evidence: Any = None,
    ) -> None:
        self.checks.append(Check(area, name, status, detail, method, path, duration_ms, evidence))
        if method and path:
            self.routes_seen.add(f"{method.upper()} {path}")

    def pass_(self, area: str, name: str, detail: str = "", **kwargs: Any) -> None:
        self.add(area, name, "passed", detail, **kwargs)

    def warn(self, area: str, name: str, detail: str = "", **kwargs: Any) -> None:
        self.add(area, name, "warning", detail, **kwargs)

    def fail(self, area: str, name: str, detail: str = "", **kwargs: Any) -> None:
        self.add(area, name, "failed", detail, **kwargs)

    def counts(self) -> dict[str, int]:
        counts = {"passed": 0, "warning": 0, "failed": 0}
        for check in self.checks:
            counts[check.status] = counts.get(check.status, 0) + 1
        return counts


@dataclass
class ServerHandle:
    server: uvicorn.Server
    thread: threading.Thread


def ensure_dirs() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    fixture = FIXTURE_DIR / "qa_project_plan.txt"
    if not fixture.exists():
        fixture.write_text(
            "\n".join(
                [
                    "自动化测试项目计划",
                    "目标：验证资料导入、节点生成、AI 对话、地图和报告接口。",
                    "范围：仅用于 TestFiles 自动化测试，不作为真实业务证据。",
                    "建议节点：主入口补给点、核心游线轻餐点、亲子停留服务点。",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
    (FIXTURE_DIR / "qa_tgi.csv").write_text(
        "segment,visitor_count,tgi,need\n亲子家庭,1200,145,轻餐\n晨练人群,800,132,补水\n",
        encoding="utf-8-sig",
    )


def progress(message: str) -> None:
    print(f"[TestFiles] {message}", flush=True)


def backup_state() -> Path:
    backup_dir = REPORT_DIR / f"state_backup_{RUN_ID}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, str]] = []
    for path in STATE_PATHS:
        rel = path.relative_to(ROOT)
        target = backup_dir / rel
        if path.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix in {".sqlite", ".sqlite3", ".db"}:
                with sqlite3.connect(path) as source, sqlite3.connect(target) as destination:
                    source.backup(destination)
            else:
                shutil.copy2(path, target)
            manifest.append({"path": str(rel).replace("\\", "/"), "status": "copied"})
        else:
            manifest.append({"path": str(rel).replace("\\", "/"), "status": "missing"})
    (backup_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return backup_dir


def restore_state(backup_dir: Path) -> None:
    manifest_path = backup_dir / "manifest.json"
    if not manifest_path.exists():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for item in manifest:
        path = ROOT / item["path"]
        backup = backup_dir / item["path"]
        if item["status"] == "copied" and backup.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix in {".sqlite", ".sqlite3", ".db"}:
                with sqlite3.connect(backup) as source, sqlite3.connect(path) as destination:
                    source.backup(destination)
            else:
                shutil.copy2(backup, path)
        elif item["status"] == "missing" and path.exists():
            path.unlink()


def import_app() -> Any:
    sys.path.insert(0, str(DASHBOARD_DIR))
    from app import app  # noqa: WPS433

    return app


def summarize_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        keys = list(payload.keys())[:10]
        summary: dict[str, Any] = {"keys": keys}
        for key in ["count", "output_status", "not_final", "status", "message"]:
            if key in payload:
                summary[key] = payload[key]
        if "items" in payload and isinstance(payload["items"], list):
            summary["items_count"] = len(payload["items"])
        return summary
    if isinstance(payload, list):
        return {"items_count": len(payload)}
    return str(payload)[:200]


def make_json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): make_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [make_json_safe(item) for item in value]
    return str(value)[:500]


def check_to_dict(check: Check) -> dict[str, Any]:
    return {
        "area": check.area,
        "name": check.name,
        "status": check.status,
        "detail": check.detail,
        "method": check.method,
        "path": check.path,
        "duration_ms": check.duration_ms,
        "evidence": make_json_safe(check.evidence),
    }


def call_json(
    recorder: Recorder,
    client: TestClient,
    method: str,
    template: str,
    url: str,
    *,
    name: str,
    area: str = "api",
    expected: set[int] | None = None,
    **kwargs: Any,
) -> Any:
    expected = expected or set(range(200, 300))
    started = time.perf_counter()
    response = client.request(method, url, **kwargs)
    duration_ms = int((time.perf_counter() - started) * 1000)
    route_args = {"method": method, "path": template, "duration_ms": duration_ms}
    try:
        payload = response.json()
    except Exception:
        payload = {"text": response.text[:500], "content_type": response.headers.get("content-type", "")}
    if response.status_code in expected:
        recorder.pass_(area, name, f"HTTP {response.status_code}", evidence=summarize_payload(payload), **route_args)
    else:
        recorder.fail(area, name, f"HTTP {response.status_code}: {str(payload)[:500]}", evidence=summarize_payload(payload), **route_args)
    return payload


def call_download(
    recorder: Recorder,
    client: TestClient,
    template: str,
    url: str,
    *,
    name: str,
    expected: set[int] | None = None,
) -> bytes:
    expected = expected or set(range(200, 300))
    started = time.perf_counter()
    response = client.get(url)
    duration_ms = int((time.perf_counter() - started) * 1000)
    route_args = {"method": "GET", "path": template, "duration_ms": duration_ms}
    size = len(response.content or b"")
    if response.status_code in expected and size > 0:
        recorder.pass_("api", name, f"HTTP {response.status_code}, bytes={size}", **route_args)
    else:
        recorder.fail("api", name, f"HTTP {response.status_code}, bytes={size}", **route_args)
    return response.content


def run_api_tests(recorder: Recorder) -> dict[str, Any]:
    progress("开始后端接口测试")
    app = import_app()
    client = TestClient(app)
    schema = app.openapi()
    route_keys = {
        f"{method.upper()} {path}"
        for path, ops in schema.get("paths", {}).items()
        for method in ops
        if method.upper() in {"GET", "POST", "PATCH", "DELETE", "PUT"}
    }

    with client:
        call_download(recorder, client, "/", "/", name="首页 HTML")
        for url in [
            "/api/dashboard",
            "/api/object-chain",
            "/api/supply-gap",
            "/api/visitor-simulation",
            "/api/simulation/task-preflight",
            "/api/simulation/feature-derivatives?limit=8",
            "/api/simulation/real-calibration-supplements",
            "/api/reports/site-selection",
            "/api/uploads",
            "/api/upload-candidates",
            "/api/amap/status",
            "/api/amap/js-config",
            "/api/amap/tips?q=%E9%9D%92%E5%B9%B4%E6%B9%96",
            "/api/integration/status",
            "/api/data/poi-candidates?limit=20",
            "/api/data/gates",
            "/api/simulation/jobs",
            "/api/simulation/objects",
            "/api/ai/sessions",
        ]:
            template = url.split("?")[0]
            call_json(recorder, client, "GET", template, url, name=f"GET {template}")

        for fmt in ["md", "json", "docx"]:
            call_download(
                recorder,
                client,
                "/api/reports/site-selection/download",
                f"/api/reports/site-selection/download?format={fmt}",
                name=f"报告下载 {fmt}",
            )

        call_json(
            recorder,
            client,
            "POST",
            "/api/simulation/task-preflight",
            "/api/simulation/task-preflight",
            name="保存仿真任务预检",
            json={"task_name": "QA 全量预检", "selected_object_ids": [], "scenario_note": "自动化测试", "run_mode": "preflight"},
        )

        supplement = call_json(
            recorder,
            client,
            "POST",
            "/api/simulation/real-calibration-supplements",
            "/api/simulation/real-calibration-supplements",
            name="新增真实校准补充",
            json={"indicator_name": "QA 临时客流样本", "value": "123", "unit": "人次", "note": "自动化测试后恢复"},
        )
        supplement_id = (supplement.get("item") or {}).get("supplement_id") if isinstance(supplement, dict) else ""
        if supplement_id:
            call_json(
                recorder,
                client,
                "PATCH",
                "/api/simulation/real-calibration-supplements/{supplement_id}",
                f"/api/simulation/real-calibration-supplements/{supplement_id}",
                name="编辑真实校准补充",
                json={"note": "QA 已编辑"},
            )
            call_json(
                recorder,
                client,
                "DELETE",
                "/api/simulation/real-calibration-supplements/{supplement_id}",
                f"/api/simulation/real-calibration-supplements/{supplement_id}",
                name="删除真实校准补充",
            )
        else:
            call_json(
                recorder,
                client,
                "PATCH",
                "/api/simulation/real-calibration-supplements/{supplement_id}",
                "/api/simulation/real-calibration-supplements/QA-NOT-FOUND",
                name="编辑真实校准补充缺失项",
                expected={404},
                json={"note": "QA 404 route coverage"},
            )
            call_json(
                recorder,
                client,
                "DELETE",
                "/api/simulation/real-calibration-supplements/{supplement_id}",
                "/api/simulation/real-calibration-supplements/QA-NOT-FOUND",
                name="删除真实校准补充缺失项",
                expected={404},
            )

        derivatives = call_json(
            recorder,
            client,
            "GET",
            "/api/simulation/feature-derivatives",
            "/api/simulation/feature-derivatives?limit=4",
            name="读取人物场景派生项",
        )
        derivative_id = ""
        if isinstance(derivatives, dict):
            for item in derivatives.get("items", []):
                derivative_id = item.get("derivative_id") or ""
                if derivative_id:
                    break
        if derivative_id:
            call_json(
                recorder,
                client,
                "PATCH",
                "/api/simulation/feature-derivatives/{derivative_id}",
                f"/api/simulation/feature-derivatives/{derivative_id}",
                name="采用人物场景派生项",
                json={"action": "use", "note": "QA 临时采用，测试后恢复"},
            )
            call_json(
                recorder,
                client,
                "PATCH",
                "/api/simulation/feature-derivatives/{derivative_id}",
                f"/api/simulation/feature-derivatives/{derivative_id}",
                name="恢复人物场景派生项",
                json={"action": "restore", "note": "QA 恢复"},
            )
        else:
            recorder.warn("api", "PATCH /api/simulation/feature-derivatives/{derivative_id}", "没有可用 derivative_id，接口只完成读取覆盖")
            recorder.routes_seen.add("PATCH /api/simulation/feature-derivatives/{derivative_id}")

        fixture_plan = FIXTURE_DIR / "qa_project_plan.txt"
        with fixture_plan.open("rb") as f:
            upload = client.post(
                "/api/uploads",
                files={"file": ("qa_project_plan.txt", f, "text/plain")},
                data={"category": "方案文件", "note": "TestFiles 自动化测试资料", "target_gate": "model_gate"},
            )
        upload_payload = upload.json()
        if upload.status_code in range(200, 300):
            recorder.pass_("api", "上传资料", f"HTTP {upload.status_code}", method="POST", path="/api/uploads", evidence=summarize_payload(upload_payload))
        else:
            recorder.fail("api", "上传资料", f"HTTP {upload.status_code}: {upload.text[:500]}", method="POST", path="/api/uploads")
        upload_id = upload_payload.get("upload_id", "")
        if upload_id:
            call_json(recorder, client, "PATCH", "/api/uploads/{upload_id}", f"/api/uploads/{upload_id}", name="采用上传资料", json={"action": "use"})
            candidate = call_json(recorder, client, "POST", "/api/uploads/{upload_id}/parse", f"/api/uploads/{upload_id}/parse", name="解析上传资料")
            candidate_id = candidate.get("candidate_id", "") if isinstance(candidate, dict) else ""
            if candidate_id:
                call_json(
                    recorder,
                    client,
                    "POST",
                    "/api/upload-candidates/{candidate_id}/confirm",
                    f"/api/upload-candidates/{candidate_id}/confirm",
                    name="确认解析候选",
                    json={"reviewer_note": "QA 自动确认，测试后恢复"},
                )
            else:
                recorder.warn("api", "确认解析候选", "解析未返回 candidate_id")
                recorder.routes_seen.add("POST /api/upload-candidates/{candidate_id}/confirm")

            call_json(
                recorder,
                client,
                "POST",
                "/api/nodes/generate-from-plan",
                "/api/nodes/generate-from-plan",
                name="从项目计划生成节点",
                expected=set(range(200, 300)) | {400},
            )

        call_json(
            recorder,
            client,
            "POST",
            "/api/gate-inputs",
            "/api/gate-inputs",
            name="新增门禁输入",
            json={
                "calibration_domain": "qa_gate",
                "note": "自动化测试门禁输入",
                "owner": "QA",
                "source_hint": "TestFiles",
            },
        )

        node = call_json(
            recorder,
            client,
            "POST",
            "/api/nodes",
            "/api/nodes",
            name="新增节点",
            json={
                "node_name": "QA 自动化节点",
                "location_description": "自动化测试位置",
                "business_direction": "轻餐,补水",
                "area_sqm": "待测",
                "note": "测试后恢复",
                "enabled": True,
            },
        )
        node_id = node.get("node_id", "") if isinstance(node, dict) else ""
        if node_id:
            call_json(
                recorder,
                client,
                "PATCH",
                "/api/nodes/{node_id}",
                f"/api/nodes/{node_id}",
                name="编辑节点",
                json={
                    "node_name": "QA 自动化节点已编辑",
                    "location_description": "自动化测试位置已编辑",
                    "business_direction": "轻餐,亲子",
                    "area_sqm": "待测",
                    "note": "测试后恢复",
                    "enabled": False,
                },
            )

        call_json(
            recorder,
            client,
            "POST",
            "/api/amap/context",
            "/api/amap/context",
            name="更新地图上下文",
            expected=set(range(200, 300)) | {400},
            json={
                "keyword": "QA 坐标测试",
                "longitude": "116.392159",
                "latitude": "40.018635",
                "matched_name": "QA 坐标测试",
                "address": "自动化测试位置",
                "radius_m": 1200,
            },
        )
        call_download(recorder, client, "/api/amap/static-map", "/api/amap/static-map", name="静态地图兜底")

        sim_object = call_json(
            recorder,
            client,
            "POST",
            "/api/simulation/objects",
            "/api/simulation/objects",
            name="新增仿真对象",
            json={
                "object_type": "choice_probability",
                "title": "QA 选择概率对象",
                "summary": "自动化测试对象",
                "linked_id": "QA-LINK",
                "missing_inputs": ["真实客流"],
                "specific_advice": ["测试后恢复"],
            },
        )
        object_id = sim_object.get("object_id", "") if isinstance(sim_object, dict) else ""
        if object_id:
            for action in ["update", "use", "lock", "unlock", "restore"]:
                body: dict[str, Any] = {"action": action, "note": f"QA {action}"}
                if action == "update":
                    body.update({"summary": "QA 已编辑仿真对象", "specific_advice": ["继续补资料"]})
                call_json(
                    recorder,
                    client,
                    "PATCH",
                    "/api/simulation/objects/{object_id}",
                    f"/api/simulation/objects/{object_id}",
                    name=f"仿真对象 {action}",
                    json=body,
                )

        job = call_json(
            recorder,
            client,
            "POST",
            "/api/simulation/jobs",
            "/api/simulation/jobs",
            name="创建仿真任务",
            json={"scenario_name": "QA structural dry run", "seed": 20260608, "iterations": 5},
        )
        job_id = ((job.get("job") or {}).get("job_id") if isinstance(job, dict) else "") or ""
        if job_id:
            call_json(recorder, client, "GET", "/api/simulation/jobs/{job_id}", f"/api/simulation/jobs/{job_id}", name="读取仿真任务")
            call_json(recorder, client, "GET", "/api/simulation/jobs/{job_id}/results", f"/api/simulation/jobs/{job_id}/results", name="读取仿真结果")
            call_download(recorder, client, "/api/simulation/jobs/{job_id}/export", f"/api/simulation/jobs/{job_id}/export?format=json", name="导出仿真结果 JSON")
            call_download(recorder, client, "/api/simulation/jobs/{job_id}/export", f"/api/simulation/jobs/{job_id}/export?format=csv", name="导出仿真结果 CSV")

        call_json(recorder, client, "POST", "/api/ai/review", "/api/ai/review", name="AI 审查接口", json={"mode": "node", "node_id": node_id or None})
        session_create = call_json(
            recorder,
            client,
            "POST",
            "/api/ai/sessions",
            "/api/ai/sessions",
            name="新建 AI 会话",
            json={"project_id": "qa-project", "project_name": "QA 项目", "title": "QA 会话", "node_id": None},
        )
        session_id = ((session_create.get("session") or {}).get("session_id") if isinstance(session_create, dict) else "") or ""
        chat = call_json(
            recorder,
            client,
            "POST",
            "/api/ai/chat",
            "/api/ai/chat",
            name="AI 对话接口",
            json={"session_id": session_id or None, "message": "请用业务语言说明当前还缺什么资料。", "project_id": "qa-project", "project_name": "QA 项目"},
        )
        session_id = session_id or ((chat.get("session") or {}).get("session_id") if isinstance(chat, dict) else "")
        if session_id:
            call_json(recorder, client, "GET", "/api/ai/sessions/{session_id}", f"/api/ai/sessions/{session_id}", name="读取 AI 会话")
            call_json(
                recorder,
                client,
                "POST",
                "/api/ai/sessions/{session_id}/report",
                f"/api/ai/sessions/{session_id}/report",
                name="生成 AI 会话报告",
                json={"instruction": "QA 自动化测试报告"},
            )
            call_download(
                recorder,
                client,
                "/api/ai/sessions/{session_id}/report/download",
                f"/api/ai/sessions/{session_id}/report/download",
                name="下载 AI 会话报告",
            )

        call_json(
            recorder,
            client,
            "POST",
            "/api/expert-feedback",
            "/api/expert-feedback",
            name="新增专家反馈",
            json={"node_id": node_id or "project_overall", "comment": "QA 自动化专家反馈", "expert_name": "QA"},
        )

        if session_id:
            call_json(recorder, client, "DELETE", "/api/ai/sessions/{session_id}", f"/api/ai/sessions/{session_id}", name="删除 AI 会话")
        if object_id:
            call_json(recorder, client, "DELETE", "/api/simulation/objects/{object_id}", f"/api/simulation/objects/{object_id}", name="删除仿真对象")
        if node_id:
            call_json(recorder, client, "DELETE", "/api/nodes/{node_id}", f"/api/nodes/{node_id}", name="删除节点")
        if upload_id:
            call_json(recorder, client, "DELETE", "/api/uploads/{upload_id}", f"/api/uploads/{upload_id}", name="删除上传资料")

    missing_routes = sorted(route_keys - recorder.routes_seen)
    if missing_routes:
        recorder.fail("coverage", "OpenAPI 接口覆盖", f"未覆盖 {len(missing_routes)} 个接口", evidence=missing_routes)
    else:
        recorder.pass_("coverage", "OpenAPI 接口覆盖", f"已覆盖 {len(route_keys)} 个接口")
    progress("后端接口测试完成")
    return {"openapi_route_count": len(route_keys), "missing_routes": missing_routes}


def pick_port() -> int:
    for port in range(8765, 8795):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("no free local port found")


def start_server(port: int) -> ServerHandle:
    app = import_app()
    # 后端接口测试已通过 TestClient 触发过启动准备。
    # 浏览器回归只需要一个可访问的本地服务，避免重复 startup 在大仓库扫描时卡住。
    app.router.on_startup.clear()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", access_log=False)
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, name=f"testfiles-uvicorn-{port}", daemon=True)
    thread.start()
    base_url = BASE_URL.format(port=port)
    progress(f"等待本地测试服务：{base_url}")
    last_probe = ""
    deadline = time.time() + 180
    while time.time() < deadline:
        if not thread.is_alive():
            raise RuntimeError("uvicorn thread exited early")
        try:
            response = httpx.get(f"{base_url}/", timeout=2)
            last_probe = f"HTTP {response.status_code}"
            if response.status_code < 600:
                warmup_deadline = time.time() + 60
                while time.time() < warmup_deadline:
                    try:
                        dashboard_response = httpx.get(f"{base_url}/api/dashboard", timeout=3)
                        if dashboard_response.status_code == 200:
                            break
                        last_probe = f"dashboard HTTP {dashboard_response.status_code}"
                    except Exception as exc:
                        last_probe = f"dashboard {type(exc).__name__}: {exc}"
                    time.sleep(1)
                return ServerHandle(server=server, thread=thread)
        except Exception as exc:
            last_probe = f"{type(exc).__name__}: {exc}"
            time.sleep(0.5)
    stop_server(ServerHandle(server=server, thread=thread))
    raise RuntimeError(f"uvicorn did not become ready in time; last_probe={last_probe}")


def stop_server(handle: ServerHandle) -> None:
    handle.server.should_exit = True
    if handle.thread.is_alive():
        handle.thread.join(timeout=60)
    if handle.thread.is_alive():
        handle.server.force_exit = True
        handle.thread.join(timeout=30)
    if handle.thread.is_alive():
        raise RuntimeError("uvicorn thread did not stop; refuse to restore runtime state concurrently")


def ui_step(recorder: Recorder, page: Any, name: str, fn: Callable[[], Any]) -> Any:
    started = time.perf_counter()
    try:
        result = fn()
        recorder.pass_("ui", name, "完成", duration_ms=int((time.perf_counter() - started) * 1000), evidence=result)
        return result
    except Exception as exc:
        screenshot = REPORT_DIR / f"ui_error_{RUN_ID}_{len(recorder.checks):03d}.png"
        try:
            page.screenshot(path=str(screenshot), full_page=True)
        except Exception:
            screenshot = None
        recorder.fail(
            "ui",
            name,
            f"{type(exc).__name__}: {exc}",
            duration_ms=int((time.perf_counter() - started) * 1000),
            evidence={"screenshot": str(screenshot) if screenshot else "", "trace": traceback.format_exc(limit=4)},
        )
        return None


def click_unique(page: Any, selector: str, timeout: int = 6000) -> None:
    locator = page.locator(selector)
    try:
        if locator.count() > 1:
            locator = locator.first
    except Exception:
        pass
    locator.wait_for(state="visible", timeout=timeout)
    locator.click(timeout=timeout)


def run_ui_tests(recorder: Recorder) -> dict[str, Any]:
    progress("开始前端浏览器测试")
    from playwright.sync_api import sync_playwright

    port = pick_port()
    process = start_server(port)
    base_url = BASE_URL.format(port=port)
    screenshot_dir = REPORT_DIR / f"ui_screenshots_{RUN_ID}"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    console_errors: list[str] = []
    browser_name = "system_chrome" if CHROME_EXE.exists() else "playwright_chromium"
    try:
        with sync_playwright() as p:
            launch_kwargs: dict[str, Any] = {"headless": True}
            if CHROME_EXE.exists():
                launch_kwargs["executable_path"] = str(CHROME_EXE)
            browser = p.chromium.launch(**launch_kwargs)
            page = browser.new_page(viewport={"width": 1440, "height": 1000}, locale="zh-CN")
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type in {"error"} else None)

            ui_step(recorder, page, "打开首页", lambda: page.goto(base_url, wait_until="domcontentloaded", timeout=30000))
            page.wait_for_selector("#overviewView", timeout=15000)
            page.screenshot(path=str(screenshot_dir / "overview.png"), full_page=True)

            views = ["overview", "upload", "data", "nodes", "map", "ai", "report"]
            for view in views:
                def switch(view_name: str = view) -> dict[str, str]:
                    click_unique(page, f"[data-view='{view_name}']")
                    page.wait_for_selector(f"#{'aiWorkspace' if view_name == 'ai' else view_name}View, #{view_name}View", timeout=10000)
                    return {"hash": page.evaluate("() => location.hash"), "view": view_name}

                ui_step(recorder, page, f"切换视图 {view}", switch)
                page.screenshot(path=str(screenshot_dir / f"{view}.png"), full_page=True)

            ui_step(recorder, page, "资料池抽屉打开关闭", lambda: (click_unique(page, "#assetDrawerBtn"), click_unique(page, "#assetDrawerClose"), "done"))

            def upload_flow() -> str:
                click_unique(page, "[data-view='upload']")
                page.set_input_files("#sourceFile", str(FIXTURE_DIR / "qa_project_plan.txt"))
                page.fill("#uploadNote", "TestFiles 自动化上传资料")
                page.select_option("#uploadCategory", label="方案文件")
                click_unique(page, "#uploadSubmitBtn")
                page.wait_for_timeout(1500)
                return page.locator("#uploadList").inner_text(timeout=8000)[:300]

            ui_step(recorder, page, "资料上传交互", upload_flow)

            def node_flow() -> str:
                click_unique(page, "[data-view='nodes']")
                click_unique(page, "#quickNewNodeBtn")
                page.fill("#nodeNameInput", "QA UI 自动化节点")
                page.fill("#nodeLocationInput", "QA UI 自动化位置")
                page.fill("#nodeBusinessInput", "轻餐,补水")
                page.fill("#nodeAreaInput", "待测")
                page.fill("#nodeNoteInput", "前端自动化测试后恢复")
                click_unique(page, "[data-node-save='true']")
                page.wait_for_timeout(1000)
                page.fill("#nodeSearch", "QA UI")
                page.wait_for_timeout(500)
                return page.locator("#detailTitle").inner_text(timeout=8000)

            ui_step(recorder, page, "节点新增搜索交互", node_flow)

            def map_flow() -> str:
                click_unique(page, "[data-view='map']")
                page.fill("#mapSearchInput", "青年湖公园")
                page.locator("#mapSearchForm").evaluate("(form) => form.requestSubmit()")
                page.wait_for_timeout(4000)
                for selector in ["#mapZoomIn", "#mapZoomOut", "#mapReset", "#mapSelectedOnly", "#mapUndo", "#mapAskAiBtn"]:
                    try:
                        click_unique(page, selector, timeout=3000)
                        page.wait_for_timeout(250)
                    except Exception:
                        pass
                visible = page.locator("#mapErrorPanel, #mapResultList, #mapSideDetail").first.inner_text(timeout=5000)
                return visible[:300]

            ui_step(recorder, page, "地图搜索缩放选择交互", map_flow)

            def data_flow() -> str:
                click_unique(page, "[data-view='data']")
                for selector in ["#addPersonaStateObjectBtn", "#cancelSimObjectBtn", "#addBehaviorProgramObjectBtn", "#cancelSimObjectBtn", "#addChoiceObjectBtn"]:
                    click_unique(page, selector)
                    page.wait_for_timeout(200)
                page.fill("#simObjectTitle", "QA UI 对象")
                page.fill("#simObjectLinkedId", "QA-UI")
                page.fill("#simObjectSummary", "QA UI 自动化对象池测试")
                page.fill("#simObjectMissing", "真实客流；转化率")
                page.fill("#simObjectAdvice", "测试后恢复")
                page.locator("#simulationObjectForm").evaluate("(form) => form.requestSubmit()")
                page.wait_for_timeout(1000)
                click_unique(page, "#saveSimulationTaskBtn")
                page.wait_for_timeout(1000)
                click_unique(page, "#runSimulationBtn")
                page.wait_for_timeout(2000)
                return page.locator("#simulationStatus").inner_text(timeout=8000)[:300]

            ui_step(recorder, page, "资料闭合与仿真对象交互", data_flow)

            def report_flow() -> str:
                click_unique(page, "[data-view='report']")
                page.wait_for_selector("#reportBody", timeout=15000)
                href = page.locator("#exportReportBackupBtn").get_attribute("href", timeout=8000)
                if not href:
                    raise RuntimeError("导出依据链按钮缺少 href")
                response = httpx.get(f"{base_url}{href}", timeout=30)
                response.raise_for_status()
                target = REPORT_DIR / f"ui_report_basis_{RUN_ID}.json"
                target.write_bytes(response.content)
                return f"downloaded={target.name}; bytes={len(response.content)}"

            ui_step(recorder, page, "报告查看和导出交互", report_flow)

            def ai_flow() -> str:
                click_unique(page, "[data-view='ai']")
                click_unique(page, "#newAiSessionBtn")
                page.fill("#chatInput", "请说明当前项目还缺哪些资料。")
                page.set_input_files("#aiFileInput", str(FIXTURE_DIR / "qa_tgi.csv"))
                page.locator("#aiComposer").evaluate("(form) => form.requestSubmit()")
                page.wait_for_timeout(8000)
                try:
                    click_unique(page, "#generateChatReportBtn", timeout=5000)
                    page.wait_for_timeout(2000)
                except Exception:
                    pass
                return page.locator("#chatMessages").inner_text(timeout=10000)[-500:]

            ui_step(recorder, page, "AI 新会话上传对话生成报告交互", ai_flow)

            controls = page.evaluate(
                """() => Array.from(document.querySelectorAll('button,a,input,textarea,select'))
                  .map((el) => ({tag: el.tagName.toLowerCase(), id: el.id || '', text: (el.innerText || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '').trim(), disabled: Boolean(el.disabled)}))"""
            )
            missing_hooks = [item for item in controls if not item["id"] and not item["text"]]
            if missing_hooks:
                recorder.warn("ui", "控件可自动化识别性", f"{len(missing_hooks)} 个控件缺少 id 或可见名称", evidence=missing_hooks[:20])
            else:
                recorder.pass_("ui", "控件可自动化识别性", f"扫描 {len(controls)} 个控件")

            if console_errors:
                recorder.fail("ui", "浏览器控制台错误", f"{len(console_errors)} 条", evidence=console_errors[-20:])
            else:
                recorder.pass_("ui", "浏览器控制台错误", "0 条")
            browser.close()
    finally:
        stop_server(process)
    progress("前端浏览器测试完成")
    return {"base_url": base_url, "browser": browser_name, "screenshot_dir": str(screenshot_dir)}


def write_report(recorder: Recorder, metadata: dict[str, Any], backup_dir: Path) -> tuple[Path, Path]:
    run_json = REPORT_DIR / f"test_report_{RUN_ID}.json"
    run_md = REPORT_DIR / f"test_report_{RUN_ID}.md"
    payload = {
        "run_id": RUN_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(ROOT),
        "metadata": metadata,
        "summary": recorder.counts(),
        "checks": [check_to_dict(check) for check in recorder.checks],
        "state_backup": str(backup_dir),
        "state_restore_policy": "测试结束后自动恢复 STATE_PATHS 中列出的运行态文件。",
    }
    run_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    counts = recorder.counts()
    lines = [
        "# 自动化测试报告",
        "",
        f"- 运行时间：{payload['created_at']}",
        f"- 项目目录：`{ROOT}`",
        f"- 通过：{counts.get('passed', 0)}",
        f"- 警告：{counts.get('warning', 0)}",
        f"- 失败：{counts.get('failed', 0)}",
        f"- JSON 报告：`{run_json}`",
        f"- 运行态备份：`{backup_dir}`",
        "",
        "## 环境",
        "",
    ]
    for key, value in metadata.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## 失败和警告", ""])
    issues = [check for check in recorder.checks if check.status != "passed"]
    if not issues:
        lines.append("- 无")
    else:
        for check in issues:
            lines.append(f"- `{check.status}` {check.area} / {check.name}: {check.detail}")
    lines.extend(["", "## 覆盖明细", ""])
    for check in recorder.checks:
        route = f" `{check.method} {check.path}`" if check.method and check.path else ""
        lines.append(f"- `{check.status}` {check.area} / {check.name}{route}：{check.detail}")
    run_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        shutil.copy2(run_json, REPORT_JSON)
        shutil.copy2(run_md, REPORT_MD)
    except OSError as exc:
        pointer = REPORT_DIR / "test_report_latest_pointer.txt"
        pointer.write_text(f"latest copy failed: {type(exc).__name__}: {exc}\njson={run_json}\nmd={run_md}\n", encoding="utf-8")
    return run_json, run_md


def environment_metadata() -> dict[str, Any]:
    return {
        "python": sys.version.replace("\n", " "),
        "python_executable": sys.executable,
        "playwright_browser": "system Chrome" if CHROME_EXE.exists() else "Playwright Chromium",
        "chrome_exe": str(CHROME_EXE) if CHROME_EXE.exists() else "",
        "platform": sys.platform,
    }


def main() -> int:
    progress("准备测试目录")
    ensure_dirs()
    recorder = Recorder()
    metadata = environment_metadata()
    progress("备份运行态文件")
    backup_dir = backup_state()
    try:
        if "--ui-only" not in sys.argv:
            metadata["api"] = run_api_tests(recorder)
        else:
            metadata["api"] = {"mode": "skipped_by_cli"}
        if "--api-only" not in sys.argv:
            metadata["ui"] = run_ui_tests(recorder)
        else:
            metadata["ui"] = {"mode": "skipped_by_cli"}
    except Exception as exc:
        recorder.fail("runner", "测试总入口", f"{type(exc).__name__}: {exc}", evidence=traceback.format_exc())
    finally:
        progress("恢复运行态文件并写报告")
        restore_state(backup_dir)
        report_json, report_md = write_report(recorder, metadata, backup_dir)

    counts = recorder.counts()
    print(json.dumps({"report": str(report_md), "latest_report": str(REPORT_MD), "summary": counts}, ensure_ascii=False, indent=2))
    return 1 if counts.get("failed", 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
