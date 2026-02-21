"""6-tool customer support agent definition with schemas and trace builder."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from attest.agent import Agent
from attest.trace import TraceBuilder

# ---------------------------------------------------------------------------
# Tool argument schemas (JSON Schema)
# ---------------------------------------------------------------------------

TOOL_ARG_SCHEMAS: dict[str, dict[str, Any]] = {
    "lookup_account": {
        "type": "object",
        "properties": {
            "email": {"type": "string", "format": "email"},
            "customer_id": {"type": "string"},
        },
        "anyOf": [
            {"required": ["email"]},
            {"required": ["customer_id"]},
        ],
    },
    "search_knowledge_base": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "max_results": {"type": "integer", "minimum": 1, "maximum": 20},
        },
        "required": ["query"],
    },
    "check_order_status": {
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
        },
        "required": ["order_id"],
    },
    "create_ticket": {
        "type": "object",
        "properties": {
            "subject": {"type": "string"},
            "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
            "body": {"type": "string"},
        },
        "required": ["subject", "priority", "body"],
    },
    "send_email": {
        "type": "object",
        "properties": {
            "to": {"type": "string", "format": "email"},
            "subject": {"type": "string"},
            "body": {"type": "string"},
        },
        "required": ["to", "subject", "body"],
    },
    "escalate_to_human": {
        "type": "object",
        "properties": {
            "reason": {"type": "string"},
            "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
        },
        "required": ["reason", "priority"],
    },
}

# ---------------------------------------------------------------------------
# Tool result schemas (JSON Schema)
# ---------------------------------------------------------------------------

TOOL_RESULT_SCHEMAS: dict[str, dict[str, Any]] = {
    "lookup_account": {
        "type": "object",
        "properties": {
            "customer_id": {"type": "string"},
            "name": {"type": "string"},
            "email": {"type": "string"},
            "tier": {"type": "string", "enum": ["free", "basic", "pro", "enterprise"]},
            "status": {"type": "string", "enum": ["active", "suspended", "closed"]},
        },
        "required": ["customer_id", "name", "email", "tier", "status"],
    },
    "search_knowledge_base": {
        "type": "object",
        "properties": {
            "articles": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "snippet": {"type": "string"},
                        "score": {"type": "number"},
                    },
                    "required": ["id", "title", "snippet", "score"],
                },
            },
        },
        "required": ["articles"],
    },
    "check_order_status": {
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
            "status": {"type": "string"},
            "tracking": {"type": ["string", "null"]},
            "items": {"type": "array", "items": {"type": "object"}},
            "dates": {"type": "object"},
        },
        "required": ["order_id", "status", "items", "dates"],
    },
    "create_ticket": {
        "type": "object",
        "properties": {
            "ticket_id": {"type": "string"},
            "status": {"type": "string"},
            "created_at": {"type": "string"},
        },
        "required": ["ticket_id", "status", "created_at"],
    },
    "send_email": {
        "type": "object",
        "properties": {
            "message_id": {"type": "string"},
            "sent_at": {"type": "string"},
        },
        "required": ["message_id", "sent_at"],
    },
    "escalate_to_human": {
        "type": "object",
        "properties": {
            "escalation_id": {"type": "string"},
            "queue_position": {"type": "integer"},
            "eta": {"type": "string"},
        },
        "required": ["escalation_id", "queue_position", "eta"],
    },
}

# ---------------------------------------------------------------------------
# Tool result factories — generate realistic synthetic data
# ---------------------------------------------------------------------------

_NOW_ISO = datetime.now(timezone.utc).isoformat()


def _result_lookup_account(args: dict[str, Any]) -> dict[str, Any]:
    email = args.get("email", "customer@example.com")
    cid = args.get("customer_id", f"CUS-{uuid.uuid4().hex[:8].upper()}")
    return {
        "customer_id": cid,
        "name": "Alice Johnson",
        "email": email,
        "tier": "pro",
        "status": "active",
    }


def _result_search_knowledge_base(args: dict[str, Any]) -> dict[str, Any]:
    query = args.get("query", "")
    return {
        "articles": [
            {
                "id": f"KB-{i:04d}",
                "title": f"Article about {query[:30]}",
                "snippet": f"This article explains how to handle {query[:40]}...",
                "score": round(0.95 - i * 0.05, 2),
            }
            for i in range(min(args.get("max_results", 3), 5))
        ],
    }


def _result_check_order_status(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "order_id": args.get("order_id", "ORD-00001"),
        "status": "shipped",
        "tracking": "TRK-1Z999AA10123456784",
        "items": [{"name": "Widget Pro", "quantity": 1, "price": 49.99}],
        "dates": {
            "ordered": "2026-02-10T10:00:00Z",
            "shipped": "2026-02-12T14:30:00Z",
            "estimated_delivery": "2026-02-18T00:00:00Z",
        },
    }


def _result_create_ticket(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "ticket_id": f"TKT-{uuid.uuid4().hex[:8].upper()}",
        "status": "open",
        "created_at": _NOW_ISO,
    }


def _result_send_email(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "message_id": f"MSG-{uuid.uuid4().hex[:12]}",
        "sent_at": _NOW_ISO,
    }


def _result_escalate_to_human(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "escalation_id": f"ESC-{uuid.uuid4().hex[:8].upper()}",
        "queue_position": 3,
        "eta": "15 minutes",
    }


TOOL_RESULT_FACTORIES: dict[str, Any] = {
    "lookup_account": _result_lookup_account,
    "search_knowledge_base": _result_search_knowledge_base,
    "check_order_status": _result_check_order_status,
    "create_ticket": _result_create_ticket,
    "send_email": _result_send_email,
    "escalate_to_human": _result_escalate_to_human,
}

# ---------------------------------------------------------------------------
# Default tool args per tool (used when scenario doesn't specify)
# ---------------------------------------------------------------------------

DEFAULT_TOOL_ARGS: dict[str, dict[str, Any]] = {
    "lookup_account": {"email": "alice@example.com"},
    "search_knowledge_base": {"query": "password reset", "max_results": 3},
    "check_order_status": {"order_id": "ORD-20260215-001"},
    "create_ticket": {"subject": "Support request", "priority": "medium", "body": "Customer needs help."},
    "send_email": {"to": "alice@example.com", "subject": "Follow-up", "body": "Your request has been handled."},
    "escalate_to_human": {"reason": "Complex issue requires specialist", "priority": "high"},
}

# ---------------------------------------------------------------------------
# Trace builder
# ---------------------------------------------------------------------------


def build_trace(
    scenario_id: str,
    user_message: str,
    tool_sequence: list[str],
    output_message: str,
    output_structured: dict[str, Any],
    total_tokens: int,
    cost_usd: float,
    latency_ms: int,
    tool_args_overrides: dict[str, dict[str, Any]] | None = None,
) -> Agent:
    """Build a synthetic trace for a scenario and return an AgentResult via Agent.with_trace()."""
    overrides = tool_args_overrides or {}
    builder = TraceBuilder(agent_id="support-agent")
    builder.set_input_dict({"user_message": user_message})

    # LLM call: intent classification
    ts_base = 1708000000000
    builder.add_llm_call(
        name="intent_classification",
        args={"prompt": user_message, "model": "gpt-4.1-mini"},
        result={"intent": scenario_id.split("-")[0], "confidence": 0.95},
        started_at_ms=ts_base,
        ended_at_ms=ts_base + 200,
    )

    # Tool calls per scenario sequence
    ts_cursor = ts_base + 300
    for tool_name in tool_sequence:
        args = overrides.get(tool_name, DEFAULT_TOOL_ARGS.get(tool_name, {}))
        factory = TOOL_RESULT_FACTORIES[tool_name]
        result = factory(args)
        builder.add_tool_call(
            name=tool_name,
            args=args,
            result=result,
            started_at_ms=ts_cursor,
            ended_at_ms=ts_cursor + 150,
        )
        ts_cursor += 200

    # LLM call: response generation
    builder.add_llm_call(
        name="response_generation",
        args={"model": "gpt-4.1"},
        result={"message": output_message},
        started_at_ms=ts_cursor,
        ended_at_ms=ts_cursor + 500,
    )

    builder.set_output_dict({
        "message": output_message,
        "structured": output_structured,
    })
    builder.set_metadata(
        total_tokens=total_tokens,
        cost_usd=cost_usd,
        latency_ms=latency_ms,
        model="gpt-4.1",
    )

    trace = builder.build()
    return Agent("support-agent").with_trace(trace)
