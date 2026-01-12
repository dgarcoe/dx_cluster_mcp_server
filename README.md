# DX Cluster MCP Server

A Model Context Protocol (MCP) server that provides AI assistants with access to ham radio DX cluster networks. Query real-time DX spots, search by callsign or frequency, and get propagation information directly through your AI assistant.

## Features

- **Real-time DX Spots**: Connect to DX cluster networks and receive live propagation information
- **Multiple Search Options**:
  - Get recent DX spots
  - Search by callsign (partial matches supported)
  - Search by frequency range
  - Filter by amateur radio band (160m-2m)
- **MCP Integration**: Seamless integration with Claude Desktop and other MCP clients
- **Docker Support**: Fully containerized with Docker Compose for easy deployment
- **Automatic Reconnection**: Maintains connection to the DX cluster

## What is a DX Cluster?

A DX cluster is a network where amateur radio operators share information about DX (long distance) contacts. When an operator spots a rare or interesting station, they post it to the cluster, and the information is distributed to all connected users in real-time. This helps operators find interesting stations to contact and track propagation conditions.

## Installation

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/dx_cluster_mcp_server.git
cd dx_cluster_mcp_server
```

2. Copy the example environment file and configure it:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Build and run with Docker Compose:
```bash
docker-compose up -d
```

4. View logs:
```bash
docker-compose logs -f
```

### Using Docker

```bash
# Build the image
docker build -t dx-cluster-mcp-server .

# Run the container
docker run -it --rm \
  -e DX_CLUSTER_HOST=dxc.nc7j.com \
  -e DX_CLUSTER_PORT=7300 \
  -e DX_CLUSTER_CALLSIGN=YOUR-CALLSIGN \
  dx-cluster-mcp-server
```

### Local Development

1. Install Python 3.10 or higher

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -e .
```

4. Set environment variables:
```bash
export DX_CLUSTER_HOST=dxc.nc7j.com
export DX_CLUSTER_PORT=7300
export DX_CLUSTER_CALLSIGN=YOUR-CALLSIGN
```

5. Run the server:
```bash
python -m dx_cluster_mcp_server.server
```

## Configuration

Configure the server using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DX_CLUSTER_HOST` | Hostname of the DX cluster | `dxc.nc7j.com` |
| `DX_CLUSTER_PORT` | Port number (usually 7300 or 23) | `7300` |
| `DX_CLUSTER_CALLSIGN` | Your amateur radio callsign | `MCP-SERVER` |

### Popular DX Clusters

- **NC7J DX Cluster**: dxc.nc7j.com:7300
- **DXFun**: dxfun.com:8000
- **W6CUA**: w6cua.no-ip.org:7300
- **VE7CC**: ve7cc.net:23

## MCP Integration

### Claude Desktop Configuration

Add to your Claude Desktop config file:

**MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "dx-cluster": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "DX_CLUSTER_HOST=dxc.nc7j.com",
        "-e",
        "DX_CLUSTER_PORT=7300",
        "-e",
        "DX_CLUSTER_CALLSIGN=YOUR-CALLSIGN",
        "dx-cluster-mcp-server"
      ]
    }
  }
}
```

Or if running locally with Python:

```json
{
  "mcpServers": {
    "dx-cluster": {
      "command": "python",
      "args": ["-m", "dx_cluster_mcp_server.server"],
      "env": {
        "DX_CLUSTER_HOST": "dxc.nc7j.com",
        "DX_CLUSTER_PORT": "7300",
        "DX_CLUSTER_CALLSIGN": "YOUR-CALLSIGN"
      }
    }
  }
}
```

## Available Tools

The MCP server provides the following tools:

### get_recent_spots
Get the most recent DX spots from the cluster.

**Parameters**:
- `count` (optional): Number of spots to retrieve (default: 10, max: 100)

**Example**: "Show me the 20 most recent DX spots"

### search_by_callsign
Search for DX spots by callsign (supports partial matches).

**Parameters**:
- `callsign` (required): The callsign to search for

**Example**: "Search for spots with K1ABC"

### search_by_frequency
Search for DX spots within a frequency range.

**Parameters**:
- `min_frequency` (required): Minimum frequency in kHz
- `max_frequency` (required): Maximum frequency in kHz

**Example**: "Show me spots between 14000 and 14350 kHz"

### get_band_spots
Get DX spots for a specific amateur radio band.

**Parameters**:
- `band` (required): Ham radio band (160m, 80m, 60m, 40m, 30m, 20m, 17m, 15m, 12m, 10m, 6m, 2m)

**Example**: "What spots are on 20 meters?"

### get_cluster_status
Get the current status of the DX cluster connection.

**Example**: "Is the cluster connected?"

## Available Resources

### dx://spots/recent
Get the 20 most recent DX spots as JSON.

### dx://spots/all
Get all cached DX spots (up to 500) as JSON.

## Example Prompts for Claude

Once configured, you can ask Claude questions like:

- "What are the latest DX spots?"
- "Show me all spots on 20 meters"
- "Are there any spots for JA stations?"
- "What's happening on 40 meters right now?"
- "Show me spots between 14.000 and 14.100 MHz"
- "Is K1ABC being spotted anywhere?"
- "What's the cluster status?"

## Development

### Project Structure

```
dx_cluster_mcp_server/
├── src/
│   └── dx_cluster_mcp_server/
│       ├── __init__.py
│       └── server.py          # Main MCP server implementation
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```

### Running Tests

```bash
# Install development dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
```

## Troubleshooting

### Connection Issues

If you can't connect to a DX cluster:

1. Verify the hostname and port are correct
2. Check that your firewall allows outbound telnet connections
3. Some clusters require a valid amateur radio callsign
4. Try an alternative DX cluster from the list above

### Docker Issues

If the container won't start:

```bash
# Check logs
docker-compose logs dx-cluster-mcp-server

# Rebuild the image
docker-compose build --no-cache

# Restart the service
docker-compose restart
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Built with the [Model Context Protocol](https://modelcontextprotocol.io/)
- Thanks to the amateur radio community and DX cluster operators
- DX cluster format based on the AR-Cluster/CC Cluster protocol

## Amateur Radio Resources

- **ARRL**: https://www.arrl.org/
- **DX Summit**: https://dxsummit.fi/
- **QRZ**: https://www.qrz.com/

73 and good DX!
