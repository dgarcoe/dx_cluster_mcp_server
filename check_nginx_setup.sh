#!/bin/bash
# Helper script to detect nginx setup and configure the MCP server accordingly

echo "=== DX Cluster MCP Server - nginx Integration Check ==="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

echo "✓ Docker is installed"
echo ""

# Check if nginx is running in Docker
NGINX_CONTAINERS=$(docker ps --filter "name=nginx" --format "{{.Names}}")

if [ -z "$NGINX_CONTAINERS" ]; then
    echo "⚠️  No nginx container found running in Docker."
    echo ""
    echo "OPTIONS:"
    echo ""
    echo "Option 1: nginx is running on host system (not in Docker)"
    echo "  → You need to create a Docker network and configure nginx to connect to it"
    echo "  → Run: docker network create mcp-network"
    echo "  → Then update docker-compose.nginx-proxy.yml to use 'mcp-network'"
    echo "  → Your nginx will access MCP server at: http://172.17.0.1:8000"
    echo ""
    echo "Option 2: nginx container exists but is stopped"
    echo "  → Start your nginx container first"
    echo ""
else
    echo "✓ Found nginx container(s): $NGINX_CONTAINERS"
    echo ""

    for container in $NGINX_CONTAINERS; do
        echo "Checking container: $container"
        NETWORKS=$(docker inspect $container --format '{{range $key, $value := .NetworkSettings.Networks}}{{$key}} {{end}}')
        echo "  Networks: $NETWORKS"
        echo ""
    done

    # Get the first network name (most likely the one to use)
    FIRST_NETWORK=$(docker inspect $NGINX_CONTAINERS --format '{{range $key, $value := .NetworkSettings.Networks}}{{$key}}{{end}}' | head -n1 | awk '{print $1}')

    if [ ! -z "$FIRST_NETWORK" ]; then
        echo "RECOMMENDATION:"
        echo "  Use network: $FIRST_NETWORK"
        echo ""
        echo "Update docker-compose.nginx-proxy.yml:"
        echo "  1. Line 29: Replace 'your_nginx_network' with '$FIRST_NETWORK'"
        echo "  2. Line 38: Replace 'your_nginx_network' with '$FIRST_NETWORK'"
        echo ""
        echo "Or run this command to update automatically:"
        echo "  sed -i 's/your_nginx_network/$FIRST_NETWORK/g' docker-compose.nginx-proxy.yml"
    fi
fi

echo ""
echo "=== Network List ==="
docker network ls
