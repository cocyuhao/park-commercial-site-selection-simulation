from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "60_model" / "src"))

from llm_router import route_for, run_deepseek_task  # noqa: E402


INPUT_CSV = ROOT / "30_extraction" / "tables" / "pdf_native_tables_summary.csv"
OUT_DIR = ROOT / "60_model" / "llm_runs"
RAW_JSONL = OUT_DIR / "deepseek_table_classification_raw.jsonl"
OUT_CSV = ROOT / "30_extraction" / "tables" / "pdf_table_topic_draft_deepseek.csv"
REPORT = ROOT / "40_quality_evidence" / "deepseek_table_classification_report.md"
PROGRESS_JSON = OUT_DIR / "deepseek_table_classification_progress.json"


ALLOWED_TOPICS = {
    "visitor_flow",
    "time_peak",
    "demographic_profile",
    "origin_residence_work",
    "tgi_preference",
    "poi_hot_visit",
    "consumption_spending",
    "commercial_supply",
    "revenue_finance",
    "supply_gap",
    "empty_or_visual_noise",
    "other",
}

FIELDS = [
    "table_id",
    "source_file",
    "page",
    "table_index",
    "row_count",
    "column_count",
    "topic_draft",
    "topic_confidence",
    "reason_draft",
    "evidence_keywords_draft",
    "output_status",
    "executor",
    "model",
    "review_gate",
    "llm_task_id",
    "run_id",
]


def read_rows(limit: int | None = None) -> list[dict[str, str]]:
    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if limit is not None:
        return rows[:limit]
    return rows


def chunked(rows: list[dict[str, str]], size: int) -> list[list[dict[str, str]]]:
    return [rows[index : index + size] for index in range(0, len(rows), size)]


def compact_item(row: dict[str, str]) -> dict[str, str]:
    sample = str(row.get("sample", "") or "")
    sample = re.sub(r"\s+", " ", sample).strip()
    return {
        "table_id": row.get("table_id", ""),
        "source_file": Path(row.get("source_file", "")).name,
        "page": row.get("page", ""),
        "row_count": row.get("row_count", ""),
        "column_count": row.get("column_count", ""),
        "sample": sample[:360],
    }


def extract_json_array(text: str) -> list[dict[str, str]]:
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


def normalize_topic(value: str) -> str:
    value = str(value or "").strip()
    return value if value in ALLOWED_TOPICS else "other"


def normalize_confidence(value: str) -> str:
    value = str(value or "").strip().lower()
    return value if value in {"low", "medium", "high"} else "low"


def make_messages(items: list[dict[str, str]]) -> list[dict[str, str]]:
    allowed = ", ".join(sorted(ALLOWED_TOPICS))
    return [
        {
            "role": "system",
            "content": (
                "你是公园商业选址项目的低成本批处理助手。"
                "你的输出只能作为 draft，不能做最终真实性判断。"
                "只根据给定表格摘要分类，不要补充、推断或发明表中没有的数字。"
                "只输出 JSON 数组，不要输出 Markdown。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请对以下 PDF 原生表格摘要做主题分类草稿。\n"
                f"允许 topic 只能从这些值中选择：{allowed}。\n"
                "每个输入必须输出一条，字段为："
                "table_id, topic_draft, topic_confidence, reason_draft, evidence_keywords_draft, output_status。\n"
                "topic_confidence 只能是 low/medium/high；output_status 必须是 draft。\n"
                "如果 sample 为空或明显是图表抽取噪声，用 empty_or_visual_noise。\n"
                "输入 JSON：\n"
                + json.dumps(items, ensure_ascii=False)
            ),
        },
    ]


