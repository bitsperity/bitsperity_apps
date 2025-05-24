#!/bin/bash

# Health check script for MongoDB MCP Server

# Check if the web server is responding
if curl -f -s http://localhost:8080/health > /dev/null; then
    echo "Health check passed"
    exit 0
else
    echo "Health check failed"
    exit 1
fi 