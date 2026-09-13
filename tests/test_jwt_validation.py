from datetime import timedelta

import pytest
from fastapi import HTTPException

from adapters.api.auth import create_access_token, get_current_user


@pytest.mark.anyio
async def test_get_current_user_accepts_valid_customer_token():
    token = create_access_token(
        username="ahmed",
        role="customer",
        customer_id="CUST-1001",
    )

    user = await get_current_user(token)

    assert user is not None
    assert user.username == "ahmed"
    assert user.role == "customer"
    assert user.customer_id == "CUST-1001"


@pytest.mark.anyio
async def test_get_current_user_accepts_valid_manager_token():
    token = create_access_token(
        username="manager",
        role="manager",
    )

    user = await get_current_user(token)

    assert user is not None
    assert user.username == "manager"
    assert user.role == "manager"
    assert user.customer_id is None


@pytest.mark.anyio
async def test_get_current_user_rejects_invalid_token():
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user("this-is-not-a-valid-jwt")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"


@pytest.mark.anyio
async def test_get_current_user_rejects_expired_token():
    token = create_access_token(
        username="ahmed",
        role="customer",
        customer_id="CUST-1001",
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"


@pytest.mark.anyio
async def test_get_current_user_rejects_token_for_unknown_user():
    token = create_access_token(
        username="does-not-exist",
        role="customer",
        customer_id="CUST-9999",
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"
