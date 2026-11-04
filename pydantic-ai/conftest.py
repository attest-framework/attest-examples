"""Pytest configuration for the Pydantic AI example."""

from __future__ import annotations

# Re-export the attest fixtures from attest.plugin
from attest.plugin import attest, attest_engine, attest_replay

__all__ = ["attest", "attest_engine", "attest_replay"]
