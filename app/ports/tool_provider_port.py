from __future__ import annotations

from typing import Any, Protocol


class ToolProviderPort(Protocol):
    """Output port for discovering tools an agent can call."""

    def create_client(self) -> Any:
        ...

    async def get_tools(self, client: Any | None = None) -> list[Any]:
        ...
