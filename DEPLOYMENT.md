# DX Cluster MCP Server - Deployment Guide for ea1rfi.es

This guide will help you deploy the MCP server on your server at ea1rfi.es with your existing nginx setup.

## Prerequisites

- Your server at ea1rfi.es with Docker installed
- nginx already running with Let's Encrypt certificates
- Git installed to clone this repository

## Step 1: Clone Repository on Your Server

SSH into your server at ea1rfi.es and clone this repository:

```bash
# SSH to your server
ssh user@ea1rfi.es

# Clone the repository
git clone <your-repo-url> /opt/dx_cluster_mcp_server
cd /opt/dx_cluster_mcp_server

# Checkout the branch with nginx integration
git checkout claude/mcp-ham-radio-server-ZsgiG
```

## Step 2: Detect Your nginx Setup

Run the helper script to detect your nginx configuration:

```bash
chmod +x check_nginx_setup.sh
./check_nginx_setup.sh
```

This script will tell you:
- Whether nginx is running in Docker or on the host
- Which Docker network nginx is using (if in Docker)
- Which docker-compose file to use

## Step 3: Choose Your Deployment Method

Based on the script output, choose the appropriate method:

### Method A: nginx Running in Docker

If the script found an nginx container and network (e.g., `nginx_default`):

```bash
# Update the docker-compose file with your network name
# Replace 'nginx_default' with your actual network name from the script
sed -i 's/your_nginx_network/nginx_default/g' docker-compose.nginx-proxy.yml

# Verify the .env file is correct
cat .env

# Deploy the MCP server
docker-compose -f docker-compose.nginx-proxy.yml build
docker-compose -f docker-compose.nginx-proxy.yml up -d

# Check logs
docker-compose -f docker-compose.nginx-proxy.yml logs -f
```

**nginx configuration needed:**
```nginx
location /dx-cluster/ {
    proxy_pass http://dx-cluster-mcp-server:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Required for SSE
    proxy_http_version 1.1;
    proxy_set_header Connection '';
    proxy_buffering off;
    proxy_cache off;
    chunked_transfer_encoding off;
    proxy_read_timeout 86400s;
}
```

### Method B: nginx Running on Host System (Not in Docker)

If nginx is installed directly on your system (not in Docker):

```bash
# Use the host-nginx docker-compose configuration
docker-compose -f docker-compose.host-nginx.yml build
docker-compose -f docker-compose.host-nginx.yml up -d

# Check logs
docker-compose -f docker-compose.host-nginx.yml logs -f
```

**nginx configuration needed:**
```nginx
location /dx-cluster/ {
    proxy_pass http://127.0.0.1:8000/;  # Note: localhost instead of container name
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Required for SSE
    proxy_http_version 1.1;
    proxy_set_header Connection '';
    proxy_buffering off;
    proxy_cache off;
    chunked_transfer_encoding off;
    proxy_read_timeout 86400s;
}
```

**Key difference:** Use `http://127.0.0.1:8000/` instead of `http://dx-cluster-mcp-server:8000/` because nginx on the host needs to access the container via the published port.

## Step 4: Update nginx Configuration

Add the location block (from above) to your nginx configuration at:
- `/etc/nginx/sites-available/ea1rfi.es` (or your config file location)
- Inside the `server` block that listens on port 443

Then reload nginx:

```bash
# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
# OR if nginx is in Docker:
# docker exec <nginx-container-name> nginx -s reload
```

## Step 5: Verify Deployment

### Test 1: Health Check

```bash
# From your server
curl http://localhost:8000/health

# From anywhere (through nginx)
curl https://ea1rfi.es/dx-cluster/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "dx-cluster-mcp-server",
  "dx_cluster": {
    "connected": true,
    "info": {
      "host": "dxc.nc7j.com",
      "port": 7300,
      "callsign": "EA1RFI",
      "iaru_region": "1",
      "cached_spots": 42
    }
  }
}
```

### Test 2: SSE Endpoint

```bash
curl -N https://ea1rfi.es/dx-cluster/sse
# Should establish connection (press Ctrl+C to close)
```

### Test 3: Browser Test

Open in your browser:
```
https://ea1rfi.es/dx-cluster/health
```

Should display the JSON health response.

## Step 6: Configure Claude Desktop

On your local machine (where Claude Desktop is installed):

### macOS:
Edit `~/Library/Application Support/Claude/claude_desktop_config.json`

### Windows:
Edit `%APPDATA%/Claude/claude_desktop_config.json`

### Linux:
Edit `~/.config/Claude/claude_desktop_config.json`

