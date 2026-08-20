import asyncio

from langgraph.types import Command
#from langgraph.errors import GraphInterrupt

from agents.main_agent import (
    create_customer_support_agent,
)


CONFIG = {
    "configurable": {
        "thread_id": "customer-support-session"
    }
}


async def main():

    # ========================================
    # CREATE AGENT
    # ========================================

    agent = (
        await create_customer_support_agent()
    )


    # ========================================
    # CONVERSATION HISTORY
    # ========================================

    messages = []


    print()
    print("=" * 60)
    print("        CUSTOMER SUPPORT AGENT")
    print("=" * 60)
    print()
    print(
        "Type your message and press Enter."
    )
    print(
        "Type 'exit' or 'quit' to stop."
    )
    print()


    # ========================================
    # CHAT LOOP
    # ========================================

    while True:

        try:

            user_input = input(
                "You: "
            ).strip()

        except (
            KeyboardInterrupt,
            EOFError,
        ):

            print(
                "\n\nGoodbye!"
            )

            break


        # ------------------------------------
        # EXIT
        # ------------------------------------

        if user_input.lower() in {
            "exit",
            "quit",
        }:

            print(
                "\nGoodbye!"
            )

            break


        # ------------------------------------
        # EMPTY INPUT
        # ------------------------------------

        if not user_input:
            continue


        # ------------------------------------
        # ADD USER MESSAGE
        # ------------------------------------

        messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )


        print(
            "\nAgent:"
        )


        try:

            # =================================
            # START / CONTINUE AGENT
            # =================================

            result = await agent.ainvoke(
                {
                    "messages": messages
                },
                config=CONFIG,
            )


            # =================================
            # CHECK FOR INTERRUPT
            # =================================

            interrupts = (
                result.get("__interrupt__")
            )


            if interrupts:

                interrupt_value = (
                    interrupts[0].value
                )

                print(
                    interrupt_value
                )


                # -----------------------------
                # ASK HUMAN
                # -----------------------------

                approval = input(
                    "\nApprove this action? "
                    "(yes/no): "
                ).strip().lower()


                approved = approval in {
                    "yes",
                    "y",
                }


                # -----------------------------
                # RESUME AGENT
                # -----------------------------

                result = await agent.ainvoke(
                    Command(
                        resume=approved
                    ),
                    config=CONFIG,
                )


            # =================================
            # UPDATE HISTORY
            # =================================

            messages = result[
                "messages"
            ]


            # =================================
            # FINAL RESPONSE
            # =================================

            if messages:

                final_message = (
                    messages[-1]
                )

                content = getattr(
                    final_message,
                    "content",
                    "",
                )

                if content:

                    print(
                        content
                    )


        except Exception as e:

            print(
                "\nAgent error:"
            )

            print(
                str(e)
            )


        print()


if __name__ == "__main__":

    asyncio.run(main())