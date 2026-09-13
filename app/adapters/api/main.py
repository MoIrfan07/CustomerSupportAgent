import logging
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4
import json
from pathlib import Path
import openai
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from pydantic import BaseModel, Field

from app.adapters.api.auth import (
    User,
    get_current_user,
    get_optional_current_user,
    login,
)
from app.adapters.api.error_handlers import register_exception_handlers
from app.application.approval_context import (
    clear_approval_context,
    set_approval_context,
)
from app.application.approval_registry import (
    ApprovalRegistry,
)

from app.application.session_manager import SessionManager
from app.infrastructure.container import build_customer_support_container
from app.config import CORS_ORIGINS
from app.infrastructure.agent_factory import (
    AgentProvider,
)
from app.infrastructure.state import (
    ApplicationState,
)
from app.mcp_client import (
    create_mcp_client,
    get_mcp_tools,
)
from app.observability import (
    clear_request_id,
    set_request_id,
)


logging.basicConfig(
    level=logging.INFO,
    format=("%(asctime)s | %(levelname)s | %(name)s | %(message)s"),
)


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("APPLICATION STARTUP | initializing application")

    mcp_client = create_mcp_client()

    mcp_tools = await get_mcp_tools(mcp_client)

    data_path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "customer_data.json"

    with data_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    services = build_customer_support_container(
        customers=data["customers"],
        orders=data["orders"],
        invoices=data["invoices"],
        payments=data["payments"],
        tickets=data["tickets"],
    )
    checkpointer = InMemorySaver()

    approval_registry = ApprovalRegistry()

    session_manager = SessionManager()

    agent_provider = AgentProvider(
        tools=mcp_tools,
        checkpointer=checkpointer,
    )

    await agent_provider.initialize_role_agents()

    app.state.application = ApplicationState(
        mcp_client=mcp_client,
        mcp_tools=mcp_tools,
        session_manager=session_manager,
        services=services,
        agent_provider=agent_provider,
        checkpointer=checkpointer,
        approval_registry=approval_registry,
    )

    app.state.ready = True

    logger.info(
        "APPLICATION STARTUP | ready=true | mcp_tools=%s",
        len(mcp_tools),
    )

    try:
        yield

    finally:
        app.state.ready = False

        approval_registry.clear()

        clear_request_id()
        clear_approval_context()

        logger.info("APPLICATION SHUTDOWN | ready=false")


app = FastAPI(
    title="Customer Support Agent",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


register_exception_handlers(app)


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    user_role: str
    customer: str | None = None
    activities: list[dict[str, Any]] = Field(default_factory=list)
    approval_required: bool = False
    approval_id: str | None = None


class ApprovalDecision(BaseModel):
    approved: bool


@app.get("/health")
async def health():
    return {
        "status": "ok",
    }


@app.get("/ready")
async def readiness(
    request: Request,
):
    """
    Readiness endpoint.

    Returns whether the application completed
    startup and initialized its required runtime state.
    """

    ready = getattr(
        request.app.state,
        "ready",
        False,
    )

    if not ready:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
            },
        )

    application_state = getattr(
        request.app.state,
        "application",
        None,
    )

    if application_state is None:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
            },
        )

    if not application_state.mcp_tools:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
            },
        )

    return {
        "status": "ready",
    }


@app.post("/auth/login")
async def auth_login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    return await login(
        request,
        response,
        form_data,
    )


@app.get("/config")
async def get_config(
    current_user: User = Depends(get_current_user),
):
    return {
        "authenticated": True,
        "username": current_user.username,
        "role": current_user.role,
        "customer_id": current_user.customer_id,
    }


@app.get("/health/live")
async def liveness():
    return {
        "status": "alive",
    }


