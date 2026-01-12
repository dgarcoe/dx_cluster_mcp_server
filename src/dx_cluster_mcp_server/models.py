"""Data models for DX Cluster MCP Server."""

from typing import Dict, Any
from pydantic import BaseModel, Field


class DXSpot(BaseModel):
    """Represents a DX spot from the cluster.

    A DX spot contains information about a station that was heard
    on a specific frequency, including who spotted it and when.
    """

    callsign: str = Field(description="The DX station callsign")
    frequency: float = Field(description="Frequency in kHz")
    spotter: str = Field(description="Callsign of the spotter")
    time: str = Field(description="Time of the spot (HHMMZ format)")
    comment: str = Field(default="", description="Additional comment or mode information")

    def to_string(self) -> str:
        """Format spot as a human-readable string.

        Returns:
            Formatted string representation of the spot.
        """
        comment_part = f" - {self.comment}" if self.comment else ""
        return (
            f"{self.callsign} on {self.frequency} kHz "
            f"spotted by {self.spotter} at {self.time}{comment_part}"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert spot to dictionary.

        Returns:
            Dictionary representation of the spot.
        """
        return self.model_dump()


class ClusterStatus(BaseModel):
    """Represents the status of the DX cluster connection."""

    connected: bool = Field(description="Whether connected to the cluster")
    host: str = Field(description="Hostname of the cluster")
    port: int = Field(description="Port number")
    callsign: str = Field(description="Callsign used for connection")
    cached_spots: int = Field(description="Number of spots in the buffer")

    def to_string(self) -> str:
        """Format status as a human-readable string.

        Returns:
            Formatted string representation of the status.
        """
        return (
            f"DX Cluster Connection Status:\n"
            f"• Connected: {self.connected}\n"
            f"• Host: {self.host}:{self.port}\n"
            f"• Callsign: {self.callsign}\n"
            f"• Cached spots: {self.cached_spots}"
        )
