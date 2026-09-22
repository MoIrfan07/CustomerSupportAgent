from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
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

DATA_PATH = Path(__file__).resolve().parent / "data" / "customer_data.json"
PRODUCTS_PATH = Path(__file__).resolve().parent / "data" / "products.json"
NOTIFICATIONS_PATH = Path(__file__).resolve().parent / "data" / "notifications.json"

with DATA_PATH.open("r", encoding="utf-8") as file:
    DATA = json.load(file)
with PRODUCTS_PATH.open("r", encoding="utf-8") as file:
    PRODUCTS = json.load(file)["products"]

CUSTOMERS = DATA["customers"]
ORDERS = DATA["orders"]
INVOICES = DATA["invoices"]
PAYMENTS = DATA["payments"]
TICKETS = DATA["tickets"]


def _append_notification(customer_id: str, message: str, notification_type: str) -> None:
    NOTIFICATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    notifications: dict[str, list[dict[str, Any]]] = {}
    if NOTIFICATIONS_PATH.exists():
        with NOTIFICATIONS_PATH.open("r", encoding="utf-8") as file:
            notifications = json.load(file)
    notifications.setdefault(customer_id, []).append(
        {
            "id": f"NTF-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
            "type": notification_type,
            "message": message,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "read": False,
        }
    )
    with NOTIFICATIONS_PATH.open("w", encoding="utf-8") as file:
        json.dump(notifications, file, indent=2)


def _persist_catalog_and_orders() -> None:
    with PRODUCTS_PATH.open("w", encoding="utf-8") as file:
        json.dump({"products": PRODUCTS}, file, indent=2)
    with DATA_PATH.open("w", encoding="utf-8") as file:
        json.dump(DATA, file, indent=2)


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


# ============================================================
# PRODUCT AND ORDER CREATION TOOLS
# ============================================================


@mcp.tool
def list_products() -> dict[str, Any]:
    """List products currently available for purchase."""
    available = [product for product in PRODUCTS if product["stock"] > 0]
    return {"success": True, "products": available}


@mcp.tool
def create_order(
    customer_id: str,
    product_id: str,
    quantity: int = 1,
) -> dict[str, Any]:
    """Create an order for an authenticated customer."""
    resolved_id = get_resolved_customer_id(customer_id)
    if not resolved_id:
        return {"success": False, "error": f"Customer '{customer_id}' was not found."}
    if quantity < 1 or quantity > 20:
        return {"success": False, "error": "Quantity must be between 1 and 20."}

    product = next((item for item in PRODUCTS if item["product_id"] == product_id), None)
    if product is None:
        return {"success": False, "error": f"Product '{product_id}' was not found."}
    if product["stock"] < quantity:
        return {"success": False, "error": f"Only {product['stock']} units are available."}

    product["stock"] -= quantity
    customer_orders = ORDERS.setdefault(resolved_id, [])
    order_number = max(
        (int(order["order_id"].split("-")[-1]) for orders in ORDERS.values() for order in orders),
        default=5000,
    ) + 1
    order = {
        "order_id": f"ORD-{order_number}",
        "product": product["name"],
        "product_id": product["product_id"],
        "quantity": quantity,
        "amount": product["unit_price"] * quantity,
        "status": "Processing",
        "order_date": datetime.now(timezone.utc).date().isoformat(),
    }
    customer_orders.append(order)
    _persist_catalog_and_orders()
    message = f"Order {order['order_id']} for {quantity} x {product['name']} was placed successfully."
    _append_notification(resolved_id, message, "order_created")
    logger.info("MCP MUTATION | order created | customer_id=%s | order_id=%s", resolved_id, order["order_id"])
    return {"success": True, "message": message, "customer_id": resolved_id, "order": order}


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
    _append_notification(
        resolved_id,
        f"Order {order_id} was cancelled successfully.",
        "order_cancelled",
    )

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
