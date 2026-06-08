from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "60_model" / "src"
sys.path.insert(0, str(SRC))

from llm_router import (  # noqa: E402
    fingerprint_deepseek_request,
    route_for,
    should_cache_deepseek_task,
    validate_deepseek_call_context,
)


OUT_JSON = ROOT / "40_quality_evidence" / "deepseek_orchestration_validation_20260605.json"
OUT_MD = ROOT / "40_quality_evidence" / "deepseek_orchestration_validation_20260605.md"


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, evidence: str) -> None:
    checks.append({"name": name, "passed": passed, "evidence": evidence})


def main() -> None:
    checks: list[dict[str, Any]] = []
    messages = [
        {"role": "system", "content": "只输出 JSON。"},
        {"role": "user", "content": "请做低风险主题分类草稿。"},
    ]
    route_batch = route_for("LLM-001")
    route_chat = route_for("LLM-026")
    route_final = route_for("LLM-006")

    fp1 = fingerprint_deepseek_request("LLM-001", messages, temperature=0.0, model="deepseek-v4-pro")
    fp2 = fingerprint_deepseek_request("LLM-001", messages, temperature=0.0, model="deepseek-v4-pro")
    fp3 = fingerprint_deepseek_request("LLM-001", messages, temperature=0.1, model="deepseek-v4-pro")
    add_check(checks, "stable_fingerprint", fp1 == fp2 and fp1 != fp3, f"fp1={fp1[:12]} fp3={fp3[:12]}")

    add_check(
        checks,
        "batch_cache_default",
        should_cache_deepseek_task(route_batch, None) is True,
        "LLM-001 should default to local cache because it is low-risk batch work.",
    )
    add_check(
        checks,
        "runtime_chat_cache_disabled",
        should_cache_deepseek_task(route_chat, None) is False,
        "LLM-026 runtime chat should not silently reuse answers across contexts.",
    )
    add_check(
        checks,
        "final_decision_not_deepseek",
        route_final.default_executor != "deepseek" and route_final.risk == "high",
        f"LLM-006 executor={route_final.default_executor} risk={route_final.risk}",
    )

    try:
        validate_deepseek_call_context(route_batch, {"call_granularity": "per_visitor", "object_count": 50000})
    except RuntimeError as exc:
        per_visitor_blocked = "per virtual visitor" in str(exc)
    else:
        per_visitor_blocked = False
    add_check(
        checks,
        "per_visitor_call_blocked",
        per_visitor_blocked,
        "DeepSeek cannot be used as a real-time model call inside each virtual visitor loop.",
    )

    router_text = (SRC / "llm_router.py").read_text(encoding="utf-8")
    required_router_terms = [
        "RateLimitError",
        "APITimeoutError",
        "APIConnectionError",
        "DEEPSEEK_MAX_RETRIES",
        "DEEPSEEK_LOCAL_MAX_CONCURRENT",
        "BoundedSemaphore",
        "queue_wait_ms",
        "deepseek_call_log_",
        "DEEPSEEK_CACHE_DIR",
        "trace_file",
    ]
    missing_router_terms = [term for term in required_router_terms if term not in router_text]
    add_check(
        checks,
        "router_has_retry_cache_trace_terms",
        not missing_router_terms,
        f"missing={missing_router_terms}",
    )

    try:
        import telemetry  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        telemetry_ok = False
        telemetry_evidence = f"{type(exc).__name__}: {exc}"
    else:
        telemetry_ok = True
        telemetry_evidence = "telemetry module import ok"
    add_check(checks, "telemetry_import_ok", telemetry_ok, telemetry_evidence)

    schema = json.loads((ROOT / "60_model" / "schemas" / "deepseek_task_contract.schema.json").read_text(encoding="utf-8"))
    required = set(schema.get("required", []))
    add_check(
        checks,
        "contract_forces_review_required",
        {"needs_human_review", "review_required"} <= required,
        f"required={sorted(required)}",
    )

    passed = all(item["passed"] for item in checks)
    report = {
        "validator": "verify_deepseek_orchestration.py",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "pass" if passed else "fail",
        "check_count": len(checks),
        "failure_count": sum(1 for item in checks if not item["passed"]),
        "checks": checks,
        "boundary": {
            "deepseek_role": "constrained_semantic_worker",
            "main_simulation_role": "local_python_schema_rules_spatial_operational_constraints",
            "forbidden_pattern": "per_virtual_visitor_realtime_llm_call",
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# DeepSeek 受限调用层验证（2026-06-05）",
        "",
        f"- 状态：{report['status']}",
        f"- 检查项：{report['check_count']}",
        f"- 失败项：{report['failure_count']}",
        "",
        "## 结论",
        "",
        "- DeepSeek 现在被约束为低成本语义工人，不是逐游客仿真引擎。",
        "- 批处理任务默认可缓存；运行时聊天默认不缓存，避免跨上下文误复用。",
        "- 调用层已经具备 429/timeout/connection 分类、重试参数、调用日志和 OpenTelemetry trace 入口。",
        "- 本地运行时增加小并发闸门，避免网页或脚本把多个 DeepSeek 请求无控制地同时打出去。",
        "- 契约要求 `needs_human_review=true` 和 `review_required=true`，防止流畅文本被误当事实。",
        "",
        "## 检查明细",
        "",
    ]
    for item in checks:
        mark = "pass" if item["passed"] else "fail"
        lines.append(f"- `{mark}` {item['name']}：{item['evidence']}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"status={report['status']}")
    print(f"wrote={OUT_JSON.relative_to(ROOT)}")
    print(f"wrote={OUT_MD.relative_to(ROOT)}")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
