import logging
import json
import os
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4
from pathlib import Path
import openai
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import AIMessage, ToolMessage
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
from app.application.user_conversation_log import UserConversationLog
from app.config import (
    CORS_ORIGINS,
    LANGSMITH_API_KEY,
    LANGSMITH_ENDPOINT,
    LANGSMITH_PROJECT,
    LANGSMITH_TRACING,
)
from app.infrastructure.agent_factory import (
    AgentProvider,
)
from app.infrastructure.state import (
    ApplicationState,
)
from app.adapters.mcp_tools import MCPToolProviderAdapter
from app.observability import (
    clear_request_id,
    set_request_id,
)


SYSTEM_LOG_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "system_logs" / "system.log"
)
SYSTEM_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format=("%(asctime)s | %(levelname)s | %(name)s | %(message)s"),
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(SYSTEM_LOG_PATH, encoding="utf-8"),
    ],
)


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("APPLICATION STARTUP | initializing application")

    if LANGSMITH_TRACING or LANGSMITH_API_KEY:
        if not LANGSMITH_API_KEY:
            raise RuntimeError(
                "LANGSMITH_API_KEY is required when LANGSMITH_TRACING=true"
            )
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGSMITH_API_KEY"] = LANGSMITH_API_KEY
        os.environ["LANGSMITH_PROJECT"] = LANGSMITH_PROJECT
        os.environ["LANGSMITH_ENDPOINT"] = LANGSMITH_ENDPOINT
        logger.info("LANGSMITH TRACING | enabled | project=%s", LANGSMITH_PROJECT)

    tool_provider = MCPToolProviderAdapter()
    mcp_client = tool_provider.create_client()

    mcp_tools = await tool_provider.get_tools(mcp_client)

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
    chat_id: str = "chat1"


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


async def _invoke_workspace_agent(
    request: Request,
    prompt: str,
    *,
    user: User,
) -> dict[str, Any]:
    application_state: ApplicationState = request.app.state.application
    agent = await application_state.agent_provider.get_agent(
        user_role=user.role,
        username=user.username,
        customer_id=user.customer_id,
    )

    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": prompt}]},
        config={
            "configurable": {
                "thread_id": f"{user.username}:workspace-data:{uuid4()}",
            },
            "metadata": {"workspace_query": True, "user_role": user.role},
            "tags": ["customer-support", "workspace-query", user.role],
        },
    )

    workspace_results: list[dict[str, Any]] = []
    for message in result.get("messages", []):
        if not isinstance(message, (ToolMessage, AIMessage)):
            continue
        decoded = _decode_workspace_tool_result(message.content)
        if decoded is not None:
            workspace_results.append(decoded)

    if workspace_results:
        return _merge_workspace_results(workspace_results)

    logger.error(
        "WORKSPACE AGENT INVALID RESULT | user=%s | message_types=%s",
        user.username,
        [type(message).__name__ for message in result.get("messages", [])],
    )
    raise HTTPException(
        status_code=502,
        detail="The workspace agent did not return structured data.",
    )


def _merge_workspace_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    merged: dict[str, Any] = {
        "orders": [],
        "invoices": [],
        "payments": [],
        "tickets": [],
        "customers": [],
    }

    def collect(value: Any) -> None:
        if isinstance(value, dict):
            for key, nested_value in value.items():
                if key in merged and isinstance(nested_value, list):
                    merged[key].extend(nested_value)
                elif isinstance(nested_value, (dict, list)):
                    collect(nested_value)
                elif key == "customer_id" and isinstance(nested_value, str):
                    merged[key] = nested_value
        elif isinstance(value, list):
            for item in value:
                collect(item)

    for result in results:
        collect(result)

    return {
        key: _deduplicate_records(value, key)
        if isinstance(value, list)
        else value
        for key, value in merged.items()
    }


def _deduplicate_records(value: list[Any], collection_name: str) -> list[Any]:
    """Keep the first record for each stable workspace identifier."""
    identifier_fields = {
        "orders": ("order_id",),
        "invoices": ("invoice_id",),
        "payments": ("payment_id",),
        "tickets": ("ticket_id",),
        "customers": ("customer_id",),
    }.get(collection_name, ())

    if not identifier_fields:
        return value

    unique: list[Any] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            unique.append(item)
            continue

        identifier = next(
            (item.get(field) for field in identifier_fields if item.get(field)),
            None,
        )
        if identifier is None:
            unique.append(item)
            continue

        key = str(identifier)
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def _decode_workspace_tool_result(result: Any) -> dict[str, Any] | None:
    """Normalize MCP text/content envelopes into the returned JSON object."""
    if isinstance(result, dict):
        if "text" in result and isinstance(result["text"], str):
            return _decode_workspace_tool_result(result["text"])
        if "content" in result and len(result) == 1:
            return _decode_workspace_tool_result(result["content"])
        return result

    if isinstance(result, str):
        text = result.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            object_start = text.find("{")
            object_end = text.rfind("}")
            if object_start < 0 or object_end <= object_start:
                return None
            try:
                parsed = json.loads(text[object_start : object_end + 1])
            except json.JSONDecodeError:
                return None
        return parsed if isinstance(parsed, dict) else None

    if isinstance(result, list):
        for item in result:
            decoded = _decode_workspace_tool_result(item)
            if decoded is not None:
                return decoded
        return None

    content = getattr(result, "content", None)
    if content is not None:
        return _decode_workspace_tool_result(content)

    text = getattr(result, "text", None)
    if isinstance(text, str):
        return _decode_workspace_tool_result(text)

    return None