**Add this configuration:**
```json
{
  "mcpServers": {
    "dx-cluster": {
      "url": "https://ea1rfi.es/dx-cluster"
    }
  }
}
```

**Important:**
- Use `https://` (nginx provides HTTPS)
- NO trailing slash on the URL

**Restart Claude Desktop:**
1. Completely quit Claude Desktop
2. Restart the application
3. The DX cluster tools should now appear

## Step 7: Test in Claude Desktop

In a Claude Desktop conversation, try:
- "Show me recent DX spots on 20m"
- "Search for callsign EA1RFI"
- "What's the cluster connection status?"

Available tools:
- `get_dx_spots` - Get recent DX spots
- `search_by_callsign` - Search spots by callsign
- `search_by_frequency` - Search by frequency range
- `search_by_band` - Filter by amateur band
- `get_cluster_status` - Check connection status

## Troubleshooting

### Issue: 502 Bad Gateway

**If using docker-compose.nginx-proxy.yml:**
```bash
# Check if containers can communicate
docker network inspect <your-network-name>
# Both nginx and dx-cluster-mcp-server should be listed

# Check if container is running
docker ps | grep dx-cluster-mcp-server
```

**If using docker-compose.host-nginx.yml:**
```bash
# Check if port is accessible from host
curl http://127.0.0.1:8000/health

# Check if port is listening
sudo netstat -tlnp | grep 8000
```

### Issue: DX Cluster Not Connected

```bash
# Check logs
docker logs dx-cluster-mcp-server

# Verify environment variables
docker exec dx-cluster-mcp-server env | grep DX_

# Test DX cluster connectivity from container
docker exec -it dx-cluster-mcp-server telnet dxc.nc7j.com 7300
```

**Solutions:**
- Verify firewall allows outbound telnet (port 7300)
- Try alternative DX clusters in `.env`:
  - `DX_CLUSTER_HOST=dxfun.com` and `DX_CLUSTER_PORT=8000`
  - `DX_CLUSTER_HOST=ve7cc.net` and `DX_CLUSTER_PORT=23`

### Issue: Claude Desktop Can't Connect

```bash
# Test from your local machine
curl -v https://ea1rfi.es/dx-cluster/health
```

**Solutions:**
- Verify URL has NO trailing slash in Claude config
- Ensure URL uses `https://`
- Completely restart Claude Desktop (quit and reopen)
- Check nginx SSL certificates are valid
- Verify nginx configuration has the location block

## Maintenance

### View Logs
```bash
# Follow logs
docker logs -f dx-cluster-mcp-server

# Last 100 lines
docker logs --tail 100 dx-cluster-mcp-server
```

### Restart Service
```bash
# Using docker-compose.nginx-proxy.yml
docker-compose -f docker-compose.nginx-proxy.yml restart

# Using docker-compose.host-nginx.yml
docker-compose -f docker-compose.host-nginx.yml restart
```

### Stop Service
```bash
docker-compose -f docker-compose.nginx-proxy.yml down
# or
docker-compose -f docker-compose.host-nginx.yml down
```

### Update Configuration

If you need to change DX cluster settings:

```bash
# Edit .env file
nano .env

# Restart container
docker-compose -f docker-compose.nginx-proxy.yml restart
# or
docker-compose -f docker-compose.host-nginx.yml restart

# Verify changes
curl https://ea1rfi.es/dx-cluster/health
```

## Quick Reference

**Files:**
- `.env` - Your configuration (callsign, region, etc.)
- `docker-compose.nginx-proxy.yml` - Use if nginx is in Docker
- `docker-compose.host-nginx.yml` - Use if nginx is on host
- `check_nginx_setup.sh` - Helper to detect your setup

**URLs:**
- Health check: `https://ea1rfi.es/dx-cluster/health`
- SSE endpoint: `https://ea1rfi.es/dx-cluster/sse`
- Claude Desktop config: `https://ea1rfi.es/dx-cluster` (no trailing slash)

**Commands:**
```bash
# Start
docker-compose -f <compose-file> up -d

# Stop
docker-compose -f <compose-file> down

# Logs
docker logs -f dx-cluster-mcp-server

# Health check
curl https://ea1rfi.es/dx-cluster/health
```

## Need Help?

If you encounter issues:
1. Check the logs: `docker logs dx-cluster-mcp-server`
2. Verify health endpoint works: `curl https://ea1rfi.es/dx-cluster/health`
3. Review the full documentation: `docs/NGINX_INTEGRATION.md`
4. Check nginx error logs: `sudo tail -f /var/log/nginx/error.log`
