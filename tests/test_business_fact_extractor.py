from __future__ import annotations

import json

from app.application.business_fact_extractor import BusinessFactExtractor


def test_extracts_customer_identity() -> None:
    extractor = BusinessFactExtractor()

    content = json.dumps(
        {
            "success": True,
            "data": {
                "customer_id": "CUST-1001",
                "name": "Ahmed Khan",
                "email": "ahmed@example.com",
                "status": "active",
                "plan": "premium",
            },
        }
    )

    result = extractor.extract("get_customer", content)

    assert result == {
        "customer_id": "CUST-1001",
        "name": "Ahmed Khan",
        "email": "ahmed@example.com",
        "status": "active",
        "plan": "premium",
    }


def test_extracts_resolved_customer() -> None:
    extractor = BusinessFactExtractor()

    content = {
        "success": True,
        "data": {
            "customer_id": "CUST-1001",
            "name": "Ahmed Khan",
        },
    }

    result = extractor.extract("resolve_customer", content)

    assert result == {
        "customer_id": "CUST-1001",
        "name": "Ahmed Khan",
    }


def test_extracts_orders() -> None:
    extractor = BusinessFactExtractor()

    content = {
        "success": True,
        "data": {
            "customer_id": "CUST-1001",
            "orders": [
                {
                    "order_id": "ORD-5001",
                    "status": "delivered",
                    "product": "Laptop",
                    "amount": 2500,
                    "currency": "SAR",
                },
                {
                    "order_id": "ORD-5002",
                    "status": "processing",
                    "product": "Monitor",
                    "amount": 800,
                    "currency": "SAR",
                },
            ],
        },
    }

    result = extractor.extract("get_customer_orders", content)

    assert result == {
        "orders": [
            {
                "order_id": "ORD-5001",
                "status": "delivered",
                "product": "Laptop",
                "amount": 2500,
                "currency": "SAR",
            },
            {
                "order_id": "ORD-5002",
                "status": "processing",
                "product": "Monitor",
                "amount": 800,
                "currency": "SAR",
            },
        ],
        "customer_id": "CUST-1001",
    }


def test_extracts_invoices() -> None:
    extractor = BusinessFactExtractor()

    content = {
        "success": True,
        "data": {
            "customer_id": "CUST-1001",
            "invoices": [
                {
                    "invoice_id": "INV-1001",
                    "status": "paid",
                    "amount": 1200,
                    "currency": "SAR",
                    "due_date": "2026-09-01",
                    "issued_date": "2026-08-01",
                }
            ],
        },
    }

    result = extractor.extract("get_customer_invoices", content)

    assert result == {
        "invoices": [
            {
                "invoice_id": "INV-1001",
                "status": "paid",
                "amount": 1200,
                "currency": "SAR",
                "due_date": "2026-09-01",
                "issued_date": "2026-08-01",
            }
        ],
        "customer_id": "CUST-1001",
    }


def test_extracts_payments() -> None:
    extractor = BusinessFactExtractor()

    content = {
        "success": True,
        "data": {
            "customer_id": "CUST-1001",
            "payments": [
                {
                    "payment_id": "PAY-1001",
                    "status": "completed",
                    "amount": 1200,
                    "currency": "SAR",
                    "payment_method": "card",
                    "created_at": "2026-08-15",
                }
            ],
        },
    }

    result = extractor.extract("get_customer_payments", content)

    assert result == {
        "payments": [
            {
                "payment_id": "PAY-1001",
                "status": "completed",
                "amount": 1200,
                "currency": "SAR",
                "payment_method": "card",
                "created_at": "2026-08-15",
            }
        ],
        "customer_id": "CUST-1001",
    }


def test_extracts_tickets() -> None:
    extractor = BusinessFactExtractor()

    content = {
        "success": True,
        "data": {
            "customer_id": "CUST-1001",
            "tickets": [
                {
                    "ticket_id": "TKT-1001",
                    "status": "open",
                    "subject": "Cannot access account",
                    "priority": "high",
                    "created_at": "2026-08-20",
                    "updated_at": "2026-08-21",
                }
            ],
        },
    }

    result = extractor.extract("get_customer_tickets", content)

    assert result == {
        "tickets": [
            {
                "ticket_id": "TKT-1001",
                "status": "open",
                "subject": "Cannot access account",
                "priority": "high",
                "created_at": "2026-08-20",
                "updated_at": "2026-08-21",
            }
        ],
        "customer_id": "CUST-1001",
    }


