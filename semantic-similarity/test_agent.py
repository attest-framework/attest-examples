"""Tests demonstrating Layer 5 — Embedding Similarity assertions.

Layer 5 uses ONNX embeddings to compute cosine similarity between
agent output and a reference string. Useful for verifying semantic
meaning is preserved (translations, summaries, paraphrases).
"""

from __future__ import annotations

from agent import summarize, translate
from attest.expect import expect


def test_translation_preserves_meaning(attest) -> None:
    """Verify translation output is semantically similar to the input meaning."""
    result = translate(text="Hello, how are you today?", target_lang="French")

    chain = (
        expect(result)
        # Layer 5: Embedding similarity — translation should preserve meaning
        .output_similar_to("Hello, how are you today?", threshold=0.7)
        # Layer 2: Cost constraint
        .cost_under(0.01)
        # Layer 4: Content check — output should not contain the English input
        .output_not_contains("Hello, how are you today?")
    )

    attest.evaluate(chain)


def test_summary_preserves_core_meaning(attest) -> None:
    """Verify summary is semantically close to the original text."""
    original = (
        "Machine learning is a subset of artificial intelligence that focuses on "
        "building systems which learn from data. These systems use algorithms to "
        "identify patterns and make predictions on new, unseen data without being "
        "explicitly programmed for each specific task."
    )

    result = summarize(text=original)

    chain = (
        expect(result)
        # Layer 5: Summary should be semantically similar to the original
        .output_similar_to(original, threshold=0.75)
        # Layer 5: Summary should capture the key concept
        .output_similar_to("algorithms learn patterns from data", threshold=0.7)
        # Layer 2: Summarization should be cheaper than full generation
        .cost_under(0.01)
        .tokens_under(200)
    )

    attest.evaluate(chain)


def test_semantic_similarity_with_soft_threshold(attest) -> None:
    """Demonstrate soft failure mode for embedding similarity."""
    result = translate(text="Good morning", target_lang="French")

    chain = (
        expect(result)
        # Strict threshold — hard fail if not met
        .output_similar_to("Good morning", threshold=0.6)
        # Higher threshold — soft fail (warn but don't block CI)
        .output_similar_to("Good morning", threshold=0.95, soft=True)
    )

    attest.evaluate(chain)
