from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from app.application.context_compression_policy import (
    ContextCompressionPolicy,
)
from app.application.context_compression_service import (
    ContextCompressionService,
)


def test_does_not_prepare_compression_below_threshold() -> None:
    policy = ContextCompressionPolicy(
        token_threshold=8_000,
        message_threshold=40,
        preserve_recent_messages=3,
    )

    service = ContextCompressionService(policy=policy)

    messages = [
        HumanMessage(content="message 1"),
        AIMessage(content="response 1"),
    ]

    state = {
        "messages": messages,
    }

    metrics = {
        "approximate_tokens": 100,
        "message_count": 2,
        "interrupt_count": 0,
    }

    result = service.prepare(state, metrics)

    assert result.eligible is False
    assert result.reason == "compression_not_required_or_blocked"
    assert result.original_message_count == 2
    assert result.compressed_message_count == 0
    assert result.preserved_message_count == 2
    assert result.messages_to_compress == []
    assert result.preserved_messages == messages
    assert result.summary == {}


def test_prepares_old_messages_for_compression() -> None:
    policy = ContextCompressionPolicy(
        token_threshold=100,
        message_threshold=40,
        preserve_recent_messages=2,
    )

    service = ContextCompressionService(policy=policy)

    messages = [
        HumanMessage(content="old user message"),
        AIMessage(content="old assistant response"),
        HumanMessage(content="recent user message"),
        AIMessage(content="recent assistant response"),
    ]

    state = {
        "messages": messages,
        "username": "ahmed",
        "user_role": "customer",
        "customer_id": "CUST-1001",
        "thread_id": "ahmed:session-1",
    }

    metrics = {
        "approximate_tokens": 200,
        "message_count": 4,
        "interrupt_count": 0,
    }

    result = service.prepare(state, metrics)

    assert result.eligible is True
    assert result.reason == "compression_ready"

    assert result.original_message_count == 4
    assert result.compressed_message_count == 2
    assert result.preserved_message_count == 2

    assert result.messages_to_compress == messages[:2]
    assert result.preserved_messages == messages[2:]

    assert result.summary["protected_context"]["username"] == "ahmed"
    assert result.summary["protected_context"]["user_role"] == "customer"
    assert result.summary["protected_context"]["customer_id"] == "CUST-1001"
    assert result.summary["protected_context"]["thread_id"] == ("ahmed:session-1")


def test_preserves_recent_messages_exactly() -> None:
    policy = ContextCompressionPolicy(
        token_threshold=100,
        preserve_recent_messages=2,
    )

    service = ContextCompressionService(policy=policy)

    messages = [
        HumanMessage(content="message 1"),
        AIMessage(content="response 1"),
        HumanMessage(content="message 2"),
        AIMessage(content="response 2"),
    ]

    state = {
        "messages": messages,
    }

    metrics = {
        "approximate_tokens": 200,
        "message_count": 4,
        "interrupt_count": 0,
    }

    result = service.prepare(state, metrics)

    assert result.preserved_messages[0] is messages[2]
    assert result.preserved_messages[1] is messages[3]


def test_pending_approval_prevents_compression() -> None:
    policy = ContextCompressionPolicy(
        token_threshold=100,
        message_threshold=2,
        preserve_recent_messages=1,
    )

    service = ContextCompressionService(policy=policy)

    messages = [
        HumanMessage(content="Cancel my order."),
        AIMessage(content="Approval required."),
        HumanMessage(content="I approve it."),
    ]

    state = {
        "messages": messages,
        "pending_approval": {
            "approval_id": "APR-1001",
            "tool_name": "cancel_order",
        },
    }

    metrics = {
        "approximate_tokens": 20_000,
        "message_count": 100,
        "interrupt_count": 1,
    }

    result = service.prepare(state, metrics)

    assert result.eligible is False
    assert result.reason == "compression_not_required_or_blocked"
    assert result.messages_to_compress == []
    assert result.preserved_messages == messages
    assert result.summary == {}


def test_empty_compression_window_is_not_eligible() -> None:
    policy = ContextCompressionPolicy(
        token_threshold=100,
        message_threshold=2,
        preserve_recent_messages=10,
    )

    service = ContextCompressionService(policy=policy)

    messages = [
        HumanMessage(content="message 1"),
        HumanMessage(content="message 2"),
    ]

    state = {
        "messages": messages,
    }

    metrics = {
        "approximate_tokens": 1_000,
        "message_count": 100,
        "interrupt_count": 0,
    }

    result = service.prepare(state, metrics)

    assert result.eligible is False
    assert result.reason == "compression_window_empty"
    assert result.messages_to_compress == []
    assert result.preserved_messages == messages
    assert result.summary == {}


def test_invalid_messages_state_is_handled_safely() -> None:
    policy = ContextCompressionPolicy(
        token_threshold=100,
        message_threshold=2,
    )

    service = ContextCompressionService(policy=policy)

    state = {
        "messages": "invalid",
    }

    metrics = {
        "approximate_tokens": 1_000,
        "message_count": 100,
        "interrupt_count": 0,
    }

    result = service.prepare(state, metrics)

    assert result.eligible is False
    assert result.original_message_count == 0
    assert result.preserved_message_count == 0
    assert result.messages_to_compress == []
    assert result.preserved_messages == []
    assert result.summary == {}


def test_service_does_not_modify_state() -> None:
    policy = ContextCompressionPolicy(
        token_threshold=100,
        preserve_recent_messages=1,
    )

    service = ContextCompressionService(policy=policy)

    messages = [
        HumanMessage(content="old message"),
        AIMessage(content="recent message"),
    ]

    state = {
        "messages": messages,
        "username": "ahmed",
        "user_role": "customer",
        "customer_id": "CUST-1001",
        "thread_id": "ahmed:session-1",
    }

    original_state = dict(state)

    metrics = {
        "approximate_tokens": 1_000,
        "message_count": 100,
        "interrupt_count": 0,
    }

    service.prepare(state, metrics)

    assert state == original_state
    assert state["messages"] == messages


def test_tool_activity_is_preserved_in_summary() -> None:
    policy = ContextCompressionPolicy(
        token_threshold=100,
        preserve_recent_messages=1,
    )

    service = ContextCompressionService(policy=policy)

    messages = [
        HumanMessage(content="Show my orders."),
        AIMessage(content="I'll check your orders."),
    ]

    state = {
        "messages": messages,
    }

    metrics = {
        "approximate_tokens": 1_000,
        "message_count": 100,
        "interrupt_count": 0,
    }

    result = service.prepare(state, metrics)

    assert result.eligible is True
    assert result.summary["conversation_history"] == [
        {
            "role": "user",
            "content": "Show my orders.",
        }
    ]


def test_custom_policy_is_used() -> None:
    policy = ContextCompressionPolicy(
        token_threshold=1_000_000,
        message_threshold=2,
        preserve_recent_messages=1,
    )

    service = ContextCompressionService(policy=policy)

    messages = [
        HumanMessage(content="old message"),
        AIMessage(content="recent message"),
    ]

    state = {
        "messages": messages,
    }

    metrics = {
        "approximate_tokens": 10,
        "message_count": 2,
        "interrupt_count": 0,
    }

    result = service.prepare(state, metrics)

    assert result.eligible is True
    assert result.compressed_message_count == 1
    assert result.preserved_message_count == 1
