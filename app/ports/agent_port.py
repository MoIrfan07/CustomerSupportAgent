from __future__ import annotations

from typing import Any, Protocol


class AgentPort(Protocol):
    """Input port used by delivery adapters to access support agents."""

    async def initialize_role_agents(self) -> None:
        ...

    async def get_agent(
        self,
        user_role: str,
        username: str,
        customer_id: str | None = None,
    ) -> Any:
        ...

    def get_role_agents(self) -> dict[str, Any]:
        ...
