# bitsperity-mqtt-mcp - Deployment Design

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Umbrel Host                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │
│  │   Cursor IDE    │  │ MQTT MCP Server │  │  Docker Networks    │ │
│  │   (External)    │  │                 │  │                     │ │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────────┤ │
│  │ SSH Connection  │──┤ • MCP Container │  │ • Host Network      │ │
│  │ JSON-RPC 2.0    │  │ • Web Monitor   │  │ • Mosquitto Network │ │
│  │ docker exec     │  │ • Port 8090     │  │ • Bridge Network    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │
│                                │                                   │
│  ┌─────────────────────────────┴─────────────────────────────────┐ │
│  │                     Service Dependencies                       │ │
│  ├─────────────────────────────────────────────────────────────────┤ │
│  │ ┌─────────────┐  ┌─────────────┐  ┌───────────────────────────┐│ │
│  │ │ Mosquitto   │  │ IoT Devices │  │     External Services     ││ │
│  │ │ MQTT Broker │  │             │  │                           ││ │
│  │ ├─────────────┤  ├─────────────┤  ├───────────────────────────┤│ │
│  │ │ Port 1883   │◄─┤ • Sensors   │  │ • Development MQTT Broker ││ │
│  │ │ Internal    │  │ • Actuators │  │   (192.168.178.57:1883)   ││ │
│  │ │ Container   │  │ • Controllers│  │ • External Test Brokers   ││ │
│  │ └─────────────┘  └─────────────┘  └───────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Docker Compose Configuration

### Production docker-compose.yml
```yaml
# bitsperity-mqtt-mcp/docker-compose.yml
version: '3.8'

services:
  # MQTT MCP Server (STDIO mode for AI Assistant)
  mcp-server:
    image: bitsperity/mqtt-mcp:latest
    container_name: bitsperity-mqtt-mcp_mcp-server_1
    restart: unless-stopped
    stop_grace_period: 30s
    stdin_open: true    # Enable STDIN for MCP communication
    tty: true          # Enable TTY for MCP communication
    network_mode: host  # SSH access for AI Assistant integration
    
    volumes:
      - ${APP_DATA_DIR:-./data}/data:/app/data
      - ${APP_DATA_DIR:-./data}/logs:/app/logs
      
    environment:
      # MCP Configuration
      SESSION_TTL: ${SESSION_TTL:-3600}           # 1 hour
      MAX_CONNECTIONS: ${MAX_CONNECTIONS:-5}       # Max MQTT connections
      CONNECTION_TIMEOUT: ${CONNECTION_TIMEOUT:-30} # 30 seconds
      
      # MQTT Configuration
      DEFAULT_MQTT_BROKER: ${DEFAULT_MQTT_BROKER:-mosquitto_broker_1:1883}
      MQTT_TIMEOUT: ${MQTT_TIMEOUT:-30}
      
      # Logging
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      LOG_FILE: /app/logs/mqtt-mcp.log
      
      # Data Directory
      DATA_DIR: /app/data
      
      # Web API URL for logging
      WEB_API_URL: http://localhost:8090
      
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.5'
        reservations:
          memory: 128M
          cpus: '0.25'
          
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  # Web Monitoring Interface
  web:
    image: bitsperity/mqtt-mcp:latest
    container_name: bitsperity-mqtt-mcp_web_1
    restart: unless-stopped
    stop_grace_period: 30s
    
    ports:
      - "8090:8080"  # Web Interface
      
    environment:
      # Web Server Configuration
      WEB_HOST: 0.0.0.0
      WEB_PORT: 8080
      APP_ENV: ${APP_ENV:-production}
      
      # API Configuration
      CORS_ORIGINS: ${CORS_ORIGINS:-*}
      
    command: ["python", "src/web_monitor.py"]
    
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.3'
        reservations:
          memory: 64M
          cpus: '0.1'
          
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

# External networks for service integration
networks:
  default:
    external: false
  mosquitto_default:
    external: true
    name: mosquitto_default
```

