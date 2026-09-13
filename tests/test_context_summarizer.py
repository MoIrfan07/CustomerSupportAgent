from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.application.context_summarizer import ContextSummarizer


def test_extracts_protected_context() -> None:
    summarizer = ContextSummarizer()

    state = {
        "username": "ahmed",
        "user_role": "customer",
        "customer_id": "CUST-1001",
        "thread_id": "ahmed:session-1",
        "approval_id": "APR-1001",
        "approval_state": "pending",
        "tool_call_id": "call-123",
    }

    result = summarizer.summarize(state)

    protected = result["protected_context"]

    assert protected["username"] == "ahmed"
    assert protected["user_role"] == "customer"
    assert protected["customer_id"] == "CUST-1001"
    assert protected["thread_id"] == "ahmed:session-1"
    assert protected["approval_id"] == "APR-1001"
    assert protected["approval_state"] == "pending"
    assert protected["tool_call_id"] == "call-123"


def test_extracts_approval_context() -> None:
    summarizer = ContextSummarizer()

    approval_context = {
        "approval_id": "APR-2001",
        "tool_name": "refund_payment",
    }

    state = {
        "approval_context": approval_context,
    }

    result = summarizer.summarize(state)

    assert result["protected_context"]["approval_context"] == approval_context


def test_extracts_conversation_messages() -> None:
    summarizer = ContextSummarizer()

    messages = [
        HumanMessage(content="Show Ahmed's orders."),
        AIMessage(content="Ahmed has two orders."),
    ]

    result = summarizer.summarize(
        {
            "messages": messages,
        }
    )

    assert result["conversation_history"] == [
        {
            "role": "user",
            "content": "Show Ahmed's orders.",
        },
        {
            "role": "assistant",
            "content": "Ahmed has two orders.",
        },
    ]


def test_extracts_tool_results_without_rewriting_them() -> None:
    summarizer = ContextSummarizer()

    messages = [
        ToolMessage(
            content='{"success": true, "orders": [{"order_id": "ORD-5001"}]}',
            tool_call_id="call-5001",
            name="get_customer_orders",
        )
    ]

    result = summarizer.summarize(
        {
            "messages": messages,
        }
    )

    assert result["tool_activity"] == [
        {
            "tool_name": "get_customer_orders",
            "tool_call_id": "call-5001",
            "content": '{"success": true, "orders": [{"order_id": "ORD-5001"}]}',
        }
    ]


def test_extracts_active_tool_calls() -> None:
    summarizer = ContextSummarizer()

    messages = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "call-6001",
                    "name": "cancel_order",
                    "args": {
                        "order_id": "ORD-5002",
                    },
                }
            ],
        )
    ]

    result = summarizer.summarize(
        {
            "messages": messages,
        }
    )

    assert result["active_workflow"]["active_tool_calls"] == [
        {
            "id": "call-6001",
            "name": "cancel_order",
            "args": {
                "order_id": "ORD-5002",
            },
        }
    ]


def test_detects_interrupt_state() -> None:
    summarizer = ContextSummarizer()

    result = summarizer.summarize(
        {
            "__interrupt__": ["approval-required"],
        }
    )

    assert result["active_workflow"]["interrupt_present"] is True


def test_extracts_pending_approval_state() -> None:
    summarizer = ContextSummarizer()

    pending_approval = {
        "approval_id": "APR-7001",
        "tool_name": "refund_payment",
    }

    result = summarizer.summarize(
        {
            "pending_approval": pending_approval,
        }
    )

    assert result["active_workflow"]["pending_approval"] == pending_approval


def test_summarizer_does_not_modify_state() -> None:
    summarizer = ContextSummarizer()

    messages = [
        HumanMessage(content="Show my orders."),
        AIMessage(content="Here are your orders."),
    ]

    state = {
        "username": "ahmed",
        "user_role": "customer",
        "customer_id": "CUST-1001",
        "thread_id": "ahmed:session-2",
        "messages": messages,
    }

    original_state = dict(state)

    result = summarizer.summarize(state)

    assert state == original_state
    assert result is not state


def test_invalid_messages_state_is_handled() -> None:
    summarizer = ContextSummarizer()

    result = summarizer.summarize(
        {
            "messages": "not-a-list",
        }
    )

    assert result["conversation_history"] == []
    assert result["tool_activity"] == []
    assert result["active_workflow"] == {}


def test_empty_state_returns_safe_empty_summary() -> None:
    summarizer = ContextSummarizer()

    result = summarizer.summarize({})

    assert result == {
        "protected_context": {},
        "active_workflow": {},
        "conversation_history": [],
        "tool_activity": [],
    }
