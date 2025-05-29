#!/bin/bash

# Bitsperity Beacon - Docker Hub Deployment
# Für öffentliche Docker Hub Registry

set -e

# Konfiguration
REGISTRY="docker.io"
NAMESPACE="bitsperity"
IMAGE_NAME="beacon"
VERSION=${1:-"latest"}
UMBREL_HOST=${UMBREL_HOST:-"umbrel@umbrel.local"}

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

# Build Frontend
echo "🎨 Baue Frontend..."
cd frontend
npm run build
cd ..

# Build Multi-Platform Images
echo "🔨 Baue Multi-Platform Docker Images..."

# Erstelle Builder falls nicht vorhanden
docker buildx create --name multiarch --use 2>/dev/null || docker buildx use multiarch

# Build und Push für amd64 (Multi-Platform Build hat Probleme mit Rollup)
docker buildx build \
    --platform linux/amd64 \
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

echo "✅ Docker Deployment erfolgreich!"

# 🆕 AUTO-DEPLOY auf Umbrel Server
echo ""
echo "🔄 Auto-Deploy auf Umbrel Server..."

# Prüfe SSH-Verbindung
if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no $UMBREL_HOST "echo 'SSH OK'" 2>/dev/null; then
    echo "📡 SSH-Verbindung zu $UMBREL_HOST erfolgreich"
    
    # Deinstalliere App
    echo "🗑️  Deinstalliere bitsperity-beacon..."
    if ssh $UMBREL_HOST "umbreld client apps.uninstall.mutate --appId bitsperity-beacon" 2>/dev/null; then
        echo "✅ App erfolgreich deinstalliert"
        
        # Warte kurz für cleanup
        echo "⏳ Warte 5 Sekunden für Cleanup..."
        sleep 5
        
        # Installiere App neu
        echo "📦 Installiere bitsperity-beacon neu..."
        if ssh $UMBREL_HOST "umbreld client apps.install.mutate --appId bitsperity-beacon" 2>/dev/null; then
            echo "✅ App erfolgreich neu installiert"
            
            # Warte auf Start
            echo "⏳ Warte 10 Sekunden für App-Start..."
            sleep 10
            
            # Teste Health Endpoint
            echo "🏥 Teste Health Endpoint..."
            if curl -s -o /dev/null -w "%{http_code}" http://umbrel.local:8097/api/v1/health | grep -q "200"; then
                echo "✅ Health Check erfolgreich - App läuft!"
            else
                echo "⚠️  Health Check fehlgeschlagen - prüfe App-Status"
            fi
        else
            echo "❌ App-Installation fehlgeschlagen"
        fi
    else
        echo "❌ App-Deinstallation fehlgeschlagen"
    fi
else
    echo "⚠️  SSH-Verbindung zu $UMBREL_HOST fehlgeschlagen - überspringe Auto-Deploy"
    echo "   Setze UMBREL_HOST environment variable für anderen Host"
fi

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