def test_extracts_cancel_order_result() -> None:
    extractor = BusinessFactExtractor()

    content = {
        "success": True,
        "data": {
            "order_id": "ORD-5002",
            "customer_id": "CUST-1001",
            "status": "cancelled",
            "message": "Order cancelled successfully.",
        },
    }

    result = extractor.extract("cancel_order", content)

    assert result == {
        "order_id": "ORD-5002",
        "customer_id": "CUST-1001",
        "status": "cancelled",
        "message": "Order cancelled successfully.",
    }


def test_extracts_refund_result() -> None:
    extractor = BusinessFactExtractor()

    content = {
        "success": True,
        "data": {
            "payment_id": "PAY-1001",
            "customer_id": "CUST-1001",
            "status": "refunded",
            "amount": 1200,
            "currency": "SAR",
            "message": "Payment refunded successfully.",
        },
    }

    result = extractor.extract("refund_payment", content)

    assert result == {
        "payment_id": "PAY-1001",
        "customer_id": "CUST-1001",
        "status": "refunded",
        "amount": 1200,
        "currency": "SAR",
        "message": "Payment refunded successfully.",
    }


def test_failed_mcp_result_produces_no_facts() -> None:
    extractor = BusinessFactExtractor()

    content = {
        "success": False,
        "error": {
            "code": "customer_not_found",
            "message": "Customer was not found.",
        },
    }

    result = extractor.extract("get_customer", content)

    assert result == {}


def test_missing_data_produces_no_facts() -> None:
    extractor = BusinessFactExtractor()

    content = {
        "success": True,
    }

    result = extractor.extract("get_customer", content)

    assert result == {}


def test_invalid_json_produces_no_facts() -> None:
    extractor = BusinessFactExtractor()

    result = extractor.extract(
        "get_customer_orders",
        "this is not valid json",
    )

    assert result == {}


def test_unknown_tool_produces_no_facts() -> None:
    extractor = BusinessFactExtractor()

    content = {
        "success": True,
        "data": {
            "secret": "should not be extracted",
        },
    }

    result = extractor.extract(
        "unknown_tool",
        content,
    )

    assert result == {}


def test_orders_with_invalid_items_are_ignored() -> None:
    extractor = BusinessFactExtractor()

    content = {
        "success": True,
        "data": {
            "customer_id": "CUST-1001",
            "orders": [
                None,
                "invalid-order",
                {
                    "order_id": "ORD-5001",
                    "status": "delivered",
                },
            ],
        },
    }

    result = extractor.extract("get_customer_orders", content)

    assert result == {
        "orders": [
            {
                "order_id": "ORD-5001",
                "status": "delivered",
            }
        ],
        "customer_id": "CUST-1001",
    }


def test_missing_collection_produces_no_facts() -> None:
    extractor = BusinessFactExtractor()

    for tool_name, collection_name in (
        ("get_customer_orders", "orders"),
        ("get_customer_invoices", "invoices"),
        ("get_customer_payments", "payments"),
        ("get_customer_tickets", "tickets"),
    ):
        content = {
            "success": True,
            "data": {
                "customer_id": "CUST-1001",
            },
        }

        result = extractor.extract(tool_name, content)

        assert collection_name not in result
        assert result == {}


def test_none_content_produces_no_facts() -> None:
    extractor = BusinessFactExtractor()

    assert extractor.extract("get_customer", None) == {}


def test_list_content_produces_no_facts() -> None:
    extractor = BusinessFactExtractor()

    assert (
        extractor.extract(
            "get_customer",
            ["unexpected", "payload"],
        )
        == {}
    )


def test_extracts_only_supported_order_fields() -> None:
    extractor = BusinessFactExtractor()

    content = {
        "success": True,
        "data": {
            "orders": [
                {
                    "order_id": "ORD-5001",
                    "status": "delivered",
                    "product": "Laptop",
                    "amount": 2500,
                    "currency": "SAR",
                    "internal_secret": "DO-NOT-COPY",
                    "debug_value": "IGNORE",
                }
            ],
        },
    }

    result = extractor.extract("get_customer_orders", content)

    assert result == {
        "orders": [
            {
                "order_id": "ORD-5001",
                "status": "delivered",
                "product": "Laptop",
                "amount": 2500,
                "currency": "SAR",
            }
        ]
    }
