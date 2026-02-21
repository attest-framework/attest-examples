"""Three assertion strategies for the approach-comparison benchmark."""

from __future__ import annotations

from attest.expect import ExpectChain, expect
from attest.result import AgentResult

from scenarios import Scenario

# Model used for all LLM judge calls — explicit for defensibility
JUDGE_MODEL = "gpt-4.1"


def build_all_judge_assertions(scenario: Scenario, result: AgentResult) -> ExpectChain:
    """Approach A: Naive Judge — broad LLM judge calls for every evaluation dimension.

    Models what teams actually do when they "just use LLM-as-judge for everything":
    3-4 coarse judge calls per scenario covering correctness, tool usage,
    response quality, and subjective criteria. No deterministic assertions.

    ~3-4 judge calls per scenario, ~175 total across 50 scenarios.
    """
    chain = expect(result)

    # 1. Correctness: Did the agent understand and handle the request?
    chain = chain.passes_judge(
        f"The user asked: '{scenario.user_message}'. "
        f"Does the agent response correctly address this request? "
        f"Check that the output contains relevant information and "
        f"keywords like: {', '.join(scenario.output_keywords)}. "
        f"The response must NOT contain: {', '.join(scenario.forbidden_terms)}.",
        model=JUDGE_MODEL,
        threshold=0.8,
    )

    # 2. Tool usage: Were the right tools called in the right order?
    tools_desc = ", ".join(scenario.tool_sequence) if scenario.tool_sequence else "none"
    forbidden_desc = ", ".join(scenario.forbidden_tools) if scenario.forbidden_tools else "none"
    chain = chain.passes_judge(
        f"Evaluate the agent's tool usage. "
        f"Expected tools in order: [{tools_desc}]. "
        f"Forbidden tools: [{forbidden_desc}]. "
        f"Were the correct tools called? Were forbidden tools avoided?",
        model=JUDGE_MODEL,
        threshold=0.8,
    )

    # 3. Response quality: Is the output well-structured and complete?
    chain = chain.passes_judge(
        f"Evaluate the response quality: Is it well-structured? "
        f"Does it provide actionable information? "
        f"Is the cost (${scenario.metadata.cost_usd}) and latency "
        f"({scenario.metadata.latency_ms}ms) reasonable for this task?",
        model=JUDGE_MODEL,
        threshold=0.7,
    )

    # 4. Subjective criteria (scenario-specific)
    combined_criteria = " ".join(scenario.judge_criteria)
    chain = chain.passes_judge(
        combined_criteria,
        model=JUDGE_MODEL,
        threshold=0.8,
    )

    return chain


def build_graduated_assertions(scenario: Scenario, result: AgentResult) -> ExpectChain:
    """Approach B: Graduated — deterministic layers (L1-L4) + judge (L6) for subjective only.

    Uses the right tool for each job. Deterministic checks handle schema,
    constraints, trace ordering, and content. Judge calls reserved for
    genuinely subjective criteria (tone, empathy, clarity).

    ~10-14 deterministic assertions + 2-3 judge calls per scenario.
    """
    chain = expect(result)

    # L1: Schema assertions (deterministic)
    chain = chain.output_matches_schema(scenario.output_schema)
    for tool in scenario.required_tools:
        from support_agent import TOOL_ARG_SCHEMAS
        if tool in TOOL_ARG_SCHEMAS:
            chain = chain.tool_args_match_schema(tool, TOOL_ARG_SCHEMAS[tool])

    # L2: Constraint assertions (deterministic)
    chain = (
        chain
        .cost_under(0.05)
        .latency_under(5000)
        .tokens_under(2000)
    )
    tool_count = len(scenario.tool_sequence)
    chain = chain.tool_call_count("eq", tool_count)

    # L3: Trace assertions (deterministic)
    if scenario.tool_sequence:
        chain = chain.tools_called_in_order(scenario.tool_sequence)
    if scenario.required_tools:
        chain = chain.required_tools(scenario.required_tools)
    if scenario.forbidden_tools:
        chain = chain.forbidden_tools(scenario.forbidden_tools)

    # L4: Content assertions (deterministic)
    for keyword in scenario.output_keywords:
        chain = chain.output_contains(keyword)
    if scenario.forbidden_terms:
        chain = chain.output_forbids(scenario.forbidden_terms)

    # L6: LLM judge for subjective criteria only
    for criteria in scenario.judge_criteria:
        chain = chain.passes_judge(criteria, threshold=0.8, model=JUDGE_MODEL)

    return chain


def build_deterministic_assertions(scenario: Scenario, result: AgentResult) -> ExpectChain:
    """Approach C: Pure Deterministic — L1-L4 only. No LLM judge. Zero API cost.

    Same deterministic assertions as Approach B, plus keyword-based proxies
    for subjective criteria where possible.

    ~12-16 deterministic assertions per scenario, 0 judge calls.
    """
    chain = expect(result)

    # L1: Schema assertions
    chain = chain.output_matches_schema(scenario.output_schema)
    for tool in scenario.required_tools:
        from support_agent import TOOL_ARG_SCHEMAS
        if tool in TOOL_ARG_SCHEMAS:
            chain = chain.tool_args_match_schema(tool, TOOL_ARG_SCHEMAS[tool])

    # L2: Constraint assertions
    chain = (
        chain
        .cost_under(0.05)
        .latency_under(5000)
        .tokens_under(2000)
    )
    tool_count = len(scenario.tool_sequence)
    chain = chain.tool_call_count("eq", tool_count)

    # L3: Trace assertions
    if scenario.tool_sequence:
        chain = chain.tools_called_in_order(scenario.tool_sequence)
    if scenario.required_tools:
        chain = chain.required_tools(scenario.required_tools)
    if scenario.forbidden_tools:
        chain = chain.forbidden_tools(scenario.forbidden_tools)

    # L4: Content assertions
    for keyword in scenario.output_keywords:
        chain = chain.output_contains(keyword)
    if scenario.forbidden_terms:
        chain = chain.output_forbids(scenario.forbidden_terms)

    # L4: Keyword proxies for subjective criteria (soft)
    # Approximate tone and action signals that a judge would check.
    # Soft because keyword proxies are inherently imprecise.
    _TONE_PROXY_KEYWORDS = [
        "apologize", "sorry", "understand", "help", "assist", "thank",
        "welcome", "happy", "sure", "recommend", "sent", "verify",
        "support", "guide", "explain", "provide", "ensure",
    ]
    _ACTION_PROXY_KEYWORDS = [
        "ticket", "email", "refund", "escalated", "created",
        "sent", "initiated", "documented", "reviewed", "checked",
        "configured", "navigate", "select", "click", "log",
    ]
    chain = chain.output_has_any_keyword(_TONE_PROXY_KEYWORDS, soft=True)
    chain = chain.output_has_any_keyword(_ACTION_PROXY_KEYWORDS, soft=True)

    return chain


APPROACH_BUILDERS = {
    "all_judge": build_all_judge_assertions,
    "graduated": build_graduated_assertions,
    "deterministic": build_deterministic_assertions,
}
