"""Configuration management for DX Cluster MCP Server."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DXClusterConfig:
    """Configuration for DX cluster connection."""

    host: str
    port: int
    callsign: str
    buffer_size: int = 500
    connection_timeout: int = 10
    receive_timeout: int = 120

    @classmethod
    def from_environment(cls) -> "DXClusterConfig":
        """Create configuration from environment variables.

        Returns:
            DXClusterConfig instance populated from environment variables.
        """
        return cls(
            host=os.getenv("DX_CLUSTER_HOST", "dxc.nc7j.com"),
            port=int(os.getenv("DX_CLUSTER_PORT", "7300")),
            callsign=os.getenv("DX_CLUSTER_CALLSIGN", "MCP-SERVER"),
            buffer_size=int(os.getenv("DX_CLUSTER_BUFFER_SIZE", "500")),
            connection_timeout=int(os.getenv("DX_CLUSTER_CONNECTION_TIMEOUT", "10")),
            receive_timeout=int(os.getenv("DX_CLUSTER_RECEIVE_TIMEOUT", "120")),
        )

    def validate(self) -> None:
        """Validate configuration parameters.

        Raises:
            ValueError: If any configuration parameter is invalid.
        """
        if not self.host:
            raise ValueError("DX_CLUSTER_HOST cannot be empty")

        if not 1 <= self.port <= 65535:
            raise ValueError(f"Invalid port number: {self.port}")

        if not self.callsign:
            raise ValueError("DX_CLUSTER_CALLSIGN cannot be empty")

        if self.buffer_size < 1:
            raise ValueError(f"Buffer size must be positive: {self.buffer_size}")
