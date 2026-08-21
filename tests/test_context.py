import asyncio

from agents.main_agent import (
    create_customer_support_agent,
)


def create_large_text(number: int) -> str:

    return (
        f"""
Customer historical interaction #{number}

Customer ID: CUST-1001

The customer contacted support regarding account
management, billing, payments, orders, invoices,
delivery information, technical support, previous
support tickets, account status, subscription details,
payment history, refund requests, delivery concerns,
product information, service issues, and account
verification.

This is historical information that may or may not
be relevant to the current request.

Historical reference:
HIST-{number:05d}

The support team previously reviewed the customer's
account and recorded this interaction for future
reference.

Additional historical information:
The customer has previously contacted support several
times regarding orders, payments, invoices, account
status, technical issues and general questions.

This record should be preserved as part of the
conversation history.
"""
    )


async def main():

    agent = (
        await create_customer_support_agent()
    )

    messages = []


    # ============================================
    # CREATE VERY LARGE CONVERSATION
    # ============================================

    for i in range(1, 151):

        messages.append(
            {
                "role": "user",
                "content": create_large_text(i),
            }
        )

        messages.append(
            {
                "role": "assistant",
                "content": (
                    f"Support interaction "
                    f"HIST-{i:05d} was recorded. "
                    f"The customer's account-related "
                    f"request was reviewed and the "
                    f"available information was considered."
                ),
            }
        )


    # ============================================
    # CURRENT REQUEST
    # ============================================

    messages.append(
        {
            "role": "user",
            "content": (
                "Based on everything discussed so far, "
                "what are the main things this customer "
                "has previously contacted support about?"
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


    # ============================================
    # RUN AGENT
    # ============================================

    result = await agent.ainvoke(
        {
            "messages": messages
        }
    )


    output_messages = result["messages"]


    print(
        "\n===== AFTER AGENT =====\n"
    )

    print(
        "Output messages:",
        len(output_messages)
    )


    # ============================================
    # DISPLAY MESSAGE TYPES
    # ============================================

    print(
        "\n===== MESSAGE TYPES =====\n"
    )

    for index, message in enumerate(
        output_messages
    ):

        content = str(
            getattr(
                message,
                "content",
                ""
            )
        )

        print(
            f"{index:03d} | "
            f"{message.type:<10} | "
            f"{len(content):>6} chars"
        )


    # ============================================
    # FINAL RESPONSE
    # ============================================

    print(
        "\n===== FINAL RESPONSE =====\n"
    )

    print(
        output_messages[-1].content
    )


if __name__ == "__main__":

    asyncio.run(main())