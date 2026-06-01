from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_CSV = ROOT / "40_quality_evidence" / "handoff_encoding_health_review.csv"
OUT_MD = ROOT / "40_quality_evidence" / "handoff_encoding_health_review.md"

FIELDS = ["check_id", "status", "severity", "finding", "evidence"]

DURABLE_FILES = [
    "AGENTS.md",
    "progress.md",
    "findings.md",
    "handoff_next_chat.md",
    "next_chat_prompt.md",
    "task_plan.md",
    "00_control/decisions.md",
    "00_control/plugin_routing.md",
]

FORBIDDEN_TEXT = [
    "?" * 3,
    "?" * 4,
    "?" * 5,
    "锛",
    "乣",
    "銆",
    "浠跨",
    "濂ユ",
    "鍥惧",
]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def add(rows: list[dict[str, str]], status: str, severity: str, finding: str, evidence: str) -> None:
    rows.append(
        {
            "check_id": f"HANDOFF-ENC-{len(rows) + 1:03d}",
            "status": status,
            "severity": severity,
            "finding": finding,
            "evidence": evidence,
        }
    )


def ok(condition: bool) -> str:
    return "pass" if condition else "fail"


def main() -> None:
    rows: list[dict[str, str]] = []

    for item in DURABLE_FILES:
        path = ROOT / item
        exists = path.exists()
        add(rows, ok(exists), "error", f"{item} exists", item)
        if not exists:
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
            add(rows, "pass", "error", f"{item} is readable as utf-8-sig", item)
        except UnicodeDecodeError as exc:
            add(rows, "fail", "error", f"{item} utf-8 read failed: {exc}", item)
            continue

        hits = [pattern for pattern in FORBIDDEN_TEXT if pattern in text]
        add(rows, ok(not hits), "error", f"{item} forbidden mojibake tokens={hits}", item)

    agents = read("AGENTS.md")
    add(
        rows,
        ok("P2 方法原型 | 已闭环" in agents and "P2 真实公园数据 | 暂不启动" not in agents),
        "error",
        "AGENTS.md current phase says P2 method prototype is closed, not blocked",
        "AGENTS.md",
    )
    add(
        rows,
        ok("完整仿真建模" in agents and "DeepSeek-first" in agents),
        "error",
        "AGENTS.md preserves P2 boundary and DeepSeek-first routing",
        "AGENTS.md",
    )

    handoff = read("handoff_next_chat.md")
    next_prompt = read("next_chat_prompt.md")
    findings = read("findings.md")
    progress = read("progress.md")
    decisions = read("00_control/decisions.md")

    for item, text in [
        ("handoff_next_chat.md", handoff),
        ("next_chat_prompt.md", next_prompt),
        ("findings.md", findings),
        ("progress.md", progress),
    ]:
        add(rows, ok("LLM-018" in text), "error", f"{item} mentions LLM-018", item)
        add(rows, ok("LLM-019" in text), "error", f"{item} mentions LLM-019", item)
        add(rows, ok("checks=589 failures=0" in text), "error", f"{item} records latest gate", item)
        add(rows, ok("pending_conversion" in text), "error", f"{item} preserves DWG pending_conversion boundary", item)

    add(
        rows,
        ok("DEC-039" in decisions and "DEC-040" in decisions and "DEC-041" in decisions and "DEC-042" in decisions and "DEC-043" in decisions and "checks=589 failures=0" in decisions),
        "error",
        "decisions.md records latest P2 and handoff decisions plus latest gate",
        "00_control/decisions.md",
    )

    statuses = {row["status"] for row in rows}
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    failures = [row for row in rows if row["status"] != "pass"]
    OUT_MD.write_text(
        "\n".join(
            [
                "# 交接与编码健康复核报告",
                "",
                f"- 检查项：{len(rows)}",
                f"- 失败项：{len(failures)}",
                f"- 状态集合：{', '.join(sorted(statuses))}",
                "",
                "## 结论",
                "",
                "- durable 交接文件必须保持 UTF-8 可读，不保留 mojibake 占位符。",
                "- `AGENTS.md` 必须明确当前为 P2 准备中，而不是 P2 暂不启动。",
                "- 最新 DeepSeek LLM-021 图纸代理审计、LLM-020 覆盖细审和 `checks=589 failures=0` 必须进入交接链路。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"wrote handoff encoding review rows={len(rows)} to {OUT_CSV}")
    print(f"wrote review report to {OUT_MD}")
    print(f"failures={len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
