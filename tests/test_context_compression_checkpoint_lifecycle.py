from __future__ import annotations

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from app.adapters.agents.main_agent import create_customer_support_agent
from app.mcp_client import get_mcp_tools


@pytest.mark.integration
@pytest.mark.anyio
async def test_compression_lifecycle_preserves_persisted_history_across_turns():
    tools = await get_mcp_tools()

    checkpointer = InMemorySaver()

    agent = await create_customer_support_agent(
        tools=tools,
        user_role="customer",
        username="ahmed",
        customer_id="CUST-1001",
        checkpointer=checkpointer,
    )

    thread_id = "test-compression-checkpoint-lifecycle"

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    # ------------------------------------------------------------
    # TURN 1
    # ------------------------------------------------------------

    first_result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "What orders do I have?",
                }
            ]
        },
        config=config,
    )

    assert "__interrupt__" not in first_result

    first_messages = first_result["messages"]

    assert first_messages
    assert first_messages[0].content == "What orders do I have?"
    assert first_messages[-1].content

    # ------------------------------------------------------------
    # TURN 2 — SAME THREAD
    # ------------------------------------------------------------

    second_result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Which one is still processing?",
                }
            ]
        },
        config=config,
    )

    assert "__interrupt__" not in second_result

    second_messages = second_result["messages"]

    assert second_messages

    # The persisted conversation should contain the first turn.
    assert any(
        getattr(message, "content", None) == "What orders do I have?"
        for message in second_messages
    )

    # The second turn should also be present.
    assert any(
        getattr(message, "content", None) == "Which one is still processing?"
        for message in second_messages
    )

    # The agent should still have access to the business context
    # established during the first turn.
    final_message = second_messages[-1]

    assert final_message.content
    assert "ORD-5002" in final_message.content

    # ------------------------------------------------------------
    # CHECKPOINT VERIFICATION
    # ------------------------------------------------------------

    persisted_state = await agent.aget_state(config)

    assert persisted_state is not None
    assert persisted_state.values

    persisted_messages = persisted_state.values["messages"]

    assert persisted_messages

    # The persisted checkpoint must retain both user turns.
    assert any(
        getattr(message, "content", None) == "What orders do I have?"
        for message in persisted_messages
    )

    assert any(
        getattr(message, "content", None) == "Which one is still processing?"
        for message in persisted_messages
    )

    # The persisted checkpoint is independent of the model-visible
    # request. Compression must not destructively replace the
    # checkpointed conversation history.
    assert len(persisted_messages) >= len(second_messages)
