from __future__ import annotations

from langchain_core.messages import HumanMessage

from app.application.context_compression_policy import (
    ContextCompressionPolicy,
)


def test_does_not_compress_below_thresholds() -> None:
    policy = ContextCompressionPolicy(
        token_threshold=8_000,
        message_threshold=40,
    )

    metrics = {
        "approximate_tokens": 7_999,
        "message_count": 39,
        "interrupt_count": 0,
    }

    assert policy.should_compress(metrics) is False


def test_compresses_when_token_threshold_is_reached() -> None:
    policy = ContextCompressionPolicy(
        token_threshold=8_000,
        message_threshold=40,
    )

    metrics = {
        "approximate_tokens": 8_000,
        "message_count": 10,
        "interrupt_count": 0,
    }

    assert policy.should_compress(metrics) is True


def test_compresses_when_message_threshold_is_reached() -> None:
    policy = ContextCompressionPolicy(
        token_threshold=8_000,
        message_threshold=40,
    )

    metrics = {
        "approximate_tokens": 1_000,
        "message_count": 40,
        "interrupt_count": 0,
    }

    assert policy.should_compress(metrics) is True


def test_active_interrupt_blocks_compression() -> None:
    policy = ContextCompressionPolicy(
        token_threshold=8_000,
        message_threshold=40,
    )

    metrics = {
        "approximate_tokens": 20_000,
        "message_count": 100,
        "interrupt_count": 1,
    }

    assert policy.should_compress(metrics) is False


def test_interrupt_state_blocks_compression() -> None:
    policy = ContextCompressionPolicy(
        token_threshold=8_000,
        message_threshold=40,
    )

    metrics = {
        "approximate_tokens": 20_000,
        "message_count": 100,
        "interrupt_count": 0,
    }

    state = {
        "__interrupt__": ["approval-required"],
    }

    assert policy.should_compress(metrics, state) is False


def test_pending_approval_blocks_compression() -> None:
    policy = ContextCompressionPolicy(
        token_threshold=8_000,
        message_threshold=40,
    )

    metrics = {
        "approximate_tokens": 20_000,
        "message_count": 100,
        "interrupt_count": 0,
    }

    state = {
        "pending_approval": {
            "approval_id": "APR-1001",
        },
    }

    assert policy.should_compress(metrics, state) is False


def test_pending_approval_state_blocks_compression() -> None:
    policy = ContextCompressionPolicy(
        token_threshold=8_000,
        message_threshold=40,
    )

    metrics = {
        "approximate_tokens": 20_000,
        "message_count": 100,
        "interrupt_count": 0,
    }

    state = {
        "approval_state": "pending",
    }

    assert policy.should_compress(metrics, state) is False


def test_approval_id_blocks_compression() -> None:
    policy = ContextCompressionPolicy(
        token_threshold=8_000,
        message_threshold=40,
    )

    metrics = {
        "approximate_tokens": 20_000,
        "message_count": 100,
        "interrupt_count": 0,
    }

    state = {
        "approval_id": "APR-1001",
    }

    assert policy.should_compress(metrics, state) is False


def test_compression_window_preserves_recent_messages() -> None:
    policy = ContextCompressionPolicy(
        preserve_recent_messages=3,
    )

    messages = [
        HumanMessage(content="message 1"),
        HumanMessage(content="message 2"),
        HumanMessage(content="message 3"),
        HumanMessage(content="message 4"),
        HumanMessage(content="message 5"),
    ]

    window = policy.compression_window(messages)

    assert [message.content for message in window] == [
        "message 1",
        "message 2",
    ]


def test_compression_window_returns_empty_when_history_is_small() -> None:
    policy = ContextCompressionPolicy(
        preserve_recent_messages=12,
    )

    messages = [
        HumanMessage(content="message 1"),
        HumanMessage(content="message 2"),
    ]

    assert policy.compression_window(messages) == []


def test_zero_preserve_recent_messages_allows_entire_history() -> None:
    policy = ContextCompressionPolicy(
        preserve_recent_messages=0,
    )

    messages = [
        HumanMessage(content="message 1"),
        HumanMessage(content="message 2"),
        HumanMessage(content="message 3"),
    ]

    window = policy.compression_window(messages)

    assert window == messages


def test_invalid_messages_input_returns_empty_window() -> None:
    policy = ContextCompressionPolicy()

    assert policy.compression_window("not-a-list") == []


def test_invalid_metrics_are_treated_as_zero() -> None:
    policy = ContextCompressionPolicy(
        token_threshold=8_000,
        message_threshold=40,
    )

    metrics = {
        "approximate_tokens": "invalid",
        "message_count": None,
        "interrupt_count": False,
    }

    assert policy.should_compress(metrics) is False
