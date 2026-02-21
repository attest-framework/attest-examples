"""Tests for continuous evaluation using ContinuousEvalRunner.

Runs in simulation mode (ATTEST_SIMULATION=1) so no engine binary
or API keys are needed. Demonstrates queue-based background evaluation,
sampling, and direct trace evaluation.
"""

from __future__ import annotations

import os
from typing import Any

import pytest

from attest import Assertion, Trace
from attest.client import AttestClient
from attest.continuous import ContinuousEvalRunner, Sampler
from attest.engine_manager import EngineManager

from agent import build_assertions, build_traces, create_runner

# Force simulation mode — deterministic pass results, no engine needed
os.environ["ATTEST_SIMULATION"] = "1"


@pytest.fixture
def traces() -> list[Trace]:
    return build_traces()


@pytest.fixture
def assertions() -> list[Assertion]:
    return build_assertions()


@pytest.fixture
def client() -> AttestClient:
    engine = EngineManager(engine_path="/dev/null")
    return AttestClient(engine)


@pytest.mark.asyncio
async def test_direct_evaluation(client: AttestClient, traces: list[Trace], assertions: list[Assertion]) -> None:
    """Evaluate traces directly via client.evaluate_batch in simulation mode.

    Verifies each trace produces passing results for all assertions.
    """
    for trace in traces:
        result = await client.evaluate_batch(trace, assertions)
        assert len(result.results) == len(assertions)
        for r in result.results:
            assert r.status == "pass"
        assert result.total_cost == 0.0


@pytest.mark.asyncio
async def test_runner_submit_and_drain(client: AttestClient, traces: list[Trace]) -> None:
    """Submit traces to ContinuousEvalRunner and verify the queue drains.

    The runner processes submitted traces in a background task.
    After stopping, the queue should be empty.
    """
    runner = create_runner(client, sample_rate=1.0)
    await runner.start()

    for trace in traces:
        await runner.submit(trace)

    # Wait for queue to drain before stopping
    await runner._queue.join()
    await runner.stop()


@pytest.mark.asyncio
async def test_runner_evaluate_trace(client: AttestClient, traces: list[Trace]) -> None:
    """Test evaluate_trace returns results when sampled at 100%."""
    runner = create_runner(client, sample_rate=1.0)
    result = await runner.evaluate_trace(traces[0])
    assert result is not None
    assert len(result.results) == 2
    assert all(r.status == "pass" for r in result.results)


def test_sampler_zero_rate() -> None:
    """Sampler with rate=0.0 never samples."""
    sampler = Sampler(0.0)
    results = [sampler.should_sample() for _ in range(100)]
    assert not any(results)


def test_sampler_full_rate() -> None:
    """Sampler with rate=1.0 always samples."""
    sampler = Sampler(1.0)
    results = [sampler.should_sample() for _ in range(100)]
    assert all(results)
