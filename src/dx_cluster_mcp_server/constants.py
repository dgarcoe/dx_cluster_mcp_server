"""Constants for DX Cluster MCP Server."""

from typing import Dict, Tuple

# Amateur radio band frequency ranges in kHz
BAND_RANGES: Dict[str, Tuple[float, float]] = {
    "160m": (1800.0, 2000.0),
    "80m": (3500.0, 4000.0),
    "60m": (5330.0, 5405.0),
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

# Valid band names
VALID_BANDS = list(BAND_RANGES.keys())

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
