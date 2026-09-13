import pytest

from langchain_core.messages import ToolMessage

from adapters.agents.middleware.security_middleware import CustomerAuthorizationMiddleware


class FakeToolRequest:
    def __init__(self, tool_name: str, args: dict):
        self.tool_call = {
            "id": "test-tool-call",
            "name": tool_name,
            "args": args,
        }


async def fake_handler(request):
    return "TOOL_EXECUTED"


@pytest.mark.anyio
async def test_customer_can_access_own_customer_data():
    middleware = CustomerAuthorizationMiddleware(
        user_role="customer",
        username="ahmed",
        customer_id="CUST-1001",
    )

    request = FakeToolRequest(
        tool_name="get_customer_orders",
        args={"customer_id": "CUST-1001"},
    )

    result = await middleware.awrap_tool_call(
        request,
        fake_handler,
    )

    assert result == "TOOL_EXECUTED"


@pytest.mark.anyio
async def test_customer_cannot_access_another_customer_data():
    middleware = CustomerAuthorizationMiddleware(
        user_role="customer",
        username="ahmed",
        customer_id="CUST-1001",
    )

    request = FakeToolRequest(
        tool_name="get_customer_orders",
        args={"customer_id": "CUST-1002"},
    )

    result = await middleware.awrap_tool_call(
        request,
        fake_handler,
    )

    assert isinstance(result, ToolMessage)
    assert result.status == "error"
    assert "don't have access" in result.content.lower()


@pytest.mark.anyio
async def test_customer_cannot_use_manager_only_tools():
    middleware = CustomerAuthorizationMiddleware(
        user_role="customer",
        username="ahmed",
        customer_id="CUST-1001",
    )

    request = FakeToolRequest(
        tool_name="refund_payment",
        args={
            "customer_id": "CUST-1001",
            "payment_id": "PAY-1001",
        },
    )

    result = await middleware.awrap_tool_call(
        request,
        fake_handler,
    )

    assert isinstance(result, ToolMessage)
    assert result.status == "error"


@pytest.mark.anyio
async def test_internal_deep_agent_tools_are_allowed():
    middleware = CustomerAuthorizationMiddleware(
        user_role="customer",
        username="ahmed",
        customer_id="CUST-1001",
    )

    request = FakeToolRequest(
        tool_name="write_todos",
        args={},
    )

    result = await middleware.awrap_tool_call(
        request,
        fake_handler,
    )

    assert result == "TOOL_EXECUTED"
