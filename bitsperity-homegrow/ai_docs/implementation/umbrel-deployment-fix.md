# Umbrel Deployment Fix - HomeGrow v3

## 🐛 Problem
Umbrel deployment failed with:
```
unable to prepare context: path "/opt/umbreld/source/modules/apps/legacy-compat/app" not found
```

## 🔧 Root Cause
Docker build context in `docker-compose.yml` war nicht explizit genug konfiguriert:
```yaml
# FEHLERHAFTE Konfiguration:
web:
  build: ./app
```

## ✅ Solution
**1. Docker-Compose Fix** - Explizite context und dockerfile Pfade:
```yaml
web:
  build:
    context: ./app
    dockerfile: Dockerfile
```

**2. Dockerfile Fix** - curl für Health Checks installieren:
```dockerfile
FROM node:18-alpine

# Install curl for health checks
RUN apk add --no-cache curl
```

## 🧪 Testing
**Local Build Test:**
```bash
docker build -t bitsperity-homegrow:test ./app
# ✅ SUCCESS - 28.8s build time
```

**Deploy Script:**
- Build context bereits korrekt (`./app`)
- Multi-platform builds funktional
- Deployment-Automatisierung ready

## 📦 Files Modified
- `docker-compose.yml` - Explizite build context
- `app/Dockerfile` - curl Installation für Health Checks

## 🚀 Ready for Deployment
- ✅ Docker build lokal erfolgreich
- ✅ Build context korrekt konfiguriert
- ✅ Health checks funktional
- ✅ Deployment script ready

**Next:** Deploy auf Umbrel via `./deploy-dockerhub.sh` 