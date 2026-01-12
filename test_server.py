#!/usr/bin/env python3
"""Test script to verify DX Cluster MCP Server functionality."""

import sys
import asyncio
from typing import List

# Add src to path
sys.path.insert(0, '/home/user/dx_cluster_mcp_server/src')


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from dx_cluster_mcp_server import (
            DXClusterConfig,
            DXClusterClient,
            DXSpot,
            ClusterStatus,
        )
        from dx_cluster_mcp_server.constants import BAND_RANGES, VALID_BANDS
        from dx_cluster_mcp_server.utils import (
            parse_dx_spot,
            validate_band,
            validate_frequency_range,
            format_spot_list,
        )
        from dx_cluster_mcp_server.mcp_handlers import (
            MCPResourceHandler,
            MCPToolHandler,
        )
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_models():
    """Test data models."""
    print("\nTesting models...")
    try:
        from dx_cluster_mcp_server.models import DXSpot, ClusterStatus

        # Test DXSpot
        spot = DXSpot(
            callsign="K1ABC",
            frequency=14074.0,
            spotter="W1XYZ",
            time="1234Z",
            comment="FT8 signal",
        )
        spot_str = spot.to_string()
        assert "K1ABC" in spot_str
        assert "14074.0" in spot_str
        print(f"  DXSpot: {spot_str}")

        # Test ClusterStatus
        status = ClusterStatus(
            connected=True,
            host="dxc.nc7j.com",
            port=7300,
            callsign="TEST",
            iaru_region="2",
            cached_spots=42,
        )
        status_str = status.to_string()
        assert "dxc.nc7j.com" in status_str
        assert "Region: 2" in status_str
        print(f"  ClusterStatus created successfully")

        print("✓ Models working correctly")
        return True
    except Exception as e:
        print(f"✗ Model test failed: {e}")
        return False


def test_utils():
    """Test utility functions."""
    print("\nTesting utilities...")
    try:
        from dx_cluster_mcp_server.utils import (
            parse_dx_spot,
            validate_band,
            validate_frequency_range,
            get_band_range,
        )

        # Test DX spot parsing
        sample_line = "DX de W1AW:     14074.0  K1ABC     FT8 signal                    1234Z"
        spot = parse_dx_spot(sample_line)
        assert spot is not None
        assert spot.callsign == "K1ABC"
        assert spot.frequency == 14074.0
        assert spot.spotter == "W1AW"
        print(f"  Parsed spot: {spot.to_string()}")

        # Test band validation
        assert validate_band("20m") == True
        assert validate_band("99m") == False
        print("  Band validation working")

        # Test frequency validation
        assert validate_frequency_range(14000, 14350) == True
        assert validate_frequency_range(14350, 14000) == False
        print("  Frequency validation working")

        # Test band range lookup
        band_range = get_band_range("20m")
        assert band_range == (14000.0, 14350.0)
        print(f"  Band range lookup: 20m = {band_range}")

        print("✓ Utilities working correctly")
        return True
    except Exception as e:
        print(f"✗ Utility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """Test configuration."""
    print("\nTesting configuration...")
    try:
        from dx_cluster_mcp_server.config import DXClusterConfig

        # Test manual config
        config = DXClusterConfig(
            host="test.example.com",
            port=7300,
            callsign="TEST",
            buffer_size=500,
        )
        config.validate()
        print(f"  Config created: {config.host}:{config.port}")

        # Test validation
        try:
            bad_config = DXClusterConfig(
                host="test.example.com",
                port=99999,  # Invalid port
                callsign="TEST",
            )
            bad_config.validate()
            print("✗ Validation should have failed")
            return False
        except ValueError:
            print("  Config validation working (caught invalid port)")

        print("✓ Configuration working correctly")
        return True
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_constants():
    """Test constants."""
    print("\nTesting constants...")
    try:
        from dx_cluster_mcp_server.constants import (
            BAND_RANGES,
            VALID_BANDS,
            DX_SPOT_PATTERN,
        )

        assert len(BAND_RANGES) == 12
        assert "20m" in BAND_RANGES
        assert BAND_RANGES["20m"] == (14000.0, 14350.0)
        print(f"  Band ranges loaded: {len(BAND_RANGES)} bands")

        assert len(VALID_BANDS) == 12
        assert "40m" in VALID_BANDS
        print(f"  Valid bands: {', '.join(VALID_BANDS)}")

        print("✓ Constants defined correctly")
        return True
    except Exception as e:
        print(f"✗ Constants test failed: {e}")
        return False


def test_dx_client_structure():
    """Test DX client class structure (without connecting)."""
    print("\nTesting DX client structure...")
    try:
        from dx_cluster_mcp_server.dx_client import DXClusterClient
        from dx_cluster_mcp_server.config import DXClusterConfig

        config = DXClusterConfig(
            host="test.example.com", port=7300, callsign="TEST"
        )
        client = DXClusterClient(config)

        # Check client has required methods
        assert hasattr(client, "connect")
        assert hasattr(client, "disconnect")
        assert hasattr(client, "get_recent_spots")
        assert hasattr(client, "search_by_callsign")
        assert hasattr(client, "search_by_frequency")
        assert hasattr(client, "get_band_spots")
        assert hasattr(client, "get_status")

        print("  Client has all required methods")

        # Test that spots buffer is initialized
        assert hasattr(client, "spots_buffer")
        assert len(client.spots_buffer) == 0
        print("  Spots buffer initialized")

        print("✓ DX client structure correct")
        return True
    except Exception as e:
        print(f"✗ DX client test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mcp_handlers_structure():
    """Test MCP handlers structure (without actual client)."""
    print("\nTesting MCP handlers structure...")
    try:
        from dx_cluster_mcp_server.mcp_handlers import (
            MCPResourceHandler,
            MCPToolHandler,
        )
        from dx_cluster_mcp_server.dx_client import DXClusterClient
        from dx_cluster_mcp_server.config import DXClusterConfig

        config = DXClusterConfig(
            host="test.example.com", port=7300, callsign="TEST"
        )
        client = DXClusterClient(config)

        # Test resource handler
        resource_handler = MCPResourceHandler(client)
        resources = resource_handler.list_resources()
        assert len(resources) > 0
        print(f"  Resource handler: {len(resources)} resources defined")

        # Test tool handler
        tool_handler = MCPToolHandler(client)
        tools = tool_handler.list_tools()
        assert len(tools) == 5
        tool_names = [tool.name for tool in tools]
        print(f"  Tool handler: {len(tools)} tools defined")
        print(f"  Tools: {', '.join(tool_names)}")

        expected_tools = [
            "get_recent_spots",
            "search_by_callsign",
            "search_by_frequency",
            "get_band_spots",
            "get_cluster_status",
        ]
        for tool_name in expected_tools:
            assert tool_name in tool_names
        print("  All expected tools present")

        print("✓ MCP handlers structure correct")
        return True
    except Exception as e:
        print(f"✗ MCP handlers test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("DX Cluster MCP Server - Test Suite")
    print("=" * 60)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("Models", test_models()))
    results.append(("Utils", test_utils()))
    results.append(("Config", test_config()))
    results.append(("Constants", test_constants()))
    results.append(("DX Client", test_dx_client_structure()))
    results.append(("MCP Handlers", test_mcp_handlers_structure()))

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n🎉 All tests passed! The code is working correctly.")
        print("\nNote: This validates the code structure and logic.")
        print("To test actual DX cluster connectivity, you would need to:")
        print("  1. Have network access to a DX cluster")
        print("  2. Run: python -m dx_cluster_mcp_server.server")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
