#!/bin/bash
# MongoDB MCP Server - Docker Starter

set -e

echo "🚀 Starting MongoDB MCP Server (Docker-only)..."

# Build the image
echo "📦 Building MCP Server image..."
docker compose build mcp-server

# Start the MCP server
echo "▶️  Starting MCP Server..."
docker compose up -d mcp-server

echo ""
echo "✅ MongoDB MCP Server is running!"
echo ""
echo "📋 Usage:"
echo "   🔗 Connect from any MCP client:"
echo "   docker exec -i $(docker compose ps -q mcp-server) python src/mcp_stdio_server.py"
echo ""
echo "   📊 Optional: Start web interface:"
echo "   docker compose --profile web up -d"
echo "   🌐 Web UI: http://localhost:8080"
echo ""
echo "📝 Logs:"
echo "   docker compose logs -f mcp-server"
echo ""
echo "🛑 Stop:"
echo "   docker compose down" 