# Nginx Integration Guide

## Running Behind nginx with Let's Encrypt

This guide shows how to integrate the DX Cluster MCP Server with your existing nginx setup that already has Let's Encrypt certificates.

## Prerequisites

- Existing nginx with Let's Encrypt certificates
- nginx running in Docker (or accessible to the MCP server container)
- Domain name (e.g., ea1rfi.es)

## Architecture

```
Internet → nginx (HTTPS:443) → MCP Server (HTTP:8000)
         ↓
    Let's Encrypt
    /etc/letsencrypt/
```

nginx handles:
- HTTPS/TLS termination
- Let's Encrypt certificates
- Request routing

MCP Server handles:
- HTTP only (no TLS needed)
- MCP protocol
- DX cluster connection

## Step 1: Update nginx Configuration

Add this location block to your nginx server configuration (port 443 section):

```nginx
# DX Cluster MCP Server
location /dx-cluster/ {
    proxy_pass http://dx-cluster-mcp-server:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Required for SSE (Server-Sent Events)
    proxy_http_version 1.1;
    proxy_set_header Connection '';
    proxy_buffering off;
    proxy_cache off;
    chunked_transfer_encoding off;

    # SSE timeout - keep connection alive
    proxy_read_timeout 86400s;
}
```

### Alternative: Run on Subdomain

If you prefer a subdomain instead of a path:

```nginx
server {
    listen 443 ssl;
    server_name dx-cluster.ea1rfi.es;

    ssl_certificate /etc/letsencrypt/live/ea1rfi.es/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ea1rfi.es/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://dx-cluster-mcp-server:8000;
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
}
```

Don't forget to:
1. Add DNS A record: `dx-cluster.ea1rfi.es → your-server-ip`
2. Get certificate: `certbot certonly --webroot -w /var/www/certbot -d dx-cluster.ea1rfi.es`

## Step 2: Configure Docker Compose

### Update docker-compose.nginx-proxy.yml

1. Change the network name to match your nginx network:

```bash
# Find your nginx network name
docker network ls | grep nginx
```

2. Update `docker-compose.nginx-proxy.yml`:

```yaml
networks:
  your_nginx_network:
    external: true
    name: your_actual_nginx_network_name  # e.g., nginx_default
```

### Create .env file

```bash
cp .env.example .env
# Edit with your settings:
nano .env
```

Set your callsign and cluster:
```bash
DX_CLUSTER_CALLSIGN=EA1RFI  # Your callsign
IARU_REGION=1  # Europe = Region 1
```

## Step 3: Start the MCP Server

```bash
# Start the MCP server
docker-compose -f docker-compose.nginx-proxy.yml up -d

# Check logs
docker-compose -f docker-compose.nginx-proxy.yml logs -f
```

## Step 4: Reload nginx

```bash
# Test nginx configuration
docker exec nginx nginx -t

# Reload nginx
docker exec nginx nginx -s reload
```

Or if nginx is not in Docker:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Step 5: Verify It's Working

### Test health endpoint:

**Path-based:**
```bash
curl https://ea1rfi.es/dx-cluster/health
```

**Subdomain-based:**
```bash
curl https://dx-cluster.ea1rfi.es/health
```

Expected response:
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

### Test SSE endpoint:

```bash
curl -N https://ea1rfi.es/dx-cluster/sse
```

You should see the SSE connection establish (it will wait for events).

## Step 6: Configure Claude Desktop

Edit your Claude Desktop config:

**MacOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%/Claude/claude_desktop_config.json`

### Path-based URL:

```json
{
  "mcpServers": {
    "dx-cluster": {
      "url": "https://ea1rfi.es/dx-cluster"
    }
  }
}
```

### Subdomain-based URL:

```json
{
  "mcpServers": {
    "dx-cluster": {
      "url": "https://dx-cluster.ea1rfi.es"
    }
  }
}
```

**Note:** No trailing slash!

Restart Claude Desktop and the MCP server should appear in the available tools.

## Troubleshooting

### 502 Bad Gateway

**Problem:** nginx can't reach the MCP server

**Solutions:**
1. Check container is running: `docker ps | grep dx-cluster`
2. Check network: `docker network inspect your_nginx_network`
3. Verify container is on the right network
4. Check container logs: `docker logs dx-cluster-mcp-server`

### 504 Gateway Timeout

**Problem:** SSE connection timing out

**Solution:** Ensure these nginx directives are set:
```nginx
proxy_read_timeout 86400s;
proxy_buffering off;
```

### Connection not secure / Certificate error

**Problem:** HTTPS not working

**Solutions:**
1. Check certificate path in nginx config
2. Verify certificate is valid: `certbot certificates`
3. Check nginx error log: `docker logs nginx` or `tail -f /var/log/nginx/error.log`

### MCP server not connecting to DX cluster

**Problem:** `"dx_cluster": {"connected": false}`

**Solutions:**
1. Check environment variables: `docker exec dx-cluster-mcp-server env | grep DX_`
2. Check logs: `docker logs dx-cluster-mcp-server`
3. Verify cluster is accessible: `telnet dxc.nc7j.com 7300`
4. Try alternative cluster in .env file

### Claude Desktop can't connect

**Problem:** MCP server not appearing in Claude Desktop

**Solutions:**
1. Verify URL in config (no trailing slash)
2. Test URL in browser: `https://ea1rfi.es/dx-cluster/health`
3. Check Claude Desktop logs
4. Restart Claude Desktop after config changes
5. Verify nginx is proxying correctly: `curl -v https://ea1rfi.es/dx-cluster/health`

