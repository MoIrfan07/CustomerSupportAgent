from typing import Any

from app.adapters.agents.main_agent import create_customer_support_agent
from app.ports.agent_port import AgentPort


class AgentProvider(AgentPort):
    """
    Infrastructure-level provider responsible for constructing
    and returning Deep Agent instances.

    The API layer should not need to know how agents are built.
    """

    def __init__(
        self,
        tools: list[Any],
        checkpointer: Any,
    ):
        self.tools = tools
        self.checkpointer = checkpointer
        self._role_agents: dict[str, Any] = {}

    async def initialize_role_agents(self) -> None:
        """
        Build the shared agents used by non-customer roles.
        """

        for role in (
            "guest",
            "user",
            "support",
            "manager",
        ):
            self._role_agents[role] = await create_customer_support_agent(
                tools=self.tools,
                user_role=role,
                username=role,
                customer_id=None,
                checkpointer=self.checkpointer,
            )

    async def get_agent(
        self,
        user_role: str,
        username: str,
        customer_id: str | None = None,
    ) -> Any:
        """
        Return the appropriate agent for the authenticated user.

        Customer agents are constructed per authenticated customer.
        Other role agents are shared application-level agents.
        """

        if user_role == "customer":
            return await create_customer_support_agent(
                tools=self.tools,
                user_role="customer",
                username=username,
                customer_id=customer_id,
                checkpointer=self.checkpointer,
            )

        if user_role not in self._role_agents:
            raise ValueError(f"Unsupported user role: {user_role}")

        return self._role_agents[user_role]

    def get_role_agents(self) -> dict[str, Any]:
        """
        Return the initialized shared role agents.
        """

        return self._role_agents
