from unittest.mock import AsyncMock

import httpx
import openai
import pytest
from fastapi.testclient import TestClient

from adapters.api.main import app


def _build_api_error(error_type):
    request = httpx.Request(
        "POST",
        "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
    )

    response = httpx.Response(
        status_code=429 if error_type is openai.RateLimitError else 401,
        request=request,
    )

    if error_type is openai.RateLimitError:
        return openai.RateLimitError(
            message="simulated quota failure",
            response=response,
            body=None,
        )

    if error_type is openai.AuthenticationError:
        return openai.AuthenticationError(
            message="simulated authentication failure",
            response=response,
            body=None,
        )

    raise ValueError(f"Unsupported error type: {error_type}")


@pytest.mark.parametrize(
    ("error_type", "expected_status"),
    [
        (openai.RateLimitError, 503),
        (openai.AuthenticationError, 502),
    ],
)
def test_qwen_provider_errors_are_safely_mapped(
    error_type,
    expected_status,
):
    mock_agent = AsyncMock()
    mock_agent.ainvoke.side_effect = _build_api_error(error_type)

    class FakeAgentProvider:
        async def get_agent(
            self,
            user_role,
            username,
            customer_id=None,
        ):
            return mock_agent

    with TestClient(app) as client:
        original_provider = app.state.application.agent_provider
        app.state.application.agent_provider = FakeAgentProvider()

        try:
            response = client.post(
                "/chat",
                json={
                    "message": "Hello",
                    "thread_id": "provider-error-test",
                },
            )
        finally:
            app.state.application.agent_provider = original_provider

    assert response.status_code == expected_status

    body = response.json()

    assert body["detail"]["request_id"]
    assert "simulated" not in str(body)
    assert "quota" not in str(body).lower()
    assert "authentication failure" not in str(body).lower()
