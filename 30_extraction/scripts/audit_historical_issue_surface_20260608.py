from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "40_quality_evidence" / "historical_issue_surface_audit_20260608.json"
OUT_MD = ROOT / "40_quality_evidence" / "historical_issue_surface_audit_20260608.md"
MAX_TEXT_BYTES = 2_000_000

SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "TestFiles/reports",
}

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


@dataclass(frozen=True)
class PatternRule:
    group: str
    name: str
    regex: str
    active_severity: str
    note: str


@dataclass
class Finding:
    path: str
    surface: str
    line: int
    group: str
    name: str
    severity: str
    text: str
    note: str


def j(*parts: str) -> str:
    return "".join(parts)


RULES = [
    PatternRule("personal_path", "foreign_local_path", r"G:\\|" + j("wxjw", "Works") + r"|works\\park" + "_commercial", "high", "协作文件不能携带他人本机路径。"),
    PatternRule("personal_path", "user_local_path", r"C:\\Users\\Yy199", "medium", "项目交接可记录本机事实，但客户材料和通用说明不应依赖绝对路径。"),
    PatternRule("old_node_default", "n001_default", r"\b" + j("N", "-001") + r"\b", "high", "旧固定节点曾是默认硬绑定历史问题；客户可见或当前 AI 缓存中出现需复核。"),
    PatternRule("old_node_default", "youth_lake_scope", r"青年湖", "medium", "青年湖曾与奥森资料混用；当前奥森链路中出现需复核上下文。"),
    PatternRule("internal_token", "legacy_preview_token", j("external", "_preview_only") + "|" + j("外部", "预览") + "|" + j("仅地图", "预览"), "high", "内部状态不得裸露给客户；代码映射表可降级为中风险。"),
    PatternRule("internal_token", "raw_debug_payload", r"\bdebug\b|\bpayload\b|\braw\b|traceback|ConnectError", "medium", "测试诊断允许，产品文案和客户报告不允许。"),
    PatternRule("internal_token", "draft_state", r"\bneeds_review\b|\bnot_final\b", "medium", "内部状态应映射成人话；客户材料不应出现。"),
    PatternRule("old_gate_language", "gate_jargon", r"\bGATE\b|门禁|API contract|smoke test", "medium", "门禁/测试术语只能留在工程证据，不应进入客户面。"),
    PatternRule("client_boundary", "ask_client_for_more", j("请", "补") + "|" + j("补", "齐") + "|" + j("补", "来源文件") + "|" + j("训练", "资料"), "high", "客户报告应基于已给材料判断，不把内部数据复核动作写给客户。"),
    PatternRule("ai_boundary", "ai_provider_leak", r"\bDeepSeek\b|\bLLM\b|OpenAI|Codex", "medium", "AI 供应商/内部链路不应进入客户可见面。"),
]

CUSTOMER_VISIBLE_ROOTS = (
    "90_p6_expert_dashboard/static",
)
CUSTOMER_VISIBLE_FILES = {
    "80_delivery/site_selection_gap_report_latest.json",
    "80_delivery/site_selection_gap_report_latest.md",
    "80_delivery/osen_business_decision_report_20260607.md",
    "80_delivery/osen_business_decision_report_20260607.docx",
    "80_delivery/osen_prediction_adjustment_report_20260607.md",
    "80_delivery/osen_prediction_adjustment_report_20260607.html",
}
ACTIVE_CODE_ROOTS = (
    "30_extraction/scripts",
    "50_external_gis/scripts",
    "60_model",
    "90_p6_expert_dashboard",
    "TestFiles",
)
DURABLE_DOC_ROOTS = (
    "00_control",
    "10_research",
    "40_quality_evidence",
)


