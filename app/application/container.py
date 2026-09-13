from dataclasses import dataclass

from app.application.services.billing_service import BillingService
from app.application.services.customer_service import CustomerService
from app.application.services.operations_service import OperationsService
from app.application.services.order_service import OrderService
from app.application.services.technical_support_service import (
    TechnicalSupportService,
)


@dataclass(frozen=True, slots=True)
class ApplicationContainer:
    """Application-level services available to the running system."""

    customer_service: CustomerService
    order_service: OrderService
    billing_service: BillingService
    technical_support_service: TechnicalSupportService
    operations_service: OperationsService
