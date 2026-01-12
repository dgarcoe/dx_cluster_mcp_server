"""Constants for DX Cluster MCP Server."""

from typing import Dict, Tuple

# Amateur radio band frequency ranges by IARU Region (in kHz)
# Reference: https://www.iaru.org/

BAND_RANGES_REGION_1: Dict[str, Tuple[float, float]] = {
    "160m": (1810.0, 2000.0),
    "80m": (3500.0, 3800.0),
    "60m": (5351.5, 5366.5),  # Various allocations, varies by country
    "40m": (7000.0, 7200.0),
    "30m": (10100.0, 10150.0),
    "20m": (14000.0, 14350.0),
    "17m": (18068.0, 18168.0),
    "15m": (21000.0, 21450.0),
    "12m": (24890.0, 24990.0),
    "10m": (28000.0, 29700.0),
    "6m": (50000.0, 52000.0),
    "2m": (144000.0, 146000.0),
}

BAND_RANGES_REGION_2: Dict[str, Tuple[float, float]] = {
    "160m": (1800.0, 2000.0),
    "80m": (3500.0, 4000.0),
    "60m": (5330.5, 5403.5),  # Various channels
    "40m": (7000.0, 7300.0),
    "30m": (10100.0, 10150.0),
    "20m": (14000.0, 14350.0),
    "17m": (18068.0, 18168.0),
    "15m": (21000.0, 21450.0),
    "12m": (24890.0, 24990.0),
    "10m": (28000.0, 29700.0),
    "6m": (50000.0, 54000.0),
    "2m": (144000.0, 148000.0),
}

BAND_RANGES_REGION_3: Dict[str, Tuple[float, float]] = {
    "160m": (1800.0, 2000.0),
    "80m": (3500.0, 3900.0),
    "60m": (5351.5, 5366.5),  # Limited allocations
    "40m": (7000.0, 7200.0),
    "30m": (10100.0, 10150.0),
    "20m": (14000.0, 14350.0),
    "17m": (18068.0, 18168.0),
    "15m": (21000.0, 21450.0),
    "12m": (24890.0, 24990.0),
    "10m": (28000.0, 29700.0),
    "6m": (50000.0, 54000.0),
    "2m": (144000.0, 146000.0),
}

# Map region names to band ranges
BAND_RANGES_BY_REGION: Dict[str, Dict[str, Tuple[float, float]]] = {
    "1": BAND_RANGES_REGION_1,
    "2": BAND_RANGES_REGION_2,
    "3": BAND_RANGES_REGION_3,
}

# Default to Region 2 (Americas) for backward compatibility
BAND_RANGES = BAND_RANGES_REGION_2

# Valid band names
VALID_BANDS = list(BAND_RANGES.keys())

# Valid IARU regions
VALID_IARU_REGIONS = ["1", "2", "3"]

# DX spot parsing regex pattern
# Format: DX de SPOTTER:     FREQ.F CALLSIGN  COMMENT                 HHMMZ
DX_SPOT_PATTERN = r'DX de\s+(\S+):\s+(\d+\.?\d*)\s+(\S+)\s+(.+?)\s+(\d{4}Z)'

# Maximum number of spots to return in a single query
MAX_SPOTS_PER_QUERY = 100

# Default number of spots to return
DEFAULT_SPOTS_COUNT = 10

# Connection settings
DEFAULT_LOGIN_DELAY_SECONDS = 1
INITIAL_SPOTS_WAIT_SECONDS = 3

# Resource URIs
RESOURCE_URI_RECENT = "dx://spots/recent"
RESOURCE_URI_ALL = "dx://spots/all"
