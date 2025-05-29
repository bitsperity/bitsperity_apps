#!/bin/bash

# Bitsperity HomeGrow - Lokales Deployment
# Für lokales Testing und Entwicklung

set -e

# Konfiguration
IMAGE_NAME="homegrow-local"
VERSION="dev"
CONTAINER_NAME="homegrow-dev"

echo "🚀 Building Bitsperity HomeGrow locally..."

# Build Frontend
echo "🎨 Baue Frontend..."
npm run build

# Build Docker Image lokal
echo "🔨 Baue Docker Image lokal..."
docker build -t $IMAGE_NAME:$VERSION .

# Stoppe und entferne alten Container falls vorhanden
echo "🧹 Bereinige alte Container..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# Starte neuen Container
echo "🚀 Starte HomeGrow Container..."
docker run -d \
    --name $CONTAINER_NAME \
    -p 3000:3000 \
    -e NODE_ENV=development \
    -e MONGODB_URL=mongodb://umbrel:umbrel@host.docker.internal:27017/homegrow \
    -e MQTT_URL=mqtt://host.docker.internal:1883 \
    -e BEACON_URL=http://host.docker.internal:8097 \
    --add-host=host.docker.internal:host-gateway \
    $IMAGE_NAME:$VERSION

echo "✅ Container gestartet!"
echo ""
echo "📊 Container Status:"
docker ps --filter name=$CONTAINER_NAME

# Warte auf App-Start
echo ""
echo "⏳ Warte auf App-Start..."
sleep 5

# Teste Health Endpoint
echo "🏥 Teste Health Endpoint..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/health | grep -q "200"; then
    echo "✅ Health Check erfolgreich - App läuft!"
    
    # Zeige Service Status
    echo ""
    echo "📊 Service Status:"
    curl -s http://localhost:3000/api/v1/system/status | jq '.services' 2>/dev/null || echo "Status konnte nicht abgerufen werden"
else
    echo "⚠️  Health Check fehlgeschlagen"
    echo ""
    echo "📋 Container Logs:"
    docker logs $CONTAINER_NAME --tail 50
fi

echo ""
echo "🌐 HomeGrow Dashboard: http://localhost:3000"
echo ""
echo "🛠️  Nützliche Befehle:"
echo "   Logs anzeigen:     docker logs -f $CONTAINER_NAME"
echo "   Container stoppen: docker stop $CONTAINER_NAME"
echo "   Container starten: docker start $CONTAINER_NAME"
echo "   Shell öffnen:      docker exec -it $CONTAINER_NAME /bin/sh" 