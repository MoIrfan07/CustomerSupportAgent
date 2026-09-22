"""Compatibility exports for the MCP tool-provider adapter."""

from app.adapters.mcp_tools import MCPToolProviderAdapter


def create_mcp_client():
    return MCPToolProviderAdapter().create_client()


async def get_mcp_tools(client=None):
    return await MCPToolProviderAdapter().get_tools(client)
