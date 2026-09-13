from __future__ import annotations

import logging
from typing import Any

from langchain.agents.middleware import AgentMiddleware

from app.application.context_inspector import ContextInspector


logger = logging.getLogger(__name__)


class ContextInspectionMiddleware(AgentMiddleware):
    """
    Observe the agent's state and record context metrics.

    This middleware is intentionally observation-only.

    It does not:
        - modify messages
        - remove context
        - summarize context
        - alter tool calls
        - alter tool results
        - interrupt execution
        - change the agent response
    """

    def __init__(
        self,
        inspector: ContextInspector | None = None,
    ) -> None:
        super().__init__()

        self.inspector = inspector if inspector is not None else ContextInspector()

    def before_model(
        self,
        state: dict[str, Any],
        runtime: Any,
    ) -> None:
        """
        Inspect the state immediately before model execution.
        """

        try:
            metrics = self.inspector.inspect(state)

            logger.info(
                "CONTEXT OBSERVATION | "
                "message_count=%s | "
                "approx_tokens=%s | "
                "tool_calls=%s | "
                "tool_results=%s | "
                "interrupts=%s",
                metrics["message_count"],
                metrics["approximate_tokens"],
                metrics["tool_call_count"],
                metrics["tool_result_count"],
                metrics["interrupt_count"],
            )

        except Exception:
            # Context inspection must never break the agent.
            logger.exception("CONTEXT OBSERVATION FAILED | continuing agent execution")

        return None
