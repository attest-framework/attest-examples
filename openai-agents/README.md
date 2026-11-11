# OpenAI Agents SDK

An order-status agent on the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) with one tool, `lookup_order(order_id)`. `attest capture` records its run through the OpenTelemetry project's [`opentelemetry-instrumentation-openai-agents-v2`](https://github.com/open-telemetry/opentelemetry-python-contrib/tree/main/instrumentation-genai/opentelemetry-instrumentation-openai-agents-v2): there is no attest-specific adapter. See the [Frameworks section of the capture guide](https://github.com/attest-framework/attest/blob/main/docs/guides/capture.md#frameworks).

Run the commands below from `openai-agents/`. The example pins Attest 1.1.0. To try it, run `uv sync`, then start with [Test](#test): the committed fixture and replay tests need no real API key, and you do not need to capture first.

The instrumentation is alpha. It emits `unknown` spans for SDK internals, which capture does not turn into steps, and its tool spans carry no `gen_ai.tool.call.id`, so trace check pairs them by order. Use this package, not the similarly named Traceloop `opentelemetry-instrumentation-openai-agents`: the two share an import namespace and the Traceloop spans fail trace check on the missing tool-call ID.

The route:

- `set_trace_processors([])` removes the SDK's hosted trace exporter, then `OpenAIAgentsInstrumentor().instrument(tracer_provider=..., capture_message_content=True)` routes spans to a provider the example owns. Do not disable SDK tracing globally: that also disables the instrumentation's hooks.
- The provider exports through an OTLP/HTTP exporter that reads `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`, added only when that variable is set.
- The SDK's default client reads `OPENAI_BASE_URL` and uses the Responses API, so the recording proxy needs no code change.
- Each `run()` builds its own provider and uninstruments before it returns, so repeated runs in one process do not share spans.

## Pinned versions

Strict replay matches the request the agent sends, including the tool's JSON schema. `openai-agents` and `pydantic` shape that schema. This example commits `uv.lock` (a narrow exception in the repo's `.gitignore`) and `pyproject.toml` pins the framework and OTel packages exactly. A dependency bump then shows up as a reviewed lockfile change plus a replay miss, not as a surprise failure.

## Capture

`attest capture` runs the agent once against a scripted model server, so no provider key is needed:

```bash
uv sync
python3 ../scripted-model/server.py --port 8791 &
OPENAI_BASE_URL=http://127.0.0.1:8791/v1 OPENAI_API_KEY=sk-fake \
  uv run attest capture --name openai-agents -- uv run python agent.py
kill %1   # stop the scripted server
```

```text
capture openai-agents: tests/attest/fixtures/openai-agents.attest.json
  trace: 1 agent_call, 2 llm_call, 1 tool_call; trace check OK
  exchanges: 2 recorded (openai responses ×2)
  contracts:
    pass  tools-called                           trajectory (superset) matches [lookup_order]
    pass  cardinality-lookup_order-per-order_id  lookup_order within max 1 for each of 1 order_id value(s)
  verified: every drafted contract passes
  test: drafted tests/attest/test_openai_agents.py
```

The fixture and the drafted test are committed. Against your own agent, run the same command with your agent's start command and a real key: the proxy forwards to the provider and records what it returns.

## Test

```bash
uv run pytest -v
```

Two tests, no keys, no network to providers:

- `tests/attest/test_openai_agents.py` (drafted by capture): the contracts run on the fixture's trace.
- `tests/attest/test_openai_agents_replay.py`: runs the real agent (`agent.run()`) against the fixture through `attest_replay("openai-agents")`, then asserts `lookup_order` was called once per `order_id` on the trace that run produced. `pyproject.toml` sets `--attest-replay=strict --attest-egress=block`.

```text
attest replay: 2 replayed · 0 live model calls · $0.00
2 passed
```

Change anything the model request carries (the prompt, a tool description, the model) and strict replay fails with the changed component named:

```text
replay miss: tools changed (hash 5764ff4→9ce1737); re-record with `attest capture --refresh openai-agents`
```
