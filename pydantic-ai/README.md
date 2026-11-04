# Pydantic AI

An order-status agent on [Pydantic AI](https://ai.pydantic.dev/) with one tool, `lookup_order(order_id)`. `attest capture` records its run through Pydantic AI's native OpenTelemetry instrumentation: there is no attest-specific adapter. See the [Frameworks section of the capture guide](https://github.com/attest-framework/attest/blob/main/docs/guides/capture.md#frameworks).

The route:

- `Instrumentation(InstrumentationSettings(tracer_provider=..., include_content=True, version=5))` on the agent, with an OTLP/HTTP exporter that reads `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`.
- The model client (`OpenAIProvider()`) reads `OPENAI_BASE_URL`, so the recording proxy needs no code change.
- `provider.force_flush()` before the process exits.

## Capture

`attest capture` runs the agent once against a scripted model server, so no provider key is needed:

```bash
uv sync
python3 ../scripted-model/server.py --port 8791 &
OPENAI_BASE_URL=http://127.0.0.1:8791/v1 OPENAI_API_KEY=sk-fake \
  uv run attest capture --name pydantic-ai -- uv run python agent.py
```

```text
capture pydantic-ai: tests/attest/fixtures/pydantic-ai.attest.json
  trace: 2 llm_call, 1 tool_call; trace check OK
  exchanges: 2 recorded (openai chat_completions ×2)
  contracts:
    pass  tools-called                           trajectory (superset) matches [lookup_order]
    pass  cardinality-lookup_order-per-order_id  lookup_order within max 1 for each of 1 order_id value(s)
  verified: every drafted contract passes
  test: drafted tests/attest/test_pydantic_ai.py
```

The fixture and the drafted test are committed. Against your own agent, run the same command with your agent's start command and a real key: the proxy forwards to the provider and records what it returns.

## Test

```bash
uv run pytest -v
```

Two tests, no keys, no network to providers:

- `tests/attest/test_pydantic_ai.py` (drafted by capture): the contracts run on the fixture's trace.
- `tests/attest/test_pydantic_ai_replay.py`: runs the real agent (`agent.run()`) against the fixture through `attest_replay("pydantic-ai")`, then asserts `lookup_order` was called once per `order_id` on the trace that run produced. `pyproject.toml` sets `--attest-replay=strict --attest-egress=block`.

```text
attest replay: 2 replayed · 0 live model calls · $0.00
2 passed
```

Change anything the model request carries (the system prompt, a tool description, the model) and strict replay fails with the changed component named:

```text
replay miss: tools changed (hash 7c0d258→8e039d0); re-record with `attest capture --refresh pydantic-ai`
```
