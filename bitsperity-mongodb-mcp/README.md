# MongoDB MCP Server

Ein moderner MongoDB Model Context Protocol (MCP) Server für nahtlose Integration zwischen LLM-Anwendungen wie Cursor und MongoDB-Datenbanken.

## 🚀 Schnellstart

### 1. Server bauen
```bash
./build.sh
```

### 2. In Cursor installieren
```bash
./install-cursor.sh
```

### 3. Web-Server starten (optional)
```bash
./run.sh
```

### 4. Cursor verwenden
1. **Cursor neu starten**
2. **Neuen Chat öffnen**
3. **Verbindung herstellen**: 
   ```
   Verbinde dich mit mongodb://user:pass@host:port/database
   ```

## 📋 Voraussetzungen

- **Python 3.11+**
- **Cursor IDE** (mit MCP-Unterstützung)
- **Docker & Docker Compose** (nur für Web-Interface)

## 🔧 Verfügbare Scripts

### `build.sh`
- Baut das Docker Image
- Erstellt notwendige Verzeichnisse
- Setzt Umgebungsvariablen

### `install-cursor.sh` ⭐
- **Installiert den MCP Server in Cursor**
- Erstellt automatisch Virtual Environment
- Installiert Python Dependencies
- Konfiguriert Cursor automatisch
- **Hauptinstallationsscript für Cursor-Integration**

### `run.sh`
- Startet den Web-Server in Docker
- Optional für Monitoring und Status
- Nicht erforderlich für Cursor-Funktionalität

### `dev.sh`
- Startet den Server direkt mit Python
- Ideal für Entwicklung und Debugging

## 🌐 Zugriff

- **Cursor Integration**: Automatisch nach Installation
- **Web Interface**: http://localhost:8080 (falls `run.sh` gestartet)

## 📖 Verwendung mit Cursor

### Installation
```bash
# Einmalige Installation
./build.sh
./install-cursor.sh

# Cursor neu starten
```

### Verwendung
```bash
# In Cursor Chat schreiben:
"Verbinde dich mit mongodb://localhost:27017/myapp"
"Zeige mir alle Datenbanken"
"Welche Collections gibt es in der Datenbank 'users'?"
"Analysiere das Schema der Collection 'products'"
"Finde alle Benutzer wo status = 'active'"
"Erstelle eine Aggregation für die Top 10 Kunden nach Umsatz"
```

### Unterstützte Befehle

| Befehl | Beschreibung | Beispiel |
|--------|--------------|----------|
| **Verbindung herstellen** | MongoDB-Verbindung aufbauen | `Verbinde dich mit mongodb://user:pass@cluster.net/db` |
| **Datenbanken auflisten** | Alle verfügbaren DBs anzeigen | `Zeige mir alle Datenbanken` |
| **Collections auflisten** | Collections einer DB anzeigen | `Welche Collections gibt es in myapp?` |
| **Schema analysieren** | Struktur einer Collection | `Analysiere das Schema von users` |
| **Dokumente abfragen** | Daten suchen und filtern | `Finde alle wo status = 'active'` |
| **Aggregationen** | Komplexe Datenanalyse | `Gruppiere Bestellungen nach Monat` |
| **Sample Daten** | Beispieldokumente anzeigen | `Zeige mir ein paar Beispiele aus orders` |

## 🏗️ Projektstruktur

```
bitsperity-mongodb-mcp/
├── src/                     # Python Quellcode
│   ├── server.py           # Web-Server (optional)
│   ├── mcp_stdio_server.py # MCP Server für Cursor ⭐
│   ├── connection_manager.py # Verbindungsmanagement
│   ├── schema_analyzer.py  # Schema-Analyse
│   ├── mongodb_tools.py    # MCP Tools
│   └── requirements.txt    # Python Dependencies
├── web/                    # Web Interface (optional)
├── build.sh               # Build Script
├── install-cursor.sh      # Cursor Installation ⭐
├── run.sh                # Web-Server (optional)
├── dev.sh               # Development Script
└── cursor-config.json   # Cursor Konfiguration
```

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `SESSION_TTL` | 3600 | Session-Timeout in Sekunden |
| `MAX_CONNECTIONS` | 10 | Maximale gleichzeitige Verbindungen |
| `LOG_LEVEL` | INFO | Log-Level (DEBUG, INFO, WARNING, ERROR) |
| `DATA_DIR` | ./data | Datenverzeichnis für Logs |

### Cursor-spezifische Konfiguration

Die Installation erfolgt automatisch über `install-cursor.sh`. Manuelle Konfiguration:

