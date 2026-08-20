from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.main_agent import (
    create_customer_support_agent,
)


# ============================================
# FASTAPI APP
# ============================================

app = FastAPI(
    title="Customer Support Agent API",
    version="1.0.0",
)


# ============================================
# CORS
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# AGENT
# ============================================

agent = None


async def get_agent():

    global agent

    if agent is None:

        agent = (
            await create_customer_support_agent()
        )

    return agent


# ============================================
# REQUEST MODELS
# ============================================

class ChatRequest(BaseModel):

    message: str

    thread_id: str = (
        "customer-support-session"
    )


class ChatResponse(BaseModel):

    response: str

    customer: dict[str, Any] | None = None

    activities: list[dict[str, Any]] = []

    approval_required: bool = False

    approval_message: str | None = None


# ============================================
# HEALTH CHECK
# ============================================

@app.get("/health")
async def health():

    return {
        "status": "ok",
        "service": "customer-support-agent",
    }


# ============================================
# CHAT
# ============================================

@app.post(
    "/chat",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
):

    customer_agent = (
        await get_agent()
    )

    config = {
        "configurable": {
            "thread_id": request.thread_id,
        }
    }

    result = await customer_agent.ainvoke(
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

    # ========================================
    # CHECK HUMAN APPROVAL
    # ========================================

    interrupts = result.get(
        "__interrupt__"
    )

    if interrupts:

        interrupt_value = (
            interrupts[0].value
        )

        return ChatResponse(
            response="",
            activities=[
                {
                    "label": "Human approval required",
                    "type": "approval",
                    "status": "waiting",
                }
            ],
            approval_required=True,
            approval_message=str(
                interrupt_value
            ),
        )

    # ========================================
    # FINAL MESSAGE
    # ========================================

    messages = result.get(
        "messages",
        [],
    )

    final_message = (
        messages[-1]
        if messages
        else None
    )

    content = ""

    if final_message:

        content = getattr(
            final_message,
            "content",
            "",
        )

    # ========================================
    # RETURN
    # ========================================

    return ChatResponse(
        response=str(content),
        activities=[
            {
                "label": "Request completed",
                "type": "success",
                "status": "completed",
            }
        ],
    )