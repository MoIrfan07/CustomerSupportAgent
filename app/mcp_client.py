from langchain_mcp_adapters.client import (
    MultiServerMCPClient,
)


async def get_mcp_tools():

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

    return tools