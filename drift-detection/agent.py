"""Drift detection helpers — baseline vs drifted trace builders.

Demonstrates how to construct two sets of traces representing normal
agent behavior and degraded (drifted) behavior, then evaluate both
against the same assertions to detect drift.
"""

from __future__ import annotations

from attest import Assertion, ManualAdapter, Trace

AGENT_ID = "qa-agent"


def build_baseline_traces() -> list[Trace]:
    """Build traces representing normal (baseline) agent behavior."""
    adapter = ManualAdapter(agent_id=AGENT_ID)
    traces: list[Trace] = []

    scenarios = [
        ("What is Python?", "Python is a programming language.", 50, 0.002, 300),
        ("Explain REST APIs", "REST APIs use HTTP methods.", 80, 0.003, 450),
        ("What is Docker?", "Docker is a containerization platform.", 60, 0.002, 350),
    ]

    for question, answer, tokens, cost, latency in scenarios:
        def build(b: object, q: str = question, a: str = answer, t: int = tokens, c: float = cost, la: int = latency) -> None:
            b.set_input(message=q)  # type: ignore[union-attr]
            b.add_llm_call(  # type: ignore[union-attr]
                name="gpt-4.1-mini",
                args={"model": "gpt-4.1-mini"},
                result={"completion": a, "total_tokens": t},
            )
            b.set_output(message=a)  # type: ignore[union-attr]
            b.set_metadata(total_tokens=t, cost_usd=c, latency_ms=la)  # type: ignore[union-attr]

        traces.append(adapter.capture(build))

    return traces


def build_drifted_traces() -> list[Trace]:
    """Build traces showing drift — higher cost, more tokens, slower."""
    adapter = ManualAdapter(agent_id=AGENT_ID)
    traces: list[Trace] = []

    scenarios = [
        ("What is Python?", "Python is a high-level interpreted programming language with dynamic typing...", 500, 0.02, 3000),
        ("Explain REST APIs", "Representational State Transfer APIs are an architectural style...", 800, 0.035, 5000),
        ("What is Docker?", "Docker is an open-source containerization platform that enables...", 600, 0.025, 4000),
    ]

    for question, answer, tokens, cost, latency in scenarios:
        def build(b: object, q: str = question, a: str = answer, t: int = tokens, c: float = cost, la: int = latency) -> None:
            b.set_input(message=q)  # type: ignore[union-attr]
            b.add_llm_call(  # type: ignore[union-attr]
                name="gpt-4.1",
                args={"model": "gpt-4.1"},
                result={"completion": a, "total_tokens": t},
            )
            b.set_output(message=a)  # type: ignore[union-attr]
            b.set_metadata(total_tokens=t, cost_usd=c, latency_ms=la)  # type: ignore[union-attr]

        traces.append(adapter.capture(build))

    return traces


def build_drift_assertions() -> list[Assertion]:
    """Assertions that catch drift: cost, token, and latency budgets."""
    return [
        Assertion(
            assertion_id="cost-budget",
            type="constraint",
            spec={"field": "metadata.cost_usd", "operator": "lte", "value": 0.01},
        ),
        Assertion(
            assertion_id="token-budget",
            type="constraint",
            spec={"field": "metadata.total_tokens", "operator": "lte", "value": 200},
        ),
        Assertion(
            assertion_id="latency-sla",
            type="constraint",
            spec={"field": "metadata.latency_ms", "operator": "lte", "value": 1000},
        ),
    ]
