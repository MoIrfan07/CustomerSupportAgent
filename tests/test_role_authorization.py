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


READ_TOOLS = [
    "get_customer",
    "get_customer_orders",
    "get_customer_invoices",
    "get_customer_payments",
    "get_customer_tickets",
]


@pytest.mark.anyio
@pytest.mark.parametrize("tool_name", READ_TOOLS)
async def test_manager_can_use_all_read_tools(tool_name):
    middleware = CustomerAuthorizationMiddleware(
        user_role="manager",
        username="manager",
    )

    request = FakeToolRequest(
        tool_name,
        {"customer_id": "CUST-1001"},
    )

    result = await middleware.awrap_tool_call(
        request,
        fake_handler,
    )

    assert result == "TOOL_EXECUTED"


@pytest.mark.anyio
@pytest.mark.parametrize("tool_name", READ_TOOLS)
async def test_support_can_use_all_read_tools(tool_name):
    middleware = CustomerAuthorizationMiddleware(
        user_role="support",
        username="support",
    )

    request = FakeToolRequest(
        tool_name,
        {"customer_id": "CUST-1001"},
    )

    result = await middleware.awrap_tool_call(
        request,
        fake_handler,
    )

    assert result == "TOOL_EXECUTED"


@pytest.mark.anyio
async def test_manager_can_refund_payment():
    middleware = CustomerAuthorizationMiddleware(
        user_role="manager",
        username="manager",
    )

    request = FakeToolRequest(
        "refund_payment",
        {
            "customer_id": "CUST-1001",
            "payment_id": "PAY-1001",
        },
    )

    result = await middleware.awrap_tool_call(
        request,
        fake_handler,
    )

    assert result == "TOOL_EXECUTED"


@pytest.mark.anyio
async def test_manager_can_cancel_order():
    middleware = CustomerAuthorizationMiddleware(
        user_role="manager",
        username="manager",
    )

    request = FakeToolRequest(
        "cancel_order",
        {
            "customer_id": "CUST-1001",
            "order_id": "ORD-1001",
        },
    )

    result = await middleware.awrap_tool_call(
        request,
        fake_handler,
    )

    assert result == "TOOL_EXECUTED"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "role",
    ["support", "user", "customer", "guest"],
)
async def test_non_manager_roles_cannot_refund_payment(role):
    customer_id = "CUST-1001" if role == "customer" else None

    middleware = CustomerAuthorizationMiddleware(
        user_role=role,
        username=role,
        customer_id=customer_id,
    )

    request = FakeToolRequest(
        "refund_payment",
        {
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
@pytest.mark.parametrize(
    "role",
    ["support", "user", "customer", "guest"],
)
async def test_non_manager_roles_cannot_cancel_order(role):
    customer_id = "CUST-1001" if role == "customer" else None

    middleware = CustomerAuthorizationMiddleware(
        user_role=role,
        username=role,
        customer_id=customer_id,
    )

    request = FakeToolRequest(
        "cancel_order",
        {
            "customer_id": "CUST-1001",
            "order_id": "ORD-1001",
        },
    )

    result = await middleware.awrap_tool_call(
        request,
        fake_handler,
    )

    assert isinstance(result, ToolMessage)
    assert result.status == "error"


@pytest.mark.anyio
async def test_guest_cannot_use_customer_read_tools():
    middleware = CustomerAuthorizationMiddleware(
        user_role="guest",
        username="guest",
    )

    request = FakeToolRequest(
        "get_customer_orders",
        {"customer_id": "CUST-1001"},
    )

    result = await middleware.awrap_tool_call(
        request,
        fake_handler,
    )

    assert isinstance(result, ToolMessage)
    assert result.status == "error"


@pytest.mark.anyio
async def test_guest_cannot_use_internal_tools():
    middleware = CustomerAuthorizationMiddleware(
        user_role="guest",
        username="guest",
    )

    request = FakeToolRequest(
        "write_todos",
        {},
    )

    result = await middleware.awrap_tool_call(
        request,
        fake_handler,
    )

    assert result == "TOOL_EXECUTED"
