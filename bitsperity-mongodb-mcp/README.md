# MongoDB MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

A modern **MongoDB Model Context Protocol (MCP) Server** that enables seamless integration between AI assistants (like Cursor IDE) and MongoDB databases. Chat with your database using natural language!

## 🎯 What is this?

This MCP server allows AI assistants to interact with MongoDB databases through a standardized protocol. Instead of writing complex queries, you can simply ask:

- *"Show me all users from Germany"*
- *"What's the schema of my products collection?"*
- *"Find orders from the last 30 days"*
- *"Create an aggregation for top customers by revenue"*

## ✨ Features

- 🤖 **Natural Language Database Queries** - Chat with your MongoDB
- 🔌 **Cursor IDE Integration** - Seamless setup with popular AI coding assistant
- 🔒 **Secure Session Management** - No persistent credential storage
- 📊 **Automatic Schema Analysis** - Understand your data structure instantly
- 🚀 **10 Powerful Tools** - From basic queries to complex aggregations
- 🐳 **Docker Ready** - Easy deployment and development
- 🔄 **Multi-Database Support** - Handle multiple connections simultaneously

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose** (recommended)
- **Cursor IDE** (for AI integration)

### Installation

#### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd mongodb-mcp-server

# Start the MCP server
docker-compose up -d

# Configure Cursor IDE (see below)
```

#### Option 2: Local Development

```bash
# Clone and setup
git clone <your-repo-url>
cd mongodb-mcp-server

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r src/requirements.txt

# Run the server
python src/simple_mcp_server.py
```

### Cursor IDE Setup

1. **Open Cursor IDE Settings** (`Cmd/Ctrl + ,`)
2. **Search for "MCP"** in settings
3. **Add this configuration**:

```json
{
  "mcpServers": {
    "mongodb": {
      "command": "docker",
      "args": [
        "exec", "-i", 
        "mongodb-mcp-server-mcp-server-1",
        "python", "src/simple_mcp_server.py"
      ]
    }
  }
}
```

4. **Restart Cursor IDE**
5. **Start a new chat** and try: *"Connect to mongodb://localhost:27017"*

## 🛠️ Available Tools

| Tool | Description | Example Usage |
|------|-------------|---------------|
| `establish_connection` | Connect to MongoDB | *"Connect to mongodb://user:pass@host:port/db"* |
| `list_databases` | Show all databases | *"Show me all databases"* |
| `list_collections` | Show collections in a database | *"What collections are in myapp?"* |
| `get_sample_documents` | Get example documents | *"Show me some examples from users"* |
| `get_collection_schema` | Analyze document structure | *"What's the schema of products?"* |
| `query_collection` | Find documents with filters | *"Find all active users"* |
| `aggregate_collection` | Run aggregation pipelines | *"Group orders by month"* |
| `list_active_connections` | Show current sessions | *"What connections are active?"* |
| `test_connection` | Check connection health | *"Test my database connection"* |
| `close_connection` | End a database session | *"Close the connection"* |

## 💬 Usage Examples

### Basic Exploration

```
You: "Connect to mongodb://localhost:27017/ecommerce"
Assistant: ✅ Connected successfully! Session ID: abc123

You: "What databases are available?"
Assistant: 📊 Found 3 databases:
- ecommerce (15.2 MB, 5 collections)
- analytics (8.1 MB, 3 collections)  
- logs (125.8 MB, 2 collections)

You: "Show me the collections in ecommerce"
Assistant: 📋 Collections in ecommerce:
- users (12,450 documents)
- products (8,932 documents)
- orders (45,123 documents)
- reviews (23,891 documents)
- categories (156 documents)
```

### Data Analysis

```
You: "Analyze the schema of the users collection"
Assistant: 🔍 Schema Analysis for users:
- _id: ObjectId (100% present)
- email: string (100% present, appears unique)
- name: string (98% present)
- status: string (95% present, values: active, inactive, pending)
- createdAt: date (100% present)
- lastLogin: date (78% present)

You: "Find all active users from the last month"
Assistant: 🔎 Query: {status: "active", createdAt: {$gte: "2024-04-24"}}
Found 1,247 active users created in the last month.

