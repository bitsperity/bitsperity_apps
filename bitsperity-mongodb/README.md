# MongoDB für Umbrel

Diese App stellt eine saubere MongoDB-Datenbank bereit, die von anderen Apps im Umbrel-Ökosystem genutzt werden kann.

## Zugangsdaten
- Benutzer: `umbrel`
- Passwort: `umbrel`
- Port: `27017`

## Verbindung
Andere Apps können sich mit folgendem URI verbinden:

```
mongodb://umbrel:umbrel@bitsperity-mongodb:27017/
```

## Datenpersistenz
Die Datenbankdaten werden im Volume `mongodb-data` gespeichert und bleiben bei Updates erhalten. 