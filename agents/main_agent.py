# from deepagents import create_deep_agent

# from middleware.logging_middleware import (
#     CustomerSupportLoggingMiddleware,
# )

# from middleware.subagent_logging_middleware import (
#     SubagentLoggingMiddleware,
# )


# from middleware.security_middleware import (
#     CustomerAuthorizationMiddleware,
# )

# from middleware.approval_middleware import (
#     CustomerApprovalMiddleware,
# )


# from langgraph.checkpoint.memory import (
#     InMemorySaver,
# )


# from app.config import QWEN_LANGUAGE
# from app.llm import qwen_model
# from app.mcp_client import get_mcp_tools

# from agents.subagents import build_subagents



# SYSTEM_PROMPT = f"""
# You are a professional customer support coordinator.

# You are the main agent responsible for understanding
# the customer's request and coordinating specialist
# agents and tools.

# Your responsibilities:

# 1. Understand the customer's request.

# 2. Resolve customer references such as:
#    - "Ahmed"
#    - "customer 1001"
#    - "cust-1001"
#    - "1001"
#    - "John"
#    - "his account"
#    - "her order"

# 3. Use the appropriate specialist when the request
#    belongs to a specialized area.

# 4. Use available tools whenever customer, order,
#    payment, invoice, account, ticket, refund, or
#    cancellation information is required.

# 5. Delegate customer/profile/order questions to the
#    Customer Specialist.

# 6. Delegate invoice/payment/billing questions to the
#    Billing Specialist.

# 7. Delegate support-ticket and technical questions
#    to the Technical Specialist.

# 8. Delegate refunds and order cancellations to the
#    Customer Operations Specialist.

# 9. Never invent, assume, or estimate factual
#    customer information.

# 10. Only state customer information explicitly
#     present in tool results or specialist results.

# 11. If a requested field is not present, explicitly
#     say that the information is not available.

# 12. Never substitute information from another customer.

# 13. Give clear and concise answers.

# 14. Always respond in {QWEN_LANGUAGE} unless the
#     customer explicitly asks for another language.

# 15. Ask for clarification when required information
#     is genuinely missing.

# 16. When a user refers to an order by position
#     ("first order", "second order") or description
#     ("the monitor order"), resolve it using the
#     customer's actual order records.

# 17. For order cancellation:
#     - Only orders that are actually eligible for
#       cancellation may be cancelled.
#     - A delivered order must not be cancelled.
#     - An already cancelled order must not be cancelled.
#     - If multiple orders exist, identify which ones
#       are eligible before asking the user to choose.
#     - If only one order is eligible, use that order
#       instead of unnecessarily asking the user to
#       choose.

# 18. For sensitive operations such as refunds and
#     cancellations:
#     - Authorization must be respected.
#     - Human approval must be obtained.
#     - Never bypass the approval process.

# 19. Monetary amounts returned by tools are already
#     expressed in the currency's major unit.

# 20. Never divide monetary amounts by 100 unless
#     a tool explicitly states that the amount is
#     stored in minor units.

# 21. Preserve monetary values exactly as returned
#     by tools.

# IMPORTANT:

# Tool and specialist results are the source of truth.

# Never fabricate customer, order, payment, invoice,
# ticket, refund, or cancellation information.

# You are the main customer support coordinator.
# """

# # ============================================
# # CREATE AGENT
# # ============================================

# async def create_customer_support_agent():

#     tools = await get_mcp_tools()


#     checkpointer = InMemorySaver()
#     # print(
#     #     "\n===== MCP TOOLS LOADED =====\n"
#     # )

#     # for tool in tools:
#     #     print(
#     #         f"- {tool.name}"
#     #     )

#     subagents = build_subagents(
#         tools
#     )

    

#     agent = create_deep_agent(
#         model=qwen_model,
#         tools=tools,
#         system_prompt=SYSTEM_PROMPT,
#         subagents=subagents,
#         middleware=[
#             CustomerSupportLoggingMiddleware(),
#             SubagentLoggingMiddleware(),
#             CustomerAuthorizationMiddleware(
#                 user_role="manager"
            
#             ),
#             CustomerApprovalMiddleware(),
#         ],
#         checkpointer=checkpointer,
#     )

#     return agent



from deepagents import create_deep_agent

from middleware.logging_middleware import (
    CustomerSupportLoggingMiddleware,
)

from middleware.subagent_logging_middleware import (
    SubagentLoggingMiddleware,
)

from middleware.security_middleware import (
    CustomerAuthorizationMiddleware,
)

