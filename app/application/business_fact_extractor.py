from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class BusinessFactExtractor:
    """
    Extract compact, deterministic facts from customer-support MCP results.

    This component is intentionally model-independent.

    It does NOT:
        - call Qwen
        - infer facts
        - modify MCP results
        - perform authorization
        - decide whether a customer can access data
        - mutate LangGraph state

    It only extracts explicitly present values from known MCP response
    structures.

    MCP remains the authoritative source of business data.
    """

    SUPPORTED_TOOLS = frozenset(
        {
            "resolve_customer",
            "get_customer",
            "list_customers",
            "get_customer_orders",
            "get_customer_invoices",
            "get_customer_payments",
            "get_customer_tickets",
            "cancel_order",
            "refund_payment",
        }
    )

    def extract(
        self,
        tool_name: str | None,
        content: Any,
    ) -> dict[str, Any]:
        """
        Extract business facts from a single MCP tool result.

        Supports the current MCP response shapes used by this project.

        Examples:

            {
                "found": True,
                "customer_id": "...",
                "name": "...",
                "match_type": "resolved"
            }

            {
                "success": True,
                "customer": {...}
            }

            {
                "success": True,
                "customer_id": "...",
                "orders": [...]
            }

        Also supports the previously established nested "data" envelope
        for backward compatibility:

            {
                "success": True,
                "data": {...}
            }

        Unknown tools or malformed responses return an empty result
        rather than attempting to interpret arbitrary content.
        """

        if tool_name not in self.SUPPORTED_TOOLS:
            return {}

        payload = self._parse_content(content)

        if not isinstance(payload, dict):
            logger.warning(
                "BUSINESS FACT EXTRACTOR | invalid payload | tool=%s",
                tool_name,
            )
            return {}

        if not self._is_successful_payload(
            tool_name,
            payload,
        ):
            return {}

        data = self._get_business_data(payload)

        if not isinstance(data, dict):
            logger.warning(
                "BUSINESS FACT EXTRACTOR | invalid business data | tool=%s",
                tool_name,
            )
            return {}

        extractor = getattr(
            self,
            f"_extract_{tool_name}",
            None,
        )

        if extractor is None:
            return {}

        try:
            result = extractor(data)

            logger.info(
                "BUSINESS FACT EXTRACTOR | tool=%s | fact_keys=%s",
                tool_name,
                list(result.keys()),
            )

            return result

        except Exception:
            logger.exception(
                "BUSINESS FACT EXTRACTOR FAILED | tool=%s",
                tool_name,
            )
            return {}

    @staticmethod
    def _is_successful_payload(
        tool_name: str,
        payload: dict[str, Any],
    ) -> bool:
        """
        Determine whether the MCP response represents a successful
        business operation.

        Most tools use:

            success=True

        The current resolve_customer tool uses:

            found=True

        The older response contract may also use:

            success=True

        Therefore resolve_customer accepts either successful indicator.
        """

        if tool_name == "resolve_customer":
            return payload.get("found") is True or payload.get("success") is True

        return payload.get("success") is True

    @staticmethod
    def _get_business_data(
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Return the business-data portion of an MCP response.

        The current server generally uses top-level response structures.

        Example:

            {
                "success": True,
                "customer_id": "CUST-1001",
                "orders": [...]
            }

        Older/future-compatible responses may use:

            {
                "success": True,
                "data": {
                    ...
                }
            }
        """

        nested_data = payload.get("data")

        if isinstance(nested_data, dict):
            return nested_data

        return payload

    def _extract_resolve_customer(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}

        for field_name in (
            "customer_id",
            "name",
            "match_type",
        ):
            self._copy_if_present(
                data,
                result,
                field_name,
            )

        return result

    def _extract_get_customer(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Extract customer identity information.

        Supports both:

            {
                "customer": {
                    ...
                }
            }

        and the older direct-data structure:

            {
                "customer_id": "...",
                "name": "...",
                ...
            }
        """

        customer = data.get("customer")

        if isinstance(customer, dict):
            return self._customer_identity(customer)

        # Backward compatibility with the established test/response shape.
        return self._customer_identity(data)

    def _extract_list_customers(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        customers = data.get("customers")

        if not isinstance(customers, list):
            return {}

        extracted_customers: list[dict[str, Any]] = []

        for customer in customers:
            if not isinstance(customer, dict):
                continue

            extracted_customers.append(self._customer_identity(customer))

        if not extracted_customers:
            return {}

        return {
            "customers": extracted_customers,
        }

    def _extract_get_customer_orders(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        orders = data.get("orders")

        if not isinstance(orders, list):
            return {}

        extracted_orders: list[dict[str, Any]] = []

        for order in orders:
            if not isinstance(order, dict):
                continue

            order_fact: dict[str, Any] = {}

            for field_name in (
                "order_id",
                "status",
                "customer_id",
                "product",
                "amount",
                "currency",
                "created_at",
                "updated_at",
            ):
                self._copy_if_present(
                    order,
                    order_fact,
                    field_name,
                )

            if order_fact:
                extracted_orders.append(order_fact)

        if not extracted_orders:
            return {}

        result: dict[str, Any] = {
            "orders": extracted_orders,
        }

        self._copy_if_present(
            data,
            result,
            "customer_id",
        )

        return result

    def _extract_get_customer_invoices(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        invoices = data.get("invoices")

        if not isinstance(invoices, list):
            return {}

        extracted_invoices: list[dict[str, Any]] = []

        for invoice in invoices:
            if not isinstance(invoice, dict):
                continue

            invoice_fact: dict[str, Any] = {}

            for field_name in (
                "invoice_id",
                "status",
                "amount",
                "currency",
                "customer_id",
                "due_date",
                "issued_date",
            ):
                self._copy_if_present(
                    invoice,
                    invoice_fact,
                    field_name,
                )

            if invoice_fact:
                extracted_invoices.append(invoice_fact)

        if not extracted_invoices:
            return {}

        result: dict[str, Any] = {
            "invoices": extracted_invoices,
        }

        self._copy_if_present(
            data,
            result,
            "customer_id",
        )

        return result

    def _extract_get_customer_payments(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        payments = data.get("payments")

        if not isinstance(payments, list):
            return {}

        extracted_payments: list[dict[str, Any]] = []

        for payment in payments:
            if not isinstance(payment, dict):
                continue

            payment_fact: dict[str, Any] = {}

            for field_name in (
                "payment_id",
                "status",
                "amount",
                "currency",
                "customer_id",
                "payment_method",
                "created_at",
            ):
                self._copy_if_present(
                    payment,
                    payment_fact,
                    field_name,
                )

            if payment_fact:
                extracted_payments.append(payment_fact)

        if not extracted_payments:
            return {}

        result: dict[str, Any] = {
            "payments": extracted_payments,
        }

        self._copy_if_present(
            data,
            result,
            "customer_id",
        )

        return result

    def _extract_get_customer_tickets(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        tickets = data.get("tickets")

        if not isinstance(tickets, list):
            return {}

        extracted_tickets: list[dict[str, Any]] = []

        for ticket in tickets:
            if not isinstance(ticket, dict):
                continue

            ticket_fact: dict[str, Any] = {}

            for field_name in (
                "ticket_id",
                "status",
                "subject",
                "priority",
                "customer_id",
                "created_at",
                "updated_at",
            ):
                self._copy_if_present(
                    ticket,
                    ticket_fact,
                    field_name,
                )

            if ticket_fact:
                extracted_tickets.append(ticket_fact)

        if not extracted_tickets:
            return {}

        result: dict[str, Any] = {
            "tickets": extracted_tickets,
        }

        self._copy_if_present(
            data,
            result,
            "customer_id",
        )

        return result

    def _extract_cancel_order(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}

        for field_name in (
            "order_id",
            "customer_id",
            "status",
            "current_status",
            "product",
            "amount",
            "message",
        ):
            self._copy_if_present(
                data,
                result,
                field_name,
            )

        return result

    def _extract_refund_payment(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}

        for field_name in (
            "payment_id",
            "customer_id",
            "status",
            "current_status",
            "amount",
            "currency",
            "message",
        ):
            self._copy_if_present(
                data,
                result,
                field_name,
            )

        return result

    @staticmethod
    def _customer_identity(
        data: dict[str, Any],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}

        for field_name in (
            "customer_id",
            "name",
            "email",
            "status",
            "plan",
        ):
            BusinessFactExtractor._copy_if_present(
                data,
                result,
                field_name,
            )

        return result

    @staticmethod
    def _copy_if_present(
        source: dict[str, Any],
        destination: dict[str, Any],
        field_name: str,
    ) -> None:
        if field_name not in source:
            return

        value = source[field_name]

        if value is not None:
            destination[field_name] = value

    @staticmethod
    def _parse_content(
        content: Any,
    ) -> Any:
        if isinstance(content, dict):
            return content

        if isinstance(content, str):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return None

        return None