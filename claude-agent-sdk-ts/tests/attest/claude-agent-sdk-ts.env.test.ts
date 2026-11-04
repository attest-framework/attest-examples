// The Claude Code subprocess gets an allowlisted environment, whatever the caller's shell holds.
//
// A stand-in for the Claude Code binary records the environment it is started with; the test runs
// the real SDK against it with sentinel request and provider settings in the parent.
import { chmod, mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";
import { run } from "../../agent";

const SENTINELS = [
  "CLAUDE_CODE_ENTRYPOINT",
  "CLAUDE_CODE_MAX_OUTPUT_TOKENS",
  "CLAUDE_CODE_USE_BEDROCK",
  "CLAUDE_CODE_USE_VERTEX",
  "CLAUDE_CODE_USE_FOUNDRY",
  "MAX_THINKING_TOKENS",
  "ANTHROPIC_MODEL",
  "ANTHROPIC_CUSTOM_HEADERS",
  "ANTHROPIC_BETAS",
  "ANTHROPIC_AUTH_TOKEN",
  "CLAUDE_CODE_OAUTH_TOKEN",
  "AWS_ACCESS_KEY_ID",
];

describe("claude-agent-sdk-ts environment", () => {
  afterEach(() => vi.unstubAllEnvs());

  it("blanks request and provider settings from the parent environment", async () => {
    const dir = await mkdtemp(join(tmpdir(), "attest-claude-probe-"));
    const dump = join(dir, "env.json");
    const probe = join(dir, "claude.mjs");
    await writeFile(
      probe,
      `#!/usr/bin/env node
import { writeFileSync } from "node:fs";
writeFileSync(${JSON.stringify(dump)}, JSON.stringify(process.env));
`,
    );
    await chmod(probe, 0o755);
    for (const name of SENTINELS) vi.stubEnv(name, "sentinel");
    vi.stubEnv("ANTHROPIC_BASE_URL", "http://127.0.0.1:1");
    vi.stubEnv("ANTHROPIC_API_KEY", "sk-dummy");
    vi.stubEnv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://127.0.0.1:1/v1/traces");

    await run(undefined, probe).catch(() => undefined); // the stand-in exits without speaking

    const received = JSON.parse(await readFile(dump, "utf8")) as Record<string, string>;
    // The SDK sets CLAUDE_CODE_ENTRYPOINT itself, so the check is on the sentinel value.
    expect(Object.entries(received).filter(([, value]) => value === "sentinel")).toEqual([]);
    expect(received.CLAUDE_CODE_USE_BEDROCK).toBeUndefined();
    expect(received.ANTHROPIC_BASE_URL).toBe("http://127.0.0.1:1");
    expect(received.CLAUDE_CODE_ENHANCED_TELEMETRY_BETA).toBe("1");
  });
});
