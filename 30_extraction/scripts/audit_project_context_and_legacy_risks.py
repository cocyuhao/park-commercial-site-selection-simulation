from __future__ import annotations

import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "40_quality_evidence" / "project_context_legacy_risk_audit_20260605.json"
OUT_MD = ROOT / "40_quality_evidence" / "project_context_legacy_risk_audit_20260605.md"

TEXT_EXTENSIONS = {
    ".md",
    ".py",
    ".js",
    ".html",
    ".css",
    ".json",
    ".jsonl",
    ".csv",
    ".txt",
    ".yml",
    ".yaml",
    ".ps1",
    ".sql",
}

IGNORE_PARTS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
}

BOSS_RAW_EXPECTED = {
    "1e00cea7fa6c97950ae18ae4b762644.jpg",
    "2510.01272v1.pdf",
    "2603.03303.pdf",
    "591775 (已转换).pdf",
    "人工智能模拟实验论文.docx",
    "已转换 - main-1.docx",
}

AUTHORITATIVE_CONTEXT_FILES = [
    "AGENTS.md",
    "00_control/codex_mainline_guardrails.md",
    "00_control/decisions.md",
    "progress.md",
    "findings.md",
    "handoff_next_chat.md",
    "next_chat_prompt.md",
    "10_research/method_tool_plugin_audit_20260604.md",
    "10_research/global_ai_simulation_design_rebaseline_20260604.md",
    "10_research/advanced_ai_learning_absorption_register_20260604.md",
    "10_research/boss_method_materials_20260604/full_system_rebaseline_20260604.md",
    "10_research/boss_method_materials_20260604/unified_simulation_method_matrix_20260604.md",
    "10_research/boss_method_materials_20260604/simulation_accuracy_plan_20260604.md",
    "10_research/boss_method_materials_20260604/boss_model_inventory_20260604.md",
    "10_research/boss_method_materials_20260604/deepseek_constrained_simulation_design_20260604.md",
]

