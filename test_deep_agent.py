import asyncio

from agents.main_agent import (
    create_customer_support_agent,
)


async def main():

    # ========================================
    # CREATE AGENT
    # ========================================

    agent = (
        await create_customer_support_agent()
    )


    # ========================================
    # CUSTOMER REQUEST
    # ========================================

    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "What invoices and payment information do we have for customer CUST-1001?"
                    ),
                }
            ]
        }
    )


    # ========================================
    # DISPLAY RESULT
    # ========================================

    print(
        "\n===== DEEP AGENT RESPONSE =====\n"
    )

    for message in result["messages"]:

        print(
            f"{message.type}:"
        )

        print(
            message.content
        )

        if getattr(
            message,
            "tool_calls",
            None,
        ):

            print(
                "Tool calls:",
                message.tool_calls
            )

        print()


if __name__ == "__main__":

    asyncio.run(main())