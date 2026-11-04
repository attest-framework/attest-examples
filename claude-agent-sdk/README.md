# Claude Agent SDK (Python)

An order-status agent on the [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview) with one in-process MCP tool, `lookup_order`. The SDK drives its bundled Claude Code, and `attest capture` records the run through Claude Code's native OpenTelemetry traces: there is no attest-specific adapter. See the [Frameworks section of the capture guide](https://github.com/attest-framework/attest/blob/main/docs/guides/capture.md#frameworks).

The route:

- Claude Code's traces are a beta and are off unless `CLAUDE_CODE_ENABLE_TELEMETRY=1` and `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1` are both set. Without the second, Claude Code exports metrics and logs only and capture finds no steps. `agent.py` sets both for the Claude Code subprocess, with `OTEL_TRACES_EXPORTER=otlp`, `OTEL_EXPORTER_OTLP_PROTOCOL=http/json`, the metrics and logs exporters set to `none`, and `OTEL_LOG_TOOL_DETAILS=1`.
- `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` and `ANTHROPIC_BASE_URL` come from the environment (`attest capture` sets both) and go to the subprocess. The model client reads only the standard variables.
- Claude Code is a subprocess, outside any in-process egress guard, so the environment it receives is the protection. `agent.py` builds it from an allowlist (`PATH`, `TMPDIR`, a scratch `HOME` and `CLAUDE_CONFIG_DIR`, `ANTHROPIC_BASE_URL`, `ANTHROPIC_API_KEY`, the telemetry switches, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`, `DISABLE_AUTOUPDATER=1`), and blanks every other variable the SDK would inherit from the parent process (the SDK also runs `claude -v` before it applies the environment, so `agent.py` skips that check with `CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK=1`). A request setting (`CLAUDE_CODE_MAX_OUTPUT_TOKENS`, `MAX_THINKING_TOKENS`, `ANTHROPIC_MODEL`, ...) or a provider switch (`CLAUDE_CODE_USE_BEDROCK`, `AWS_*`, ...) in your shell never reaches it, and no user settings or subscription is read. Claude Code still queries the macOS keychain, but under a service name derived from the scratch config directory, so it cannot match your own entry. The environment test proves it with sentinel values.
- It also runs with `tools=[]`, `strict_mcp_config=True` and `setting_sources=[]`: its only tool is the in-process MCP server, so the run makes exactly two model calls. Its working directory is a fixed scratch directory, `/tmp/attest-claude-agent-sdk-example`, so the fixture holds no username or checkout path.
- Claude Code records neither tool arguments nor message content, so the drafted contracts cover the tool called, not per-id cardinality.

`claude-agent-sdk` (and the Claude Code it bundles) is pinned exactly in `pyproject.toml`, and `uv.lock` is committed (a narrow exception in the repo's `.gitignore`): a bump changes the requests Claude Code sends, and with no replay test nothing flags it: it is caught only when someone re-captures the fixture.

## Capture

`attest capture` runs the agent once against a scripted model server, so no provider key is needed:

```bash
uv sync
python3 ../scripted-model/server.py --port 8793 &
env -i PATH="$PATH" HOME="$(mktemp -d)" TMPDIR=/tmp \
  ANTHROPIC_BASE_URL=http://127.0.0.1:8793 ANTHROPIC_API_KEY=sk-fake \
  uv run attest capture --name claude-agent-sdk -- uv run python agent.py
kill %1   # stop the scripted server
```

```text
capture claude-agent-sdk: tests/attest/fixtures/claude-agent-sdk.attest.json
  trace: 2 llm_call, 1 tool_call; trace check OK
  exchanges: 2 recorded (anthropic messages ×2)
  contracts:
    pass  tools-called  trajectory (superset) matches [lookup_order]
  verified: every drafted contract passes
  test: drafted tests/attest/test_claude_agent_sdk.py
```

`env -i` keeps your own shell, including any Claude Code variables, out of the recording. The fixture and the drafted test are committed. Against your own agent, run the same command with your agent's start command and a real key: the proxy forwards to the provider and records what it returns.

## Test

```bash
uv run pytest -v
```

Two tests, no keys, no model calls, no network:

- `tests/attest/test_claude_agent_sdk.py` (drafted by capture): the contracts run on the fixture's recorded trace.
- `tests/attest/test_claude_agent_sdk_env.py`: runs the real SDK against a stand-in for the Claude Code binary and checks that sentinel request and provider settings in the parent environment do not reach it.

CI makes zero model calls: nothing here starts Claude Code against a model.

### Why there is no replay test

The other framework examples also run the real agent against the fixture with `--attest-replay=strict`. This one does not: Claude Code inserts its working directory, platform, shell, OS version and `Today's date is …` into the first user message of every request, and attest's replay matcher does not normalize them yet. A strict replay of this fixture misses on any other machine and on any other day. When the matcher normalizes those fields, a replay test can be added the way `pydantic-ai/` does it.
