import pytest

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from typing import Any, TypedDict

from adapters.agents.middleware.approval_middleware import CustomerApprovalMiddleware


class FakeToolRequest:
    def __init__(self, tool_name, args):
        self.tool_call = {
            "name": tool_name,
            "args": args,
            "id": "test-tool-call",
        }


@pytest.mark.anyio
async def test_normal_tool_does_not_require_approval():
    middleware = CustomerApprovalMiddleware()

    request = FakeToolRequest(
        "get_customer",
        {
            "customer_id": "CUST-1001",
        },
    )

    async def fake_handler(request):
        return "TOOL_EXECUTED"

    result = await middleware.awrap_tool_call(
        request,
        fake_handler,
    )

    assert result == "TOOL_EXECUTED"


@pytest.mark.anyio
async def test_refund_requires_human_approval():
    middleware = CustomerApprovalMiddleware()

    request = FakeToolRequest(
        "refund_payment",
        {
            "customer_id": "CUST-1001",
            "payment_id": "PAY-1001",
        },
    )

    async def fake_handler(request):
        return "REFUND_EXECUTED"

    class TestState(TypedDict, total=False):
        result: Any

    graph = StateGraph(TestState)

    async def approval_node(state):
        result = await middleware.awrap_tool_call(
            request,
            fake_handler,
        )
        return {
            "result": result,
        }

    graph.add_node(
        "approval",
        approval_node,
    )

    graph.add_edge(
        START,
        "approval",
    )

    graph.add_edge(
        "approval",
        END,
    )

    compiled = graph.compile(
        checkpointer=InMemorySaver(),
    )

    config = {
        "configurable": {
            "thread_id": "test-approval",
        }
    }

    result = await compiled.ainvoke(
        {},
        config=config,
    )

    assert "__interrupt__" in result

    interrupt_data = result["__interrupt__"]

    assert interrupt_data

    approval_request = interrupt_data[0]

    assert "HUMAN APPROVAL REQUIRED" in approval_request.value
    assert "refund_payment" in approval_request.value
    assert "CUST-1001" in approval_request.value
    assert "PAY-1001" in approval_request.value
