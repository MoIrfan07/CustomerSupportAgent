from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient


logger = logging.getLogger(__name__)


def create_mcp_client() -> MultiServerMCPClient:
    """
    Create the MCP client used by the application.

    The MCP server is launched using the same Python interpreter
    running the application.
    """

    project_root = Path(__file__).resolve().parent.parent
    mcp_server = project_root / "mcp_server.py"
    python_executable = sys.executable

    logger.info(
        "MCP CLIENT | creating client | server=%s | python=%s",
        mcp_server,
        python_executable,
    )

    if not mcp_server.is_file():
        raise FileNotFoundError(f"MCP server file was not found: {mcp_server}")

    return MultiServerMCPClient(
        {
            "customer_support": {
                "command": python_executable,
                "args": [
                    str(mcp_server),
                ],
                "transport": "stdio",
                "cwd": str(project_root),
            }
        }
    )


async def get_mcp_tools(
    client: MultiServerMCPClient | None = None,
) -> list[Any]:
    """
    Load tools from the MCP server.

    A client can be supplied by the application lifespan.
    If none is supplied, a client is created for backwards
    compatibility.

    MCP discovery failures are logged with useful context and
    re-raised so application startup cannot continue with an
    incomplete tool set.
    """

    if client is None:
        client = create_mcp_client()

    logger.info("MCP DISCOVERY | requesting tools from customer_support server")

    try:
        tools = await client.get_tools()

    except Exception:
        logger.exception(
            "MCP DISCOVERY FAILED | unable to retrieve tools "
            "from customer_support server"
        )
        raise

    if not tools:
        logger.error("MCP DISCOVERY FAILED | customer_support server returned no tools")

        raise RuntimeError("MCP server returned no tools.")

    logger.info(
        "MCP DISCOVERY | loaded %s tools | names=%s",
        len(tools),
        [tool.name for tool in tools],
    )

    return tools
