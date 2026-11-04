"""The Claude Code subprocess gets an allowlisted environment, whatever the caller's shell holds.

A stand-in for the Claude Code binary records the environment it is started with; the test
runs the real SDK against it with sentinel request and provider settings in the parent.
"""

from __future__ import annotations

import json
import stat
from pathlib import Path

import pytest

from agent import run

SENTINELS = {
    "CLAUDE_CODE_ENTRYPOINT": "sentinel-entrypoint",
    "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "12345",
    "CLAUDE_CODE_USE_BEDROCK": "1",
    "CLAUDE_CODE_USE_VERTEX": "1",
    "CLAUDE_CODE_USE_FOUNDRY": "1",
    "MAX_THINKING_TOKENS": "999",
    "ANTHROPIC_MODEL": "sentinel-model",
    "ANTHROPIC_CUSTOM_HEADERS": "x-sentinel: 1",
    "ANTHROPIC_BETAS": "sentinel-beta",
    "ANTHROPIC_AUTH_TOKEN": "sentinel-token",
    "CLAUDE_CODE_OAUTH_TOKEN": "sentinel-oauth",
    "AWS_ACCESS_KEY_ID": "sentinel-aws",
}


def test_run_blanks_request_and_provider_settings_from_the_parent_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dump = tmp_path / "env.json"
    probe = tmp_path / "claude"
    probe.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        f"json.dump(dict(os.environ), open({str(dump)!r}, 'w'))\n"
        # Answer the SDK's initialize request, so it does not wait out its 60 s timeout.
        "request = json.loads(sys.stdin.readline())\n"
        "reply = {'subtype': 'success', 'request_id': request['request_id'], 'response': {}}\n"
        "print(json.dumps({'type': 'control_response', 'response': reply}), flush=True)\n"
    )
    probe.chmod(probe.stat().st_mode | stat.S_IXUSR)
    for name, value in SENTINELS.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-dummy")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://127.0.0.1:1/v1/traces")

    assert run(cli_path=str(probe)) == ""  # the stand-in exits after initialize

    received = json.loads(dump.read_text())
    assert {name: received.get(name) for name in SENTINELS} == {name: "" for name in SENTINELS}
    assert received["ANTHROPIC_BASE_URL"] == "http://127.0.0.1:1"
    assert received["CLAUDE_CODE_ENHANCED_TELEMETRY_BETA"] == "1"
    assert received["HOME"] != str(Path.home())