@app.get("/workspace/customers")
async def workspace_customers(
    http_request: Request,
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in {"support", "manager"}:
        raise HTTPException(status_code=403, detail="Customer directory access is restricted.")
    return await _invoke_workspace_agent(
        http_request,
        "Use the list_customers tool and return its complete structured result. "
        "Do not summarize or invent data.",
        user=current_user,
    )


@app.get("/workspace/customer-data")
async def workspace_customer_data(
    http_request: Request,
    current_user: User = Depends(get_current_user),
):
    if not current_user.customer_id:
        raise HTTPException(status_code=403, detail="A customer account is required.")

    result = await _invoke_workspace_agent(
        http_request,
        "Use the customer data tools to retrieve orders, invoices, payments, "
        "and tickets for my authenticated customer account. Return one JSON "
        "object with keys customer_id, orders, invoices, payments, and tickets. "
        "Include the complete tool results in those arrays. Return JSON only, "
        "without Markdown fences or explanatory text. Do not summarize or invent data.",
        user=current_user,
    )
    return {
        "customer_id": current_user.customer_id,
        "orders": result.get("orders", []),
        "invoices": result.get("invoices", []),
        "payments": result.get("payments", []),
        "tickets": result.get("tickets", []),
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
            },
            "metadata": {
                "request_id": request_id,
                "user_role": approval.role,
                "approval_resume": True,
            },
            "tags": ["customer-support", approval.role, "approval-resume"],
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
    chat_id: str = "chat1",
    current_user: User | None = Depends(get_optional_current_user),
):
    username = current_user.username if current_user is not None else "guest"
    identifier = current_user.customer_id if current_user and current_user.customer_id else username
    log = UserConversationLog()
    try:
        path = log._chat_path(identifier, chat_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    messages = []
    if chat_id == "chat1":
        legacy_path = log._path_for(identifier)
        if legacy_path.exists():
            messages.extend(log._read_messages(legacy_path))
    if path.exists():
        messages.extend(log._read_messages(path))

    return {
        "chat_id": chat_id,
        "messages": [
            {
                "role": ("human" if message.type == "human" else "assistant"),
                "content": message.content,
            }
            for message in messages
            if message.type in {"human", "ai"}
        ],
    }


@app.get("/chat/chats")
async def chat_list(
    current_user: User | None = Depends(get_optional_current_user),
):
    identifier = (
        current_user.customer_id if current_user and current_user.customer_id
        else current_user.username if current_user
        else "guest"
    )
    log = UserConversationLog()
    chat_ids = log.list_chat_ids(identifier) or ["chat1"]
    return {
        "chats": [
            {"chat_id": chat_id, "title": chat_id.title()}
            for chat_id in chat_ids
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

        chat_id = request.chat_id
        UserConversationLog()._chat_path(customer_id or username, chat_id)
        thread_id = f"{username}:{chat_id}"

        set_approval_context(
            registry=application_state.approval_registry,
            username=username,
            role=user_role,
            customer_id=customer_id,
            thread_id=thread_id,
        )

        conversation_context = UserConversationLog().load_compressed_context(
            customer_id or username,
            chat_id=chat_id,
        )
        input_messages: list[Any] = []
        if conversation_context is not None:
            input_messages.append(conversation_context)
        input_messages.append(
            {
                "role": "user",
                "content": request.message,
            }
        )

        config = {
            "configurable": {
                "thread_id": thread_id,
            },
            "metadata": {
                "request_id": request_id,
                "user_role": user_role,
            },
            "tags": ["customer-support", user_role],
        }

        logger.info(
            "CHAT THREAD | request_id=%s | thread_id=%s",
            request_id,
            thread_id,
        )

        try:
            result = await agent.ainvoke(
                {
                    "messages": input_messages
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

        UserConversationLog().append_turn(
            customer_id or username,
            user_message=request.message,
            assistant_message=response_text,
            chat_id=chat_id,
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
