from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.main_agent import (
    create_customer_support_agent,
)

from app.mcp_client import get_mcp_tools


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
USER_ROLE = "manager"  # default user role for the agent, can be changed based on the application context
agent = None
@app.get("/config")
async def config():

    return {
        "user_role": USER_ROLE,
    }

async def get_agent(user_role: str ):

    global agent

    if agent is None:

        agent = await create_customer_support_agent(
            user_role= USER_ROLE
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
    user_role : str
    customer: dict[str, Any] | None = None
    
    

    activities: list[dict[str, Any]] = []

    approval_required: bool = False

    approval_message: str | None = None



# ============================================
# CUSTOMERS
# ============================================

@app.get("/customers")
async def get_customers():

    # Get the MCP tools available to the application
    tools = await get_mcp_tools()

    # Find the customer tool
    get_customer_tool = next(
        tool
        for tool in tools
        if tool.name == "get_customer"
    )

    # Customer IDs that should appear
    # in the Customers tab
    customer_ids = [
        "CUST-1001",
        "CUST-1002",
        "CUST-1003",
    ]

    customers = []

    # Retrieve each customer through the MCP tool
    for customer_id in customer_ids:

        result = await get_customer_tool.ainvoke(
            {
                "customer_id": customer_id
            }
        )

        customers.append(result)

    return {
        "customers": customers
    }
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

    customer_agent = await get_agent(user_role=USER_ROLE)
    

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
            user_role=USER_ROLE,
            activities=[
                {
                    "id": 1,
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
        user_role=USER_ROLE,
        activities=[
            {
                "id": 1,
                "label": "Request completed",
                "type": "success",
                "status": "completed",
            }
        ],
    )