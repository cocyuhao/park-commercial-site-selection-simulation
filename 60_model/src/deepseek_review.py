"""deepseek_review.py — Tier-2 DeepSeek 语义审查模块

流水线三层架构：
  Tier 1  auto_gate.py       → 本地 Python 规则（结构/枚举/正则）
  Tier 2  deepseek_review.py → DeepSeek 语义判断（borderline / 误报过滤）
  Tier 3  Codex              → 仅处理 Tier 2 仍无法判断的高风险情况

所有 Tier-2 输出字段带 output_status="needs_review"，
Tier-3 确认后才可升为 "checked"。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "60_model" / "src"))

from llm_router import run_deepseek_task  # noqa: E402


# --------------------------------------------------------------------------- #
# 公共返回结构
# --------------------------------------------------------------------------- #

def _result(
    passed: bool,
    issues: list[str],
    escalate: bool = False,
    details: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "passed": passed,
        "issues": issues,
        "escalate": escalate,
        "details": details or [],
        "tier": 2,
        "output_status": "needs_review",
    }


def _ask_deepseek(task_id: str, prompt: str) -> str:
    """向 DeepSeek 发送单轮审查请求，返回原始字符串响应。"""
    messages = [
        {
            "role": "system",
            "content": (
                "你是一个严格的数据质量审查员。"
                "只输出 JSON，不输出其他内容。"
                "你的判断不能标注 checked，只能用 needs_review 或 draft。"
            ),
        },
        {"role": "user", "content": prompt},
    ]
    return run_deepseek_task(task_id, messages, temperature=0.0)


# --------------------------------------------------------------------------- #
# Review 1 : 安全扫描误报过滤 (LLM-009)
# --------------------------------------------------------------------------- #

def review_security_hits(hits: list[str]) -> dict[str, Any]:
    """Tier-1 正则扫描命中后，DeepSeek 判断是否为真实凭据泄露。

    hits: list[str]  — auto_gate.gate_security_scan 返回的 issues 列表
    返回:
      passed=True  → 全部为误报，无需 Codex
      passed=False → 仍有疑似真实泄露，escalate=True 给 Codex
    """
    if not hits:
        return _result(True, ["无命中，跳过语义审查"])

    items_json = json.dumps(hits, ensure_ascii=False, indent=2)
    prompt = f"""以下是正则扫描发现的疑似 API Key 命中列表：
{items_json}

请逐项判断是否为真实凭据泄露（而非测试占位符、注释示例、掩码格式 sk-xx...xx、env 变量名引用）。
输出格式（JSON 数组，每项对应输入的一项）：
[
  {{
    "hit": "<原始命中文本>",
    "is_real_leak": true/false,
    "reason": "<简短理由>"
  }}
]"""

    try:
        raw = _ask_deepseek("LLM-009", prompt)
        items: list[dict[str, Any]] = json.loads(raw)
    except (json.JSONDecodeError, Exception) as exc:
        return _result(False, [f"DeepSeek 解析失败: {exc}"], escalate=True)

    real_leaks = [it for it in items if it.get("is_real_leak")]
    if real_leaks:
        return _result(
            False,
            [f"DeepSeek 确认真实泄露: {it['hit'][:60]}… ({it.get('reason','')})" for it in real_leaks],
            escalate=True,
            details=items,
        )
    return _result(True, ["全部为误报，已过滤"], details=items)


# --------------------------------------------------------------------------- #
# Review 2 : 证据引用语义一致性 (LLM-009 复用，语义不同)
# --------------------------------------------------------------------------- #

def review_evidence_quotes(
    rows: list[dict[str, Any]],
    max_rows: int = 20,
) -> dict[str, Any]:
    """检查 evidence_ledger 中 source_quote 与 value+unit 的语义一致性。

    rows: 从 CSV 读取的行列表（已通过 auto_gate 结构校验）
    只审查 validation_status in {"needs_review", "conflict"} 的行，
    或随机抽取 ≤ max_rows 行。
    """
    to_review = [
        r for r in rows
        if r.get("validation_status") in ("needs_review", "conflict")
    ][:max_rows]

    if not to_review:
        return _result(True, ["无需复核的行，跳过语义审查"])

    items_json = json.dumps(
        [
            {
                "metric_id": r.get("metric_id"),
                "metric_name": r.get("metric_name"),
                "value": r.get("value"),
                "unit": r.get("unit"),
                "source_quote": r.get("source_quote", "")[:200],
            }
            for r in to_review
        ],
        ensure_ascii=False,
        indent=2,
    )
    prompt = f"""以下是待审查的证据条目，请逐项判断 source_quote 是否支持 value+unit 声明：
{items_json}

