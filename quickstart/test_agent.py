"""Tests for the customer support agent."""

from __future__ import annotations

from agent import customer_support
from attest.expect import expect


def test_customer_support_refund(attest) -> None:
    """Test the customer support agent processes refunds correctly.

    Demonstrates Attest assertions across all layers:
    - Layer 1: Schema validation
    - Layer 2: Cost and performance constraints
    - Layer 3: Trace structure (tool ordering)
    - Layer 4: Content validation
    """
    # Run the agent
    result = customer_support(order_id="ORD-12345")

    # Build and evaluate assertions using the expect DSL
    chain = (
        expect(result)
        # Layer 1: Schema validation
        .output_matches_schema(
            {
                "type": "object",
                "properties": {
                    "refund_id": {"type": "string"},
                    "amount": {"type": "number"},
                    "status": {"type": "string"},
                },
                "required": ["refund_id", "status"],
            }
        )
        # Layer 2: Cost and performance constraints
        .cost_under(0.01)
        .latency_under(5000)
        .tokens_under(500)
        # Layer 3: Trace structure (tool ordering and requirements)
        .tools_called_in_order(["lookup_order", "process_refund"])
        .required_tools(["lookup_order", "process_refund"])
        .forbidden_tools(["delete_order", "cancel_refund"])
        # Layer 4: Content validation
        .output_contains("refund")
        .output_contains("processed")
        .output_not_contains("error")
    )

    # Evaluate all assertions
    attest.evaluate(chain)
