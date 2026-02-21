"""Custom Attest plugins — profanity filter, response length, cost efficiency.

Demonstrates the AttestPlugin protocol, PluginRegistry for registration,
and PluginResult for returning structured evaluation results. Plugins
run locally (no engine or API calls needed).
"""

from __future__ import annotations

from typing import Any

from attest import ManualAdapter, Trace
from attest.plugins import (
    AttestPlugin,
    PluginRegistry,
    PluginResult,
    register_plugin,
)


class ProfanityFilterPlugin:
    """Check agent output for banned words."""

    name: str = "profanity-filter"
    plugin_type: str = "assertion"

    def execute(self, trace: Trace, spec: dict[str, Any]) -> PluginResult:
        banned_words: list[str] = spec.get("banned_words", ["damn", "hell"])
        output_text = (trace.output or {}).get("message", "").lower()
        violations = [w for w in banned_words if w in output_text]

        if violations:
            return PluginResult(
                status="fail",
                score=0.0,
                explanation=f"Found banned words: {', '.join(violations)}",
                metadata={"violations": violations},
            )
        return PluginResult(
            status="pass",
            score=1.0,
            explanation="No profanity detected",
        )


class ResponseLengthPlugin:
    """Validate response length is within bounds."""

    name: str = "response-length"
    plugin_type: str = "assertion"

    def execute(self, trace: Trace, spec: dict[str, Any]) -> PluginResult:
        min_chars: int = spec.get("min_chars", 10)
        max_chars: int = spec.get("max_chars", 5000)
        output_text = (trace.output or {}).get("message", "")
        length = len(output_text)

        if length < min_chars:
            return PluginResult(
                status="fail",
                score=length / min_chars,
                explanation=f"Response too short: {length} chars (min: {min_chars})",
            )
        if length > max_chars:
            return PluginResult(
                status="fail",
                score=max_chars / length,
                explanation=f"Response too long: {length} chars (max: {max_chars})",
            )
        normalized = (length - min_chars) / (max_chars - min_chars)
        return PluginResult(
            status="pass",
            score=1.0 - abs(normalized - 0.5),
            explanation=f"Response length {length} chars within [{min_chars}, {max_chars}]",
        )


class CostEfficiencyPlugin:
    """Rate cost efficiency: chars of output per dollar spent."""

    name: str = "cost-efficiency"
    plugin_type: str = "reporter"

    def execute(self, trace: Trace, spec: dict[str, Any]) -> PluginResult:
        cost = (trace.metadata.cost_usd if trace.metadata else None) or 0.0
        output_text = (trace.output or {}).get("message", "")

        if cost == 0:
            return PluginResult(status="pass", score=1.0, explanation="Zero cost")

        efficiency = len(output_text) / cost
        threshold: float = spec.get("min_chars_per_dollar", 10000)
        score = min(efficiency / threshold, 1.0)

        return PluginResult(
            status="pass" if score >= 0.7 else "fail",
            score=score,
            explanation=f"Efficiency: {efficiency:.0f} chars/$ (threshold: {threshold})",
            metadata={"chars_per_dollar": efficiency},
        )


def create_registry() -> PluginRegistry:
    """Create a registry with all three custom plugins registered."""
    registry = PluginRegistry()
    register_plugin(registry, "profanity-filter", ProfanityFilterPlugin())
    register_plugin(registry, "response-length", ResponseLengthPlugin())
    register_plugin(registry, "cost-efficiency", CostEfficiencyPlugin())
    return registry


def build_clean_trace() -> Trace:
    """Build a trace with clean, well-formed output."""
    adapter = ManualAdapter(agent_id="demo-agent")
    return adapter.capture(lambda b: (
        b.set_input(message="Tell me about AI testing"),
        b.add_llm_call(
            name="gpt-4.1",
            args={"model": "gpt-4.1"},
            result={"completion": "AI testing frameworks validate agent behavior."},
        ),
        b.set_output(message="AI testing frameworks validate agent behavior across multiple dimensions."),
        b.set_metadata(total_tokens=50, cost_usd=0.002),
    ))


def build_profane_trace() -> Trace:
    """Build a trace with profanity in the output."""
    adapter = ManualAdapter(agent_id="demo-agent")
    return adapter.capture(lambda b: (
        b.set_input(message="How do I fix this?"),
        b.add_llm_call(
            name="gpt-4.1",
            args={"model": "gpt-4.1"},
            result={"completion": "Damn, that's a hell of a bug."},
        ),
        b.set_output(message="Damn, that's a hell of a bug. Try restarting."),
        b.set_metadata(total_tokens=30, cost_usd=0.001),
    ))


def build_short_trace() -> Trace:
    """Build a trace with very short output."""
    adapter = ManualAdapter(agent_id="demo-agent")
    return adapter.capture(lambda b: (
        b.set_input(message="Summarize AI"),
        b.add_llm_call(name="gpt-4.1", args={}, result={"completion": "AI."}),
        b.set_output(message="AI."),
        b.set_metadata(total_tokens=5, cost_usd=0.0001),
    ))
