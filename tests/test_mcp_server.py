from mcp_server import (
    cancel_order,
    get_customer,
    get_customer_invoices,
    get_customer_orders,
    get_customer_payments,
    get_customer_tickets,
    refund_payment,
    resolve_customer,
)


# ============================================================
# CUSTOMER RESOLUTION
# ============================================================


def test_resolve_customer_by_customer_id():
    result = resolve_customer("CUST-1001")

    assert result["found"] is True
    assert result["customer_id"] == "CUST-1001"
    assert result["name"] == "Ahmed Khan"


def test_resolve_customer_by_customer_number():
    result = resolve_customer("1001")

    assert result["found"] is True
    assert result["customer_id"] == "CUST-1001"


def test_resolve_customer_by_first_name():
    result = resolve_customer("Ahmed")

    assert result["found"] is True
    assert result["customer_id"] == "CUST-1001"


def test_resolve_customer_by_full_name():
    result = resolve_customer("Ahmed Khan")

    assert result["found"] is True
    assert result["customer_id"] == "CUST-1001"


def test_resolve_unknown_customer():
    result = resolve_customer("Unknown Customer")

    assert result["found"] is False
    assert "error" in result


def test_resolve_empty_customer_reference():
    result = resolve_customer("")

    assert result["found"] is False
    assert "error" in result


# ============================================================
# CUSTOMER PROFILE
# ============================================================


def test_get_customer_success():
    result = get_customer("CUST-1001")

    assert result["success"] is True
    assert result["customer"]["customer_id"] == "CUST-1001"
    assert result["customer"]["name"] == "Ahmed Khan"


def test_get_customer_not_found():
    result = get_customer("CUST-9999")

    assert result["success"] is False
    assert result["customer"] is None
    assert "error" in result


# ============================================================
# ORDERS
# ============================================================


def test_get_customer_orders_success():
    result = get_customer_orders("CUST-1001")

    assert result["success"] is True
    assert result["customer_id"] == "CUST-1001"
    assert len(result["orders"]) == 2


def test_get_customer_orders_not_found():
    result = get_customer_orders("CUST-9999")

    assert result["success"] is False
    assert result["orders"] == []
    assert "error" in result


def test_cancel_processing_order_success():
    result = cancel_order(
        "CUST-1001",
        "ORD-5002",
    )

    assert result["success"] is True
    assert result["order_id"] == "ORD-5002"
    assert result["status"] == "Cancelled"


def test_cancel_delivered_order_fails():
    result = cancel_order(
        "CUST-1001",
        "ORD-5001",
    )

    assert result["success"] is False
    assert result["current_status"] == "Delivered"
    assert "error" in result


def test_cancel_already_cancelled_order_fails():
    result = cancel_order(
        "CUST-1002",
        "ORD-5003",
    )

    assert result["success"] is False
    assert result["current_status"] == "Cancelled"
    assert "error" in result


def test_cancel_unknown_order_fails():
    result = cancel_order(
        "CUST-1001",
        "ORD-9999",
    )

    assert result["success"] is False
    assert result["order_id"] == "ORD-9999"
    assert "error" in result


# ============================================================
# INVOICES
# ============================================================


def test_get_customer_invoices_success():
    result = get_customer_invoices("CUST-1001")

    assert result["success"] is True
    assert result["customer_id"] == "CUST-1001"
    assert len(result["invoices"]) == 2


def test_get_customer_invoices_not_found():
    result = get_customer_invoices("CUST-9999")

    assert result["success"] is False
    assert result["invoices"] == []
    assert "error" in result


# ============================================================
# PAYMENTS
# ============================================================


def test_get_customer_payments_success():
    result = get_customer_payments("CUST-1001")

    assert result["success"] is True
    assert result["customer_id"] == "CUST-1001"
    assert len(result["payments"]) == 2


def test_get_customer_payments_not_found():
    result = get_customer_payments("CUST-9999")

    assert result["success"] is False
    assert result["payments"] == []
    assert "error" in result


def test_refund_completed_payment_success():
    result = refund_payment(
        "CUST-1001",
        "PAY-1001",
    )

    assert result["success"] is True
    assert result["customer_id"] == "CUST-1001"
    assert result["payment_id"] == "PAY-1001"
    assert result["amount"] == 4200


def test_refund_pending_payment_fails():
    result = refund_payment(
        "CUST-1001",
        "PAY-1002",
    )

    assert result["success"] is False
    assert result["payment_id"] == "PAY-1002"
    assert result["current_status"] == "Pending"
    assert "error" in result


def test_refund_failed_payment_fails():
    result = refund_payment(
        "CUST-1002",
        "PAY-1003",
    )

    assert result["success"] is False
    assert result["payment_id"] == "PAY-1003"
    assert result["current_status"] == "Failed"
    assert "error" in result


def test_refund_unknown_payment_fails():
    result = refund_payment(
        "CUST-1001",
        "PAY-9999",
    )

    assert result["success"] is False
    assert result["payment_id"] == "PAY-9999"
    assert "error" in result


# ============================================================
# SUPPORT TICKETS
# ============================================================


def test_get_customer_tickets_success():
    result = get_customer_tickets("CUST-1001")

    assert result["success"] is True
    assert result["customer_id"] == "CUST-1001"
    assert len(result["tickets"]) == 1


def test_get_customer_tickets_not_found():
    result = get_customer_tickets("CUST-9999")

    assert result["success"] is False
    assert result["tickets"] == []
    assert "error" in result
