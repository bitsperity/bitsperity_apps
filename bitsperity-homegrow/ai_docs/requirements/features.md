# HomeGrow v3 - Feature Specifications

## F-001: System Dashboard
**Beschreibung**: Zentrale Übersicht über alle hydroponischen Systeme mit Status-Karten und Quick Actions
**Priorität**: Must-Have (MVP)

**Funktionale Anforderungen**:
- Anzeige von 4 Status-Karten: Online/Offline Geräte, Aktive Programme, Aktive Alerts, System Uptime
- Device-Grid mit aktuellen Sensor-Werten aller Geräte
- Recent Activity Feed mit letzten Aktionen und Korrekturen
- Quick Actions für häufige Aufgaben (Discover, Emergency Stop, Refresh)
- Auto-Refresh alle 30 Sekunden mit manueller Refresh-Option

**Business Rules**:
- Dashboard muss innerhalb 2 Sekunden laden
- Status-Updates erfolgen in Echtzeit via WebSocket
- Emergency Actions sind immer verfügbar
- Maximal 50 Geräte können gleichzeitig angezeigt werden

**Acceptance Criteria**:
- [ ] Alle 4 Status-Karten sind sichtbar und zeigen korrekte Werte
- [ ] Device-Grid zeigt alle registrierten Geräte mit aktuellem Status
- [ ] Auto-Refresh funktioniert alle 30 Sekunden
- [ ] Quick Actions sind funktional und reagieren innerhalb 1 Sekunde
- [ ] Mobile-optimierte Darstellung auf Smartphones

## F-002: Automatische Device Discovery
**Beschreibung**: Automatische Erkennung von ESP32-Clients über Bitsperity Beacon Service Discovery
**Priorität**: Must-Have (MVP)

**Funktionale Anforderungen**:
- Automatische Erkennung neuer HomeGrow ESP32-Clients
- Anzeige entdeckter Geräte mit Geräteinformationen
- Ein-Klick Registrierung von entdeckten Geräten
- Manueller Discovery-Trigger über Button
- Benachrichtigung bei neu entdeckten Geräten

**Business Rules**:
- Discovery läuft automatisch bei App-Start
- Clients müssen sich beim Beacon-Service registriert haben
- Duplikate werden automatisch gefiltert
- Discovery-Prozess darf nicht länger als 30 Sekunden dauern

**Acceptance Criteria**:
- [ ] ESP32-Clients werden automatisch erkannt
- [ ] Entdeckte Geräte können mit einem Klick hinzugefügt werden
- [ ] Manuelle Discovery-Funktion verfügbar
- [ ] Fehlerbehandlung bei Discovery-Problemen
- [ ] Status-Feedback während Discovery-Prozess

## F-003: Real-time Sensor Monitoring
**Beschreibung**: Live-Anzeige von pH- und TDS-Sensordaten mit historischen Charts
**Priorität**: Must-Have (MVP)

**Funktionale Anforderungen**:
- Live-Updates alle 10 Sekunden für Sensor-Daten
- Anzeige aktueller pH- und TDS-Werte mit Trends
- Historische Charts mit konfigurierbaren Zeiträumen (1h, 6h, 24h, 7d, 30d)
- Multi-Device Vergleich in einem Chart
- Program-Target Overlays in Charts für Soll-Ist-Vergleich

**Business Rules**:
- Sensor-Daten älter als 30 Tage werden automatisch archiviert
- Normale Bereiche: pH 5.5-6.5, TDS 800-1200ppm
- Warning-Indikatoren bei Werten außerhalb der Zielbereiche
- Charts müssen auch bei 1000+ Datenpunkten flüssig funktionieren

**Acceptance Criteria**:
- [ ] Live-Werte aktualisieren sich alle 10 Sekunden
- [ ] Historische Charts laden innerhalb 3 Sekunden
- [ ] Zeitraum-Auswahl funktioniert korrekt
- [ ] Warning-Indikatoren bei kritischen Werten
- [ ] Export-Funktion für Sensor-Daten (CSV)

## F-004: Wachstumsprogramm Template-Editor
**Beschreibung**: Intuitiver Editor zur Erstellung eigener Wachstumsprogramme mit Multi-Phasen Support
**Priorität**: Must-Have (MVP)

**Funktionale Anforderungen**:
- Visueller Phasen-Editor mit Drag & Drop Timeline
- Definition von Phasen: Name, Dauer, pH/TDS-Zielbereich, Nährstoffverhältnisse
- Pump-Zyklen Konfiguration (Wasser/Luft) mit Intervall und Laufzeit
- Template-Vorschau mit visueller Timeline
- Template-Speicherung in eigener Bibliothek

