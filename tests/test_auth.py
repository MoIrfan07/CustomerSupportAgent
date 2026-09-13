import os

from adapters.api.auth import authenticate_user


AHMED_TEST_PASSWORD = os.getenv("TEST_AHMED_PASSWORD")


def test_authenticate_user_with_valid_username():
    assert AHMED_TEST_PASSWORD is not None, (
        "TEST_AHMED_PASSWORD environment variable is required"
    )

    user = authenticate_user("ahmed", AHMED_TEST_PASSWORD)

    assert user is not None
    assert user.username == "ahmed"
    assert user.role == "customer"
    assert user.customer_id == "CUST-1001"


def test_authenticate_user_with_invalid_password():
    user = authenticate_user("ahmed", "incorrect-password")

    assert user is None


def test_authenticate_user_with_unknown_user():
    user = authenticate_user("does-not-exist", "some-password")

    assert user is None
