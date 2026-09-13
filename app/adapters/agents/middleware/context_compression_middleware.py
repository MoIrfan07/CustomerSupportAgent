from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware import (
    AgentMiddleware,
    ModelRequest,
    ModelResponse,
)

from app.application.context_compression_service import (
    ContextCompressionService,
)
from app.application.context_inspector import ContextInspector

logger = logging.getLogger(__name__)


class ContextCompressionMiddleware(AgentMiddleware):
    """
    Compress historical context for the model request without modifying
    persisted agent state.

    The middleware:

        1. Inspects the current agent state.
        2. Determines whether compression is appropriate.
        3. Builds a compressed message list when eligible.
        4. Creates a model request override containing those messages.
        5. Sends the overridden request to the model.
        6. Leaves the original LangGraph state unchanged.

    The same behavior is implemented for both synchronous and
    asynchronous model execution.

    This separation is intentional:

        persisted state
            !=
        model-visible context

    The persisted state remains authoritative for checkpointing and
    future execution, while the model can receive a smaller context.
    """

    def __init__(
        self,
        compression_service: ContextCompressionService | None = None,
        inspector: ContextInspector | None = None,
    ) -> None:
        super().__init__()

        self.compression_service = (
            compression_service
            if compression_service is not None
            else ContextCompressionService()
        )

        self.inspector = inspector if inspector is not None else ContextInspector()

    def _prepare_compressed_request(
        self,
        request: ModelRequest,
    ) -> ModelRequest:
        """
        Prepare a model request with compressed messages when eligible.

        This method does not mutate the original request or persisted
        LangGraph state.
        """
        state = request.state

        metrics = self.inspector.inspect(state)

        result = self.compression_service.prepare(
            state,
            metrics,
        )

        if not result.eligible:
            logger.info(
                "CONTEXT COMPRESSION | "
                "eligible=false | "
                "reason=%s | "
                "original_messages=%s | "
                "compression_candidates=%s | "
                "preserved_messages=%s | "
                "model_visible_messages=%s",
                result.reason,
                result.original_message_count,
                result.compressed_message_count,
                result.preserved_message_count,
                result.original_message_count,
            )

            return request

        compressed_messages = self.compression_service.build_compressed_messages(result)

        original_message_count = result.original_message_count
        model_visible_message_count = len(compressed_messages)

        compression_ratio = (
            model_visible_message_count / original_message_count
            if original_message_count > 0
            else 1.0
        )

        reduction_ratio = 1.0 - compression_ratio if original_message_count > 0 else 0.0

        logger.info(
            "CONTEXT COMPRESSION | "
            "eligible=true | "
            "reason=%s | "
            "original_messages=%s | "
            "compression_candidates=%s | "
            "preserved_messages=%s | "
            "model_visible_messages=%s | "
            "compression_ratio=%.3f | "
            "reduction_ratio=%.3f",
            result.reason,
            original_message_count,
            result.compressed_message_count,
            result.preserved_message_count,
            model_visible_message_count,
            compression_ratio,
            reduction_ratio,
        )

        compressed_request = request.override(
            messages=compressed_messages,
        )

        logger.info(
            "CONTEXT COMPRESSION | "
            "model request override created | "
            "persisted_messages=%s | "
            "model_request_messages=%s",
            len(state.get("messages", [])),
            len(compressed_request.messages),
        )

        return compressed_request

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """
        Synchronous model-call middleware path.
        """
        try:
            compressed_request = self._prepare_compressed_request(request)

            return handler(compressed_request)

        except Exception:
            logger.exception(
                "CONTEXT COMPRESSION MIDDLEWARE FAILED | "
                "continuing with original model request"
            )

            return handler(request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[
            [ModelRequest],
            Awaitable[ModelResponse],
        ],
    ) -> ModelResponse:
        """
        Asynchronous model-call middleware path.

        This path is required when the agent is executed through
        ainvoke(), astream(), or another asynchronous LangGraph
        execution path.
        """
        try:
            compressed_request = self._prepare_compressed_request(request)

            return await handler(compressed_request)

        except Exception:
            logger.exception(
                "CONTEXT COMPRESSION MIDDLEWARE ASYNC FAILED | "
                "continuing with original model request"
            )

            return await handler(request)
