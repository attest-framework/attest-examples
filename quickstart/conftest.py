"""Pytest configuration for quickstart example."""

from __future__ import annotations

# Re-export the attest fixtures from attest.plugin
from attest.plugin import attest, attest_engine

__all__ = ["attest_engine", "attest"]
