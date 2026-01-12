"""MCP tool and resource handlers for DX Cluster server."""

import json
from typing import Any, List

from mcp.types import Resource, Tool, TextContent

from .dx_client import DXClusterClient
from .models import ClusterStatus
from .utils import format_spot_list, validate_band, validate_frequency_range
from .constants import (
    VALID_BANDS,
    MAX_SPOTS_PER_QUERY,
    DEFAULT_SPOTS_COUNT,
    RESOURCE_URI_RECENT,
    RESOURCE_URI_ALL,
)


class MCPResourceHandler:
    """Handles MCP resource requests."""

    def __init__(self, client: DXClusterClient):
        """Initialize the resource handler.

        Args:
            client: DX cluster client instance.
        """
        self.client = client

    def list_resources(self) -> List[Resource]:
        """List available resources.

        Returns:
            List of Resource objects.
        """
        return [
            Resource(
                uri=RESOURCE_URI_RECENT,
                name="Recent DX Spots",
                description="Most recent DX spots from the cluster",
                mimeType="application/json",
            ),
            Resource(
                uri=RESOURCE_URI_ALL,
                name="All Cached Spots",
                description="All DX spots currently in the buffer",
                mimeType="application/json",
            ),
        ]

    def read_resource(self, uri: str) -> str:
        """Read a resource by URI.

        Args:
            uri: Resource URI to read.

        Returns:
            JSON string representation of the resource.

        Raises:
            ValueError: If URI is unknown.
        """
        if uri == RESOURCE_URI_RECENT:
            spots = self.client.get_recent_spots(20)
            return json.dumps([spot.to_dict() for spot in spots], indent=2)

        elif uri == RESOURCE_URI_ALL:
            spots = list(self.client.spots_buffer)
            return json.dumps([spot.to_dict() for spot in spots], indent=2)

        else:
            raise ValueError(f"Unknown resource: {uri}")


class MCPToolHandler:
    """Handles MCP tool invocations."""

    def __init__(self, client: DXClusterClient):
        """Initialize the tool handler.

        Args:
            client: DX cluster client instance.
        """
        self.client = client

    def list_tools(self) -> List[Tool]:
        """List available tools.

        Returns:
            List of Tool objects.
        """
        return [
            Tool(
                name="get_recent_spots",
                description="Get the most recent DX spots from the cluster",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "count": {
                            "type": "number",
                            "description": f"Number of spots to retrieve (default: {DEFAULT_SPOTS_COUNT}, max: {MAX_SPOTS_PER_QUERY})",
                            "default": DEFAULT_SPOTS_COUNT,
                        }
                    },
                },
            ),
            Tool(
                name="search_by_callsign",
                description="Search for DX spots by callsign",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "callsign": {
                            "type": "string",
                            "description": "The callsign to search for (partial matches supported)",
                        }
                    },
                    "required": ["callsign"],
                },
            ),
            Tool(
                name="search_by_frequency",
                description="Search for DX spots within a frequency range",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "min_frequency": {
                            "type": "number",
                            "description": "Minimum frequency in kHz",
                        },
                        "max_frequency": {
                            "type": "number",
                            "description": "Maximum frequency in kHz",
                        },
                    },
                    "required": ["min_frequency", "max_frequency"],
                },
            ),
            Tool(
                name="get_band_spots",
                description="Get DX spots for a specific amateur radio band",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "band": {
                            "type": "string",
                            "description": "Ham radio band (e.g., '20m', '40m', '80m')",
                            "enum": VALID_BANDS,
                        }
                    },
                    "required": ["band"],
                },
            ),
            Tool(
                name="get_cluster_status",
                description="Get the current status of the DX cluster connection",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
        ]

    def handle_tool_call(self, name: str, arguments: Any) -> List[TextContent]:
        """Handle a tool invocation.

        Args:
            name: Tool name.
            arguments: Tool arguments.

        Returns:
            List of TextContent responses.

        Raises:
            ValueError: If tool name is unknown.
        """
        handlers = {
            "get_recent_spots": self._handle_get_recent_spots,
            "search_by_callsign": self._handle_search_by_callsign,
            "search_by_frequency": self._handle_search_by_frequency,
            "get_band_spots": self._handle_get_band_spots,
            "get_cluster_status": self._handle_get_cluster_status,
        }

        handler = handlers.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")

        return handler(arguments)

    def _handle_get_recent_spots(self, arguments: dict) -> List[TextContent]:
        """Handle get_recent_spots tool call."""
        count = min(arguments.get("count", DEFAULT_SPOTS_COUNT), MAX_SPOTS_PER_QUERY)
        spots = self.client.get_recent_spots(count)

        if not spots:
            return [
                TextContent(
                    type="text",
                    text="No spots available yet. The cluster may still be loading, or there may be no recent activity.",
                )
            ]

        result = format_spot_list(spots, f"Found {len(spots)} recent spots:")
        return [TextContent(type="text", text=result)]

    def _handle_search_by_callsign(self, arguments: dict) -> List[TextContent]:
        """Handle search_by_callsign tool call."""
        callsign = arguments["callsign"]
        spots = self.client.search_by_callsign(callsign)

        if not spots:
            return [
                TextContent(type="text", text=f"No spots found for callsign: {callsign}")
            ]

        result = format_spot_list(spots, f"Found {len(spots)} spots for {callsign}:")
        return [TextContent(type="text", text=result)]

    def _handle_search_by_frequency(self, arguments: dict) -> List[TextContent]:
        """Handle search_by_frequency tool call."""
        min_freq = arguments["min_frequency"]
        max_freq = arguments["max_frequency"]

        if not validate_frequency_range(min_freq, max_freq):
            return [
                TextContent(
                    type="text",
                    text=f"Invalid frequency range: {min_freq} - {max_freq} kHz",
                )
            ]

        spots = self.client.search_by_frequency(min_freq, max_freq)

        if not spots:
            return [
                TextContent(
                    type="text",
                    text=f"No spots found between {min_freq} kHz and {max_freq} kHz",
                )
            ]

        result = format_spot_list(
            spots, f"Found {len(spots)} spots between {min_freq} kHz and {max_freq} kHz:"
        )
        return [TextContent(type="text", text=result)]

    def _handle_get_band_spots(self, arguments: dict) -> List[TextContent]:
        """Handle get_band_spots tool call."""
        band = arguments["band"]

        if not validate_band(band):
            return [TextContent(type="text", text=f"Invalid band: {band}")]

        spots = self.client.get_band_spots(band)

        if not spots:
            return [TextContent(type="text", text=f"No spots found for {band} band")]

        result = format_spot_list(spots, f"Found {len(spots)} spots on {band} band:")
        return [TextContent(type="text", text=result)]

    def _handle_get_cluster_status(self, arguments: dict) -> List[TextContent]:
        """Handle get_cluster_status tool call."""
        status_dict = self.client.get_status()
        status = ClusterStatus(**status_dict)
        return [TextContent(type="text", text=status.to_string())]
