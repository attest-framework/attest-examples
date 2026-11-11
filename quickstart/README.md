# Attest Quickstart Example

A small customer-support agent with fixed responses, demonstrating Attest 1.1.0's assertion DSL. No model calls or API keys are needed: the tests check what the agent returns and which tools it calls.

## Setup

Run these commands from `quickstart/`. Install the pinned dependencies:

```bash
uv sync
```

The Attest engine needs no build step: the SDK downloads the release that matches the pinned `attest-ai` version on the first run and caches it under `~/.attest/bin/`.

## Running Tests

Run all tests:

```bash
uv run pytest
```

Run with verbose output:

```bash
uv run pytest -v
```

Run with cost reporting:

```bash
uv run pytest --attest-cost-report
```

## Example Agent

The example includes a simple customer support agent that:

1. Receives a customer refund request
2. Calls `lookup_order` to retrieve order details
3. Calls `process_refund` to issue the refund
4. Returns a confirmation message

## Assertions Demonstrated

The tests cover the four deterministic assertion layers below, not all eight layers:

- **Layer 1 (Schema)**: Output matches a JSON Schema
- **Layer 2 (Constraints)**: Cost, latency, and token budgets
- **Layer 3 (Trace)**: Tool ordering, required tools, forbidden tools
- **Layer 4 (Content)**: String matching in output messages

## Key Files

- `agent.py` — The customer support agent using the `@agent` decorator
- `test_agent.py` — Tests using the `expect()` DSL with chained assertions
- `conftest.py` — Pytest configuration (imports fixtures from `attest.plugin`)
- `pyproject.toml` — Project dependencies and pytest config

## No API Keys Required

This example uses manual trace construction via the `@agent` decorator and `TraceBuilder`. No LLM API keys are needed.

## Testing Existing Agents

The `@agent` decorator and `TraceBuilder` injection pattern shown here lets you record steps in an agent you control. This example uses scripted responses rather than an LLM, so failures are repeatable without paying for model calls.

For an existing framework agent, choose an adapter that captures framework events, or capture its OpenTelemetry spans without an attest-specific adapter:

- [`langchain-agent/`](../langchain-agent/) — Capture a live LangChain agent via callbacks; requires `OPENAI_API_KEY`.
- [`google-adk/`](../google-adk/) — Capture live Google ADK agent events; requires `GOOGLE_API_KEY` or `GEMINI_API_KEY`.
- [`llamaindex-agent/`](../llamaindex-agent/) — Capture a live LlamaIndex query pipeline; requires `OPENAI_API_KEY`.
- [`langgraph/`](../langgraph/) — Run committed capture and strict-replay tests offline, using LangSmith's local OpenTelemetry mode.

See the [framework adapter guide](https://github.com/attest-framework/attest/blob/main/docs/guides/framework-adapters.md) and [capture guide](https://github.com/attest-framework/attest/blob/main/docs/guides/capture.md#frameworks) for the supported routes.
