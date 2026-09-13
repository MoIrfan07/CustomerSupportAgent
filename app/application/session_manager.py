"""Application-level in-memory session management.

The session manager stores authenticated identity server-side.

It is deliberately independent of FastAPI, cookies, JWTs, and HTTP so
the storage implementation can be replaced later without changing the
authentication flow.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import secrets
from threading import RLock


@dataclass(frozen=True, slots=True)
class SessionPrincipal:
    """Trusted identity associated with an authenticated session."""

    username: str
    role: str
    customer_id: str | None = None


@dataclass(frozen=True, slots=True)
class Session:
    """Server-side authenticated session."""

    session_id: str
    principal: SessionPrincipal
    expires_at: datetime


class SessionManager:
    """Manage authenticated sessions in application memory."""

    def __init__(
        self,
        ttl: timedelta = timedelta(hours=8),
    ) -> None:
        if ttl <= timedelta(0):
            raise ValueError("Session TTL must be positive")

        self._ttl = ttl
        self._sessions: dict[str, Session] = {}
        self._lock = RLock()

    def create_session(
        self,
        principal: SessionPrincipal,
    ) -> Session:
        """Create and store a new authenticated session."""

        session = Session(
            session_id=secrets.token_urlsafe(32),
            principal=principal,
            expires_at=(datetime.now(timezone.utc) + self._ttl),
        )

        with self._lock:
            self._sessions[session.session_id] = session

        return session

    def get_principal(
        self,
        session_id: str,
    ) -> SessionPrincipal | None:
        """
        Resolve an active session to its already-authenticated principal.

        This does NOT authenticate the user again. It only verifies that
        the supplied session still exists and has not expired.
        """

        with self._lock:
            session = self._sessions.get(session_id)

            if session is None:
                return None

            if session.expires_at <= datetime.now(timezone.utc):
                self._sessions.pop(
                    session_id,
                    None,
                )
                return None

            return session.principal

    def delete_session(
        self,
        session_id: str,
    ) -> SessionPrincipal | None:
        """Invalidate a session."""

        with self._lock:
            session = self._sessions.pop(
                session_id,
                None,
            )

        if session is None:
            return None

        return session.principal

    def clear(self) -> None:
        """Remove all sessions during application shutdown."""

        with self._lock:
            self._sessions.clear()
