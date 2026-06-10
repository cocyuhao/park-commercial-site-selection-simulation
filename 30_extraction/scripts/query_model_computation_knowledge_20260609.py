from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
KB_DIR = ROOT / "10_research" / "recent_knowledge_base_20260609"
PACK_JSONL = KB_DIR / "model_computation_knowledge_pack_20260609.jsonl"
CLASSIC_JSONL = KB_DIR / "classic_model_reference_20260609.jsonl"

OFF_DOMAIN_RE = re.compile(
    r"clinical|patient|cancer|genomic|drug|molecular|semiconductor|quantum|microgrid|wind farm|solar power|battery chemistry|"
    r"hemoglobin|preterm|infant|pediatric|paediatric|disease|hospital|healthcare|medical|surgery|nursing|cardio|diabetes|"
    r"protein|enzyme|pharmaceutical|wireless sensor only|crop disease|livestock|"
    r"option pricing|black scholes|baseball|railway settlement|space weather|solar fuel|livelihood assets|agriculture international|"
    r"mass disasters|rescuing operations|earthquake|flood|wildfire|construction material|power grid",
    re.IGNORECASE,
)

QUERY_SYNONYMS = {
    "收益": ["revenue", "spending", "income", "profit"],
    "收入": ["income", "revenue", "spending"],
    "天气": ["weather", "seasonality", "rain", "temperature"],
    "转化率": ["conversion", "conversion rate"],
    "转化": ["conversion", "conversion rate"],
    "离散": ["discrete", "choice", "logit"],
    "选择": ["choice", "selection", "utility"],
    "目的地": ["destination", "attraction", "site"],
    "消费": ["spending", "consumer", "willingness to pay"],
    "价格": ["price", "pricing", "price sensitivity"],
    "敏感": ["sensitivity", "sensitive"],
    "排队": ["queue", "queueing", "wait time"],
    "容量": ["capacity", "throughput"],
    "热力": ["heatmap", "trajectory", "density"],
    "仿真": ["simulation", "model"],
    "校准": ["calibration", "validation"],
    "不确定": ["uncertainty", "stochastic", "probabilistic"],
    "客流": ["visitor flow", "footfall", "demand"],
    "轨迹": ["trajectory", "route sequence"],
    "ABM": ["agent based", "agent-based", "multi agent", "pedestrian simulation"],
    "Monte": ["Monte Carlo", "uncertainty", "stochastic"],
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def tokenize(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-zA-Z0-9\u4e00-\u9fff]+", text.lower()) if len(word) >= 2}


def expand_query(query: str) -> str:
    expanded = [query]
    for key, synonyms in QUERY_SYNONYMS.items():
        if key.lower() in query.lower():
            expanded.extend(synonyms)
    return " ".join(expanded)


def row_text(row: dict[str, Any]) -> str:
    return " ".join(
        str(part or "")
        for part in [
            row.get("title"),
            row.get("abstract_excerpt"),
            row.get("abstract"),
            row.get("project_landing_text"),
            row.get("project_use"),
            row.get("quality_reason"),
        ]
    )


def rank(rows: list[dict[str, Any]], query: str, layer: str | None, limit: int) -> list[dict[str, Any]]:
    expanded_query = expand_query(query)
    query_tokens = tokenize(expanded_query)
    query_lower = expanded_query.lower()
    ranked = []
    for row in rows:
        row_layer = str(row.get("model_layer") or row.get("layer") or "")
        if layer and layer != row_layer:
            continue
        text = row_text(row)
        text_lower = text.lower()
        if OFF_DOMAIN_RE.search(text):
            continue
        if ("abm" in query_lower or "agent based" in query_lower) and not re.search(
            r"agent-based|agent based|multi agent|pedestrian|crowd|trajectory|heatmap|simulation",
            text,
            re.IGNORECASE,
        ):
            continue
        if "monte" in query_lower and not re.search(r"monte carlo|uncertainty|stochastic|probabilistic|sensitivity", text, re.IGNORECASE):
            continue
        if re.search(r"收益|收入|revenue|conversion|转化", query, re.IGNORECASE) and not re.search(
            r"revenue|spending|retail|demand|conversion|visitor|footfall|consumer|food beverage|concession|commercial",
            text,
            re.IGNORECASE,
        ):
            continue
        if re.search(r"离散|choice|logit|目的地|价格|price", query, re.IGNORECASE) and not re.search(
            r"choice|logit|willingness to pay|price|pricing|destination|consumer|retail|spending|utility",
            text,
            re.IGNORECASE,
        ):
            continue
        tokens = tokenize(text)
        overlap = len(query_tokens & tokens)
        phrase_bonus = 8 if query and query.lower() in text.lower() else 0
        for phrase in expanded_query.split():
            if len(phrase) >= 5 and phrase.lower() in text.lower():
                phrase_bonus += 1
        layer_bonus = 10 if layer and layer == row_layer else 0
        base = float(row.get("model_pack_score") or row.get("model_reference_score") or 0)
        if query_tokens and overlap == 0 and phrase_bonus == 0:
            continue
        ranked.append((overlap * 5 + phrase_bonus + layer_bonus + base / 12, row))
    ranked.sort(key=lambda item: (item[0], float(item[1].get("model_pack_score") or item[1].get("model_reference_score") or 0)), reverse=True)
    return [row for _, row in ranked[:limit]]


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="查询计算与模型知识包")
    parser.add_argument("--query", default="", help="例如：Monte Carlo 收益 P95 天气 转化率")
    parser.add_argument("--layer", default=None, help="例如：monte_carlo_uncertainty")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--include-classic", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    rows = read_jsonl(PACK_JSONL)
    if args.include_classic:
        rows.extend(read_jsonl(CLASSIC_JSONL))
    results = rank(rows, args.query, args.layer, args.limit)
    payload = {
        "query": args.query,
        "layer": args.layer,
        "source": "model_computation_pack",
        "result_count": len(results),
        "results": [
            {
                "model_layer": row.get("model_layer") or row.get("layer"),
                "source_tier": row.get("source_tier") or row.get("reference_class"),
                "score": row.get("model_pack_score") or row.get("model_reference_score"),
                "year": row.get("year"),
                "title": row.get("title"),
                "source": row.get("source"),
                "venue": row.get("venue"),
                "url": row.get("url"),
                "layer_controls": row.get("layer_controls") or row.get("project_use"),
                "quality_reason": row.get("quality_reason"),
            }
            for row in results
        ],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"模型知识包命中：{payload['result_count']}")
    for index, row in enumerate(payload["results"], start=1):
        print(f"\n{index}. {row['model_layer']} | {row['year']} | {row['source_tier']} | {row['score']}")
        print(row["title"])
        print(f"来源：{row['source']} / {row['venue']}")
        print(f"控制：{row['layer_controls']}")
        print(f"链接：{row['url']}")


if __name__ == "__main__":
    main()
