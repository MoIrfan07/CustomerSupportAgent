from decimal import Decimal

from app.domain.models import (
    Invoice,
    InvoiceStatus,
    Payment,
    PaymentStatus,
)
from app.ports.billing_port import BillingPort


class InMemoryBillingAdapter(BillingPort):
    """In-memory implementation of the billing port."""

    def __init__(
        self,
        invoices: dict[str, list[dict]],
        payments: dict[str, list[dict]],
    ) -> None:
        self._invoices = invoices
        self._payments = payments

    async def get_customer_invoices(
        self,
        customer_id: str,
    ) -> list[Invoice]:
        customer_invoices = self._invoices.get(customer_id, [])

        return [
            Invoice(
                invoice_id=str(item["invoice_id"]),
                customer_id=customer_id,
                amount=Decimal(str(item["amount"])),
                status=InvoiceStatus(item["status"]),
            )
            for item in customer_invoices
        ]

    async def get_customer_payments(
        self,
        customer_id: str,
    ) -> list[Payment]:
        customer_payments = self._payments.get(customer_id, [])

        return [
            Payment(
                payment_id=str(item["payment_id"]),
                customer_id=customer_id,
                amount=Decimal(str(item["amount"])),
                status=PaymentStatus(item["status"]),
            )
            for item in customer_payments
        ]

    async def refund_payment(
        self,
        customer_id: str,
        payment_id: str,
    ) -> Payment:
        customer_payments = self._payments.get(customer_id, [])

        payment = next(
            (item for item in customer_payments if item["payment_id"] == payment_id),
            None,
        )

        if payment is None:
            raise ValueError(
                f"Payment {payment_id} was not found for customer {customer_id}."
            )

        payment["status"] = "Refunded"

        return Payment(
            payment_id=str(payment["payment_id"]),
            customer_id=customer_id,
            amount=Decimal(str(payment["amount"])),
            status=PaymentStatus(payment["status"]),
        )
