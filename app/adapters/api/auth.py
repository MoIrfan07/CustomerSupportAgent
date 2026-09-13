from typing import Annotated
import os

from fastapi import (
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordRequestForm,
)
from pydantic import BaseModel
from pwdlib import PasswordHash

from app.application.session_manager import (
    SessionManager,
    SessionPrincipal,
)


# ============================================
# SESSION CONFIGURATION
# ============================================

SESSION_COOKIE_NAME = "customer_support_session"

SESSION_COOKIE_MAX_AGE = 8 * 60 * 60

SESSION_COOKIE_SECURE = (
    os.getenv(
        "SESSION_COOKIE_SECURE",
        "false",
    ).lower()
    == "true"
)


# ============================================
# PASSWORD HASHING
# ============================================

password_hash = PasswordHash.recommended()


# ============================================
# USERS
# ============================================

# Authentication owns the account identity.
# MCP remains the source of truth for customer
# information.
#
# customer_id only establishes ownership:
#
# ahmed -> CUST-1001
# john  -> CUST-1002
#
# Customer name, email, plan, status, orders,
# invoices, payments, tickets, etc. remain in MCP.
# ============================================

USERS = {
    "manager": {
        "username": "manager",
        "role": "manager",
        "customer_id": None,
        "hashed_password": (
            "$argon2id$v=19$m=65536,t=3,p=4$"
            "wpwV80k35M0Jz8jGiBf0qQ$"
            "7zx/9Ca6j062h3qDFZ3B3rgYB0Cycy566zDhgDiOtXo"
        ),
    },
    "support": {
        "username": "support",
        "role": "support",
        "customer_id": None,
        "hashed_password": (
            "$argon2id$v=19$m=65536,t=3,p=4$"
            "FzZbmJUvZJnKIKHRpoB8Dw$"
            "CG+uusrIdbTVd5ssyyxl8hah5DtOU3eAiEDh8vK+x+E"
        ),
    },
    "ahmed": {
        "username": "ahmed",
        "role": "customer",
        "customer_id": "CUST-1001",
        "hashed_password": (
            "$argon2id$v=19$m=65536,t=3,p=4$"
            "sTZUXNJkKsK0MNpH3D1g7A$"
            "f95HoLSeL4kRGwFy1xZgMqHC5U4hiR8ucRicxaRKGIc"
        ),
    },
    "john": {
        "username": "john",
        "role": "customer",
        "customer_id": "CUST-1002",
        "hashed_password": (
            "$argon2id$v=19$m=65536,t=3,p=4$"
            "klrUA2VXfCtJIpvmsWB/SQ$"
            "fDcjMrjmiMfdIdV7hyFMTnNCa6UAebemMRwkeBQIcJo"
        ),
    },
}


# ============================================
# USER MODELS
# ============================================


class User(BaseModel):
    username: str
    role: str
    customer_id: str | None = None


class UserInDB(User):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


# ============================================
# PASSWORD FUNCTIONS
# ============================================


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


# ============================================
# USER FUNCTIONS
# ============================================


def get_user(
    username: str,
) -> UserInDB | None:
    user = USERS.get(username)

    if user is None:
        return None

    return UserInDB(**user)


def get_user_by_customer_id(
    customer_id: str,
) -> UserInDB | None:
    normalized_customer_id = customer_id.strip().upper()

    for user_data in USERS.values():
        if user_data.get("customer_id") == normalized_customer_id:
            return UserInDB(**user_data)

    return None


def authenticate_user(
    login_identifier: str,
    password: str,
) -> UserInDB | None:

    identifier = login_identifier.strip()

    # Staff and normal account usernames.
    user = get_user(identifier)

    # Customer login using customer ID.
    #
    # Example:
    # CUST-1001 -> ahmed
    # CUST-1002 -> john
    if user is None:
        user = get_user_by_customer_id(identifier)

    if user is None:
        return None

    if not verify_password(
        password,
        user.hashed_password,
    ):
        return None

    return user


# ============================================
# SESSION DEPENDENCIES
# ============================================


session_bearer = HTTPBearer(
    auto_error=False,
)


def get_session_manager(
    request: Request,
) -> SessionManager:

    application_state = getattr(
        request.app.state,
        "application",
        None,
    )

    if application_state is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Application state is unavailable",
        )

    return application_state.session_manager


def get_session_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:

    # Browser clients use the HTTP-only cookie.
    session_id = request.cookies.get(SESSION_COOKIE_NAME)

    if session_id:
        return session_id

    # API clients may use:
    #
    # Authorization: Bearer <session_id>
    #
    if credentials is not None:
        return credentials.credentials

    return None


# ============================================
# AUTHENTICATION DEPENDENCIES
# ============================================


async def get_optional_current_user(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(session_bearer),
    ],
) -> User | None:

    session_id = get_session_id(
        request,
        credentials,
    )

    # No session means guest.
    if session_id is None:
        return None

    session_manager = get_session_manager(request)

    principal = session_manager.get_principal(session_id)

    if principal is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    return User(
        username=principal.username,
        role=principal.role,
        customer_id=principal.customer_id,
    )


async def get_current_user(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(session_bearer),
    ],
) -> User:

    session_id = get_session_id(
        request,
        credentials,
    )

    if session_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    session_manager = get_session_manager(request)

    principal = session_manager.get_principal(session_id)

    if principal is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    return User(
        username=principal.username,
        role=principal.role,
        customer_id=principal.customer_id,
    )


# ============================================
# LOGIN
# ============================================


async def login(
    request: Request,
    response: Response,
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
) -> Token:

    # Password verification happens ONLY here.
    user = authenticate_user(
        form_data.username,
        form_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=("Incorrect username or customer ID or password"),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    session_manager = get_session_manager(request)

    principal = SessionPrincipal(
        username=user.username,
        role=user.role,
        customer_id=user.customer_id,
    )

    session = session_manager.create_session(principal)

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session.session_id,
        max_age=SESSION_COOKIE_MAX_AGE,
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )

    # The returned value is the opaque session ID.
    # It is NOT a JWT.
    return Token(
        access_token=session.session_id,
        token_type="bearer",
    )


# ============================================
# LOGOUT
# ============================================


async def logout(
    request: Request,
    response: Response,
) -> None:

    credentials = await session_bearer(request)

    session_id = get_session_id(
        request,
        credentials,
    )

    if session_id is not None:
        session_manager = get_session_manager(request)

        session_manager.delete_session(session_id)

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
    )
