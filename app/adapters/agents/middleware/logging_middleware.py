from datetime import datetime
from typing import Any

import logging

from langchain.agents.middleware import AgentMiddleware

from app.observability import get_request_id


logger = logging.getLogger(__name__)


class CustomerSupportLoggingMiddleware(AgentMiddleware):
    """
    Middleware for logging model requests and responses
    in the customer support agent.
    """

    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _request_id(self) -> str:
        return get_request_id() or "unknown"

    # ---------------------------------------------------------
    # BEFORE MODEL
    # ---------------------------------------------------------

    def before_model(
        self,
        state: dict[str, Any],
        runtime: Any,
    ):
        """
        Log the request before it is sent to the model.
        """

        messages = state.get("messages", [])
        request_id = self._request_id()

        logger.info(
            "MODEL REQUEST | request_id=%s | timestamp=%s | messages=%s",
            request_id,
            self._timestamp(),
            len(messages),
        )

        if messages:
            last_message = messages[-1]

            logger.info(
                "MODEL REQUEST | request_id=%s | last_message_type=%s",
                request_id,
                getattr(
                    last_message,
                    "type",
                    "unknown",
                ),
            )

            content = getattr(
                last_message,
                "content",
                "",
            )

            logger.info(
                "MODEL REQUEST | request_id=%s | content_preview=%s",
                request_id,
                str(content)[:300],
            )

        return None

    # ---------------------------------------------------------
    # AFTER MODEL
    # ---------------------------------------------------------

    def after_model(
        self,
        state: dict[str, Any],
        runtime: Any,
    ):
        """
        Log the response after it is received from the model.
        """

        messages = state.get("messages", [])
        request_id = self._request_id()

        logger.info(
            "MODEL RESPONSE | request_id=%s | timestamp=%s | messages=%s",
            request_id,
            self._timestamp(),
            len(messages),
        )

        if messages:
            last_message = messages[-1]

            logger.info(
                "MODEL RESPONSE | request_id=%s | response_type=%s",
                request_id,
                getattr(
                    last_message,
                    "type",
                    "unknown",
                ),
            )

            content = getattr(
                last_message,
                "content",
                "",
            )

            logger.info(
                "MODEL RESPONSE | request_id=%s | generated=%s",
                request_id,
                bool(content),
            )

        return None
