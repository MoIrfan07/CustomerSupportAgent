from app.config import QWEN_LANGUAGE
from app.llm import qwen_model


def build_subagents(tools):

    tool_map = {
        tool.name: tool
        for tool in tools
    }


    # ========================================
    # CUSTOMER SPECIALIST
    # ========================================

    customer_tools = [
        tool_map["get_customer"],
        tool_map["get_customer_orders"],
    ]


    customer_specialist = {

        "name": "customer_specialist",

        "description": (
            "Handles customer profiles, customer "
            "status, contact information, account "
            "information, and customer orders."
        ),

        "system_prompt": f"""
You are the Customer Specialist.

Handle:

- Customer profiles
- Customer status
- Customer contact information
- Customer account information
- Customer orders

Always respond in {QWEN_LANGUAGE}.

Use only the tools provided to you.

Never invent customer information.

Tool results are the source of truth.

Return a concise summary to the main agent.
""",

        "tools": customer_tools,

        "model": qwen_model,
    }


    # ========================================
    # BILLING SPECIALIST
    # ========================================

    billing_tools = [
        tool_map["get_customer_invoices"],
        tool_map["get_customer_payments"],
    ]


    billing_specialist = {

        "name": "billing_specialist",

        "description": (
            "Handles customer invoices, payments, "
            "refund-related information, and "
            "billing status."
        ),

        "system_prompt": f"""
You are the Billing Specialist.

Handle:

- Invoices
- Payments
- Billing status
- Payment status

Always respond in {QWEN_LANGUAGE}.

Use only the tools provided to you.

Never invent financial information.

Tool results are the source of truth.

Return a concise summary to the main agent.
""",

        "tools": billing_tools,

        "model": qwen_model,
    }


    # ========================================
    # TECHNICAL SPECIALIST
    # ========================================

    technical_tools = [
        tool_map["get_customer_tickets"],
    ]


    technical_specialist = {

        "name": "technical_specialist",

        "description": (
            "Handles technical support tickets, "
            "incidents, troubleshooting requests, "
            "and customer technical issues."
        ),

        "system_prompt": f"""
You are the Technical Support Specialist.

Handle:

- Support tickets
- Technical issues
- Incidents
- Troubleshooting requests

Always respond in {QWEN_LANGUAGE}.

Use only the tools provided to you.

Never invent technical information.

Tool results are the source of truth.

Return a concise summary to the main agent.
""",

        "tools": technical_tools,

        "model": qwen_model,
    }


    return [
        customer_specialist,
        billing_specialist,
        technical_specialist,
    ]