**Business Rules**:
- Maximum 10 Phasen pro Template
- Phasen-Dauer zwischen 1-90 Tagen
- pH-Bereich zwischen 4.0-8.5
- TDS-Bereich zwischen 100-2000ppm
- Template-Namen müssen eindeutig sein

**Acceptance Criteria**:
- [ ] Phasen können visuell erstellt und bearbeitet werden
- [ ] Template-Validierung mit Fehlermeldungen
- [ ] Template-Vorschau zeigt alle Phasen korrekt an
- [ ] Speichern und Laden von Templates funktioniert
- [ ] Clone & Modify Funktion für bestehende Templates

## F-005: Program Instance Management
**Beschreibung**: Starten, Überwachen und Verwalten von aktiven Wachstumsprogrammen
**Priorität**: Must-Have (MVP)

**Funktionale Anforderungen**:
- Starten von Program-Instances basierend auf Templates
- Live-Monitoring des Program-Fortschritts mit aktueller Phase
- Anzeige von Target vs. Ist-Werten
- Vollständiges Action-Log aller Automatisierungs-Aktionen
- Program pausieren/fortsetzen/stoppen Funktionen

**Business Rules**:
- Pro Gerät kann nur ein Programm gleichzeitig aktiv sein
- Program-Logs werden für die gesamte Laufzeit gespeichert
- Automatische Phasen-Übergänge basierend auf Zeitplan
- Program-Pause bei kritischen Sensor-Werten

**Acceptance Criteria**:
- [ ] Program kann von Template gestartet werden
- [ ] Aktueller Fortschritt ist sichtbar
- [ ] Action-Log zeigt alle Automatisierungs-Aktionen
- [ ] Pause/Resume/Stop Funktionen arbeiten korrekt
- [ ] Performance-Metriken werden angezeigt

## F-006: Automatisierung Engine
**Beschreibung**: Intelligente Automatisierung für pH/TDS-Korrekturen und Pump-Zyklen
**Priorität**: Must-Have (MVP)

**Funktionale Anforderungen**:
- Kontinuierliche pH-Überwachung mit automatischer Korrektur
- TDS-Management mit phasenspezifischen Nährstoffmischungen
- Zeitbasierte Wasser- und Luft-Pump-Zyklen
- Safety-Features mit Emergency Stop bei kritischen Werten
- Intelligente Wartezeiten zwischen Korrekturen

**Business Rules**:
- Emergency Stop bei pH < 4.0 oder > 8.5
- Emergency Stop bei TDS > 2000ppm
- Maximale Pumpen-Laufzeit 5 Minuten als Schutz
- Mindestens 10 Minuten Wartezeit zwischen pH-Korrekturen
- Konfigurierbare Cooldowns zwischen Aktionen

**Acceptance Criteria**:
- [ ] Automatische pH-Korrektur funktioniert korrekt
- [ ] TDS-Anpassungen erfolgen phasenspezifisch
- [ ] Safety-Stops bei kritischen Werten
- [ ] Pump-Zyklen laufen nach Programm-Zeitplan
- [ ] Alle Aktionen werden protokolliert

## F-007: Manuelle Pumpensteuerung
**Beschreibung**: Direkte manuelle Kontrolle über alle Pumpen und Aktoren
**Priorität**: Must-Have (MVP)

**Funktionale Anforderungen**:
- Einzelsteuerung aller Pumpen (Wasser, Luft, pH-Down, pH-Up, Nutrient A/B, Cal-Mag)
- Einstellbare Laufzeit von 1 Sekunde bis 5 Minuten
- Emergency-Stop Button für alle Pumpen
- Live-Feedback während Pumpen-Aktivierung
- Test-Modi für Sensor-Kalibrierung

**Business Rules**:
- Manuelle Aktionen pausieren automatische Programme
- Maximale Laufzeit 5 Minuten als Sicherheitsschutz
- Alle manuellen Aktionen werden geloggt
- Emergency Stop stoppt alle Pumpen sofort

**Acceptance Criteria**:
- [ ] Alle Pumpen können einzeln gesteuert werden
- [ ] Laufzeit-Einstellung funktioniert korrekt
- [ ] Emergency Stop stoppt alle Aktionen sofort
- [ ] Live-Feedback während Aktionen
- [ ] Automatische Program-Pause bei manuellen Eingriffen

## F-008: Mobile Progressive Web App
**Beschreibung**: Mobile-optimierte PWA mit Offline-Funktionalität und Push-Benachrichtigungen
**Priorität**: Should-Have

