import logging
from datetime import datetime
from time import perf_counter
from typing import Any

from langchain.agents.middleware import AgentMiddleware

from app.observability import get_request_id


logger = logging.getLogger(__name__)


class CustomerSupportLoggingMiddleware(AgentMiddleware):
    """Log model lifecycle events without recording message contents."""

    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _request_id(self) -> str:
        return get_request_id() or "unknown"

    def before_model(self, state: dict[str, Any], runtime: Any) -> None:
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
                "MODEL REQUEST | request_id=%s | last_message_type=%s | has_content=%s",
                request_id,
                getattr(last_message, "type", "unknown"),
                bool(getattr(last_message, "content", "")),
            )

    def after_model(self, state: dict[str, Any], runtime: Any) -> None:
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
                "MODEL RESPONSE | request_id=%s | response_type=%s | generated=%s",
                request_id,
                getattr(last_message, "type", "unknown"),
                bool(getattr(last_message, "content", "")),
            )


class SubagentLoggingMiddleware(AgentMiddleware):
    """Log specialist delegation and tool-call lifecycle events."""

    def __init__(self, agent_name: str = "unknown") -> None:
        self.agent_name = agent_name

    def _request_id(self) -> str:
        return get_request_id() or "unknown"

    @staticmethod
    def _tool_call(request: Any) -> dict[str, Any]:
        return getattr(request, "tool_call", {}) or {}

    async def awrap_tool_call(self, request: Any, handler: Any) -> Any:
        request_id = self._request_id()
        tool_call = self._tool_call(request)
        tool_name = str(tool_call.get("name", "unknown"))
        tool_args = tool_call.get("args", {}) or {}
        start = perf_counter()

        if tool_name == "task":
            scope = "[MAIN AGENT] SUBAGENT"
            subject = tool_args.get("subagent_type", "unknown")
        else:
            scope = f"[SUBAGENT: {self.agent_name}] TOOL"
            subject = tool_name

        logger.info(
            "%s START | request_id=%s | target=%s | arg_keys=%s",
            scope,
            request_id,
            subject,
            sorted(tool_args) if isinstance(tool_args, dict) else [],
        )

        try:
            result = await handler(request)
        except Exception:
            logger.exception(
                "%s ERROR | request_id=%s | target=%s | duration_ms=%.2f",
                scope,
                request_id,
                subject,
                (perf_counter() - start) * 1000,
            )
            raise

        logger.info(
            "%s END | request_id=%s | target=%s | duration_ms=%.2f",
            scope,
            request_id,
            subject,
            (perf_counter() - start) * 1000,
        )
        return result
