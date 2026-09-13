from datetime import timedelta

from app.application.session_manager import (
    SessionManager,
    SessionPrincipal,
)


def test_create_session_returns_authenticated_principal():
    manager = SessionManager()

    principal = SessionPrincipal(
        username="ahmed",
        role="customer",
        customer_id="CUST-1001",
    )

    session = manager.create_session(principal)

    assert session.session_id
    assert session.principal == principal
    assert session.expires_at is not None


def test_session_round_trip():
    manager = SessionManager()

    principal = SessionPrincipal(
        username="ahmed",
        role="customer",
        customer_id="CUST-1001",
    )

    session = manager.create_session(principal)

    resolved = manager.get_principal(session.session_id)

    assert resolved == principal


def test_delete_session_invalidates_session():
    manager = SessionManager()

    principal = SessionPrincipal(
        username="ahmed",
        role="customer",
        customer_id="CUST-1001",
    )

    session = manager.create_session(principal)

    deleted_principal = manager.delete_session(session.session_id)

    assert deleted_principal == principal
    assert manager.get_principal(session.session_id) is None


def test_unknown_session_returns_none():
    manager = SessionManager()

    assert manager.get_principal("invalid-session-id") is None


def test_expired_session_returns_none():
    manager = SessionManager(ttl=timedelta(seconds=-1))

    principal = SessionPrincipal(
        username="ahmed",
        role="customer",
        customer_id="CUST-1001",
    )

    session = manager.create_session(principal)

    assert manager.get_principal(session.session_id) is None


def test_clear_removes_all_sessions():
    manager = SessionManager()

    first = manager.create_session(
        SessionPrincipal(
            username="ahmed",
            role="customer",
            customer_id="CUST-1001",
        )
    )

    second = manager.create_session(
        SessionPrincipal(
            username="john",
            role="customer",
            customer_id="CUST-1002",
        )
    )

    manager.clear()

    assert manager.get_principal(first.session_id) is None
    assert manager.get_principal(second.session_id) is None
