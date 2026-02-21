"""Simple customer support agent for Attest quickstart example."""

from __future__ import annotations

from typing import Any

from attest.agent import agent
from attest.trace import TraceBuilder


@agent("customer-support")
def customer_support(builder: TraceBuilder, order_id: str) -> dict[str, Any]:
    """Customer support agent that processes refund requests.

    Args:
        builder: TraceBuilder for constructing the trace
        order_id: The order ID to look up and potentially refund

    Returns:
        A dictionary with the refund result
    """
    # Simulate LLM call to understand the customer's request
    builder.add_llm_call(
        name="gpt-4",
        args={
            "messages": [
                {
                    "role": "user",
                    "content": f"Customer wants to return order {order_id}. Process the refund.",
                }
            ],
        },
        result={"response": "I will process the refund for this order."},
    )

    # First tool: look up the order details
    builder.add_tool_call(
        name="lookup_order",
        args={"order_id": order_id},
        result={
            "order_id": order_id,
            "status": "delivered",
            "amount": 89.99,
            "customer": "John Doe",
        },
    )

    # Second tool: process the refund
    builder.add_tool_call(
        name="process_refund",
        args={"order_id": order_id, "amount": 89.99},
        result={"refund_id": "RFD-001", "status": "processed"},
    )

    # Set metadata with sample values (no actual LLM API calls)
    builder.set_metadata(
        total_tokens=150,
        cost_usd=0.005,
        latency_ms=1200,
        model="gpt-4",
    )

    # Return the final output
    refund_message = (
        f"Your refund of $89.99 has been processed successfully. "
        f"Refund ID: RFD-001. The funds will appear in your account within 3-5 business days."
    )

    return {
        "message": refund_message,
        "structured": {
            "refund_id": "RFD-001",
            "amount": 89.99,
            "status": "processed",
        },
    }
