#!/bin/bash

# Bitsperity MQTT MCP - Docker Hub Deployment
# Für öffentliche Docker Hub Registry

set -e

# push changes to github
echo "🔄 Pushing changes to GitHub..."
git add . && git commit -m 'Phase 4: Advanced Tools & Production deployment' && git push

# Konfiguration
REGISTRY="docker.io"
NAMESPACE="bitsperity"
IMAGE_NAME="mqtt-mcp"
VERSION=${1:-"latest"}
UMBREL_HOST=${UMBREL_HOST:-"umbrel@umbrel.local"}

echo "🚀 Deploying Bitsperity MQTT MCP to Docker Hub..."

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

# Build und Push für amd64 (MCP Server für AI Assistant)
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
    echo "🗑️  Deinstalliere bitsperity-mqtt-mcp..."
    if ssh $UMBREL_HOST "umbreld client apps.uninstall.mutate --appId bitsperity-mqtt-mcp" 2>/dev/null; then
        echo "✅ App erfolgreich deinstalliert"
        
        # Warte kurz für cleanup
        echo "⏳ Warte 5 Sekunden für Cleanup..."
        sleep 5
        
        # Installiere App neu
        echo "📦 Installiere bitsperity-mqtt-mcp neu..."
        if ssh $UMBREL_HOST "umbreld client apps.install.mutate --appId bitsperity-mqtt-mcp" 2>/dev/null; then
            echo "✅ App erfolgreich neu installiert"
            
            # Warte auf Start
            echo "⏳ Warte 15 Sekunden für App-Start..."
            sleep 15
            
            # Teste MCP Server über SSH (STDIO communication)
            echo "🔌 Teste MCP Server..."
            MCP_TEST_RESULT=$(ssh $UMBREL_HOST "docker exec bitsperity-mqtt-mcp python3 -c \"
import json
import sys
import subprocess
import time

# Test MCP server via stdin/stdout
proc = subprocess.Popen(
    ['python3', '/app/src/simple_mcp_server.py'], 
    stdin=subprocess.PIPE, 
    stdout=subprocess.PIPE, 
    stderr=subprocess.PIPE,
    text=True,
    cwd='/app'
)

# Send JSON-RPC test request
test_request = {
    'jsonrpc': '2.0',
    'method': 'list_active_connections',
    'params': {},
    'id': 1
}

try:
    proc.stdin.write(json.dumps(test_request) + '\n')
    proc.stdin.flush()
    
    # Wait for response (timeout 5s)
    proc.wait(timeout=5)
    
    # Get response
    response_line = proc.stdout.readline().strip()
    if response_line:
        response = json.loads(response_line)
        if response.get('jsonrpc') == '2.0' and 'result' in response:
            print('MCP_SERVER_OK')
        else:
            print('MCP_SERVER_ERROR')
    else:
        print('MCP_SERVER_NO_RESPONSE')
        
except Exception as e:
    print(f'MCP_SERVER_EXCEPTION: {e}')
finally:
    proc.terminate()
\"" 2>/dev/null)
            
            if echo "$MCP_TEST_RESULT" | grep -q "MCP_SERVER_OK"; then
                echo "✅ MCP Server Test erfolgreich - Server läuft!"
                
                # Teste Web Interface (falls implementiert)
                echo "🌐 Teste Web Interface..."
                if curl -s -o /dev/null -w "%{http_code}" http://umbrel.local:8090/health 2>/dev/null | grep -q "200"; then
                    echo "✅ Web Interface erreichbar auf Port 8090"
                else
                    echo "⚠️  Web Interface nicht erreichbar (optional in Phase 4)"
                fi
                
                # Zeige Container Status
                echo ""
                echo "📊 Container Status:"
                ssh $UMBREL_HOST "docker ps --filter name=bitsperity-mqtt-mcp --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'" 2>/dev/null || echo "Status konnte nicht abgerufen werden"
                
            else
                echo "❌ MCP Server Test fehlgeschlagen"
                echo "   Debug: $MCP_TEST_RESULT"
                echo "   Logs anzeigen: ssh $UMBREL_HOST 'docker logs bitsperity-mqtt-mcp'"
            fi
        else
            echo "❌ App-Installation fehlgeschlagen"
            echo "   Prüfe ob Dependencies installiert sind:"
            echo "   - mosquitto (MQTT Broker für testing)"
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
echo "   docker run -d --name mqtt-mcp --network host $NAMESPACE/$IMAGE_NAME:$VERSION"
echo ""
echo "🔗 Dependencies:"
echo "   - mosquitto (MQTT Broker zum testing)"
echo ""
echo "🏗️  Unterstützte Architekturen:"
echo "   - linux/amd64 (x86_64)"
echo ""
echo "📱 MCP Server: SSH + docker exec für AI Assistant integration"
echo "🌐 Web Interface: http://umbrel.local:8090 (optional)" 