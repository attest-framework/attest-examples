/**
 * An order-status agent built on the Vercel AI SDK, traced through its native OpenTelemetry
 * integration (`@ai-sdk/otel`). There is no attest-specific adapter: `attest capture` sets
 * OPENAI_BASE_URL (the recording proxy) and OTEL_EXPORTER_OTLP_TRACES_ENDPOINT (the trace
 * receiver), and the standard clients below read both.
 */
import { createOpenAI } from "@ai-sdk/openai";
import { OpenTelemetry } from "@ai-sdk/otel";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import {
  NodeTracerProvider,
  SimpleSpanProcessor,
  type SpanExporter,
} from "@opentelemetry/sdk-trace-node";
import { generateText, registerTelemetry, stepCountIs, tool } from "ai";
import { pathToFileURL } from "node:url";
import { z } from "zod";

const MODEL = "gpt-4.1";
const QUESTION = "Where is order O-1?";

/**
 * Run the agent once and return its answer, exporting its spans before returning.
 * `extraExporters` receive the same spans as the OTLP exporter; tests use one to read the trace.
 */
export async function run(
  question: string = QUESTION,
  extraExporters: SpanExporter[] = [],
): Promise<string> {
  // The OTLP exporter reads OTEL_EXPORTER_OTLP_TRACES_ENDPOINT; without it, run() only exports to
  // `extraExporters` instead of failing on the exporter's localhost:4318 default.
  const exporters = process.env.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT
    ? [new OTLPTraceExporter(), ...extraExporters]
    : extraExporters;
  const provider = new NodeTracerProvider({
    spanProcessors: exporters.map((exporter) => new SimpleSpanProcessor(exporter)),
  });
  // No global provider: OpenTelemetry ignores a second global registration, so a second run()
  // in one process would export to a provider that is already shut down.
  registerTelemetry(new OpenTelemetry({ tracer: provider.getTracer("ai") }));
  try {
    // createOpenAI reads OPENAI_BASE_URL and OPENAI_API_KEY when it is called.
    const openai = createOpenAI();
    const result = await generateText({
      model: openai(MODEL),
      prompt: question,
      tools: {
        lookup_order: tool({
          description: "Look up the current shipping status of an order.",
          inputSchema: z.object({ order_id: z.string() }),
          execute: async () => "shipped",
        }),
      },
      stopWhen: stepCountIs(3),
      maxRetries: 0,
      experimental_telemetry: { isEnabled: true },
    });
    return result.text;
  } finally {
    await provider.forceFlush();
    await provider.shutdown();
  }
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  console.log(await run());
}
