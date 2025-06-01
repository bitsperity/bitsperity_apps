# Dockerfile für bitsperity-mqtt-mcp
# Phase 1: MCP Foundation Development

FROM python:3.11-slim AS base

# Install system dependencies + build tools for psutil
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY src/ ./src/
COPY tests/ ./tests/

# Create data and logs directories
RUN mkdir -p /app/data /app/logs

# Health check for MCP server
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Development stage
FROM base as development
EXPOSE 8090
CMD ["python", "src/simple_mcp_server.py"]

# Production stage (für spätere Phasen)
FROM base as production
USER 1000:1000
CMD ["python", "src/simple_mcp_server.py"] 