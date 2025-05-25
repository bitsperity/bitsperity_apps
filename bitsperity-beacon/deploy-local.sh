#!/bin/bash

# Bitsperity Beacon - Lokales Deployment Skript
# Für lokale Entwicklung und Testing

set -e

echo "🚀 Starte lokales Deployment von Bitsperity Beacon..."

# Prüfe ob Docker läuft
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker ist nicht verfügbar. Bitte starte Docker."
    exit 1
fi

# Prüfe ob docker-compose verfügbar ist
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose ist nicht installiert."
    exit 1
fi

# Environment Setup
if [ ! -f .env ]; then
    echo "📝 Erstelle .env Datei..."
    cp env.example .env
    echo "✅ .env Datei erstellt. Bitte konfiguriere sie nach Bedarf."
fi

# Erstelle notwendige Verzeichnisse
echo "📁 Erstelle Datenverzeichnisse..."
mkdir -p data/data
mkdir -p data/logs

# Build und starte Services
echo "🔨 Baue Docker Images..."
docker-compose build

echo "🚀 Starte Services..."
docker-compose up -d

# Warte auf Services
echo "⏳ Warte auf Services..."
sleep 10

# Health Check
echo "🔍 Prüfe Service Status..."
if curl -f http://localhost:8080/api/v1/health > /dev/null 2>&1; then
    echo "✅ Bitsperity Beacon ist erfolgreich gestartet!"
    echo ""
    echo "🌐 Dashboard: http://localhost:8080"
    echo "📚 API Docs: http://localhost:8080/api/docs"
    echo "🔧 API: http://localhost:8080/api/v1"
    echo ""
    echo "📋 Nützliche Befehle:"
    echo "  docker-compose logs -f beacon-api    # Logs anzeigen"
    echo "  docker-compose stop                  # Services stoppen"
    echo "  docker-compose down                  # Services entfernen"
    echo "  docker-compose ps                    # Status anzeigen"
else
    echo "❌ Service Health Check fehlgeschlagen"
    echo "📋 Logs:"
    docker-compose logs beacon-api
    exit 1
fi 