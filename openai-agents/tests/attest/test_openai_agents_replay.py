"""Replay: run the real OpenAI Agents SDK agent against the captured fixture with zero model calls.

`attest_replay("openai-agents")` serves the fixture's recorded model responses through a local
proxy and points OPENAI_BASE_URL and OTEL_EXPORTER_OTLP_TRACES_ENDPOINT at it. pyproject.toml
runs pytest with `--attest-replay=strict --attest-egress=block`, so a changed prompt, tool or
model fails with a replay-miss message and nothing can reach a provider.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from attest import OTelAdapter, expect
from attest.plugin import AttestEngineFixture
from attest.replay import ReplaySession
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from agent import run

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_openai_agents_replay_calls_lookup_order_once_per_order(
    attest: AttestEngineFixture,
    attest_replay: Callable[..., ReplaySession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # No provider key: the OpenAI client needs a value, replay never forwards it.
    monkeypatch.setenv("OPENAI_API_KEY", "sk-replay-dummy")
    exporter = InMemorySpanExporter()

    # fixtures_dir: attest_replay resolves fixtures from pytest's rootdir, which CI moves to the
    # repo root with --rootdir=.. .
    with attest_replay("openai-agents", fixtures_dir=FIXTURES_DIR):
        # The client and the exporter read the replay proxy's variables when run() builds them.
        answer = run(extra_exporters=[exporter])

    assert answer == "Order O-1 has shipped."
    trace = OTelAdapter.from_spans(exporter.get_finished_spans())
    attest.evaluate(
        expect(trace)
        .trajectory(["lookup_order"], mode="superset")
        .tool_cardinality("lookup_order", per="order_id", at_most=1)
    )
