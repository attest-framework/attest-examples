"""Relational checks use committed world state, not tool arguments or a model judge."""
from pathlib import Path

import pytest
from attest import expect, related

from agent import refund_order


@pytest.mark.parametrize("order_id", ["O-2077", "O-2078"])
def test_refunds_and_recipient(attest, attest_world, order_id: str) -> None:
    world = attest_world(Path(__file__).with_name("payments.world.yaml"))
    trace = refund_order(order_id=order_id)
    snapshot = world.state()
    attest.evaluate(
        expect(trace)
        .world(snapshot)
        .sum("refunds", "amount_cents", at_most=related("orders", "amount_cents", on="order_id"))
        .world(snapshot)
        .matches("notifications", "customer_id", related("orders", "customer_id", on="order_id"))
    )
