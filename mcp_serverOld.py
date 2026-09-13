from __future__ import annotations

import logging
import re
from typing import Any

from fastmcp import FastMCP


logger = logging.getLogger("mcp_server")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


mcp = FastMCP("Customer Support MCP Server")


# ============================================================
# CUSTOMER DATABASE
# ============================================================

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


# ============================================================
# CUSTOMER RESOLUTION HELPERS
# ============================================================


def normalize_customer_reference(
    value: str,
) -> str:
    """
    Normalize a customer reference for comparison.

    Examples:
        CUST-1001 -> cust1001
        CUST 1001 -> cust1001
        cust1001 -> cust1001
        Ahmed Khan -> ahmedkhan
    """
    if not isinstance(value, str):
        return ""

    return re.sub(
        r"[\s\-_]+",
        "",
        value.strip().lower(),
    )


def resolve_customer_reference(
    customer_reference: str,
) -> dict[str, Any]:
    """
    Resolve a customer reference against the customer database.

    Supported references include:
        - CUST-1001
        - CUST 1001
        - cust1001
        - 1001
        - Ahmed
        - Ahmed Khan
    """

    if not isinstance(customer_reference, str):
        return {
            "found": False,
            "error": "Customer reference must be a string.",
        }

    customer_reference = customer_reference.strip()

    if not customer_reference:
        return {
            "found": False,
            "error": "Customer reference cannot be empty.",
        }

    normalized_input = normalize_customer_reference(customer_reference)

    matches: list[dict[str, Any]] = []

    for customer in CUSTOMERS.values():
        normalized_id = normalize_customer_reference(customer["customer_id"])

        normalized_name = normalize_customer_reference(customer["name"])

        first_name = customer["name"].strip().lower().split()[0]

        # Exact customer ID
        if normalized_input == normalized_id:
            matches.append(customer)

        # Number only:
        # 1001 -> CUST-1001
        elif normalized_input.isdigit() and normalized_id.endswith(normalized_input):
            matches.append(customer)

        # Full name
        elif normalized_input == normalized_name:
            matches.append(customer)

        # First name
        elif normalized_input == first_name:
            matches.append(customer)

    if not matches:
        return {
            "found": False,
            "error": (f"Could not identify customer '{customer_reference}'."),
        }

    if len(matches) > 1:
        return {
            "found": False,
            "ambiguous": True,
            "error": (f"Customer reference '{customer_reference}' is ambiguous."),
            "matches": [
                {
                    "customer_id": customer["customer_id"],
                    "name": customer["name"],
                }
                for customer in matches
            ],
        }

    customer = matches[0]

    return {
        "found": True,
        "customer_id": customer["customer_id"],
        "name": customer["name"],
        "match_type": "resolved",
    }


def get_resolved_customer_id(
    customer_reference: str,
) -> str | None:
    """
    Resolve a customer reference and return only
    the canonical customer ID.

    This is an internal helper and is NOT an MCP tool.
    """

    resolved = resolve_customer_reference(customer_reference)

    if not resolved.get("found"):
        return None

    return resolved["customer_id"]


# ============================================================
# CUSTOMER RESOLUTION TOOL
# ============================================================


@mcp.tool
def resolve_customer(
    customer_reference: str,
) -> dict[str, Any]:
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

    logger.info(
        "MCP TOOL | resolve_customer | reference=%s",
        customer_reference,
    )

    return resolve_customer_reference(customer_reference)


# ============================================================
# CUSTOMER TOOL
# ============================================================


@mcp.tool
def get_customer(
    customer_id: str,
) -> dict[str, Any]:
    """
    Retrieve basic customer profile information.

    Accepts customer ID, customer number,
    first name, or full name.
    """

    logger.info(
        "MCP TOOL | get_customer | customer_reference=%s",
        customer_id,
    )

    resolved = resolve_customer_reference(customer_id)

    if not resolved.get("found"):
        return {
            "success": False,
            "error": (f"Customer '{customer_id}' could not be identified."),
            "customer": None,
        }

    actual_customer_id = resolved["customer_id"]

    customer = CUSTOMERS.get(actual_customer_id)

    if customer is None:
        logger.error(
            "MCP DATA ERROR | customer resolved but "
            "record was missing | customer_id=%s",
            actual_customer_id,
        )

        return {
            "success": False,
            "error": (f"Customer '{actual_customer_id}' could not be retrieved."),
            "customer": None,
        }

    return {
        "success": True,
        "customer": customer,
    }


# ============================================================
# CUSTOMER LISTING TOOL
# ============================================================


@mcp.tool
def list_customers() -> dict[str, Any]:
    """
    Retrieve the full list of customer profiles.

    This is a staff-facing capability (manager/support) and is
    NOT scoped to a single authenticated customer. Authorization
    for who may call this tool is enforced by the application
    layer, not by this server.
    """

    logger.info(
        "MCP TOOL | list_customers | count=%s",
        len(CUSTOMERS),
    )

    return {
        "success": True,
        "customers": list(CUSTOMERS.values()),
    }


# ============================================================
# ORDER TOOL
# ============================================================


@mcp.tool
def get_customer_orders(
    customer_id: str,
) -> dict[str, Any]:
    """
    Retrieve orders belonging to a customer.
    """

    logger.info(
        "MCP TOOL | get_customer_orders | customer_reference=%s",
        customer_id,
    )

    resolved_id = get_resolved_customer_id(customer_id)

    if not resolved_id:
        return {
            "success": False,
            "error": (f"Customer '{customer_id}' was not found."),
            "orders": [],
        }

    return {
        "success": True,
        "customer_id": resolved_id,
        "orders": ORDERS.get(
            resolved_id,
            [],
        ),
    }


