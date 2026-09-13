from __future__ import annotations

from typing import Any

import pytest
from langchain.agents.middleware import ModelRequest, ModelResponse
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from app.application.context_compression_service import (
    ContextCompressionService,
)
from adapters.agents.middleware.context_compression_middleware import (
    ContextCompressionMiddleware,
)


class ForceCompressionPolicy:
    """
    Test-only policy that deterministically makes compression eligible.

    This bypasses the production threshold so this test can verify the
    complete compression pipeline rather than waiting for a very large
    real conversation.
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
        # Compress everything except the final two messages.
        return list(messages[:-2])


class DeterministicSummarizer:
    """
    Test-only summarizer.

    The production service remains responsible for orchestrating the
    compression process. This summarizer simply avoids an external LLM
    call so the test remains deterministic.
    """

    def summarize(
        self,
        state: dict[str, Any],
        messages_to_summarize: list[Any],
    ) -> dict[str, Any]:
        return {
            "protected_context": {
                "customer_id": "CUST-1001",
            },
            "conversation_summary": (
                "The customer previously asked about their account and order history."
            ),
            "tool_activity": [
                {
                    "tool_name": "get_customer_orders",
                    "tool_call_id": "call-orders-001",
                    "content": (
                        '{"success": true, "orders": [{"order_id": "ORD-5001"}]}'
                    ),
                }
            ],
        }


class FixedInspector:
    """
    Test-only inspector that makes the middleware's decision path
    deterministic while preserving the real compression service.
    """

    def inspect(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "message_count": len(state.get("messages", [])),
            "character_count": 50000,
            "approx_tokens": 12500,
            "tool_calls": 1,
            "tool_results": 1,
            "interrupts": 0,
        }


class CapturingHandler:
    """Capture the request received by the downstream model."""

    def __init__(self) -> None:
        self.request: ModelRequest | None = None

    async def __call__(
        self,
        request: ModelRequest,
    ) -> ModelResponse:
        self.request = request

        return ModelResponse(
            result=AIMessage(content="compressed-context model response")
        )


def _build_state() -> dict[str, Any]:
    return {
        "messages": [
            HumanMessage(content="I need help with my account."),
            AIMessage(content="Sure, I can help."),
            ToolMessage(
                content=('{"success": true, "customer_id": "CUST-1001"}'),
                name="get_customer",
                tool_call_id="call-customer-001",
            ),
            HumanMessage(content="Can you check my orders?"),
            AIMessage(content="I will check your orders."),
            ToolMessage(
                content=('{"success": true, "orders": [{"order_id": "ORD-5001"}]}'),
                name="get_customer_orders",
                tool_call_id="call-orders-001",
            ),
            HumanMessage(content="Thanks."),
            AIMessage(content="You're welcome."),
        ]
    }


def _build_service() -> ContextCompressionService:
    return ContextCompressionService(
        policy=ForceCompressionPolicy(),
        summarizer=DeterministicSummarizer(),
    )


def _build_request(
    state: dict[str, Any],
) -> ModelRequest:
    return ModelRequest(
        model=None,
        tools=[],
        system_prompt=None,
        response_format=None,
        messages=state["messages"],
        state=state,
        runtime=None,
    )


@pytest.mark.anyio
async def test_real_compression_service_produces_compressed_model_context() -> None:
    service = _build_service()

    middleware = ContextCompressionMiddleware(
        compression_service=service,
        inspector=FixedInspector(),
    )

    state = _build_state()
    request = _build_request(state)
    handler = CapturingHandler()

    response = await middleware.awrap_model_call(
        request,
        handler,
    )

    assert isinstance(response, ModelResponse)
    assert handler.request is not None

    compressed_messages = handler.request.messages

    assert compressed_messages
    assert isinstance(compressed_messages[0], SystemMessage)

    summary = compressed_messages[0].content

    assert "Historical conversation context has been compressed." in summary
    assert "CUST-1001" in summary
    assert "ORD-5001" in summary

    # The recent conversation is preserved.
    assert any(
        message.content == "Thanks."
        for message in compressed_messages
        if isinstance(message, HumanMessage)
    )

    assert any(
        message.content == "You're welcome."
        for message in compressed_messages
        if isinstance(message, AIMessage)
    )

    # Protected historical business context is also preserved.
    assert any(
        isinstance(message, ToolMessage) and message.name == "get_customer"
        for message in compressed_messages
    )

    assert any(
        isinstance(message, ToolMessage) and message.name == "get_customer_orders"
        for message in compressed_messages
    )

    # The compressed request is smaller than the original context.
    assert len(compressed_messages) < len(state["messages"])


@pytest.mark.anyio
async def test_real_compression_does_not_mutate_persisted_state() -> None:
    service = _build_service()

    middleware = ContextCompressionMiddleware(
        compression_service=service,
        inspector=FixedInspector(),
    )

    state = _build_state()
    original_messages = list(state["messages"])

    request = _build_request(state)
    handler = CapturingHandler()

    await middleware.awrap_model_call(
        request,
        handler,
    )

    assert state["messages"] == original_messages
    assert len(state["messages"]) == 8

    assert request.messages == original_messages
    assert len(request.messages) == 8

    assert handler.request is not None
    assert len(handler.request.messages) < len(request.messages)


@pytest.mark.anyio
async def test_real_compression_preserves_business_facts_in_summary() -> None:
    service = _build_service()

    middleware = ContextCompressionMiddleware(
        compression_service=service,
        inspector=FixedInspector(),
    )

    state = _build_state()
    request = _build_request(state)
    handler = CapturingHandler()

    await middleware.awrap_model_call(
        request,
        handler,
    )

    assert handler.request is not None

    summary_message = handler.request.messages[0]

    assert isinstance(summary_message, SystemMessage)

    summary = summary_message.content

    assert "BUSINESS FACTS:" in summary
    assert "ORD-5001" in summary
    assert "get_customer_orders" in summary
