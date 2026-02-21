"""Continuous evaluation helpers — trace builders and runner setup.

Demonstrates ContinuousEvalRunner: sampling, background evaluation,
and queue-based trace submission. All traces are manually constructed
to keep the example self-contained (no external API calls).
"""

from __future__ import annotations

from attest import Assertion, ManualAdapter, Trace
from attest.client import AttestClient
from attest.continuous import ContinuousEvalRunner

AGENT_ID = "qa-agent"

SCENARIOS: list[tuple[str, str, int, float]] = [
    ("What is 2+2?", "4", 10, 0.001),
    ("Explain quantum computing", "Quantum computing uses qubits to represent states.", 500, 0.05),
    ("Translate hello to French", "Bonjour", 25, 0.002),
    ("Write a haiku about AI", "Silicon dreams flow\nThrough circuits of endless thought\nMachines learn to feel", 80, 0.008),
    ("Summarize the news", "Today's headlines include economic growth and tech advances.", 200, 0.02),
]


def build_traces() -> list[Trace]:
    """Build sample traces with varying token counts and costs."""
    adapter = ManualAdapter(agent_id=AGENT_ID)
    traces: list[Trace] = []

    for question, answer, tokens, cost in SCENARIOS:
        def build(b: object, q: str = question, a: str = answer, t: int = tokens, c: float = cost) -> None:
            b.set_input(message=q)  # type: ignore[union-attr]
            b.add_llm_call(  # type: ignore[union-attr]
                name="gpt-4.1",
                args={"model": "gpt-4.1"},
                result={"completion": a, "total_tokens": t},
            )
            b.set_output(message=a)  # type: ignore[union-attr]
            b.set_metadata(total_tokens=t, cost_usd=c)  # type: ignore[union-attr]

        traces.append(adapter.capture(build))

    return traces


def build_assertions() -> list[Assertion]:
    """Define assertions for continuous evaluation."""
    return [
        Assertion(
            assertion_id="cost-check",
            type="constraint",
            spec={"field": "metadata.cost_usd", "operator": "lte", "value": 0.10},
        ),
        Assertion(
            assertion_id="output-check",
            type="content",
            spec={"check": "non_empty"},
        ),
    ]


def create_runner(client: AttestClient, sample_rate: float = 1.0) -> ContinuousEvalRunner:
    """Create a ContinuousEvalRunner with standard assertions."""
    return ContinuousEvalRunner(
        client=client,
        assertions=build_assertions(),
        sample_rate=sample_rate,
    )
