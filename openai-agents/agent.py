"""An order-status agent built on the OpenAI Agents SDK, traced through OpenTelemetry.

There is no attest-specific adapter: `attest capture` sets OPENAI_BASE_URL (the recording proxy)
and OTEL_EXPORTER_OTLP_TRACES_ENDPOINT (the trace receiver), and this code reads both through
the standard clients. Spans come from the OpenTelemetry project's
`opentelemetry-instrumentation-openai-agents-v2` (alpha).
"""

from __future__ import annotations

import os
from collections.abc import Sequence

from agents import Agent, Runner, function_tool, set_trace_processors
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.openai_agents import OpenAIAgentsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter

MODEL = "gpt-4.1"
QUESTION = "Where is order O-1?"


@function_tool
def lookup_order(order_id: str) -> str:
    """Look up the current shipping status of an order."""
    return "shipped"


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
    # Drop the SDK's hosted trace exporter so nothing is sent to OpenAI's tracing endpoint.
    set_trace_processors([])
    instrumentor = OpenAIAgentsInstrumentor()
    instrumentor.instrument(tracer_provider=provider, capture_message_content=True)
    try:
        # The default client reads OPENAI_BASE_URL and OPENAI_API_KEY; the SDK uses the Responses API.
        agent = Agent(name="Order desk", model=MODEL, tools=[lookup_order])
        result = Runner.run_sync(agent, question)
        return str(result.final_output)
    finally:
        instrumentor.uninstrument()
        provider.force_flush()
        provider.shutdown()


if __name__ == "__main__":
    print(run())
