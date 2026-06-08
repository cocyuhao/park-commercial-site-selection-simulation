from __future__ import annotations

import csv
import hashlib
import json
import os
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError


ROOT = Path(__file__).resolve().parents[2]
ROUTING_CSV = ROOT / "60_model" / "configs" / "llm_task_routing.csv"
ENV_FILE = ROOT / ".env"
LLM_RUN_DIR = ROOT / "60_model" / "llm_runs"
DEEPSEEK_CACHE_DIR = LLM_RUN_DIR / "cache" / "deepseek"
DEEPSEEK_ORCHESTRATION_DIR = LLM_RUN_DIR / "deepseek_orchestration"
PER_VISITOR_CALL_KEYS = {"per_visitor", "per_agent", "per_virtual_visitor", "visitor_loop"}
_DEEPSEEK_SEMAPHORE: threading.BoundedSemaphore | None = None
_DEEPSEEK_SEMAPHORE_LIMIT = 0


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
    env_aliases = {
        "OPENAI_API_KEY": "DEEPSEEK_API_KEY",
        "OPENAI_API_BASE": "DEEPSEEK_API_BASE",
        "LLM_MODEL": "DEEPSEEK_MODEL",
        "AMAP_API_KEY": "AMAP_WEB_SERVICE_KEY",
    }
    for source_key, target_key in env_aliases.items():
        if source_key in os.environ and target_key not in os.environ:
            os.environ[target_key] = os.environ[source_key]


def deepseek_client() -> OpenAI:
    load_local_env()
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set. Do not hard-code keys; set it in the environment.")
    try:
        timeout = float(os.environ.get("DEEPSEEK_TIMEOUT_SECONDS", "300"))
    except ValueError:
        timeout = 300.0
    base_url = os.environ.get("DEEPSEEK_API_BASE", "https://api.deepseek.com")
    return OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today_log_path() -> Path:
    return DEEPSEEK_ORCHESTRATION_DIR / f"deepseek_call_log_{datetime.now(timezone.utc):%Y%m%d}.jsonl"


def _local_concurrency_semaphore() -> tuple[threading.BoundedSemaphore, int]:
    """Small in-process concurrency gate for runtime dashboard calls.

    DeepSeek's official limit is account-level, so this is not a replacement for
    provider-side capacity expansion. It prevents the local app from launching
    too many simultaneous calls while larger batch jobs should still use explicit
    batching and caching.
    """
    global _DEEPSEEK_SEMAPHORE, _DEEPSEEK_SEMAPHORE_LIMIT
    load_local_env()
    try:
        limit = int(os.environ.get("DEEPSEEK_LOCAL_MAX_CONCURRENT", "4"))
    except ValueError:
        limit = 4
    limit = max(1, min(limit, 64))
    if _DEEPSEEK_SEMAPHORE is None or _DEEPSEEK_SEMAPHORE_LIMIT != limit:
        _DEEPSEEK_SEMAPHORE = threading.BoundedSemaphore(limit)
        _DEEPSEEK_SEMAPHORE_LIMIT = limit
    return _DEEPSEEK_SEMAPHORE, limit


def _write_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def _message_stats(messages: list[dict[str, str]]) -> dict[str, int]:
    chars = sum(len(str(item.get("content", ""))) for item in messages)
    return {"message_count": len(messages), "input_chars": chars}


def fingerprint_deepseek_request(
    task_id: str,
    messages: Iterable[dict[str, str]],
    *,
    temperature: float,
    model: str,
) -> str:
    """Stable request fingerprint used for local cache and audit logs.

    The cache key is based on task/model/messages only; no API key or local
    credential is ever included.
    """
    body = {
        "task_id": task_id,
        "model": model,
        "temperature": temperature,
        "messages": list(messages),
    }
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _cache_file(cache_key: str) -> Path:
    return DEEPSEEK_CACHE_DIR / f"{cache_key}.json"


def should_cache_deepseek_task(route: LLMRoute, allow_cache: bool | None) -> bool:
    if os.environ.get("DEEPSEEK_DISABLE_CACHE") == "1":
        return False
    if allow_cache is not None:
        return allow_cache
    # Runtime chat is context-sensitive and should not silently reuse answers.
    if route.task_id == "LLM-026":
        return False
    return route.default_executor == "deepseek" and route.risk in {"low", "medium"}


def validate_deepseek_call_context(route: LLMRoute, metadata: dict[str, Any] | None = None) -> None:
    """Block dangerous DeepSeek usage before any network call is made."""
    meta = metadata or {}
    granularity = str(meta.get("call_granularity") or meta.get("object_kind") or "").strip().lower()
    if granularity in PER_VISITOR_CALL_KEYS:
        raise RuntimeError(
            "DeepSeek must not be called per virtual visitor/agent. "
            "Use local simulation plus cached batch behavior programs."
        )
    try:
        object_count = int(meta.get("object_count", 0) or 0)
    except (TypeError, ValueError):
        object_count = 0
    if object_count > 10000 and route.task_id != "LLM-002":
        raise RuntimeError(
            f"DeepSeek task {route.task_id} received object_count={object_count}; "
            "batch or summarize inputs before calling the model."
        )


def _classify_deepseek_error(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, RateLimitError):
        return {"error_kind": "rate_limit_429", "http_status": 429, "retryable": True}
    if isinstance(exc, APITimeoutError):
        return {"error_kind": "timeout", "http_status": "", "retryable": True}
    if isinstance(exc, APIConnectionError):
        return {"error_kind": "connection", "http_status": "", "retryable": True}
    if isinstance(exc, APIStatusError):
        status_code = getattr(exc, "status_code", "")
        return {
            "error_kind": f"http_{status_code}",
            "http_status": status_code,
            "retryable": status_code == 429 or int(status_code or 0) >= 500,
        }
    return {"error_kind": type(exc).__name__, "http_status": "", "retryable": False}


