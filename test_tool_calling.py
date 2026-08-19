import json

import dashscope

from app.config import (
    QWEN_API_KEY,
    QWEN_BASE_URL,
    QWEN_MODEL,
    QWEN_LANGUAGE,
)

from tools.customer_tools import get_customer


dashscope.base_http_api_url = QWEN_BASE_URL


# ============================================
# TOOL DEFINITION
# ============================================

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_customer",
            "description": (
                "Retrieve customer information "
                "using a customer ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": (
                            "The customer ID, "
                            "for example CUST-1001."
                        ),
                    }
                },
                "required": ["customer_id"],
            },
        },
    }
]


# ============================================
# USER REQUEST
# ============================================

messages = [
    {
    "role": "system",
    "content": (
        "You are a professional customer support "
        "assistant.\n\n"
        "Always respond in" f"{QWEN_LANGUAGE}"
        "unless the user explicitly asks for another language."
        "Use the available tools whenever you need "
        "customer information.\n\n"
        "Keep your responses concise, clear, "
        "professional, and helpful."
    ),
},
    {
        "role": "user",
        "content": (
            "Can you tell me the status of "
            "customer CUST-1001?"
        ),
    },
]


# ============================================
# FIRST QWEN CALL
# ============================================

response = dashscope.Generation.call(
    api_key=QWEN_API_KEY,
    model=QWEN_MODEL,
    messages=messages,
    tools=tools,
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


print("\n===== QWEN DECISION =====\n")

print(assistant_message)


# ============================================
# CHECK FOR TOOL CALL
# ============================================

tool_calls = getattr(
    assistant_message,
    "tool_calls",
    None,
)


if not tool_calls:

    print(
        "\nQwen did not request a tool."
    )

    print(
        "\nFinal response:"
    )

    print(
        assistant_message.content
    )

    raise SystemExit


# ============================================
# EXECUTE TOOL
# ============================================
for tool_call in tool_calls:

    function_name = (
        tool_call["function"]["name"]
    )

    arguments = json.loads(
        tool_call["function"]["arguments"]
    )

    print(
        "\n===== TOOL CALL ====="
    )

    print(
        "Tool:",
        function_name,
    )

    print(
        "Arguments:",
        arguments,
    )


    if function_name == "get_customer":

        result = get_customer(
            arguments["customer_id"]
        )

    else:

        result = {
            "error": (
                f"Unknown tool: "
                f"{function_name}"
            )
        }


    # ========================================
    # ADD TOOL RESULT TO CONVERSATION
    # ========================================

    messages.append(
        {
            "role": "assistant",
            "content": assistant_message.content,
            "tool_calls": tool_calls,
        }
    )

    messages.append(
        {
            "role": "tool",
            "name": function_name,
            "content": json.dumps(result),
        }
    )


# ============================================
# SECOND QWEN CALL
# ============================================

final_response = dashscope.Generation.call(
    api_key=QWEN_API_KEY,
    model=QWEN_MODEL,
    messages=messages,
    tools=tools,
    result_format="message",
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