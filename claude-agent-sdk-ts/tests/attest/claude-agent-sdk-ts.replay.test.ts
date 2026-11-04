// Replay: run the real Claude Agent SDK agent against the captured fixture with zero model calls.
//
// `useReplay("claude-agent-sdk-ts", { egress: "block" })` serves the fixture's recorded model
// responses through a local proxy and points ANTHROPIC_BASE_URL at it. In strict mode (CI sets
// CI=1; this file sets it explicitly) a changed prompt, tool or model fails with a replay-miss
// message, and nothing can reach a provider host.
//
// Claude Code exports its traces from its own process, so the test starts a local OTLP/HTTP sink,
// hands `run()` its URL, and converts what Claude Code sent.
import { attestExpect, OTelAdapter } from "@attest-ai/core";
import { evaluate, useReplay } from "@attest-ai/vitest";
import { createServer, type Server } from "node:http";
import type { AddressInfo } from "node:net";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it } from "vitest";
import { run } from "../../agent";

// Explicit, so the test does not depend on the directory Vitest runs from.
const FIXTURES_DIR = fileURLToPath(new URL("./fixtures", import.meta.url));

interface OtlpExport {
  resourceSpans: unknown[];
}

/** Serves POST /v1/traces on a local port and keeps the exports it receives. */
async function startOtlpSink(): Promise<{ server: Server; url: string; exports: OtlpExport[] }> {
  const exports: OtlpExport[] = [];
  const server = createServer((req, res) => {
    const chunks: Buffer[] = [];
    req.on("data", (chunk: Buffer) => chunks.push(chunk));
    req.on("end", () => {
      exports.push(JSON.parse(Buffer.concat(chunks).toString("utf8")) as OtlpExport);
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end("{}");
    });
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const { port } = server.address() as AddressInfo;
  return { server, url: `http://127.0.0.1:${port}/v1/traces`, exports };
}

describe("claude-agent-sdk-ts replay", () => {
  let sink: Server | undefined;
  afterEach(async () => {
    await new Promise<void>((resolve) => (sink ? sink.close(() => resolve()) : resolve()));
  });

  it("calls lookup_order once", async () => {
    // No provider key: Claude Code needs a value, replay never forwards it.
    process.env.ANTHROPIC_API_KEY = "sk-replay-dummy";
    const started = await startOtlpSink();
    sink = started.server;

    await useReplay("claude-agent-sdk-ts", {
      mode: "strict",
      egress: "block",
      fixturesDir: FIXTURES_DIR,
    });
    // run() builds the Claude Code environment from the proxy's ANTHROPIC_BASE_URL.
    const answer = await run(undefined, started.url);

    expect(answer).toBe("Order O-1 has shipped.");
    // Claude Code exports in batches; one trace, so merge the batches into one export.
    const otlp = { resourceSpans: started.exports.flatMap((e) => e.resourceSpans) };
    const trace = await OTelAdapter.fromOtlp(otlp);
    // Claude Code records no tool arguments, so the contract is the tool and its count.
    await evaluate(
      attestExpect(trace)
        .trajectory(["lookup_order"], { mode: "superset" })
        .toolCardinality("lookup_order", { atMost: 1 }),
    );
  });
});
