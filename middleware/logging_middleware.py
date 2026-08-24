from datetime import datetime
from typing import Any

from langchain.agents.middleware import (
    AgentMiddleware,
)


class CustomerSupportLoggingMiddleware(
    AgentMiddleware
):    #custom middleware for logging requests and responses in the customer support agent

    def _timestamp(self) -> str:   #timestamp for logging purposes

        return datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    # BEFORE MODEL  

    def before_model(
        self,
        state: dict[str, Any],
        runtime: Any,
    ):   #logs the request before it is sent to the model

        messages = state.get(
            "messages",
            []
        )

        print(
            "\n"
            f"[{self._timestamp()}] "
            "MODEL REQUEST"
        )

        print(
            "Messages:",
            len(messages)
        )

        if messages:

            last_message = messages[-1]

            print(
                "Last message type:",
                getattr(
                    last_message,
                    "type",
                    "unknown"
                )
            )

            content = getattr(
                last_message,
                "content",
                ""
            )

            print(
                "Content preview:",
                str(content)[:300]
            )

        return None




    # AFTER MODEL

    def after_model(
        self,
        state: dict[str, Any],
        runtime: Any,
    ):   #logs the response after it is received from the model

        messages = state.get(
            "messages",
            []
        )

        print(
            "\n"
            f"[{self._timestamp()}] "
            "MODEL RESPONSE"
        )

        print(
            "Messages:",
            len(messages)
        )

        if messages:

            last_message = messages[-1]

            print(
                "Response type:",
                getattr(
                    last_message,
                    "type",
                    "unknown"
                )
            )

            content = getattr(
                last_message,
                "content",
                "",
            )

            print(
                "Response preview:",
                "Response Generated" if content else "No response generated"
            )

        return None