输出格式（JSON 数组）：
[
  {{
    "metric_id": "MET-XXXX",
    "consistent": true/false,
    "issue": "<如果 false，说明不一致原因；否则为空字符串>"
  }}
]"""

    try:
        raw = _ask_deepseek("LLM-009", prompt)
        items: list[dict[str, Any]] = json.loads(raw)
    except (json.JSONDecodeError, Exception) as exc:
        return _result(False, [f"DeepSeek 解析失败: {exc}"], escalate=True)

    inconsistent = [it for it in items if not it.get("consistent")]
    if inconsistent:
        return _result(
            False,
            [f"{it['metric_id']}: {it.get('issue', '不一致')}" for it in inconsistent],
            escalate=True,
            details=items,
        )
    return _result(True, [f"全部 {len(items)} 条引用语义一致"], details=items)


# --------------------------------------------------------------------------- #
# Review 3 : partial 表格可用性判断 (LLM-010)
# --------------------------------------------------------------------------- #

def review_partial_tables(
    tables: list[dict[str, Any]],
    max_tables: int = 30,
) -> dict[str, Any]:
    """对 quality_flag="partial" 的表格，DeepSeek 判断是否含有效业务数据。

    tables: 从 JSONL 筛出的 partial 行（含 rows 字段）
    返回每张表的 usable: true/false，供下游分类任务决定是否跳过。
    """
    sample = tables[:max_tables]
    if not sample:
        return _result(True, ["无 partial 表，跳过"])

    items_json = json.dumps(
        [
            {
                "table_id": t.get("table_id"),
                "fill_rate": t.get("fill_rate"),
                "row_count": t.get("row_count"),
                "column_count": t.get("column_count"),
                "sample_rows": t.get("rows", [])[:3],
            }
            for t in sample
        ],
        ensure_ascii=False,
        indent=2,
    )
    prompt = f"""以下是填充率在 30%~70% 之间的"partial"表格样本，请判断每张表是否含有可用的业务数据：
{items_json}

判断标准：如果前三行包含有意义的文字或数字（而非全空、分隔符或页眉），则 usable=true。
输出格式（JSON 数组）：
[
  {{
    "table_id": "TBL-XXXXX",
    "usable": true/false,
    "reason": "<简短理由>"
  }}
]"""

    try:
        raw = _ask_deepseek("LLM-010", prompt)
        items: list[dict[str, Any]] = json.loads(raw)
    except (json.JSONDecodeError, Exception) as exc:
        return _result(False, [f"DeepSeek 解析失败: {exc}"], escalate=True)

    unusable = [it for it in items if not it.get("usable")]
    issues = [f"{it['table_id']}: {it.get('reason', '不可用')}" for it in unusable]
    return _result(
        True,
        issues or [f"{len(items)} 张 partial 表全部可用"],
        escalate=False,
        details=items,
    )


# --------------------------------------------------------------------------- #
# 统一 Tier-2 入口
# --------------------------------------------------------------------------- #

_DISPATCH = {
    "security":  lambda kw: review_security_hits(kw["hits"]),
    "evidence":  lambda kw: review_evidence_quotes(kw["rows"], kw.get("max_rows", 20)),
    "partial":   lambda kw: review_partial_tables(kw["tables"], kw.get("max_tables", 30)),
}


def run_tier2_review(review_type: str, **kwargs: Any) -> dict[str, Any]:
    """根据 review_type 调用对应审查函数。

    review_type 可选值: "security" | "evidence" | "partial"

    示例::

        from deepseek_review import run_tier2_review
        result = run_tier2_review("security", hits=gate_result["issues"])
        if result["escalate"]:
            raise RuntimeError("仍有真实泄露，请 Codex 介入")
    """
    if review_type not in _DISPATCH:
        return _result(False, [f"未知 review_type: {review_type}"], escalate=True)
    return _DISPATCH[review_type](kwargs)
