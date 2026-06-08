from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "90_p6_expert_dashboard"
OUT_JSON = ROOT / "40_quality_evidence" / "otel_fastapi_trace_probe_20260605.json"

sys.path.insert(0, str(APP_DIR))
import app  # noqa: E402


def check(name: str, passed: bool, evidence: Any) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence}


def main() -> None:
    exporter = InMemorySpanExporter()
    provider = TracerProvider(resource=Resource.create({"service.name": "p6-expert-dashboard-qa"}))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app.app, tracer_provider=provider)
    HTTPXClientInstrumentor().instrument(tracer_provider=provider)

    client = TestClient(app.app)
    endpoints = ["/api/dashboard", "/api/object-chain", "/api/ai/sessions"]
    responses = {endpoint: client.get(endpoint).status_code for endpoint in endpoints}
    spans = exporter.get_finished_spans()
    span_records = [
        {
            "name": span.name,
            "status": span.status.status_code.name,
            "attributes": {
                key: value
                for key, value in dict(span.attributes or {}).items()
                if key in {"http.route", "http.request.method", "url.path", "http.response.status_code"}
            },
        }
        for span in spans
    ]
    span_text = json.dumps(span_records, ensure_ascii=False)
    checks = [
        check("all_endpoints_http_200", all(status == 200 for status in responses.values()), responses),
        check("spans_generated", len(spans) >= len(endpoints), len(spans)),
        check("dashboard_span_present", "/api/dashboard" in span_text, span_records[:8]),
        check("object_chain_span_present", "/api/object-chain" in span_text, span_records[:8]),
        check("ai_sessions_span_present", "/api/ai/sessions" in span_text, span_records[:8]),
        check("no_error_spans", not any(record["status"] == "ERROR" for record in span_records), [record for record in span_records if record["status"] == "ERROR"]),
    ]
    status = "pass" if all(item["passed"] for item in checks) else "fail"
    report = {
        "validator": "otel_fastapi_trace_probe_20260605.py",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": status,
        "check_count": len(checks),
        "failure_count": sum(1 for item in checks if not item["passed"]),
        "responses": responses,
        "span_count": len(spans),
        "spans": span_records[:40],
        "checks": checks,
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"status={status}")
    print(f"span_count={len(spans)}")
    print(f"wrote={OUT_JSON.relative_to(ROOT)}")
    if status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
