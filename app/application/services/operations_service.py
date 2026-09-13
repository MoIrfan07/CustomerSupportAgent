from app.domain.models import Order, Payment
from app.ports.billing_port import BillingPort
from app.ports.order_port import OrderPort


class OperationsService:
    """Application service for customer service operations."""

    def __init__(
        self,
        order_port: OrderPort,
        billing_port: BillingPort,
    ) -> None:
        self._order_port = order_port
        self._billing_port = billing_port

    async def cancel_order(
        self,
        customer_id: str,
        order_id: str,
    ) -> Order:
        """Cancel a customer order."""

        return await self._order_port.cancel_order(
            customer_id=customer_id,
            order_id=order_id,
        )

    async def refund_payment(
        self,
        customer_id: str,
        payment_id: str,
    ) -> Payment:
        """Refund a customer payment."""

        return await self._billing_port.refund_payment(
            customer_id=customer_id,
            payment_id=payment_id,
        )