**Funktionale Anforderungen**:
- PWA-Installation auf mobilen Geräten
- Responsive Design für alle Bildschirmgrößen
- Touch-optimierte Bedienung mit großen Buttons
- Offline-Funktionalität für kritische Features
- Push-Benachrichtigungen für Alerts

**Business Rules**:
- App muss auf iOS und Android installierbar sein
- Offline-Modus mindestens für Status-Anzeige und Emergency Stop
- Push-Benachrichtigungen nur bei Critical/Warning Alerts
- Mindestens 60fps Performance auf mobilen Geräten

**Acceptance Criteria**:
- [ ] PWA-Installation funktioniert auf iOS/Android
- [ ] Responsive Design auf allen Bildschirmgrößen
- [ ] Touch-Bedienung ist intuitiv und reaktionsschnell
- [ ] Offline-Funktionen arbeiten korrekt
- [ ] Push-Benachrichtigungen werden korrekt zugestellt

## F-009: Alert & Notification System
**Beschreibung**: Umfassendes Benachrichtigungssystem für verschiedene Event-Typen
**Priorität**: Should-Have

**Funktionale Anforderungen**:
- 4 Alert-Typen: Critical, Warning, Info, System
- Multiple Benachrichtigungskanäle: In-App, Browser Push, Email
- Konfigurierbare Alert-Thresholds
- Alert-Historie und Status-Tracking
- Benachrichtigungs-Präferenzen pro Alert-Typ

**Business Rules**:
- Critical Alerts pausieren automatisch Programme
- Warning Alerts bei 10% Abweichung von Targets
- Info Alerts für erfolgreiche Automatisierungs-Aktionen
- System Alerts bei Device Status-Änderungen

**Acceptance Criteria**:
- [ ] Alle Alert-Typen werden korrekt generiert
- [ ] Benachrichtigungskanäle funktionieren zuverlässig
- [ ] Alert-Konfiguration ist benutzerfreundlich
- [ ] Alert-Historie ist vollständig und durchsuchbar
- [ ] Email-Benachrichtigungen kommen zeitnah an

## F-010: System Settings & Configuration
**Beschreibung**: Umfassende Konfigurationsmöglichkeiten für System und Benutzer-Präferenzen
**Priorität**: Should-Have

**Funktionale Anforderungen**:
- Theme-Wechsel zwischen Dark/Light Mode
- Safety-Limits Konfiguration (pH, TDS, Pump-Laufzeiten)
- Data Retention Einstellungen
- Automatisches Backup konfigurieren
- System-Export/Import Funktionen

**Business Rules**:
- Theme-Einstellungen werden im Browser gespeichert
- Safety-Limits können nicht unter Mindestschutz-Werte gesetzt werden
- Data Retention minimum 7 Tage, maximum 365 Tage
- Backup-Intervall zwischen täglich und monatlich

**Acceptance Criteria**:
- [ ] Theme-Wechsel funktioniert sofort ohne Reload
- [ ] Safety-Limits werden korrekt validiert und angewendet
- [ ] Data Retention Settings werden korrekt umgesetzt
- [ ] Backup-Funktionen arbeiten zuverlässig
- [ ] Export/Import von Konfigurationen funktioniert

## Performance Anforderungen

### Response Times
- **Dashboard Load**: < 2 Sekunden
- **Live Updates**: < 500ms Latency
- **Chart Rendering**: < 1 Sekunde
- **API Responses**: < 1 Sekunde
- **Program Actions**: < 5 Sekunden von Trigger bis Ausführung

### Scalability
- **Geräte**: Bis zu 50 ESP32-Clients gleichzeitig
- **Sensor-Readings**: 100.000 pro Tag
- **Program-Actions**: 1.000 pro Tag
- **Parallele Program-Instances**: 100
- **Uptime**: 24/7 Betrieb ohne Neustart

### Browser Support
- **Chrome**: Version 90+
- **Firefox**: Version 88+
- **Safari**: Version 14+
- **Edge**: Version 90+
- **Mobile Browsers**: iOS Safari 14+, Chrome Mobile 90+

## Integration Requirements

### Umbrel Dependencies
- **Eclipse Mosquitto**: MQTT-Kommunikation mit ESP32-Clients
- **Bitsperity MongoDB**: Persistente Datenspeicherung
- **Bitsperity Beacon**: Service Discovery für ESP32-Clients

### External APIs
- **MQTT Protocol**: v3.1.1 für Device-Kommunikation
- **WebSocket**: Real-time Updates im Frontend
- **REST API**: v1 für Frontend-Backend Kommunikation 