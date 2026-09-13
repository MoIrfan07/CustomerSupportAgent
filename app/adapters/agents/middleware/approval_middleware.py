from __future__ import annotations

import logging
from uuid import uuid4

from langchain.agents.middleware import AgentMiddleware
from langgraph.types import interrupt

from app.application.approval_context import (
    get_approval_customer_id,
    get_approval_registry,
    get_approval_role,
    get_approval_thread_id,
    get_approval_username,
)


logger = logging.getLogger(__name__)


class CustomerApprovalMiddleware(AgentMiddleware):
    """
    Middleware responsible for pausing sensitive operations
    until human approval is received.

    The application-level approval registry bridges the HTTP
    approval endpoint and the LangGraph interrupt/resume lifecycle.

    The same approval ID is reused when LangGraph resumes so
    an approval cannot accidentally turn into a new approval
    request during replay.
    """

    SENSITIVE_TOOLS = {
        "refund_payment",
        "cancel_order",
    }

    async def awrap_tool_call(
        self,
        request,
        handler,
    ):
        """
        Intercept every tool call before the tool actually runs.
        """

        tool_name = request.tool_call["name"]
        tool_call_id = request.tool_call.get("id")

        # Normal tools do not require human approval.
        if tool_name not in self.SENSITIVE_TOOLS:
            return await handler(request)

        args = request.tool_call.get(
            "args",
            {},
        )

        customer_id = args.get(
            "customer_id",
            "Unknown",
        )

        payment_id = args.get(
            "payment_id",
            "Unknown",
        )

        order_id = args.get(
            "order_id",
            "Unknown",
        )

        registry = get_approval_registry()

        username = get_approval_username()
        role = get_approval_role()
        authenticated_customer_id = get_approval_customer_id()
        thread_id = get_approval_thread_id()

        resolved_thread_id = thread_id or "unknown"

        # ---------------------------------------------------------
        # Find an existing approval for this exact tool call.
        #
        # This lookup intentionally includes approvals that already
        # have a decision. The API stores the decision BEFORE
        # Command(resume=...) is called.
        # ---------------------------------------------------------
        approval = None

        if registry is not None:
            approval = registry.find_for_tool_call(
                thread_id=resolved_thread_id,
                tool_name=tool_name,
                tool_call_id=tool_call_id,
            )

        # ---------------------------------------------------------
        # Create the application-level approval only when this is
        # the initial execution of the tool call.
        # ---------------------------------------------------------
        if approval is None:
            approval_id = str(uuid4())

            if registry is not None:
                approval = registry.create(
                    approval_id=approval_id,
                    username=username,
                    role=role,
                    customer_id=(
                        authenticated_customer_id
                        or (None if customer_id == "Unknown" else customer_id)
                    ),
                    thread_id=resolved_thread_id,
                    tool_name=tool_name,
                    tool_call_id=tool_call_id,
                )
        else:
            approval_id = approval.approval_id

        logger.info(
            "APPROVAL REQUEST | "
            "approval_id=%s | "
            "user=%s | "
            "role=%s | "
            "tool=%s | "
            "tool_call_id=%s | "
            "thread_id=%s",
            approval_id,
            username,
            role,
            tool_name,
            tool_call_id,
            resolved_thread_id,
        )

        # ---------------------------------------------------------
        # Build the approval message.
        # ---------------------------------------------------------
        if tool_name == "refund_payment":
            approval_message = (
                "\n"
                "========================================\n"
                "        HUMAN APPROVAL REQUIRED\n"
                "========================================\n"
                f"Approval ID: {approval_id}\n"
                f"Action: {tool_name}\n"
                f"Customer: {customer_id}\n"
                f"Payment: {payment_id}\n"
                "\n"
                "This operation is sensitive.\n"
                "Do you approve this action?\n"
                "========================================\n"
            )

        elif tool_name == "cancel_order":
            approval_message = (
                "\n"
                "========================================\n"
                "        HUMAN APPROVAL REQUIRED\n"
                "========================================\n"
                f"Approval ID: {approval_id}\n"
                f"Action: {tool_name}\n"
                f"Customer: {customer_id}\n"
                f"Order: {order_id}\n"
                "\n"
                "This operation is sensitive.\n"
                "Do you approve this action?\n"
                "========================================\n"
            )

        else:
            approval_message = "Human approval is required for this operation."

        # ---------------------------------------------------------
        # Pause/resume LangGraph.
        #
        # On the first execution this raises an interrupt.
        #
        # On resume, LangGraph re-enters this middleware and the
        # existing approval record is found above. interrupt()
        # then returns the decision supplied through Command().
        # ---------------------------------------------------------
        approved = interrupt(approval_message)

        logger.info(
            "APPROVAL RESUMED | "
            "approval_id=%s | "
            "approved=%s | "
            "tool=%s | "
            "tool_call_id=%s | "
            "thread_id=%s",
            approval_id,
            approved,
            tool_name,
            tool_call_id,
            resolved_thread_id,
        )

        # ---------------------------------------------------------
        # NOT APPROVED
        # ---------------------------------------------------------
        if not approved:
            if registry is not None:
                registry.remove(approval_id)

            logger.info(
                "APPROVAL REJECTED | approval_id=%s | tool=%s | thread_id=%s",
                approval_id,
                tool_name,
                resolved_thread_id,
            )

            return {
                "success": False,
                "message": ("The requested action was rejected by the user."),
            }

        # ---------------------------------------------------------
        # APPROVED
        #
        # Execute the actual sensitive tool only now.
        # ---------------------------------------------------------
        result = await handler(request)

        # Consume the approval only after the sensitive operation
        # has successfully returned.
        if registry is not None:
            registry.remove(approval_id)

        logger.info(
            "APPROVAL EXECUTED | "
            "approval_id=%s | "
            "tool=%s | "
            "tool_call_id=%s | "
            "thread_id=%s",
            approval_id,
            tool_name,
            tool_call_id,
            resolved_thread_id,
        )

        return result
