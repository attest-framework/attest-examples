"""Tests for the Aethon Robotics RAG agent using Attest assertions."""

from __future__ import annotations

from agent import build_agent
from attest.adapters.llamaindex import LlamaIndexInstrumentationHandler
from attest.expect import expect
from attest.result import AgentResult


def test_rag_agent_answers_product_question(attest) -> None:
    """Test that the RAG agent retrieves product info and answers correctly.

    Validates:
    - Layer 2: Cost and latency constraints
    - Layer 3: Required tool usage and retrieval steps
    - Layer 4: Output contains relevant product information
    """
    agent = build_agent()
    query = "What is the payload capacity of the AethonBot Heavy?"

    with LlamaIndexInstrumentationHandler(agent_id="aethon-rag") as handler:
        response = agent.chat(query)
        trace = handler.build_trace(query=query, response=str(response))

    result = AgentResult(trace=trace)
    chain = (
        expect(result)
        .cost_under(0.05)
        .latency_under(10000)
        .required_tools(["aethon_knowledge_base"])
        .output_contains("25")
        .output_not_contains("error")
    )
    attest.evaluate(chain)


def test_rag_agent_handles_faq_query(attest) -> None:
    """Test that the RAG agent retrieves FAQ content about weather handling.

    Validates:
    - Layer 3: Knowledge base tool is called
    - Layer 4: Response mentions IP65 rating or weather handling
    """
    agent = build_agent()
    query = "How do AethonBots handle bad weather?"

    with LlamaIndexInstrumentationHandler(agent_id="aethon-rag") as handler:
        response = agent.chat(query)
        trace = handler.build_trace(query=query, response=str(response))

    result = AgentResult(trace=trace)
    chain = (
        expect(result)
        .required_tools(["aethon_knowledge_base"])
        .output_contains("IP65")
    )
    attest.evaluate(chain)
