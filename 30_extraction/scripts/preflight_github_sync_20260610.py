from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "40_quality_evidence" / "github_sync_preflight_20260610.json"

SECRET_PATTERNS = [
    ("deepseek_key_literal", re.compile(r"sk-[A-Za-z0-9_\-]{20,}")),
    ("amap_long_literal", re.compile(r"(?i)(amap[^\\n]{0,40}(?:key|token)[^\\n]{0,20}[=:：]\\s*[A-Za-z0-9]{16,})")),
    ("generic_secret_assignment", re.compile(r"(?i)(api[_-]?key|secret|token)\\s*[=:]\\s*['\\\"]?[A-Za-z0-9_\\-]{24,}")),
]

SKIP_PARTS = {".git", "__pycache__", "node_modules", ".venv"}
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".pdf", ".docx", ".dwg", ".dxf", ".sqlite3", ".pptx", ".xlsx", ".zip", ".dll", ".pyc"}
ALLOWED_SECRET_FILES = {".env"}


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True, check=False)


def git_lines(args: list[str]) -> list[str]:
    proc = run(["git", *args])
    if proc.returncode != 0:
        return []
    return [line for line in proc.stdout.splitlines() if line.strip()]


def check_lfs_patterns() -> dict[str, object]:
    gitattributes = ROOT / ".gitattributes"
    text = gitattributes.read_text(encoding="utf-8", errors="ignore") if gitattributes.exists() else ""
    required = ["*.dwg", "*.dxf", "10_research/recent_knowledge_base_20260609/*.jsonl", "*.pptx", "*.docx", "*.pdf"]
    return {
        "exists": gitattributes.exists(),
        "required_present": [item for item in required if item in text],
        "missing": [item for item in required if item not in text],
    }


def large_files() -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for path in ROOT.rglob("*"):
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if not path.is_file():
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size >= 50 * 1024 * 1024:
            rel = path.relative_to(ROOT).as_posix()
            attrs = run(["git", "check-attr", "filter", "--", rel]).stdout.strip()
            items.append({"path": rel, "bytes": size, "git_attr_filter": attrs})
    return sorted(items, key=lambda row: int(row["bytes"]), reverse=True)


def secret_hits() -> list[dict[str, object]]:
    hits: list[dict[str, object]] = []
    for path in ROOT.rglob("*"):
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if not path.is_file() or path.suffix.lower() in SKIP_SUFFIXES:
            continue
        rel = path.relative_to(ROOT).as_posix()
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for name, pattern in SECRET_PATTERNS:
            matches = list(pattern.finditer(text))
            if not matches:
                continue
            if rel in ALLOWED_SECRET_FILES:
                hits.append({"path": rel, "kind": name, "allowed_local_secret": True, "count": len(matches)})
            else:
                hits.append({"path": rel, "kind": name, "allowed_local_secret": False, "count": len(matches)})
    return hits


def main() -> None:
    status_lines = git_lines(["status", "--short"])
    ignored_env = run(["git", "check-ignore", "-q", ".env"]).returncode == 0
    lfs = check_lfs_patterns()
    big = large_files()
    secrets = secret_hits()
    blocking_secrets = [row for row in secrets if not row["allowed_local_secret"]]
    big_without_lfs = [row for row in big if "filter: lfs" not in str(row["git_attr_filter"])]
    verify = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "pass" if ignored_env and not blocking_secrets and not lfs["missing"] and not big_without_lfs else "needs_action",
        "git_status_count": len(status_lines),
        "env_ignored": ignored_env,
        "lfs": lfs,
        "large_file_count": len(big),
        "large_files": big,
        "large_without_lfs": big_without_lfs,
        "secret_hit_count": len(secrets),
        "blocking_secret_count": len(blocking_secrets),
        "blocking_secrets": blocking_secrets[:100],
        "rule": "允许上传除 .env/API Key 外的项目文件；超过 GitHub 普通限制的大文件必须走 Git LFS。",
    }
    OUT.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify, ensure_ascii=False, indent=2))
    raise SystemExit(0 if verify["status"] == "pass" else 2)


if __name__ == "__main__":
    main()
