from app.domain.models import Invoice, Payment
from app.ports.billing_port import BillingPort


class BillingService:
    """Application service for billing-related use cases."""

    def __init__(self, billing_port: BillingPort) -> None:
        self._billing_port = billing_port

    async def get_customer_invoices(
        self,
        customer_id: str,
    ) -> list[Invoice]:
        """Retrieve all invoices belonging to a customer."""

        return await self._billing_port.get_customer_invoices(customer_id)

    async def get_customer_payments(
        self,
        customer_id: str,
    ) -> list[Payment]:
        """Retrieve all payments belonging to a customer."""

        return await self._billing_port.get_customer_payments(customer_id)

    async def refund_payment(
        self,
        customer_id: str,
        payment_id: str,
    ) -> Payment:
        """Refund a customer payment through the billing capability."""

        return await self._billing_port.refund_payment(
            customer_id=customer_id,
            payment_id=payment_id,
        )
