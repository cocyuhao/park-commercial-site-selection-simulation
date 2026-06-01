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


QUEUE_CSV = ROOT / "30_extraction" / "tables" / "pdf_table_review_queue.csv"
TABLE_JSONL = ROOT / "30_extraction" / "tables" / "pdf_native_tables.jsonl"
OUT_DIR = ROOT / "60_model" / "llm_runs"
RAW_JSONL = OUT_DIR / "deepseek_evidence_candidates_raw.jsonl"
PROGRESS_JSON = OUT_DIR / "deepseek_evidence_candidates_progress.json"
OUT_CSV = ROOT / "30_extraction" / "tables" / "pdf_table_evidence_candidates_deepseek.csv"
REPORT = ROOT / "40_quality_evidence" / "deepseek_evidence_candidates_report.md"


ALLOWED_CANDIDATE_TYPES = {
    "visitor_flow",
    "time_peak",
    "poi_hot_visit",
    "commercial_supply",
    "consumption_spending",
    "revenue_finance",
    "supply_gap",
    "other",
}

FIELDS = [
    "candidate_id",
    "table_id",
    "source_file",
    "page",
    "table_index",
    "topic_draft",
    "candidate_type",
    "metric_name_draft",
    "subject_draft",
    "value_draft",
    "unit_draft",
    "period_or_scope_draft",
    "source_row_text_draft",
    "source_column_hint",
    "extraction_confidence",
    "review_reason",
    "output_status",
    "executor",
    "model",
    "review_gate",
    "llm_task_id",
    "run_id",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_tables(path: Path) -> dict[str, dict[str, Any]]:
    tables: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        tables[str(record.get("table_id", ""))] = record
    return tables


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def clean_cell(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def compact_rows(rows: list[list[Any]], max_rows: int = 30) -> list[list[str]]:
    cleaned: list[list[str]] = []
    for row in rows:
        values = [clean_cell(cell) for cell in row]
        if any(values):
            cleaned.append(values)
    return cleaned[:max_rows]


def choose_queue(priority: str) -> list[dict[str, str]]:
    rows = read_csv(QUEUE_CSV)
    return [row for row in rows if row.get("sampling_priority") == priority]


def build_items(queue_rows: list[dict[str, str]], tables_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for queue_row in queue_rows:
        table_id = queue_row["table_id"]
        table = tables_by_id.get(table_id)
        if not table:
            continue
        items.append(
            {
                "table_id": table_id,
                "source_file": Path(queue_row.get("source_file", "")).name,
                "page": queue_row.get("page", ""),
                "table_index": queue_row.get("table_index", ""),
                "topic_draft": queue_row.get("topic_draft", ""),
                "row_count": queue_row.get("row_count", ""),
                "column_count": queue_row.get("column_count", ""),
                "rows": compact_rows(table.get("rows") or []),
            }
        )
    return items


def chunked(rows: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [rows[index : index + size] for index in range(0, len(rows), size)]


def extract_json_array(text: str) -> list[dict[str, Any]]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped, flags=re.IGNORECASE).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    start = stripped.find("[")
    end = stripped.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("DeepSeek response does not contain a JSON array")
    data = json.loads(stripped[start : end + 1])
    if not isinstance(data, list):
        raise ValueError("DeepSeek response JSON is not a list")
    return data


def normalize_candidate_type(value: Any) -> str:
    value = clean_cell(value)
    return value if value in ALLOWED_CANDIDATE_TYPES else "other"


def normalize_confidence(value: Any) -> str:
    value = clean_cell(value).lower()
    return value if value in {"low", "medium", "high"} else "low"


def truncate(value: Any, limit: int) -> str:
    return clean_cell(value)[:limit]


def make_messages(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    allowed = ", ".join(sorted(ALLOWED_CANDIDATE_TYPES))
    return [
        {
            "role": "system",
            "content": (
                "你是公园商业选址项目的低成本证据候选抽取助手。"
                "你的输出只能作为 needs_review 草稿，不能做最终真实性判断，不能标注 checked。"
                "只根据输入表格里的单元格抽取，不要补充、推断或发明表中没有的数字。"
                "只输出 JSON 数组，不要输出 Markdown。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请从以下 PDF 原生表格中抽取可进入二次人工复核的指标候选。\n"
                f"candidate_type 只能从这些值中选：{allowed}。\n"
                "每个候选输出字段必须为："
                "table_id, candidate_type, metric_name_draft, subject_draft, value_draft, "
                "unit_draft, period_or_scope_draft, source_row_text_draft, source_column_hint, "
                "extraction_confidence, review_reason, output_status。\n"
                "output_status 必须是 needs_review；extraction_confidence 只能是 low/medium/high。\n"
                "如果某张表没有可抽取业务指标，输出一条 candidate_type=other、metric_name_draft=no_candidate 的记录。\n"
                "每张表最多输出 12 条候选；优先选择数字、单位、主体和来源行最清楚的候选。\n"
                "热门到访/POI 表：优先抽 POI 名称、指数、人均消费等一行一候选。\n"
                "客流/峰值表：优先抽到访人数、时段峰值、同比/占比等明确数字。\n"
                "商业供给/消费表：优先抽业态、覆盖度、TGI、消费金额、频次或供给数量。\n"
                "输入 JSON：\n"
                + json.dumps(items, ensure_ascii=False)
            ),
        },
    ]


def existing_rows() -> list[dict[str, str]]:
    if not OUT_CSV.exists():
        return []
    return read_csv(OUT_CSV)


def normalize_output(
    parsed: list[dict[str, Any]],
    source_by_table: dict[str, dict[str, Any]],
    route: Any,
    run_id: str,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in parsed:
        table_id = truncate(item.get("table_id", ""), 40)
        source = source_by_table.get(table_id)
        if not source:
            continue
        rows.append(
            {
                "candidate_id": "",
                "table_id": table_id,
                "source_file": str(source.get("source_file", "")),
                "page": str(source.get("page", "")),
                "table_index": str(source.get("table_index", "")),
                "topic_draft": str(source.get("topic_draft", "")),
                "candidate_type": normalize_candidate_type(item.get("candidate_type", "")),
                "metric_name_draft": truncate(item.get("metric_name_draft", ""), 120),
                "subject_draft": truncate(item.get("subject_draft", ""), 180),
                "value_draft": truncate(item.get("value_draft", ""), 80),
                "unit_draft": truncate(item.get("unit_draft", ""), 80),
                "period_or_scope_draft": truncate(item.get("period_or_scope_draft", ""), 180),
                "source_row_text_draft": truncate(item.get("source_row_text_draft", ""), 500),
                "source_column_hint": truncate(item.get("source_column_hint", ""), 180),
                "extraction_confidence": normalize_confidence(item.get("extraction_confidence", "")),
                "review_reason": truncate(item.get("review_reason", ""), 260),
                "output_status": "needs_review",
                "executor": route.default_executor,
                "model": route.model,
                "review_gate": route.review_gate,
                "llm_task_id": "LLM-003",
                "run_id": run_id,
            }
        )
    return rows


def renumber(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = sorted(rows, key=lambda row: (row["source_file"], int(row["page"] or 0), row["table_id"], row["metric_name_draft"], row["subject_draft"]))
    for index, row in enumerate(rows, start=1):
        row["candidate_id"] = f"EV-CAND-{index:04d}"
    return rows


def write_report(rows: list[dict[str, str]], total_tables: int, raw_count: int) -> None:
    by_type = Counter(row.get("candidate_type", "") for row in rows)
    by_status = Counter(row.get("output_status", "") for row in rows)
    by_conf = Counter(row.get("extraction_confidence", "") for row in rows)
    completed_tables = {row.get("table_id", "") for row in rows}
    lines = [
        "# DeepSeek PDF 表格证据候选草稿报告",
        "",
        "## 结论",
        "",
        f"- 输入 P0 表格：{total_tables} 张。",
        f"- 已覆盖表格：{len(completed_tables)} 张。",
        f"- 证据候选草稿：{len(rows)} 条。",
        f"- DeepSeek 批次：{raw_count} 个。",
        f"- 输出状态：{dict(sorted(by_status.items()))}",
        f"- 候选类型：{dict(sorted(by_type.items()))}",
        f"- 置信度：{dict(sorted(by_conf.items()))}",
        "",
        "## 口径限制",
        "",
        "- 本结果由 DeepSeek 生成，只能作为 `needs_review`。",
        "- 不能直接写入 `40_quality_evidence/evidence_ledger.csv`。",
        "- 后续入账必须回查 `pdf_native_tables.jsonl`、PDF 页码、单位、字段含义和重复项。",
        "- 若候选为热门 POI/到访指数，仍不等于完整供给清单。",
        "",
        "## 输出文件",
        "",
        "- `30_extraction/tables/pdf_table_evidence_candidates_deepseek.csv`",
        "- `60_model/llm_runs/deepseek_evidence_candidates_raw.jsonl`",
        "- `60_model/llm_runs/deepseek_evidence_candidates_progress.json`",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_progress(run_id: str, total_tables: int, rows: list[dict[str, str]], chunk_size: int) -> None:
    completed_tables = {row.get("table_id", "") for row in rows}
    raw_count = sum(1 for line in RAW_JSONL.read_text(encoding="utf-8").splitlines() if line.strip()) if RAW_JSONL.exists() else 0
    PROGRESS_JSON.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "total_tables": total_tables,
                "completed_tables": len(completed_tables),
                "remaining_tables": total_tables - len(completed_tables),
                "candidate_rows": len(rows),
                "raw_chunks": raw_count,
                "chunk_size": chunk_size,
                "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def run(priority: str, chunk_size: int, resume: bool, max_chunks: int | None) -> None:
    task_id = "LLM-003"
    route = route_for(task_id)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    queue_rows = choose_queue(priority)
    tables_by_id = read_tables(TABLE_JSONL)
    items = build_items(queue_rows, tables_by_id)
    source_by_table = {item["table_id"]: item for item in items}

    rows = existing_rows() if resume else []
    completed = {row["table_id"] for row in rows}
    pending = [item for item in items if item["table_id"] not in completed]
    chunks = chunked(pending, chunk_size)
    if max_chunks is not None:
        chunks = chunks[:max_chunks]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_mode = "a" if resume and RAW_JSONL.exists() else "w"
    with RAW_JSONL.open(raw_mode, encoding="utf-8") as raw_file:
        for chunk_index, chunk in enumerate(chunks, start=1):
            content = run_deepseek_task(task_id, make_messages(chunk), temperature=0.0)
            raw_file.write(
                json.dumps(
                    {
                        "run_id": run_id,
                        "task_id": task_id,
                        "task_name": route.task_name,
                        "executor": route.default_executor,
                        "model": route.model,
                        "output_status": route.output_status,
                        "chunk_index": chunk_index,
                        "input_table_ids": [item["table_id"] for item in chunk],
                        "response_excerpt": content[:4000],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            raw_file.flush()
            parsed = extract_json_array(content)
            rows.extend(normalize_output(parsed, source_by_table, route, run_id))
            rows = renumber(rows)
            write_csv(OUT_CSV, rows, FIELDS)
            raw_count = sum(1 for line in RAW_JSONL.read_text(encoding="utf-8").splitlines() if line.strip())
            write_report(rows, len(items), raw_count)
            write_progress(run_id, len(items), rows, chunk_size)

    rows = renumber(rows)
    write_csv(OUT_CSV, rows, FIELDS)
    raw_count = sum(1 for line in RAW_JSONL.read_text(encoding="utf-8").splitlines() if line.strip()) if RAW_JSONL.exists() else 0
    write_report(rows, len(items), raw_count)
    write_progress(run_id, len(items), rows, chunk_size)
    print(f"wrote {len(rows)} needs_review evidence candidates to {OUT_CSV}")
    print(f"covered_tables={len({row['table_id'] for row in rows})}/{len(items)}")
    print(f"wrote report to {REPORT}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--priority", default="P0_second_evidence_candidate")
    parser.add_argument("--chunk-size", type=int, default=2)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-chunks", type=int, default=None)
    args = parser.parse_args()
    run(args.priority, args.chunk_size, args.resume, args.max_chunks)


if __name__ == "__main__":
    main()
