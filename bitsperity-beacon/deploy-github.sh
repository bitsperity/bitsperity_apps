#!/bin/bash

# Bitsperity Beacon - GitHub Container Registry Deployment
# Für automatische Builds und Deployment

set -e

# Konfiguration
REGISTRY="ghcr.io"
NAMESPACE="bitsperity"
IMAGE_NAME="beacon"
VERSION=${1:-"latest"}

echo "🚀 Deploying Bitsperity Beacon to GitHub Container Registry..."

# Prüfe ob GitHub CLI verfügbar ist
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) ist nicht installiert."
    echo "   Installiere es mit: https://cli.github.com/"
    exit 1
fi

# Prüfe GitHub Authentication
if ! gh auth status &> /dev/null; then
    echo "❌ Nicht bei GitHub angemeldet."
    echo "   Führe 'gh auth login' aus."
    exit 1
fi

# Prüfe Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker ist nicht verfügbar."
    exit 1
fi

# GitHub Container Registry Login
echo "🔐 Anmeldung bei GitHub Container Registry..."
echo $GITHUB_TOKEN | docker login $REGISTRY -u $GITHUB_ACTOR --password-stdin

# Build Image
echo "🔨 Baue Docker Image..."
docker build -t $REGISTRY/$NAMESPACE/$IMAGE_NAME:$VERSION .
docker build -t $REGISTRY/$NAMESPACE/$IMAGE_NAME:latest .

# Push Images
echo "📤 Pushe Images zu GitHub Container Registry..."
docker push $REGISTRY/$NAMESPACE/$IMAGE_NAME:$VERSION
docker push $REGISTRY/$NAMESPACE/$IMAGE_NAME:latest

# Tag für Release
if [ "$VERSION" != "latest" ]; then
    echo "🏷️  Erstelle Git Tag..."
    git tag -a "v$VERSION" -m "Release v$VERSION"
    git push origin "v$VERSION"
fi

echo "✅ Deployment erfolgreich!"
echo ""
echo "📦 Image: $REGISTRY/$NAMESPACE/$IMAGE_NAME:$VERSION"
echo "🌐 Registry: https://github.com/orgs/$NAMESPACE/packages/container/package/$IMAGE_NAME"
echo ""
echo "🚀 Verwendung:"
echo "   docker pull $REGISTRY/$NAMESPACE/$IMAGE_NAME:$VERSION"
echo "   docker run -d --name beacon --network host $REGISTRY/$NAMESPACE/$IMAGE_NAME:$VERSION" 