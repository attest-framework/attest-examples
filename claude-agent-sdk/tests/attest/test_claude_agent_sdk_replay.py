"""Replay: run the real Claude Agent SDK agent against the captured fixture with zero model calls.

`attest_replay("claude-agent-sdk")` serves the fixture's recorded model responses through a local
proxy and points ANTHROPIC_BASE_URL at it. pyproject.toml runs pytest with
`--attest-replay=strict --attest-egress=block`, so a changed prompt, tool or model fails with a
replay-miss message and nothing can reach a provider.

Claude Code exports its traces from its own process, so the test starts a local OTLP/HTTP sink,
hands `run()` its URL, and converts what Claude Code sent.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest
from attest import OTelAdapter, expect
from attest.plugin import AttestEngineFixture
from attest.replay import ReplaySession

from agent import run

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@contextmanager
def otlp_sink() -> Iterator[tuple[str, list[dict[str, Any]]]]:
    """Serve POST /v1/traces on a local port; yield its URL and the exports it received."""
    exports: list[dict[str, Any]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            body = self.rfile.read(int(self.headers["Content-Length"]))
            exports.append(json.loads(body))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b"{}")

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1/traces", exports
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_claude_agent_sdk_replay_calls_lookup_order_once(
    attest: AttestEngineFixture,
    attest_replay: Callable[..., ReplaySession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # No provider key: Claude Code needs a value, replay never forwards it.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-replay-dummy")

    # fixtures_dir: attest_replay resolves fixtures from pytest's rootdir, which CI moves to the
    # repo root with --rootdir=.. .
    with otlp_sink() as (traces_url, exports), attest_replay(
        "claude-agent-sdk", fixtures_dir=FIXTURES_DIR
    ):
        # run() builds the Claude Code environment from the proxy's ANTHROPIC_BASE_URL.
        answer = run(traces_endpoint=traces_url)

    assert answer == "Order O-1 has shipped."
    # Claude Code exports in batches; one trace, so merge the batches into one export.
    spans = {"resourceSpans": [rs for export in exports for rs in export["resourceSpans"]]}
    trace = OTelAdapter.from_otlp(spans)
    # Claude Code records no tool arguments, so the contract is the tool and its count.
    attest.evaluate(
        expect(trace)
        .trajectory(["lookup_order"], mode="superset")
        .tool_cardinality("lookup_order", at_most=1)
    )
