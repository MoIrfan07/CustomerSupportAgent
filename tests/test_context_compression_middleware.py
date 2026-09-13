from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.application.context_compression_policy import ContextCompressionPolicy
from app.application.context_compression_service import ContextCompressionService
from adapters.agents.middleware.context_compression_middleware import (
    ContextCompressionMiddleware,
)


def test_context_compression_middleware_prepares_plan_when_threshold_is_reached() -> (
    None
):
    policy = ContextCompressionPolicy(
        token_threshold=50,
        message_threshold=6,
        preserve_recent_messages=2,
    )

    service = ContextCompressionService(policy=policy)

    middleware = ContextCompressionMiddleware(
        compression_service=service,
    )

    state: dict[str, Any] = {
        "messages": [
            HumanMessage(content="Show me Ahmed's customer information."),
            AIMessage(content="I'll look up Ahmed's customer information."),
            ToolMessage(
                content=(
                    '{"success": true, "customer": '
                    '{"customer_id": "CUST-1001", '
                    '"name": "Ahmed Khan", '
                    '"status": "active"}}'
                ),
                tool_call_id="call-customer-1",
                name="get_customer",
            ),
            AIMessage(content="Ahmed Khan is an active customer."),
            HumanMessage(content="Show me his orders."),
            AIMessage(content="I'll check his orders."),
            ToolMessage(
                content=(
                    '{"success": true, "orders": ['
                    '{"order_id": "ORD-5001", "status": "delivered"}, '
                    '{"order_id": "ORD-5002", "status": "processing"}]}'
                ),
                tool_call_id="call-orders-1",
                name="get_customer_orders",
            ),
            AIMessage(content="Ahmed has two orders."),
            HumanMessage(content="Can I cancel ORD-5002?"),
            AIMessage(content="Cancellation requires approval."),
        ],
        "username": "ahmed",
        "user_role": "customer",
        "customer_id": "CUST-1001",
        "thread_id": "ahmed:session-100",
    }

    middleware.before_model(
        state,
        runtime=None,
    )
