#!/bin/bash

# MongoDB MCP Server Development Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Starting MongoDB MCP Server in Development Mode...${NC}"

# Set environment variables for development
export APP_ENV=development
export MCP_HOST=127.0.0.1
export MCP_PORT=3001
export WEB_HOST=127.0.0.1
export WEB_PORT=8080
export SESSION_TTL=3600
export MAX_CONNECTIONS=10
export CONNECTION_TIMEOUT=300
export LOG_LEVEL=DEBUG
export DATA_DIR="./data"

# Create necessary directories
echo -e "${YELLOW}📁 Creating development directories...${NC}"
mkdir -p ./data/data
mkdir -p ./data/logs

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}🐍 Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}🔌 Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
pip install -r src/requirements.txt

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Stopping development server...${NC}"
    # Kill any background processes
    jobs -p | xargs -r kill
    echo -e "${GREEN}✅ Development server stopped${NC}"
}

# Setup signal handlers
trap cleanup EXIT INT TERM

# Start the server
echo -e "${GREEN}🚀 Starting MongoDB MCP Server...${NC}"
echo -e "${BLUE}🌐 Web interface: http://localhost:8080${NC}"
echo -e "${BLUE}🔌 MCP server: http://localhost:3001${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

cd src
python server.py 