#!/bin/bash

echo "=== CSS Debug Script für Bitsperity Beacon ==="
echo

# 1. Frontend Build lokal testen
echo "1. Building Frontend lokal..."
cd frontend
npm run build
echo "✓ Frontend Build abgeschlossen"
echo

# 2. CSS-Datei analysieren
echo "2. Analysiere generierte CSS-Datei..."
CSS_FILE=$(find dist/assets -name "*.css" | head -1)
if [ -f "$CSS_FILE" ]; then
    echo "CSS-Datei gefunden: $CSS_FILE"
    echo "Größe: $(wc -c < "$CSS_FILE") bytes"
    echo "Erste 500 Zeichen:"
    head -c 500 "$CSS_FILE"
    echo
    echo "..."
    echo "Letzte 200 Zeichen:"
    tail -c 200 "$CSS_FILE"
    echo
    
    # Prüfe auf @apply Direktiven (sollten nicht da sein)
    if grep -q "@apply" "$CSS_FILE"; then
        echo "❌ PROBLEM: @apply Direktiven gefunden - Tailwind wurde nicht kompiliert!"
        grep -n "@apply" "$CSS_FILE" | head -5
    else
        echo "✓ Keine @apply Direktiven gefunden - CSS scheint kompiliert zu sein"
    fi
    
    # Prüfe auf Tailwind-Klassen
    if grep -q "\.bg-gradient-to-br" "$CSS_FILE"; then
        echo "✓ Tailwind-Klassen gefunden"
    else
        echo "❌ PROBLEM: Keine Tailwind-Klassen gefunden!"
    fi
else
    echo "❌ PROBLEM: Keine CSS-Datei gefunden!"
fi
echo

# 3. Docker Build testen
echo "3. Testing Docker Build..."
cd ..
docker build -t beacon-debug:test . --no-cache
echo "✓ Docker Build abgeschlossen"
echo

# 4. CSS aus Docker Container extrahieren
echo "4. Extrahiere CSS aus Docker Container..."
docker run --rm beacon-debug:test sh -c "find /app/frontend/dist/assets -name '*.css' -exec cat {} \;" > docker-css-output.txt
echo "CSS aus Docker Container gespeichert in: docker-css-output.txt"
echo "Größe: $(wc -c < docker-css-output.txt) bytes"
echo

# 5. Vergleiche lokales vs Docker CSS
echo "5. Vergleiche lokales vs Docker CSS..."
if [ -f "$CSS_FILE" ] && [ -f "docker-css-output.txt" ]; then
    LOCAL_SIZE=$(wc -c < "$CSS_FILE")
    DOCKER_SIZE=$(wc -c < "docker-css-output.txt")
    echo "Lokale CSS-Größe: $LOCAL_SIZE bytes"
    echo "Docker CSS-Größe: $DOCKER_SIZE bytes"
    
    if [ "$LOCAL_SIZE" -eq "$DOCKER_SIZE" ]; then
        echo "✓ CSS-Größen sind identisch"
    else
        echo "❌ PROBLEM: CSS-Größen unterscheiden sich!"
    fi
    
    if diff -q "$CSS_FILE" docker-css-output.txt > /dev/null; then
        echo "✓ CSS-Inhalte sind identisch"
    else
        echo "❌ PROBLEM: CSS-Inhalte unterscheiden sich!"
        echo "Erste Unterschiede:"
        diff "$CSS_FILE" docker-css-output.txt | head -10
    fi
else
    echo "❌ Kann CSS-Dateien nicht vergleichen"
fi
echo

echo "=== Debug abgeschlossen ==="
echo "Nächste Schritte:"
echo "1. Prüfe docker-css-output.txt auf @apply Direktiven"
echo "2. Teste das Image: docker run -p 8080:80 beacon-debug:test"
echo "3. Öffne http://localhost:8080 und prüfe Developer Tools" 