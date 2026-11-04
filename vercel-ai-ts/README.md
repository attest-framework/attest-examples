# Vercel AI SDK (TypeScript)

An order-status agent on the [Vercel AI SDK](https://ai-sdk.dev/) 7 with one tool, `lookup_order`, run through `generateText` over several steps. `attest capture` records its run through the SDK's native OpenTelemetry integration (`@ai-sdk/otel`): there is no attest-specific adapter. See the [Frameworks section of the capture guide](https://github.com/attest-framework/attest/blob/main/docs/guides/capture.md#frameworks).

The route:

- `registerTelemetry(new OpenTelemetry())` and `experimental_telemetry: { isEnabled: true }` on the call. The legacy `LegacyOpenTelemetry` integration is not supported: it records no `gen_ai.operation.name`, so capture finds no steps and refuses to verify.
- A `NodeTracerProvider` with an OTLP/HTTP exporter that reads `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`.
- `createOpenAI()` reads `OPENAI_BASE_URL`, so the recording proxy needs no code change.
- `provider.forceFlush()` before the process exits.

## Capture

`attest capture` runs the agent once against a scripted model server, so no provider key is needed:

```bash
pnpm install
python3 ../scripted-model/server.py --port 8792 &
OPENAI_BASE_URL=http://127.0.0.1:8792/v1 OPENAI_API_KEY=sk-fake \
  npx attest capture --name vercel-ai-ts -- npx tsx agent.ts
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
pnpm install && pnpm test
```

Two test files, no keys, no network to providers:

- `tests/attest/vercel-ai-ts.test.ts` (drafted by capture): the contracts run on the fixture's trace.
- `tests/attest/vercel-ai-ts.replay.test.ts`: runs the real agent (`run()`) against the fixture through `useReplay("vercel-ai-ts", { mode: "strict", egress: "block" })`, then asserts `lookup_order` was called once per `order_id` on the trace that run produced.

`vitest.config.ts` adds the `AttestReporter`, which prints the replay summary:

```text
 Test Files  2 passed (2)
      Tests  2 passed (2)
attest replay: 2 replayed · 0 live model calls · $0.00
```

Change anything the model request carries (the system prompt, a tool description, the model) and strict replay fails with the changed component named:

```text
Error: replay miss: tools changed (hash b971156→87ef174); re-record with `attest capture --refresh vercel-ai-ts`
```
