from contextvars import ContextVar


_request_id: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)


def set_request_id(request_id: str) -> None:
    """
    Set the request ID for the current asynchronous context.
    """

    _request_id.set(request_id)


def get_request_id() -> str | None:
    """
    Return the request ID for the current asynchronous context.
    """

    return _request_id.get()


def clear_request_id() -> None:
    """
    Clear the request ID from the current asynchronous context.
    """

    _request_id.set(None)
