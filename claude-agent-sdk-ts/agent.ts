/**
 * An order-status agent built on the Claude Agent SDK, traced through Claude Code's native
 * traces. The SDK drives its bundled Claude Code, which exports OpenTelemetry traces itself (a
 * beta, enabled by the two switches in `cliEnv`). There is no attest-specific adapter:
 * `attest capture` sets ANTHROPIC_BASE_URL (the recording proxy) and
 * OTEL_EXPORTER_OTLP_TRACES_ENDPOINT (the trace receiver), and this code hands both to the
 * Claude Code subprocess.
 */
import { createSdkMcpServer, query, tool, type SDKUserMessage } from "@anthropic-ai/claude-agent-sdk";
import { mkdir, mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { z } from "zod";

const MODEL = "claude-sonnet-4-5";
const QUESTION = "Where is order O-1?";
const TOOL = "mcp__orders__lookup_order";
// Claude Code puts its working directory in every request, so it runs in a fixed neutral one and
// a fixture holds no username or checkout path.
const WORKDIR = "/tmp/attest-claude-agent-sdk-example";

const lookupOrder = tool(
  "lookup_order",
  "Look up the current shipping status of an order.",
  { order_id: z.string() },
  async () => ({ content: [{ type: "text" as const, text: "shipped" }] }),
);

/**
 * The environment of the Claude Code subprocess, built from an allowlist: nothing else in the
 * caller's shell (`CLAUDE_CODE_*` request settings, `CLAUDE_CODE_USE_BEDROCK`, `AWS_*`, ...) reaches
 * Claude Code. HOME and CLAUDE_CONFIG_DIR point at a scratch directory, so no user login, settings
 * or subscription is read.
 */
export function cliEnv(
  home: string,
  tracesEndpoint: string,
  parent: NodeJS.ProcessEnv,
): Record<string, string> {
  const need = (name: string): string => {
    const value = parent[name];
    if (!value) throw new Error(`${name} is not set`);
    return value;
  };
  return {
    PATH: need("PATH"),
    TMPDIR: parent.TMPDIR ?? "/tmp",
    HOME: home,
    CLAUDE_CONFIG_DIR: join(home, ".claude"),
    ANTHROPIC_BASE_URL: need("ANTHROPIC_BASE_URL"),
    ANTHROPIC_API_KEY: need("ANTHROPIC_API_KEY"),
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
 * `pathToClaudeCodeExecutable` replaces the bundled Claude Code; the environment test uses it to
 * see what the subprocess receives.
 */
export async function run(
  question: string = QUESTION,
  pathToClaudeCodeExecutable: string | undefined = undefined,
): Promise<string> {
  const tracesEndpoint = process.env.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT;
  if (!tracesEndpoint) throw new Error("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT is not set");
  const home = await mkdtemp(join(tmpdir(), "attest-claude-home-"));
  try {
    await mkdir(WORKDIR, { recursive: true });
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
        cwd: WORKDIR,
        env: cliEnv(home, tracesEndpoint, process.env),
        ...(pathToClaudeCodeExecutable ? { pathToClaudeCodeExecutable } : {}),
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
