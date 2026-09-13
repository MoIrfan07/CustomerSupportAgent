from __future__ import annotations

from types import SimpleNamespace

import pytest

from adapters.api.dependencies import (
    get_application_state,
    get_services,
)


class DummyServices:
    pass


def build_request(application_state=None):
    return SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(
                application=application_state,
            )
        )
    )


def test_get_application_state_returns_application_state():
    application_state = object()
    request = build_request(application_state)

    result = get_application_state(request)

    assert result is application_state


def test_get_application_state_fails_when_not_initialized():
    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(),
        )
    )

    with pytest.raises(
        RuntimeError,
        match="Application state is not initialized",
    ):
        get_application_state(request)


def test_get_services_returns_application_services():
    services = DummyServices()

    application_state = SimpleNamespace(
        services=services,
    )

    request = build_request(application_state)

    result = get_services(request)

    assert result is services
