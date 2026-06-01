from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "60_model" / "src"))

from llm_router import route_for, run_deepseek_task  # noqa: E402


OUT_DIR = ROOT / "60_model" / "llm_runs"
RAW_JSONL = OUT_DIR / "deepseek_project_context_sync_raw.jsonl"
PROGRESS_JSON = OUT_DIR / "deepseek_project_context_sync_progress.json"
LATEST_JSON = OUT_DIR / "deepseek_project_context_sync_latest.json"
TASK_QUEUE_CSV = ROOT / "70_outputs" / "processed_tables" / "deepseek_first_task_queue.csv"
REPORT = ROOT / "40_quality_evidence" / "deepseek_project_context_sync_report.md"

TEXT_CONTEXT_FILES = [
    "progress.md",
    "handoff_next_chat.md",
    "task_plan.md",
    "findings.md",
    "00_control/model_orchestration.md",
    "00_control/plugin_routing.md",
    "00_control/decisions.md",
    "40_quality_evidence/verification/implementation_verification_20260524.md",
]

CSV_CONTEXT_FILES = [
    "40_quality_evidence/evidence_ledger.csv",
    "70_outputs/processed_tables/poi_supply_p0_followup_worklist.csv",
    "70_outputs/processed_tables/poi_supply_p0_entrance_route_review.csv",
    "50_external_gis/amap_routes/amap_p0_entrance_node_semantic_review_queue.csv",
    "70_outputs/processed_tables/p0_manual_verification_package_deepseek.csv",
    "40_quality_evidence/deepseek_p0_verification_package_review.csv",
]

TASK_FIELDS = [
    "queue_id",
    "priority",
    "task_name",
    "delegate_to",
    "codex_role",
    "input_paths",
    "output_paths",
    "gate_type",
    "output_status",
    "reason",
]


def clamp(text: Any, limit: int = 5000) -> str:
    value = str(text or "").strip()
    return value[:limit]


def read_text_context(path: str, max_chars: int) -> dict[str, Any]:
    full = ROOT / path
    if not full.exists():
        return {"path": path, "exists": False}
    text = full.read_text(encoding="utf-8-sig", errors="replace")
    if len(text) <= max_chars:
        excerpt = text
    else:
        half = max_chars // 2
        excerpt = text[:half] + "\n\n...[middle omitted]...\n\n" + text[-half:]
    return {
        "path": path,
        "exists": True,
        "bytes": full.stat().st_size,
        "excerpt": excerpt,
    }


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def summarize_csv(path: str, sample_rows: int = 3) -> dict[str, Any]:
    full = ROOT / path
    if not full.exists():
        return {"path": path, "exists": False}
    rows = read_csv_rows(full)
    columns = list(rows[0].keys()) if rows else []
    counters: dict[str, dict[str, int]] = {}
    for field in [
        "output_status",
        "validation_status",
        "evidence_type",
        "p2_gate_draft",
        "final_use_gate",
        "local_rule_priority",
        "can_enter_p2_supply",
        "can_enter_p2_supply_after_entrance_route",
        "status",
    ]:
        if field in columns:
            counters[field] = dict(Counter(row.get(field, "") for row in rows))
    return {
        "path": path,
        "exists": True,
        "rows": len(rows),
        "columns": columns,
        "counters": counters,
        "sample": rows[:sample_rows],
    }


def extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped, flags=re.IGNORECASE).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("DeepSeek response does not contain a JSON object")
    payload = json.loads(stripped[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError("DeepSeek response JSON is not an object")
    return payload


def build_context(max_text_chars: int, include_env_path: bool) -> dict[str, Any]:
    context = {
        "project": "公园商业选址仿真与经营决策系统",
        "current_phase": "P1 样例资料拆解，尚未进入 P2",
        "deepseek_first_policy": (
            "默认把简单、繁琐、批量、可复核以及中等难度但可拆解的任务交给 DeepSeek；"
            "Codex 负责计划、调度、本地执行、关键补丁和最终门禁。"
        ),
        "local_env_access": {
            "env_path": ".env" if include_env_path else "(not provided)",
            "note": "本地 Python 脚本负责读取 .env 或环境变量并封装 API 调用；模型输出不得要求人工粘贴 Key。",
        },
        "text_context": [read_text_context(path, max_text_chars) for path in TEXT_CONTEXT_FILES],
        "csv_context": [summarize_csv(path) for path in CSV_CONTEXT_FILES],
    }
    return context


def make_messages(context: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "你是本项目的 DeepSeek-first 执行规划助手。"
                "你可以承担大部分理解、拆解、草稿、批量整理、中等难度方案和代码草稿任务。"
                "Codex 只负责指挥、计划、本地执行、少量关键补丁和最终门禁。"
                "你的输出必须是 needs_review，不得宣称任何 P2 门禁已通过。"
                "只输出 JSON 对象，不输出 Markdown。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请基于以下完整项目上下文，生成 DeepSeek-first 后续执行队列和门禁分工。\n"
                "JSON 对象字段：output_status, phase_assessment, delegation_policy, "
                "task_queue, gate_delegation, codex_minimal_role, immediate_next_step。\n"
                "task_queue 是数组，每项字段：priority, task_name, delegate_to, codex_role, "
                "input_paths, output_paths, gate_type, output_status, reason。\n"
                "delegate_to 优先填 deepseek，只有必须本地执行的填 local_python，必须最终裁决才填 codex。\n"
                "gate_delegation 要说明哪些门禁可由 DeepSeek 先审，哪些必须用本地脚本 exit code 判定。\n"
                "所有 task_queue.output_status 必须是 draft 或 needs_review；整体 output_status 必须是 needs_review。\n"
                "上下文 JSON：\n"
                + json.dumps(context, ensure_ascii=False)
            ),
        },
    ]