RISK_PATTERNS = {
    "complete_simulation_claim": ["完整仿真", "仿真已完成", "full simulation"],
    "final_claim": ["最终推荐", "最终排序", "最终排名", "final recommendation", "final ranking"],
    "roi_revenue_claim": ["ROI", "收益预测", "revenue forecast"],
    "legacy_dry_run": ["dry-run", "dry_run", "干跑"],
    "raw_internal_ui": ["external_preview_only", "needs_review", "not_final", "payload", "debug", "traceback", "ConnectError"],
    "score_overclaim": ["裸分数", "综合分", "discussion_score_draft"],
    "deepseek_boundary": ["DeepSeek", "checked", "draft", "needs_review"],
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def should_ignore(path: Path) -> bool:
    return any(part in IGNORE_PARTS for part in path.parts)


def iter_project_files() -> list[Path]:
    return sorted(path for path in ROOT.rglob("*") if path.is_file() and not should_ignore(path))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def git_status() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001 - exact report is useful here
        return [f"git status unavailable: {type(exc).__name__}: {exc}"]
    return [line for line in result.stdout.splitlines() if line.strip()]


def scan_risks(files: list[Path]) -> dict[str, Any]:
    counts: dict[str, int] = {key: 0 for key in RISK_PATTERNS}
    samples: dict[str, list[dict[str, Any]]] = {key: [] for key in RISK_PATTERNS}
    user_visible_roots = {
        "90_p6_expert_dashboard/static/index.html",
        "90_p6_expert_dashboard/static/app.js",
        "90_p6_expert_dashboard/static/styles.css",
    }
    visible_samples: list[dict[str, Any]] = []
    for path in files:
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            lines = read_text(path).splitlines()
        except OSError:
            continue
        path_rel = rel(path)
        for line_no, line in enumerate(lines, start=1):
            for risk, patterns in RISK_PATTERNS.items():
                if any(pattern in line for pattern in patterns):
                    counts[risk] += 1
                    if len(samples[risk]) < 18:
                        samples[risk].append(
                            {
                                "path": path_rel,
                                "line": line_no,
                                "text": line.strip()[:220],
                            }
                        )
                    if path_rel in user_visible_roots and len(visible_samples) < 30:
                        visible_samples.append(
                            {
                                "risk": risk,
                                "path": path_rel,
                                "line": line_no,
                                "text": line.strip()[:220],
                            }
                        )
    return {
        "counts": counts,
        "samples": samples,
        "user_visible_samples": visible_samples,
    }


def classify_files(files: list[Path]) -> dict[str, Any]:
    by_top = Counter(path.relative_to(ROOT).parts[0] for path in files)
    by_ext = Counter(path.suffix.lower() or "(none)" for path in files)
    text_count = sum(1 for path in files if path.suffix.lower() in TEXT_EXTENSIONS)
    total_bytes = sum(path.stat().st_size for path in files)
    large_files = sorted(files, key=lambda path: path.stat().st_size, reverse=True)[:25]
    return {
        "file_count": len(files),
        "text_like_file_count": text_count,
        "total_bytes": total_bytes,
        "by_top_directory": dict(by_top.most_common()),
        "by_extension": dict(by_ext.most_common(25)),
        "large_files": [{"path": rel(path), "bytes": path.stat().st_size} for path in large_files],
    }


def boss_materials_status() -> dict[str, Any]:
    raw_dir = ROOT / "老板资料"
    extracted_dir = ROOT / "10_research" / "boss_method_materials_20260604"
    raw_files = {path.name for path in raw_dir.iterdir() if path.is_file()} if raw_dir.exists() else set()
    extracted_files = sorted(path for path in extracted_dir.rglob("*") if path.is_file()) if extracted_dir.exists() else []
    key_docs = [
        "full_system_rebaseline_20260604.md",
        "unified_simulation_method_matrix_20260604.md",
        "simulation_accuracy_plan_20260604.md",
        "boss_model_inventory_20260604.md",
        "method_absorption_landing_register_20260604.md",
        "deepseek_constrained_simulation_design_20260604.md",
        "legacy_file_trust_audit_20260604.md",
    ]
    return {
        "raw_dir_exists": raw_dir.exists(),
        "raw_expected_count": len(BOSS_RAW_EXPECTED),
        "raw_found_count": len(raw_files & BOSS_RAW_EXPECTED),
        "raw_missing": sorted(BOSS_RAW_EXPECTED - raw_files),
        "raw_extra": sorted(raw_files - BOSS_RAW_EXPECTED),
        "extracted_file_count": len(extracted_files),
        "key_docs": [
            {
                "path": f"10_research/boss_method_materials_20260604/{name}",
                "exists": (extracted_dir / name).exists(),
                "bytes": (extracted_dir / name).stat().st_size if (extracted_dir / name).exists() else 0,
            }
            for name in key_docs
        ],
    }


def authoritative_status() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in AUTHORITATIVE_CONTEXT_FILES:
        path = ROOT / item
        rows.append({"path": item, "exists": path.exists(), "bytes": path.stat().st_size if path.exists() else 0})
    return rows


def pending_work_status(status_lines: list[str]) -> dict[str, Any]:
    pending = defaultdict(list)
    for line in status_lines:
        marker = line[:2].strip() or "??"
        path = line[3:].strip() if len(line) > 3 else line.strip()
        pending[marker].append(path)
    untracked_src = [path for path in pending.get("??", []) if path.startswith("60_model/src/")]
    return {
        "status_line_count": len(status_lines),
        "by_marker": {key: len(value) for key, value in sorted(pending.items())},
        "untracked_src_files": untracked_src,
        "telemetry_pending": "60_model/src/telemetry.py" in untracked_src,
    }


def build_payload() -> dict[str, Any]:
    files = iter_project_files()
    status_lines = git_status()
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "purpose": "Full-project context and legacy risk audit before continuing simulation implementation.",
        "file_inventory": classify_files(files),
        "boss_materials": boss_materials_status(),
        "authoritative_context": authoritative_status(),
        "legacy_risk_scan": scan_risks(files),
        "pending_work": pending_work_status(status_lines),
        "interpretation": [
            "This audit reads text-like project files for risk patterns and treats PDFs/DOCX/images by manifest unless they already have extracted knowledge artifacts.",
            "Risk hits are not automatically bugs; many are legitimate guardrails or historical notes. User-visible hits and old completion claims need deeper review first.",
            "OpenTelemetry telemetry.py is currently an unintegrated draft from the interrupted implementation path and must either be integrated or explicitly documented before final validation.",
        ],
    }


