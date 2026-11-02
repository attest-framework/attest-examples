"""Tests for drift detection using constraint assertions.

Demonstrates comparing baseline vs drifted traces against the same
budget assertions (Layer 2) to detect performance degradation. The
engine evaluates both sets through a direct client, so the drift it
catches in the drifted traces does not appear as hard failures in the
Attest report: every baseline assertion passes, and every drifted trace
fails at least one budget.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from attest import Trace
from attest.client import AttestClient
from attest.engine_manager import EngineManager
from attest.expect import expect

from agent import build_baseline_traces, build_drift_assertions, build_drifted_traces


@pytest.fixture
def baseline_traces() -> list[Trace]:
    return build_baseline_traces()


@pytest.fixture
def drifted_traces() -> list[Trace]:
    return build_drifted_traces()


@pytest.fixture
async def client() -> AsyncIterator[AttestClient]:
    async with EngineManager() as engine:
        yield AttestClient(engine)


async def test_baseline_traces_within_budget(
    client: AttestClient, baseline_traces: list[Trace]
) -> None:
    """Every baseline trace passes the cost, token, and latency budgets."""
    for trace in baseline_traces:
        result = await client.evaluate_batch(trace, build_drift_assertions())
        assert [r.status for r in result.results] == ["pass"] * len(result.results)


async def test_drifted_traces_exceed_budget(
    client: AttestClient, drifted_traces: list[Trace]
) -> None:
    """The engine flags every drifted trace on at least one budget."""
    for trace in drifted_traces:
        result = await client.evaluate_batch(trace, build_drift_assertions())
        failed = [r.assertion_id for r in result.results if r.status == "hard_fail"]
        assert failed, f"no budget caught drift in trace {trace.trace_id}"


def test_drift_detection_comparison(baseline_traces: list[Trace], drifted_traces: list[Trace]) -> None:
    """Compare aggregate metrics between baseline and drifted traces.

    Verifies that drifted traces show measurable degradation across
    all three dimensions: cost, tokens, and latency.
    """
    def avg_metric(traces: list[Trace], field: str) -> float:
        values = [getattr(t.metadata, field) for t in traces if t.metadata and getattr(t.metadata, field) is not None]
        return sum(values) / len(values) if values else 0.0

    for field in ("cost_usd", "total_tokens", "latency_ms"):
        baseline_avg = avg_metric(baseline_traces, field)
        drifted_avg = avg_metric(drifted_traces, field)
        assert drifted_avg > baseline_avg, f"Expected drift in {field}: {drifted_avg} <= {baseline_avg}"


def test_baseline_output_not_empty(attest: object, baseline_traces: list[Trace]) -> None:
    """Each baseline trace should have non-empty output."""
    for trace in baseline_traces:
        chain = expect(trace).output_matches_regex(r"\S")
        attest.evaluate(chain)  # type: ignore[union-attr]
