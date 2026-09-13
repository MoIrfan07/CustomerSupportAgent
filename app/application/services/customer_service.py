# from app.domain.models import Customer
# from app.ports.customer_port import CustomerPort


# class CustomerService:
#     """Application service for customer-related use cases."""

#     def __init__(self, customer_port: CustomerPort) -> None:
#         self._customer_port = customer_port

#     async def get_customer(
#         self,
#         customer_id: str,
#     ) -> Customer | None:
#         """Retrieve a customer through the configured customer port."""

#         return await self._customer_port.get_customer(customer_id)


from app.domain.models import Customer
from app.ports.customer_port import CustomerPort


class CustomerService:
    """Application service for customer-related use cases."""

    def __init__(self, customer_port: CustomerPort) -> None:
        self._customer_port = customer_port

    async def get_customer(
        self,
        customer_id: str,
    ) -> Customer | None:
        """Retrieve a customer through the configured customer port."""

        return await self._customer_port.get_customer(customer_id)

    async def list_customers(self) -> list[Customer]:
        """Retrieve all customers through the configured customer port."""

        return await self._customer_port.list_customers()