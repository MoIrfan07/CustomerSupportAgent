import logging
from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage


logger = logging.getLogger(__name__)


class CustomerAuthorizationMiddleware(AgentMiddleware):
    """
    Enforces authorization for customer-support business tools.

    Business tools are controlled by user role and, for customer users,
    by ownership of the authenticated customer ID.

    Deep Agents framework tools are handled separately because they are
    internal agent capabilities rather than customer-support business
    operations.
    """

    # ---------------------------------------------------------
    # BUSINESS TOOL AUTHORIZATION
    # ---------------------------------------------------------

    ALLOWED_TOOLS = {
        "manager": {
            "get_customer",
            "list_customers",
            "get_customer_orders",
            "get_customer_invoices",
            "get_customer_payments",
            "get_customer_tickets",
            "cancel_order",
            "refund_payment",
        },
        "support": {
            "get_customer",
            "list_customers",
            "get_customer_orders",
            "get_customer_invoices",
            "get_customer_payments",
            "get_customer_tickets",
        },
        "user": {
            "get_customer",
            "get_customer_orders",
            "get_customer_invoices",
            "get_customer_payments",
            "get_customer_tickets",
        },
        "customer": {
            "get_customer",
            "get_customer_orders",
            "get_customer_invoices",
            "get_customer_payments",
            "get_customer_tickets",
        },
        "guest": set(),
    }

    # ---------------------------------------------------------
    # DEEP AGENTS INTERNAL TOOLS
    # ---------------------------------------------------------

    INTERNAL_TOOLS = {
        "task",
        "write_todos",
        "ls",
        "read_file",
        "write_file",
        "edit_file",
        "glob",
        "grep",
    }

    # ---------------------------------------------------------
    # CUSTOMER OWNERSHIP ENFORCEMENT
    # ---------------------------------------------------------

    CUSTOMER_ID_TOOLS = {
        "get_customer",
        "get_customer_orders",
        "get_customer_invoices",
        "get_customer_payments",
        "get_customer_tickets",
        "cancel_order",
        "refund_payment",
    }

    def __init__(
        self,
        user_role: str,
        username: str = "unknown",
        customer_id: str | None = None,
    ):
        super().__init__()

        self.user_role = user_role
        self.username = username
        self.customer_id = customer_id

    # ---------------------------------------------------------
    # MODEL REQUEST LOGGING
    # ---------------------------------------------------------

    def before_model(
        self,
        state: dict[str, Any],
        runtime: Any,
    ):
        logger.info(
            "[SECURITY] REQUEST | user=%s role=%s customer_id=%s",
            self.username,
            self.user_role,
            self.customer_id,
        )

        return None

    # ---------------------------------------------------------
    # TOOL AUTHORIZATION
    # ---------------------------------------------------------

    async def awrap_tool_call(
        self,
        request,
        handler,
    ):
        tool_name = request.tool_call.get(
            "name",
            "unknown",
        )

        tool_args = request.tool_call.get(
            "args",
            {},
        )

        # -----------------------------------------------------
        # AUTHENTICATED IDENTITY VALIDATION
        # -----------------------------------------------------
        #
        # Username and role are required for every authenticated
        # business-tool request.
        #
        # customer_id is intentionally NOT required here because
        # manager/support users legitimately have customer_id=None.
        #
        if not self.username or self.username == "unknown":
            logger.warning(
                "[SECURITY] ACCESS DENIED | missing username | tool=%s",
                tool_name,
            )

            return ToolMessage(
                content="You don't have access.",
                tool_call_id=request.tool_call["id"],
                status="error",
            )

        if not self.user_role:
            logger.warning(
                "[SECURITY] ACCESS DENIED | missing role | user=%s tool=%s",
                self.username,
                tool_name,
            )

            return ToolMessage(
                content="You don't have access.",
                tool_call_id=request.tool_call["id"],
                status="error",
            )

        # -----------------------------------------------------
        # INTERNAL DEEP AGENTS TOOLS
        # -----------------------------------------------------
        #
        # These tools are framework capabilities rather than
        # customer-support business operations. They therefore
        # do not participate in business authorization.
        #
        if tool_name in self.INTERNAL_TOOLS:
            logger.info(
                "[SECURITY] INTERNAL TOOL | user=%s role=%s customer_id=%s tool=%s",
                self.username,
                self.user_role,
                self.customer_id,
                tool_name,
            )

            return await handler(request)

        # -----------------------------------------------------
        # BUSINESS TOOL ROLE AUTHORIZATION
        # -----------------------------------------------------

        role_tools = self.ALLOWED_TOOLS.get(
            self.user_role,
            set(),
        )

        if tool_name not in role_tools:
            logger.warning(
                "[SECURITY] ACCESS DENIED | user=%s role=%s customer_id=%s tool=%s",
                self.username,
                self.user_role,
                self.customer_id,
                tool_name,
            )

            return ToolMessage(
                content=("You don't have access. Please login to continue."),
                tool_call_id=request.tool_call["id"],
                status="error",
            )

        # -----------------------------------------------------
        # CUSTOMER OWNERSHIP AUTHORIZATION
        # -----------------------------------------------------
        if self.user_role == "customer":
            # Customer users MUST have an authenticated
            # customer ID associated with their session.
            if not self.customer_id:
                logger.warning(
                    "[SECURITY] CUSTOMER ACCESS DENIED | "
                    "user=%s has no authenticated customer_id | tool=%s",
                    self.username,
                    tool_name,
                )

                return ToolMessage(
                    content="You don't have access.",
                    tool_call_id=request.tool_call["id"],
                    status="error",
                )

            # Customer ownership applies only to tools that
            # operate on a specific customer.
            if tool_name in self.CUSTOMER_ID_TOOLS:
                requested_customer_id = tool_args.get("customer_id")

                if (
                    not requested_customer_id
                    or requested_customer_id.strip().upper()
                    != self.customer_id.strip().upper()
                ):
                    logger.warning(
                        "[SECURITY] OWNERSHIP DENIED | "
                        "user=%s role=%s owned_customer_id=%s "
                        "requested_customer_id=%s tool=%s",
                        self.username,
                        self.user_role,
                        self.customer_id,
                        requested_customer_id,
                        tool_name,
                    )

                    return ToolMessage(
                        content=("You don't have access to this customer's information."),
                        tool_call_id=request.tool_call["id"],
                        status="error",
                    )
        # -----------------------------------------------------
        # BUSINESS TOOL AUTHORIZED
        # -----------------------------------------------------

        logger.info(
            "[SECURITY] ACCESS GRANTED | user=%s role=%s customer_id=%s tool=%s",
            self.username,
            self.user_role,
            self.customer_id,
            tool_name,
        )

        return await handler(request)
    
    