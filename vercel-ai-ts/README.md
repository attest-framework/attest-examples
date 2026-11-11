# Vercel AI SDK (TypeScript)

An order-status agent on the [Vercel AI SDK](https://ai-sdk.dev/) 7 with one tool, `lookup_order`, run through `generateText` over several steps. `attest capture` records its run through the SDK's native OpenTelemetry integration (`@ai-sdk/otel`): there is no attest-specific adapter. See the [Frameworks section of the capture guide](https://github.com/attest-framework/attest/blob/main/docs/guides/capture.md#frameworks).

Run the commands below from `vercel-ai-ts/`. The example pins Attest 1.1.0. Start with [Test](#test) to run the committed fixture and strict-replay tests without a real API key; capture is only needed to record a new fixture.

The route:

- `registerTelemetry(new OpenTelemetry({ tracer: provider.getTracer("ai") }))` and `experimental_telemetry: { isEnabled: true }` on the call. The capture guide's snippet calls `provider.register()` and `new OpenTelemetry()`; `agent.ts` hands the tracer to the integration instead, because OpenTelemetry ignores a second global registration, so a second `run()` in one process would export to a provider the first call already shut down. The legacy `LegacyOpenTelemetry` integration is not supported: it records no `gen_ai.operation.name`, so capture finds no steps and refuses to verify.
- A `NodeTracerProvider` (not registered globally) with an OTLP/HTTP exporter that reads `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`; without the variable `run()` adds no OTLP exporter.
- `createOpenAI()` reads `OPENAI_BASE_URL`, so the recording proxy needs no code change.
- `provider.forceFlush()` before the process exits.

## Capture

`attest capture` runs the agent once against a scripted model server, so no provider key is needed:

```bash
pnpm install
python3 ../scripted-model/server.py --port 8792 &
OPENAI_BASE_URL=http://127.0.0.1:8792/v1 OPENAI_API_KEY=sk-fake \
  npx attest capture --name vercel-ai-ts -- npx tsx agent.ts
kill %1   # stop the scripted server
```

```text
capture vercel-ai-ts: tests/attest/fixtures/vercel-ai-ts.attest.json
  trace: 2 llm_call, 1 tool_call; trace check OK
  exchanges: 2 recorded (openai responses ×2)
  contracts:
    pass  tools-called                           trajectory (superset) matches [lookup_order]
    pass  cardinality-lookup_order-per-order_id  lookup_order within max 1 for each of 1 order_id value(s)
  verified: every drafted contract passes
  test: drafted tests/attest/vercel-ai-ts.test.ts
```

The fixture and the drafted test are committed. Against your own agent, run the same command with your agent's start command and a real key.

## Test

```bash
pnpm install
npx attest doctor
pnpm test
```

Run `npx attest doctor` once before the first test to download and check the engine outside Vitest's test timeout. Otherwise a cold engine download can exceed the default 5-second timeout.

The committed `pnpm-lock.yaml` pins the versions: strict replay matches the request the SDK builds, so a different `ai` or `@ai-sdk/openai` release can change it. CI installs with `--frozen-lockfile`.

Two test files, no keys, no network to providers:

- `tests/attest/vercel-ai-ts.test.ts` (drafted by capture): the contracts run on the fixture's trace.
- `tests/attest/vercel-ai-ts.replay.test.ts`: runs the real agent (`run()`) against the fixture through `useReplay("vercel-ai-ts", { mode: "strict", egress: "block" })`, then asserts `lookup_order` was called once per `order_id` on the trace that run produced.

`vitest.config.ts` adds the `AttestReporter`, which prints the replay summary:

```text
 Test Files  2 passed (2)
      Tests  2 passed (2)
attest replay: 2 replayed · 0 live model calls · $0.00
```

Change anything the model request carries (the prompt, a tool description, the model) and strict replay fails with the changed component named:

```text
Error: replay miss: tools changed (hash b971156→87ef174); re-record with `attest capture --refresh vercel-ai-ts`
```