## Network Configuration Examples

### Example 1: Shared network with nginx

```yaml
# In your nginx docker-compose.yml
networks:
  web:
    name: nginx_default

# In docker-compose.nginx-proxy.yml
networks:
  your_nginx_network:
    external: true
    name: nginx_default
```

### Example 2: Using docker-compose project name

If your nginx is in a project called "infrastructure":

```yaml
networks:
  your_nginx_network:
    external: true
    name: infrastructure_default
```

### Example 3: Custom network name

```yaml
networks:
  your_nginx_network:
    external: true
    name: my_custom_network
```

## Certificate Renewal

Since nginx handles certificates, your existing certbot renewal process will work:

```bash
# Manual renewal
certbot renew

# Reload nginx after renewal
docker exec nginx nginx -s reload
# or
sudo systemctl reload nginx
```

The MCP server doesn't need to be restarted when certificates are renewed.

## Security Considerations

### 1. Firewall Rules

Only nginx needs to be accessible from internet:
- Port 80 (HTTP) - for Let's Encrypt validation
- Port 443 (HTTPS) - for HTTPS traffic

MCP server port 8000 should NOT be exposed to the internet.

### 2. nginx Security Headers

Add to your nginx config:

```nginx
location /dx-cluster/ {
    # ... existing proxy settings ...

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
}
```

### 3. Rate Limiting

Protect against abuse:

```nginx
# In http block
limit_req_zone $binary_remote_addr zone=mcp_limit:10m rate=10r/s;

# In location block
location /dx-cluster/ {
    limit_req zone=mcp_limit burst=20;
    # ... rest of config ...
}
```

## Monitoring

### Health Check

Add to your monitoring:

```bash
#!/bin/bash
# health_check.sh
STATUS=$(curl -s https://ea1rfi.es/dx-cluster/health | jq -r '.status')
if [ "$STATUS" != "healthy" ]; then
    echo "MCP Server unhealthy!"
    # Send alert
fi
```

### Log Monitoring

Monitor nginx logs for MCP server access:

```bash
tail -f /var/log/nginx/access.log | grep dx-cluster
```

Monitor MCP server logs:

```bash
docker logs -f dx-cluster-mcp-server
```

## Complete Example

Here's a complete working example for ea1rfi.es:

### nginx config: `/etc/nginx/sites-available/ea1rfi.es`

```nginx
server {
    listen 80;
    server_name ea1rfi.es www.ea1rfi.es;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name ea1rfi.es www.ea1rfi.es;

    ssl_certificate /etc/letsencrypt/live/ea1rfi.es/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ea1rfi.es/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Existing app
    location / {
        proxy_pass http://app:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
    }

    # DX Cluster MCP Server
    location /dx-cluster/ {
        proxy_pass http://dx-cluster-mcp-server:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding off;
        proxy_read_timeout 86400s;
    }
}

map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}
```

### docker-compose.nginx-proxy.yml

```yaml
version: '3.8'

services:
  dx-cluster-mcp-server:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: dx-cluster-mcp-server
    restart: unless-stopped
    expose:
      - "8000"
    environment:
      - MCP_TRANSPORT=sse
      - MCP_SERVER_HOST=0.0.0.0
      - MCP_SERVER_PORT=8000
      - DX_CLUSTER_HOST=dxc.nc7j.com
      - DX_CLUSTER_PORT=7300
      - DX_CLUSTER_CALLSIGN=EA1RFI
      - IARU_REGION=1
    networks:
      - nginx_default

networks:
  nginx_default:
    external: true
```

### Claude Desktop config

```json
{
  "mcpServers": {
    "dx-cluster": {
      "url": "https://ea1rfi.es/dx-cluster"
    }
  }
}
```

## Advantages of This Setup

✅ **Let's Encrypt:** Free, automatic certificate renewal
✅ **nginx handles HTTPS:** MCP server doesn't need TLS configuration
✅ **Single domain:** Use existing domain with a path
✅ **Easy to manage:** Standard nginx reverse proxy pattern
✅ **Secure:** MCP server not exposed directly to internet
✅ **Scalable:** Can add more services to same domain easily

## Next Steps

1. Add monitoring/alerting
2. Set up log rotation
3. Configure backups
4. Add rate limiting
5. Set up health check automation
6. Document your specific callsign/region settings

73 and good DX! 📻