@contextmanager
def _trace_span(name: str, attributes: dict[str, Any]) -> Iterator[tuple[Any, str, str]]:
    try:
        from telemetry import span_trace_id, start_span, trace_file_path

        with start_span(name, attributes) as span:
            yield span, span_trace_id(span), trace_file_path()
    except Exception:
        yield None, "", ""


def route_for(task_id: str) -> LLMRoute:
    routes = load_routes()
    if task_id not in routes:
        raise KeyError(f"Unknown LLM task_id: {task_id}")
    return routes[task_id]


def run_deepseek_task(
    task_id: str,
    messages: Iterable[dict[str, str]],
    temperature: float = 0.1,
    *,
    metadata: dict[str, Any] | None = None,
    allow_cache: bool | None = None,
    max_retries: int | None = None,
) -> str:
    route = route_for(task_id)
    if route.default_executor != "deepseek":
        raise RuntimeError(f"Task {task_id} is routed to {route.default_executor}, not DeepSeek.")
    if route.risk == "high":
        raise RuntimeError(f"Task {task_id} is high-risk and must not be delegated to DeepSeek.")
    metadata = dict(metadata or {})
    validate_deepseek_call_context(route, metadata)
    messages_list = list(messages)
    model = os.environ.get("DEEPSEEK_MODEL") or route.model or "deepseek-v4-pro"
    cache_key = fingerprint_deepseek_request(task_id, messages_list, temperature=temperature, model=model)
    stats = _message_stats(messages_list)
    use_cache = should_cache_deepseek_task(route, allow_cache)
    cache_file = _cache_file(cache_key)
    log_base = {
        "run_at": _utc_now(),
        "task_id": task_id,
        "task_name": route.task_name,
        "risk": route.risk,
        "model": model,
        "temperature": temperature,
        "expected_output_status": route.output_status,
        "cache_key": cache_key,
        "cache_enabled": use_cache,
        "metadata": {
            key: value
            for key, value in metadata.items()
            if key in {"call_granularity", "object_kind", "object_count", "project_id", "session_id", "node_id"}
        },
        **stats,
    }
    if use_cache and cache_file.exists():
        cached = json.loads(cache_file.read_text(encoding="utf-8"))
        _write_jsonl(_today_log_path(), {**log_base, "status": "cache_hit", "content_chars": len(cached.get("content", ""))})
        return str(cached.get("content", ""))

    client = deepseek_client()
    retries = max_retries
    if retries is None:
        try:
            retries = int(os.environ.get("DEEPSEEK_MAX_RETRIES", "2"))
        except ValueError:
            retries = 2
    delay = float(os.environ.get("DEEPSEEK_RETRY_BASE_SECONDS", "1.5"))
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        semaphore, local_concurrency_limit = _local_concurrency_semaphore()
        queued_at = time.perf_counter()
        semaphore.acquire()
        queue_wait_ms = int((time.perf_counter() - queued_at) * 1000)
        with _trace_span(
            "deepseek.chat.completions",
            {
                "llm.task_id": task_id,
                "llm.model": model,
                "llm.risk": route.risk,
                "llm.cache_enabled": use_cache,
                "llm.message_count": stats["message_count"],
                "llm.input_chars": stats["input_chars"],
                "llm.attempt": attempt,
                "llm.local_concurrency_limit": local_concurrency_limit,
                "llm.queue_wait_ms": queue_wait_ms,
            },
        ) as (span, trace_id, trace_file):
            started = time.perf_counter()
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages_list,
                    temperature=temperature,
                )
                content = response.choices[0].message.content or ""
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                if use_cache:
                    cache_file.parent.mkdir(parents=True, exist_ok=True)
                    cache_payload = {
                        "created_at": _utc_now(),
                        "task_id": task_id,
                        "model": model,
                        "temperature": temperature,
                        "cache_key": cache_key,
                        "content": content,
                        "output_status": route.output_status,
                    }
                    cache_file.write_text(json.dumps(cache_payload, ensure_ascii=False, indent=2), encoding="utf-8")
                _write_jsonl(
                    _today_log_path(),
                    {
                        **log_base,
                        "status": "ok",
                        "attempt": attempt,
                        "queue_wait_ms": queue_wait_ms,
                        "local_concurrency_limit": local_concurrency_limit,
                        "elapsed_ms": elapsed_ms,
                        "content_chars": len(content),
                        "trace_id": trace_id,
                        "trace_file": trace_file,
                    },
                )
                return content
            except Exception as exc:  # noqa: BLE001 - exact provider errors are normalized below
                last_error = exc
                error = _classify_deepseek_error(exc)
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                if span is not None:
                    try:
                        span.add_event("deepseek_error", error)
                    except Exception:
                        pass
                _write_jsonl(
                    _today_log_path(),
                    {
                        **log_base,
                        "status": "error",
                        "attempt": attempt,
                        "queue_wait_ms": queue_wait_ms,
                        "local_concurrency_limit": local_concurrency_limit,
                        "elapsed_ms": elapsed_ms,
                        "trace_id": trace_id,
                        "trace_file": trace_file,
                        "error_kind": error["error_kind"],
                        "http_status": error["http_status"],
                        "retryable": error["retryable"],
                    },
                )
                if not error["retryable"] or attempt >= retries:
                    break
                time.sleep(delay * (2 ** attempt))
            finally:
                semaphore.release()
    assert last_error is not None
    raise last_error


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
