from __future__ import annotations

import json
import os
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HOME = Path.home()
OUT_JSON = ROOT / "40_quality_evidence" / "agent_editor_influence_surface_audit_20260609.json"
OUT_MD = ROOT / "40_quality_evidence" / "agent_editor_influence_surface_audit_20260609.md"

MAX_TEXT_BYTES = 1_500_000
MAX_FILES_PER_ROOT = 20_000
MAX_FINDINGS_PER_FILE = 20
RECENT_CUTOFF = datetime(2026, 6, 1).timestamp()

BINARY_SUFFIXES = {
    ".7z",
    ".bin",
    ".bmp",
    ".db",
    ".dll",
    ".docx",
    ".dwg",
    ".dxf",
    ".exe",
    ".gif",
    ".ico",
    ".jpg",
    ".jpeg",
    ".mp4",
    ".pdf",
    ".png",
    ".pptx",
    ".pyc",
    ".sqlite",
    ".sqlite3",
    ".ttf",
    ".webp",
    ".xlsx",
    ".zip",
}

SKIP_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "node_modules",
    "Cache",
    "Code Cache",
    "GPUCache",
    "CachedData",
    "Crashpad",
    "extensions",
    "logs",
    "log",
    "tmp",
    ".tmp",
    ".sandbox",
    ".sandbox-bin",
    ".sandbox-secrets",
    "plugins",
    "vendor_imports",
    "node_repl",
}

IMPORTANT_FILENAMES = {
    ".claude.json",
    ".codex-global-state.json",
    "AGENTS.md",
    "CODEX_LEARNING_MEMORY.md",
    "MEMORY.md",
    "config.toml",
    "keybindings.json",
    "launch.json",
    "session_index.jsonl",
    "settings.json",
    "tasks.json",
}

