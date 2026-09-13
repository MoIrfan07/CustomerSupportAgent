from app.domain.models import Customer, CustomerStatus
from app.ports.customer_port import CustomerPort


class InMemoryCustomerAdapter(CustomerPort):
    """In-memory implementation of the customer port."""

    def __init__(self, customers: dict[str, dict]) -> None:
        self._customers = customers

    async def get_customer(
        self,
        customer_id: str,
    ) -> Customer | None:
        customer = self._customers.get(customer_id)

        if customer is None:
            return None

        return Customer(
            customer_id=str(customer["customer_id"]),
            name=str(customer["name"]),
            email=str(customer["email"]),
            status=CustomerStatus(customer["status"]),
            plan=str(customer["plan"]),
        )

    async def list_customers(self) -> list[Customer]:
        return [
            Customer(
                customer_id=str(item["customer_id"]),
                name=str(item["name"]),
                email=str(item["email"]),
                status=CustomerStatus(item["status"]),
                plan=str(item["plan"]),
            )
            for item in self._customers.values()
        ]
