"""Utility functions for DX Cluster MCP Server."""

import re
from typing import Optional, Tuple, Dict

from .models import DXSpot
from .constants import DX_SPOT_PATTERN, BAND_RANGES_BY_REGION, BAND_RANGES


def parse_dx_spot(line: str) -> Optional[DXSpot]:
    """Parse a DX spot line from the cluster.

    Args:
        line: Raw line from the DX cluster.

    Returns:
        DXSpot object if parsing succeeds, None otherwise.
    """
    match = re.search(DX_SPOT_PATTERN, line)

    if not match:
        return None

    try:
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
            comment=comment,
        )
    except (ValueError, IndexError):
        return None


def get_band_ranges_for_region(region: str) -> Dict[str, Tuple[float, float]]:
    """Get band ranges for a specific IARU region.

    Args:
        region: IARU region ('1', '2', or '3').

    Returns:
        Dictionary mapping band names to frequency ranges.
    """
    return BAND_RANGES_BY_REGION.get(region, BAND_RANGES_BY_REGION["2"])


def get_band_range(band: str, region: str = "2") -> Optional[Tuple[float, float]]:
    """Get frequency range for a given band in a specific region.

    Args:
        band: Band name (e.g., '20m', '40m').
        region: IARU region ('1', '2', or '3'). Defaults to '2'.

    Returns:
        Tuple of (min_freq, max_freq) in kHz, or None if band is invalid.
    """
    band_ranges = get_band_ranges_for_region(region)
    return band_ranges.get(band)


def validate_band(band: str, region: str = "2") -> bool:
    """Check if a band name is valid for a specific region.

    Args:
        band: Band name to validate.
        region: IARU region ('1', '2', or '3'). Defaults to '2'.

    Returns:
        True if band is valid, False otherwise.
    """
    band_ranges = get_band_ranges_for_region(region)
    return band in band_ranges


def validate_frequency_range(min_freq: float, max_freq: float) -> bool:
    """Validate a frequency range.

    Args:
        min_freq: Minimum frequency in kHz.
        max_freq: Maximum frequency in kHz.

    Returns:
        True if range is valid, False otherwise.
    """
    return 0 < min_freq < max_freq


def format_spot_list(spots: list[DXSpot], title: str = "") -> str:
    """Format a list of spots as a human-readable string.

    Args:
        spots: List of DXSpot objects.
        title: Optional title to prepend.

    Returns:
        Formatted string representation of the spots.
    """
    if not spots:
        return "No spots found."

    lines = []
    if title:
        lines.append(title)
        lines.append("")

    for spot in spots:
        lines.append(f"• {spot.to_string()}")

    return "\n".join(lines)
