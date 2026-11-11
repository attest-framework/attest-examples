# Mastra (TypeScript)

An order-status agent on [Mastra](https://mastra.ai/) with one tool, `lookup_order`, run through `agent.generate`. `attest capture` records its run through Mastra's native OpenTelemetry exporter (`@mastra/otel-exporter`): there is no attest-specific adapter. See the [Frameworks section of the capture guide](https://github.com/attest-framework/attest/blob/main/docs/guides/capture.md#frameworks).

Run the commands below from `mastra-ts/`. The example pins Attest 1.1.0. Start with [Test](#test) to run the committed fixture and strict-replay tests without a real API key; capture is only needed to record a new fixture.

The route:

- `new Observability({ configs: { otel: { exporters: [new OtelExporter(...)] } } })` passed to `new Mastra({ observability })`, with a custom OTLP/HTTP endpoint read from `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` and `protocol: "http/json"`. `agent.ts` builds the `Observability` inside `run()` so a second call in one process does not export through an instance the first call already shut down; without the variable `run()` adds no OTLP exporter.
- `createOpenAI().chat(...)` for the model: Mastra's exporter reports it as `openai.chat`, and the client reads `OPENAI_BASE_URL`, so the recording proxy needs no code change.
- `observability.flush()` and `observability.shutdown()` before the process exits.

Mastra's model spans carry no `gen_ai.output.messages` and no cost, so the fixture's final output message is empty. The drafted contracts cover the tools called and per-order cardinality.

## Capture

`attest capture` runs the agent once against a scripted model server, so no provider key is needed:

```bash
pnpm install
python3 ../scripted-model/server.py --port 8793 &
OPENAI_BASE_URL=http://127.0.0.1:8793/v1 OPENAI_API_KEY=sk-fake \
  MASTRA_TELEMETRY_DISABLED=true npx attest capture --name mastra-ts -- npx tsx agent.ts
kill %1   # stop the scripted server
```

```text
capture mastra-ts: tests/attest/fixtures/mastra-ts.attest.json
  trace: 2 llm_call, 1 tool_call; trace check OK
  exchanges: 2 recorded (openai chat_completions ×2)
  contracts:
    pass  tools-called                           trajectory (superset) matches [lookup_order]
    pass  cardinality-lookup_order-per-order_id  lookup_order within max 1 for each of 1 order_id value(s)
  verified: every drafted contract passes
  test: drafted tests/attest/mastra-ts.test.ts
```

The fixture and the drafted test are committed. Against your own agent, run the same command with your agent's start command and a real key.

## Test

```bash
pnpm install
npx attest doctor
pnpm test
```

Run `npx attest doctor` once before the first test to download and check the engine outside Vitest's test timeout. This example also increases the timeout for Mastra's cold startup.

The committed `pnpm-lock.yaml` pins the versions: strict replay matches the request Mastra and `@ai-sdk/openai` build, so a different release can change it. CI installs with `--frozen-lockfile`.

Two test files, no keys, no network to providers:

- `tests/attest/mastra-ts.test.ts` (drafted by capture): the contracts run on the fixture's trace.
- `tests/attest/mastra-ts.replay.test.ts`: runs the real agent (`run()`) against the fixture through `useReplay("mastra-ts", { mode: "strict", egress: "block" })`, then asserts `lookup_order` was called once per `order_id` on the trace that run produced. `run()` also hands the spans to a collecting exporter the test passes in (`OtelExporter` accepts an `exporter`), so the test reads the trace without a network receiver. `OtelExporter` still requires a `provider.custom` endpoint for that exporter; it is never contacted.

`vitest.config.ts` sets `testTimeout: 60_000` (a runner with an empty HOME downloads the attest engine on the first evaluation, about 5s, and Mastra starts cold; vitest's 5s default is too short) and adds the `AttestReporter`, which prints the replay summary:

```text
 Test Files  2 passed (2)
      Tests  2 passed (2)
attest replay: 2 replayed · 0 live model calls · $0.00
```

Change anything the model request carries (the prompt, a tool description, the model) and strict replay fails with the changed component named:

```text
Error: replay miss: tools changed (hash b7bec5d→3e7d3b2); re-record with `attest capture --refresh mastra-ts`
```
