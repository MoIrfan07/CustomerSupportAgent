from langchain.agents.middleware import (
    AgentMiddleware,
)

from langgraph.types import interrupt


class CustomerApprovalMiddleware(
    AgentMiddleware
):

    SENSITIVE_TOOLS = {
        "refund_payment",
        "cancel_order",
    }

    async def awrap_tool_call(
        self,
        request,
        handler,
    ):

        tool_name = request.tool_call[
            "name"
        ]

        # ====================================
        # NORMAL TOOL
        # ====================================

        if tool_name not in self.SENSITIVE_TOOLS:

            return await handler(
                request
            )

        # ====================================
        # TOOL ARGUMENTS
        # ====================================

        args = request.tool_call.get(
            "args",
            {}
        )

        customer_id = args.get(
            "customer_id",
            "Unknown"
        )

        payment_id = args.get(
            "payment_id",
            "Unknown"
        )

        order_id = args.get(
            "order_id",
            "Unknown"
        )

        # ====================================
        # REFUND APPROVAL
        # ====================================

        if tool_name == "refund_payment":

            approval_message = (
                "\n"
                "========================================\n"
                "        HUMAN APPROVAL REQUIRED\n"
                "========================================\n"
                f"Action: {tool_name}\n"
                f"Customer: {customer_id}\n"
                f"Payment: {payment_id}\n"
                "\n"
                "This operation is sensitive.\n"
                "Do you approve this action?\n"
                "========================================\n"
            )

        # ====================================
        # ORDER CANCELLATION APPROVAL
        # ====================================

        elif tool_name == "cancel_order":

            approval_message = (
                "\n"
                "========================================\n"
                "        HUMAN APPROVAL REQUIRED\n"
                "========================================\n"
                f"Action: {tool_name}\n"
                f"Customer: {customer_id}\n"
                f"Order: {order_id}\n"
                "\n"
                "This operation is sensitive.\n"
                "Do you approve this action?\n"
                "========================================\n"
            )

        else:

            approval_message = (
                "Human approval is required "
                "for this operation."
            )

        # ====================================
        # PAUSE GRAPH
        # ====================================

        approved = interrupt(
            approval_message
        )

        # ====================================
        # REJECTED
        # ====================================

        if not approved:

            return {
                "success": False,
                "message": (
                    "The requested action "
                    "was rejected by the user."
                ),
            }

        # ====================================
        # APPROVED
        # ====================================

        return await handler(
            request
        )