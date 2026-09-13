"""Application ports for external business capabilities."""

from .customer_port import CustomerPort
from .order_port import OrderPort
from .billing_port import BillingPort
from .technical_support_port import TechnicalSupportPort

__all__ = [
    "CustomerPort",
    "OrderPort",
    "BillingPort",
    "TechnicalSupportPort",
]
