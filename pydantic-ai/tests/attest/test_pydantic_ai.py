"""Contracts drafted by `attest capture` from fixture "pydantic-ai".

Review and edit before committing: they check the captured trace without running
the agent. Re-capturing does not overwrite this file.
"""

from __future__ import annotations

from pathlib import Path

from attest import ExpectChain, expect, load_fixture
from attest.plugin import AttestEngineFixture

FIXTURE = load_fixture(Path(__file__).parent / "fixtures/pydantic-ai.attest.json")


def contracts() -> ExpectChain:
    return (
        expect(FIXTURE.trace)
        # tools-called: calls lookup_order
        .trajectory(["lookup_order"], mode="superset")
        # cardinality-lookup_order-per-order_id: lookup_order at most once per order_id
        .tool_cardinality("lookup_order", per="order_id", at_most=1)
    )


def test_pydantic_ai_contracts_hold(attest: AttestEngineFixture) -> None:
    attest.evaluate(contracts())