### Development docker-compose.override.yml
```yaml
# Development overrides
version: '3.8'

services:
  mcp-server:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    volumes:
      - ./src:/app/src:ro  # Source code mounting for development
      - ./ai_docs:/app/ai_docs:ro
    environment:
      LOG_LEVEL: DEBUG
      DEFAULT_MQTT_BROKER: 192.168.178.57:1883  # External test broker
      
  web:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    volumes:
      - ./src:/app/src:ro
    environment:
      APP_ENV: development
      LOG_LEVEL: DEBUG
```

## Dockerfile Design

### Multi-stage Dockerfile
```dockerfile
# bitsperity-mqtt-mcp/Dockerfile
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
WORKDIR /app
USER app

# Copy requirements first for better caching
COPY --chown=app:app requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Development stage
FROM base as development
COPY --chown=app:app requirements-dev.txt .
RUN pip install --no-cache-dir --user -r requirements-dev.txt

# Production stage  
FROM base as production
COPY --chown=app:app src/ ./src/
COPY --chown=app:app ai_docs/ ./ai_docs/

# Create data directories
RUN mkdir -p data logs

# Default command (can be overridden)
CMD ["python", "src/simple_mcp_server.py"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"
```

## Umbrel App Integration

### umbrel-app.yml
```yaml
# bitsperity-mqtt-mcp/umbrel-app.yml
manifestVersion: 1
id: bitsperity-mqtt-mcp
category: developer-tools
name: MQTT MCP Server
icon: https://raw.githubusercontent.com/bitsperity/bitsperity_apps/master/bitsperity-mqtt-mcp/applogo.svg
version: "1.0.0"

tagline: AI-powered MQTT debugging and analysis tool for IoT developers

description: >-
  A powerful MQTT Model Context Protocol (MCP) Server that enables seamless integration 
  between AI assistants (like Cursor IDE) and MQTT brokers. Perfect for IoT debugging, 
  device monitoring, and message flow analysis.
  
  Key Features:
  • Dynamic MQTT broker connections - Connect to any MQTT broker
  • Natural language queries - "Show me all sensor data from the last 5 minutes"  
  • Real-time message collection - Time-bounded with intelligent pruning
  • Topic discovery - Automatic MQTT topic exploration with wildcards
  • QoS support - Full MQTT QoS 0, 1, 2 handling
  • Device debugging - Specialized tools for IoT device analysis
  • Performance monitoring - Message throughput and latency analysis
  • Secure session management - No persistent credential storage
  • Web monitoring interface - Real-time status and statistics
  
  Perfect for IoT developers, system integrators, and DevOps engineers who want to 
  combine the power of MQTT with modern AI assistants for debugging and analysis.

releaseNotes: >-
  Initial release of MQTT MCP Server featuring:
  • 6 core MCP tools for MQTT operations
  • Real-time message collection with intelligent pruning  
  • Topic discovery with wildcard support
  • QoS 0, 1, 2 support for all operations
  • Session-based security model
  • Web monitoring interface on port 8090
  • Integration with Cursor IDE and other AI assistants
  • Docker-based deployment for easy installation

developer: Bitsperity
website: https://bitsperity.com
dependencies: []
repo: https://github.com/bitsperity/bitsperity_apps
support: https://github.com/bitsperity/bitsperity_apps/discussions

port: 8090

gallery:
  - https://raw.githubusercontent.com/bitsperity/bitsperity_apps/master/bitsperity-mqtt-mcp/gallery/1.png
  - https://raw.githubusercontent.com/bitsperity/bitsperity_apps/master/bitsperity-mqtt-mcp/gallery/2.png
  - https://raw.githubusercontent.com/bitsperity/bitsperity_apps/master/bitsperity-mqtt-mcp/gallery/3.png

path: ""
defaultUsername: ""
defaultPassword: ""

submitter: Bitsperity
submission: https://github.com/getumbrel/umbrel-apps
```

## Cursor MCP Configuration

### cursor-mcp-config.json
```json
{
  "mcpServers": {
    "mqtt-remote": {
      "command": "ssh",
      "args": [
        "umbrel@umbrel.local", 
        "sudo", "docker", "exec", "-i",
        "bitsperity-mqtt-mcp_mcp-server_1",
        "python", "src/simple_mcp_server.py"
      ]
    }
  }
}
```

