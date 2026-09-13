import asyncio
# to run the asynchronous main function

from langgraph.types import Command
# from langgraph.errors import GraphInterrupt

from adapters.agents.main_agent import (
    create_customer_support_agent,
)

from app.mcp_client import get_mcp_tools


CONFIG = {
    "configurable": {
        "thread_id": "customer-support-session"  # thread ID for the customer support session, used to maintain conversation context
    }
}


async def main():

    # CREATE AGENT

    tools = await get_mcp_tools()
    # Loads the MCP tools for the test environment

    agent = await create_customer_support_agent(
        tools=tools,
        user_role="manager",
    )
    # Creates the Deep Agent using the MCP tools

    # CONVERSATION HISTORY

    messages = []  # store the conversation history between the user and the agent

    print()
    print("=" * 60)
    print("        CUSTOMER SUPPORT AGENT")
    print("=" * 60)
    print()
    print("Type your message and press Enter.")
    print("Type 'exit' or 'quit' to stop.")
    print()

    # CHAT
    while True:
        try:
            user_input = input("You: ").strip()

        except (
            KeyboardInterrupt,
            EOFError,
        ):
            print("\n\nGoodbye!")

            break

        # EXIT

        if user_input.lower() in {
            "exit",
            "quit",
        }:
            print("\nGoodbye!")

            break

        # EMPTY INPUT

        if not user_input:
            continue

        # ADD USER MESSAGE

        messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )  # adds the user's message to the conversation history, which will be sent to the agent for processing

        print("\nAgent:")

        try:
            # START / CONTINUE AGENT

            result = await agent.ainvoke(
                {"messages": messages},
                config=CONFIG,
            )

            # CHECK FOR INTERRUPT

            interrupts = result.get("__interrupt__")

            if interrupts:
                interrupt_value = interrupts[0].value

                print(interrupt_value)

                # ASK HUMAN FOR APPROVAL

                approval = input("\nApprove this action? (yes/no): ").strip().lower()

                approved = approval in {
                    "yes",
                    "y",
                }

                # RESUME AGENT

                result = await agent.ainvoke(
                    Command(resume=approved),
                    config=CONFIG,
                )

            # UPDATE HISTORY

            messages = result["messages"]

            # FINAL RESPONSE

            if messages:
                final_message = messages[-1]

                content = getattr(
                    final_message,
                    "content",
                    "",
                )

                if content:
                    print(content)

        except Exception as e:
            print("\nAgent error:")

            print(str(e))

        print()


if __name__ == "__main__":
    asyncio.run(main())
