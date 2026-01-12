#!/usr/bin/env python3
"""
Test MCP client to connect to the DX Cluster MCP Server via SSE.

This demonstrates how to properly connect to the MCP server over HTTP/SSE.
"""

import asyncio
import sys


async def test_mcp_connection(server_url: str = "http://localhost:8000"):
    """Test connection to MCP server and list available tools.

    Args:
        server_url: URL of the MCP server (default: http://localhost:8000)
    """
    try:
        # Import MCP client
        from mcp import ClientSession
        from mcp.client.sse import sse_client

        print(f"Connecting to MCP server at {server_url}...")

        # Connect to the server
        async with sse_client(server_url) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                print("✓ Connected successfully!")

                # List available tools
                print("\n--- Available Tools ---")
                tools_result = await session.list_tools()
                for tool in tools_result.tools:
                    print(f"  • {tool.name}: {tool.description}")

                # List available resources
                print("\n--- Available Resources ---")
                resources_result = await session.list_resources()
                for resource in resources_result.resources:
                    print(f"  • {resource.name} ({resource.uri})")
                    print(f"    {resource.description}")

                # Example: Call get_cluster_status tool
                print("\n--- Testing get_cluster_status ---")
                status_result = await session.call_tool("get_cluster_status", {})
                for content in status_result.content:
                    if hasattr(content, 'text'):
                        print(content.text)

                # Example: Get recent spots
                print("\n--- Testing get_recent_spots ---")
                spots_result = await session.call_tool("get_recent_spots", {"count": 5})
                for content in spots_result.content:
                    if hasattr(content, 'text'):
                        print(content.text)

                print("\n✓ All tests passed!")

    except ImportError:
        print("Error: MCP client libraries not installed.")
        print("Install with: pip install mcp")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def test_health_check(server_url: str = "http://localhost:8000"):
    """Test the health check endpoint.

    Args:
        server_url: URL of the MCP server (default: http://localhost:8000)
    """
    import aiohttp

    try:
        health_url = f"{server_url}/health"
        print(f"Checking health endpoint: {health_url}")

        async with aiohttp.ClientSession() as session:
            async with session.get(health_url) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✓ MCP Server is healthy!")
                    print(f"  Service: {data.get('service')}")
                    print(f"  Version: {data.get('version')}")
                    print(f"  Transport: {data.get('transport')}")

                    # Check DX cluster connection
                    dx_cluster = data.get('dx_cluster', {})
                    cluster_connected = dx_cluster.get('connected', False)

                    print(f"\n  DX Cluster Connection:")
                    if cluster_connected:
                        info = dx_cluster.get('info', {})
                        print(f"    ✓ Connected to {info.get('host')}:{info.get('port')}")
                        print(f"    Callsign: {info.get('callsign')}")
                        print(f"    IARU Region: {info.get('iaru_region')}")
                        print(f"    Cached spots: {info.get('cached_spots')}")
                    else:
                        print(f"    ⚠ Not connected to DX cluster yet")
                        print(f"    (Connection happens on first MCP request)")

                    return True  # Server is healthy
                else:
                    print(f"✗ Health check failed with status: {response.status}")
                    return False
    except Exception as e:
        print(f"✗ Could not connect to server: {e}")
        return False


async def main():
    """Run tests."""
    import argparse

    parser = argparse.ArgumentParser(description="Test MCP DX Cluster Server")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="MCP server URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--health-only",
        action="store_true",
        help="Only test health check endpoint"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("DX Cluster MCP Server - Connection Test")
    print("=" * 60)
    print()

    # First, test health check
    health_ok = await test_health_check(args.url)

    if not health_ok:
        print("\n⚠ Server is not responding. Is the server running?")
        print("Start the server with: docker-compose up")
        sys.exit(1)

    if args.health_only:
        print("\n✓ Health check passed!")
        return

    print()

    # Then test full MCP connection
    await test_mcp_connection(args.url)


if __name__ == "__main__":
    asyncio.run(main())
