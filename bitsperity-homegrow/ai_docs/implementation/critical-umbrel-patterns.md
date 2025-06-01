# Kritische Umbrel Deployment Patterns

## 🚨 KRITISCHES WISSEN: App Proxy Container Naming

Dieses Dokument enthält die **wichtigsten Learnings** für erfolgreiche Umbrel App Deployments, basierend auf echten Problemen und deren Lösungen.

## Problem: ERR_CONNECTION_REFUSED bei Umbrel Apps

### Symptom
```
This site can't be reached
umbrel.local refused to connect.
ERR_CONNECTION_REFUSED
```

### Root Cause
**App Proxy kann den Web Container nicht finden** wegen falscher Container-Namen Konfiguration.

## ⚠️ UMBREL APP PROXY REGELN (KRITISCH!)

### Regel #1: APP_HOST = Echter Container Name
```yaml
# ❌ FALSCH
services:
  app_proxy:
    environment:
      APP_HOST: bitsperity-homegrow_web_1  # Standard Docker Compose Name
  web:
    container_name: homegrow               # Anderer Name!

# ✅ KORREKT  
services:
  app_proxy:
    environment:
      APP_HOST: homegrow                   # Exakt wie Container heißt
  web:
    container_name: homegrow               # Gleicher Name!
```

### Regel #2: Container Naming Strategien
```yaml
# Option A: Standard Docker Compose (ohne container_name)
services:
  app_proxy:
    environment:
      APP_HOST: myapp_web_1               # Standard Pattern
  web:
    image: myapp:latest
    # Kein container_name -> automatisch: myapp_web_1

# Option B: Custom Namen (mit container_name)
services:
  app_proxy:
    environment:
      APP_HOST: myapp                     # Custom Name
  web:
    image: myapp:latest
    container_name: myapp                 # APP_HOST muss matchen!
```

### Regel #3: Debugging Commands
```bash
# Container Namen prüfen
ssh umbrel@umbrel.local "sudo docker ps | grep {app-id}"

# App Proxy Logs checken
ssh umbrel@umbrel.local "sudo docker logs {app-id}_app_proxy_1 --tail 20"

# Netzwerk Aliases prüfen
ssh umbrel@umbrel.local "sudo docker inspect {container} | grep -A 10 'Networks'"
```

## 🎯 STANDARD UMBREL APP PATTERN (Bewährt)

### docker-compose.yml Template
```yaml
services:
  app_proxy:
    environment:
      # KRITISCH: Exakt der Container Name!
      APP_HOST: {app-name}
      APP_PORT: {internal-port}
      PROXY_AUTH_ADD: "false"

  web:
    image: {registry}/{app-name}:latest
    container_name: {app-name}            # APP_HOST muss das matchen!
    restart: unless-stopped
    environment:
      - NODE_ENV=production
      - PORT={internal-port}
    volumes:
      - ${APP_DATA_DIR}/data:/app/data
      - ${APP_DATA_DIR}/logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{internal-port}/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 5s

  # Optional: Service Discovery Registration
  beacon-registrar:
    image: curlimages/curl:latest
    depends_on:
      web:
        condition: service_healthy
    restart: "no"
    command: >
      curl -X POST http://bitsperity-beacon_web_1:80/api/v1/services/register
      -H "Content-Type: application/json"
      -d '{
        "name": "{app-name}",
        "type": "iot",
        "host": "{app-name}",             # Selber Name wie APP_HOST
        "port": {internal-port},
        "protocol": "http",
        "tags": ["iot", "automation"],
        "metadata": {
          "version": "1.0.0",
          "umbrel_app": "{umbrel-app-id}"
        },
        "ttl": 300
      }'
```

## 📋 PRE-DEPLOYMENT CHECKLIST

### ✅ Vor jedem Deployment:
1. **Namespace Check**: APP_HOST == container_name?
2. **Port Check**: APP_PORT == interner Service Port?
3. **Health Check**: Funktioniert /health endpoint?
4. **Dependencies**: Sind externe Services erreichbar?

### ✅ Nach Deployment:
1. **Container Status**: Alle Container laufen?
2. **App Proxy Logs**: Keine DNS Resolution Fehler?
3. **Health Endpoint**: Antwortet erfolgreich?
4. **Web Access**: App öffnet in Browser?

## 🔧 DEPLOYMENT VALIDATION SCRIPT

