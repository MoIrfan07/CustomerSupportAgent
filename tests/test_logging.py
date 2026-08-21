import asyncio

from agents.main_agent import (
    create_customer_support_agent,
)


async def main():

    agent = (
        await create_customer_support_agent()
    )

    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "What is the status of "
                        "customer CUST-1001?"
                    ),
                }
            ]
        }
    )

    print(
        "\n===== FINAL ANSWER =====\n"
    )

    print(
        result["messages"][-1].content
    )


if __name__ == "__main__":

    asyncio.run(main())