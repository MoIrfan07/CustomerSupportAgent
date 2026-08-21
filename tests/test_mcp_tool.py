import asyncio

from app.mcp_client import get_mcp_tools


async def main():

    tools = await get_mcp_tools()

    print(
        "\n===== MCP TOOL DETAILS =====\n"
    )

    for tool in tools:

        print(
            "Name:",
            tool.name
        )

        print(
            "Type:",
            type(tool)
        )

        print(
            "Runnable:",
            type(tool).__mro__
        )

        print(
            "Has _run:",
            hasattr(tool, "_run")
        )

        print(
            "Has _arun:",
            hasattr(tool, "_arun")
        )

        print(
            "Has ainvoke:",
            hasattr(tool, "ainvoke")
        )

        print(
            "Has invoke:",
            hasattr(tool, "invoke")
        )

        print()


if __name__ == "__main__":

    asyncio.run(main())