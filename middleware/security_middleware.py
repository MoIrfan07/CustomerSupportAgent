from typing import Any

from langchain.agents.middleware import (
    AgentMiddleware,
)


class CustomerAuthorizationMiddleware(
    AgentMiddleware
):

    def __init__(
        self,
        user_role: str = "support",
    ):

        super().__init__()

        self.user_role = user_role

    # ========================================
    # BEFORE MODEL
    # ========================================

    def before_model(
        self,
        state: dict[str, Any],
        runtime: Any,
    ):

        messages = state.get(
            "messages",
            []
        )

        if not messages:
            return None

        latest_message = messages[-1]

        content = str(
            getattr(
                latest_message,
                "content",
                ""
            )
        )

        print(
            "\n[SECURITY] "
            f"User role: {self.user_role}"
        )

        print(
            "[SECURITY] "
            "Request received."
        )

        # ====================================
        # CUSTOMER DATA ACCESS
        # ====================================

        customer_keywords = [
            "customer",
            "cust",
            "account",
            "order",
            "invoice",
            "payment",
            "ticket",
            "subscription",
        ]

        normalized_content = (
            content.lower()
        )

        requesting_customer_data = any(
            keyword in normalized_content
            for keyword in customer_keywords
        )

        # ====================================
        # CUSTOMER DATA AUTHORIZATION
        # ====================================

        if (
            requesting_customer_data
            and self.user_role
            not in {
                "support",
                "manager",
            }
        ):

            print(
                "[SECURITY] "
                "ACCESS DENIED"
            )

            return {
                "messages": [
                    {
                        "role": "assistant",
                        "content": (
                            "You are not authorized "
                            "to access customer information."
                        ),
                    }
                ]
            }

        # ====================================
        # ACCESS ALLOWED
        # ====================================

        print(
            "[SECURITY] "
            "ACCESS ALLOWED"
        )

        return None