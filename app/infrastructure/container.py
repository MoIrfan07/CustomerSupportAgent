from typing import Any

from app.adapters.in_memory.billing_adapter import InMemoryBillingAdapter
from app.adapters.in_memory.customer_adapter import InMemoryCustomerAdapter
from app.adapters.in_memory.order_adapter import InMemoryOrderAdapter
from app.adapters.in_memory.technical_support_adapter import (
    InMemoryTechnicalSupportAdapter,
)
from app.application.container import ApplicationContainer
from app.application.customer_support import CustomerSupportApplication
from app.application.services.billing_service import BillingService
from app.application.services.customer_service import CustomerService
from app.application.services.operations_service import OperationsService
from app.application.services.order_service import OrderService
from app.application.services.technical_support_service import (
    TechnicalSupportService,
)


def build_customer_support_container(
    customers: dict[str, dict],
    orders: dict[str, list[dict]],
    invoices: dict[str, list[dict]],
    payments: dict[str, list[dict]],
    tickets: dict[str, list[dict]],
) -> CustomerSupportApplication:
    """Build the application dependency graph."""

    customer_adapter = InMemoryCustomerAdapter(customers)
    order_adapter = InMemoryOrderAdapter(orders)
    billing_adapter = InMemoryBillingAdapter(
        invoices=invoices,
        payments=payments,
    )
    technical_support_adapter = InMemoryTechnicalSupportAdapter(tickets)

    services = ApplicationContainer(
        customer_service=CustomerService(
            customer_port=customer_adapter,
        ),
        order_service=OrderService(
            order_port=order_adapter,
        ),
        billing_service=BillingService(
            billing_port=billing_adapter,
        ),
        technical_support_service=TechnicalSupportService(
            technical_support_port=technical_support_adapter,
        ),
        operations_service=OperationsService(
            order_port=order_adapter,
            billing_port=billing_adapter,
        ),
    )

    return CustomerSupportApplication(services)
