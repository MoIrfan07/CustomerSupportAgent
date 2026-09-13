from __future__ import annotations

import pytest
from langchain_core.messages import ToolMessage

from app.adapters.in_memory.customer_adapter import MCPCustomerAdapter
from mcp_server import list_customers
from adapters.agents.middleware.security_middleware import CustomerAuthorizationMiddleware


# ============================================================
# MCP SERVER — business logic
# ============================================================


def test_list_customers_returns_all_customers():
    result = list_customers()

    assert result["success"] is True
    assert len(result["customers"]) == 2

    customer_ids = {customer["customer_id"] for customer in result["customers"]}

    assert customer_ids == {"CUST-1001", "CUST-1002"}


# ============================================================
# ADAPTER — MCP envelope unwrapping
# ============================================================


class FakeTool:
    def __init__(self, result):
        self.result = result
        self.calls = []

    async def ainvoke(self, arguments):
        self.calls.append(arguments)
        return self.result


@pytest.mark.anyio
async def test_customer_adapter_lists_all_customers():
    tool = FakeTool(
        {
            "success": True,
            "customers": [
                {
                    "customer_id": "CUST-1001",
                    "name": "Ahmed Khan",
                    "email": "ahmed@example.com",
                    "status": "Active",
                    "plan": "Premium",
                },
                {
                    "customer_id": "CUST-1002",
                    "name": "John Smith",
                    "email": "john@example.com",
                    "status": "Suspended",
                    "plan": "Basic",
                },
            ],
        }
    )

    adapter = MCPCustomerAdapter({"list_customers": tool})

    customers = await adapter.list_customers()

    assert len(customers) == 2
    assert customers[0].customer_id == "CUST-1001"
    assert customers[1].customer_id == "CUST-1002"

    # Called with no arguments.
    assert tool.calls == [{}]


@pytest.mark.anyio
async def test_customer_adapter_list_customers_returns_empty_on_failure():
    tool = FakeTool(
        {
            "success": False,
            "error": "unexpected failure",
        }
    )

    adapter = MCPCustomerAdapter({"list_customers": tool})

    customers = await adapter.list_customers()

    assert customers == []


@pytest.mark.anyio
async def test_customer_adapter_list_customers_raises_on_invalid_shape():
    tool = FakeTool(
        {
            "success": True,
            "customers": "not-a-list",
        }
    )

    adapter = MCPCustomerAdapter({"list_customers": tool})

    with pytest.raises(TypeError):
        await adapter.list_customers()


# ============================================================
# AUTHORIZATION — staff-only access
# ============================================================


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
@pytest.mark.parametrize("role", ["manager", "support"])
async def test_staff_can_list_customers(role):
    middleware = CustomerAuthorizationMiddleware(
        user_role=role,
        username=role,
    )

    request = FakeToolRequest("list_customers", {})

    result = await middleware.awrap_tool_call(request, fake_handler)

    assert result == "TOOL_EXECUTED"


@pytest.mark.anyio
@pytest.mark.parametrize("role", ["customer", "guest", "user"])
async def test_non_staff_cannot_list_customers(role):
    customer_id = "CUST-1001" if role == "customer" else None

    middleware = CustomerAuthorizationMiddleware(
        user_role=role,
        username=role,
        customer_id=customer_id,
    )

    request = FakeToolRequest("list_customers", {})

    result = await middleware.awrap_tool_call(request, fake_handler)

    assert isinstance(result, ToolMessage)
    assert result.status == "error"