@app.post("/approvals/{approval_id}")
async def approve_operation(
    approval_id: str,
    decision: ApprovalDecision,
    http_request: Request,
    current_user: User = Depends(get_current_user),
):
    """
    Approve or reject a pending sensitive operation.

    The endpoint:

    1. validates the approval exists;
    2. validates approval ownership;
    3. validates the current user is a manager;
    4. stores the human decision;
    5. resumes the exact LangGraph thread;
    6. returns the resumed agent response.

    The approval is only consumed after the resumed
    operation completes successfully.
    """

    if http_request is None:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "application_state_unavailable",
                "message": "Application state is unavailable.",
            },
        )

    application_state: ApplicationState = http_request.app.state.application

    approval_registry = application_state.approval_registry

    approval = approval_registry.get(approval_id)

    if approval is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "approval_not_found",
                "message": (
                    "The approval request does not exist or has already been consumed."
                ),
                "approval_id": approval_id,
            },
        )

    # ---------------------------------------------------------
    # Approval ownership check.
    # ---------------------------------------------------------
    if current_user.username != approval.username:
        logger.warning(
            "APPROVAL ACCESS DENIED | approval_id=%s | requester=%s | owner=%s",
            approval_id,
            current_user.username,
            approval.username,
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "approval_forbidden",
                "message": ("You are not authorized to approve this operation."),
                "approval_id": approval_id,
            },
        )

    # ---------------------------------------------------------
    # Sensitive operations currently require manager approval.
    # ---------------------------------------------------------
    if current_user.role != "manager":
        logger.warning(
            "APPROVAL ROLE DENIED | approval_id=%s | user=%s | role=%s",
            approval_id,
            current_user.username,
            current_user.role,
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "approval_forbidden",
                "message": ("Your role is not authorized to approve this operation."),
                "approval_id": approval_id,
            },
        )

        # ---------------------------------------------------------
    # Approval decisions are strictly one-shot.
    #
    # Once a decision has been recorded, the approval cannot be
    # submitted again. This prevents a second request from
    # resuming the same LangGraph execution a second time.
    # ---------------------------------------------------------
    if approval.decision is not None:
        logger.warning(
            "APPROVAL ALREADY DECIDED | "
            "approval_id=%s | "
            "requester=%s | "
            "existing_decision=%s | "
            "requested_decision=%s",
            approval_id,
            current_user.username,
            approval.decision,
            decision.approved,
        )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "approval_already_decided",
                "message": (
                    "This approval request has already been decided "
                    "and cannot be submitted again."
                ),
                "approval_id": approval_id,
            },
        )

    # ---------------------------------------------------------
    # Record the first decision WITHOUT consuming the approval.
    #
    # The approval must remain available while LangGraph resumes.
    # ---------------------------------------------------------
    decided_approval = approval_registry.set_decision(
        approval_id=approval_id,
        approved=decision.approved,
    )

    if decided_approval is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "approval_not_found",
                "message": (
                    "The approval request does not exist or has already been consumed."
                ),
                "approval_id": approval_id,
            },
        )

    logger.info(
        "APPROVAL DECISION | "
        "approval_id=%s | "
        "user=%s | "
        "approved=%s | "
        "tool=%s | "
        "thread_id=%s",
        decided_approval.approval_id,
        current_user.username,
        decision.approved,
        decided_approval.tool_name,
        decided_approval.thread_id,
    )

    # ---------------------------------------------------------
    # Restore the exact approval context required by middleware.
    # ---------------------------------------------------------
    set_approval_context(
        registry=approval_registry,
        username=approval.username,
        role=approval.role,
        customer_id=approval.customer_id,
        thread_id=approval.thread_id,
    )

    request_id = str(uuid4())

    http_request.state.request_id = request_id

    set_request_id(request_id)

    try:
        # -----------------------------------------------------
        # Rebuild/select the same agent identity that originally
        # created the approval.
        # -----------------------------------------------------
        agent = await application_state.agent_provider.get_agent(
            user_role=approval.role,
            username=approval.username,
            customer_id=approval.customer_id,
        )

        config = {
            "configurable": {
                "thread_id": approval.thread_id,
            }
        }

        logger.info(
            "APPROVAL RESUME | "
            "request_id=%s | "
            "approval_id=%s | "
            "thread_id=%s | "
            "approved=%s",
            request_id,
            approval_id,
            approval.thread_id,
            decision.approved,
        )

        # -----------------------------------------------------
        # Resume the SAME LangGraph execution.
        # -----------------------------------------------------
        try:
            result = await agent.ainvoke(
                Command(
                    resume=decision.approved,
                ),
                config=config,
            )

        except openai.RateLimitError:
            logger.exception(
                "QWEN PROVIDER ERROR | rate_limit | request_id=%s",
                request_id,
            )

            raise HTTPException(
                status_code=503,
                detail={
                    "error": "llm_unavailable",
                    "message": (
                        "The AI service is temporarily unavailable. "
                        "Please try again later."
                    ),
                    "request_id": request_id,
                },
            )

        except openai.AuthenticationError:
            logger.exception(
                "QWEN PROVIDER ERROR | authentication | request_id=%s",
                request_id,
            )

            raise HTTPException(
                status_code=502,
                detail={
                    "error": "llm_provider_error",
                    "message": ("The AI service is temporarily unavailable."),
                    "request_id": request_id,
                },
            )

        except openai.APIStatusError:
            logger.exception(
                "QWEN PROVIDER ERROR | status_error | request_id=%s",
                request_id,
            )

            raise HTTPException(
                status_code=502,
                detail={
                    "error": "llm_provider_error",
                    "message": ("The AI service is temporarily unavailable."),
                    "request_id": request_id,
                },
            )

        # -----------------------------------------------------
        # If another interrupt exists, do not consume this
        # approval because the graph is still paused.
        # -----------------------------------------------------
        if "__interrupt__" in result:
            logger.warning(
                "APPROVAL RESUME INTERRUPTED AGAIN | "
                "request_id=%s | "
                "approval_id=%s | "
                "thread_id=%s",
                request_id,
                approval_id,
                approval.thread_id,
            )

            return {
                "approval_id": approval_id,
                "status": "approval_required",
                "message": ("The operation requires another approval."),
                "tool_name": approval.tool_name,
                "thread_id": approval.thread_id,
            }

        # -----------------------------------------------------
        # Extract the final agent response.
        # -----------------------------------------------------
        messages = result.get(
            "messages",
            [],
        )

        final_message = messages[-1] if messages else None

        response_text = (
            final_message.content
            if final_message is not None
            else "No response was generated."
        )

        # -----------------------------------------------------
        # The resumed graph completed successfully.
        #
        # Now consume the approval.
        # -----------------------------------------------------
        consumed = approval_registry.remove(approval_id)

        if consumed is None:
            logger.warning(
                "APPROVAL ALREADY CONSUMED | approval_id=%s | request_id=%s",
                approval_id,
                request_id,
            )

        logger.info(
            "APPROVAL COMPLETED | "
            "request_id=%s | "
            "approval_id=%s | "
            "approved=%s | "
            "thread_id=%s",
            request_id,
            approval_id,
            decision.approved,
            approval.thread_id,
        )

        return {
            "approval_id": approval_id,
            "status": ("approved" if decision.approved else "rejected"),
            "message": response_text,
            "tool_name": approval.tool_name,
            "thread_id": approval.thread_id,
        }

    finally:
        clear_approval_context()
        clear_request_id()


