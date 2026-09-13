import pytest

from langchain_core.messages import ToolCall
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from adapters.agents.middleware.approval_middleware import CustomerApprovalMiddleware


def refund_payment(customer_id: str, payment_id: str) -> dict:
    """Simulated refund operation."""
    return {
        "success": True,
        "message": f"Payment {payment_id} refunded for customer {customer_id}.",
    }


refund_tool = StructuredTool.from_function(
    func=refund_payment,
    name="refund_payment",
    description="Refund a payment for a customer.",
)


class ToolRequest:
    """Minimal tool-call request compatible with the approval middleware."""

    def __init__(self, tool_name: str, args: dict, tool_call_id: str):
        self.tool_call = {
            "name": tool_name,
            "args": args,
            "id": tool_call_id,
        }


@pytest.mark.anyio
async def test_refund_requires_human_approval():
    middleware = CustomerApprovalMiddleware()

    request = ToolRequest(
        tool_name="refund_payment",
        args={
            "customer_id": "CUST-1001",
            "payment_id": "PAY-1001",
        },
        tool_call_id="refund-call-1",
    )

    async def handler(_request):
        return {
            "success": True,
            "message": "Refund executed.",
        }

    # The middleware calls interrupt(), so this must execute inside
    # a LangGraph checkpointed graph.
    from langgraph.graph import END, START, StateGraph
    from typing import TypedDict, Any

    class TestState(TypedDict, total=False):
        result: Any

    graph = StateGraph(TestState)

    async def approval_node(state):
        result = await middleware.awrap_tool_call(
            request,
            handler,
        )
        return {"result": result}

    graph.add_node("approval", approval_node)
    graph.add_edge(START, "approval")
    graph.add_edge("approval", END)

    compiled = graph.compile(checkpointer=InMemorySaver())

    config = {
        "configurable": {
            "thread_id": "test-refund-approval",
        }
    }

    result = await compiled.ainvoke(
        {},
        config=config,
    )

    assert "__interrupt__" in result

    interrupts = result["__interrupt__"]

    assert interrupts

    approval_request = interrupts[0]

    assert "HUMAN APPROVAL REQUIRED" in approval_request.value
    assert "refund_payment" in approval_request.value
    assert "CUST-1001" in approval_request.value
    assert "PAY-1001" in approval_request.value


@pytest.mark.anyio
async def test_approved_refund_resumes_and_executes():
    middleware = CustomerApprovalMiddleware()

    request = ToolRequest(
        tool_name="refund_payment",
        args={
            "customer_id": "CUST-1001",
            "payment_id": "PAY-1001",
        },
        tool_call_id="refund-call-2",
    )

    execution_count = 0

    async def handler(_request):
        nonlocal execution_count

        execution_count += 1

        return {
            "success": True,
            "message": "Payment PAY-1001 refunded for customer CUST-1001.",
        }

    from langgraph.graph import END, START, StateGraph
    from typing import TypedDict, Any

    class TestState(TypedDict, total=False):
        result: Any

    graph = StateGraph(TestState)

    async def approval_node(state):
        result = await middleware.awrap_tool_call(
            request,
            handler,
        )
        return {"result": result}

    graph.add_node("approval", approval_node)
    graph.add_edge(START, "approval")
    graph.add_edge("approval", END)

    checkpointer = InMemorySaver()

    compiled = graph.compile(
        checkpointer=checkpointer,
    )

    config = {
        "configurable": {
            "thread_id": "test-approved-refund",
        }
    }

    first_result = await compiled.ainvoke(
        {},
        config=config,
    )

    assert "__interrupt__" in first_result

    resumed_result = await compiled.ainvoke(
        Command(resume=True),
        config=config,
    )

    assert "__interrupt__" not in resumed_result

    assert execution_count == 1

    assert resumed_result["result"]["success"] is True

    assert "PAY-1001" in resumed_result["result"]["message"]

    assert "CUST-1001" in resumed_result["result"]["message"]
