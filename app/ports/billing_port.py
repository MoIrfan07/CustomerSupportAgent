from typing import Protocol

from app.domain.models import Invoice, Payment


class BillingPort(Protocol):
    """Port for customer billing information and operations."""

    async def get_customer_invoices(
        self,
        customer_id: str,
    ) -> list[Invoice]:
        """Retrieve all invoices belonging to a customer."""
        ...

    async def get_customer_payments(
        self,
        customer_id: str,
    ) -> list[Payment]:
        """Retrieve all payments belonging to a customer."""
        ...

    async def refund_payment(
        self,
        customer_id: str,
        payment_id: str,
    ) -> Payment:
        """Refund a customer payment."""
        ...
