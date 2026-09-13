# from typing import Protocol

# from app.domain.models import Customer


# class CustomerPort(Protocol):
#     """Port for retrieving customer information."""

#     async def get_customer(
#         self,
#         customer_id: str,
#     ) -> Customer | None:
#         """Retrieve a customer by identifier."""
#         ...


from typing import Protocol

from app.domain.models import Customer


class CustomerPort(Protocol):
    """Port for retrieving customer information."""

    async def get_customer(
        self,
        customer_id: str,
    ) -> Customer | None:
        """Retrieve a customer by identifier."""
        ...

    async def list_customers(self) -> list[Customer]:
        """Retrieve all customers."""
        ...