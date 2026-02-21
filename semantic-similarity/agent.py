"""Translation agent — demonstrates Layer 5 (Embedding Similarity) assertions."""

from __future__ import annotations

from typing import Any

from attest.agent import agent
from attest.trace import TraceBuilder


@agent("translator")
def translate(builder: TraceBuilder, text: str, target_lang: str = "French") -> dict[str, Any]:
    """Translate text to a target language.

    Uses LLM to translate, then verifies the output is semantically similar
    to the input (meaning preserved despite language change).
    """
    builder.add_llm_call(
        name="gpt-4.1",
        args={
            "model": "gpt-4.1",
            "messages": [
                {"role": "system", "content": f"Translate the following to {target_lang}."},
                {"role": "user", "content": text},
            ],
        },
        result={"completion": "Bonjour, comment allez-vous aujourd'hui?"},
    )

    builder.set_metadata(total_tokens=45, cost_usd=0.001, latency_ms=600, model="gpt-4.1")

    return {
        "message": "Bonjour, comment allez-vous aujourd'hui?",
        "structured": {
            "source_lang": "English",
            "target_lang": target_lang,
            "translation": "Bonjour, comment allez-vous aujourd'hui?",
        },
    }


@agent("summarizer")
def summarize(builder: TraceBuilder, text: str) -> dict[str, Any]:
    """Summarize text while preserving core meaning.

    The summary should be semantically similar to the original text.
    """
    builder.add_llm_call(
        name="gpt-4.1-mini",
        args={
            "model": "gpt-4.1-mini",
            "messages": [
                {"role": "system", "content": "Summarize the following text concisely."},
                {"role": "user", "content": text},
            ],
        },
        result={
            "completion": (
                "Machine learning uses algorithms to learn patterns from data, "
                "enabling predictions on new inputs."
            ),
        },
    )

    builder.set_metadata(total_tokens=120, cost_usd=0.002, latency_ms=800, model="gpt-4.1-mini")

    return {
        "message": (
            "Machine learning uses algorithms to learn patterns from data, "
            "enabling predictions on new inputs."
        ),
    }
