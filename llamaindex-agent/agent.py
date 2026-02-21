"""RAG agent using LlamaIndex with ReAct over a vector store index.

This module has ZERO Attest imports. All testing instrumentation is handled
externally by the LlamaIndex adapter.
"""

from __future__ import annotations

import os
from pathlib import Path

from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.llms.openai import OpenAI


DATA_DIR = Path(__file__).parent / "data"


def build_agent() -> ReActAgent:
    """Build a ReAct agent with a query engine tool over local documents."""
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    llm = OpenAI(model=model)
    Settings.llm = llm

    documents = SimpleDirectoryReader(str(DATA_DIR)).load_data()
    index = VectorStoreIndex.from_documents(documents)
    query_engine = index.as_query_engine()

    tools = [
        QueryEngineTool(
            query_engine=query_engine,
            metadata=ToolMetadata(
                name="aethon_knowledge_base",
                description=(
                    "Search the Aethon Robotics knowledge base for information "
                    "about products, pricing, delivery capabilities, and FAQs."
                ),
            ),
        ),
    ]

    return ReActAgent.from_tools(tools, llm=llm, verbose=False)
