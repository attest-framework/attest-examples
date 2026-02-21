"""Attest engine fixture for the approach-comparison benchmark."""

from __future__ import annotations

from collections.abc import Generator

import pytest

from attest.plugin import AttestEngineFixture


@pytest.fixture(scope="session")
def attest_engine(request: pytest.FixtureRequest) -> Generator[AttestEngineFixture, None, None]:
    """Session-scoped fixture providing access to the Attest engine."""
    engine_path: str | None = request.config.getoption("--attest-engine", default=None)
    log_level: str = request.config.getoption("--attest-log-level", default="warn")

    fixture = AttestEngineFixture(engine_path=engine_path, log_level=log_level)
    try:
        fixture.start()
    except FileNotFoundError:
        pytest.skip("attest-engine binary not found; build with 'make engine'")

    yield fixture
    fixture.stop()


@pytest.fixture
def attest(attest_engine: AttestEngineFixture) -> AttestEngineFixture:
    """Function-scoped convenience fixture."""
    return attest_engine
