from datetime import datetime
from typing import Any

from langchain.agents.middleware import (
    AgentMiddleware,
)


class CustomerSupportLoggingMiddleware(
    AgentMiddleware
):

    def _timestamp(self) -> str:

        return datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )


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


    # ========================================
    # AFTER MODEL
    # ========================================

    def after_model(
        self,
        state: dict[str, Any],
        runtime: Any,
    ):

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