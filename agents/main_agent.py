from deepagents import create_deep_agent
from agents.subagents import build_subagents
from app.config import QWEN_LANGUAGE
from app.llm import qwen_model
from app.mcp_client import get_mcp_tools


# ============================================
# CUSTOMER SUPPORT INSTRUCTIONS
# ============================================

SYSTEM_PROMPT = f"""
You are a professional customer support agent.

Your responsibilities are:

1. Understand the customer's request.

2. Use available tools whenever customer,
   order, payment, account, or other business
   information is required.

3. Never invent, assume, or estimate factual
   customer information.

4. Only state customer information that is
   explicitly present in the result returned
   by a tool.

5. If a requested field is not present in the
   tool result, explicitly say that the information
   is not available.

6. Never substitute information from another
   customer.

7. Give clear and concise answers.

8. Always respond in {QWEN_LANGUAGE} unless the
   customer explicitly asks for another language.

9. If you cannot complete a request, explain why.

10. Ask for clarification when required
    information is missing.

You are the main customer support coordinator.

IMPORTANT:
Tool results are the source of truth for customer
data. Do not add information that is not contained
in the tool results.
"""


# ============================================
# CREATE AGENT
# ============================================

async def create_customer_support_agent():

    tools = await get_mcp_tools()
    subagents = build_subagents(tools)
    
    
    print(
        "\n===== MCP TOOLS LOADED =====\n"
    )

    for tool in tools:

        print(
            f"- {tool.name}"
        )

    agent = create_deep_agent(
        model=qwen_model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        subagents=subagents,
    )

    return agent