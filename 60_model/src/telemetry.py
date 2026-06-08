from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExportResult, SpanExporter


ROOT = Path(__file__).resolve().parents[2]
TRACE_DIR = ROOT / "40_quality_evidence" / "otel_traces"
TRACE_FILE = TRACE_DIR / f"simulation_ai_spans_{datetime.now():%Y%m%d}.jsonl"
SERVICE_NAME = "park-simulation-decision-system"

_READY = False


def _safe_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_safe_value(item) for item in value[:20]]
    if isinstance(value, dict):
        return {str(key): _safe_value(item) for key, item in list(value.items())[:40]}
    return str(value)


class JsonlSpanExporter(SpanExporter):
    def export(self, spans: list[ReadableSpan]) -> SpanExportResult:
        TRACE_DIR.mkdir(parents=True, exist_ok=True)
        with TRACE_FILE.open("a", encoding="utf-8") as f:
            for span in spans:
                ctx = span.get_span_context()
                parent = span.parent
                payload = {
                    "name": span.name,
                    "trace_id": f"{ctx.trace_id:032x}",
                    "span_id": f"{ctx.span_id:016x}",
                    "parent_span_id": f"{parent.span_id:016x}" if parent else "",
                    "start_time_unix_nano": span.start_time,
                    "end_time_unix_nano": span.end_time,
                    "status": span.status.status_code.name,
                    "attributes": {key: _safe_value(value) for key, value in span.attributes.items()},
                    "events": [
                        {
                            "name": event.name,
                            "timestamp": event.timestamp,
                            "attributes": {key: _safe_value(value) for key, value in event.attributes.items()},
                        }
                        for event in span.events
                    ],
                }
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        return None


def setup_tracing() -> None:
    global _READY
    if _READY:
        return
    provider = TracerProvider(resource=Resource.create({"service.name": SERVICE_NAME}))
    provider.add_span_processor(SimpleSpanProcessor(JsonlSpanExporter()))
    try:
        trace.set_tracer_provider(provider)
    except Exception:
        # Another runtime may have already configured tracing. Keep using it.
        pass
    _READY = True


def get_tracer() -> trace.Tracer:
    setup_tracing()
    return trace.get_tracer(SERVICE_NAME)


@contextmanager
def start_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[trace.Span]:
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        for key, value in (attributes or {}).items():
            span.set_attribute(key, _safe_value(value))
        yield span


def span_trace_id(span: trace.Span) -> str:
    ctx = span.get_span_context()
    if not ctx or not ctx.trace_id:
        return ""
    return f"{ctx.trace_id:032x}"


def trace_file_path() -> str:
    return str(TRACE_FILE.relative_to(ROOT)).replace("\\", "/")
