"""Refund two installments through real HTTP; assertions inspect the resulting world."""
from __future__ import annotations

import json
import os
from typing import Any
from urllib.request import Request, urlopen

from attest import agent
from attest.trace import TraceBuilder


def request(path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if body is None else json.dumps(body).encode()
    req = Request(os.environ["PAYMENTS_BASE_URL"] + path, data=data,
                  headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=5) as response:
        return json.load(response)


@agent("relational-refunds")
def refund_order(builder: TraceBuilder, order_id: str) -> dict[str, Any]:
    order = request(f"/orders/{order_id}")
    builder.add_tool_call(name="lookup_order", args={"order_id": order_id}, result=order)
    # Each payment alone is within the order amount. Only their sum proves the cap.
    for amount in (1200, order["amount_cents"] - 1200):
        body = {"order_id": order_id, "amount_cents": amount}
        result = request("/refunds", body)
        builder.add_tool_call(name="issue_refund", args=body, result=result)
    body = {"order_id": order_id, "customer_id": order["customer_id"]}
    result = request("/notifications", body)
    builder.add_tool_call(name="notify_customer", args=body, result=result)
    return {"message": f"Refunded {order_id} and notified its customer."}
