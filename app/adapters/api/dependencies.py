from fastapi import Request

from app.infrastructure.state import ApplicationState


def get_application_state(
    request: Request,
) -> ApplicationState:
    """Return the application's runtime state."""

    application_state = getattr(request.app.state, "application", None)
    if application_state is None:
        raise RuntimeError("Application state is not initialized")
    return application_state
