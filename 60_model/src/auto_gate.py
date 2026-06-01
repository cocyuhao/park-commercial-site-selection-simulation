"""auto_gate.py — 本地 Python 自动门控模块

替代原来由 Codex 手动执行的重复性验证任务，
只有自动规则无法判断的情况才向上升级（escalate=True）给 Codex。

覆盖场景：
  - gate_table_quality      : LLM-002/003 前，检查 JSONL 表格填充质量
  - gate_evidence_ledger    : LLM-003→正式入账前，结构+必填+状态规则
  - gate_security_scan      : 任意脚本/文件的 Key 泄露扫描
  - gate_deepseek_output    : DeepSeek draft 输出的 schema 完整性检查
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------- #
# 公共返回结构
# --------------------------------------------------------------------------- #

def _result(
    passed: bool,
    issues: list[str],
    escalate: bool = False,
    **extra: Any,
) -> dict[str, Any]:
    result: dict[str, Any] = {"passed": passed, "issues": issues, "escalate": escalate, "tier": 1}
    result.update(extra)
    return result


# --------------------------------------------------------------------------- #
# Gate 1 : 表格质量检查（LLM-002/003 前自动运行）
# --------------------------------------------------------------------------- #

QUALITY_THRESHOLDS = {
    "good_pass": 0.90,   # ≥90% good → 直接通过，无需 DeepSeek
    "good_warn": 0.70,   # 70–90% good → 交 DeepSeek 判断（tier2_needed）
    "empty_pass": 0.05,  # ≤5% empty → 直接通过
    "empty_warn": 0.20,  # 5–20% empty → 交 DeepSeek 判断
    # good < good_warn 或 empty > empty_warn → 直接升 Codex（escalate）
}


def gate_table_quality(jsonl_path: Path) -> dict[str, Any]:
    """读取 pdf_native_tables.jsonl，统计 quality_flag 分布。

    三段式判断：
      - PASS  : good ≥ good_pass AND empty ≤ empty_pass → 直接通过
      - WARN  : good_warn ≤ good < good_pass 或 empty_pass < empty ≤ empty_warn
                → tier2_needed=True，交 DeepSeek 审查 partial 表格内容
      - FAIL  : good < good_warn 或 empty > empty_warn → escalate=True（Codex）
    """
    if not jsonl_path.exists():
        return _result(False, [f"文件不存在: {jsonl_path}"], escalate=True)

    records: list[dict] = []
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            return _result(False, ["JSONL 解析失败，文件可能损坏"], escalate=True)

    total = len(records)
    if total == 0:
        return _result(False, ["JSONL 为空"], escalate=True)

    counts: dict[str, int] = {"good": 0, "partial": 0, "empty": 0, "unknown": 0}
    for rec in records:
        flag = rec.get("quality_flag", "unknown")
        counts[flag if flag in counts else "unknown"] += 1

    good_rate  = counts["good"]  / total
    empty_rate = counts["empty"] / total
    partial_records = [r for r in records if r.get("quality_flag") == "partial"]
    summary = f"good={good_rate:.1%} empty={empty_rate:.1%} partial={counts['partial']} total={total}"

    # --- 明确失败：直接升 Codex ---
    hard_issues = []
    if good_rate < QUALITY_THRESHOLDS["good_warn"]:
        hard_issues.append(f"good 占比 {good_rate:.1%} 过低（硬下限 {QUALITY_THRESHOLDS['good_warn']:.0%}），需 Codex 介入")
    if empty_rate > QUALITY_THRESHOLDS["empty_warn"]:
        hard_issues.append(f"empty 占比 {empty_rate:.1%} 过高（硬上限 {QUALITY_THRESHOLDS['empty_warn']:.0%}），需 Codex 介入")
    if hard_issues:
        return _result(False, hard_issues, escalate=True, partial_records=partial_records)

    # --- 临界区：交 DeepSeek 判断 ---
    warn_reasons = []
    if good_rate < QUALITY_THRESHOLDS["good_pass"]:
        warn_reasons.append(f"good 占比 {good_rate:.1%} 处于临界区（{QUALITY_THRESHOLDS['good_warn']:.0%}–{QUALITY_THRESHOLDS['good_pass']:.0%}），DeepSeek 复核 partial 表格")
    if empty_rate > QUALITY_THRESHOLDS["empty_pass"]:
        warn_reasons.append(f"empty 占比 {empty_rate:.1%} 处于临界区，DeepSeek 复核")
    if warn_reasons:
        return _result(
            None, warn_reasons, escalate=False,
            tier2_needed=True,
            partial_records=partial_records,
        )

    # --- 明确通过 ---
    return _result(True, [f"通过：{summary}"], escalate=False, partial_records=[])


# --------------------------------------------------------------------------- #
# Gate 2 : 证据台账入账校验（替代 Codex 逐行复核的结构部分）
# --------------------------------------------------------------------------- #

LEDGER_REQUIRED = {
    "metric_id", "metric_name", "value", "unit",
    "source_file", "source_page_or_slide", "source_quote",
    "evidence_type", "confidence", "validation_status",
}
VALID_VALIDATION_STATUS = {"checked", "needs_review", "conflict", "draft"}
VALID_CONFIDENCE = {"high", "medium", "low", "estimate"}
VALID_EVIDENCE_TYPE = {"source_report_pdf", "presentation_assumption", "gis_api", "model_estimate"}
METRIC_ID_RE = re.compile(r"^MET-\d{4}$")


def gate_evidence_ledger(csv_path: Path) -> dict[str, Any]:
    """检查 evidence_ledger.csv 结构完整性和枚举约束。

    通过条件（无需 Codex）：
      - 全部必填字段非空
      - validation_status / confidence / evidence_type 均为允许值
      - metric_id 格式匹配 MET-XXXX
    三段式判断：
      - PASS  : 结构完整 + 枚举合法 + 无 needs_review/conflict 行 → 直接通过
      - WARN  : 结构完整但有 needs_review/conflict 行 → tier2_needed=True，DeepSeek 语义复核
      - FAIL  : 缺列 / 枚举非法 / 格式错误 → escalate=True（Codex）
    """
    if not csv_path.exists():
        return _result(False, [f"文件不存在: {csv_path}"], escalate=True)

    hard_issues: list[str] = []   # 结构错误 → Codex
    review_rows: list[dict] = []  # 语义待审 → DeepSeek

    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = set(reader.fieldnames or [])
        missing_fields = LEDGER_REQUIRED - fieldnames
        if missing_fields:
            return _result(
                False,
                [f"缺少必要列: {sorted(missing_fields)}"],
                escalate=True,
            )

        for i, row in enumerate(reader, start=2):  # row 2 = first data row
            row_id = row.get("metric_id", f"row{i}")

            for col in LEDGER_REQUIRED:
                if not row.get(col, "").strip():
                    hard_issues.append(f"{row_id} 行 {i}: 字段 '{col}' 为空")

            mid = row.get("metric_id", "")
            if mid and not METRIC_ID_RE.match(mid):
                hard_issues.append(f"行 {i}: metric_id '{mid}' 格式错误")

            vs = row.get("validation_status", "")
            if vs and vs not in VALID_VALIDATION_STATUS:
                hard_issues.append(f"{row_id} 行 {i}: validation_status='{vs}' 非法")

            cf = row.get("confidence", "")
            if cf and cf not in VALID_CONFIDENCE:
                hard_issues.append(f"{row_id} 行 {i}: confidence='{cf}' 非法")

            et = row.get("evidence_type", "")
            if et and et not in VALID_EVIDENCE_TYPE:
                hard_issues.append(f"{row_id} 行 {i}: evidence_type='{et}' 非法")

            # 结构合法但语义待审 → 收集给 DeepSeek
            if not hard_issues and vs in ("needs_review", "conflict"):
                review_rows.append(dict(row))

    # --- 明确失败：结构错误 → Codex ---
    if hard_issues:
        return _result(False, hard_issues, escalate=True)

    # --- 临界区：有待审行 → DeepSeek ---
    if review_rows:
        reasons = [
            f"有 {len(review_rows)} 行 validation_status=needs_review/conflict，交 DeepSeek 语义复核"
        ]
        return _result(None, reasons, escalate=False, tier2_needed=True, review_rows=review_rows)

    # --- 明确通过 ---
    return _result(True, ["通过：结构完整，枚举值合法，无待审行"], escalate=False)


# --------------------------------------------------------------------------- #
# Gate 3 : 安全扫描（替代 Codex 手动安全检查）
# --------------------------------------------------------------------------- #

# 匹配常见 API Key 模式（不匹配已知掩码格式 sk-xx...xx）
_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}", re.IGNORECASE),        # DeepSeek / OpenAI key
    re.compile(r"AMAP_WEB_SERVICE_KEY\s*=\s*[A-Za-z0-9]{28,}"),  # 高德 key 赋值
    re.compile(r"(?i)api[_-]?key\s*=\s*['\"]?[A-Za-z0-9]{20,}"), # 通用 API key
]
_SKIP_EXTS = {".pyc", ".png", ".jpg", ".jpeg", ".pdf", ".pptx", ".xlsx"}
_SKIP_DIRS = {".git", "__pycache__", "90_archive", ".venv"}


def gate_security_scan(root: Path, patterns: list[re.Pattern] | None = None) -> dict[str, Any]:
    """递归扫描工作区文本文件，查找疑似明文 Key。

    三段式判断：
      - PASS  : 无任何命中 → 直接通过
      - WARN  : 有正则命中 → tier2_needed=True，DeepSeek 判断是否真实泄露（过滤误报）
      - FAIL  : DeepSeek 确认真实泄露后由上层升级 Codex（本层不直接 escalate）
    """
    patterns = patterns or _SECRET_PATTERNS
    issues: list[str] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name == ".env":
            continue
        if path.suffix.lower() in _SKIP_EXTS:
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pat in patterns:
                if pat.search(line):
                    rel = path.relative_to(root)
                    issues.append(f"{rel}:{lineno} — 疑似明文凭据（模式: {pat.pattern[:30]}…）")
                    break  # 同一行只报一次

    if not issues:
        return _result(True, ["通过：未发现明文凭据"], escalate=False)

    # 有命中 → 不直接 escalate Codex，先交 DeepSeek 过滤误报
    return _result(
        None,
        [f"正则命中 {len(issues)} 处疑似凭据，交 DeepSeek 判断真伪"],
        escalate=False,
        tier2_needed=True,
        raw_hits=issues,  # DeepSeek 语义复核用（含文件路径+行号，不含 Key 原文）
    )


# --------------------------------------------------------------------------- #
# Gate 4 : DeepSeek draft 输出 schema 检查（LLM-002/003 后自动运行）
# --------------------------------------------------------------------------- #

REQUIRED_DRAFT_FIELDS = {"table_id", "topic_draft", "topic_confidence"}


def gate_deepseek_output(jsonl_path: Path, allowed_topics: set[str]) -> dict[str, Any]:
    """验证 DeepSeek 表格分类 draft 输出的 schema 和枚举合法性。

    通过条件（无需 Codex）：
      - 每行包含全部 REQUIRED_DRAFT_FIELDS
      - topic_draft 属于 allowed_topics
      - 无 checked 状态（DeepSeek 不能输出 checked）
    """
    if not jsonl_path.exists():
        return _result(False, [f"文件不存在: {jsonl_path}"], escalate=True)

    issues: list[str] = []
    line_count = 0
    for i, line in enumerate(jsonl_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        line_count += 1
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            issues.append(f"行 {i}: JSON 解析失败")
            continue

        for field in REQUIRED_DRAFT_FIELDS:
            if field not in rec:
                issues.append(f"行 {i}: 缺少字段 '{field}'")

        topic = rec.get("topic_draft", "")
        if topic and topic not in allowed_topics:
            issues.append(f"行 {i}: topic_draft='{topic}' 不在允许集合中")

        status = rec.get("output_status", "")
        if status == "checked":
            issues.append(f"行 {i}: DeepSeek 输出不允许标注 'checked'")

    # --- 明确失败：schema 损坏或 checked 污染 → Codex ---
    hard_issues = [x for x in issues if "缺少字段" in x or "'checked'" in x or "JSON 解析失败" in x]
    soft_issues = [x for x in issues if x not in hard_issues]  # 未知 topic 等模糊问题

    if hard_issues:
        return _result(False, hard_issues, escalate=True)

    if soft_issues:
        # 未知 topic / 低置信度 → 交 DeepSeek 判断
        return _result(
            None, soft_issues, escalate=False,
            tier2_needed=True,
            soft_records=soft_issues,
        )

    return _result(True, [f"通过：schema 合法，共 {line_count} 行"], escalate=False)


# --------------------------------------------------------------------------- #
# 统一入口：根据 task_id 选择对应 gate
# --------------------------------------------------------------------------- #

def run_gate(task_id: str, **kwargs: Any) -> dict[str, Any]:
    """Tier-1 本地 Python 门控。

    根据路由 task_id 自动选择 gate 函数。
    kwargs 透传给对应 gate，调用方无需关心内部实现。

    示例::
        run_gate("LLM-002", jsonl_path=Path("..."))
        run_gate("LLM-003", jsonl_path=Path("..."), allowed_topics={...})
        run_gate("security", root=Path("."))
        run_gate("ledger", csv_path=Path("..."))
    """
    dispatch = {
        "LLM-001": lambda: gate_table_quality(kwargs["jsonl_path"]),
        "LLM-002": lambda: gate_table_quality(kwargs["jsonl_path"]),
        "LLM-003": lambda: gate_deepseek_output(
            kwargs["jsonl_path"], kwargs.get("allowed_topics", set())
        ),
        # LLM-009/010 由 Tier-2 直接处理，Tier-1 无规则检查可跨过
        "LLM-009": lambda: _result(True, ["路过 Tier-1，直接进入 Tier-2 DeepSeek 审查"], escalate=False),
        "LLM-010": lambda: _result(True, ["路过 Tier-1，直接进入 Tier-2 DeepSeek 审查"], escalate=False),
        "ledger":   lambda: gate_evidence_ledger(kwargs["csv_path"]),
        "security": lambda: gate_security_scan(kwargs["root"]),
    }
    if task_id not in dispatch:
        return _result(False, [f"未知 task_id: {task_id}，无法自动验证"], escalate=True)
    return dispatch[task_id]()
