#!/usr/bin/env python3
"""
DX Cluster MCP Server

An MCP server that provides access to ham radio DX cluster networks,
allowing AI assistants to query DX spots and propagation information.
"""

import asyncio
import os
import sys
import json
import re
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from collections import deque

from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.server.stdio
from pydantic import BaseModel, Field


class DXSpot(BaseModel):
    """Represents a DX spot from the cluster."""
    callsign: str = Field(description="The DX station callsign")
    frequency: float = Field(description="Frequency in kHz")
    spotter: str = Field(description="Callsign of the spotter")
    time: str = Field(description="Time of the spot")
    comment: str = Field(default="", description="Additional comment")

    def to_string(self) -> str:
        """Format spot as a string."""
        return f"{self.callsign} on {self.frequency} kHz spotted by {self.spotter} at {self.time} - {self.comment}"


class DXClusterClient:
    """Manages connection to a DX cluster via telnet."""

    def __init__(self, host: str, port: int, callsign: str):
        self.host = host
        self.port = port
        self.callsign = callsign
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
        self.spots_buffer = deque(maxlen=500)  # Keep last 500 spots
        self.receive_task: Optional[asyncio.Task] = None

    async def connect(self) -> bool:
        """Connect to the DX cluster."""
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port
            )

            # Wait for login prompt and send callsign
            await asyncio.sleep(1)
            await self.send_command(self.callsign)
            await asyncio.sleep(1)

            self.connected = True

            # Start receiving spots in background
            self.receive_task = asyncio.create_task(self._receive_loop())

            return True
        except Exception as e:
            print(f"Failed to connect to DX cluster: {e}", file=sys.stderr)
            return False

    async def disconnect(self):
        """Disconnect from the DX cluster."""
        self.connected = False

        if self.receive_task:
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass

        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except:
                pass

    async def send_command(self, command: str):
        """Send a command to the cluster."""
        if not self.writer:
            raise Exception("Not connected to cluster")

        self.writer.write(f"{command}\n".encode())
        await self.writer.drain()

    async def _receive_loop(self):
        """Background task to receive and parse spots."""
        try:
            while self.connected and self.reader:
                line = await self.reader.readline()
                if not line:
                    break

                decoded = line.decode('utf-8', errors='ignore').strip()
                if decoded:
                    spot = self._parse_spot(decoded)
                    if spot:
                        self.spots_buffer.append(spot)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error in receive loop: {e}", file=sys.stderr)

    def _parse_spot(self, line: str) -> Optional[DXSpot]:
        """Parse a DX spot line."""
        # Common DX cluster format: DX de SPOTTER:     FREQ.F CALLSIGN  COMMENT                 TIME Z
        # Example: DX de W1AW:     14074.0  K1ABC     FT8 signal                    1234Z

        # Try to match the standard DX spot format
        pattern = r'DX de\s+(\S+):\s+(\d+\.?\d*)\s+(\S+)\s+(.+?)\s+(\d{4}Z)'
        match = re.search(pattern, line)

        if match:
            spotter = match.group(1)
            frequency = float(match.group(2))
            callsign = match.group(3)
            comment = match.group(4).strip()
            time = match.group(5)

            return DXSpot(
                callsign=callsign,
                frequency=frequency,
                spotter=spotter,
                time=time,
                comment=comment
            )

        return None

    def get_recent_spots(self, count: int = 10) -> List[DXSpot]:
        """Get the most recent spots."""
        spots_list = list(self.spots_buffer)
        return spots_list[-count:] if len(spots_list) >= count else spots_list

    def search_by_callsign(self, callsign: str) -> List[DXSpot]:
        """Search for spots by callsign."""
        callsign_upper = callsign.upper()
        return [
            spot for spot in self.spots_buffer
            if callsign_upper in spot.callsign.upper()
        ]

    def search_by_frequency(self, min_freq: float, max_freq: float) -> List[DXSpot]:
        """Search for spots within a frequency range."""
        return [
            spot for spot in self.spots_buffer
            if min_freq <= spot.frequency <= max_freq
        ]

    def get_band_spots(self, band: str) -> List[DXSpot]:
        """Get spots for a specific ham band."""
        band_ranges = {
            "160m": (1800, 2000),
            "80m": (3500, 4000),
            "60m": (5330, 5405),
            "40m": (7000, 7300),
            "30m": (10100, 10150),
            "20m": (14000, 14350),
            "17m": (18068, 18168),
            "15m": (21000, 21450),
            "12m": (24890, 24990),
            "10m": (28000, 29700),
            "6m": (50000, 54000),
            "2m": (144000, 148000),
        }

        if band not in band_ranges:
            return []

        min_freq, max_freq = band_ranges[band]
        return self.search_by_frequency(min_freq, max_freq)


