/**
 * An order-status agent built on Mastra, traced through its native OpenTelemetry exporter
 * (`@mastra/otel-exporter`). There is no attest-specific adapter: `attest capture` sets
 * OPENAI_BASE_URL (the recording proxy) and OTEL_EXPORTER_OTLP_TRACES_ENDPOINT (the trace
 * receiver), and the standard client and exporter configuration below read both.
 */
import { createOpenAI } from "@ai-sdk/openai";
import { Agent } from "@mastra/core/agent";
import { Mastra } from "@mastra/core/mastra";
import { createTool } from "@mastra/core/tools";
import { Observability } from "@mastra/observability";
import { OtelExporter } from "@mastra/otel-exporter";
import type { SpanExporter } from "@opentelemetry/sdk-trace-node";
import { pathToFileURL } from "node:url";
import { z } from "zod";

const MODEL = "gpt-4.1";
const QUESTION = "Where is order O-1?";

// OtelExporter refuses a custom provider without an endpoint even when it is given a span
// exporter, which then receives the spans in place of the HTTP exporter. Never contacted.
const UNUSED_ENDPOINT = "http://127.0.0.1:4318/v1/traces";

function otlpExporter(endpoint: string, exporter?: SpanExporter): OtelExporter {
  return new OtelExporter({
    provider: { custom: { endpoints: { traces: endpoint }, protocol: "http/json" } },
    signals: { traces: true, logs: false },
    exporter,
  });
}

/**
 * Run the agent once and return its answer, exporting its spans before returning.
 * `extraExporters` receive the same spans as the OTLP exporter; tests use one to read the trace.
 */
export async function run(
  question: string = QUESTION,
  extraExporters: SpanExporter[] = [],
): Promise<string> {
  // Without the variable, run() adds no OTLP exporter and exports only to `extraExporters`.
  const traceEndpoint = process.env.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT;
  const exporters = [
    ...(traceEndpoint ? [otlpExporter(traceEndpoint)] : []),
    ...extraExporters.map((exporter) => otlpExporter(UNUSED_ENDPOINT, exporter)),
  ];
  // A fresh Observability per run keeps a second run() in one process from exporting through an
  // instance the first run already shut down.
  const observability = new Observability({
    configs: { otel: { serviceName: "mastra-ts", exporters } },
  });
  const lookupOrder = createTool({
    id: "lookup_order",
    description: "Look up the current shipping status of an order.",
    inputSchema: z.object({ order_id: z.string() }),
    outputSchema: z.string(),
    execute: async () => "shipped",
  });
  const agent = new Agent({
    id: "order-agent",
    name: "Order Agent",
    instructions: "Use lookup_order to answer order status questions.",
    model: createOpenAI().chat(MODEL),
    tools: { lookup_order: lookupOrder },
  });
  const mastra = new Mastra({ agents: { agent }, observability, logger: false });
  try {
    const result = await mastra.getAgent("agent").generate(question);
    return result.text;
  } finally {
    await observability.flush();
    await observability.shutdown();
  }
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  console.log(await run());
}