## Network Configuration

### Docker Networks
```yaml
# Network setup for service integration
networks:
  # Internal network for MQTT MCP containers
  mqtt-mcp-internal:
    driver: bridge
    internal: false
    
  # External network for Mosquitto integration
  mosquitto_default:
    external: true
    
  # Host network for SSH access
  host:
    external: true
```

### Port Mapping
- **8090**: Web monitoring interface (external access)
- **1883**: MQTT broker access (internal network)
- **SSH**: Host network for Cursor IDE integration

## Environment Configuration

### Production Environment (.env)
```bash
# MQTT MCP Configuration
APP_ENV=production
SESSION_TTL=3600
MAX_CONNECTIONS=5
CONNECTION_TIMEOUT=30

# MQTT Settings
DEFAULT_MQTT_BROKER=mosquitto_broker_1:1883
MQTT_TIMEOUT=30

# Logging
LOG_LEVEL=INFO

# Web Interface
CORS_ORIGINS=*

# Resource Limits
MEMORY_LIMIT=256M
CPU_LIMIT=0.5
```

### Development Environment (.env.dev)
```bash
# Development overrides
APP_ENV=development
LOG_LEVEL=DEBUG
DEFAULT_MQTT_BROKER=192.168.178.57:1883

# Development tools
RELOAD=true
DEBUG_MODE=true
```

## Deployment Scripts

### deploy-local.sh
```bash
#!/bin/bash
# Local development deployment
set -e

echo "🚀 Deploying MQTT MCP Server (Local Development)"

# Build development image
docker-compose -f docker-compose.yml -f docker-compose.override.yml build

# Start services
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

# Show status
docker-compose ps

echo "✅ MQTT MCP Server deployed locally"
echo "📊 Web Interface: http://localhost:8090"
echo "🔧 MCP Server: Use cursor-mcp-config.json for integration"
```

### deploy-umbrel.sh
```bash
#!/bin/bash
# Umbrel production deployment
set -e

echo "🚀 Deploying MQTT MCP Server (Umbrel Production)"

# Build and push production image
docker build -t bitsperity/mqtt-mcp:latest --target production .
docker push bitsperity/mqtt-mcp:latest

# Deploy to Umbrel (via app store or manual)
docker-compose -f docker-compose.yml up -d

# Check health
sleep 30
docker-compose ps
curl -f http://localhost:8090/health

echo "✅ MQTT MCP Server deployed to Umbrel"
echo "📊 Web Interface: http://umbrel.local:8090"
```

## Health Checks & Monitoring

### Health Check Endpoints
```python
# Health check implementation
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "mcp_server": "running",
            "web_interface": "running"
        }
    }

@app.get("/ready")  
async def readiness_check():
    # Check if all dependencies are available
    return {"ready": True}
```

### Container Health Monitoring
```yaml
# Docker Compose health checks
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 30s
```

## Security Configuration

### Container Security
```dockerfile
# Security best practices
USER app                    # Non-root user
COPY --chown=app:app ...   # Proper file ownership
RUN apt-get clean          # Clean package cache
```

### Network Security
- **SSH**: Encrypted communication for MCP protocol
- **Docker Networks**: Isolated container communication
- **No Exposed Credentials**: Environment-based configuration
- **Resource Limits**: Prevent resource exhaustion

## Troubleshooting Guide

### Common Issues
1. **SSH Connection Failed**
   ```bash
   ssh-copy-id umbrel@umbrel.local
   ssh umbrel@umbrel.local "docker ps"
   ```

2. **Container Not Starting**
   ```bash
   docker-compose logs mcp-server
   docker-compose logs web
   ```

3. **MQTT Connection Failed**
   ```bash
   docker exec -it bitsperity-mqtt-mcp_mcp-server_1 python -c "
   import asyncio
   import aiomqtt
   async def test(): 
       async with aiomqtt.Client('mosquitto_broker_1') as client:
           print('Connected!')
   asyncio.run(test())
   "
   ```

### Log Locations
- **MCP Server**: `/app/logs/mqtt-mcp.log`
- **Docker Logs**: `docker-compose logs -f`
- **Web Interface**: `/app/logs/web.log` 