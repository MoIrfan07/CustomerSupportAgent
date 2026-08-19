import asyncio
import json

import dashscope

from langchain_mcp_adapters.client import (
    MultiServerMCPClient,
)

from app.config import (
    QWEN_API_KEY,
    QWEN_BASE_URL,
    QWEN_MODEL,
    QWEN_LANGUAGE,
)


# ============================================
# QWEN CONFIGURATION
# ============================================

dashscope.base_http_api_url = QWEN_BASE_URL


# ============================================
# MCP CLIENT
# ============================================

async def create_mcp_client():

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

    return client


# ============================================
# MAIN
# ============================================

async def main():

    client = await create_mcp_client()

    # Get tools exposed by MCP
    tools = await client.get_tools()

    print("\n===== MCP TOOLS =====\n")

    for tool in tools:

        print(
            f"- {tool.name}"
        )

    # ----------------------------------------
    # Convert LangChain tools to Qwen schema
    # ----------------------------------------

    qwen_tools = []

    for tool in tools:

        if isinstance(tool.args_schema, dict):
            schema = tool.args_schema
            
        else:
            schema = (
                tool.args_schema
                .model_json_schema()
            )

    qwen_tools.append(
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": (
                    tool.description
                    or ""
                ),
                "parameters": schema,
            },
        }
    )

    # ----------------------------------------
    # User conversation
    # ----------------------------------------

    messages = [

        {
            "role": "system",
            "content": (
                "You are a professional customer "
                "support assistant.\n\n"
                "Always respond in "f"{QWEN_LANGUAGE}"" unless the user explicitly asks for another "
                "language.\n\n"
                "Use the available tools whenever "
                "you need customer information."
            ),
        },

        {
            "role": "user",
            "content": (
                "What is the status of "
                "customer CUST-1001?"
            ),
        },

    ]

    # ----------------------------------------
    # FIRST QWEN CALL
    # ----------------------------------------

    response = dashscope.Generation.call(

        api_key=QWEN_API_KEY,

        model=QWEN_MODEL,

        messages=messages,

        tools=qwen_tools,

        result_format="message",
    )

    if response.status_code != 200:

        raise RuntimeError(
            f"Qwen API error: "
            f"{response.code} - "
            f"{response.message}"
        )

    assistant_message = (
        response.output
        .choices[0]
        .message
    )

    print(
        "\n===== QWEN RESPONSE =====\n"
    )

    print(assistant_message)

    # ----------------------------------------
    # CHECK TOOL CALL
    # ----------------------------------------

    tool_calls = getattr(
        assistant_message,
        "tool_calls",
        None,
    )

    if not tool_calls:

        print(
            "\nNo tool call requested."
        )

        print(
            assistant_message.content
        )

        return

    # ----------------------------------------
    # EXECUTE MCP TOOL
    # ----------------------------------------

    for tool_call in tool_calls:

        function_name = (
            tool_call["function"]["name"]
        )

        arguments = json.loads(
            tool_call["function"]["arguments"]
        )

        print(
            "\n===== MCP TOOL CALL ====="
        )

        print(
            "Tool:",
            function_name,
        )

        print(
            "Arguments:",
            arguments,
        )

        # Find the corresponding MCP tool
        selected_tool = next(
            (
                tool
                for tool in tools
                if tool.name == function_name
            ),
            None,
        )

        if selected_tool is None:

            raise RuntimeError(
                f"MCP tool not found: "
                f"{function_name}"
            )

        # Execute through MCP
        result = await selected_tool.ainvoke(
            arguments
        )

        print(
            "\n===== MCP TOOL RESULT ====="
        )

        print(result)

        # ------------------------------------
        # ADD ASSISTANT TOOL CALL
        # ------------------------------------

        messages.append(
            {
                "role": "assistant",
                "content": (
                    assistant_message.content
                ),
                "tool_calls": tool_calls,
            }
        )

        # ------------------------------------
        # ADD TOOL RESULT
        # ------------------------------------

        messages.append(
            {
                "role": "tool",
                "name": function_name,
                "content": json.dumps(
                    result
                ),
            }
        )

    # ----------------------------------------
    # SECOND QWEN CALL
    # ----------------------------------------

    final_response = (
        dashscope.Generation.call(

            api_key=QWEN_API_KEY,

            model=QWEN_MODEL,

            messages=messages,

            tools=qwen_tools,

            result_format="message",
        )
    )

    if final_response.status_code != 200:

        raise RuntimeError(
            f"Qwen API error: "
            f"{final_response.code} - "
            f"{final_response.message}"
        )

    final_message = (
        final_response.output
        .choices[0]
        .message
    )

    print(
        "\n===== FINAL ANSWER =====\n"
    )

    print(
        final_message.content
    )


if __name__ == "__main__":

    asyncio.run(main())