def write_markdown(payload: dict[str, Any]) -> None:
    inv = payload["file_inventory"]
    boss = payload["boss_materials"]
    risks = payload["legacy_risk_scan"]
    pending = payload["pending_work"]
    lines = [
        "# 全项目上下文与历史遗留风险审计（2026-06-05）",
        "",
        f"- 生成时间：{payload['generated_at']}",
        f"- 项目文件数：{inv['file_count']}，可文本扫描文件：{inv['text_like_file_count']}，总大小：{inv['total_bytes']} bytes",
        f"- 老板原始资料：{boss['raw_found_count']} / {boss['raw_expected_count']} 已找到",
        f"- Git 待处理行数：{pending['status_line_count']}，未接入 telemetry 草稿：{pending['telemetry_pending']}",
        "",
        "## 1. 结论",
        "",
        "- 项目不是缺资料，而是历史产物多、旧口径多、方向变化大；继续实现前必须用脚本分层，而不是靠聊天记忆。",
        "- 老板六份资料原件已齐，关键吸收文档存在；后续应复核这些文档是否真正进入 schema、UI、DeepSeek 契约和门禁。",
        "- 旧风险词命中很多，其中不少是正确的警戒语；真正危险的是用户可见界面或结果文件继续把 dry-run、最终推荐、ROI、裸分数写成事实。",
        "- 刚刚创建的 `60_model/src/telemetry.py` 还没有接入主链，当前只能算草稿，不能写成已落地。",
        "",
        "## 2. 文件分层",
        "",
    ]
    for key, value in inv["by_top_directory"].items():
        lines.append(f"- `{key}`：{value} 个文件")
    lines.extend(["", "## 3. 老板资料覆盖", ""])
    if boss["raw_missing"]:
        lines.append(f"- 缺失原始资料：{', '.join(boss['raw_missing'])}")
    else:
        lines.append("- 六份老板原始资料均已找到。")
    for item in boss["key_docs"]:
        status = "存在" if item["exists"] else "缺失"
        lines.append(f"- `{item['path']}`：{status}，{item['bytes']} bytes")
    lines.extend(["", "## 4. 旧风险词命中", ""])
    for risk, count in risks["counts"].items():
        lines.append(f"- `{risk}`：{count} 处")
    lines.extend(["", "## 5. 用户可见风险样例", ""])
    visible = risks["user_visible_samples"]
    if not visible:
        lines.append("- 当前扫描未在前端三大文件中找到旧风险样例。")
    else:
        for item in visible[:20]:
            lines.append(f"- `{item['path']}:{item['line']}` [{item['risk']}] {item['text']}")
    lines.extend(["", "## 6. 风险样例摘录", ""])
    for risk, samples in risks["samples"].items():
        lines.append(f"### {risk}")
        if not samples:
            lines.append("- 无")
            continue
        for item in samples[:8]:
            lines.append(f"- `{item['path']}:{item['line']}` {item['text']}")
    lines.extend(["", "## 7. 下一步建议", ""])
    lines.extend([
        "1. 先把本审计加入门禁和交接，避免后续新对话忘记全项目风险。",
        "2. 对用户可见风险样例逐项确认：前端可以保留人话状态，但不能出现内部词或最终化口径。",
        "3. 对老板资料吸收文档做一次“落点覆盖”检查：schema、adapter、UI、DeepSeek 契约、验证脚本是否都有对应项。",
        "4. 决定 `60_model/src/telemetry.py`：要么接入并验证，要么标记为未接入草稿，不能让它漂在主线外。",
    ])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_payload()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(payload)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    print(f"files={payload['file_inventory']['file_count']} text={payload['file_inventory']['text_like_file_count']} risks={sum(payload['legacy_risk_scan']['counts'].values())}")


if __name__ == "__main__":
    main()
