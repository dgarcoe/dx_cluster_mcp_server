.PHONY: help build up down logs shell test clean install dev

help:
	@echo "DX Cluster MCP Server - Available commands:"
	@echo ""
	@echo "  make build      - Build Docker image"
	@echo "  make up         - Start services with docker-compose"
	@echo "  make down       - Stop services"
	@echo "  make logs       - Show container logs"
	@echo "  make shell      - Open shell in container"
	@echo "  make test       - Run tests"
	@echo "  make clean      - Clean up Docker resources"
	@echo "  make install    - Install locally for development"
	@echo "  make dev        - Run in development mode"
	@echo ""

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f dx-cluster-mcp-server

shell:
	docker-compose exec dx-cluster-mcp-server /bin/bash

test:
	pytest tests/ -v

clean:
	docker-compose down -v
	docker system prune -f

install:
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt && pip install -e .

dev:
	python -m dx_cluster_mcp_server.server
