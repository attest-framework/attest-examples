"""An order-status agent built on the Claude Agent SDK, traced through Claude Code's native traces.

The SDK drives its bundled Claude Code, which exports OpenTelemetry traces itself (a beta, enabled
by the two switches in `_cli_env`). There is no attest-specific adapter: `attest capture` sets
ANTHROPIC_BASE_URL (the recording proxy) and OTEL_EXPORTER_OTLP_TRACES_ENDPOINT (the trace
receiver), and this code hands both to the Claude Code subprocess.
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    TextBlock,
    create_sdk_mcp_server,
    tool,
)

MODEL = "claude-sonnet-4-5"
QUESTION = "Where is order O-1?"
TOOL = "mcp__orders__lookup_order"
# Claude Code puts a device id and a session id in every request's metadata. Strict replay matches
# request parameters, so both are fixed: a random value would miss on every run.
SESSION_ID = "5d1a1c3e-6f0b-4a57-9f55-0b7c2a6e1d11"
DEVICE_ID = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


@tool("lookup_order", "Look up the current shipping status of an order.", {"order_id": str})
async def lookup_order(args: dict[str, str]) -> dict[str, list[dict[str, str]]]:
    return {"content": [{"type": "text", "text": "shipped"}]}


def _cli_env(home: Path, traces_endpoint: str) -> dict[str, str]:
    """The environment of the Claude Code subprocess.

    HOME and CLAUDE_CONFIG_DIR point at a scratch directory, so no user login, settings or
    subscription is read; the login tokens are blanked for the same reason. The model client
    reads only ANTHROPIC_BASE_URL and ANTHROPIC_API_KEY.
    """
    return {
        "HOME": str(home),
        "CLAUDE_CONFIG_DIR": str(home / ".claude"),
        "CLAUDE_CODE_OAUTH_TOKEN": "",
        "ANTHROPIC_AUTH_TOKEN": "",
        "ANTHROPIC_BASE_URL": os.environ["ANTHROPIC_BASE_URL"],
        "ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"],
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        "DISABLE_AUTOUPDATER": "1",
        # Native traces are off unless both switches are set; without the second, Claude Code
        # exports metrics and logs only.
        "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
        "CLAUDE_CODE_ENHANCED_TELEMETRY_BETA": "1",
        "OTEL_TRACES_EXPORTER": "otlp",
        "OTEL_EXPORTER_OTLP_PROTOCOL": "http/json",
        "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT": traces_endpoint,
        "OTEL_TRACES_EXPORT_INTERVAL": "100",
        "OTEL_METRICS_EXPORTER": "none",
        "OTEL_LOGS_EXPORTER": "none",
        "OTEL_LOG_TOOL_DETAILS": "1",
    }


async def _ask(question: str, env: dict[str, str]) -> str:
    options = ClaudeAgentOptions(
        tools=[],  # no built-in tools
        allowed_tools=[TOOL],
        mcp_servers={"orders": create_sdk_mcp_server("orders", tools=[lookup_order])},
        strict_mcp_config=True,
        setting_sources=[],
        model=MODEL,
        max_turns=3,
        system_prompt="Answer the user using lookup_order.",
        permission_mode="dontAsk",
        session_id=SESSION_ID,
        env=env,
    )
    answer = ""
    async with ClaudeSDKClient(options=options) as client:
        await client.query(question)
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                answer = "".join(b.text for b in message.content if isinstance(b, TextBlock))
        # Leaving the client waits for Claude Code to exit, which flushes its final trace batch.
    return answer


def _seed_config(home: Path) -> None:
    """Write the Claude Code config the device id comes from, instead of a random one."""
    config_dir = home / ".claude"
    config_dir.mkdir()
    (config_dir / ".claude.json").write_text(json.dumps({"userID": DEVICE_ID}))


def run(question: str = QUESTION, traces_endpoint: str | None = None) -> str:
    """Run the agent once and return its answer, with its spans exported before returning.

    `traces_endpoint` overrides OTEL_EXPORTER_OTLP_TRACES_ENDPOINT; tests point it at a local sink
    to read the trace.
    """
    endpoint = traces_endpoint or os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"]
    with tempfile.TemporaryDirectory(prefix="attest-claude-home-") as home:
        _seed_config(Path(home))
        return asyncio.run(_ask(question, _cli_env(Path(home), endpoint)))


if __name__ == "__main__":
    print(run())