def classify_rows(rows: list[dict[str, str]], chunk_size: int) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    task_id = "LLM-002"
    route = route_for(task_id)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw_records: list[dict[str, str]] = []
    results_by_id: dict[str, dict[str, str]] = {}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with RAW_JSONL.open("w", encoding="utf-8") as raw_file:
        for chunk_index, chunk in enumerate(chunked(rows, chunk_size), start=1):
            items = [compact_item(row) for row in chunk]
            messages = make_messages(items)
            content = run_deepseek_task(task_id, messages, temperature=0.0)
            raw_record = {
                "run_id": run_id,
                "task_id": task_id,
                "task_name": route.task_name,
                "executor": route.default_executor,
                "model": route.model,
                "output_status": route.output_status,
                "chunk_index": chunk_index,
                "input_table_ids": [item["table_id"] for item in items],
                "response_excerpt": content[:2000],
            }
            raw_file.write(json.dumps(raw_record, ensure_ascii=False) + "\n")
            raw_records.append(raw_record)

            parsed = extract_json_array(content)
            for item in parsed:
                table_id = str(item.get("table_id", "")).strip()
                if table_id:
                    results_by_id[table_id] = {
                        "topic_draft": normalize_topic(item.get("topic_draft", "")),
                        "topic_confidence": normalize_confidence(item.get("topic_confidence", "")),
                        "reason_draft": str(item.get("reason_draft", "") or "")[:500],
                        "evidence_keywords_draft": str(item.get("evidence_keywords_draft", "") or "")[:250],
                        "output_status": "draft",
                        "executor": route.default_executor,
                        "model": route.model,
                        "review_gate": route.review_gate,
                        "llm_task_id": task_id,
                        "run_id": run_id,
                    }

    output_rows: list[dict[str, str]] = []
    for row in rows:
        result = results_by_id.get(row["table_id"])
        if result is None:
            result = {
                "topic_draft": "other",
                "topic_confidence": "low",
                "reason_draft": "DeepSeek 未返回该 table_id；保守标记为 other。",
                "evidence_keywords_draft": "",
                "output_status": "draft",
                "executor": route.default_executor,
                "model": route.model,
                "review_gate": route.review_gate,
                "llm_task_id": task_id,
                "run_id": run_id,
            }
        output_rows.append(
            {
                "table_id": row.get("table_id", ""),
                "source_file": row.get("source_file", ""),
                "page": row.get("page", ""),
                "table_index": row.get("table_index", ""),
                "row_count": row.get("row_count", ""),
                "column_count": row.get("column_count", ""),
                **result,
            }
        )
    return output_rows, raw_records


