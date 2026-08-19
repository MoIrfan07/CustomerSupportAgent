import asyncio

from langchain_mcp_adapters.client import (
    MultiServerMCPClient,
)


async def main():

    client = MultiServerMCPClient(
        {
            "customer_support": {
                "command": "python",
                "args": [
                    "mcp_server.py"
                ],
                "transport": "stdio",
            }
        }
    )


    tools = await client.get_tools()


    print(
        "\n===== MCP TOOLS =====\n"
    )


    for tool in tools:

        print(
            f"Name: {tool.name}"
        )

        print(
            f"Description: "
            f"{tool.description}"
        )

        print()


if __name__ == "__main__":

    asyncio.run(main())