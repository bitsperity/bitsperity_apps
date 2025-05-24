# MongoDB MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Umbrel App](https://img.shields.io/badge/umbrel-app-purple.svg)](https://umbrel.com/)

A modern **MongoDB Model Context Protocol (MCP) Server** for Umbrel that enables AI assistants to interact with MongoDB databases using natural language.

## Features

- 🤖 **Natural Language Queries** - Chat with your MongoDB databases
- 🔌 **Cursor IDE Integration** - Seamless setup with AI coding assistants  
- 📊 **Real-time Monitoring** - Web dashboard on port 8090
- 🌐 **Multi-Database Support** - Connect to local and remote MongoDB instances
- 🔒 **Secure Sessions** - No persistent credential storage
- 🚀 **10 Powerful Tools** - From basic queries to complex aggregations

## Quick Start

### 1. Install via Umbrel

1. Open Umbrel Dashboard
2. Go to App Store  
3. Search for "MongoDB MCP Server"
4. Click Install

The app will be available at `http://your-umbrel:8090`

### 2. Configure Cursor IDE

Add this to your Cursor MCP settings:

```json
{
  "mcpServers": {
    "mongodb-remote": {
      "command": "ssh",
      "args": [
        "umbrel@umbrel.local",
        "sudo", "docker", "exec", "-i", 
        "bitsperity-mongodb-mcp_mcp-server_1",
        "python", "src/simple_mcp_server.py"
      ]
    }
  }
}
```

### 3. Start Chatting

In Cursor, try:
- *"Connect to mongodb://umbrel:umbrel@umbrel.local:27017"*
- *"Show me all databases"*
- *"What collections are in my database?"*

## Available Tools

| Tool | Description |
|------|-------------|
| `establish_connection` | Connect to MongoDB instance |
| `list_databases` | Show available databases |
| `list_collections` | List collections in database |
| `query_collection` | Find documents with filters |
| `get_collection_schema` | Analyze document structure |
| `aggregate_collection` | Run aggregation pipelines |
| `get_sample_documents` | Get example documents |
| `list_active_connections` | Show current sessions |
| `test_connection` | Check connection health |
| `close_connection` | End database session |

## Example Connections

```bash
# Local Umbrel MongoDB
mongodb://umbrel:umbrel@umbrel.local:27017/

# External MongoDB
mongodb://192.168.1.100:27017/myapp

# MongoDB with authentication
mongodb://user:password@host:port/database
```

## SSH Setup (One-time)

```bash
# Add SSH key to Umbrel
ssh-copy-id umbrel@umbrel.local

# Add Docker permission
ssh umbrel@umbrel.local
echo 'umbrel ALL=(ALL) NOPASSWD: /usr/bin/docker' | sudo tee /etc/sudoers.d/umbrel-docker
sudo chmod 440 /etc/sudoers.d/umbrel-docker
```

## Architecture

```
┌─────────────────┐    SSH    ┌─────────────────┐
│   Cursor IDE    │ ────────► │   Umbrel Host   │
└─────────────────┘           └─────────────────┘
                                       │
                               Docker exec -i
                                       ▼
                              ┌─────────────────┐
                              │   MCP Server    │
                              │   Container     │
                              └─────────────────┘
                                       │
                                  HTTP POST
                                       ▼
                              ┌─────────────────┐
                              │  Web Interface  │
                              │  Port 8090      │
                              └─────────────────┘
```

## Troubleshooting

**MCP tools not available in Cursor:**
- Restart Cursor IDE
- Verify SSH connection: `ssh umbrel@umbrel.local`
- Check container status: `sudo docker ps | grep mongodb-mcp`

**Connection refused:**
- For Umbrel MongoDB: `mongodb://umbrel:umbrel@umbrel.local:27017/`
- For external: Check network connectivity and MongoDB port

**Web interface not accessible:**
- Ensure app is running: Check Umbrel dashboard
- Verify port 8090 is not blocked

## Development

```bash
# Clone repository
git clone https://github.com/bitsperity/bitsperity_apps
cd bitsperity_apps/bitsperity-mongodb-mcp

# Run locally
docker-compose up -d

# View logs
docker-compose logs -f mcp-server
```

## Security

- Connection strings are never persisted
- Sessions expire automatically (1 hour default)
- SSH encryption for all communication
- Isolated Docker containers

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- [GitHub Issues](https://github.com/bitsperity/bitsperity_apps/issues)
- [Umbrel Community](https://community.umbrel.com)

---

**Made with ❤️ for the Umbrel Community** 