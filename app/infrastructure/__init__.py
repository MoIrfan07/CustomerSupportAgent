"""
Infrastructure layer for external integrations,
runtime state, dependency composition, and agent provisioning.
"""

from .agent_factory import AgentProvider
from .container import build_customer_support_container
from .state import ApplicationState

__all__ = [
    "AgentProvider",
    "ApplicationState",
    "build_customer_support_container",
]
