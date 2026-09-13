import pytest
from fastapi.security import HTTPAuthorizationCredentials

from adapters.api.auth import create_access_token, get_optional_current_user


@pytest.mark.anyio
async def test_get_optional_current_user_returns_none_without_credentials():
    user = await get_optional_current_user(None)

    assert user is None


@pytest.mark.anyio
async def test_get_optional_current_user_accepts_valid_customer_token():
    token = create_access_token(
        username="ahmed",
        role="customer",
        customer_id="CUST-1001",
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    user = await get_optional_current_user(credentials)

    assert user is not None
    assert user.username == "ahmed"
    assert user.role == "customer"
    assert user.customer_id == "CUST-1001"


@pytest.mark.anyio
async def test_get_optional_current_user_accepts_valid_manager_token():
    token = create_access_token(
        username="manager",
        role="manager",
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    user = await get_optional_current_user(credentials)

    assert user is not None
    assert user.username == "manager"
    assert user.role == "manager"
    assert user.customer_id is None