@app.get("/chat/history")
async def chat_history(
    http_request: Request,
    current_user: User | None = Depends(get_optional_current_user),
):
    application_state: ApplicationState = http_request.app.state.application

    username = current_user.username if current_user is not None else "guest"

    thread_id = f"{username}:customer-support-session"

    agent = await application_state.agent_provider.get_agent(
        user_role=(current_user.role if current_user is not None else "guest"),
        username=username,
        customer_id=(current_user.customer_id if current_user is not None else None),
    )

    state = await agent.aget_state(
        {
            "configurable": {
                "thread_id": thread_id,
            }
        }
    )

    messages = state.values.get("messages", [])

    return {
        "messages": [
            {
                "role": ("human" if message.type == "human" else "assistant"),
                "content": message.content,
            }
            for message in messages
            if message.type in {"human", "ai"}
        ]
    }


@app.post(
    "/chat",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
    http_request: Request,
    current_user: User | None = Depends(get_optional_current_user),
):
    request_id = str(uuid4())

    http_request.state.request_id = request_id

    set_request_id(request_id)

    logger.info(
        "CHAT REQUEST | request_id=%s",
        request_id,
    )

    try:
        if current_user is None:
            username = "guest"
            user_role = "guest"
            customer_id = None

        else:
            username = current_user.username
            user_role = current_user.role
            customer_id = current_user.customer_id

        application_state: ApplicationState = http_request.app.state.application

        agent = await application_state.agent_provider.get_agent(
            user_role=user_role,
            username=username,
            customer_id=customer_id,
        )

        thread_id = f"{username}:{request.thread_id}"

        set_approval_context(
            registry=application_state.approval_registry,
            username=username,
            role=user_role,
            customer_id=customer_id,
            thread_id=thread_id,
        )

        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        logger.info(
            "CHAT THREAD | request_id=%s | thread_id=%s",
            request_id,
            thread_id,
        )

        try:
            result = await agent.ainvoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": request.message,
                        }
                    ]
                },
                config=config,
            )

        except openai.RateLimitError:
            logger.exception(
                "QWEN PROVIDER ERROR | rate_limit | request_id=%s",
                request_id,
            )

            raise HTTPException(
                status_code=503,
                detail={
                    "error": "llm_unavailable",
                    "message": (
                        "The AI service is temporarily unavailable. "
                        "Please try again later."
                    ),
                    "request_id": request_id,
                },
            )

        except openai.AuthenticationError:
            logger.exception(
                "QWEN PROVIDER ERROR | authentication | request_id=%s",
                request_id,
            )

            raise HTTPException(
                status_code=502,
                detail={
                    "error": "llm_provider_error",
                    "message": ("The AI service is temporarily unavailable."),
                    "request_id": request_id,
                },
            )

        except openai.APIStatusError:
            logger.exception(
                "QWEN PROVIDER ERROR | status_error | request_id=%s",
                request_id,
            )

            raise HTTPException(
                status_code=502,
                detail={
                    "error": "llm_provider_error",
                    "message": ("The AI service is temporarily unavailable."),
                    "request_id": request_id,
                },
            )

        if "__interrupt__" in result:
            logger.info(
                "CHAT APPROVAL REQUIRED | request_id=%s | thread_id=%s",
                request_id,
                thread_id,
            )

            interrupt_data = result["__interrupt__"]

            approval_id = None

            if interrupt_data:
                interrupt_value = getattr(
                    interrupt_data[0],
                    "value",
                    None,
                )

                if isinstance(
                    interrupt_value,
                    str,
                ):
                    marker = "Approval ID:"

                    if marker in interrupt_value:
                        approval_id = (
                            interrupt_value.split(
                                marker,
                                1,
                            )[1]
                            .split(
                                "\n",
                                1,
                            )[0]
                            .strip()
                        )

            return ChatResponse(
                response=("Human approval is required for this operation."),
                user_role=user_role,
                customer=customer_id,
                activities=[],
                approval_required=True,
                approval_id=approval_id,
            )

        messages = result.get(
            "messages",
            [],
        )

        final_message = messages[-1] if messages else None

        response_text = (
            final_message.content
            if final_message is not None
            else "No response was generated."
        )

        logger.info(
            "CHAT RESPONSE | request_id=%s | thread_id=%s",
            request_id,
            thread_id,
        )

        return ChatResponse(
            response=response_text,
            user_role=user_role,
            customer=customer_id,
            activities=[],
            approval_required=False,
        )

    finally:
        clear_approval_context()
        clear_request_id()
