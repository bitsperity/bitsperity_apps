#!/bin/bash

# Setup script for MongoDB MCP Server

echo "Setting up MongoDB MCP Server..."

# Create necessary directories
mkdir -p /app/data
mkdir -p /app/logs

# Set permissions
chown -R appuser:appuser /app/data
chown -R appuser:appuser /app/logs

# Create empty log file if it doesn't exist
touch /app/logs/mongodb-mcp.log
chown appuser:appuser /app/logs/mongodb-mcp.log

echo "Setup completed successfully!" 