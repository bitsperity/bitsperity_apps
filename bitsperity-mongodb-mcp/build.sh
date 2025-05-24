#!/bin/bash

# MongoDB MCP Server Build Script
set -e

echo "🔧 Building MongoDB MCP Server..."

# Set default environment variables
export APP_DATA_DIR="${PWD}/data"
export COMPOSE_PROJECT_NAME="bitsperity-mongodb-mcp"

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p "${APP_DATA_DIR}/data"
mkdir -p "${APP_DATA_DIR}/logs"

# Set permissions (if running as root, change to user)
if [[ $EUID -eq 0 ]]; then
    echo "⚠️  Running as root, setting up user permissions..."
    chown -R 1000:1000 "${APP_DATA_DIR}"
fi

# Build the unified Docker image
echo "🐳 Building MongoDB MCP Server Docker image..."
docker compose build --no-cache

# Verify the build
echo "✅ Build completed successfully!"
echo "📊 Docker images:"
docker images | grep bitsperity-mongodb-mcp || echo "No MongoDB MCP images found"

echo ""
echo "🚀 Ready to run!"
echo "🌐 Web mode: ./run.sh then http://localhost:8080"
echo "🔌 Cursor MCP: Uses same image with 'stdio' argument"
echo ""
echo "📋 One server, two modes:"
echo "  • Web: docker run ... bitsperity-mongodb-mcp-web:latest"
echo "  • MCP: docker run ... bitsperity-mongodb-mcp-web:latest stdio" 