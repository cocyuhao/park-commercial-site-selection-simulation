from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LATEST_JSON = ROOT / "60_model" / "llm_runs" / "deepseek_project_context_sync_latest.json"
TASK_QUEUE_CSV = ROOT / "70_outputs" / "processed_tables" / "deepseek_first_task_queue.csv"
OUT_REVIEW = ROOT / "40_quality_evidence" / "deepseek_project_context_sync_review.csv"
REPORT = ROOT / "40_quality_evidence" / "deepseek_project_context_sync_review.md"

REVIEW_FIELDS = ["check_id", "status", "severity", "finding", "evidence"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def ok(condition: bool) -> str:
    return "pass" if condition else "fail"


def add(rows: list[dict[str, str]], status: str, severity: str, finding: str, evidence: str) -> None:
    rows.append(
        {
            "check_id": f"DS-FIRST-{len(rows) + 1:03d}",
            "status": status,
            "severity": severity,
            "finding": finding,
            "evidence": evidence,
        }
    )


def main() -> None:
    payload = json.loads(LATEST_JSON.read_text(encoding="utf-8-sig"))
    queue_rows = read_csv(TASK_QUEUE_CSV)
    review: list[dict[str, str]] = []
    delegates = Counter(row.get("delegate_to", "") for row in queue_rows)
    statuses = Counter(row.get("output_status", "") for row in queue_rows)
    gate_types = Counter(row.get("gate_type", "") for row in queue_rows)
    p2_claims = [
        row.get("queue_id", "")
        for row in queue_rows
        if "进入P2" in "".join(row.values()) or "P2通过" in "".join(row.values()) or "checked" == row.get("output_status", "")
    ]

    add(review, ok(payload.get("output_status") == "needs_review"), "error", f"context sync output_status={payload.get('output_status')}", str(LATEST_JSON))
    add(review, ok(len(queue_rows) >= 5), "error", f"DeepSeek-first task queue rows={len(queue_rows)}", str(TASK_QUEUE_CSV))
    add(review, ok(delegates.get("deepseek", 0) >= 3), "error", f"delegate distribution={dict(delegates)}", "delegate_to")
    add(review, ok(all(status in {"draft", "needs_review"} for status in statuses)), "error", f"task output_status distribution={dict(statuses)}", "output_status")
    add(review, ok(not p2_claims), "error", f"unexpected P2/checked claims={p2_claims}", "task queue text")
    add(review, "pass", "info", f"gate_type distribution={dict(gate_types)}", "gate_type")

    write_csv(OUT_REVIEW, review, REVIEW_FIELDS)
    by_status = Counter(row["status"] for row in review)
    REPORT.write_text(
        "\n".join(
            [
                "# DeepSeek-first 项目上下文同步本地复核报告",
                "",
                "## 结论",
                "",
                f"- 复核项状态：{dict(sorted(by_status.items()))}",
                f"- 任务委托分布：{dict(sorted(delegates.items()))}",
                f"- 任务状态分布：{dict(sorted(statuses.items()))}",
                "",
                "## 口径",
                "",
                "- 本复核只确认 DeepSeek-first 任务队列可作为草稿使用。",
                "- 不代表 P2 阶段门禁通过。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    failures = [row for row in review if row["status"] == "fail"]
    print(f"wrote DeepSeek-first context sync review rows={len(review)} to {OUT_REVIEW}")
    print(f"wrote report to {REPORT}")
    print(f"failures={len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
