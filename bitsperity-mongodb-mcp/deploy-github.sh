#!/bin/bash

echo "🏗️  Building Docker image..."
docker build -t ghcr.io/bitsperity/bitsperity_apps/mongodb-mcp:latest .

echo "🔐 GitHub Container Registry Setup:"
echo "1. Create a Personal Access Token with 'write:packages' scope"
echo "2. Run: echo \$GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin"
echo "3. Then run this script again"
echo ""

# Simple check if logged in (may not work perfectly)
if ! docker info 2>/dev/null | grep -q "ghcr.io"; then
    echo "⚠️  Please login to GitHub Container Registry first"
    echo "Run: echo \$GITHUB_TOKEN | docker login ghcr.io -u bitsperity --password-stdin"
    echo ""
fi

echo "📤 Pushing to GitHub Container Registry..."
docker push ghcr.io/bitsperity/bitsperity_apps/mongodb-mcp:latest

echo "✅ Image deployed to GitHub Container Registry"
echo ""
echo "🚀 Next steps:"
echo "1. Commit and push the updated docker-compose.yml"
echo "2. Install the app from your Community Store"
echo "3. Image will be pulled from GitHub (HTTPS, secure)" 