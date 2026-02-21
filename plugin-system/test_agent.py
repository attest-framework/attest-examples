"""Tests for the Attest plugin system.

Demonstrates custom plugin registration, execution, and result
verification. Plugins run locally — no engine or API calls needed.
"""

from __future__ import annotations

from attest import Trace
from attest.plugins import PluginRegistry, load_entrypoint_plugins

from agent import (
    CostEfficiencyPlugin,
    ProfanityFilterPlugin,
    ResponseLengthPlugin,
    build_clean_trace,
    build_profane_trace,
    build_short_trace,
    create_registry,
)


def test_registry_creation() -> None:
    """Registry should contain all three registered plugins."""
    registry = create_registry()
    assert "profanity-filter" in registry.list_plugins("assertion")
    assert "response-length" in registry.list_plugins("assertion")
    assert "cost-efficiency" in registry.list_plugins("reporter")
    assert len(registry.list_plugins()) == 3


def test_profanity_filter_passes_clean_output() -> None:
    """Profanity filter should pass on clean text."""
    plugin = ProfanityFilterPlugin()
    trace = build_clean_trace()
    result = plugin.execute(trace, {"banned_words": ["damn", "hell", "crap"]})
    assert result.status == "pass"
    assert result.score == 1.0


def test_profanity_filter_catches_violations() -> None:
    """Profanity filter should fail and report banned words found."""
    plugin = ProfanityFilterPlugin()
    trace = build_profane_trace()
    result = plugin.execute(trace, {"banned_words": ["damn", "hell"]})
    assert result.status == "fail"
    assert result.score == 0.0
    assert result.metadata is not None
    assert "damn" in result.metadata["violations"]
    assert "hell" in result.metadata["violations"]


def test_response_length_within_bounds() -> None:
    """Response length plugin should pass for normal-length output."""
    plugin = ResponseLengthPlugin()
    trace = build_clean_trace()
    result = plugin.execute(trace, {"min_chars": 10, "max_chars": 500})
    assert result.status == "pass"
    assert result.score > 0.0


def test_response_length_too_short() -> None:
    """Response length plugin should fail for very short output."""
    plugin = ResponseLengthPlugin()
    trace = build_short_trace()
    result = plugin.execute(trace, {"min_chars": 20, "max_chars": 500})
    assert result.status == "fail"
    assert "too short" in result.explanation


def test_cost_efficiency_good() -> None:
    """Cost efficiency should pass for reasonable cost/output ratio."""
    plugin = CostEfficiencyPlugin()
    trace = build_clean_trace()
    result = plugin.execute(trace, {"min_chars_per_dollar": 10000})
    assert result.status == "pass"
    assert result.metadata is not None
    assert result.metadata["chars_per_dollar"] > 0


def test_cost_efficiency_zero_cost() -> None:
    """Zero-cost traces should get maximum efficiency score."""
    plugin = CostEfficiencyPlugin()
    from attest import ManualAdapter
    adapter = ManualAdapter(agent_id="test")
    trace = adapter.capture(lambda b: (
        b.set_input(message="test"),
        b.set_output(message="response"),
        b.set_metadata(total_tokens=10, cost_usd=0.0),
    ))
    result = plugin.execute(trace, {})
    assert result.status == "pass"
    assert result.score == 1.0


def test_entrypoint_loading() -> None:
    """Entry point loading should succeed (returns 0 if no plugins installed)."""
    registry = PluginRegistry()
    count = load_entrypoint_plugins(registry)
    assert isinstance(count, int)
    assert count >= 0
