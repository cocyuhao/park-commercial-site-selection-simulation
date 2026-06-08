from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LLM_RUNS_DIR = ROOT / "60_model" / "llm_runs"
ENVELOPE_DIR = LLM_RUNS_DIR / "contract_envelopes"
QUALITY_DIR = ROOT / "40_quality_evidence"
REPORT_JSON = QUALITY_DIR / "deepseek_legacy_envelope_adapter_20260604.json"
REPORT_CSV = QUALITY_DIR / "deepseek_legacy_envelope_adapter_20260604.csv"
REPORT_MD = QUALITY_DIR / "deepseek_legacy_envelope_adapter_20260604.md"


def safe_id(raw: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_-]+", "-", raw).strip("-")
    return value[:120] or "legacy-output"


def detect_kind(path: Path) -> str:
    name = path.name
    if name.endswith("_raw.jsonl"):
        return "raw_jsonl"
    if name.endswith("_progress.json"):
        return "progress_json"
    if name.endswith("_latest.json"):
        return "latest_json"
    return "json"


def read_first_json_line(path: Path) -> dict[str, Any]:
    try:
        if path.suffix.lower() == ".jsonl":
            with path.open("r", encoding="utf-8-sig") as f:
                for line in f:
                    if line.strip():
                        return json.loads(line)
            return {}
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # noqa: BLE001 - exact failure is useful in audit
        return {"_parse_error": str(exc)}


def count_lines(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8-sig") as f:
            return sum(1 for _ in f)
    except UnicodeError:
        with path.open("rb") as f:
            return sum(1 for _ in f)


def infer_original_task_id(path: Path, first: dict[str, Any]) -> str:
    task_id = first.get("task_id")
    if isinstance(task_id, str) and task_id.strip():
        return task_id.strip()
    stem = path.stem
    return f"legacy:{stem}"


def build_envelope(path: Path) -> tuple[dict[str, Any], dict[str, str]]:
    rel = path.relative_to(ROOT).as_posix()
    first = read_first_json_line(path)
    parse_error = first.get("_parse_error") if isinstance(first, dict) else None
    kind = detect_kind(path)
    original_task_id = infer_original_task_id(path, first if isinstance(first, dict) else {})
    line_count = count_lines(path)
    byte_count = path.stat().st_size
    envelope_name = f"legacy_{safe_id(path.stem)}.json"
    envelope_path = ENVELOPE_DIR / envelope_name

    envelope: dict[str, Any] = {
        "task_id": f"LEGACY-{safe_id(path.stem)}",
        "task_type": "source_summary",
        "output_status": "needs_review",
        "source_refs": [
            {
                "source_file": rel,
                "page_or_slide": "file",
                "quote_or_table_ref": "legacy DeepSeek output metadata only; original content not semantically revalidated",
            }
        ],
        "assumptions": [
            "This envelope adapts file-level metadata only.",
            "Original DeepSeek output predates the 2026-06-04 boss-method rebaseline.",
            "The envelope does not certify semantic correctness, evidence status, ranking, ROI, or simulation completion.",
        ],
        "uncertainties": [
            "Original content may contain old-stage assumptions, node scores, or P4 feedback draft language.",
            "Task-specific fields must be re-extracted against the current schema before use.",
        ],
        "needs_human_review": True,
        "items": [
            {
                "legacy_file": rel,
                "legacy_kind": kind,
                "original_task_id": original_task_id,
                "line_count": line_count,
                "byte_count": byte_count,
                "parse_error": parse_error or "",
                "adaptation_status": "metadata_wrapped_only",
                "allowed_use": "history_tracking_and_reaudit",
                "prohibited_use": [
                    "checked_evidence",
                    "final_ranking",
                    "roi_forecast",
                    "simulation_complete",
                    "operation_decision",
                ],
                "next_action": "Run a task-specific adapter or re-extraction script before using any item in persona, behavior, node, report, or simulation outputs.",
            }
        ],
    }

    report_row = {
        "legacy_file": rel,
        "envelope_file": envelope_path.relative_to(ROOT).as_posix(),
        "legacy_kind": kind,
        "original_task_id": original_task_id,
        "line_count": str(line_count),
        "byte_count": str(byte_count),
        "parse_error": str(parse_error or ""),
        "adaptation_status": "metadata_wrapped_only",
    }
    return envelope, report_row


def write_reports(rows: list[dict[str, str]]) -> None:
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(
        json.dumps(
            {
                "adapter": "adapt_deepseek_legacy_outputs.py",
                "status": "metadata_wrapped_only",
                "legacy_file_count": len(rows),
                "important_boundary": "Passing contract validation for generated envelopes only proves old files are registered for audit; it does not validate old DeepSeek content.",
                "rows": rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    fields = [
        "legacy_file",
        "envelope_file",
        "legacy_kind",
        "original_task_id",
        "line_count",
        "byte_count",
        "parse_error",
        "adaptation_status",
    ]
    with REPORT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    by_kind: dict[str, int] = {}
    for row in rows:
        by_kind[row["legacy_kind"]] = by_kind.get(row["legacy_kind"], 0) + 1

    lines = [
        "# DeepSeek 旧输出 envelope 适配报告（2026-06-04）",
        "",
        "本报告由 `60_model/scripts/adapt_deepseek_legacy_outputs.py` 生成。",
        "",
        "## 口径",
        "",
        "生成的 envelope 只包装旧文件元数据，状态统一为 `needs_review`，用途是把旧 DeepSeek 输出纳入新契约审计。它不证明旧内容语义正确，不证明旧 P2/P3/P4 草稿可用，也不允许升级为 checked 证据、最终排名、ROI 或完整仿真。",
        "",
        "## 汇总",
        "",
        f"- 旧文件数：{len(rows)}",
    ]
    for kind, count in sorted(by_kind.items()):
        lines.append(f"- {kind}: {count}")
    lines.extend(["", "## 下一步", "", "- 对 `source_summary` envelope 做契约验证。", "- 需要使用旧内容时，再写任务专用 adapter：persona_state、behavior_program、node_explanation 或 report_draft。", "- 专用 adapter 通过前，旧输出只能作为历史和复核线索。", ""])
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ENVELOPE_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    for path in sorted(LLM_RUNS_DIR.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".json", ".jsonl"}:
            continue
        envelope, row = build_envelope(path)
        envelope_path = ROOT / row["envelope_file"]
        envelope_path.write_text(json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8")
        rows.append(row)
    write_reports(rows)
    print(f"wrote {len(rows)} legacy envelopes to {ENVELOPE_DIR}")
    print(f"wrote adapter report to {REPORT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
