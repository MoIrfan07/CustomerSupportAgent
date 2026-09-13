from fastapi import Request

from app.application.customer_support import CustomerSupportApplication
from app.infrastructure.state import ApplicationState


def get_application_state(
    request: Request,
) -> ApplicationState:
    """Return the application's runtime state."""

    return request.app.state.runtime


def get_services(
    request: Request,
) -> CustomerSupportApplication:
    """Return the application's customer support services."""

    return request.app.state.runtime.services
