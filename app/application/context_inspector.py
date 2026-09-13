from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import BaseMessage


logger = logging.getLogger(__name__)


class ContextInspector:
    """
    Inspect the current agent context without modifying it.

    This is an observation-only component.

    It provides:
        - message count
        - message type distribution
        - approximate character count
        - approximate token count
        - tool call count
        - tool result count
        - interrupt count

    No conversation state is changed by this class.
    """

    def inspect(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Inspect an agent state and return context metrics.
        """

        messages = state.get("messages", [])

        if not isinstance(messages, list):
            logger.warning(
                "CONTEXT INSPECTOR | invalid messages state | type=%s",
                type(messages).__name__,
            )

            messages = []

        message_types: dict[str, int] = {}

        total_characters = 0
        tool_call_count = 0
        tool_result_count = 0

        for message in messages:
            message_type = self._get_message_type(message)

            message_types[message_type] = message_types.get(message_type, 0) + 1

            content = self._get_content(message)

            total_characters += len(content)

            tool_calls = getattr(
                message,
                "tool_calls",
                None,
            )

            if isinstance(tool_calls, list):
                tool_call_count += len(tool_calls)

            if message_type == "ToolMessage":
                tool_result_count += 1

        approximate_tokens = self._estimate_tokens(total_characters)

        interrupts = state.get(
            "__interrupt__",
            [],
        )

        interrupt_count = len(interrupts) if isinstance(interrupts, list) else 0

        result = {
            "message_count": len(messages),
            "message_types": message_types,
            "total_characters": total_characters,
            "approximate_tokens": approximate_tokens,
            "tool_call_count": tool_call_count,
            "tool_result_count": tool_result_count,
            "interrupt_count": interrupt_count,
        }

        logger.info(
            "CONTEXT INSPECTOR | messages=%s | characters=%s | "
            "approx_tokens=%s | tool_calls=%s | tool_results=%s | "
            "interrupts=%s",
            result["message_count"],
            result["total_characters"],
            result["approximate_tokens"],
            result["tool_call_count"],
            result["tool_result_count"],
            result["interrupt_count"],
        )

        return result

    @staticmethod
    def _get_message_type(
        message: Any,
    ) -> str:
        """
        Return a stable message type name.
        """

        if isinstance(message, BaseMessage):
            return message.__class__.__name__

        if isinstance(message, dict):
            message_type = message.get("type")

            if message_type:
                return str(message_type)

            return "dict"

        return type(message).__name__

    @staticmethod
    def _get_content(
        message: Any,
    ) -> str:
        """
        Extract message content as text for size estimation.
        """

        if isinstance(message, BaseMessage):
            content = message.content

        elif isinstance(message, dict):
            content = message.get("content", "")

        else:
            content = getattr(
                message,
                "content",
                "",
            )

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            return str(content)

        if content is None:
            return ""

        return str(content)

    @staticmethod
    def _estimate_tokens(
        characters: int,
    ) -> int:
        """
        Estimate token count from character count.

        This is intentionally approximate.

        A later context-engineering step will use
        model/tokenizer-specific accounting where appropriate.
        """

        if characters <= 0:
            return 0

        return max(
            1,
            characters // 4,
        )
