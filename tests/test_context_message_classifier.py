from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.application.context_message_classifier import (
    ContextMessageCategory,
    ContextMessageClassifier,
)


def test_classifies_user_message_as_compressible() -> None:
    classifier = ContextMessageClassifier()

    message = HumanMessage(content="Show me my orders.")

    result = classifier.classify(message)

    assert result.category == ContextMessageCategory.USER_MESSAGE
    assert result.is_business_data is False
    assert result.is_active_workflow is False
    assert result.is_candidate_for_compression is True
    assert result.reason == "ordinary_user_message"


def test_classifies_normal_assistant_message_as_compressible() -> None:
    classifier = ContextMessageClassifier()

    message = AIMessage(content="You have two orders.")

    result = classifier.classify(message)

    assert result.category == ContextMessageCategory.ASSISTANT_MESSAGE
    assert result.is_business_data is False
    assert result.is_active_workflow is False
    assert result.is_candidate_for_compression is True
    assert result.reason == "ordinary_assistant_message"


def test_classifies_customer_tool_result_as_business_data() -> None:
    classifier = ContextMessageClassifier()

    message = ToolMessage(
        content='{"success": true, "customer_id": "CUST-1001"}',
        tool_call_id="call-1001",
        name="get_customer",
    )

    result = classifier.classify(message)

    assert result.category == ContextMessageCategory.TOOL_RESULT
    assert result.is_business_data is True
    assert result.is_active_workflow is False
    assert result.is_candidate_for_compression is False
    assert result.reason == "business_tool_result"


def test_classifies_order_tool_result_as_business_data() -> None:
    classifier = ContextMessageClassifier()

    message = ToolMessage(
        content=('{"success": true, "orders": [{"order_id": "ORD-5002"}]}'),
        tool_call_id="call-1002",
        name="get_customer_orders",
    )

    result = classifier.classify(message)

    assert result.category == ContextMessageCategory.TOOL_RESULT
    assert result.is_business_data is True
    assert result.is_candidate_for_compression is False
    assert result.reason == "business_tool_result"


def test_classifies_non_business_tool_result_as_compressible() -> None:
    classifier = ContextMessageClassifier()

    message = ToolMessage(
        content="Framework operation completed.",
        tool_call_id="call-1003",
        name="some_framework_tool",
    )

    result = classifier.classify(message)

    assert result.category == ContextMessageCategory.TOOL_RESULT
    assert result.is_business_data is False
    assert result.is_active_workflow is False
    assert result.is_candidate_for_compression is True
    assert result.reason == "non_business_tool_result"


def test_classifies_business_tool_call() -> None:
    classifier = ContextMessageClassifier()

    message = AIMessage(
        content="",
        tool_calls=[
            {
                "id": "call-1004",
                "name": "get_customer_orders",
                "args": {
                    "customer_id": "CUST-1001",
                },
            }
        ],
    )

    result = classifier.classify(message)

    assert result.category == ContextMessageCategory.ACTIVE_TOOL_CALL
    assert result.is_business_data is True
    assert result.is_active_workflow is False
    assert result.is_candidate_for_compression is False
    assert result.reason == "business_tool_call"


def test_classifies_sensitive_tool_call_as_active_workflow() -> None:
    classifier = ContextMessageClassifier()

    message = AIMessage(
        content="",
        tool_calls=[
            {
                "id": "call-1005",
                "name": "cancel_order",
                "args": {
                    "order_id": "ORD-5002",
                },
            }
        ],
    )

    result = classifier.classify(message)

    assert result.category == ContextMessageCategory.ACTIVE_TOOL_CALL
    assert result.is_business_data is True
    assert result.is_active_workflow is True
    assert result.is_candidate_for_compression is False
    assert result.reason == "sensitive_business_tool_call"


def test_classifies_sensitive_refund_tool_call_as_active_workflow() -> None:
    classifier = ContextMessageClassifier()

    message = AIMessage(
        content="",
        tool_calls=[
            {
                "id": "call-1006",
                "name": "refund_payment",
                "args": {
                    "payment_id": "PAY-1001",
                },
            }
        ],
    )

    result = classifier.classify(message)

    assert result.category == ContextMessageCategory.ACTIVE_TOOL_CALL
    assert result.is_business_data is True
    assert result.is_active_workflow is True
    assert result.is_candidate_for_compression is False
    assert result.reason == "sensitive_business_tool_call"


def test_classifies_unknown_message_safely() -> None:
    classifier = ContextMessageClassifier()

    class UnknownMessage:
        content = "unknown"

    result = classifier.classify(UnknownMessage())  # type: ignore[arg-type]

    assert result.category == ContextMessageCategory.UNKNOWN
    assert result.is_business_data is False
    assert result.is_active_workflow is False
    assert result.is_candidate_for_compression is False
    assert result.reason == "unknown_message_type"


def test_classifies_multiple_messages() -> None:
    classifier = ContextMessageClassifier()

    messages = [
        HumanMessage(content="Show my orders."),
        AIMessage(content="I'll check."),
        ToolMessage(
            content='{"success": true}',
            tool_call_id="call-1007",
            name="get_customer_orders",
        ),
    ]

    results = classifier.classify_messages(messages)

    assert len(results) == 3

    assert results[0].category == ContextMessageCategory.USER_MESSAGE
    assert results[1].category == ContextMessageCategory.ASSISTANT_MESSAGE
    assert results[2].category == ContextMessageCategory.TOOL_RESULT


def test_detects_business_data() -> None:
    classifier = ContextMessageClassifier()

    messages = [
        HumanMessage(content="Show my orders."),
        ToolMessage(
            content='{"success": true}',
            tool_call_id="call-1008",
            name="get_customer_orders",
        ),
    ]

    results = classifier.classify_messages(messages)

    assert classifier.contains_business_data(results) is True


def test_detects_active_workflow() -> None:
    classifier = ContextMessageClassifier()

    messages = [
        HumanMessage(content="Refund my payment."),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "call-1009",
                    "name": "refund_payment",
                    "args": {
                        "payment_id": "PAY-1001",
                    },
                }
            ],
        ),
    ]

    results = classifier.classify_messages(messages)

    assert classifier.contains_active_workflow(results) is True


def test_returns_only_compression_candidates() -> None:
    classifier = ContextMessageClassifier()

    messages = [
        HumanMessage(content="Show my orders."),
        ToolMessage(
            content='{"success": true}',
            tool_call_id="call-1010",
            name="get_customer_orders",
        ),
        AIMessage(content="Your order is processing."),
    ]

    results = classifier.classify_messages(messages)

    candidates = classifier.compression_candidates(results)

    assert len(candidates) == 2

    assert candidates[0].category == (ContextMessageCategory.USER_MESSAGE)
    assert candidates[1].category == (ContextMessageCategory.ASSISTANT_MESSAGE)


def test_business_tool_result_is_not_compression_candidate() -> None:
    classifier = ContextMessageClassifier()

    message = ToolMessage(
        content='{"success": true}',
        tool_call_id="call-1011",
        name="get_customer_payments",
    )

    result = classifier.classify(message)

    assert result.is_business_data is True
    assert result.is_candidate_for_compression is False


def test_classifier_does_not_modify_original_message() -> None:
    classifier = ContextMessageClassifier()

    message = HumanMessage(content="Show Ahmed's orders.")

    original_content = message.content

    result = classifier.classify(message)

    assert result.message is message
    assert message.content == original_content
