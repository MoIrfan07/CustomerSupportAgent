from __future__ import annotations

from copy import deepcopy
from typing import Any

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from app.application.context_compression_service import (
    ContextCompressionService,
)


class StubContextCompressionPolicy:
    """
    Test-only policy that always permits compression.

    These tests are for ContextCompressionService's message-building
    behavior, not for testing compression-policy eligibility.
    """

    def should_compress(
        self,
        metrics: dict[str, Any],
        state: dict[str, Any],
    ) -> bool:
        return True

    def compression_window(
        self,
        messages: list[Any],
    ) -> list[Any]:
        # Keep the final two messages as recent context.
        return list(messages[:-2])


class StubContextSummarizer:
    """Deterministic summarizer used to isolate service behavior."""

    def summarize(
        self,
        state: dict[str, Any],
        messages_to_summarize: list[Any],
    ) -> dict[str, Any]:
        return {
            "protected_context": {
                "customer_id": "CUST-001",
            },
            "conversation_summary": ("The customer previously asked about an order."),
            "tool_activity": [
                {
                    "tool_name": "get_customer_orders",
                    "tool_call_id": "call-001",
                    "content": '{"orders": [{"order_id": "ORD-001"}]}',
                }
            ],
        }


def _build_service() -> ContextCompressionService:
    return ContextCompressionService(
        policy=StubContextCompressionPolicy(),
        summarizer=StubContextSummarizer(),
    )


def _build_state() -> dict[str, Any]:
    return {
        "messages": [
            HumanMessage(content="I need help with my account."),
            AIMessage(content="Sure, I can help."),
            ToolMessage(
                content='{"success": true, "customer_id": "CUST-001"}',
                name="get_customer",
                tool_call_id="call-customer-001",
            ),
            HumanMessage(content="Can you check my orders?"),
            AIMessage(content="I will check your orders."),
            ToolMessage(
                content='{"success": true, "orders": []}',
                name="get_customer_orders",
                tool_call_id="call-orders-001",
            ),
            HumanMessage(content="Thanks."),
            AIMessage(content="You're welcome."),
        ]
    }


def test_build_compressed_messages_creates_historical_summary_system_message() -> None:
    service = _build_service()
    state = _build_state()

    metrics = {
        "message_count": len(state["messages"]),
        "character_count": 5000,
        "approx_tokens": 1250,
        "tool_calls": 2,
        "tool_results": 2,
        "interrupts": 0,
    }

    result = service.prepare(state, metrics)

    assert result.eligible is True
    assert result.reason == "compression_ready"

    compressed_messages = service.build_compressed_messages(result)

    assert compressed_messages
    assert isinstance(compressed_messages[0], SystemMessage)

    summary = compressed_messages[0].content

    assert "Historical conversation context has been compressed." in summary
    assert "PROTECTED CONTEXT:" in summary
    assert "customer_id: CUST-001" in summary
    assert "CONVERSATION SUMMARY:" in summary
    assert "The customer previously asked about an order." in summary
    assert "HISTORICAL TOOL ACTIVITY:" in summary
    assert "get_customer_orders" in summary


def test_build_compressed_messages_preserves_recent_and_protected_messages() -> None:
    service = _build_service()
    state = _build_state()

    original_messages = list(state["messages"])

    metrics = {
        "message_count": len(original_messages),
        "character_count": 5000,
        "approx_tokens": 1250,
        "tool_calls": 2,
        "tool_results": 2,
        "interrupts": 0,
    }

    result = service.prepare(state, metrics)

    assert result.eligible is True

    compressed_messages = service.build_compressed_messages(result)

    # One historical summary + two recent messages +
    # two protected business tool messages.
    assert len(compressed_messages) == 5

    # The first message is the generated historical-context summary.
    assert isinstance(compressed_messages[0], SystemMessage)

    # The most recent messages must survive compression.
    assert original_messages[-2] in compressed_messages
    assert original_messages[-1] in compressed_messages

    # Both protected business-data ToolMessages must survive.
    assert original_messages[2] in compressed_messages
    assert original_messages[5] in compressed_messages

    # Exactly one new summary message should have been introduced.
    assert compressed_messages.count(compressed_messages[0]) == 1


def test_build_compressed_messages_does_not_mutate_original_state_or_messages() -> None:
    service = _build_service()
    state = _build_state()

    original_state = deepcopy(state)
    original_messages = list(state["messages"])
    original_message_contents = [message.content for message in original_messages]

    metrics = {
        "message_count": len(original_messages),
        "character_count": 5000,
        "approx_tokens": 1250,
        "tool_calls": 2,
        "tool_results": 2,
        "interrupts": 0,
    }

    result = service.prepare(state, metrics)

    assert result.eligible is True

    service.build_compressed_messages(result)

    # The original state must remain unchanged.
    assert state == original_state

    # The original message list must remain unchanged.
    assert state["messages"] == original_messages
    assert len(state["messages"]) == len(original_messages)

    # Individual message content must remain unchanged.
    assert [
        message.content for message in state["messages"]
    ] == original_message_contents

    # The compression result must use separate lists.
    assert result.preserved_messages is not state["messages"]
    assert result.messages_to_compress is not state["messages"]


def test_build_compressed_messages_returns_preserved_messages_when_not_eligible() -> (
    None
):
    class NeverCompressPolicy:
        def should_compress(
            self,
            metrics: dict[str, Any],
            state: dict[str, Any],
        ) -> bool:
            return False

        def compression_window(
            self,
            messages: list[Any],
        ) -> list[Any]:
            return []

    service = ContextCompressionService(
        policy=NeverCompressPolicy(),
        summarizer=StubContextSummarizer(),
    )

    state = _build_state()

    metrics = {
        "message_count": len(state["messages"]),
        "character_count": 5000,
        "approx_tokens": 12500,
        "tool_calls": 2,
        "tool_results": 2,
        "interrupts": 0,
    }

    result = service.prepare(state, metrics)

    assert result.eligible is False

    compressed_messages = service.build_compressed_messages(result)

    assert compressed_messages == result.preserved_messages
    assert not any(
        isinstance(message, SystemMessage) for message in compressed_messages
    )
