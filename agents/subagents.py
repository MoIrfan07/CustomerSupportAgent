from app.config import QWEN_LANGUAGE
from app.llm import qwen_model


def build_subagents(tools):   #creates subagents and gives them their required tools


    tool_map = {
        tool.name: tool      # converts the list of MCP tools into a dictionary so we can easily get a tool by its name
        for tool in tools
    }

    subagents = []   #list where subagents will be stored
    
    
    
    
    # CUSTOMER SPECIALIST

    customer_tools = [
        tool_map["get_customer"],
        tool_map["get_customer_orders"],    
    ]   #gives required tools to the customer specialist subagent


#customwr specialist
    customer_specialist = {

        "name": "customer_specialist",

        "description": (
            "Handles customer profiles, customer "
            "identity resolution, customer status, "
            "contact information, account information, "
            "and customer orders."
        ),

        "system_prompt": f"""
You are the Customer Specialist.

Your responsibilities:

- Find customers by ID or name.
- Resolve informal customer references.
- Retrieve customer profiles.
- Check customer status.
- Retrieve customer contact information.
- Retrieve customer orders.
- Determine which orders are active, processing,
  delivered, cancelled, or otherwise unavailable
  for cancellation.

Always respond in {QWEN_LANGUAGE}.

Use only the tools provided to you.

Never invent customer information.

Tool results are the source of truth.

If a customer cannot be found, say so clearly.

When the user refers to an order such as
"first order", "second order", or "the monitor",
use the available customer/order information
to resolve the correct order.

Return a concise factual summary to the main agent.
""",

        "tools": customer_tools,  

        "model": qwen_model,
        
        
        #customer tools & model are assigned to the customer specialist subagent
    }

    subagents.append(customer_specialist)   #customer specialist subagent is added to the list of subagents




    # BILLING SPECIALIST

    billing_tools = [
        tool_map["get_customer_invoices"],
        tool_map["get_customer_payments"],
    ]   #same as above but for billing specialist subagent

    billing_specialist = {

        "name": "billing_specialist",

        "description": (
            "Handles customer invoices, payments, "
            "billing status, payment status, and "
            "billing-related investigations."
        ),

        "system_prompt": f"""
You are the Billing Specialist.

Your responsibilities:

- Investigate invoices.
- Investigate payments.
- Check payment status.
- Check invoice status.
- Investigate billing issues.
- Determine whether a payment is pending,
  completed, failed, or otherwise stated by
  the available records.

Always respond in {QWEN_LANGUAGE}.

Use only the tools provided to you.

Never invent financial information.

Never invent a reason for a payment status.

If the records do not contain a reason,
explicitly say that the reason is unavailable.

Monetary amounts returned by tools are already
in the major currency unit.

Never divide amounts by 100 unless a tool
explicitly states that the value is stored
in minor units.

Tool results are the source of truth.

Return a concise factual summary to the main agent.
""",

        "tools": billing_tools,

        "model": qwen_model,
    }

    subagents.append(billing_specialist)



    # TECHNICAL SPECIALIST

    technical_tools = [
        tool_map["get_customer_tickets"],
    ] #same as above but for technical specialist subagent

    technical_specialist = {

        "name": "technical_specialist",

        "description": (
            "Handles support tickets, technical "
            "issues, incidents, troubleshooting, "
            "and customer support problems."
        ),

        "system_prompt": f"""
You are the Technical Support Specialist.

Your responsibilities:

- Investigate support tickets.
- Identify open or closed tickets.
- Review ticket priority.
- Review ticket subjects.
- Investigate technical issues.
- Summarize support incidents.

Always respond in {QWEN_LANGUAGE}.

Use only the tools provided to you.

Never invent technical information.

If the available ticket information does not
contain a cause or resolution, say that it
is unavailable.

Tool results are the source of truth.

Return a concise factual summary to the main agent.
""",

        "tools": technical_tools,

        "model": qwen_model,
    }

    subagents.append(technical_specialist)




    # OPERATIONS SPECIALIST

    operations_tools = []  #init operations tools list
    operations_tools = [
        tool_map["refund_payment"],
        tool_map["cancel_order"],
    ]
    
    
# gives the Operations Specialist both operation tools

    if operations_tools:

        operations_specialist = {

            "name": "operations_specialist",

            "description": (
                "Handles customer service operations "
                "such as payment refunds and order "
                "cancellations. Only perform actions "
                "when the requested operation is "
                "actually supported and authorized."
            ),

            "system_prompt": f"""
You are the Customer Operations Specialist.

Your responsibilities:

- Process payment refunds when authorized.
- Cancel orders when authorized.
- Verify the relevant customer and order/payment
  before performing an operation.
- Determine whether an order is eligible for
  cancellation based on the actual order status.
- Never cancel an order that is already delivered,
  already cancelled, or otherwise not eligible
  according to the tool result.
- Never refund a payment unless the payment is
  eligible according to the tool result.
- Never invent operational information.

Always respond in {QWEN_LANGUAGE}.

Sensitive operations require the main agent's
authorization and human approval middleware.

Do not bypass authorization or approval.

If an operation cannot be performed, clearly
explain why.

Tool results are the source of truth.

Monetary amounts must be reported exactly as
returned by the tools.

Return a concise factual result to the main agent.
""",

            "tools": operations_tools,

            "model": qwen_model,
        }

        subagents.append(
            operations_specialist
        )

    return subagents