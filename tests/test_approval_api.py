import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from langgraph.types import Command

from adapters.api.auth import User
from adapters.api.main import approve_operation
from app.application.approval_registry import ApprovalRegistry


class FakeAgent:
    def __init__(self, result=None):
        self.result = result or {
            "messages": [
                type(
                    "Message",
                    (),
                    {"content": ("The requested operation was completed.")},
                )()
            ]
        }

        self.calls = []

    async def ainvoke(
        self,
        input_data,
        *,
        config,
    ):
        self.calls.append(
            {
                "input": input_data,
                "config": config,
            }
        )

        return self.result


class DecisionRecordingAgent(FakeAgent):
    def __init__(
        self,
        registry: ApprovalRegistry,
        approval_id: str,
        result=None,
    ):
        super().__init__(result=result)

        self.registry = registry
        self.approval_id = approval_id
        self.decision_seen_during_resume = None

    async def ainvoke(
        self,
        input_data,
        *,
        config,
    ):
        approval = self.registry.get(self.approval_id)

        self.decision_seen_during_resume = (
            approval.decision if approval is not None else None
        )

        return await super().ainvoke(
            input_data,
            config=config,
        )


class FakeAgentProvider:
    def __init__(
        self,
        agent,
    ):
        self.agent = agent

    async def get_agent(
        self,
        *,
        user_role,
        username,
        customer_id=None,
    ):
        return self.agent


def create_test_app(
    *,
    agent=None,
) -> FastAPI:
    app = FastAPI()

    approval_registry = ApprovalRegistry()

    fake_agent = agent or FakeAgent()

    agent_provider = FakeAgentProvider(fake_agent)

    app.state.application = type(
        "ApplicationState",
        (),
        {
            "approval_registry": approval_registry,
            "agent_provider": agent_provider,
        },
    )()

    app.include_router(_build_router())

    return app


def _build_router():
    from fastapi import APIRouter

    router = APIRouter()

    router.add_api_route(
        "/approvals/{approval_id}",
        approve_operation,
        methods=["POST"],
    )

    return router


def override_manager(app):
    from adapters.api.auth import get_current_user

    app.dependency_overrides[get_current_user] = lambda: User(
        username="manager",
        role="manager",
        customer_id=None,
    )


def override_support(app):
    from adapters.api.auth import get_current_user

    app.dependency_overrides[get_current_user] = lambda: User(
        username="support",
        role="support",
        customer_id=None,
    )


