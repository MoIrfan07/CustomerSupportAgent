from __future__ import annotations

import pytest


@pytest.fixture
def anyio_backend() -> str:
    """
    Restrict the async test suite to the asyncio backend.

    Without this override, anyio's pytest plugin parametrizes every
    @pytest.mark.anyio test across both asyncio and trio. This project
    does not depend on (or need) trio, so leaving the default in place
    would make the entire async test suite fail on collection with a
    missing-dependency error.
    """

    return "asyncio"
