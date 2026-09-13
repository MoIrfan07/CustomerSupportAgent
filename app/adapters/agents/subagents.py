from app.config import QWEN_LANGUAGE
from app.llm import qwen_model
import logging

from app.adapters.agents.middleware.security_middleware import (
    CustomerAuthorizationMiddleware,
)
from app.adapters.agents.middleware.approval_middleware import (
    CustomerApprovalMiddleware,
)
from app.adapters.agents.middleware.subagent_logging_middleware import (
    SubagentLoggingMiddleware,
)

def build_subagents(
    tools,
    user_role: str,
    username: str = "unknown",
    customer_id: str | None = None,
):
    tool_map = {tool.name: tool for tool in tools}

    subagents = []

    # CUSTOMER SPECIALIST

    customer_tools = [
        tool_map["get_customer"],
        tool_map["get_customer_orders"],
    ]

    # list_customers is a staff-facing capability (manager/support).
    # It is still handed to the specialist for every role: the
    # CustomerAuthorizationMiddleware enforces per-role access at
    # the tool-call layer, so customers/guests attempting to use it
    # are denied there rather than by omitting it here.
    if "list_customers" in tool_map:
        customer_tools.append(tool_map["list_customers"])

    customer_specialist = {
        "name": "customer_specialist",
        "description": (
            "Handles customer profiles, customer "
            "identity resolution, customer status, "
            "contact information, account information, "
            "and customer orders."
        ),
        "system_prompt": f"""
You are the Customer Specialist.

The authenticated customer's ID is:

{customer_id}

AUTHENTICATED USER CONTEXT:

- The authenticated user's role is: {user_role}
- The authenticated username is: {username}
- If the role is "customer", customer_id is the customer's
  authenticated and authoritative customer ID.
- If the role is "manager" or "support", customer_id may be None.
  This is expected because staff users are not restricted to one
  customer account.
- Managers and support staff may retrieve a specific customer's
  information when their role is authorized to access it.
- Never interpret customer_id=None for a manager or support user
  as meaning the user is unauthenticated or has no access.
- Authentication and role authorization are enforced by the
  application and CustomerAuthorizationMiddleware.

Your responsibilities:

- Retrieve the authenticated customer's profile.
- Retrieve the authenticated customer's orders.
- Check order status.
- Determine which orders are active, processing,
  delivered, cancelled, or otherwise unavailable
  for cancellation.
- If a list_customers tool is available to you and the
  requester is authorized staff (manager/support), you
  may list all customers when asked to. If the tool call
  is denied, tell the user they don't have access rather
  than inventing customer data.

CUSTOMER ID RULES:

- If the authenticated user is a customer, ALWAYS use
  the authenticated customer ID above when accessing
  customer data.
- Do NOT ask the customer to provide their customer ID,
  name, or email.
- If the user says "my orders", "my account", "my payments",
  "my invoices", "my tickets", etc., use the authenticated
  customer ID automatically.
- Never substitute another customer ID supplied by the user.
- If the user explicitly asks for another customer's data,
  do not access it.
- The authorization middleware is the final enforcement
  layer for customer ownership.

CUSTOMER ID FORMAT:

The actual customer ID includes the "CUST-" prefix.

For example:

- 1001 → CUST-1001
- 1002 → CUST-1002

However, when the user is authenticated as a customer,
prefer the authenticated customer ID above rather than
relying on an ID supplied in the conversation.

Always respond in {QWEN_LANGUAGE}.

Use only the tools provided to you.

Never invent customer information.

Tool results are the source of truth.

If the authenticated customer's information cannot be
retrieved, clearly explain that the information could
not be retrieved.

When the user refers to an order such as "first order",
"second order", or "the monitor", use the authenticated
customer's actual order records to resolve the reference.

Return a concise factual summary to the main agent.
""",
        "tools": customer_tools,
        "model": qwen_model,
        "middleware": [
            CustomerAuthorizationMiddleware(
                user_role=user_role,
                username=username,
                customer_id=customer_id,
            ),
            SubagentLoggingMiddleware(agent_name="customer_specialist"),
            
         ],
    }

    subagents.append(customer_specialist)

    # BILLING SPECIALIST...............................................................

    billing_tools = [
        tool_map["get_customer_invoices"],
        tool_map["get_customer_payments"],
    ]

    billing_specialist = {
        "name": "billing_specialist",
        "description": (
            "Handles customer invoices, payments, "
            "billing status, payment status, and "
            "billing-related investigations."
        ),
        "system_prompt": f"""
You are the Billing Specialist.

Your responsibilities:

- Investigate invoices.
- Investigate payments.
- Check payment status.
- Check invoice status.
- Investigate billing issues.
- Determine whether a payment is pending,
  completed, failed, or otherwise stated by
  the available records.

Always respond in {QWEN_LANGUAGE}.

Use only the tools provided to you.

Never invent financial information.

Never invent a reason for a payment status.

If the records do not contain a reason,
explicitly say that the reason is unavailable.

Monetary amounts returned by tools are already
in the major currency unit.

Never divide amounts by 100 unless a tool
explicitly states that the value is stored
in minor units.

Tool results are the source of truth.

Return a concise factual summary to the main agent.
""",
        "tools": billing_tools,
        "model": qwen_model,
        "middleware": [
            CustomerAuthorizationMiddleware(
                user_role=user_role,
                username=username,
                customer_id=customer_id,
            ),
            SubagentLoggingMiddleware(),
        ],
    }

    subagents.append(billing_specialist)

    # TECHNICAL SPECIALIST

    technical_tools = [
        tool_map["get_customer_tickets"],
    ]

    technical_specialist = {
        "name": "technical_specialist",
        "description": (
            "Handles support tickets, technical "
            "issues, incidents, troubleshooting, "
            "and customer support problems."
        ),
        "system_prompt": f"""
You are the Technical Support Specialist.

Your responsibilities:

- Investigate support tickets.
- Identify open or closed tickets.
- Review ticket priority.
- Review ticket subjects.
- Investigate technical issues.
- Summarize support incidents.

Always respond in {QWEN_LANGUAGE}.

Use only the tools provided to you.

Never invent technical information.

If the available ticket information does not
contain a cause or resolution, say that it
is unavailable.

Tool results are the source of truth.

Return a concise factual summary to the main agent.
""",
        "tools": technical_tools,
        "model": qwen_model,
        "middleware": [
            CustomerAuthorizationMiddleware(
                user_role=user_role,
                username=username,
                customer_id=customer_id,
            ),
            SubagentLoggingMiddleware(),
        ],
    }

    subagents.append(technical_specialist)

    # OPERATIONS SPECIALIST

    operations_tools = [
        tool_map["refund_payment"],
        tool_map["cancel_order"],
    ]

    if operations_tools:
        operations_specialist = {
            "name": "operations_specialist",
            "description": (
                "Handles customer service operations "
                "such as payment refunds and order "
                "cancellations. Only perform actions "
                "when the requested operation is "
                "actually supported and authorized."
            ),
            "system_prompt": f"""
You are the Customer Operations Specialist.

Your responsibilities:

- Process payment refunds when authorized.
- Cancel orders when authorized.
- Verify the relevant customer and order/payment
  before performing an operation.
- Determine whether an order is eligible for
  cancellation based on the actual order status.
- Never cancel an order that is already delivered,
  already cancelled, or otherwise not eligible
  according to the tool result.
- Never refund a payment unless the payment is
  eligible according to the tool result.
- Never invent operational information.

Always respond in {QWEN_LANGUAGE}.

Sensitive operations require the main agent's
authorization and human approval middleware.

Do not bypass authorization or approval.

If an operation cannot be performed, clearly
explain why.

Tool results are the source of truth.

Monetary amounts must be reported exactly as
returned by the tools.

Return a concise factual result to the main agent.
""",
            "tools": operations_tools,
            "model": qwen_model,
            "middleware": [
                CustomerAuthorizationMiddleware(
                    user_role=user_role,
                    username=username,
                    customer_id=customer_id,
                ),
                CustomerApprovalMiddleware(),
                SubagentLoggingMiddleware(),
            ],
        }

        subagents.append(operations_specialist)

    return subagents