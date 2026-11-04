"""An order-status agent built on the Claude Agent SDK, traced through Claude Code's native traces.

The SDK drives its bundled Claude Code, which exports OpenTelemetry traces itself (a beta, enabled
by the two switches in `cli_env`). There is no attest-specific adapter: `attest capture` sets
ANTHROPIC_BASE_URL (the recording proxy) and OTEL_EXPORTER_OTLP_TRACES_ENDPOINT (the trace
receiver), and this code hands both to the Claude Code subprocess.

Claude Code is a subprocess, outside any in-process egress guard. The protection is the
environment it receives: `cli_env` builds it from an allowlist.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from collections.abc import Mapping
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
# Claude Code puts its working directory in every request, so it runs in a fixed neutral one and
# a fixture holds no username or checkout path.
WORKDIR = Path("/tmp/attest-claude-agent-sdk-example")


@tool("lookup_order", "Look up the current shipping status of an order.", {"order_id": str})
async def lookup_order(args: dict[str, str]) -> dict[str, list[dict[str, str]]]:
    return {"content": [{"type": "text", "text": "shipped"}]}


def cli_env(home: Path, traces_endpoint: str, parent: Mapping[str, str]) -> dict[str, str]:
    """The environment of the Claude Code subprocess, built from an allowlist.

    The SDK merges the parent process environment into whatever it is given, so every inherited
    variable that is not on the allowlist is blanked: a request setting (`CLAUDE_CODE_*`,
    `MAX_THINKING_TOKENS`, `ANTHROPIC_MODEL`, ...) or a provider switch (`CLAUDE_CODE_USE_BEDROCK`,
    `AWS_*`, ...) in the caller's shell never reaches Claude Code. HOME and CLAUDE_CONFIG_DIR point
    at a scratch directory, so no user settings or subscription is read.
    """
    # CLAUDE_CODE_ENTRYPOINT stays out of the blanking: the SDK sets its own value (`sdk-py`) over
    # the inherited one, so the parent's never reaches Claude Code.
    env = {name: "" for name in parent if name != "CLAUDE_CODE_ENTRYPOINT"}
    env.update(
        {
            "PATH": parent["PATH"],
            "TMPDIR": parent.get("TMPDIR", "/tmp"),
            "HOME": str(home),
            "CLAUDE_CONFIG_DIR": str(home / ".claude"),
            "ANTHROPIC_BASE_URL": parent["ANTHROPIC_BASE_URL"],
            "ANTHROPIC_API_KEY": parent["ANTHROPIC_API_KEY"],
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
    )
    return env


async def _ask(question: str, env: dict[str, str], cli_path: str | None) -> str:
    # The SDK's version check runs `claude -v` with the full parent environment and the real HOME,
    # before `env` applies. Skip it.
    os.environ["CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK"] = "1"
    WORKDIR.mkdir(exist_ok=True)
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
        cwd=WORKDIR,
        env=env,
        cli_path=cli_path,
    )
    answer = ""
    async with ClaudeSDKClient(options=options) as client:
        await client.query(question)
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                answer = "".join(b.text for b in message.content if isinstance(b, TextBlock))
        # Leaving the client waits for Claude Code to exit, which flushes its final trace batch.
    return answer


def run(question: str = QUESTION, cli_path: str | None = None) -> str:
    """Run the agent once and return its answer, with its spans exported before returning.

    `cli_path` replaces the bundled Claude Code; the environment test uses it to see what the
    subprocess receives.
    """
    traces_endpoint = os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"]
    with tempfile.TemporaryDirectory(prefix="attest-claude-home-") as home:
        env = cli_env(Path(home), traces_endpoint, os.environ)
        return asyncio.run(_ask(question, env, cli_path))


if __name__ == "__main__":
    print(run())
