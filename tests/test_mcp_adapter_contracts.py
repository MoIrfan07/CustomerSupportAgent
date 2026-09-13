from __future__ import annotations

import pytest

from app.adapters.in_memory.billing_adapter import MCPBillingAdapter
from app.adapters.in_memory.customer_adapter import MCPCustomerAdapter
from app.adapters.in_memory.order_adapter import MCPOrderAdapter
from app.adapters.in_memory.technical_support_adapter import (
    MCPTechnicalSupportAdapter,
)


class FakeTool:
    def __init__(self, result):
        self.result = result

    async def ainvoke(self, _arguments):
        return self.result


@pytest.mark.anyio
async def test_customer_adapter_unwraps_mcp_envelope():
    tools = {
        "get_customer": FakeTool(
            {
                "success": True,
                "customer": {
                    "customer_id": "CUST-1001",
                    "name": "Ahmed Khan",
                    "email": "ahmed@example.com",
                    "status": "Active",
                    "plan": "Premium",
                },
            }
        )
    }

    adapter = MCPCustomerAdapter(tools)

    customer = await adapter.get_customer("CUST-1001")

    assert customer is not None
    assert customer.customer_id == "CUST-1001"
    assert customer.name == "Ahmed Khan"
    assert customer.email == "ahmed@example.com"


@pytest.mark.anyio
async def test_customer_adapter_returns_none_for_failed_lookup():
    tools = {
        "get_customer": FakeTool(
            {
                "success": False,
                "error": "Customer was not found.",
                "customer": None,
            }
        )
    }

    adapter = MCPCustomerAdapter(tools)

    customer = await adapter.get_customer("UNKNOWN")

    assert customer is None


@pytest.mark.anyio
async def test_order_adapter_unwraps_orders_envelope():
    tools = {
        "get_customer_orders": FakeTool(
            {
                "success": True,
                "customer_id": "CUST-1001",
                "orders": [
                    {
                        "order_id": "ORD-5001",
                        "product": "Laptop",
                        "amount": 4200,
                        "status": "Delivered",
                    },
                    {
                        "order_id": "ORD-5002",
                        "product": "Monitor",
                        "amount": 850,
                        "status": "Processing",
                    },
                ],
            }
        )
    }

    adapter = MCPOrderAdapter(tools)

    orders = await adapter.get_customer_orders("CUST-1001")

    assert len(orders) == 2
    assert orders[0].order_id == "ORD-5001"
    assert orders[1].order_id == "ORD-5002"


@pytest.mark.anyio
async def test_billing_adapter_unwraps_invoice_envelope():
    tools = {
        "get_customer_invoices": FakeTool(
            {
                "success": True,
                "customer_id": "CUST-1001",
                "invoices": [
                    {
                        "invoice_id": "INV-1001",
                        "amount": 4200,
                        "status": "Paid",
                    }
                ],
            }
        )
    }

    adapter = MCPBillingAdapter(tools)

    invoices = await adapter.get_customer_invoices("CUST-1001")

    assert len(invoices) == 1
    assert invoices[0].invoice_id == "INV-1001"
    assert str(invoices[0].amount) == "4200"


@pytest.mark.anyio
async def test_billing_adapter_unwraps_payment_envelope():
    tools = {
        "get_customer_payments": FakeTool(
            {
                "success": True,
                "customer_id": "CUST-1001",
                "payments": [
                    {
                        "payment_id": "PAY-1001",
                        "amount": 4200,
                        "status": "Completed",
                    }
                ],
            }
        )
    }

    adapter = MCPBillingAdapter(tools)

    payments = await adapter.get_customer_payments("CUST-1001")

    assert len(payments) == 1
    assert payments[0].payment_id == "PAY-1001"
    assert str(payments[0].amount) == "4200"


@pytest.mark.anyio
async def test_technical_adapter_unwraps_ticket_envelope():
    tools = {
        "get_customer_tickets": FakeTool(
            {
                "success": True,
                "customer_id": "CUST-1001",
                "tickets": [
                    {
                        "ticket_id": "TCK-1001",
                        "subject": "Monitor delivery",
                        "status": "Open",
                        "priority": "Medium",
                    }
                ],
            }
        )
    }

    adapter = MCPTechnicalSupportAdapter(tools)

    tickets = await adapter.get_customer_tickets("CUST-1001")

    assert len(tickets) == 1
    assert tickets[0].ticket_id == "TCK-1001"
    assert tickets[0].subject == "Monitor delivery"
