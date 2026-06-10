from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
HOME = Path.home()
OUT_JSON = ROOT / "40_quality_evidence" / "system_influence_audit_20260608.json"
OUT_MD = ROOT / "40_quality_evidence" / "system_influence_audit_20260608.md"


def run(args: list[str], cwd: Path = ROOT, timeout: int = 20) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return {
            "args": args,
            "returncode": proc.returncode,
            "stdout": (proc.stdout or "").strip()[-4000:],
            "stderr": (proc.stderr or "").strip()[-2000:],
        }
    except Exception as exc:
        return {"args": args, "error": f"{type(exc).__name__}: {exc}"}


def mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "***"
    return value[:4] + "..." + value[-4:]


def env_snapshot() -> dict[str, Any]:
    interesting = [
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "NO_PROXY",
        "PYTHONIOENCODING",
        "PYTHONPATH",
        "PATH",
        "DEEPSEEK_API_KEY",
        "AMAP_WEB_SERVICE_KEY",
        "OPENAI_API_KEY",
    ]
    values: dict[str, Any] = {}
    for key in interesting:
        value = os.environ.get(key) or os.environ.get(key.lower()) or ""
        if not value:
            values[key] = {"present": False}
        elif "KEY" in key or "TOKEN" in key:
            values[key] = {"present": True, "masked": mask(value), "length": len(value)}
        elif key == "PATH":
            values[key] = {"present": True, "entry_count": len(value.split(os.pathsep)), "first_entries": value.split(os.pathsep)[:8]}
        else:
            values[key] = {"present": True, "value": value}
    return values


def port_check(port: int) -> dict[str, Any]:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        open_ = sock.connect_ex(("127.0.0.1", port)) == 0
    return {"port": port, "open": open_}


def count_files(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "exists": False}
    count = 0
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            count += 1
            try:
                total += item.stat().st_size
            except OSError:
                pass
    return {"path": str(path), "exists": True, "file_count": count, "bytes": total}


def profile_snapshot() -> dict[str, Any]:
    profile = HOME / "Documents" / "WindowsPowerShell" / "profile.ps1"
    if not profile.exists():
        return {"path": str(profile), "exists": False}
    text = profile.read_text(encoding="utf-8", errors="replace")
    return {
        "path": str(profile),
        "exists": True,
        "bytes": profile.stat().st_size,
        "has_utf8_defaults": "InputEncoding" in text and "OutputEncoding" in text and "PSDefaultParameterValues" in text,
        "has_conda_init": "conda" in text.lower(),
        "old_path_hits": [token for token in ["wxjw" + "Works", "park_commercial" + "_site_selection_simulation"] if token in text],
    }


def main() -> None:
    codex_dir = HOME / ".codex"
    agents_dir = HOME / ".agents"
    chrome = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    payload: dict[str, Any] = {
        "status": "review",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(ROOT),
        "python": {
            "sys_executable": sys.executable,
            "sys_version": sys.version.replace("\n", " "),
            "py_launcher": run(["py", "-3.12", "-c", "import sys; print(sys.executable); print(sys.version)"]),
        },
        "node": run(["node", "--version"]),
        "npm": run(["npm", "--version"]),
        "git": {
            "status": run(["git", "status", "--short"]),
            "branch": run(["git", "branch", "--show-current"]),
            "lfs": run(["git", "lfs", "env"], timeout=30),
            "remote": run(["git", "remote", "-v"]),
            "config_origins": run(["git", "config", "--show-origin", "--list"], timeout=30),
        },
        "gh": run(["gh", "auth", "status"], timeout=30),
        "env": env_snapshot(),
        "powershell_profile": profile_snapshot(),
        "browser": {"chrome_path": str(chrome), "chrome_exists": chrome.exists(), "chrome_version": run([str(chrome), "--version"]) if chrome.exists() else {}},
        "ports": [port_check(port) for port in [8000, 8081, 8765, 8766, 8794]],
        "workspace_sizes": {
            "archive": count_files(ROOT / "90_archive"),
            "cache": count_files(ROOT / "90_p6_expert_dashboard" / "cache"),
            "test_reports": count_files(ROOT / "TestFiles" / "reports"),
            "llm_runs": count_files(ROOT / "60_model" / "llm_runs"),
            "quality_evidence": count_files(ROOT / "40_quality_evidence"),
        },
        "agent_capability_dirs": {
            "codex_skills": count_files(codex_dir / "skills"),
            "agents_skills": count_files(agents_dir / "skills"),
            "codex_plugins_cache": count_files(codex_dir / "plugins" / "cache"),
        },
    }

    risks: list[dict[str, str]] = []
    env = payload["env"]
    if env.get("HTTP_PROXY", {}).get("present") or env.get("HTTPS_PROXY", {}).get("present") or env.get("ALL_PROXY", {}).get("present"):
        risks.append({"severity": "high", "area": "env", "message": "代理环境变量存在；本地 127.0.0.1 验证必须使用 trust_env=False/no-proxy，避免假 502。"})
    if payload["workspace_sizes"]["archive"].get("file_count", 0):
        risks.append({"severity": "medium", "area": "workspace", "message": "90_archive 存在大量历史产物；全仓脚本必须显式排除或标记 archive，避免旧口径回流。"})
    if payload["ports"][1]["open"]:
        risks.append({"severity": "medium", "area": "runtime", "message": "8081 端口已有服务；跑测试或启动网页前需确认是否为当前版本。"})
    if not payload["browser"]["chrome_exists"]:
        risks.append({"severity": "medium", "area": "browser", "message": "未检测到系统 Chrome，Playwright 会回退浏览器，视觉结果可能与用户浏览器不同。"})
    payload["risks"] = risks
    payload["status"] = "needs_action" if any(r["severity"] == "high" for r in risks) else "review"

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 系统影响面审计",
        "",
        f"- 生成时间：{payload['generated_at']}",
        f"- 状态：{payload['status']}",
        f"- Python：`{payload['python']['sys_executable']}`",
        f"- Chrome：`{payload['browser']['chrome_exists']}`",
        "",
        "## 风险",
        "",
    ]
    if not risks:
        lines.append("- 无高优先级风险。")
    else:
        for risk in risks:
            lines.append(f"- `{risk['severity']}` {risk['area']}：{risk['message']}")
    lines.extend(
        [
            "",
            "## 关键结论",
            "",
            "- 这份审计只读环境，不修改配置。",
            "- 代理、归档目录、运行态端口、全局技能/插件缓存都可能影响当前程序判断。",
            "- 后续修历史问题时，必须先判断命中属于客户可见、当前运行、工程证据、还是归档历史。",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "risk_count": len(risks), "risks": risks}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
