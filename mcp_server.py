import re

from fastmcp import FastMCP


mcp = FastMCP(
    "Customer Support MCP Server"
)


# ============================================
# REFUND TOOL
# ============================================

@mcp.tool
def refund_payment(
    customer_id: str,
    payment_id: str,
) -> dict:
    """
    Refund a customer payment.

    This is a sensitive operation and should
    only be executed after human approval.
    """

    resolved = resolve_customer_reference(
        customer_id
    )

    if not resolved.get("found"):
        return {
            "error": (
                f"Customer '{customer_id}' "
                "was not found."
            )
        }

    actual_customer_id = resolved[
        "customer_id"
    ]

    payments = PAYMENTS.get(
        actual_customer_id,
        []
    )

    for payment in payments:

        if payment["payment_id"] == payment_id:

            if payment["status"] != "Completed":
                return {
                    "error": (
                        f"Payment {payment_id} "
                        "cannot be refunded because "
                        f"its status is "
                        f"{payment['status']}."
                    )
                }

            # --------------------------------
            # SIMULATED REFUND
            # --------------------------------

            return {
                "success": True,
                "message": (
                    f"Payment {payment_id} "
                    "has been refunded successfully."
                ),
                "customer_id": actual_customer_id,
                "payment_id": payment_id,
                "amount": payment["amount"],
            }

    return {
        "error": (
            f"Payment {payment_id} "
            f"was not found for "
            f"{actual_customer_id}."
        )
    }

def get_resolved_customer_id(
    customer_reference: str,
) -> str | None:

    resolved = resolve_customer_reference(
        customer_reference
    )

    if not resolved.get("found"):

        return None

    return resolved[
        "customer_id"
    ]

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

# ============================================
# CUSTOMER REFERENCE NORMALIZATION
# ============================================

def normalize_customer_reference(
    value: str,
) -> str:

    return re.sub(
        r"[\s\-_]+",
        "",
        value.strip().lower(),
    )


