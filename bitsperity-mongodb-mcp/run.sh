#!/bin/bash

# MongoDB MCP Server Run Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting MongoDB MCP Server (Web Mode)...${NC}"

# Set environment variables
export APP_DATA_DIR="${PWD}/data"
export COMPOSE_PROJECT_NAME="bitsperity-mongodb-mcp"

# Ensure data directories exist
mkdir -p "${APP_DATA_DIR}/data"
mkdir -p "${APP_DATA_DIR}/logs"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Stopping MongoDB MCP Server...${NC}"
    docker compose down
    echo -e "${GREEN}✅ Server stopped${NC}"
}

# Setup signal handlers
trap cleanup EXIT INT TERM

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Start the web server
echo -e "${BLUE}🐳 Starting MongoDB MCP Server in Web Mode...${NC}"
echo -e "${BLUE}🌐 Web interface will be available at: http://localhost:8080${NC}"
echo -e "${BLUE}🔌 Cursor uses same image with 'stdio' mode${NC}"
echo ""
docker compose up --remove-orphans

# This line will be reached if docker-compose exits normally
echo -e "${GREEN}✅ MongoDB MCP Server has stopped${NC}" 