from middleware.approval_middleware import (
    CustomerApprovalMiddleware,
)

from langgraph.checkpoint.memory import (
    InMemorySaver,
)

from app.config import QWEN_LANGUAGE
from app.llm import qwen_model
from app.mcp_client import get_mcp_tools

from agents.subagents import build_subagents


SYSTEM_PROMPT = f"""
You are a professional customer support coordinator.

You are the MAIN AGENT.

Your job is to:

1. Understand the user's request.

2. Identify which specialist is responsible.

3. Delegate the request to the appropriate specialist.

4. Receive the specialist's result.

5. Use that result to formulate the final answer.

6. Return the final answer to the user.

====================================================
SPECIALIST ROUTING
====================================================

CUSTOMER SPECIALIST

Use the Customer Specialist for:

- Customer profiles
- Customer identity
- Customer status
- Customer contact information
- Customer accounts
- Customer orders
- Order status
- Order eligibility

Examples:

"show customer 1001"

"show Ahmed's orders"

"what are his orders?"

"status of his orders"

"show his account"


BILLING SPECIALIST

Use the Billing Specialist for:

- Invoices
- Payments
- Payment status
- Invoice status
- Billing information

Examples:

"show Ahmed's payments"

"show his invoices"

"why is his payment pending?"


TECHNICAL SPECIALIST

Use the Technical Specialist for:

- Support tickets
- Technical issues
- Incidents
- Troubleshooting
- Ticket status
- Ticket priority

Examples:

"show Ahmed's tickets"

"what is the status of his ticket?"


OPERATIONS SPECIALIST

Use the Operations Specialist for:

- Refunds
- Order cancellations

Examples:

"refund payment PAY-1001"

"refund his payment"

"cancel his order"


====================================================
IMPORTANT ROUTING RULE
====================================================

The MAIN AGENT must NOT directly access business
data tools.

The MAIN AGENT must delegate business-data requests
to the appropriate specialist.

The specialist is responsible for calling its
available tools.

The specialist returns the result to the MAIN AGENT.

The MAIN AGENT then provides the final response
to the user.

Do NOT call unrelated specialists.

Use one specialist whenever one specialist can
answer the request.

Only use multiple specialists when the request
genuinely requires multiple domains.

====================================================
SOURCE OF TRUTH
====================================================

Tool results are the source of truth.

Never invent customer information.

Never invent order information.

Never invent invoice information.

Never invent payment information.

Never invent ticket information.

Never invent refund information.

Never invent cancellation information.

If the specialist reports that information is
unavailable, tell the user that it is unavailable.

====================================================
ORDER HANDLING
====================================================

When the user says:

"first order"

"second order"

"the monitor"

"his order"

"her order"

the Customer Specialist should resolve the
reference using the actual customer order records.

====================================================
SENSITIVE OPERATIONS
====================================================

Refunds and cancellations are sensitive operations.

Authorization must be respected.

Human approval must be obtained.

Never bypass the approval process.

====================================================
MONETARY VALUES
====================================================

Monetary amounts returned by tools are already
expressed in the major currency unit.

Never divide monetary amounts by 100 unless a
tool explicitly states that the value is stored
in minor units.

Preserve monetary values exactly as returned.

====================================================
FINAL RESPONSE
====================================================

After receiving the specialist result:

- Understand it.
- Summarize it clearly.
- Do not fabricate information.
- Answer the user's original question directly.

Always respond in {QWEN_LANGUAGE} unless the
user explicitly requests another language.
"""



async def create_customer_support_agent( user_role: str ):   #creates the main customer-support agent asynchronously

    tools = await get_mcp_tools()  # loads the MCP tools

    checkpointer = InMemorySaver()
    #creates an in-memory checkpointer to save agent state/conversation state


    subagents = build_subagents(
    tools  #creates the sub agents and gives them their required tools
    )
    
    

    agent = create_deep_agent(  #creates the main Deep Agent using the configurations below

        model=qwen_model, #calls qwen model

        system_prompt=SYSTEM_PROMPT,

        # Do NOT give MCP tools directly to the main agent.
       
        subagents=subagents, #calls sub agents

        middleware=[

            CustomerSupportLoggingMiddleware(),   #logs 

            SubagentLoggingMiddleware(), #subagents logs

            CustomerAuthorizationMiddleware(
                user_role=user_role,   #user role passed from the calling function
            ),

            CustomerApprovalMiddleware(),  #human approval 
        ],

        checkpointer=checkpointer,
    )


    return agent