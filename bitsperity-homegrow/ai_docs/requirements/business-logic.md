# HomeGrow v3 - Business Logic

## BL-001: Device Lifecycle Management

### Device Discovery & Registration
**Workflow**:
1. ESP32-Client startet und registriert sich bei Bitsperity Beacon
2. HomeGrow Server empfängt Discovery-Event via WebSocket
3. Server validiert Client-Typ (muss HomeGrow-kompatibel sein)
4. Neues Device wird zur Discovery-Liste hinzugefügt
5. Benutzer kann Device per Ein-Klick-Registrierung hinzufügen
6. Server erstellt Device-Eintrag in MongoDB und startet MQTT-Subscription

**Geschäftsregeln**:
- Nur HomeGrow-kompatible Clients werden angezeigt
- Device-IDs müssen systemweit eindeutig sein
- Duplikate werden automatisch gefiltert
- Maximale Anzahl: 50 Geräte pro Installation

**Status-Management**:
- **Online**: Letzter Heartbeat < 5 Minuten
- **Offline**: Letzter Heartbeat > 5 Minuten
- **Error**: Kommunikationsfehler oder kritische Sensor-Werte
- **Unknown**: Device ist registriert, aber noch nie verbunden

## BL-002: Sensor Data Processing

### Real-time Data Pipeline
**Workflow**:
1. ESP32 sendet Sensor-Rohdaten via MQTT
2. MQTT Bridge empfängt und validiert Daten
3. Daten werden in drei Formaten gespeichert:
   - **Raw**: Ursprünglicher ADC-Wert
   - **Calibrated**: Nach Sensor-Kalibrierung umgerechnet
   - **Filtered**: Nach Moving-Average Filter geglättet
4. WebSocket Service broadcastet Updates an alle verbundenen Clients
5. Automation Engine prüft auf Trigger-Bedingungen

**Datenvalidierung**:
- pH-Bereich: 0.0 - 14.0 (Warning bei < 4.0 oder > 8.5)
- TDS-Bereich: 0 - 5000ppm (Warning bei > 2000ppm)
- Zeitstempel-Validierung: Nicht älter als 1 Stunde
- Sensor-Quality-Flag: good/warning/error

**Datenretention**:
- **Live-Daten**: Alle Readings für 30 Tage
- **Aggregiert (Stunde)**: 1 Jahr Aufbewahrung
- **Aggregiert (Tag)**: 5 Jahre Aufbewahrung
- **Automatische Archivierung**: Nach konfigurierbarem Zeitraum

## BL-003: Program Template System

### Template Creation Logic
**Workflow**:
1. Benutzer öffnet Template-Editor
2. Definition der Grund-Parameter:
   - Template-Name (muss eindeutig sein)
   - Beschreibung und Tags
   - Gesamtdauer (berechnet aus Phasen)
3. Phasen-Definition (1-10 Phasen möglich):
   - Phase-Name und Dauer (1-90 Tage)
   - pH-Zielbereich (Min/Max)
   - TDS-Zielbereich (Min/Max)  
   - Nährstoffverhältnis (Nutrient A/B/C in %)
   - Pump-Zyklen (Wasser und Luft)
4. Template-Validierung vor Speicherung
5. Speicherung in User-Bibliothek

**Validierungsregeln**:
- Template-Name darf nicht leer sein
- Mindestens 1 Phase erforderlich
- pH-Bereiche zwischen 4.0-8.5
- TDS-Bereiche zwischen 100-2000ppm
- Nährstoffverhältnis muss 100% ergeben
- Pump-Zyklen dürfen nicht überlappen

### Starter Templates
**Vordefinierte Templates**:
- **Salat (42 Tage, 3 Phasen)**:
  - Setzling (14 Tage): pH 5.8-6.2, TDS 200-350
  - Wachstum (21 Tage): pH 5.5-6.0, TDS 400-600
  - Ernte (7 Tage): pH 5.5-6.0, TDS 300-500

