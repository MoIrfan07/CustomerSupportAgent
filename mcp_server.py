from fastmcp import FastMCP


mcp = FastMCP(
    "Customer Support MCP Server"
)


# ============================================
# CUSTOMER DATABASE
# ============================================

CUSTOMERS = {

    "CUST-1001": {
        "customer_id": "CUST-1001",
        "name": "Ahmed Khan",
        "email": "ahmed@example.com",
        "status": "Active",
        "plan": "Premium",
    },

    "CUST-1002": {
        "customer_id": "CUST-1002",
        "name": "John Smith",
        "email": "john@example.com",
        "status": "Suspended",
        "plan": "Basic",
    },

}


ORDERS = {

    "CUST-1001": [
        {
            "order_id": "ORD-5001",
            "product": "Laptop",
            "amount": 4200,
            "status": "Delivered",
        },
        {
            "order_id": "ORD-5002",
            "product": "Monitor",
            "amount": 850,
            "status": "Processing",
        },
    ],

    "CUST-1002": [
        {
            "order_id": "ORD-5003",
            "product": "Keyboard",
            "amount": 250,
            "status": "Cancelled",
        }
    ],

}


INVOICES = {

    "CUST-1001": [
        {
            "invoice_id": "INV-1001",
            "amount": 4200,
            "status": "Paid",
        },
        {
            "invoice_id": "INV-1002",
            "amount": 850,
            "status": "Pending",
        },
    ],

    "CUST-1002": [
        {
            "invoice_id": "INV-1003",
            "amount": 250,
            "status": "Overdue",
        }
    ],

}


PAYMENTS = {

    "CUST-1001": [
        {
            "payment_id": "PAY-1001",
            "amount": 4200,
            "status": "Completed",
        },
        {
            "payment_id": "PAY-1002",
            "amount": 850,
            "status": "Pending",
        },
    ],

    "CUST-1002": [
        {
            "payment_id": "PAY-1003",
            "amount": 250,
            "status": "Failed",
        }
    ],

}


TICKETS = {

    "CUST-1001": [
        {
            "ticket_id": "TCK-1001",
            "subject": "Monitor delivery",
            "status": "Open",
            "priority": "Medium",
        }
    ],

    "CUST-1002": [
        {
            "ticket_id": "TCK-1002",
            "subject": "Keyboard not working",
            "status": "Open",
            "priority": "High",
        }
    ],

}


# ============================================
# CUSTOMER TOOL
# ============================================

@mcp.tool
def get_customer(
    customer_id: str,
) -> dict:
    """
    Retrieve basic customer profile information.
    """

    customer = CUSTOMERS.get(customer_id)

    if not customer:

        return {
            "error": (
                f"Customer {customer_id} "
                "was not found."
            )
        }

    return customer


# ============================================
# ORDER TOOL
# ============================================

@mcp.tool
def get_customer_orders(
    customer_id: str,
) -> list:
    """
    Retrieve orders belonging to a customer.
    """

    if customer_id not in CUSTOMERS:

        return [
            {
                "error": (
                    f"Customer {customer_id} "
                    "was not found."
                )
            }
        ]

    return ORDERS.get(
        customer_id,
        []
    )


# ============================================
# INVOICE TOOL
# ============================================

@mcp.tool
def get_customer_invoices(
    customer_id: str,
) -> list:
    """
    Retrieve invoices belonging to a customer.
    """

    if customer_id not in CUSTOMERS:

        return [
            {
                "error": (
                    f"Customer {customer_id} "
                    "was not found."
                )
            }
        ]

    return INVOICES.get(
        customer_id,
        []
    )


# ============================================
# PAYMENT TOOL
# ============================================

@mcp.tool
def get_customer_payments(
    customer_id: str,
) -> list:
    """
    Retrieve payment information for a customer.
    """

    if customer_id not in CUSTOMERS:

        return [
            {
                "error": (
                    f"Customer {customer_id} "
                    "was not found."
                )
            }
        ]

    return PAYMENTS.get(
        customer_id,
        []
    )


# ============================================
# SUPPORT TICKET TOOL
# ============================================

@mcp.tool
def get_customer_tickets(
    customer_id: str,
) -> list:
    """
    Retrieve technical support tickets
    belonging to a customer.
    """

    if customer_id not in CUSTOMERS:

        return [
            {
                "error": (
                    f"Customer {customer_id} "
                    "was not found."
                )
            }
        ]

    return TICKETS.get(
        customer_id,
        []
    )


# ============================================
# RUN MCP SERVER
# ============================================

if __name__ == "__main__":

    mcp.run(
        transport="stdio"
    )