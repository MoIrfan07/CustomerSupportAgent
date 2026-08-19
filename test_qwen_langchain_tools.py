from langchain_core.tools import tool

from app.llm import qwen_model


@tool
def get_customer(customer_id: str) -> dict:
    """
    Retrieve customer information using
    a customer ID.
    """

    customers = {
        "CUST-1001": {
            "customer_id": "CUST-1001",
            "name": "Ahmed Khan",
            "status": "Active",
            "plan": "Premium",
        },
        "CUST-1002": {
            "customer_id": "CUST-1002",
            "name": "John Smith",
            "status": "Suspended",
            "plan": "Basic",
        },
    }

    return customers.get(
        customer_id,
        {
            "error": (
                f"Customer {customer_id} "
                "was not found."
            )
        },
    )


model_with_tools = qwen_model.bind_tools(
    [get_customer]
)


response = model_with_tools.invoke(
    (
        "What is the status of customer "
        "CUST-1001? Use the customer tool."
    )
)


print("\n===== LANGCHAIN TOOL CALL =====\n")

print(response)

print("\n===== TOOL CALLS =====\n")

print(response.tool_calls)