```bash
#!/bin/bash
# validate-umbrel-deployment.sh

set -e

APP_ID="bitsperity-homegrow"
CONTAINER_NAME="homegrow"
APP_PORT="3003"

echo "🔍 Validating Umbrel App Deployment..."

# 1. Validate Container Names Match
echo "Checking container name consistency..."
APP_HOST=$(grep "APP_HOST:" docker-compose.yml | awk '{print $2}')
CONTAINER_NAME_CONFIG=$(grep "container_name:" docker-compose.yml | awk '{print $2}')

if [ "$APP_HOST" != "$CONTAINER_NAME_CONFIG" ]; then
  echo "❌ FEHLER: APP_HOST ($APP_HOST) != container_name ($CONTAINER_NAME_CONFIG)"
  echo "App Proxy wird Container nicht finden können!"
  exit 1
fi
echo "✅ Container Namen sind konsistent"

# 2. Deploy App
echo "🚀 Deploying app..."
./deploy-dockerhub.sh

# 3. Wait for startup
echo "⏳ Waiting for app startup..."
sleep 30

# 4. Check containers are running
echo "🐳 Checking containers..."
ssh umbrel@umbrel.local "sudo docker ps | grep $CONTAINER_NAME" || {
  echo "❌ Container $CONTAINER_NAME ist nicht running"
  exit 1
}
echo "✅ Container läuft"

# 5. Check app proxy logs for errors
echo "📡 Checking app proxy logs..."
APP_PROXY_ERRORS=$(ssh umbrel@umbrel.local "sudo docker logs ${APP_ID}_app_proxy_1 --tail 10" | grep -c "cannot be found" || true)
if [ "$APP_PROXY_ERRORS" -gt 0 ]; then
  echo "❌ App Proxy kann Container nicht finden"
  ssh umbrel@umbrel.local "sudo docker logs ${APP_ID}_app_proxy_1 --tail 10"
  exit 1
fi
echo "✅ App Proxy Logs sehen gut aus"

# 6. Test health endpoint
echo "🏥 Testing health endpoint..."
ssh umbrel@umbrel.local "curl -f http://localhost:${APP_PORT}/api/v1/health" || {
  echo "❌ Health Check fehlgeschlagen"
  exit 1
}
echo "✅ Health Check erfolgreich"

# 7. Test external access
echo "🌐 Testing external access..."
curl -f "http://umbrel.local:${APP_PORT}/" || {
  echo "❌ External access fehlgeschlagen"
  exit 1
}
echo "✅ External access funktioniert"

echo ""
echo "🎉 Deployment erfolgreich validiert!"
echo "📱 App verfügbar unter: http://umbrel.local:${APP_PORT}/"
```

## 🎯 BEST PRACTICES SUMMARY

### Do's ✅
1. **Einfache Container Namen** - Kurz, eindeutig, keine Sonderzeichen
2. **APP_HOST Konsistenz** - Immer exakt der Container Name
3. **Health Checks** - Für alle Services, besonders für depends_on
4. **Validation Scripts** - Automatische Checks nach Deployment
5. **Logging** - Structured logging für besseres Debugging

### Don'ts ❌
1. **Inkonsistente Namen** - APP_HOST != container_name
2. **Komplexe Namen** - Keine Umlaute, Leerzeichen, Sonderzeichen
3. **Missing Health Checks** - Führt zu depends_on Problemen
4. **Blind Deployment** - Immer validieren nach Deployment
5. **Standard Docker Names** - Wenn container_name gesetzt, dann richtig

## 🔄 INTEGRATION MIT IMPLEMENTATION GUIDE

Diese Patterns erweitern das **Implementation Guide** um:

### Docker Compose Patterns (Erweiterung)
```yaml
# Standardisiertes Umbrel App Pattern
services:
  app_proxy:
    environment:
      APP_HOST: {simple-app-name}         # Einfach, eindeutig
      APP_PORT: {service-port}
      PROXY_AUTH_ADD: "false"

  web:
    image: {registry}/{image}:latest
    container_name: {simple-app-name}     # Muss APP_HOST entsprechen!
    restart: unless-stopped
    ports: []                             # Keine external ports nötig
    environment:
      - NODE_ENV=production
      - PORT={service-port}
    healthcheck:                          # KRITISCH für depends_on
      test: ["CMD", "curl", "-f", "http://localhost:{service-port}/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 5s
```

### Validation als Teil des Implementation Workflow
```bash
# Als Teil von deploy-dockerhub.sh
echo "🔍 Pre-deployment validation..."
./validate-umbrel-deployment.sh || exit 1

echo "🚀 Deploying..."
# ... deployment logic ...

echo "✅ Post-deployment validation..."
./validate-umbrel-deployment.sh || exit 1
```

## 💡 ZUKÜNFTIGE APPS

Für alle neuen Umbrel Apps:

1. **Naming Convention**: `{app-name}` für container_name und APP_HOST
2. **Validation Script**: Immer `validate-umbrel-deployment.sh` erstellen
3. **Health Endpoints**: Immer `/health` implementieren
4. **Structured Logging**: Für besseres Debugging
5. **Documentation**: Docker Patterns dokumentieren

Dieses Pattern ist **kritisch** für erfolgreiche Umbrel App Deployments! 🎯 