# ============================================================
# CANCEL ORDER TOOL
# ============================================================


@mcp.tool
def cancel_order(
    customer_id: str,
    order_id: str,
) -> dict[str, Any]:
    """
    Cancel a customer order.

    Only orders with status Processing can be
    cancelled.

    Delivered and already Cancelled orders
    cannot be cancelled.
    """

    logger.info(
        "MCP TOOL | cancel_order | customer_reference=%s | order_id=%s",
        customer_id,
        order_id,
    )

    resolved_id = get_resolved_customer_id(customer_id)

    if not resolved_id:
        return {
            "success": False,
            "error": (f"Customer '{customer_id}' was not found."),
        }

    customer_orders = ORDERS.get(
        resolved_id,
        [],
    )

    order = next(
        (order for order in customer_orders if order["order_id"] == order_id),
        None,
    )

    if order is None:
        return {
            "success": False,
            "error": (f"Order {order_id} was not found for customer {resolved_id}."),
            "customer_id": resolved_id,
            "order_id": order_id,
        }

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

    order["status"] = "Cancelled"

    logger.info(
        "MCP MUTATION | order cancelled | customer_id=%s | order_id=%s",
        resolved_id,
        order_id,
    )

    return {
        "success": True,
        "message": (f"Order {order_id} has been cancelled successfully."),
        "customer_id": resolved_id,
        "order_id": order_id,
        "product": order["product"],
        "amount": order["amount"],
        "status": order["status"],
    }


# ============================================================
# INVOICE TOOL
# ============================================================


@mcp.tool
def get_customer_invoices(
    customer_id: str,
) -> dict[str, Any]:
    """
    Retrieve invoices belonging to a customer.
    """

    logger.info(
        "MCP TOOL | get_customer_invoices | customer_reference=%s",
        customer_id,
    )

    resolved_id = get_resolved_customer_id(customer_id)

    if not resolved_id:
        return {
            "success": False,
            "error": (f"Customer '{customer_id}' was not found."),
            "invoices": [],
        }

    return {
        "success": True,
        "customer_id": resolved_id,
        "invoices": INVOICES.get(
            resolved_id,
            [],
        ),
    }


# ============================================================
# PAYMENT TOOL
# ============================================================


@mcp.tool
def get_customer_payments(
    customer_id: str,
) -> dict[str, Any]:
    """
    Retrieve payment information for a customer.
    """

    logger.info(
        "MCP TOOL | get_customer_payments | customer_reference=%s",
        customer_id,
    )

    resolved_id = get_resolved_customer_id(customer_id)

    if not resolved_id:
        return {
            "success": False,
            "error": (f"Customer '{customer_id}' was not found."),
            "payments": [],
        }

    return {
        "success": True,
        "customer_id": resolved_id,
        "payments": PAYMENTS.get(
            resolved_id,
            [],
        ),
    }


# ============================================================
# SUPPORT TICKET TOOL
# ============================================================


@mcp.tool
def get_customer_tickets(
    customer_id: str,
) -> dict[str, Any]:
    """
    Retrieve support tickets belonging to a customer.
    """

    logger.info(
        "MCP TOOL | get_customer_tickets | customer_reference=%s",
        customer_id,
    )

    resolved_id = get_resolved_customer_id(customer_id)

    if not resolved_id:
        return {
            "success": False,
            "error": (f"Customer '{customer_id}' was not found."),
            "tickets": [],
        }

    return {
        "success": True,
        "customer_id": resolved_id,
        "tickets": TICKETS.get(
            resolved_id,
            [],
        ),
    }


# ============================================================
# REFUND TOOL
# ============================================================


@mcp.tool
def refund_payment(
    customer_id: str,
    payment_id: str,
) -> dict[str, Any]:
    """
    Refund a customer payment.

    This is a sensitive operation and should
    only be executed after human approval.
    """

    logger.info(
        "MCP TOOL | refund_payment | customer_reference=%s | payment_id=%s",
        customer_id,
        payment_id,
    )

    resolved = resolve_customer_reference(customer_id)

    if not resolved.get("found"):
        return {
            "success": False,
            "error": (f"Customer '{customer_id}' was not found."),
        }

    actual_customer_id = resolved["customer_id"]

    payments = PAYMENTS.get(
        actual_customer_id,
        [],
    )

    for payment in payments:
        if payment["payment_id"] != payment_id:
            continue

        if payment["status"] != "Completed":
            return {
                "success": False,
                "error": (
                    f"Payment {payment_id} "
                    "cannot be refunded because "
                    f"its status is "
                    f"{payment['status']}."
                ),
                "customer_id": actual_customer_id,
                "payment_id": payment_id,
                "current_status": payment["status"],
            }

        logger.info(
            "MCP MUTATION | payment refunded | customer_id=%s | payment_id=%s",
            actual_customer_id,
            payment_id,
        )

        return {
            "success": True,
            "message": (f"Payment {payment_id} has been refunded successfully."),
            "customer_id": actual_customer_id,
            "payment_id": payment_id,
            "amount": payment["amount"],
        }

    return {
        "success": False,
        "error": (f"Payment {payment_id} was not found for {actual_customer_id}."),
        "customer_id": actual_customer_id,
        "payment_id": payment_id,
    }


# ============================================================
# MCP SERVER ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    logger.info("MCP SERVER | starting Customer Support MCP Server")

    mcp.run(transport="stdio")
