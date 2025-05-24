#!/bin/bash

# Get laptop IP address in local network
LAPTOP_IP=$(ip route get 1.1.1.1 | awk '{print $7}' | head -1)

if [ -z "$LAPTOP_IP" ]; then
    echo "❌ Could not determine laptop IP address"
    exit 1
fi

echo "🔍 Laptop IP: $LAPTOP_IP"

# Update docker-compose.yml with correct IP (replace any existing IP:port pattern)
sed -i "s/[0-9]\+\.[0-9]\+\.[0-9]\+\.[0-9]\+:500[0-9]/$LAPTOP_IP:5001/g" docker-compose.yml

echo "🏗️  Building Docker image..."
docker build -t bitsperity-mongodb-mcp:latest .

echo "🏷️  Tagging for local registry..."
docker tag bitsperity-mongodb-mcp:latest $LAPTOP_IP:5001/bitsperity-mongodb-mcp:latest

# Configure Docker for insecure registry
echo "🔧 Configuring Docker for insecure registry..."
if ! grep -q "\"insecure-registries\"" /etc/docker/daemon.json 2>/dev/null; then
    echo "Adding insecure registry configuration..."
    sudo mkdir -p /etc/docker
    echo "{\"insecure-registries\":[\"$LAPTOP_IP:5001\"]}" | sudo tee /etc/docker/daemon.json
    echo "⚠️  Restarting Docker daemon..."
    sudo systemctl restart docker
    sleep 5
    # Restart our registry after Docker restart
    docker start registry
fi

echo "📤 Pushing to local registry..."
docker push $LAPTOP_IP:5001/bitsperity-mongodb-mcp:latest

echo "✅ Image deployed to $LAPTOP_IP:5001/bitsperity-mongodb-mcp:latest"
echo ""
echo "🚀 Next steps:"
echo "1. Push this repository to GitHub"
echo "2. Add Community App Store in Umbrel: https://github.com/USERNAME/REPO"
echo "3. Install the app from your Community Store" 