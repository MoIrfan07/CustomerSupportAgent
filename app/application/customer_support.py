from app.application.container import ApplicationContainer
from app.domain.models import (
    Customer,
    Invoice,
    Order,
    Payment,
    SupportTicket,
)


class CustomerSupportApplication:
    """Application facade for customer-support use cases."""

    def __init__(self, services: ApplicationContainer) -> None:
        self._services = services

    async def get_customer(
        self,
        customer_id: str,
    ) -> Customer | None:
        return await self._services.customer_service.get_customer(customer_id)

    async def list_customers(self) -> list[Customer]:
        return await self._services.customer_service.list_customers()

    async def get_customer_orders(
        self,
        customer_id: str,
    ) -> list[Order]:
        return await self._services.order_service.get_customer_orders(customer_id)

    async def cancel_order(
        self,
        customer_id: str,
        order_id: str,
    ) -> Order:
        return await self._services.operations_service.cancel_order(
            customer_id=customer_id,
            order_id=order_id,
        )

    async def get_customer_invoices(
        self,
        customer_id: str,
    ) -> list[Invoice]:
        return await self._services.billing_service.get_customer_invoices(customer_id)

    async def get_customer_payments(
        self,
        customer_id: str,
    ) -> list[Payment]:
        return await self._services.billing_service.get_customer_payments(customer_id)

    async def refund_payment(
        self,
        customer_id: str,
        payment_id: str,
    ) -> Payment:
        return await self._services.operations_service.refund_payment(
            customer_id=customer_id,
            payment_id=payment_id,
        )

    async def get_customer_tickets(
        self,
        customer_id: str,
    ) -> list[SupportTicket]:
        return await self._services.technical_support_service.get_customer_tickets(
            customer_id
        )
