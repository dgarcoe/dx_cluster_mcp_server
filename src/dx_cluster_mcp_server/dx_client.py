"""DX Cluster client for connecting to and managing DX cluster connections."""

import asyncio
import sys
from typing import Optional, List
from collections import deque

from .config import DXClusterConfig
from .models import DXSpot
from .utils import parse_dx_spot, get_band_range
from .constants import DEFAULT_LOGIN_DELAY_SECONDS, INITIAL_SPOTS_WAIT_SECONDS


class DXClusterClient:
    """Manages connection to a DX cluster via telnet.

    This client handles the connection lifecycle, authentication,
    and receiving/parsing of DX spots from the cluster.
    """

    def __init__(self, config: DXClusterConfig):
        """Initialize the DX cluster client.

        Args:
            config: Configuration for the cluster connection.
        """
        self.config = config
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
        self.spots_buffer: deque[DXSpot] = deque(maxlen=config.buffer_size)
        self.receive_task: Optional[asyncio.Task] = None

    async def connect(self) -> bool:
        """Connect to the DX cluster.

        Returns:
            True if connection successful, False otherwise.
        """
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.config.host, self.config.port),
                timeout=self.config.connection_timeout,
            )

            await self._authenticate()
            self.connected = True
            self._start_receive_loop()

            # Wait for initial spots to populate
            await asyncio.sleep(INITIAL_SPOTS_WAIT_SECONDS)

            return True

        except asyncio.TimeoutError:
            print(
                f"Connection timeout to {self.config.host}:{self.config.port}",
                file=sys.stderr,
            )
            return False
        except Exception as e:
            print(f"Failed to connect to DX cluster: {e}", file=sys.stderr)
            return False

    async def disconnect(self) -> None:
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
            except Exception:
                pass

    async def send_command(self, command: str) -> None:
        """Send a command to the cluster.

        Args:
            command: Command string to send.

        Raises:
            RuntimeError: If not connected to cluster.
        """
        if not self.writer:
            raise RuntimeError("Not connected to cluster")

        self.writer.write(f"{command}\n".encode())
        await self.writer.drain()

    def get_recent_spots(self, count: int) -> List[DXSpot]:
        """Get the most recent spots from the buffer.

        Args:
            count: Number of spots to retrieve.

        Returns:
            List of the most recent DXSpot objects.
        """
        spots_list = list(self.spots_buffer)
        return spots_list[-count:] if len(spots_list) >= count else spots_list

    def search_by_callsign(self, callsign: str) -> List[DXSpot]:
        """Search for spots by callsign (partial match).

        Args:
            callsign: Callsign to search for.

        Returns:
            List of matching DXSpot objects.
        """
        callsign_upper = callsign.upper()
        return [
            spot
            for spot in self.spots_buffer
            if callsign_upper in spot.callsign.upper()
        ]

    def search_by_frequency(self, min_freq: float, max_freq: float) -> List[DXSpot]:
        """Search for spots within a frequency range.

        Args:
            min_freq: Minimum frequency in kHz.
            max_freq: Maximum frequency in kHz.

        Returns:
            List of DXSpot objects within the range.
        """
        return [
            spot
            for spot in self.spots_buffer
            if min_freq <= spot.frequency <= max_freq
        ]

    def get_band_spots(self, band: str) -> List[DXSpot]:
        """Get spots for a specific amateur radio band.

        Args:
            band: Band name (e.g., '20m', '40m').

        Returns:
            List of DXSpot objects for the specified band.
        """
        band_range = get_band_range(band)
        if not band_range:
            return []

        min_freq, max_freq = band_range
        return self.search_by_frequency(min_freq, max_freq)

    def get_status(self) -> dict:
        """Get current client status.

        Returns:
            Dictionary containing status information.
        """
        return {
            "connected": self.connected,
            "host": self.config.host,
            "port": self.config.port,
            "callsign": self.config.callsign,
            "cached_spots": len(self.spots_buffer),
        }

    async def _authenticate(self) -> None:
        """Authenticate with the DX cluster."""
        await asyncio.sleep(DEFAULT_LOGIN_DELAY_SECONDS)
        await self.send_command(self.config.callsign)
        await asyncio.sleep(DEFAULT_LOGIN_DELAY_SECONDS)

    def _start_receive_loop(self) -> None:
        """Start the background task to receive spots."""
        self.receive_task = asyncio.create_task(self._receive_loop())

    async def _receive_loop(self) -> None:
        """Background task to receive and parse spots."""
        try:
            while self.connected and self.reader:
                line = await asyncio.wait_for(
                    self.reader.readline(),
                    timeout=self.config.receive_timeout,
                )

                if not line:
                    break

                decoded = line.decode("utf-8", errors="ignore").strip()
                if decoded:
                    spot = parse_dx_spot(decoded)
                    if spot:
                        self.spots_buffer.append(spot)

        except asyncio.TimeoutError:
            print("Receive timeout - connection may be stale", file=sys.stderr)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error in receive loop: {e}", file=sys.stderr)
        finally:
            self.connected = False
