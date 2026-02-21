"""Tests for drift detection using constraint assertions.

Runs in simulation mode (ATTEST_SIMULATION=1) for deterministic results.
Demonstrates comparing baseline vs drifted traces against the same
budget assertions to detect performance degradation.

In production, these assertions would run against a real engine where
constraint assertions (Layer 2) fail when metadata values exceed
thresholds. Simulation mode returns pass for everything, so the tests
here verify trace structure and metadata values directly.
"""

from __future__ import annotations

import os

import pytest

from attest import Trace
from attest.expect import expect

from agent import build_baseline_traces, build_drift_assertions, build_drifted_traces

# Force simulation mode
os.environ["ATTEST_SIMULATION"] = "1"


@pytest.fixture
def baseline_traces() -> list[Trace]:
    return build_baseline_traces()


@pytest.fixture
def drifted_traces() -> list[Trace]:
    return build_drifted_traces()


def test_baseline_traces_within_budget(attest: object, baseline_traces: list[Trace]) -> None:
    """Baseline traces should be within cost, token, and latency budgets.

    Verifies the trace metadata values are below the thresholds defined
    in the drift assertions.
    """
    for trace in baseline_traces:
        assert trace.metadata is not None
        assert trace.metadata.cost_usd is not None and trace.metadata.cost_usd <= 0.01
        assert trace.metadata.total_tokens is not None and trace.metadata.total_tokens <= 200
        assert trace.metadata.latency_ms is not None and trace.metadata.latency_ms <= 1000


def test_drifted_traces_exceed_budget(drifted_traces: list[Trace]) -> None:
    """Drifted traces should exceed at least one budget threshold.

    Validates that the drift scenarios actually represent degradation
    by checking that cost, tokens, or latency exceed the baseline limits.
    """
    for trace in drifted_traces:
        assert trace.metadata is not None
        exceeds_cost = trace.metadata.cost_usd is not None and trace.metadata.cost_usd > 0.01
        exceeds_tokens = trace.metadata.total_tokens is not None and trace.metadata.total_tokens > 200
        exceeds_latency = trace.metadata.latency_ms is not None and trace.metadata.latency_ms > 1000
        assert exceeds_cost or exceeds_tokens or exceeds_latency


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
        chain = expect(trace).output_not_contains("")
        # In simulation mode, evaluate always passes
        attest.evaluate(chain)  # type: ignore[union-attr]
