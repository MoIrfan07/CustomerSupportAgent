from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

from app.ports.tool_provider_port import ToolProviderPort


logger = logging.getLogger(__name__)


class MCPToolProviderAdapter(ToolProviderPort):
    """Discovers MCP tools; agents execute the discovered tools."""

    def create_client(self) -> MultiServerMCPClient:
        project_root = Path(__file__).resolve().parents[2]
        mcp_server = project_root / "mcp_server.py"

        if not mcp_server.is_file():
            raise FileNotFoundError(f"MCP server file was not found: {mcp_server}")

        return MultiServerMCPClient(
            {
                "customer_support": {
                    "command": sys.executable,
                    "args": [str(mcp_server)],
                    "transport": "stdio",
                    "cwd": str(project_root),
                }
            }
        )

    async def get_tools(
        self,
        client: MultiServerMCPClient | None = None,
    ) -> list[Any]:
        if client is None:
            client = self.create_client()

        logger.info("MCP DISCOVERY | requesting tools from customer_support server")
        tools = await client.get_tools()

        if not tools:
            raise RuntimeError("MCP server returned no tools.")

        logger.info(
            "MCP DISCOVERY | loaded %s tools | names=%s",
            len(tools),
            [tool.name for tool in tools],
        )
        return tools