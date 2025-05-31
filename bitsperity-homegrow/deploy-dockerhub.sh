#!/bin/bash

# Bitsperity HomeGrow - Docker Hub Deployment
# Für öffentliche Docker Hub Registry

set -e

# push changes to github
echo "🔄 Pushing changes to GitHub..."
git add . && git commit -m 'update' && git push

# Konfiguration
REGISTRY="docker.io"
NAMESPACE="bitsperity"
IMAGE_NAME="homegrow"
VERSION=${1:-"latest"}
UMBREL_HOST=${UMBREL_HOST:-"umbrel@umbrel.local"}

echo "🚀 Deploying Bitsperity HomeGrow to Docker Hub..."

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

# Build Frontend (in app/ directory)
echo "🎨 Baue Frontend..."
cd app && npm run build && cd ..

# Build Multi-Platform Images
echo "🔨 Baue Multi-Platform Docker Images..."

# Erstelle Builder falls nicht vorhanden
docker buildx create --name multiarch --use 2>/dev/null || docker buildx use multiarch

# Build und Push für amd64 (from app/ directory as build context)
docker buildx build \
    --platform linux/amd64 \
    --tag $NAMESPACE/$IMAGE_NAME:$VERSION \
    --tag $NAMESPACE/$IMAGE_NAME:latest \
    --push \
    ./app

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
    echo "🗑️  Deinstalliere bitsperity-homegrow..."
    if ssh $UMBREL_HOST "umbreld client apps.uninstall.mutate --appId bitsperity-homegrow" 2>/dev/null; then
        echo "✅ App erfolgreich deinstalliert"
        
        # Warte kurz für cleanup
        echo "⏳ Warte 10 Sekunden für Cleanup..."
        sleep 10
        
        # Installiere App neu
        echo "📦 Installiere bitsperity-homegrow neu..."
        if ssh $UMBREL_HOST "umbreld client apps.install.mutate --appId bitsperity-homegrow" 2>/dev/null; then
            echo "✅ App erfolgreich neu installiert"
            
            # Warte auf Start (HomeGrow braucht länger wegen Dependencies)
            echo "⏳ Warte 20 Sekunden für App-Start..."
            sleep 20
            
            # Teste Health Endpoint (FIXED: correct API path)
            echo "🏥 Teste Health Endpoint..."
            if curl -s -o /dev/null -w "%{http_code}" http://umbrel.local:3000/api/v1/health | grep -q "200"; then
                echo "✅ Health Check erfolgreich - App läuft!"
                
                # Zeige Service Status
                echo ""
                echo "📊 Service Status:"
                curl -s http://umbrel.local:3000/api/v1/health | jq '.' 2>/dev/null || echo "Status konnte nicht abgerufen werden"
            else
                echo "⚠️  Health Check fehlgeschlagen - prüfe App-Status"
                echo "   Logs anzeigen: ssh $UMBREL_HOST 'docker logs bitsperity-homegrow'"
            fi
        else
            echo "❌ App-Installation fehlgeschlagen"
            echo "   Prüfe ob Dependencies installiert sind:"
            echo "   - bitsperity-mongodb"
            echo "   - bitsperity-beacon"
            echo "   - mosquitto"
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
echo "   docker run -d -p 3000:3000 --name homegrow $NAMESPACE/$IMAGE_NAME:$VERSION"
echo ""
echo "🔗 Dependencies:"
echo "   - bitsperity-mongodb (MongoDB Datenbank)"
echo "   - bitsperity-beacon (Service Discovery)"
echo "   - mosquitto (MQTT Broker)"
echo ""
echo "🏗️  Unterstützte Architekturen:"
echo "   - linux/amd64 (x86_64)"
echo ""
echo "📱 HomeGrow Dashboard: http://umbrel.local:3000" 