@pytest.mark.anyio
async def test_approval_endpoint_resumes_owned_request():
    app = create_test_app()

    registry = app.state.application.approval_registry

    agent = app.state.application.agent_provider.agent

    registry.create(
        approval_id="approval-1",
        username="manager",
        role="manager",
        customer_id=None,
        thread_id="manager:test-thread",
        tool_name="refund_payment",
        tool_call_id="tool-call-1",
    )

    override_manager(app)

    client = TestClient(app)

    response = client.post(
        "/approvals/approval-1",
        json={
            "approved": True,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["approval_id"] == "approval-1"
    assert body["status"] == "approved"
    assert body["tool_name"] == "refund_payment"
    assert body["thread_id"] == "manager:test-thread"

    assert body["message"] == ("The requested operation was completed.")

    assert not registry.contains("approval-1")

    assert len(agent.calls) == 1

    call = agent.calls[0]

    assert call["config"] == {
        "configurable": {
            "thread_id": "manager:test-thread",
        }
    }

    assert isinstance(call["input"], Command)

    assert call["input"].resume is True


@pytest.mark.anyio
async def test_approval_endpoint_resumes_with_rejection():
    app = create_test_app()

    registry = app.state.application.approval_registry

    agent = app.state.application.agent_provider.agent

    registry.create(
        approval_id="approval-2",
        username="manager",
        role="manager",
        customer_id=None,
        thread_id="manager:test-thread",
        tool_name="cancel_order",
        tool_call_id="tool-call-2",
    )

    override_manager(app)

    client = TestClient(app)

    response = client.post(
        "/approvals/approval-2",
        json={
            "approved": False,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["approval_id"] == "approval-2"
    assert body["status"] == "rejected"
    assert body["tool_name"] == "cancel_order"

    assert not registry.contains("approval-2")

    assert len(agent.calls) == 1

    call = agent.calls[0]

    assert call["config"] == {
        "configurable": {
            "thread_id": "manager:test-thread",
        }
    }

    assert isinstance(call["input"], Command)

    assert call["input"].resume is False


@pytest.mark.anyio
async def test_approval_decision_is_stored_before_resume():
    registry = ApprovalRegistry()

    registry.create(
        approval_id="approval-3",
        username="manager",
        role="manager",
        customer_id=None,
        thread_id="manager:test-thread",
        tool_name="refund_payment",
        tool_call_id="tool-call-3",
    )

    agent = DecisionRecordingAgent(
        registry=registry,
        approval_id="approval-3",
    )

    app = create_test_app(agent=agent)

    # Use the registry belonging to the test application.
    app_registry = app.state.application.approval_registry

    approval = app_registry.create(
        approval_id="approval-3",
        username="manager",
        role="manager",
        customer_id=None,
        thread_id="manager:test-thread",
        tool_name="refund_payment",
        tool_call_id="tool-call-3",
    )

    # Replace the agent's registry reference with the application's
    # registry so it observes the exact record used by the endpoint.
    agent.registry = app_registry
    agent.approval_id = approval.approval_id

    override_manager(app)

    client = TestClient(app)

    response = client.post(
        "/approvals/approval-3",
        json={
            "approved": True,
        },
    )

    assert response.status_code == 200

    assert agent.decision_seen_during_resume is True

    assert not app_registry.contains("approval-3")


@pytest.mark.anyio
async def test_approval_endpoint_rejects_other_user():
    app = create_test_app()

    registry = app.state.application.approval_registry

    registry.create(
        approval_id="approval-4",
        username="manager",
        role="manager",
        customer_id=None,
        thread_id="manager:test-thread",
        tool_name="refund_payment",
        tool_call_id="tool-call-4",
    )

    override_support(app)

    client = TestClient(app)

    response = client.post(
        "/approvals/approval-4",
        json={
            "approved": True,
        },
    )

    assert response.status_code == 403

    assert registry.contains("approval-4")


@pytest.mark.anyio
async def test_approval_endpoint_returns_404_for_unknown_approval():
    app = create_test_app()

    override_manager(app)

    client = TestClient(app)

    response = client.post(
        "/approvals/does-not-exist",
        json={
            "approved": True,
        },
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_approval_endpoint_rejects_non_manager():
    app = create_test_app()

    registry = app.state.application.approval_registry

    registry.create(
        approval_id="approval-5",
        username="support",
        role="support",
        customer_id=None,
        thread_id="support:test-thread",
        tool_name="refund_payment",
        tool_call_id="tool-call-5",
    )

    override_support(app)

    client = TestClient(app)

    response = client.post(
        "/approvals/approval-5",
        json={
            "approved": True,
        },
    )

    assert response.status_code == 403

    assert registry.contains("approval-5")


@pytest.mark.anyio
async def test_approval_registry_finds_decided_approval_for_same_tool_call():
    registry = ApprovalRegistry()

    registry.create(
        approval_id="approval-6",
        username="manager",
        role="manager",
        customer_id=None,
        thread_id="manager:test-thread",
        tool_name="refund_payment",
        tool_call_id="tool-call-6",
    )

    registry.set_decision(
        approval_id="approval-6",
        approved=True,
    )

    approval = registry.find_for_tool_call(
        thread_id="manager:test-thread",
        tool_name="refund_payment",
        tool_call_id="tool-call-6",
    )

    assert approval is not None
    assert approval.approval_id == "approval-6"
    assert approval.decision is True


@pytest.mark.anyio
async def test_approval_registry_does_not_mix_tool_calls():
    registry = ApprovalRegistry()

    registry.create(
        approval_id="approval-7",
        username="manager",
        role="manager",
        customer_id=None,
        thread_id="manager:test-thread",
        tool_name="refund_payment",
        tool_call_id="tool-call-7",
    )

    registry.create(
        approval_id="approval-8",
        username="manager",
        role="manager",
        customer_id=None,
        thread_id="manager:test-thread",
        tool_name="refund_payment",
        tool_call_id="tool-call-8",
    )

    first = registry.find_for_tool_call(
        thread_id="manager:test-thread",
        tool_name="refund_payment",
        tool_call_id="tool-call-7",
    )

    second = registry.find_for_tool_call(
        thread_id="manager:test-thread",
        tool_name="refund_payment",
        tool_call_id="tool-call-8",
    )

    assert first is not None
    assert second is not None

    assert first.approval_id == "approval-7"
    assert second.approval_id == "approval-8"


@pytest.mark.anyio
async def test_approval_endpoint_rejects_different_second_decision():
    app = create_test_app()

    registry = app.state.application.approval_registry

    registry.create(
        approval_id="approval-9",
        username="manager",
        role="manager",
        customer_id=None,
        thread_id="manager:test-thread",
        tool_name="refund_payment",
        tool_call_id="tool-call-9",
    )

    registry.set_decision(
        approval_id="approval-9",
        approved=True,
    )

    override_manager(app)

    client = TestClient(app)

    response = client.post(
        "/approvals/approval-9",
        json={
            "approved": False,
        },
    )

    assert response.status_code == 409

    assert registry.contains("approval-9")

    approval = registry.get("approval-9")

    assert approval is not None
    assert approval.decision is True


@pytest.mark.anyio
async def test_approval_endpoint_rejects_second_submission():
    app = create_test_app()

    registry = app.state.application.approval_registry
    agent = app.state.application.agent_provider.agent

    registry.create(
        approval_id="approval-10",
        username="manager",
        role="manager",
        customer_id=None,
        thread_id="manager:test-thread",
        tool_name="refund_payment",
        tool_call_id="tool-call-10",
    )

    # Simulate the first decision already being recorded.
    registry.set_decision(
        approval_id="approval-10",
        approved=True,
    )

    override_manager(app)

    client = TestClient(app)

    response = client.post(
        "/approvals/approval-10",
        json={
            "approved": True,
        },
    )

    assert response.status_code == 409

    body = response.json()

    assert body["detail"]["error"] == "approval_already_decided"
    assert body["detail"]["approval_id"] == "approval-10"

    # The second submission must never resume the agent.
    assert len(agent.calls) == 0

    # The original approval remains in the registry because the
    # second request did not consume or modify it.
    assert registry.contains("approval-10")

    approval = registry.get("approval-10")

    assert approval is not None
    assert approval.decision is True
