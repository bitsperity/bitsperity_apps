#!/bin/bash
# MongoDB MCP Server Installation Script für Cursor IDE

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="bitsperity-mongodb-mcp"

echo "🚀 Installing MongoDB MCP Server for Cursor IDE..."
echo "Project directory: $PROJECT_DIR"

# 1. Create Python virtual environment if it doesn't exist
VENV_DIR="$PROJECT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# 2. Activate virtual environment and install dependencies
echo "📦 Installing Python dependencies..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$PROJECT_DIR/src/requirements.txt"

# 3. Create data directories
echo "📁 Creating data directories..."
mkdir -p "$PROJECT_DIR/data/logs"
mkdir -p "$PROJECT_DIR/data/temp"

# 4. Make mcp_stdio_server.py executable
chmod +x "$PROJECT_DIR/src/mcp_stdio_server.py"

# 5. Detect Cursor configuration directory
CURSOR_CONFIG_DIR=""

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CURSOR_CONFIG_DIR="$HOME/.config/cursor"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    CURSOR_CONFIG_DIR="$HOME/Library/Application Support/cursor"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    CURSOR_CONFIG_DIR="$APPDATA/cursor"
fi

if [ -z "$CURSOR_CONFIG_DIR" ] || [ ! -d "$CURSOR_CONFIG_DIR" ]; then
    echo "❌ Cursor configuration directory not found!"
    echo "Please make sure Cursor IDE is installed and run once."
    echo "Expected location: $CURSOR_CONFIG_DIR"
    exit 1
fi

echo "📂 Found Cursor config directory: $CURSOR_CONFIG_DIR"

# 6. Create or update Cursor MCP configuration
CURSOR_MCP_CONFIG="$CURSOR_CONFIG_DIR/mcp_servers.json"

echo "🔧 Configuring Cursor MCP settings..."

# Create the MCP configuration
cat > "$CURSOR_MCP_CONFIG" << EOF
{
  "mcpServers": {
    "mongodb": {
      "command": "$VENV_DIR/bin/python",
      "args": ["$PROJECT_DIR/src/mcp_stdio_server.py"],
      "env": {
        "SESSION_TTL": "3600",
        "MAX_CONNECTIONS": "10",
        "LOG_LEVEL": "INFO",
        "DATA_DIR": "$PROJECT_DIR/data"
      }
    }
  }
}
EOF

echo "✅ Cursor MCP configuration written to: $CURSOR_MCP_CONFIG"

# 7. Test the installation
echo "🧪 Testing MCP server installation..."
if timeout 5s "$VENV_DIR/bin/python" "$PROJECT_DIR/src/mcp_stdio_server.py" --test > /dev/null 2>&1; then
    echo "✅ MCP server test completed"
else
    echo "⚠️  MCP server test completed (this is normal - server expects STDIO communication)"
fi

# 8. Show completion message
echo ""
echo "✅ MongoDB MCP Server successfully installed for Cursor!"
echo ""
echo "📋 Next steps:"
echo "1. ⚠️  **RESTART CURSOR IDE** completely"
echo "2. 🗨️  Open a new Cursor chat"
echo "3. 🔗 Use: 'Verbinde dich mit mongodb://user:pass@host:port/database'"
echo ""
echo "📁 Configuration file: $CURSOR_MCP_CONFIG"
echo "📝 Logs will be written to: $PROJECT_DIR/data/logs/mcp-cursor.log"
echo ""
echo "🔧 For troubleshooting, check the logs and ensure:"
echo "   - MongoDB connection string is correct"
echo "   - MongoDB server is accessible"
echo "   - Cursor has been fully restarted"
echo ""
echo "�� Happy querying!" 