# Global DX cluster client
dx_client: Optional[DXClusterClient] = None


async def get_dx_client() -> DXClusterClient:
    """Get or create the DX cluster client."""
    global dx_client

    if dx_client is None or not dx_client.connected:
        host = os.getenv("DX_CLUSTER_HOST", "dxc.nc7j.com")
        port = int(os.getenv("DX_CLUSTER_PORT", "7300"))
        callsign = os.getenv("DX_CLUSTER_CALLSIGN", "MCP-SERVER")

        dx_client = DXClusterClient(host, port, callsign)
        await dx_client.connect()

        # Wait a bit for initial spots to come in
        await asyncio.sleep(3)

    return dx_client


# Create MCP server
app = Server("dx-cluster-mcp-server")


@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="dx://spots/recent",
            name="Recent DX Spots",
            description="Most recent DX spots from the cluster",
            mimeType="application/json",
        ),
        Resource(
            uri="dx://spots/all",
            name="All Cached Spots",
            description="All DX spots currently in the buffer",
            mimeType="application/json",
        ),
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource."""
    client = await get_dx_client()

    if uri == "dx://spots/recent":
        spots = client.get_recent_spots(20)
        return json.dumps([spot.model_dump() for spot in spots], indent=2)

    elif uri == "dx://spots/all":
        spots = list(client.spots_buffer)
        return json.dumps([spot.model_dump() for spot in spots], indent=2)

    else:
        raise ValueError(f"Unknown resource: {uri}")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_recent_spots",
            description="Get the most recent DX spots from the cluster",
            inputSchema={
                "type": "object",
                "properties": {
                    "count": {
                        "type": "number",
                        "description": "Number of spots to retrieve (default: 10, max: 100)",
                        "default": 10,
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
                    }
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
                        "description": "Ham radio band (e.g., '20m', '40m', '80m', '160m', '15m', '10m', '6m', '2m')",
                        "enum": ["160m", "80m", "60m", "40m", "30m", "20m", "17m", "15m", "12m", "10m", "6m", "2m"],
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


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    try:
        client = await get_dx_client()

        if name == "get_recent_spots":
            count = min(arguments.get("count", 10), 100)
            spots = client.get_recent_spots(count)

            if not spots:
                return [TextContent(
                    type="text",
                    text="No spots available yet. The cluster may still be loading, or there may be no recent activity."
                )]

            result = f"Found {len(spots)} recent spots:\n\n"
            for spot in spots:
                result += f"• {spot.to_string()}\n"

            return [TextContent(type="text", text=result)]

        elif name == "search_by_callsign":
            callsign = arguments["callsign"]
            spots = client.search_by_callsign(callsign)

            if not spots:
                return [TextContent(
                    type="text",
                    text=f"No spots found for callsign: {callsign}"
                )]

            result = f"Found {len(spots)} spots for {callsign}:\n\n"
            for spot in spots:
                result += f"• {spot.to_string()}\n"

            return [TextContent(type="text", text=result)]

        elif name == "search_by_frequency":
            min_freq = arguments["min_frequency"]
            max_freq = arguments["max_frequency"]
            spots = client.search_by_frequency(min_freq, max_freq)

            if not spots:
                return [TextContent(
                    type="text",
                    text=f"No spots found between {min_freq} kHz and {max_freq} kHz"
                )]

            result = f"Found {len(spots)} spots between {min_freq} kHz and {max_freq} kHz:\n\n"
            for spot in spots:
                result += f"• {spot.to_string()}\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_band_spots":
            band = arguments["band"]
            spots = client.get_band_spots(band)

            if not spots:
                return [TextContent(
                    type="text",
                    text=f"No spots found for {band} band"
                )]

            result = f"Found {len(spots)} spots on {band} band:\n\n"
            for spot in spots:
                result += f"• {spot.to_string()}\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_cluster_status":
            status = {
                "connected": client.connected,
                "host": client.host,
                "port": client.port,
                "callsign": client.callsign,
                "cached_spots": len(client.spots_buffer),
            }

            result = f"""DX Cluster Connection Status:
• Connected: {status['connected']}
• Host: {status['host']}:{status['port']}
• Callsign: {status['callsign']}
• Cached spots: {status['cached_spots']}
"""

            return [TextContent(type="text", text=result)]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
