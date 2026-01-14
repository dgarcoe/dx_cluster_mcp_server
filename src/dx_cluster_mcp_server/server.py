#!/usr/bin/env python3
"""
DX Cluster MCP Server

An MCP server that provides access to ham radio DX cluster networks,
allowing AI assistants to query DX spots and propagation information.

Supports two transport modes:
- stdio: For Claude Desktop and local integrations
- sse: HTTP/SSE for Docker and network access
"""

import asyncio
import os
from typing import Any, Optional

from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
import mcp.server.stdio

from .config import DXClusterConfig
from .dx_client import DXClusterClient
from .mcp_handlers import MCPResourceHandler, MCPToolHandler
from .oauth import OAuthConfig, validate_oauth_middleware


# Global client instance
_dx_client: Optional[DXClusterClient] = None
_resource_handler: Optional[MCPResourceHandler] = None
_tool_handler: Optional[MCPToolHandler] = None


async def get_client() -> DXClusterClient:
    """Get or create the DX cluster client.

    Returns:
        DXClusterClient instance.

    Raises:
        RuntimeError: If connection to DX cluster fails.
    """
    global _dx_client, _resource_handler, _tool_handler

    if _dx_client is None or not _dx_client.connected:
        config = DXClusterConfig.from_environment()
        config.validate()

        _dx_client = DXClusterClient(config)
        success = await _dx_client.connect()

        if not success:
            _dx_client = None
            raise RuntimeError(
                f"Failed to connect to DX cluster at {config.host}:{config.port}. "
                f"Please verify:\n"
                f"  1. DX_CLUSTER_HOST and DX_CLUSTER_PORT are correct\n"
                f"  2. DX_CLUSTER_CALLSIGN is set to a valid callsign\n"
                f"  3. The DX cluster server is reachable from your network\n"
                f"  4. Firewall allows outbound connections to port {config.port}"
            )

        _resource_handler = MCPResourceHandler(_dx_client)
        _tool_handler = MCPToolHandler(_dx_client)

    return _dx_client


# Create MCP server
app = Server("dx-cluster-mcp-server")


@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available MCP resources.

    Returns:
        List of Resource objects.

    Raises:
        RuntimeError: If connection to DX cluster fails.
    """
    await get_client()
    return _resource_handler.list_resources()


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read an MCP resource.

    Args:
        uri: Resource URI to read.

    Returns:
        Resource content as string.

    Raises:
        RuntimeError: If connection to DX cluster fails.
    """
    await get_client()
    return _resource_handler.read_resource(uri)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools.

    Returns:
        List of Tool objects.

    Raises:
        RuntimeError: If connection to DX cluster fails.
    """
    await get_client()
    return _tool_handler.list_tools()


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle MCP tool invocations.

    Args:
        name: Tool name.
        arguments: Tool arguments.

    Returns:
        List of TextContent responses.
    """
    try:
        await get_client()
        return _tool_handler.handle_tool_call(name, arguments)
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main_stdio() -> None:
    """Run the MCP server with stdio transport."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


async def main_sse() -> None:
    """Run the MCP server with SSE transport."""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.responses import JSONResponse
    import uvicorn

    # Initialize OAuth configuration
    oauth_config = OAuthConfig()
    if not oauth_config.validate():
        print("⚠ Invalid OAuth configuration. Server will not start.")
        return

    # Create SSE transport
    sse = SseServerTransport("/messages")

    async def handle_sse(scope, receive, send):
        async with sse.connect_sse(scope, receive, send) as streams:
            await app.run(
                streams[0], streams[1], app.create_initialization_options()
            )

    async def handle_messages(scope, receive, send):
        await sse.handle_post_message(scope, receive, send)

    async def health_check(request):
        """Simple health check endpoint with DX cluster connection status."""
        global _dx_client

        # Check DX cluster connection
        cluster_connected = False
        cluster_info = None

        if _dx_client is not None:
            cluster_connected = _dx_client.connected
            if cluster_connected:
                cluster_info = {
                    "host": _dx_client.config.host,
                    "port": _dx_client.config.port,
                    "callsign": _dx_client.config.callsign,
                    "iaru_region": _dx_client.config.iaru_region,
                    "cached_spots": len(_dx_client.spots_buffer)
                }

        return JSONResponse({
            "status": "healthy",
            "service": "dx-cluster-mcp-server",
            "version": "0.1.0",
            "transport": "sse",
            "dx_cluster": {
                "connected": cluster_connected,
                "info": cluster_info
            },
            "endpoints": {
                "health": "/health",
                "sse": "/sse",
                "messages": "/messages"
            }
        })

    # Create Starlette app (only for health check)
    starlette_app = Starlette(
        routes=[
            Route("/health", endpoint=health_check, methods=["GET"]),
        ]
    )

    # Add OAuth middleware to Starlette app
    from starlette.middleware.base import BaseHTTPMiddleware

    class OAuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            return await validate_oauth_middleware(request, call_next, oauth_config)

    starlette_app.add_middleware(OAuthMiddleware)

    # Create ASGI middleware to intercept SSE paths
    async def asgi_app(scope, receive, send):
        if scope["type"] == "http":
            path = scope["path"]
            if path == "/sse":
                await handle_sse(scope, receive, send)
                return
            elif path == "/messages":
                await handle_messages(scope, receive, send)
                return
        # Pass through to Starlette for other routes
        await starlette_app(scope, receive, send)

    # Get configuration
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_SERVER_PORT", "8000"))

    # TLS/SSL configuration
    ssl_certfile = os.getenv("MCP_SSL_CERTFILE")
    ssl_keyfile = os.getenv("MCP_SSL_KEYFILE")
    use_ssl = ssl_certfile and ssl_keyfile

    protocol = "https" if use_ssl else "http"

    print(f"Starting DX Cluster MCP Server on {protocol}://{host}:{port}")
    print(f"Health check: {protocol}://{host}:{port}/health")
    print(f"SSE endpoint: {protocol}://{host}:{port}/sse")
    print(f"Messages endpoint: {protocol}://{host}:{port}/messages")

    if use_ssl:
        print(f"TLS enabled:")
        print(f"  Certificate: {ssl_certfile}")
        print(f"  Key: {ssl_keyfile}")
    else:
        print("⚠ Running without TLS (HTTP only)")
        print("  For Claude Desktop, HTTPS is required")
        print("  Set MCP_SSL_CERTFILE and MCP_SSL_KEYFILE environment variables")

    if oauth_config.enabled:
        print(f"\n✓ OAuth authentication enabled")
        print(f"  Client ID: {oauth_config.client_id}")
        print(f"  Client Secret: {'*' * 8}{oauth_config.client_secret[-4:]}")
        print(f"  Note: Include 'Authorization: Bearer <client_secret>' header in requests")
    else:
        print(f"\n⚠ OAuth authentication disabled")
        print(f"  Server endpoints are publicly accessible")
        print(f"  Set OAUTH_ENABLED=true to enable authentication")

    # Run server
    config = uvicorn.Config(
        asgi_app,
        host=host,
        port=port,
        log_level="info",
        ssl_certfile=ssl_certfile,
        ssl_keyfile=ssl_keyfile,
    )
    server = uvicorn.Server(config)
    await server.serve()


def run() -> None:
    """Entry point for the server.

    Runs in stdio mode by default, or SSE mode if MCP_TRANSPORT=sse.
    """
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()

    if transport == "sse":
        asyncio.run(main_sse())
    else:
        asyncio.run(main_stdio())


if __name__ == "__main__":
    run()
