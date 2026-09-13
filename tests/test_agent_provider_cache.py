from unittest.mock import AsyncMock, patch

import pytest

from app.infrastructure.agent_factory import AgentProvider


@pytest.mark.asyncio
async def test_customer_agent_is_cached():
    provider = AgentProvider(
        tools=[],
        checkpointer=object(),
    )

    first_agent = object()

    with patch(
        "app.infrastructure.agent_factory.create_customer_support_agent",
        new=AsyncMock(return_value=first_agent),
    ) as create_agent:
        result_one = await provider.get_agent(
            user_role="customer",
            username="ahmed",
            customer_id="CUST-1001",
        )

        result_two = await provider.get_agent(
            user_role="customer",
            username="ahmed",
            customer_id="CUST-1001",
        )

    assert result_one is first_agent
    assert result_two is first_agent
    create_agent.assert_awaited_once()


@pytest.mark.asyncio
async def test_different_customers_get_different_agents():
    provider = AgentProvider(
        tools=[],
        checkpointer=object(),
    )

    first_agent = object()
    second_agent = object()

    create_agent = AsyncMock(
        side_effect=[
            first_agent,
            second_agent,
        ]
    )

    with patch(
        "app.infrastructure.agent_factory.create_customer_support_agent",
        new=create_agent,
    ):
        result_one = await provider.get_agent(
            user_role="customer",
            username="ahmed",
            customer_id="CUST-1001",
        )

        result_two = await provider.get_agent(
            user_role="customer",
            username="john",
            customer_id="CUST-1002",
        )

    assert result_one is first_agent
    assert result_two is second_agent
    assert create_agent.await_count == 2


@pytest.mark.asyncio
async def test_remove_customer_agent_forces_recreation():
    provider = AgentProvider(
        tools=[],
        checkpointer=object(),
    )

    first_agent = object()
    second_agent = object()

    create_agent = AsyncMock(
        side_effect=[
            first_agent,
            second_agent,
        ]
    )

    with patch(
        "app.infrastructure.agent_factory.create_customer_support_agent",
        new=create_agent,
    ):
        first_result = await provider.get_agent(
            user_role="customer",
            username="ahmed",
            customer_id="CUST-1001",
        )

        provider.remove_agent(
            user_role="customer",
            username="ahmed",
            customer_id="CUST-1001",
        )

        second_result = await provider.get_agent(
            user_role="customer",
            username="ahmed",
            customer_id="CUST-1001",
        )

    assert first_result is first_agent
    assert second_result is second_agent
    assert create_agent.await_count == 2
