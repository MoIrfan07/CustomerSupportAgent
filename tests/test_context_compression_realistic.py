from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.application.context_compression_policy import (
    ContextCompressionPolicy,
)
from app.application.context_compression_service import (
    ContextCompressionService,
)


def test_realistic_customer_support_context_compression() -> None:
    policy = ContextCompressionPolicy(
        token_threshold=100,
        message_threshold=10,
        preserve_recent_messages=4,
    )

    service = ContextCompressionService(policy=policy)

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
        AIMessage(
            content=("Ahmed Khan is an active customer with customer ID CUST-1001.")
        ),
        HumanMessage(content="Show me his orders."),
        AIMessage(content="I'll check Ahmed's orders."),
        ToolMessage(
            content=(
                '{"success": true, "orders": ['
                '{"order_id": "ORD-5001", "status": "delivered"}, '
                '{"order_id": "ORD-5002", "status": "processing"}]}'
            ),
            tool_call_id="call-orders-1",
            name="get_customer_orders",
        ),
        AIMessage(
            content=(
                "Ahmed has two orders: "
                "ORD-5001 is delivered and "
                "ORD-5002 is processing."
            )
        ),
        HumanMessage(content="Can I cancel ORD-5002?"),
        AIMessage(
            content=("ORD-5002 can be cancelled, but this is a sensitive operation.")
        ),
        HumanMessage(content="Yes, cancel it."),
        AIMessage(content="Approval is required before cancellation."),
    ]

    state = {
        "messages": messages,
        "username": "ahmed",
        "user_role": "customer",
        "customer_id": "CUST-1001",
        "thread_id": "ahmed:session-100",
    }

    metrics = {
        "approximate_tokens": 2_000,
        "message_count": len(messages),
        "interrupt_count": 0,
    }

    result = service.prepare(state, metrics)

    assert result.eligible is True

    print("\n" + "=" * 70)
    print("CONTEXT COMPRESSION INSPECTION")
    print("=" * 70)

    print("\nPROTECTED CONTEXT:")
    for key, value in result.summary["protected_context"].items():
        print(f"  {key}: {value}")

    print("\nMESSAGES TO COMPRESS:")
    for index, message in enumerate(result.messages_to_compress, start=1):
        print(f"  {index}. {message.__class__.__name__}: {message.content}")

    print("\nPRESERVED MESSAGES:")
    for index, message in enumerate(result.preserved_messages, start=1):
        print(f"  {index}. {message.__class__.__name__}: {message.content}")

    print("\nTOOL ACTIVITY:")
    for item in result.summary["tool_activity"]:
        print(f"  {item['tool_name']} ({item['tool_call_id']}): {item['content']}")

    print("\nBUSINESS FACTS:")
    for item in result.business_facts:
        print(f"  {item['tool_name']} ({item['tool_call_id']}): {item['facts']}")

    print("=" * 70)

    # Protected identity/context required to continue the conversation.
    assert result.summary["protected_context"]["username"] == "ahmed"
    assert result.summary["protected_context"]["user_role"] == "customer"
    assert result.summary["protected_context"]["customer_id"] == "CUST-1001"
    assert result.summary["protected_context"]["thread_id"] == ("ahmed:session-100")

    # Four most-recent messages are preserved because they contain
    # the active sensitive operation and approval flow.
    assert result.preserved_messages[:4] == messages[-4:]

    # The two business ToolMessages are preserved separately so their
    # authoritative facts are not lost during future compression.
    preserved_tool_messages = [
        message
        for message in result.preserved_messages
        if isinstance(message, ToolMessage)
    ]

    assert len(preserved_tool_messages) == 2

    assert preserved_tool_messages[0] == messages[2]
    assert preserved_tool_messages[1] == messages[6]

    # Six messages are actual compression candidates:
    #   1. Human customer-information request
    #   2. AI lookup message
    #   3. AI customer summary
    #   4. Human orders request
    #   5. AI orders lookup message
    #   6. AI orders summary
    assert result.compressed_message_count == 6

    # Four recent messages + two protected business tool results.
    assert result.preserved_message_count == 6

    assert len(result.messages_to_compress) == 6

    # Business facts extracted from the protected tool results must
    # remain available independently of the original ToolMessages.
    assert len(result.business_facts) == 2

    assert result.business_facts[0]["tool_name"] == "get_customer"
    assert result.business_facts[0]["tool_call_id"] == "call-customer-1"
    assert result.business_facts[0]["facts"] == {
        "customer_id": "CUST-1001",
        "name": "Ahmed Khan",
        "status": "active",
    }

    assert result.business_facts[1]["tool_name"] == "get_customer_orders"
    assert result.business_facts[1]["tool_call_id"] == "call-orders-1"
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

    # Tool activity is intentionally empty here because these business
    # ToolMessages are classified as protected business data rather
    # than ordinary tool activity.
    assert result.summary["tool_activity"] == []