You: "Group orders by month and show revenue"
Assistant: 📊 Revenue by month:
- 2024-05: $45,230
- 2024-04: $38,910
- 2024-03: $52,100
```

## 🏗️ Project Structure

```
mongodb-mcp-server/
├── src/
│   ├── simple_mcp_server.py    # Main MCP server (10 tools)
│   ├── mcp_stdio_server.py     # Alternative server implementation
│   ├── connection_manager.py   # Database connection handling
│   ├── mongodb_tools.py        # Core MongoDB operations
│   ├── schema_analyzer.py      # Document schema analysis
│   └── requirements.txt        # Python dependencies
├── docker-compose.yml          # Docker configuration
├── Dockerfile                  # Container definition
├── start-mcp.sh               # Server startup script
└── README.md                  # This file
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SESSION_TTL` | 3600 | Session timeout in seconds |
| `MAX_CONNECTIONS` | 10 | Maximum concurrent connections |
| `CONNECTION_TIMEOUT` | 300 | Connection timeout in seconds |
| `LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `DATA_DIR` | /app/data | Directory for logs and temporary data |

### Docker Compose

```yaml
version: '3.8'
services:
  mcp-server:
    build: .
    restart: unless-stopped
    network_mode: host  # Required for localhost MongoDB access
    environment:
      SESSION_TTL: 3600
      MAX_CONNECTIONS: 10
      LOG_LEVEL: INFO
```

## 🔒 Security

- **No Persistent Credentials** - Connection strings are never stored
- **Session-Based Authentication** - Connections expire automatically
- **Encrypted Memory Storage** - Sensitive data encrypted in memory
- **Isolated Sessions** - No cross-session data leaks
- **Connection Limits** - Configurable maximum connections

## 🧪 Development

### Running Tests

```bash
# Start the development server
docker-compose up -d

# Test all tools
python test_all_tools.py

# View logs
docker-compose logs -f mcp-server
```

### Local Development

```bash
# Run without Docker
source venv/bin/activate
python src/simple_mcp_server.py

# Monitor logs
tail -f data/logs/simple-mcp.log
```

## 🔍 Troubleshooting

### Cursor IDE Issues

**Problem:** "No MCP tools available"
```bash
# Solution:
1. Restart Cursor IDE completely
2. Check MCP configuration in settings
3. Verify Docker container is running: docker ps
4. Check container logs: docker-compose logs mcp-server
```

**Problem:** "Tool call failed"
```bash
# Solution:
1. Verify MongoDB is accessible: docker ps | grep mongo
2. Test connection manually: docker exec -it <container> mongo
3. Check network mode in docker-compose.yml
```

### MongoDB Connection Issues

**Problem:** "Connection refused"
```bash
# For Docker MongoDB:
docker run -d -p 27017:27017 --name mongodb mongo:latest

# For local MongoDB:
brew services start mongodb-community  # macOS
sudo systemctl start mongod           # Linux
```

**Problem:** "Authentication failed"
```bash
# Use correct connection string format:
mongodb://username:password@host:port/database
mongodb://localhost:27017  # For no auth
```

### Docker Issues

**Problem:** "Container not starting"
```bash
# Rebuild and restart:
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check logs:
docker-compose logs mcp-server
```

## 📚 API Reference

### Connection Management
- `establish_connection(connection_string)` - Create database connection
- `test_connection(session_id)` - Verify connection health
- `close_connection(session_id)` - End session
- `list_active_connections()` - Show all active sessions

### Database Operations
- `list_databases(session_id)` - Get all databases
- `list_collections(session_id, database_name)` - Get collections

### Data Exploration
- `get_sample_documents(session_id, database, collection, limit=5)` - Sample docs
- `get_collection_schema(session_id, database, collection)` - Schema analysis
- `query_collection(session_id, database, collection, query, limit=10)` - Find documents
- `aggregate_collection(session_id, database, collection, pipeline)` - Aggregations

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md).

### Development Setup

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Add tests** if applicable
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Code Style

- Follow PEP 8 for Python code
- Use type hints where possible
- Add docstrings for all functions
- Keep functions focused and small

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io) - For the amazing MCP specification
- [Cursor IDE](https://cursor.sh) - For excellent AI coding assistant integration
- [MongoDB](https://mongodb.com) - For the powerful database platform

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/mongodb-mcp-server/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/mongodb-mcp-server/discussions)
- **Documentation**: [Wiki](https://github.com/yourusername/mongodb-mcp-server/wiki)

---

**Made with ❤️ for the AI and Database community** 