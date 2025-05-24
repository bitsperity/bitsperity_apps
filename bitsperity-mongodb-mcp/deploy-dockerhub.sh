#!/bin/bash

echo "🏗️  Building Docker image..."
docker build -t bitsperity/mongodb-mcp:latest .

echo "🔐 Docker Hub Login required..."
echo "Please run: docker login"
echo "Then run this script again."

# Check if logged in
if ! docker info | grep -q "Username:"; then
    echo "❌ Not logged into Docker Hub. Please run: docker login"
    exit 1
fi

echo "📤 Pushing to Docker Hub..."
docker push bitsperity/mongodb-mcp:latest

echo "✅ Image deployed to Docker Hub: bitsperity/mongodb-mcp:latest"
echo ""
echo "🚀 Next steps:"
echo "1. Commit and push the updated docker-compose.yml"
echo "2. Install the app from your Community Store"
echo "3. Image will be pulled from Docker Hub (HTTPS, no registry issues)" 