TEXT_SUFFIXES = {
    "",
    ".cfg",
    ".code-workspace",
    ".csv",
    ".json",
    ".jsonl",
    ".md",
    ".ps1",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

PROJECT_FOCUS_PATHS = {
    "AGENTS.md",
    "CONTEXT.md",
    "README.md",
    "findings.md",
    "handoff_next_chat.md",
    "next_chat_prompt.md",
    "progress.md",
}

PROJECT_FOCUS_PREFIXES = (
    "00_control/",
    "10_research/",
    "30_extraction/scripts/",
    "40_quality_evidence/",
    "50_external_gis/scripts/",
    "60_model/schemas/",
    "60_model/scripts/",
    "60_model/simulation/",
    "80_delivery/",
    "90_p6_expert_dashboard/",
    "TestFiles/",
)


@dataclass
class Finding:
    area: str
    root: str
    path: str
    line: int
    kind: str
    term: str
    severity: str
    text: str


def existing_roots() -> list[tuple[str, Path]]:
    candidates: list[tuple[str, Path]] = [
        ("project_workspace", ROOT),
        ("codex_global", HOME / ".codex"),
        ("agents_global", HOME / ".agents"),
        ("claude_global", HOME / ".claude"),
        ("codex_vscode", HOME / ".codex-vscode"),
        ("cursor_global", HOME / ".cursor"),
        ("vscode_user", Path(os.environ.get("APPDATA", "")) / "Code" / "User"),
        ("cursor_user", Path(os.environ.get("APPDATA", "")) / "Cursor" / "User"),
    ]
    return [(name, path) for name, path in candidates if path.exists()]


PROJECT_MARKERS = {
    "workspace_path": re.compile(re.escape(str(ROOT)), re.IGNORECASE),
    "workspace_name": re.compile("仿真设计"),
    "repo_name": re.compile("park-commercial-site-selection-simulation", re.IGNORECASE),
    "repo_slug_underscore": re.compile("park_commercial" + "_site_selection_simulation", re.IGNORECASE),
    "domain_name": re.compile("公园商业选址|商业选址仿真|公园商业"),
    "osen": re.compile("奥森|osen", re.IGNORECASE),
    "dashboard": re.compile("90_p6_expert_dashboard|site_selection_gap|simulationObjectPool", re.IGNORECASE),
}

COLLISION_TERMS = {
    "old_default_node": re.compile(r"\b" + "N" + r"-001\b|QA UI 自动化节点"),
    "legacy_preview": re.compile("external" + "_preview_only|" + "外部" + "预览|" + "仅地图" + "预览"),
    "client_asks_for_more": re.compile("请" + "补|" + "补" + "齐|" + "补" + "资料|" + "训练" + "资料"),
    "wrong_scope": re.compile("青年湖"),
    "foreign_path": re.compile("G" + r":\\|" + "wxjw" + r"Works|works\\park" + "_commercial", re.IGNORECASE),
    "internal_state": re.compile(r"\bneeds_review\b|\bnot_final\b"),
}


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if parts & SKIP_PARTS:
        return True
    if path.suffix.lower() in BINARY_SUFFIXES:
        return True
    try:
        return path.stat().st_size > MAX_TEXT_BYTES
    except OSError:
        return True


def is_recent(path: Path) -> bool:
    try:
        return path.stat().st_mtime >= RECENT_CUTOFF
    except OSError:
        return False


def is_project_candidate(path: Path) -> bool:
    try:
        rel = path.relative_to(ROOT).as_posix()
    except ValueError:
        return False
    return rel in PROJECT_FOCUS_PATHS or any(rel.startswith(prefix) for prefix in PROJECT_FOCUS_PREFIXES)


def is_global_candidate(area: str, root: Path, path: Path) -> bool:
    if path.name in IMPORTANT_FILENAMES:
        return True
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return False
    rel = rel_to(root, path).replace("\\", "/")
    lower = rel.lower()
    if any(part in lower for part in ("memory", "memories", "handoff", "prompt", "settings", "rules", "agents")):
        return True
    if area in {"vscode_user", "cursor_user"}:
        return "workspace" in lower or "state" in lower
    if area in {"codex_global", "claude_global", "codex_vscode", "cursor_global"}:
        if lower.startswith(("sessions/", "archived_sessions/")):
            return is_recent(path)
        if any(part in lower for part in ("state", "session_index", "computer-use")):
            return is_recent(path)
    return is_recent(path)


def read_text(path: Path) -> str | None:
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
        except OSError:
            return None
    return None


def rel_to(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def severity_for(area: str, path: str, kind: str) -> str:
    normalized = path.replace("\\", "/").lower()
    if area == "project_workspace":
        if normalized.startswith(("90_archive/", "60_model/llm_runs/", "80_delivery/ai_chat_reports/")):
            return "archive"
        if normalized.startswith(("80_delivery/codex_", "80_delivery/scripts/")):
            return "archive"
        if normalized in {
            "progress.md",
            "findings.md",
            "handoff_next_chat.md",
            "next_chat_prompt.md",
        }:
            return "high" if kind != "internal_state" else "medium"
        if normalized.startswith(("90_p6_expert_dashboard/", "60_model/", "80_delivery/")):
            return "high" if kind in {"old_default_node", "legacy_preview", "client_asks_for_more"} else "medium"
        return "medium"
    if area in {"codex_global", "agents_global", "claude_global", "codex_vscode", "cursor_global", "vscode_user", "cursor_user"}:
        if "memory" in normalized or "handoff" in normalized or "prompt" in normalized or "settings" in normalized:
            return "high" if kind in {"old_default_node", "legacy_preview", "client_asks_for_more", "wrong_scope"} else "medium"
        if "session" in normalized or "rollout" in normalized or "history" in normalized:
            return "context"
        return "medium"
    return "low"


def is_protective_guardrail(kind: str, line: str) -> bool:
    if kind not in {"client_asks_for_more", "old_default_node", "legacy_preview", "wrong_scope"}:
        return False
    guard_words = ("不得", "不要", "不写", "不能", "不可", "禁止", "防止", "不把", "不再", "不能再")
    return any(word in line for word in guard_words)


def adjusted_severity(area: str, rel: str, kind: str, line: str) -> str:
    severity = severity_for(area, rel, kind)
    if is_protective_guardrail(kind, line):
        if severity == "high":
            return "medium"
        if severity == "medium":
            return "info"
    return severity


def scan_file(area: str, root: Path, path: Path) -> list[Finding]:
    text = read_text(path)
    if text is None:
        return []
    marker_hits = [name for name, regex in PROJECT_MARKERS.items() if regex.search(text)]
    collision_hits = [(name, regex) for name, regex in COLLISION_TERMS.items() if regex.search(text)]
    if not marker_hits and not collision_hits:
        return []
    if area != "project_workspace" and not marker_hits:
        return []

    findings: list[Finding] = []
    rel = rel_to(root, path)
    for line_no, line in enumerate(text.splitlines(), start=1):
        if len(findings) >= MAX_FINDINGS_PER_FILE:
            break
        for name in marker_hits:
            if PROJECT_MARKERS[name].search(line):
                findings.append(
                    Finding(
                        area=area,
                        root=str(root),
                        path=rel,
                        line=line_no,
                        kind="project_marker",
                        term=name,
                        severity="info",
                        text=line.strip()[:260],
                    )
                )
                break
        if len(findings) >= MAX_FINDINGS_PER_FILE:
            break
        for name, regex in collision_hits:
            if regex.search(line):
                findings.append(
                    Finding(
                        area=area,
                        root=str(root),
                        path=rel,
                        line=line_no,
                        kind=name,
                        term=name,
                        severity=adjusted_severity(area, rel, name, line),
                        text=line.strip()[:260],
                    )
                )
                break
    return findings


def iter_files(area: str, root: Path):
    count = 0
    for path in root.rglob("*"):
        if count >= MAX_FILES_PER_ROOT:
            break
        if not path.is_file():
            continue
        count += 1
        if should_skip(path):
            continue
        if area == "project_workspace":
            if not is_project_candidate(path):
                continue
        elif not is_global_candidate(area, root, path):
            continue
        yield path


def main() -> None:
    roots = existing_roots()
    findings: list[Finding] = []
    scanned_counts: Counter[str] = Counter()
    for area, root in roots:
        for path in iter_files(area, root):
            scanned_counts[area] += 1
            findings.extend(scan_file(area, root, path))

    severity_counts = Counter(f.severity for f in findings)
    area_counts = Counter(f.area for f in findings)
    kind_counts = Counter(f.kind for f in findings)
    high_current = [f for f in findings if f.severity == "high"]
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "needs_action" if high_current else "review",
        "roots": [{"area": area, "path": str(path)} for area, path in roots],
        "scanned_counts": dict(scanned_counts),
        "finding_count": len(findings),
        "severity_counts": dict(severity_counts),
        "area_counts": dict(area_counts),
        "kind_counts": dict(kind_counts),
        "high_current_count": len(high_current),
        "high_current_findings": [asdict(f) for f in high_current[:200]],
        "findings": [asdict(f) for f in findings],
        "interpretation": [
            "本审计不是按文件年代判断，而是判断是否会影响当前项目、网页、报告、门禁或下一轮 Agent 接续。",
            "project_marker 只是说明文件与本项目有关；high 表示可能把旧口径带回当前工作流，需要人工处理或改写。",
            "session/rollout/history 类命中通常保留为 context，不应直接删除，但交接文件和全局记忆若命中 high 需要纠偏。",
        ],
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Agent / 编辑器影响面审计 2026-06-09",
        "",
        f"- 状态：{report['status']}",
        f"- 扫描根：{len(roots)}",
        f"- 扫描文件：{sum(scanned_counts.values())}",
        f"- 命中：{len(findings)}",
        f"- high：{len(high_current)}",
        f"- severity：{dict(severity_counts)}",
        f"- area：{dict(area_counts)}",
        "",
        "## 高风险当前影响源",
    ]
    if high_current:
        for item in high_current[:80]:
            lines.append(f"- `{item.area}` `{item.path}:{item.line}` [{item.kind}] {item.text}")
    else:
        lines.append("- 未发现 high 当前影响源。")
    lines.extend(
        [
            "",
            "## 解释",
            "- 本报告用于区分“无害历史记录”和“会影响当前项目的新旧冲突面”。",
            "- 不建议删除 session/history/rollout；应优先改写项目交接文件、全局记忆补丁、测试夹具和客户可见产物。",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["status", "finding_count", "severity_counts", "area_counts", "high_current_count"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
