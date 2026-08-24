from typing import Any

from langchain.agents.middleware import (
    AgentMiddleware,
    hook_config,
)
from langchain.messages import AIMessage


class CustomerAuthorizationMiddleware(
    AgentMiddleware
):
    # Custom middleware for role-based access control.

    def __init__(
        self,
        user_role: str,
    ):
        super().__init__()

        self.user_role = user_role  # stores the role passed by the application

    @hook_config(
        can_jump_to=["end"]
    )
    def before_model(
        self,
        state: dict[str, Any],
        runtime: Any,
    ):
        # Runs before every model call.

        messages = state.get(
            "messages",
            []
        )  # gets the current conversation messages

        if not messages:
            return None  # nothing to authorize if there are no messages

        latest_message = messages[-1]  # gets the most recent message

        content = str(
            getattr(
                latest_message,
                "content",
                ""
            )
        )  # gets the message text

        print(
            "\n[SECURITY] "
            f"User role: {self.user_role}"
        )

        print(
            "[SECURITY] "
            "Request received."
        )

        customer_keywords = [
            "customer",
            "cust",
            "account",
            "order",
            "invoice",
            "payment",
            "ticket",
            "subscription",
        ]  # words that indicate customer-related data access

        normalized_content = (
            content.lower()
        )  # makes keyword matching case-insensitive

        requesting_customer_data = any(
            keyword in normalized_content
            for keyword in customer_keywords
        )  # checks whether the request involves customer data

        if (
            requesting_customer_data
            and self.user_role
            not in {
                "support",
                "manager",
            }
        ):
            # User does not have permission.

            print(
                "[SECURITY] "
                "ACCESS DENIED"
            )

            return {
                "messages": [
                    AIMessage(
                        content=(
                            "You are not authorized "
                            "to access customer information."
                        )
                    )
                ],
                "jump_to": "end",
            }  # adds the denial message and TERMINATES the agent run

        print(
            "[SECURITY] "
            "ACCESS ALLOWED"
        )

        return None  # allows the agent to continue