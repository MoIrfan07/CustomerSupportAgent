from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.application.context_compression_policy import ContextCompressionPolicy
from app.application.context_compression_service import ContextCompressionService
from adapters.agents.middleware.context_compression_middleware import (
    ContextCompressionMiddleware,
)


def test_context_compression_middleware_is_non_destructive() -> None:
    policy = ContextCompressionPolicy(
        token_threshold=50,
        message_threshold=6,
        preserve_recent_messages=2,
    )

    service = ContextCompressionService(policy=policy)

    middleware = ContextCompressionMiddleware(
        compression_service=service,
    )

    messages = [
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
    ]

    state: dict[str, Any] = {
        "messages": messages,
        "username": "ahmed",
        "user_role": "customer",
        "customer_id": "CUST-1001",
        "thread_id": "ahmed:session-100",
    }

    original_state = dict(state)
    original_messages = list(messages)

    middleware.before_model(
        state,
        runtime=None,
    )

    assert state == original_state
    assert state["messages"] == original_messages
    assert state["username"] == "ahmed"
    assert state["user_role"] == "customer"
    assert state["customer_id"] == "CUST-1001"
    assert state["thread_id"] == "ahmed:session-100"


def test_context_compression_middleware_preserves_business_facts() -> None:
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

    metrics = {
        "approximate_tokens": 2_000,
        "message_count": 10,
        "interrupt_count": 0,
    }

    result = service.prepare(state, metrics)

    assert result.eligible is True
    assert len(result.business_facts) == 2

    assert result.business_facts[0]["tool_name"] == "get_customer"
    assert result.business_facts[0]["facts"] == {
        "customer_id": "CUST-1001",
        "name": "Ahmed Khan",
        "status": "active",
    }

    assert result.business_facts[1]["tool_name"] == "get_customer_orders"
    assert result.business_facts[1]["facts"] == {
        "orders": [
            {
                "order_id": "ORD-5001",
                "status": "delivered",
            },
            {
                "order_id": "ORD-5002",
                "status": "processing",
            },
        ]
    }


def test_context_compression_middleware_preserves_recent_messages() -> None:
    policy = ContextCompressionPolicy(
        token_threshold=50,
        message_threshold=6,
        preserve_recent_messages=2,
    )

    service = ContextCompressionService(policy=policy)

    middleware = ContextCompressionMiddleware(
        compression_service=service,
    )

    messages = [
        HumanMessage(content="Historical customer question."),
        AIMessage(content="Historical answer."),
        ToolMessage(
            content=(
                '{"success": true, "customer": '
                '{"customer_id": "CUST-1001", '
                '"name": "Ahmed Khan"}}'
            ),
            tool_call_id="call-customer-1",
            name="get_customer",
        ),
        AIMessage(content="Historical customer summary."),
        HumanMessage(content="Can I cancel ORD-5002?"),
        AIMessage(content="Cancellation requires approval."),
        HumanMessage(content="Yes, cancel it."),
        AIMessage(content="Approval is required before cancellation."),
    ]

    state: dict[str, Any] = {
        "messages": messages,
        "username": "ahmed",
        "user_role": "customer",
        "customer_id": "CUST-1001",
        "thread_id": "ahmed:session-100",
    }

    middleware.before_model(
        state,
        runtime=None,
    )

    result = service.prepare(
        state,
        {
            "approximate_tokens": 2_000,
            "message_count": len(messages),
            "interrupt_count": 0,
        },
    )

    assert result.eligible is True

    assert result.preserved_messages[:2] == messages[-2:]

    assert result.preserved_messages[-1:] == [messages[2]]
