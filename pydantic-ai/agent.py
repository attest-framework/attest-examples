"""An order-status agent built on Pydantic AI, traced through its native OpenTelemetry support.

There is no attest-specific adapter: `attest capture` sets OPENAI_BASE_URL (the recording proxy)
and OTEL_EXPORTER_OTLP_TRACES_ENDPOINT (the trace receiver), and this code reads both through
the standard clients.
"""

from __future__ import annotations

import os
from collections.abc import Sequence

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter
from pydantic_ai import Agent
from pydantic_ai.capabilities import Instrumentation
from pydantic_ai.models.instrumented import InstrumentationSettings
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

MODEL = "gpt-4.1"
QUESTION = "Where is order O-1?"


def run(question: str = QUESTION, extra_exporters: Sequence[SpanExporter] = ()) -> str:
    """Run the agent once and return its answer, exporting its spans before returning.

    `extra_exporters` receive the same spans as the OTLP exporter; tests use one to read the trace.
    """
    provider = TracerProvider()
    # The OTLP exporter reads OTEL_EXPORTER_OTLP_TRACES_ENDPOINT; without it, run() only exports
    # to `extra_exporters` instead of warning on the exporter's localhost:4318 default.
    if os.environ.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"):
        provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter()))
    for exporter in extra_exporters:
        provider.add_span_processor(SimpleSpanProcessor(exporter))
    try:
        settings = InstrumentationSettings(
            tracer_provider=provider, include_content=True, version=5
        )
        # OpenAIProvider reads OPENAI_BASE_URL and OPENAI_API_KEY.
        agent = Agent(
            OpenAIChatModel(MODEL, provider=OpenAIProvider()),
            name="order_agent",
            capabilities=[Instrumentation(settings)],
        )

        @agent.tool_plain
        def lookup_order(order_id: str) -> str:
            """Look up the current shipping status of an order."""
            return "shipped"

        return agent.run_sync(question).output
    finally:
        provider.force_flush()
        provider.shutdown()


if __name__ == "__main__":
    print(run())
