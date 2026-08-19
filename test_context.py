import asyncio

from agents.main_agent import (
    create_customer_support_agent,
)


async def main():

    agent = (
        await create_customer_support_agent()
    )

    messages = []

    # ========================================
    # GENERATE LARGE CONVERSATION
    # ========================================

    for i in range(1, 301):

        messages.append(
            {
                "role": "user",
                "content": (
                    f"Customer conversation message {i}. "
                    f"The customer is discussing account "
                    f"management, previous support requests, "
                    f"orders, invoices, payments, delivery "
                    f"questions, technical problems, and "
                    f"general account information. "
                    f"This is historical conversation "
                    f"record number {i}. "
                    f"Reference ID: HIST-{i:05d}."
                ),
            }
        )

        messages.append(
            {
                "role": "assistant",
                "content": (
                    f"Support response {i}. "
                    f"The customer's request was recorded "
                    f"and the relevant support information "
                    f"was considered. Historical reference "
                    f"HIST-{i:05d}."
                ),
            }
        )


    # ========================================
    # IMPORTANT CURRENT REQUEST
    # ========================================

    messages.append(
        {
            "role": "user",
            "content": (
                "This is my current request. "
                "Ignore irrelevant historical details. "
                "Tell me what you currently know about "
                "the purpose of this conversation."
            ),
        }
    )


    print(
        "\n===== CONTEXT STRESS TEST =====\n"
    )

    print(
        "Input messages:",
        len(messages)
    )


    # ========================================
    # RUN AGENT
    # ========================================

    result = await agent.ainvoke(
        {
            "messages": messages
        }
    )


    # ========================================
    # RESULTS
    # ========================================

    output_messages = result["messages"]

    print(
        "\nOutput messages:",
        len(output_messages)
    )

    print(
        "\n===== MESSAGE TYPES =====\n"
    )

    for i, message in enumerate(
        output_messages
    ):

        print(
            i,
            message.type
        )


    print(
        "\n===== FINAL RESPONSE =====\n"
    )

    print(
        output_messages[-1].content
    )


if __name__ == "__main__":

    asyncio.run(main())