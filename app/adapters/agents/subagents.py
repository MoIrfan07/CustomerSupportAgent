from pathlib import Path
from typing import Any

from app.adapters.agents.middleware.approval_middleware import (
    CustomerApprovalMiddleware,
)
from app.adapters.agents.prompt_loader import render_prompt_file
from app.adapters.agents.middleware.logging_middleware import (
    SubagentLoggingMiddleware,
)
from app.adapters.agents.middleware.security_middleware import (
    CustomerAuthorizationMiddleware,
)
from app.config import QWEN_LANGUAGE
from app.llm import qwen_model


PROMPTS_PATH = Path(__file__).resolve().parents[3] / "prompts"


def load_subagent_prompt(
    filename: str,
    *,
    username: str,
    user_role: str,
    customer_id: str | None,
) -> str:
    prompt_path = PROMPTS_PATH / filename
    if not prompt_path.is_file():
        raise FileNotFoundError(f"Specialist prompt was not found: {prompt_path}")

    return render_prompt_file(
        prompt_path,
        username=username,
        user_role=user_role,
        customer_id=customer_id,
        qwen_language=QWEN_LANGUAGE,
    )


def build_subagents(
    tools: list[Any],
    user_role: str,
    username: str = "unknown",
    customer_id: str | None = None,
) -> list[dict[str, Any]]:
    tool_map = {tool.name: tool for tool in tools}

    customer_tools = [
        tool_map["get_customer"],
        tool_map["get_customer_orders"],
    ]
    if "list_customers" in tool_map:
        customer_tools.append(tool_map["list_customers"])

    authorization = CustomerAuthorizationMiddleware(
        user_role=user_role,
        username=username,
        customer_id=customer_id,
    )

    subagents: list[dict[str, Any]] = [
        {
            "name": "customer_specialist",
            "description": "Handles customer profiles, identity, status, contact information, and orders.",
            "system_prompt": load_subagent_prompt(
                "customer_specialist.md",
                username=username,
                user_role=user_role,
                customer_id=customer_id,
            ),
            "tools": customer_tools,
            "model": qwen_model,
            "middleware": [
                authorization,
                SubagentLoggingMiddleware(agent_name="customer_specialist"),
            ],
        },
        {
            "name": "billing_specialist",
            "description": "Handles invoices, payments, billing status, and billing investigations.",
            "system_prompt": load_subagent_prompt(
                "billing_specialist.md",
                username=username,
                user_role=user_role,
                customer_id=customer_id,
            ),
            "tools": [
                tool_map["get_customer_invoices"],
                tool_map["get_customer_payments"],
            ],
            "model": qwen_model,
            "middleware": [
                CustomerAuthorizationMiddleware(
                    user_role=user_role,
                    username=username,
                    customer_id=customer_id,
                ),
                SubagentLoggingMiddleware(agent_name="billing_specialist"),
            ],
        },
        {
            "name": "technical_specialist",
            "description": "Handles support tickets, technical issues, incidents, and troubleshooting.",
            "system_prompt": load_subagent_prompt(
                "technical_specialist.md",
                username=username,
                user_role=user_role,
                customer_id=customer_id,
            ),
            "tools": [tool_map["get_customer_tickets"]],
            "model": qwen_model,
            "middleware": [
                CustomerAuthorizationMiddleware(
                    user_role=user_role,
                    username=username,
                    customer_id=customer_id,
                ),
                SubagentLoggingMiddleware(agent_name="technical_specialist"),
            ],
        },
    ]

    operations_tools = [
        tool_map["refund_payment"],
        tool_map["cancel_order"],
    ]
    if operations_tools:
        subagents.append(
            {
                "name": "operations_specialist",
                "description": "Handles authorized payment refunds and order cancellations.",
                "system_prompt": load_subagent_prompt(
                    "operations_specialist.md",
                    username=username,
                    user_role=user_role,
                    customer_id=customer_id,
                ),
                "tools": operations_tools,
                "model": qwen_model,
                "middleware": [
                    CustomerAuthorizationMiddleware(
                        user_role=user_role,
                        username=username,
                        customer_id=customer_id,
                    ),
                    CustomerApprovalMiddleware(),
                    SubagentLoggingMiddleware(agent_name="operations_specialist"),
                ],
            }
        )

    return subagents
