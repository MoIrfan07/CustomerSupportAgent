from dataclasses import dataclass
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

from app.application.approval_registry import ApprovalRegistry
from app.application.customer_support import CustomerSupportApplication
from app.application.session_manager import SessionManager
from app.infrastructure.agent_factory import AgentProvider


@dataclass(slots=True)
class ApplicationState:
    mcp_client: MultiServerMCPClient
    mcp_tools: list[Any]
    services: CustomerSupportApplication
    agent_provider: AgentProvider
    checkpointer: Any
    approval_registry: ApprovalRegistry
    session_manager: SessionManager
