import pytest
from langgraph.checkpoint.memory import InMemorySaver

from agents.main_agent import create_customer_support_agent
from app.mcp_client import get_mcp_tools


@pytest.mark.integration
@pytest.mark.anyio
async def test_customer_agent_can_retrieve_own_orders():
    tools = await get_mcp_tools()

    checkpointer = InMemorySaver()

    agent = await create_customer_support_agent(
        tools=tools,
        user_role="customer",
        username="ahmed",
        customer_id="CUST-1001",
        checkpointer=checkpointer,
    )

    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "What orders do I have?",
                }
            ]
        },
        config={
            "configurable": {
                "thread_id": "test-customer-orders",
            }
        },
    )

    assert "__interrupt__" not in result

    messages = result["messages"]
    final_message = messages[-1]

    assert final_message.content
    assert "ORD-5001" in final_message.content
    assert "ORD-5002" in final_message.content
