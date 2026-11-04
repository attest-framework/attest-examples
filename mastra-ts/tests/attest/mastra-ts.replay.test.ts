// Replay: run the real Mastra agent against the captured fixture with zero model calls.
//
// `useReplay("mastra-ts", { egress: "block" })` serves the fixture's recorded model responses
// through a local proxy and points OPENAI_BASE_URL and OTEL_EXPORTER_OTLP_TRACES_ENDPOINT at it.
// In strict mode (CI sets CI=1; this file sets it explicitly) a changed prompt, tool or model
// fails with a replay-miss message, and nothing can reach a provider host.
import { attestExpect, OTelAdapter } from "@attest-ai/core";
import { evaluate, useReplay } from "@attest-ai/vitest";
import type { ReadableSpan, SpanExporter } from "@opentelemetry/sdk-trace-node";
import { JsonTraceSerializer } from "@opentelemetry/otlp-transformer";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { run } from "../../agent";

// Explicit, so the test does not depend on the directory Vitest runs from.
const FIXTURES_DIR = fileURLToPath(new URL("./fixtures", import.meta.url));

/** Keeps the spans it receives from Mastra's OtelExporter. */
class CollectingExporter implements SpanExporter {
  readonly spans: ReadableSpan[] = [];
  export(spans: ReadableSpan[], done: (result: { code: number }) => void): void {
    this.spans.push(...spans);
    done({ code: 0 });
  }
  async shutdown(): Promise<void> {}
}

describe("mastra-ts replay", () => {
  it("calls lookup_order once per order", async () => {
    // No provider key: the OpenAI client needs a value, replay never forwards it.
    process.env.OPENAI_API_KEY = "sk-replay-dummy";
    const exporter = new CollectingExporter();

    await useReplay("mastra-ts", { mode: "strict", egress: "block", fixturesDir: FIXTURES_DIR });
    // createOpenAI and the OTLP exporter read the proxy's variables when run() builds them.
    const answer = await run(undefined, [exporter]);

    expect(answer).toBe("Order O-1 has shipped.");
    const otlp = new TextDecoder().decode(JsonTraceSerializer.serializeRequest(exporter.spans));
    const trace = await OTelAdapter.fromOtlp(otlp);
    await evaluate(
      attestExpect(trace)
        .trajectory(["lookup_order"], { mode: "superset" })
        .toolCardinality("lookup_order", { per: "order_id", atMost: 1 }),
    );
  });
});
