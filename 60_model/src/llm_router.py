from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from openai import OpenAI


ROOT = Path(__file__).resolve().parents[2]
ROUTING_CSV = ROOT / "60_model" / "configs" / "llm_task_routing.csv"
ENV_FILE = ROOT / ".env"


@dataclass(frozen=True)
class LLMRoute:
    task_id: str
    task_name: str
    default_executor: str
    model: str
    output_status: str
    review_gate: str
    risk: str
    auto_gate_fn: str  # 对应 auto_gate.py 中的函数名，"(none)" 表示仍需 Codex


def load_routes(path: Path = ROUTING_CSV) -> dict[str, LLMRoute]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = csv.DictReader(f)
        return {
            row["task_id"]: LLMRoute(
                task_id=row["task_id"],
                task_name=row["task_name"],
                default_executor=row["default_executor"],
                model=row["model"],
                output_status=row["output_status"],
                review_gate=row["review_gate"],
                risk=row["risk"],
                auto_gate_fn=row.get("auto_gate_fn", "(none)"),
            )
            for row in rows
        }


def load_local_env(path: Path | None = None) -> None:
    if path is None:
        path = ENV_FILE
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def deepseek_client() -> OpenAI:
    load_local_env()
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set. Do not hard-code keys; set it in the environment.")
    try:
        timeout = float(os.environ.get("DEEPSEEK_TIMEOUT_SECONDS", "300"))
    except ValueError:
        timeout = 300.0
    return OpenAI(api_key=api_key, base_url="https://api.deepseek.com", timeout=timeout)


def route_for(task_id: str) -> LLMRoute:
    routes = load_routes()
    if task_id not in routes:
        raise KeyError(f"Unknown LLM task_id: {task_id}")
    return routes[task_id]


def run_deepseek_task(task_id: str, messages: Iterable[dict[str, str]], temperature: float = 0.1) -> str:
    route = route_for(task_id)
    if route.default_executor != "deepseek":
        raise RuntimeError(f"Task {task_id} is routed to {route.default_executor}, not DeepSeek.")
    if route.risk == "high":
        raise RuntimeError(f"Task {task_id} is high-risk and must not be delegated to DeepSeek.")
    client = deepseek_client()
    response = client.chat.completions.create(
        model=route.model or "deepseek-v4-pro",
        messages=list(messages),
        temperature=temperature,
    )
    content = response.choices[0].message.content
    return content or ""


def gate_before_task(task_id: str, **kwargs: object) -> dict[str, object]:
    """三层门控：Tier-1 本地 Python → Tier-2 DeepSeek 语义审查 → Tier-3 Codex。

    返回最终结果字典，调用方检查 ``escalate`` 字段：
    - ``escalate=False`` → 自动通过，继续执行
    - ``escalate=True``  → 需要 Codex 介入，结果含具体 issues

    示例::

        result = gate_before_task("LLM-002", jsonl_path=Path("..."))
        if result["escalate"]:
            raise RuntimeError(f"需要 Codex 介入: {result['issues']}")
    """
    route = route_for(task_id)
    if route.auto_gate_fn in ("", "(none)"):
        return {"passed": None, "issues": [], "escalate": False, "tier": 0}

    # --- Tier-1: 本地 Python 规则 ---
    from auto_gate import run_gate
    t1 = run_gate(task_id, **kwargs)

    # 不需要 Tier-2：明确通过 或 无对应处理器的明确失败
    needs_tier2 = t1.get("tier2_needed") or t1.get("escalate")
    if not needs_tier2:
        return t1  # 明确通过

    # --- Tier-2: DeepSeek 语义审查（仅当 review_gate 有对应处理器时）---
    _TIER2_MAP: dict[str, tuple[str, object]] = {
        "tier2_security_review": (
            "security",
            lambda t: {"hits": t.get("raw_hits") or t.get("issues", [])},
        ),
        "tier2_partial_review": (
            "partial",
            lambda t: {"tables": t.get("partial_records", [])},
        ),
        "evidence_auto_gate": (
            "evidence",
            lambda t: {"rows": t.get("review_rows") or kwargs.get("rows", [])},
        ),
    }

    review_gate = route.review_gate
    if review_gate not in _TIER2_MAP:
        # 没有 Tier-2 处理器，保持 Tier-1 结果（escalate 已置 True 则升 Codex）
        t1["tier"] = 3 if t1.get("escalate") else 1
        return t1

    review_type, kwarg_builder = _TIER2_MAP[review_gate]
    t2_kwargs = kwarg_builder(t1)  # type: ignore[operator]

    # 如果没有数据可供 Tier-2 审查，保留 Tier-1 结论
    if not any(v for v in t2_kwargs.values() if v):
        t1["tier"] = 3 if t1.get("escalate") else 1
        return t1

    from deepseek_review import run_tier2_review  # 延迟导入
    t2 = run_tier2_review(review_type, **t2_kwargs)  # type: ignore[arg-type]
    return t2  # escalate=True → Tier-3 Codex；否则 Tier-2 已解决
