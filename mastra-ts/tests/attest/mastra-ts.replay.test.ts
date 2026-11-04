// Replay: run the real Mastra agent against the captured fixture with zero model calls.
//
// `useReplay("mastra-ts", { egress: "block" })` serves the fixture's recorded model responses
// through a local proxy and points OPENAI_BASE_URL and OTEL_EXPORTER_OTLP_TRACES_ENDPOINT at it.
// In strict mode (CI sets CI=1; this file sets it explicitly) a changed prompt, tool or model
// fails with a replay-miss message, and nothing can reach a provider host.
import { attestExpect, OTelAdapter } from "@attest-ai/core";
import { evaluate, useReplay } from "@attest-ai/vitest";
import { createServer, type Server } from "node:http";
import type { AddressInfo } from "node:net";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it } from "vitest";
import { run } from "../../agent";

// Explicit, so the test does not depend on the directory Vitest runs from.
const FIXTURES_DIR = fileURLToPath(new URL("./fixtures", import.meta.url));

interface OtlpTraces {
  resourceSpans: unknown[];
}

/** A loopback OTLP/HTTP receiver that keeps the spans Mastra's exporter posts to it. */
class TraceSink {
  private readonly bodies: OtlpTraces[] = [];
  private readonly server: Server = createServer((req, res) => {
    const chunks: Buffer[] = [];
    req.on("data", (chunk: Buffer) => chunks.push(chunk));
    req.on("end", () => {
      this.bodies.push(JSON.parse(Buffer.concat(chunks).toString("utf8")) as OtlpTraces);
      res.writeHead(200, { "content-type": "application/json" }).end("{}");
    });
  });

  async listen(): Promise<string> {
    await new Promise<void>((resolve) => this.server.listen(0, "127.0.0.1", resolve));
    return `http://127.0.0.1:${(this.server.address() as AddressInfo).port}/v1/traces`;
  }

  /** Every received batch merged into one OTLP export request. */
  otlp(): string {
    return JSON.stringify({ resourceSpans: this.bodies.flatMap((body) => body.resourceSpans) });
  }

  close(): void {
    this.server.close();
  }
}

describe("mastra-ts replay", () => {
  const sink = new TraceSink();
  afterEach(() => sink.close());

  it("calls lookup_order once per order", async () => {
    // No provider key: the OpenAI client needs a value, replay never forwards it.
    process.env.OPENAI_API_KEY = "sk-replay-dummy";
    const sinkEndpoint = await sink.listen();

    await useReplay("mastra-ts", { mode: "strict", egress: "block", fixturesDir: FIXTURES_DIR });
    // createOpenAI and the exporter read the proxy's variables when run() builds them.
    const answer = await run(undefined, [sinkEndpoint]);

    expect(answer).toBe("Order O-1 has shipped.");
    const trace = await OTelAdapter.fromOtlp(sink.otlp());
    await evaluate(
      attestExpect(trace)
        .trajectory(["lookup_order"], { mode: "superset" })
        .toolCardinality("lookup_order", { per: "order_id", atMost: 1 }),
    );
  });
});