- **Kräuter (45 Tage, 3 Phasen)**:
  - Setzling (15 Tage): pH 5.8-6.3, TDS 300-450
  - Wachstum (25 Tage): pH 5.5-6.2, TDS 500-800
  - Reife (5 Tage): pH 5.5-6.0, TDS 400-600

- **Tomaten (90 Tage, 4 Phasen)**:
  - Setzling (14 Tage): pH 6.0-6.5, TDS 400-600
  - Vegetativ (30 Tage): pH 5.8-6.2, TDS 600-900
  - Blüte (35 Tage): pH 5.5-6.0, TDS 800-1200
  - Reife (11 Tage): pH 5.5-6.0, TDS 600-900

## BL-004: Program Instance Execution

### Program Lifecycle
**Status-Workflow**:
```
Not Started → Running → Paused → Running → Completed
     ↓           ↓         ↓         ↓          ↓
   Error    →  Error  →  Error  →  Error  →  Error
```

**Phase-Transition Logic**:
1. Aktuelle Phase läuft bis konfigurierte Dauer erreicht
2. System prüft ob alle Targets der Phase erreicht wurden
3. Automatischer Übergang zur nächsten Phase
4. Program-Log wird mit Transition-Event aktualisiert
5. WebSocket-Update an alle Clients gesendet

**Program-Pause Trigger**:
- **Manuell**: Benutzer pausiert Programm
- **Critical Alert**: pH/TDS außerhalb Safety-Bereich
- **Device Offline**: Kein Heartbeat für 10 Minuten
- **Sensor Error**: Sensor-Quality "error" für 30 Minuten
- **Manual Override**: Benutzer startet manuelle Aktion

## BL-005: Automation Engine Logic

### pH-Korrektur Algorithmus
**Trigger-Bedingungen**:
- pH-Wert außerhalb des aktuellen Phasen-Zielbereichs
- Mindestens 10 Minuten seit letzter Korrektur
- Sensor-Quality mindestens "warning"
- Program ist im Status "running"

**Korrektur-Berechnung**:
```
Wenn pH > Zielbereich_Max:
  pH_Down_Zeit = (aktueller_pH - Ziel_pH) × Kalibrierung_Faktor
  Maximale_Zeit = min(pH_Down_Zeit, 60 Sekunden)

Wenn pH < Zielbereich_Min:
  pH_Up_Zeit = (Ziel_pH - aktueller_pH) × Kalibrierung_Faktor
  Maximale_Zeit = min(pH_Up_Zeit, 60 Sekunden)
```

**Safety-Checks**:
- Maximale Pump-Laufzeit: 60 Sekunden pro Korrektur
- Maximale Korrekturen: 10 pro Stunde
- Emergency Stop bei pH < 4.0 oder > 8.5

### TDS-Management Logic
**Nährstoff-Dosierung**:
1. Berechnung der benötigten TDS-Erhöhung
2. Verteilung basierend auf Phasen-Nährstoffverhältnis
3. Sequenzielle Dosierung (Nutrient A → B → Cal-Mag)
4. Wartezeit zwischen Dosierungen: 5 Minuten
5. Validierung nach 15 Minuten

**Verdünnung bei zu hohem TDS**:
- Automatische Frischwasser-Zugabe bei TDS > Zielbereich + 20%
- Maximale Verdünnung: 10% des Reservoir-Volumens pro Tag
- Emergency Stop bei TDS > 2000ppm

### Pump-Zyklen Management
**Zeitbasierte Zyklen**:
- **Wasser-Pumpe**: Standardzyklus alle 15 Minuten für 3 Minuten
- **Luft-Pumpe**: Standardzyklus alle 30 Minuten für 5 Minuten
- **Phasenspezifische Anpassung**: Zyklen werden pro Phase individuell konfiguriert

