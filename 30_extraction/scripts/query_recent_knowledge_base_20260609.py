from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
KB_DIR = ROOT / "10_research" / "recent_knowledge_base_20260609"
CORE_JSONL = KB_DIR / "curated_core_knowledge_base_20260609.jsonl"
SCREENED_JSONL = KB_DIR / "screened_knowledge_base_20260609.jsonl"


def load_rows(core_only: bool = True) -> list[dict[str, Any]]:
    path = CORE_JSONL if core_only and CORE_JSONL.exists() else SCREENED_JSONL
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9\u4e00-\u9fff]+", text.lower())
    return {word for word in words if len(word) >= 2}


def row_text(row: dict[str, Any]) -> str:
    return " ".join(
        str(part or "")
        for part in [
            row.get("title"),
            row.get("abstract"),
            row.get("theme"),
            row.get("venue"),
            " ".join(row.get("project_landing", []) or []),
            row.get("quality_reason"),
        ]
    )


def rank_rows(rows: list[dict[str, Any]], query: str, theme: str | None, landing: str | None, limit: int) -> list[dict[str, Any]]:
    query_tokens = tokenize(query)
    ranked = []
    for row in rows:
        if theme and theme not in str(row.get("theme") or ""):
            continue
        landing_text = "; ".join(row.get("project_landing", []) or [])
        if landing and landing not in landing_text:
            continue
        text = row_text(row)
        row_tokens = tokenize(text)
        overlap = len(query_tokens & row_tokens)
        phrase_bonus = 0
        for phrase in [query, landing or "", theme or ""]:
            if phrase and phrase.lower() in text.lower():
                phrase_bonus += 8
        score = overlap * 3 + phrase_bonus + float(row.get("score") or 0) / 10
        if query_tokens and overlap == 0 and phrase_bonus == 0:
            continue
        ranked.append((score, row))
    ranked.sort(key=lambda item: (item[0], float(item[1].get("score") or 0), int(item[1].get("year") or 0)), reverse=True)
    return [row for _, row in ranked[:limit]]


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="查询 2026-06-09 近年部署级核心知识库")
    parser.add_argument("--query", default="", help="关键词，如 ABM 轨迹层、天气、客群、报告、DeepSeek 约束")
    parser.add_argument("--theme", default=None, help="主题过滤，如 agent_llm_simulation")
    parser.add_argument("--landing", default=None, help="项目落点过滤，如 AI 约束评估与人工复核")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--include-reference", action="store_true", help="使用全量筛选库而不是部署级核心库")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    rows = load_rows(core_only=not args.include_reference)
    results = rank_rows(rows, args.query, args.theme, args.landing, args.limit)
    payload = {
        "query": args.query,
        "theme": args.theme,
        "landing": args.landing,
        "source": "curated_core" if not args.include_reference else "screened_full",
        "result_count": len(results),
        "results": [
            {
                "year": row.get("year"),
                "title": row.get("title"),
                "source": row.get("source"),
                "venue": row.get("venue"),
                "tier": row.get("curation_tier") or row.get("tier"),
                "score": row.get("score"),
                "project_landing": row.get("project_landing"),
                "quality_reason": row.get("quality_reason", ""),
                "url": row.get("url"),
            }
            for row in results
        ],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"知识库：{payload['source']}；命中：{payload['result_count']}")
    for index, row in enumerate(payload["results"], start=1):
        print(f"\n{index}. {row['year']} | {row['tier']} | {row['score']}")
        print(row["title"])
        print(f"来源：{row['source']} / {row['venue']}")
        print(f"落点：{'; '.join(row.get('project_landing') or [])}")
        if row.get("quality_reason"):
            print(f"质量理由：{row['quality_reason']}")
        print(f"链接：{row['url']}")


if __name__ == "__main__":
    main()
