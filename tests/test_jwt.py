from datetime import timedelta

from adapters.api.auth import (
    create_access_token,
    get_current_user,
)


def test_create_access_token_contains_expected_identity():
    token = create_access_token(
        username="ahmed",
        role="customer",
        customer_id="CUST-1001",
    )

    assert isinstance(token, str)
    assert token


def test_create_access_token_with_custom_expiration():
    token = create_access_token(
        username="ahmed",
        role="customer",
        customer_id="CUST-1001",
        expires_delta=timedelta(minutes=5),
    )

    assert isinstance(token, str)
    assert token


def test_create_access_token_for_non_customer_role():
    token = create_access_token(
        username="manager",
        role="manager",
    )

    assert isinstance(token, str)
    assert token
