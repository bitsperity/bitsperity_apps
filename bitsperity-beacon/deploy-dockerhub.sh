#!/bin/bash

# Bitsperity Beacon - Docker Hub Deployment
# Für öffentliche Docker Hub Registry

set -e

# Konfiguration
REGISTRY="docker.io"
NAMESPACE="bitsperity"
IMAGE_NAME="beacon"
VERSION=${1:-"latest"}

echo "🚀 Deploying Bitsperity Beacon to Docker Hub..."

# Prüfe Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker ist nicht verfügbar."
    exit 1
fi

# Prüfe Docker Hub Login
if ! docker info | grep -q "Username"; then
    echo "❌ Nicht bei Docker Hub angemeldet."
    echo "   Führe 'docker login' aus."
    exit 1
fi

# Build Multi-Platform Images
echo "🔨 Baue Multi-Platform Docker Images..."

# Erstelle Builder falls nicht vorhanden
docker buildx create --name multiarch --use 2>/dev/null || docker buildx use multiarch

# Build und Push für multiple Architekturen
docker buildx build \
    --platform linux/amd64,linux/arm64,linux/arm/v7 \
    --tag $NAMESPACE/$IMAGE_NAME:$VERSION \
    --tag $NAMESPACE/$IMAGE_NAME:latest \
    --push \
    .

# Prüfe ob Images erfolgreich gepusht wurden
echo "🔍 Prüfe gepushte Images..."
docker manifest inspect $NAMESPACE/$IMAGE_NAME:$VERSION > /dev/null
docker manifest inspect $NAMESPACE/$IMAGE_NAME:latest > /dev/null

# Tag für Release
if [ "$VERSION" != "latest" ]; then
    echo "🏷️  Erstelle Git Tag..."
    git tag -a "v$VERSION" -m "Release v$VERSION" 2>/dev/null || echo "Tag bereits vorhanden"
    git push origin "v$VERSION" 2>/dev/null || echo "Tag bereits gepusht"
fi

echo "✅ Deployment erfolgreich!"
echo ""
echo "📦 Image: $NAMESPACE/$IMAGE_NAME:$VERSION"
echo "🌐 Docker Hub: https://hub.docker.com/r/$NAMESPACE/$IMAGE_NAME"
echo ""
echo "🚀 Verwendung:"
echo "   docker pull $NAMESPACE/$IMAGE_NAME:$VERSION"
echo "   docker run -d --name beacon --network host $NAMESPACE/$IMAGE_NAME:$VERSION"
echo ""
echo "🏗️  Unterstützte Architekturen:"
echo "   - linux/amd64 (x86_64)"
echo "   - linux/arm64 (ARM64)"
echo "   - linux/arm/v7 (ARM32)" 