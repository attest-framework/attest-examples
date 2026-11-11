# LangGraph

An order-status agent on [LangGraph](https://langchain-ai.github.io/langgraph/) (`create_react_agent`) with one tool, `lookup_order(order_id)`. `attest capture` records its run through LangSmith's OpenTelemetry mode: there is no attest-specific adapter. See the [Frameworks section of the capture guide](https://github.com/attest-framework/attest/blob/main/docs/guides/capture.md#frameworks).

Run the commands below from `langgraph/`. The example pins Attest 1.1.0. To try it, run `uv sync`, then start with [Test](#test): the committed fixture and replay tests need no real API key, and you do not need to capture first.

Nothing is sent to LangSmith. The client runs in OTel mode with a tracer provider the example owns, so spans reach only that provider's exporters, and the LangSmith key is a placeholder that is never used. LangSmith exports every runnable as a span with `gen_ai.operation.name=chain`; capture ignores those and keeps the `chat` and `execute_tool` spans.

The route:

- `Client(api_key="unused", tracing_mode="otel", otel_tracer_provider=provider)` and `tracing_context(enabled=True, client=client)` around `graph.invoke(...)`.
- The provider exports through an OTLP/HTTP exporter that reads `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`, added only when that variable is set.
- `ChatOpenAI` reads `OPENAI_BASE_URL`, so the recording proxy needs no code change.
- `client.flush()` and `provider.force_flush()` before the process exits. Each `run()` builds its own provider and client.

`create_react_agent` is deprecated upstream (moved to `langchain.agents.create_agent`, removal in LangGraph V2). The example still uses it because it is the API the capture route was verified against and it keeps the dependency set to `langgraph` and `langchain-openai`; only its `LangGraphDeprecatedSinceV10` warning is silenced. Moving to `create_agent` means adding the `langchain` package, re-capturing and re-checking the replay test.

## Pinned versions

Strict replay matches the request the agent sends, including the tool's JSON schema. `langchain-core` and `pydantic` shape that schema. This example commits `uv.lock` (a narrow exception in the repo's `.gitignore`) and `pyproject.toml` pins the framework and OTel packages exactly. A dependency bump then shows up as a reviewed lockfile change plus a replay miss, not as a surprise failure.

## Capture

`attest capture` runs the agent once against a scripted model server, so no provider key is needed:

```bash
uv sync
python3 ../scripted-model/server.py --port 8791 &
OPENAI_BASE_URL=http://127.0.0.1:8791/v1 OPENAI_API_KEY=sk-fake \
  uv run attest capture --name langgraph -- uv run python agent.py
kill %1   # stop the scripted server
```

```text
capture langgraph: tests/attest/fixtures/langgraph.attest.json
  trace: 2 llm_call, 1 tool_call; trace check OK
  exchanges: 2 recorded (openai chat_completions ×2)
  contracts:
    pass  tools-called                           trajectory (superset) matches [lookup_order]
    pass  cardinality-lookup_order-per-order_id  lookup_order within max 1 for each of 1 order_id value(s)
  verified: every drafted contract passes
  test: drafted tests/attest/test_langgraph.py
```

The fixture and the drafted test are committed. Against your own agent, run the same command with your agent's start command and a real key: the proxy forwards to the provider and records what it returns.

## Test

```bash
uv run pytest -v
```

Two tests, no keys, no network to providers:

- `tests/attest/test_langgraph.py` (drafted by capture): the contracts run on the fixture's trace.
- `tests/attest/test_langgraph_replay.py`: runs the real agent (`agent.run()`) against the fixture through `attest_replay("langgraph")`, then asserts `lookup_order` was called once per `order_id` on the trace that run produced. `pyproject.toml` sets `--attest-replay=strict --attest-egress=block`.

```text
attest replay: 2 replayed · 0 live model calls · $0.00
2 passed
```

Change anything the model request carries (the prompt, a tool description, the model) and strict replay fails with the changed component named:

```text
replay miss: tools changed (hash 30cf34e→606005f); re-record with `attest capture --refresh langgraph`
```