def resolve_customer_reference(
    customer_reference: str,
) -> dict:

    normalized_input = (
        normalize_customer_reference(
            customer_reference
        )
    )

    matches = []

    for customer in CUSTOMERS.values():

        normalized_id = (
            normalize_customer_reference(
                customer["customer_id"]
            )
        )

        normalized_name = (
            normalize_customer_reference(
                customer["name"]
            )
        )

        first_name = (
            customer["name"]
            .strip()
            .lower()
            .split()[0]
        )


        # Exact customer ID
        if normalized_input == normalized_id:

            matches.append(customer)


        # Number only: 1001 -> CUST-1001
        elif (
            normalized_input.isdigit()
            and normalized_id.endswith(
                normalized_input
            )
        ):

            matches.append(customer)


        # Full name
        elif normalized_input == normalized_name:

            matches.append(customer)


        # First name
        elif normalized_input == first_name:

            matches.append(customer)


    # ========================================
    # NO MATCH
    # ========================================

    if not matches:

        return {
            "found": False,
            "error": (
                f"Could not identify customer "
                f"'{customer_reference}'."
            ),
        }


    # ========================================
    # MULTIPLE MATCHES
    # ========================================

    if len(matches) > 1:

        return {
            "found": False,
            "ambiguous": True,
            "matches": [
                {
                    "customer_id": customer[
                        "customer_id"
                    ],
                    "name": customer[
                        "name"
                    ],
                }
                for customer in matches
            ],
        }


    # ========================================
    # SINGLE MATCH
    # ========================================

    customer = matches[0]

    return {
        "found": True,
        "customer_id": customer[
            "customer_id"
        ],
        "name": customer[
            "name"
        ],
        "match_type": "resolved",
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
# CUSTOMER RESOLVER TOOL
# ============================================

@mcp.tool
def resolve_customer(
    customer_reference: str,
) -> dict:
    """
    Resolve a customer from a flexible reference.

    Examples:
    - CUST-1001
    - CUST 1001
    - cust1001
    - 1001
    - Ahmed
    - Ahmed Khan
    """

    return resolve_customer_reference(
        customer_reference
    )
# ============================================
# CUSTOMER TOOL
# ============================================

@mcp.tool
def get_customer(
    customer_id: str,
) -> dict:
    """
    Retrieve basic customer profile information.

    Accepts customer ID, customer number,
    first name, or full name.
    """

    resolved = resolve_customer_reference(
        customer_id
    )


    if not resolved.get("found"):

        return {
            "error": (
                f"Customer '{customer_id}' "
                "could not be identified."
            )
        }


    actual_customer_id = (
        resolved["customer_id"]
    )


    return CUSTOMERS[
        actual_customer_id
    ]


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

    resolved_id = (
        get_resolved_customer_id(
            customer_id
        )
    )

    if not resolved_id:

        return [
            {
                "error": (
                    f"Customer '{customer_id}' "
                    "was not found."
                )
            }
        ]

    return ORDERS.get(
        resolved_id,
        []
    )
    
    
    
    
    # ============================================
# CANCEL ORDER TOOL
# ============================================

@mcp.tool
def cancel_order(
    customer_id: str,
    order_id: str,
) -> dict:
    """
    Cancel a customer order.

    Only orders with status Processing can be
    cancelled.

    Delivered and already Cancelled orders
    cannot be cancelled.
    """

    # ========================================
    # RESOLVE CUSTOMER
    # ========================================

    resolved_id = get_resolved_customer_id(
        customer_id
    )

    if not resolved_id:

        return {
            "success": False,
            "error": (
                f"Customer '{customer_id}' "
                "was not found."
            ),
        }

    # ========================================
    # FIND CUSTOMER ORDERS
    # ========================================

    customer_orders = ORDERS.get(
        resolved_id,
        []
    )

    # ========================================
    # FIND ORDER
    # ========================================

    order = next(
        (
            order
            for order in customer_orders
            if order["order_id"] == order_id
        ),
        None,
    )

    if order is None:

        return {
            "success": False,
            "error": (
                f"Order {order_id} was not found "
                f"for customer {resolved_id}."
            ),
        }

    # ========================================
    # CHECK ORDER STATUS
    # ========================================

    if order["status"] != "Processing":

        return {
            "success": False,
            "error": (
                f"Order {order_id} cannot be "
                f"cancelled because its current "
                f"status is {order['status']}."
            ),
            "customer_id": resolved_id,
            "order_id": order_id,
            "current_status": order["status"],
        }

    # ========================================
    # CANCEL ORDER
    # ========================================

    order["status"] = "Cancelled"

    return {
        "success": True,
        "message": (
            f"Order {order_id} has been "
            "cancelled successfully."
        ),
        "customer_id": resolved_id,
        "order_id": order_id,
        "product": order["product"],
        "amount": order["amount"],
        "status": order["status"],
    }
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

    resolved_id = (
        get_resolved_customer_id(
            customer_id
        )
    )

    if not resolved_id:

        return [
            {
                "error": (
                    f"Customer '{customer_id}' "
                    "was not found."
                )
            }
        ]

    return INVOICES.get(
        resolved_id,
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
    Retrieve payment information
    for a customer.
    """

    resolved_id = (
        get_resolved_customer_id(
            customer_id
        )
    )

    if not resolved_id:

        return [
            {
                "error": (
                    f"Customer '{customer_id}' "
                    "was not found."
                )
            }
        ]

    return PAYMENTS.get(
        resolved_id,
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
    Retrieve support tickets
    belonging to a customer.
    """

    resolved_id = (
        get_resolved_customer_id(
            customer_id
        )
    )

    if not resolved_id:

        return [
            {
                "error": (
                    f"Customer '{customer_id}' "
                    "was not found."
                )
            }
        ]

    return TICKETS.get(
        resolved_id,
        []
    )
# ============================================
# RUN MCP SERVER
# ============================================

if __name__ == "__main__":

    mcp.run(
        transport="stdio"
    )