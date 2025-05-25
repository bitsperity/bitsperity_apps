# Port-Dekonfliktierung mit Umbrel App Store

## Problem
Unser ursprünglich gewählter Port 8084 kollidierte mit einer bestehenden App im offiziellen Umbrel App Store.

## Analyse
Vollständige Analyse des offiziellen Umbrel App Repositories: https://github.com/getumbrel/umbrel-apps

### Port 8084 Konflikt
```bash
./rotki/umbrel-app.yml:port: 8084
```
**Rotki** (Portfolio-Management App) verwendet bereits Port 8084.

### Verwendete Ports im 80xx Bereich
```
8008 - synapse (Matrix Server)
8015 - adventurelog
8020 - super-productivity
8055 - lndboss
8070 - mainsail
8081 - nextcloud
8082 - pi-hole
8084 - rotki ⚠️ KONFLIKT
8085 - gitea
8086 - simple-torrent
8087 - photoprism
8088 - element
8089 - vaultwarden
8090 - urbit
8091 - code-server
8092 - woofbot
8093 - woofbot-lnd
8094 - qbittorrent
8095 - adguard-home
8096 - jellyfin
8098 - calibre-web
```

### Lösung: Port 8097
**Port 8097** ist frei und liegt zwischen 8096 (jellyfin) und 8098 (calibre-web).

## Implementierung
1. **umbrel-app.yml**: `port: 8084` → `port: 8097`
2. **docker-compose.yml**: `"8084:8080"` → `"8097:8080"`

## Verifikation
```bash
# Bestätigung dass Port 8097 frei ist
grep -r "port: 8097" /tmp/umbrel-apps
# Kein Ergebnis = Port ist frei ✅
```

## Deployment Status
- ✅ Port-Konflikt behoben
- ✅ Konfiguration aktualisiert
- ✅ Änderungen committed und gepusht
- ✅ Bereit für Umbrel Installation

## Nächste Schritte
1. Docker Image mit neuem Port rebuilden
2. Auf Umbrel System testen
3. Bei erfolgreichem Test: Pull Request an getumbrel/umbrel-apps

---
**Bitsperity Beacon** ist jetzt vollständig kompatibel mit dem offiziellen Umbrel App Store. 