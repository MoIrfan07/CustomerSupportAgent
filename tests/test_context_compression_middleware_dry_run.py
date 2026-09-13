from __future__ import annotations

from typing import Any

from langchain.agents.middleware import ModelResponse
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)

from adapters.agents.middleware.context_compression_middleware import (
    ContextCompressionMiddleware,
)


class StubContextInspector:
    """Return deterministic metrics that make compression eligible."""

    def inspect(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "message_count": len(state.get("messages", [])),
            "character_count": 50000,
            "approx_tokens": 12500,
            "tool_calls": 0,
            "tool_results": 0,
            "interrupts": 0,
        }


class StubCompressionResult:
    """Minimal compression result used by the middleware test."""

    eligible = True
    reason = "compression_ready"
    original_message_count = 8
    compressed_message_count = 6
    preserved_message_count = 2


class StubCompressionService:
    """Deterministic compression service used to isolate middleware behavior."""

    def __init__(self) -> None:
        self.prepare_called = False
        self.build_called = False

    def prepare(
        self,
        state: dict[str, Any],
        metrics: dict[str, Any],
    ) -> StubCompressionResult:
        self.prepare_called = True

        assert metrics["message_count"] == len(state["messages"])

        return StubCompressionResult()

    def build_compressed_messages(
        self,
        result: StubCompressionResult,
    ) -> list[Any]:
        self.build_called = True

        assert result.eligible is True

        return [
            SystemMessage(content="Historical context has been compressed."),
            HumanMessage(content="Recent user message."),
            AIMessage(content="Recent assistant response."),
        ]


class StubHandler:
    """Capture the request received by the downstream model handler."""

    def __init__(self) -> None:
        self.called = False
        self.request = None

    def __call__(self, request: Any) -> ModelResponse:
        self.called = True
        self.request = request

        return ModelResponse(result=AIMessage(content="stub model response"))


def _build_state() -> dict[str, Any]:
    return {
        "messages": [
            HumanMessage(content="Historical message 1"),
            AIMessage(content="Historical response 1"),
            HumanMessage(content="Historical message 2"),
            AIMessage(content="Historical response 2"),
            HumanMessage(content="Historical message 3"),
            AIMessage(content="Historical response 3"),
            HumanMessage(content="Recent message"),
            AIMessage(content="Recent response"),
        ]
    }


def _build_request(state: dict[str, Any]) -> Any:
    from langchain.agents.middleware import ModelRequest

    return ModelRequest(
        model=None,
        tools=[],
        system_prompt=None,
        response_format=None,
        messages=state["messages"],
        state=state,
        runtime=None,
    )


def test_middleware_builds_and_forwards_compressed_model_request() -> None:
    compression_service = StubCompressionService()
    inspector = StubContextInspector()
    handler = StubHandler()

    middleware = ContextCompressionMiddleware(
        compression_service=compression_service,
        inspector=inspector,
    )

    state = _build_state()
    request = _build_request(state)

    response = middleware.wrap_model_call(
        request,
        handler,
    )

    assert isinstance(response, ModelResponse)

    assert compression_service.prepare_called is True
    assert compression_service.build_called is True
    assert handler.called is True

    assert handler.request is not None
    assert len(handler.request.messages) == 3

    assert (
        handler.request.messages[0].content == "Historical context has been compressed."
    )


def test_middleware_does_not_replace_persisted_state_messages() -> None:
    compression_service = StubCompressionService()
    inspector = StubContextInspector()
    handler = StubHandler()

    middleware = ContextCompressionMiddleware(
        compression_service=compression_service,
        inspector=inspector,
    )

    state = _build_state()
    original_messages = list(state["messages"])

    request = _build_request(state)

    middleware.wrap_model_call(
        request,
        handler,
    )

    assert state["messages"] == original_messages
    assert len(state["messages"]) == len(original_messages)


def test_middleware_does_not_mutate_original_model_request() -> None:
    compression_service = StubCompressionService()
    inspector = StubContextInspector()
    handler = StubHandler()

    middleware = ContextCompressionMiddleware(
        compression_service=compression_service,
        inspector=inspector,
    )

    state = _build_state()
    request = _build_request(state)

    original_request_messages = list(request.messages)

    middleware.wrap_model_call(
        request,
        handler,
    )

    assert request.messages == original_request_messages
    assert len(request.messages) == 8

    assert handler.request is not None
    assert len(handler.request.messages) == 3


def test_middleware_handles_ineligible_compression_without_overriding_request() -> None:
    class IneligibleCompressionService:
        def __init__(self) -> None:
            self.prepare_called = False
            self.build_called = False

        def prepare(
            self,
            state: dict[str, Any],
            metrics: dict[str, Any],
        ) -> Any:
            self.prepare_called = True

            class Result:
                eligible = False
                reason = "compression_not_required_or_blocked"
                original_message_count = len(state["messages"])
                compressed_message_count = 0
                preserved_message_count = len(state["messages"])

            return Result()

        def build_compressed_messages(
            self,
            result: Any,
        ) -> list[Any]:
            self.build_called = True
            return []

    compression_service = IneligibleCompressionService()
    inspector = StubContextInspector()
    handler = StubHandler()

    middleware = ContextCompressionMiddleware(
        compression_service=compression_service,
        inspector=inspector,
    )

    state = _build_state()
    request = _build_request(state)

    middleware.wrap_model_call(
        request,
        handler,
    )

    assert compression_service.prepare_called is True
    assert compression_service.build_called is False
    assert handler.called is True

    assert handler.request is not None
    assert handler.request.messages == request.messages
