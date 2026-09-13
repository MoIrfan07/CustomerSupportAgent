from time import perf_counter
from typing import Any
import logging

from langchain.agents.middleware import AgentMiddleware

from app.observability import get_request_id


logger = logging.getLogger(__name__)


class SubagentLoggingMiddleware(AgentMiddleware):
    def __init__(self, agent_name: str = "unknown") -> None:
        self.agent_name = agent_name

    def _request_id(self) -> str:
        return get_request_id() or "unknown"

    async def awrap_tool_call(
        self,
        request: Any,
        handler: Any,
    ) -> Any:
        request_id = self._request_id()

        tool_call = getattr(request, "tool_call", {}) or {}
        tool_name = tool_call.get("name", "unknown")
        tool_args = tool_call.get("args", {})

        start = perf_counter()

        if tool_name == "task":
            subagent_type = tool_args.get("subagent_type", "unknown")

            logger.info(
                "[MAIN AGENT] SUBAGENT START | request_id=%s | subagent=%s",
                request_id,
                subagent_type,
            )

            try:
                result = await handler(request)

                duration_ms = (perf_counter() - start) * 1000

                logger.info(
                    "[MAIN AGENT] SUBAGENT END | request_id=%s | subagent=%s | duration_ms=%.2f",
                    request_id,
                    subagent_type,
                    duration_ms,
                )

                return result

            except Exception:
                duration_ms = (perf_counter() - start) * 1000

                logger.exception(
                    "[MAIN AGENT] SUBAGENT ERROR | request_id=%s | subagent=%s | duration_ms=%.2f",
                    request_id,
                    subagent_type,
                    duration_ms,
                )

                raise

        logger.info(
            "[SUBAGENT: %s] TOOL START | request_id=%s | tool=%s | args=%s",
            self.agent_name,
            request_id,
            tool_name,
            tool_args,
        )

        try:
            result = await handler(request)

            duration_ms = (perf_counter() - start) * 1000

            logger.info(
                "[SUBAGENT: %s] TOOL END | request_id=%s | tool=%s | duration_ms=%.2f",
                self.agent_name,
                request_id,
                tool_name,
                duration_ms,
            )

            return result

        except Exception:
            duration_ms = (perf_counter() - start) * 1000

            logger.exception(
                "[SUBAGENT: %s] TOOL ERROR | request_id=%s | tool=%s | duration_ms=%.2f",
                self.agent_name,
                request_id,
                tool_name,
                duration_ms,
            )

            raise
