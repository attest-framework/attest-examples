# Claude Agent SDK (Python)

An order-status agent on the [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview) with one in-process MCP tool, `lookup_order`. The SDK drives its bundled Claude Code, and `attest capture` records the run through Claude Code's native OpenTelemetry traces: there is no attest-specific adapter. See the [Frameworks section of the capture guide](https://github.com/attest-framework/attest/blob/main/docs/guides/capture.md#frameworks).

The route:

- Claude Code's traces are a beta and are off unless `CLAUDE_CODE_ENABLE_TELEMETRY=1` and `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1` are both set. Without the second, Claude Code exports metrics and logs only and capture finds no steps. `agent.py` sets both for the Claude Code subprocess, with `OTEL_TRACES_EXPORTER=otlp`, `OTEL_EXPORTER_OTLP_PROTOCOL=http/json`, the metrics and logs exporters set to `none`, and `OTEL_LOG_TOOL_DETAILS=1`.
- `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` and `ANTHROPIC_BASE_URL` come from the environment (`attest capture` and `attest_replay` set both) and go to the subprocess unchanged. The model client reads only the standard variables.
- Claude Code gets a scratch `HOME` and `CLAUDE_CONFIG_DIR` on every run, with the login tokens blanked, so no user login, settings or subscription is ever used. The agent also sets `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` and `DISABLE_AUTOUPDATER=1`, and runs with `tools=[]`, `strict_mcp_config=True` and `setting_sources=[]`: its only tool is the in-process MCP server, so the run makes exactly two model calls.
- Claude Code puts a device id and a session id in every request's `metadata`, and strict replay matches request parameters. `agent.py` fixes both (`session_id` and a seeded `userID` in the scratch config); a random value would miss on every run.
- Claude Code records neither tool arguments nor message content, so the drafted contracts cover the tool called, not per-id cardinality.

`claude-agent-sdk` and its bundled Claude Code are pinned exactly in `pyproject.toml` and `uv.lock` is committed (a narrow exception in the repo's `.gitignore`): the request Claude Code sends, including the tool's schema, is part of the fixture's contract, so a Claude Code bump shows up as a reviewed lockfile change plus a replay miss.

## Capture

`attest capture` runs the agent once against a scripted model server, so no provider key is needed:

```bash
uv sync
python3 ../scripted-model/server.py --port 8793 &
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

The fixture and the drafted test are committed. Against your own agent, run the same command with your agent's start command and a real key: the proxy forwards to the provider and records what it returns.

## Test

```bash
uv run pytest -v
```

Two tests, no keys, no network to providers:

- `tests/attest/test_claude_agent_sdk.py` (drafted by capture): the contracts run on the fixture's trace.
- `tests/attest/test_claude_agent_sdk_replay.py`: runs the real agent through `attest_replay("claude-agent-sdk")` against the fixture, reads the trace Claude Code exported to a local OTLP sink, then asserts `lookup_order` was called once on it. `pyproject.toml` sets `--attest-replay=strict --attest-egress=block`.

```text
attest replay: 2 replayed · 0 live model calls · $0.00
2 passed
```

Change anything the model request carries (the prompt, a tool description, the model) and strict replay fails with the changed component named:

```text
replay miss: tools changed (hash 8ee6513→4d8c07d); re-record with `attest capture --refresh claude-agent-sdk`
```