def write_task_queue(tasks: list[dict[str, Any]]) -> None:
    TASK_QUEUE_CSV.parent.mkdir(parents=True, exist_ok=True)
    with TASK_QUEUE_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TASK_FIELDS)
        writer.writeheader()
        for index, task in enumerate(tasks, start=1):
            writer.writerow(
                {
                    "queue_id": f"DS-FIRST-{index:03d}",
                    "priority": clamp(task.get("priority", ""), 40),
                    "task_name": clamp(task.get("task_name", ""), 120),
                    "delegate_to": clamp(task.get("delegate_to", ""), 40),
                    "codex_role": clamp(task.get("codex_role", ""), 160),
                    "input_paths": clamp(";".join(task.get("input_paths", [])) if isinstance(task.get("input_paths"), list) else task.get("input_paths", ""), 500),
                    "output_paths": clamp(";".join(task.get("output_paths", [])) if isinstance(task.get("output_paths"), list) else task.get("output_paths", ""), 500),
                    "gate_type": clamp(task.get("gate_type", ""), 80),
                    "output_status": "needs_review" if task.get("output_status") not in {"draft", "needs_review"} else task.get("output_status"),
                    "reason": clamp(task.get("reason", ""), 500),
                }
            )


def run(max_text_chars: int, include_env_path: bool) -> None:
    task_id = "LLM-013"
    route = route_for(task_id)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    context = build_context(max_text_chars, include_env_path)
    content = run_deepseek_task(task_id, make_messages(context), temperature=0.0)
    payload = extract_json_object(content)
    payload["output_status"] = "needs_review"
    payload["run_id"] = run_id

    raw_record = {
        "run_id": run_id,
        "task_id": task_id,
        "task_name": route.task_name,
        "executor": route.default_executor,
        "model": route.model,
        "output_status": route.output_status,
        "context_files": TEXT_CONTEXT_FILES + CSV_CONTEXT_FILES,
        "response_excerpt": content[:5000],
    }
    RAW_JSONL.write_text(json.dumps(raw_record, ensure_ascii=False) + "\n", encoding="utf-8")
    LATEST_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tasks = payload.get("task_queue", [])
    if not isinstance(tasks, list):
        tasks = []
    write_task_queue(tasks)

    PROGRESS_JSON.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "context_text_files": len(TEXT_CONTEXT_FILES),
                "context_csv_files": len(CSV_CONTEXT_FILES),
                "task_queue_rows": len(tasks),
                "raw_chunks": 1,
                "output_status": "needs_review",
                "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    REPORT.write_text(
        "\n".join(
            [
                "# DeepSeek-first 项目上下文同步报告",
                "",
                "## 结论",
                "",
                f"- 输出状态：needs_review。",
                f"- 文本上下文文件：{len(TEXT_CONTEXT_FILES)} 个。",
                f"- CSV 上下文文件：{len(CSV_CONTEXT_FILES)} 个。",
                f"- DeepSeek 后续任务队列：{len(tasks)} 条。",
                "",
                "## 输出文件",
                "",
                "- `70_outputs/processed_tables/deepseek_first_task_queue.csv`",
                "- `60_model/llm_runs/deepseek_project_context_sync_latest.json`",
                "- `60_model/llm_runs/deepseek_project_context_sync_raw.jsonl`",
                "",
                "## 口径",
                "",
                "- 本报告只同步上下文和任务分解，不代表 P2 门禁通过。",
                "- Codex 后续只做调度、本地执行、关键补丁和最终门禁。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote DeepSeek-first task queue rows={len(tasks)} to {TASK_QUEUE_CSV}")
    print(f"wrote context sync report to {REPORT}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-text-chars", type=int, default=7000)
    parser.add_argument("--include-env-path", action="store_true")
    args = parser.parse_args()
    run(args.max_text_chars, args.include_env_path)


if __name__ == "__main__":
    main()