def as_posix(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def is_under(rel: str, prefixes: Iterable[str]) -> bool:
    return any(rel == prefix or rel.startswith(prefix + "/") for prefix in prefixes)


def surface_for(rel: str) -> str:
    if rel.startswith("90_archive/"):
        return "archive"
    if rel.startswith("60_model/llm_runs/"):
        return "model_run_archive"
    if rel.startswith("80_delivery/ai_chat_reports/") or rel.startswith("80_delivery/scripts/"):
        return "delivery_internal"
    if rel.startswith("80_delivery/") and rel not in CUSTOMER_VISIBLE_FILES:
        return "delivery_internal"
    if rel in CUSTOMER_VISIBLE_FILES:
        return "customer_visible"
    if is_under(rel, CUSTOMER_VISIBLE_ROOTS):
        return "customer_visible"
    if is_under(rel, ACTIVE_CODE_ROOTS):
        return "active_code"
    if is_under(rel, DURABLE_DOC_ROOTS) or rel in {"progress.md", "findings.md", "handoff_next_chat.md", "next_chat_prompt.md", "CONTEXT.md", "README.md", "AGENTS.md"}:
        return "durable_context"
    return "other"


def should_skip(path: Path) -> bool:
    rel = as_posix(path)
    if "node_modules" in path.parts or "__pycache__" in path.parts:
        return True
    if rel == "30_extraction/scripts/audit_historical_issue_surface_20260608.py":
        return True
    if path.suffix.lower() in BINARY_SUFFIXES:
        return True
    try:
        if path.stat().st_size > MAX_TEXT_BYTES:
            return True
    except OSError:
        return True
    return any(rel == skip or rel.startswith(skip + "/") for skip in SKIP_DIRS)


def read_text(path: Path) -> str | None:
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
        except OSError:
            return None
    return None


def severity_for(rule: PatternRule, rel: str, surface: str) -> str:
    if surface in {"archive", "model_run_archive", "delivery_internal"}:
        return "archive"
    if surface == "durable_context":
        return "context"
    if surface == "customer_visible":
        return rule.active_severity
    if surface == "active_code":
        if rule.name in {"foreign_local_path", "n001_default", "legacy_preview_token", "ask_client_for_more"}:
            return rule.active_severity
        return "medium"
    return "low"


def audit_file(path: Path) -> list[Finding]:
    rel = as_posix(path)
    text = read_text(path)
    if text is None:
        return []
    surface = surface_for(rel)
    findings: list[Finding] = []
    compiled = [(rule, re.compile(rule.regex, re.IGNORECASE)) for rule in RULES]
    for line_no, line in enumerate(text.splitlines(), start=1):
        for rule, regex in compiled:
            if not regex.search(line):
                continue
            findings.append(
                Finding(
                    path=rel,
                    surface=surface,
                    line=line_no,
                    group=rule.group,
                    name=rule.name,
                    severity=severity_for(rule, rel, surface),
                    text=line.strip()[:300],
                    note=rule.note,
                )
            )
    return findings


def list_files() -> list[Path]:
    return [path for path in ROOT.rglob("*") if path.is_file() and not should_skip(path)]


def skipped_large_text_files() -> list[dict[str, int | str]]:
    rows: list[dict[str, int | str]] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() in BINARY_SUFFIXES:
            continue
        rel = as_posix(path)
        if any(rel == skip or rel.startswith(skip + "/") for skip in SKIP_DIRS):
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size > MAX_TEXT_BYTES:
            rows.append({"path": rel, "bytes": size})
    return sorted(rows, key=lambda item: int(item["bytes"]), reverse=True)


def main() -> None:
    files = list_files()
    skipped_large = skipped_large_text_files()
    findings: list[Finding] = []
    for path in files:
        findings.extend(audit_file(path))

    severity_counts = Counter(f.severity for f in findings)
    surface_counts = Counter(f.surface for f in findings)
    group_counts = Counter(f.group for f in findings)
    active_high = [f for f in findings if f.severity == "high"]
    active_medium = [f for f in findings if f.severity == "medium"]

    by_file: dict[str, Counter[str]] = defaultdict(Counter)
    for finding in findings:
        by_file[finding.path][finding.severity] += 1
    top_files = [
        {"path": path, "counts": dict(counts)}
        for path, counts in sorted(by_file.items(), key=lambda item: (-sum(item[1].values()), item[0]))[:40]
    ]

    payload = {
        "status": "needs_action" if active_high else "review",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "rule": "全仓文本遍历；归档和 durable 历史记录不等于当前客户可见问题，但会标注风险。",
        "scanned_file_count": len(files),
        "skipped_large_text_count": len(skipped_large),
        "skipped_large_text_files": skipped_large[:100],
        "finding_count": len(findings),
        "severity_counts": dict(severity_counts),
        "surface_counts": dict(surface_counts),
        "group_counts": dict(group_counts),
        "top_files": top_files,
        "active_high_findings": [asdict(f) for f in active_high[:200]],
        "active_medium_sample": [asdict(f) for f in active_medium[:100]],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 历史问题全仓暴露面审计",
        "",
        f"- 生成时间：{payload['generated_at']}",
        f"- 扫描文件数：{payload['scanned_file_count']}",
        f"- 跳过超大文本数：{payload['skipped_large_text_count']}",
        f"- 命中总数：{payload['finding_count']}",
        f"- 严重度：{json.dumps(payload['severity_counts'], ensure_ascii=False)}",
        f"- 暴露面：{json.dumps(payload['surface_counts'], ensure_ascii=False)}",
        "",
        "## 当前高风险命中",
        "",
    ]
    if not active_high:
        lines.append("- 无")
    else:
        for finding in active_high[:80]:
            lines.append(f"- `{finding.path}:{finding.line}` [{finding.group}/{finding.name}] {finding.text}")
    lines.extend(["", "## 高命中文件", ""])
    for item in top_files[:20]:
        lines.append(f"- `{item['path']}` {json.dumps(item['counts'], ensure_ascii=False)}")
    lines.extend(
        [
            "",
            "## 解释规则",
            "",
            "- `archive`：归档历史，不能直接恢复成当前事实。",
            "- `context`：交接/证据中的历史记录，允许存在但需要标清当前边界。",
            "- `medium/high`：当前代码、客户可见文件或运行入口中需要复核或修复。",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ["status", "scanned_file_count", "finding_count", "severity_counts", "surface_counts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