```json
{
  "mcpServers": {
    "mongodb": {
      "command": "python3",
      "args": ["/pfad/zu/bitsperity-mongodb-mcp/src/mcp_stdio_server.py"],
      "env": {
        "SESSION_TTL": "3600",
        "MAX_CONNECTIONS": "10",
        "LOG_LEVEL": "INFO",
        "DATA_DIR": "/pfad/zu/data"
      }
    }
  }
}
```

## 🔧 Features

- ✅ **Cursor Integration** - Nahtlose Integration in Cursor IDE
- ✅ **Dynamische Verbindungen** - Keine hardcodierten Connection Strings
- ✅ **Session-basierte Sicherheit** - Verschlüsselte, temporäre Verbindungen
- ✅ **Schema-Analyse** - Automatische Erkennung von Datenstrukturen
- ✅ **Multi-Database Support** - Mehrere Verbindungen gleichzeitig
- ✅ **Natürlichsprachliche Queries** - Sprechen Sie mit Ihrer Datenbank
- ✅ **Intelligente Tool-Auswahl** - Cursor wählt automatisch die richtigen Tools
- ✅ **Real-time Logging** - Vollständige Nachverfolgung aller Operationen

## 🛠️ Entwicklung

### Lokale Entwicklung ohne Docker

```bash
# Development Server starten
./dev.sh

# Logs anzeigen
tail -f data/logs/mcp-cursor.log
```

### Mit Docker (für Web-Interface)

```bash
# Image neu bauen
./build.sh

# Web-Server starten
LOG_LEVEL=DEBUG ./run.sh
```

## 📝 Logs

Logs werden gespeichert unter:
- **Cursor MCP**: `./data/logs/mcp-cursor.log`
- **Web-Server**: `./data/logs/mongodb-mcp.log`

## 🔒 Sicherheit

- Connection Strings werden **niemals persistent gespeichert**
- Verbindungen laufen automatisch nach `SESSION_TTL` ab
- Verschlüsselung aller sensiblen Daten im Speicher
- Isolierte Session-basierte Verbindungen
- Keine Cross-Session Datenlecks

## 🆘 Troubleshooting

### "MCP Server nicht gefunden in Cursor"
```bash
# Neu installieren
./install-cursor.sh

# Cursor komplett neu starten
```

### "Python Modul nicht gefunden"
```bash
# Dependencies neu installieren
rm -rf venv
./install-cursor.sh
```

### "Verbindung zu MongoDB fehlgeschlagen"
- Überprüfen Sie den Connection String
- Prüfen Sie Netzwerkverbindung
- Testen Sie mit MongoDB Compass

### "Permission denied"
```bash
sudo chown -R $USER:$USER ./data
chmod +x install-cursor.sh
```

### Cursor-spezifische Probleme
1. **Cursor neu starten** nach Installation
2. Überprüfen Sie die MCP-Konfiguration in Cursor Settings
3. Prüfen Sie die Logs: `tail -f data/logs/mcp-cursor.log`

## 🎯 Beispiel-Session

```bash
# 1. Installation (einmalig)
./build.sh
./install-cursor.sh

# 2. Cursor neu starten

# 3. In Cursor Chat:
User: "Verbinde dich mit mongodb://localhost:27017/ecommerce"
Cursor: ✅ Verbindung hergestellt! Session: abc123

User: "Zeige mir alle Datenbanken"
Cursor: 📊 Gefundene Datenbanken:
- ecommerce (15.2 MB, 5 Collections)
- analytics (8.1 MB, 3 Collections)
- logs (125.8 MB, 2 Collections)

User: "Analysiere das Schema der users Collection"
Cursor: 🔍 Schema-Analyse für users:
- _id: ObjectId (100% der Dokumente)
- email: string (100%, unique)
- name: string (98%)
- createdAt: date (100%)
- status: string (95%, Werte: active, inactive, pending)
...

User: "Finde alle aktive Benutzer aus Deutschland"
Cursor: 🔎 Gefunden: 142 aktive Benutzer aus Deutschland
[Zeigt Ergebnisse...]
```

## 📄 Lizenz

MIT License - siehe LICENSE Datei für Details.

## 🤝 Beiträge

Beiträge sind willkommen! Bitte erstellen Sie Issues oder Pull Requests.

## 📞 Support

- GitHub Issues: [Repository Issues](https://github.com/bitsperity/umbrel-apps/issues)
- Diskussionen: [GitHub Discussions](https://github.com/bitsperity/umbrel-apps/discussions) 