/**
 * An order-status agent built on the Claude Agent SDK, traced through Claude Code's native
 * traces. The SDK drives its bundled Claude Code, which exports OpenTelemetry traces itself (a
 * beta, enabled by the two switches in `cliEnv`). There is no attest-specific adapter:
 * `attest capture` sets ANTHROPIC_BASE_URL (the recording proxy) and
 * OTEL_EXPORTER_OTLP_TRACES_ENDPOINT (the trace receiver), and this code hands both to the
 * Claude Code subprocess.
 */
import { createSdkMcpServer, query, tool, type SDKUserMessage } from "@anthropic-ai/claude-agent-sdk";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { z } from "zod";

const MODEL = "claude-sonnet-4-5";
const QUESTION = "Where is order O-1?";
const TOOL = "mcp__orders__lookup_order";
// Claude Code puts a device id and a session id in every request's metadata. Strict replay matches
// request parameters, so both are fixed: a random value would miss on every run.
const SESSION_ID = "5d1a1c3e-6f0b-4a57-9f55-0b7c2a6e1d11";
const DEVICE_ID = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";

function required(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`${name} is not set`);
  return value;
}

const lookupOrder = tool(
  "lookup_order",
  "Look up the current shipping status of an order.",
  { order_id: z.string() },
  async () => ({ content: [{ type: "text" as const, text: "shipped" }] }),
);

/**
 * The environment of the Claude Code subprocess. HOME and CLAUDE_CONFIG_DIR point at a scratch
 * directory, so no user login, settings or subscription is read; the login tokens are blanked for
 * the same reason. The model client reads only ANTHROPIC_BASE_URL and ANTHROPIC_API_KEY.
 */
function cliEnv(home: string, tracesEndpoint: string): Record<string, string> {
  const inherited = Object.fromEntries(
    Object.entries(process.env).filter((entry): entry is [string, string] => entry[1] !== undefined),
  );
  return {
    ...inherited,
    HOME: home,
    CLAUDE_CONFIG_DIR: join(home, ".claude"),
    CLAUDE_CODE_OAUTH_TOKEN: "",
    ANTHROPIC_AUTH_TOKEN: "",
    ANTHROPIC_BASE_URL: required("ANTHROPIC_BASE_URL"),
    ANTHROPIC_API_KEY: required("ANTHROPIC_API_KEY"),
    CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: "1",
    DISABLE_AUTOUPDATER: "1",
    // Native traces are off unless both switches are set; without the second, Claude Code exports
    // metrics and logs only.
    CLAUDE_CODE_ENABLE_TELEMETRY: "1",
    CLAUDE_CODE_ENHANCED_TELEMETRY_BETA: "1",
    OTEL_TRACES_EXPORTER: "otlp",
    OTEL_EXPORTER_OTLP_PROTOCOL: "http/json",
    OTEL_EXPORTER_OTLP_TRACES_ENDPOINT: tracesEndpoint,
    OTEL_TRACES_EXPORT_INTERVAL: "100",
    OTEL_METRICS_EXPORTER: "none",
    OTEL_LOGS_EXPORTER: "none",
    OTEL_LOG_TOOL_DETAILS: "1",
  };
}

// In-process MCP servers need streaming input, so the question goes in as a one-message stream.
async function* userTurn(question: string): AsyncGenerator<SDKUserMessage> {
  yield {
    type: "user",
    message: { role: "user", content: question },
    parent_tool_use_id: null,
  };
}

/**
 * Run the agent once and return its answer, with its spans exported before returning.
 * `tracesEndpoint` overrides OTEL_EXPORTER_OTLP_TRACES_ENDPOINT; tests point it at a local sink to
 * read the trace.
 */
export async function run(
  question: string = QUESTION,
  tracesEndpoint: string | undefined = undefined,
): Promise<string> {
  const endpoint = tracesEndpoint ?? required("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT");
  const home = await mkdtemp(join(tmpdir(), "attest-claude-home-"));
  try {
    // The Claude Code config the device id comes from, instead of a random one.
    await mkdir(join(home, ".claude"));
    await writeFile(join(home, ".claude", ".claude.json"), JSON.stringify({ userID: DEVICE_ID }));
    const conversation = query({
      prompt: userTurn(question),
      options: {
        tools: [], // no built-in tools
        allowedTools: [TOOL],
        mcpServers: { orders: createSdkMcpServer({ name: "orders", tools: [lookupOrder] }) },
        strictMcpConfig: true,
        settingSources: [],
        model: MODEL,
        maxTurns: 3,
        systemPrompt: "Answer the user using lookup_order.",
        permissionMode: "dontAsk",
        sessionId: SESSION_ID,
        env: cliEnv(home, endpoint),
      },
    });
    let answer = "";
    try {
      for await (const message of conversation) {
        if (message.type === "result" && message.subtype === "success") answer = message.result;
      }
    } finally {
      // Closing waits for Claude Code to exit, which flushes its final trace batch.
      conversation.close();
    }
    return answer;
  } finally {
    await rm(home, { recursive: true, force: true });
  }
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  console.log(await run());
}