def write_outputs(rows: list[dict[str, str]], raw_records: list[dict[str, str]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    by_topic = Counter(row["topic_draft"] for row in rows)
    by_conf = Counter(row["topic_confidence"] for row in rows)
    by_status = Counter(row["output_status"] for row in rows)
    lines = [
        "# DeepSeek PDF 表格主题分类草稿报告",
        "",
        "## 结论",
        "",
        f"- 输入表格：{len(rows)} 张。",
        f"- DeepSeek 批次：{len(raw_records)} 个。",
        f"- 输出状态：{dict(sorted(by_status.items()))}",
        f"- 主题分布：{dict(sorted(by_topic.items()))}",
        f"- 置信度分布：{dict(sorted(by_conf.items()))}",
        "",
        "## 口径限制",
        "",
        "- 本结果由 DeepSeek 生成，只能作为 `draft`。",
        "- 分类只基于 `pdf_native_tables_summary.csv` 的 sample、页码、行列数等摘要，不读取完整表格语义。",
        "- 不得直接写入 `evidence_ledger.csv`，后续必须用 PDF 表格原文、本地规则和抽样复核确认。",
        "- 本报告不包含 DeepSeek Key。",
        "",
        "## 输出文件",
        "",
        "- `30_extraction/tables/pdf_table_topic_draft_deepseek.csv`",
        "- `60_model/llm_runs/deepseek_table_classification_raw.jsonl`",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_existing_results() -> dict[str, dict[str, str]]:
    if not OUT_CSV.exists():
        return {}
    with OUT_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        return {row["table_id"]: row for row in csv.DictReader(f)}


def write_incremental_csv(source_rows: list[dict[str, str]], results_by_id: dict[str, dict[str, str]]) -> None:
    rows: list[dict[str, str]] = []
    for row in source_rows:
        result = results_by_id.get(row["table_id"])
        if not result:
            continue
        rows.append(
            {
                "table_id": row.get("table_id", ""),
                "source_file": row.get("source_file", ""),
                "page": row.get("page", ""),
                "table_index": row.get("table_index", ""),
                "row_count": row.get("row_count", ""),
                "column_count": row.get("column_count", ""),
                "topic_draft": result.get("topic_draft", ""),
                "topic_confidence": result.get("topic_confidence", ""),
                "reason_draft": result.get("reason_draft", ""),
                "evidence_keywords_draft": result.get("evidence_keywords_draft", ""),
                "output_status": result.get("output_status", ""),
                "executor": result.get("executor", ""),
                "model": result.get("model", ""),
                "review_gate": result.get("review_gate", ""),
                "llm_task_id": result.get("llm_task_id", ""),
                "run_id": result.get("run_id", ""),
            }
        )
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_incremental_report(source_rows: list[dict[str, str]], classified_rows: list[dict[str, str]], raw_count: int) -> None:
    by_topic = Counter(row["topic_draft"] for row in classified_rows)
    by_conf = Counter(row["topic_confidence"] for row in classified_rows)
    by_status = Counter(row["output_status"] for row in classified_rows)
    lines = [
        "# DeepSeek PDF 表格主题分类草稿报告",
        "",
        "## 结论",
        "",
        f"- 输入表格：{len(source_rows)} 张。",
        f"- 已分类表格：{len(classified_rows)} 张。",
        f"- DeepSeek 已完成批次：{raw_count} 个。",
        f"- 输出状态：{dict(sorted(by_status.items()))}",
        f"- 主题分布：{dict(sorted(by_topic.items()))}",
        f"- 置信度分布：{dict(sorted(by_conf.items()))}",
        "",
        "## 口径限制",
        "",
        "- 本结果由 DeepSeek 生成，只能作为 `draft`。",
        "- 分类只基于 `pdf_native_tables_summary.csv` 的 sample、页码、行列数等摘要，不读取完整表格语义。",
        "- 不得直接写入 `evidence_ledger.csv`，后续必须用 PDF 表格原文、本地规则和抽样复核确认。",
        "- 本报告不包含 DeepSeek Key。",
        "",
        "## 输出文件",
        "",
        "- `30_extraction/tables/pdf_table_topic_draft_deepseek.csv`",
        "- `60_model/llm_runs/deepseek_table_classification_raw.jsonl`",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def classify_rows_incremental(
    rows: list[dict[str, str]], chunk_size: int, *, resume: bool, max_chunks: int | None
) -> None:
    task_id = "LLM-002"
    route = route_for(task_id)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    existing = read_existing_results() if resume else {}
    results_by_id: dict[str, dict[str, str]] = {
        table_id: {
            "topic_draft": row.get("topic_draft", ""),
            "topic_confidence": row.get("topic_confidence", ""),
            "reason_draft": row.get("reason_draft", ""),
            "evidence_keywords_draft": row.get("evidence_keywords_draft", ""),
            "output_status": row.get("output_status", ""),
            "executor": row.get("executor", ""),
            "model": row.get("model", ""),
            "review_gate": row.get("review_gate", ""),
            "llm_task_id": row.get("llm_task_id", ""),
            "run_id": row.get("run_id", ""),
        }
        for table_id, row in existing.items()
    }

    pending = [row for row in rows if row["table_id"] not in results_by_id]
    chunks = chunked(pending, chunk_size)
    if max_chunks is not None:
        chunks = chunks[:max_chunks]

    raw_mode = "a" if resume and RAW_JSONL.exists() else "w"
    with RAW_JSONL.open(raw_mode, encoding="utf-8") as raw_file:
        for chunk_index, chunk in enumerate(chunks, start=1):
            items = [compact_item(row) for row in chunk]
            content = run_deepseek_task(task_id, make_messages(items), temperature=0.0)
            raw_record = {
                "run_id": run_id,
                "task_id": task_id,
                "task_name": route.task_name,
                "executor": route.default_executor,
                "model": route.model,
                "output_status": route.output_status,
                "chunk_index": chunk_index,
                "input_table_ids": [item["table_id"] for item in items],
                "response_excerpt": content[:2000],
            }
            raw_file.write(json.dumps(raw_record, ensure_ascii=False) + "\n")
            raw_file.flush()

            parsed = extract_json_array(content)
            for item in parsed:
                table_id = str(item.get("table_id", "")).strip()
                if not table_id:
                    continue
                results_by_id[table_id] = {
                    "topic_draft": normalize_topic(item.get("topic_draft", "")),
                    "topic_confidence": normalize_confidence(item.get("topic_confidence", "")),
                    "reason_draft": str(item.get("reason_draft", "") or "")[:500],
                    "evidence_keywords_draft": str(item.get("evidence_keywords_draft", "") or "")[:250],
                    "output_status": "draft",
                    "executor": route.default_executor,
                    "model": route.model,
                    "review_gate": route.review_gate,
                    "llm_task_id": task_id,
                    "run_id": run_id,
                }
            write_incremental_csv(rows, results_by_id)
            classified_rows = list(read_existing_results().values())
            raw_count = sum(1 for _ in RAW_JSONL.open("r", encoding="utf-8")) if RAW_JSONL.exists() else 0
            write_incremental_report(rows, classified_rows, raw_count)
            PROGRESS_JSON.write_text(
                json.dumps(
                    {
                        "run_id": run_id,
                        "total_rows": len(rows),
                        "classified_rows": len(classified_rows),
                        "remaining_rows": len(rows) - len(classified_rows),
                        "chunk_size": chunk_size,
                        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--chunk-size", type=int, default=8)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--incremental", action="store_true")
    parser.add_argument("--max-chunks", type=int, default=None)
    args = parser.parse_args()

    rows = read_rows(args.limit)
    if args.incremental:
        classify_rows_incremental(rows, args.chunk_size, resume=args.resume, max_chunks=args.max_chunks)
        output_count = len(read_existing_results())
    else:
        output_rows, raw_records = classify_rows(rows, args.chunk_size)
        write_outputs(output_rows, raw_records)
        output_count = len(output_rows)
    print(f"wrote {output_count} draft table classifications to {OUT_CSV}")
    print(f"wrote report to {REPORT}")


if __name__ == "__main__":
    main()
