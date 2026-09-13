from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ContextCompressionPolicy:
    """
    Decide whether the current context is eligible for compression.

    This policy does not perform compression.

    It only answers:
        1. Is the context large enough to consider compression?
        2. Is there an active workflow that makes compression unsafe?
        3. If compression is appropriate, how much history should be
           considered for compression?

    Security and authorization decisions remain outside this policy.
    """

    token_threshold: int = 8_000
    message_threshold: int = 40
    preserve_recent_messages: int = 12

    def should_compress(
        self,
        metrics: dict[str, Any],
        state: dict[str, Any] | None = None,
    ) -> bool:
        """
        Determine whether context compression should be considered.

        Compression is triggered when either:
            - approximate token count reaches the configured threshold, or
            - message count reaches the configured threshold.

        Compression is blocked when an active workflow or interrupt is
        present because the current workflow may depend on exact context.
        """
        state = state or {}

        if self._has_active_workflow(metrics, state):
            return False

        approximate_tokens = self._as_non_negative_int(
            metrics.get("approximate_tokens")
        )

        message_count = self._as_non_negative_int(metrics.get("message_count"))

        return (
            approximate_tokens >= self.token_threshold
            or message_count >= self.message_threshold
        )

    def compression_window(
        self,
        messages: list[Any],
    ) -> list[Any]:
        """
        Return the older messages eligible for compression.

        The most recent `preserve_recent_messages` messages are retained
        outside the compression window.

        If there are not enough messages to create a compression window,
        an empty list is returned.
        """
        if not isinstance(messages, list):
            return []

        if self.preserve_recent_messages <= 0:
            return list(messages)

        if len(messages) <= self.preserve_recent_messages:
            return []

        cutoff = len(messages) - self.preserve_recent_messages

        return list(messages[:cutoff])

    def _has_active_workflow(
        self,
        metrics: dict[str, Any],
        state: dict[str, Any],
    ) -> bool:
        """
        Detect conditions under which compression should be deferred.
        """
        interrupt_count = self._as_non_negative_int(metrics.get("interrupt_count"))

        if interrupt_count > 0:
            return True

        if state.get("__interrupt__"):
            return True

        if state.get("pending_approval") is not None:
            return True

        if state.get("approval_state") == "pending":
            return True

        if state.get("approval_id") is not None:
            return True

        return False

    @staticmethod
    def _as_non_negative_int(value: Any) -> int:
        """
        Convert a metric into a safe non-negative integer.
        """
        if isinstance(value, bool):
            return 0

        try:
            converted = int(value)
        except (TypeError, ValueError):
            return 0

        return max(0, converted)
