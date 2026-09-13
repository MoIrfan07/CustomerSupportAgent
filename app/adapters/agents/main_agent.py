from pathlib import Path
from typing import Any

from deepagents import create_deep_agent
from langgraph.checkpoint.memory import InMemorySaver

from app.adapters.agents.middleware.logging_middleware import (
    CustomerSupportLoggingMiddleware,
)

from app.adapters.agents.middleware.context_compression_middleware import (
    ContextCompressionMiddleware,
)


from app.adapters.agents.middleware.subagent_logging_middleware import (
    SubagentLoggingMiddleware,
)

from app.adapters.agents.middleware.context_inspection_middleware import (
    ContextInspectionMiddleware,
)

from app.adapters.agents.middleware.security_middleware import (
    CustomerAuthorizationMiddleware,
)

from app.adapters.agents.middleware.approval_middleware import (
    CustomerApprovalMiddleware,
)

from app.config import QWEN_LANGUAGE
from app.llm import qwen_model

from app.adapters.agents.subagents import build_subagents


PROMPT_PATH = Path(__file__).resolve().parent.parent.parent.parent / "prompts" / "main_agent.md"


def load_system_prompt(
    username: str,
    user_role: str,
    customer_id: str | None,
) -> str:
    """Load and populate the main-agent system prompt."""

    prompt_template = PROMPT_PATH.read_text(
        encoding="utf-8",
    )

    return prompt_template.format(
        USERNAME=username,
        USER_ROLE=user_role,
        CUSTOMER_ID=customer_id,
        QWEN_LANGUAGE=QWEN_LANGUAGE,
    )


async def create_customer_support_agent(
    tools: list[Any],
    user_role: str,
    username: str = "unknown",
    customer_id: str | None = None,
    checkpointer: Any | None = None,
):
    """
    Create the main customer-support Deep Agent.

    The checkpointer is injected by the caller so that
    conversation persistence is controlled by the
    application infrastructure rather than by the
    agent implementation itself.
    """

    if checkpointer is None:
        checkpointer = InMemorySaver()

    # Build specialist subagents using the MCP tools
    # that were initialized by the application.
    subagents = build_subagents(
        tools,
        user_role,
        username,
        customer_id,
    )

    agent = create_deep_agent(
        model=qwen_model,
        system_prompt=load_system_prompt(
            username=username,
            user_role=user_role,
            customer_id=customer_id,
        ),
        # Do NOT give MCP business tools directly
        # to the main agent.
        #
        # The main agent delegates through "task".
        # Specialists receive the appropriate MCP tools.
        subagents=subagents,
        middleware=[
            CustomerSupportLoggingMiddleware(),
            SubagentLoggingMiddleware(),
            ContextInspectionMiddleware(),
            ContextCompressionMiddleware(),
            CustomerAuthorizationMiddleware(
                user_role=user_role,
                username=username,
                customer_id=customer_id,
            ),
            CustomerApprovalMiddleware(),
        ],
        checkpointer=checkpointer,
    )

    return agent
