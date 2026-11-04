"""An order-status agent built on LangGraph, traced through LangSmith's OpenTelemetry mode.

There is no attest-specific adapter: `attest capture` sets OPENAI_BASE_URL (the recording proxy)
and OTEL_EXPORTER_OTLP_TRACES_ENDPOINT (the trace receiver), and this code reads both through
the standard clients. LangSmith runs in OTel mode with a tracer provider this module owns, so
spans go only to that provider's exporters. The LangSmith key is a placeholder that is never used
and nothing is sent to LangSmith's hosted service.
"""

from __future__ import annotations

import os
import warnings
from collections.abc import Sequence

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langsmith import Client, tracing_context
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter

MODEL = "gpt-4.1"
QUESTION = "Where is order O-1?"


@tool
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
    # OTel mode with our own provider: no run is posted to LangSmith; the key is only a placeholder.
    client = Client(
        api_key="unused", tracing_mode="otel", otel_tracer_provider=provider
    )
    try:
        # ChatOpenAI reads OPENAI_BASE_URL and OPENAI_API_KEY.
        with warnings.catch_warnings():
            # create_react_agent is deprecated upstream; the capture route is the same for its replacement.
            warnings.simplefilter("ignore", DeprecationWarning)
            graph = create_react_agent(ChatOpenAI(model=MODEL), [lookup_order])
        with tracing_context(enabled=True, client=client):
            result = graph.invoke({"messages": [("user", question)]})
        return str(result["messages"][-1].content)
    finally:
        client.flush()
        provider.force_flush()
        provider.shutdown()


if __name__ == "__main__":
    print(run())