**Überlappungsschutz**:
- Nur eine Pumpe gleichzeitig aktiv (außer Luft-Pumpe)
- Mindestabstand zwischen Pump-Aktionen: 30 Sekunden
- Manuelle Aktionen haben Priorität vor automatischen

## BL-006: Manual Control Logic

### Emergency Stop Verhalten
**Trigger-Ereignisse**:
- Benutzer klickt Emergency Stop Button
- Kritische pH-Werte (< 4.0 oder > 8.5)
- Kritische TDS-Werte (> 2000ppm)
- Sensor-Kommunikationsfehler für > 5 Minuten

**Stop-Sequence**:
1. Alle Pumpen sofort stoppen
2. Laufende Programme pausieren
3. Critical Alert an alle Benutzer senden
4. System in "Safe Mode" versetzen
5. Manuelle Freigabe erforderlich für Fortsetzung

### Manual Override Logic
**Prioritäten-System**:
1. **Emergency Stop**: Höchste Priorität, stoppt alles
2. **Manual Pump Control**: Pausiert automatische Aktionen
3. **Sensor Calibration**: Pausiert Programme temporär
4. **Program Actions**: Normale Priorität
5. **Scheduled Cycles**: Niedrigste Priorität

**Wiederaufnahme-Logic**:
- Nach manueller Aktion: 60 Sekunden Wartezeit
- Nach Kalibrierung: Sofortige Wiederaufnahme
- Nach Emergency Stop: Manuelle Freigabe erforderlich

## BL-007: Alert Management Logic

### Alert-Klassifizierung
**Critical Alerts**:
- pH außerhalb Safety-Bereich (< 4.0 oder > 8.5)
- TDS über 2000ppm
- Device offline für > 30 Minuten
- Sensor-Error für > 30 Minuten
- **Automatische Aktion**: Program pausieren

**Warning Alerts**:
- pH außerhalb Zielbereich für > 60 Minuten
- TDS außerhalb Zielbereich für > 60 Minuten
- Pump-Fehler oder maximale Laufzeit erreicht
- Device offline für > 10 Minuten
- **Automatische Aktion**: Benachrichtigung senden

**Info Alerts**:
- Erfolgreiche pH/TDS-Korrektur
- Program-Phasen-Übergang
- Device kommt online
- Erfolgreiche Backup-Erstellung
- **Automatische Aktion**: Log-Eintrag

### Benachrichtigungs-Routing
**Kanal-Auswahl basierend auf Alert-Typ**:
- **Critical**: In-App + Browser Push + Email
- **Warning**: In-App + Browser Push
- **Info**: In-App Toast
- **System**: In-App nur

**Rate Limiting**:
- Maximal 5 Alerts pro Minute
- Identische Alerts werden für 30 Minuten unterdrückt
- Critical Alerts haben keine Rate-Limits

## BL-008: Data Export & Backup Logic

### Export-Funktionen
**Sensor Data Export**:
- Format: CSV mit konfigurierbaren Spalten
- Zeitraum-Auswahl: 1 Stunde bis 1 Jahr
- Aggregierung: Raw, Stunde, Tag, Woche
- Maximale Export-Größe: 100.000 Datenpunkte

**Configuration Export**:
- Templates, Device-Konfigurationen, User-Settings
- Format: JSON für maschinelle Verarbeitung
- ZIP-Package für komplette Backups

### Automatisches Backup
**Backup-Schedule**:
- **Daily**: Sensor-Daten der letzten 7 Tage
- **Weekly**: Programme und Konfigurationen
- **Monthly**: Vollständiges System-Backup

**Backup-Rotation**:
- Daily: 7 Backups aufbewahren
- Weekly: 4 Backups aufbewahren
- Monthly: 12 Backups aufbewahren

**Restore-Logic**:
- Backup-Validierung vor Restore
- Automatische Rollback bei Restore-Fehlern
- User-Bestätigung für Daten-Überschreibung 