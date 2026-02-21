"""Comprehensive tests for the customer service agent.

Demonstrates assertion layers 1-4 and 7 (schema, constraint, trace,
content, trace tree) against a multi-agent refund flow. Uses the
@agent decorator which builds traces automatically.
"""

from __future__ import annotations

from typing import Any

from attest.expect import expect
from attest.result import AgentResult

from agent import customer_service


def test_refund_flow_schema_and_constraints(attest: Any) -> None:
    """Layers 1-2: Schema validation and cost/performance constraints."""
    result = customer_service(user_message="I want a refund for my recent order")

    chain = (
        expect(result)
        .output_matches_schema({
            "type": "object",
            "properties": {
                "intent": {"type": "string"},
                "refund_id": {"type": "string"},
                "amount": {"type": "number"},
                "status": {"type": "string"},
            },
            "required": ["intent", "refund_id", "status"],
        })
        .cost_under(0.05)
        .latency_under(5000)
        .tokens_under(500)
    )
    attest.evaluate(chain)


def test_refund_flow_trace_and_content(attest: Any) -> None:
    """Layers 3-4: Tool ordering, required/forbidden tools, output content."""
    result = customer_service(user_message="I want a refund for my recent order")

    chain = (
        expect(result)
        .tools_called_in_order(["lookup_customer", "check_refund_eligibility", "process_refund"])
        .required_tools(["lookup_customer"])
        .forbidden_tools(["delete_customer", "admin_override"])
        .output_contains("refund")
        .output_contains("RFD-999")
        .output_not_contains("error")
        .output_not_contains("denied")
    )
    attest.evaluate(chain)


def test_refund_flow_multi_agent(attest: Any) -> None:
    """Layer 7: Trace tree assertions for multi-agent delegation."""
    result = customer_service(user_message="I want a refund for my recent order")

    chain = (
        expect(result)
        .agent_called("refund-specialist")
        .delegation_depth(2)
        .follows_transitions([("customer-service", "refund-specialist")])
        .aggregate_cost_under(0.10)
        .aggregate_tokens_under(1000)
        .agent_output_contains("refund-specialist", "Refund")
    )
    attest.evaluate(chain)


def test_refund_keywords_present(attest: Any) -> None:
    """Layer 4: Verify all required keywords in response."""
    result = customer_service(user_message="I want a refund for my recent order")

    chain = (
        expect(result)
        .output_has_all_keywords(["refund", "RFD-999", "business days"])
        .output_forbids(["sorry for the inconvenience", "please hold"])
    )
    attest.evaluate(chain)
