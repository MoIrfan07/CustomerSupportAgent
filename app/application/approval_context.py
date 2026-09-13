from __future__ import annotations

from contextvars import ContextVar

from app.application.approval_registry import ApprovalRegistry


approval_registry_context: ContextVar[ApprovalRegistry | None] = ContextVar(
    "approval_registry_context",
    default=None,
)

approval_username_context: ContextVar[str] = ContextVar(
    "approval_username_context",
    default="unknown",
)

approval_role_context: ContextVar[str] = ContextVar(
    "approval_role_context",
    default="unknown",
)

approval_customer_id_context: ContextVar[str | None] = ContextVar(
    "approval_customer_id_context",
    default=None,
)

approval_thread_id_context: ContextVar[str | None] = ContextVar(
    "approval_thread_id_context",
    default=None,
)


def set_approval_context(
    *,
    registry: ApprovalRegistry,
    username: str,
    role: str,
    customer_id: str | None,
    thread_id: str,
) -> None:
    """
    Set the approval context for the current request/task.
    """

    approval_registry_context.set(registry)
    approval_username_context.set(username)
    approval_role_context.set(role)
    approval_customer_id_context.set(customer_id)
    approval_thread_id_context.set(thread_id)


def clear_approval_context() -> None:
    """
    Clear the approval context for the current request/task.
    """

    approval_registry_context.set(None)
    approval_username_context.set("unknown")
    approval_role_context.set("unknown")
    approval_customer_id_context.set(None)
    approval_thread_id_context.set(None)


def get_approval_registry() -> ApprovalRegistry | None:
    return approval_registry_context.get()


def get_approval_username() -> str:
    return approval_username_context.get()


def get_approval_role() -> str:
    return approval_role_context.get()


def get_approval_customer_id() -> str | None:
    return approval_customer_id_context.get()


def get_approval_thread_id() -> str | None:
    return approval_thread_id_context.get()
