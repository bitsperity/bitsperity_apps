# HomeGrow v3 - Acceptance Criteria

## Dashboard (AC-001)

### System Status Cards
- [ ] **AC-001-01**: Dashboard zeigt 4 Status-Karten an: Geräte, Alerts, Programme, Uptime
- [ ] **AC-001-02**: Device-Status-Karte zeigt "X/Y Geräte online" Format
- [ ] **AC-001-03**: Alert-Karte zeigt Anzahl aktiver Alerts mit Farbkodierung (grün=0, gelb=1-5, rot=>5)
- [ ] **AC-001-04**: Programme-Karte zeigt Anzahl aktiver Program-Instances
- [ ] **AC-001-05**: Uptime-Karte zeigt System-Verfügbarkeit in Prozent

### Real-time Updates
- [ ] **AC-001-06**: Status-Karten aktualisieren sich automatisch alle 30 Sekunden
- [ ] **AC-001-07**: Manuelle Aktualisierung über Refresh-Button funktioniert
- [ ] **AC-001-08**: Letzter Aktualisierungszeitpunkt wird angezeigt
- [ ] **AC-001-09**: Loading-Spinner während Aktualisierung sichtbar
- [ ] **AC-001-10**: Error-Meldung bei fehlgeschlagener Aktualisierung

### Device Grid
- [ ] **AC-001-11**: Alle registrierten Geräte werden in Grid-Layout angezeigt
- [ ] **AC-001-12**: Jedes Device zeigt Name, Status und letzte Sensor-Werte
- [ ] **AC-001-13**: Online-Geräte haben grünen Status-Indikator
- [ ] **AC-001-14**: Offline-Geräte haben roten Status-Indikator
- [ ] **AC-001-15**: Klick auf Device-Karte öffnet Detail-Ansicht

### Mobile Responsiveness
- [ ] **AC-001-16**: Dashboard ist auf Smartphones (320px+) nutzbar
- [ ] **AC-001-17**: Status-Karten stapeln sich vertikal auf kleinen Bildschirmen
- [ ] **AC-001-18**: Touch-Navigation funktioniert flüssig
- [ ] **AC-001-19**: Text ist ohne Zoom lesbar
- [ ] **AC-001-20**: Buttons haben mindestens 44px Touch-Target

## Device Discovery (AC-002)

### Automatische Erkennung
- [ ] **AC-002-01**: "Geräte entdecken" Button startet Discovery-Prozess
- [ ] **AC-002-02**: Discovery läuft automatisch beim App-Start
- [ ] **AC-002-03**: Entdeckte Geräte werden in Liste mit Geräteinformationen angezeigt
- [ ] **AC-002-04**: Device-Informationen enthalten: Name, IP, Device-ID, Firmware-Version
- [ ] **AC-002-05**: Discovery-Prozess zeigt Fortschritt oder Loading-Indikator

### Device Registration
- [ ] **AC-002-06**: "Hinzufügen" Button bei jedem entdeckten Gerät verfügbar
- [ ] **AC-002-07**: Ein-Klick-Registrierung fügt Gerät zur Device-Liste hinzu
- [ ] **AC-002-08**: Erfolgsmeldung nach Registrierung angezeigt
- [ ] **AC-002-09**: Doppelte Geräte werden automatisch gefiltert
- [ ] **AC-002-10**: Fehlermeldung bei Registrierungs-Problemen

### Manual Registration
- [ ] **AC-002-11**: "Manuell hinzufügen" Button öffnet Eingabe-Dialog
- [ ] **AC-002-12**: Device-ID und IP-Adresse können manuell eingegeben werden
- [ ] **AC-002-13**: Formular-Validierung für IP-Format und Device-ID
- [ ] **AC-002-14**: Test-Verbindung vor finaler Registrierung möglich
- [ ] **AC-002-15**: Gerät erscheint in Device-Liste nach erfolgreicher manueller Registrierung

## Real-time Monitoring (AC-003)

### Live Sensor Data
- [ ] **AC-003-01**: pH und TDS-Werte aktualisieren sich alle 10 Sekunden
- [ ] **AC-003-02**: Aktuelle Werte sind prominent mit Einheit angezeigt
- [ ] **AC-003-03**: Trend-Indikatoren (↗️↘️↔️) zeigen Änderungsrichtung
- [ ] **AC-003-04**: Warning-Symbole bei Werten außerhalb Normbereich
- [ ] **AC-003-05**: Zeitstempel der letzten Messung angezeigt

### Historical Charts
- [ ] **AC-003-06**: Charts zeigen historische Daten für pH und TDS
- [ ] **AC-003-07**: Zeitraum-Auswahl: 1h, 6h, 24h, 7d, 30d verfügbar
- [ ] **AC-003-08**: Charts laden innerhalb 3 Sekunden
- [ ] **AC-003-09**: Zoom-Funktionalität in Charts funktioniert
- [ ] **AC-003-10**: Tooltip mit exakten Werten beim Hover über Datenpunkte

### Multi-Device Comparison
- [ ] **AC-003-11**: Mehrere Geräte können in einem Chart verglichen werden
- [ ] **AC-003-12**: Farbkodierung unterscheidet verschiedene Geräte
- [ ] **AC-003-13**: Legende zeigt Device-Namen und Farben
- [ ] **AC-003-14**: Charts bleiben performant mit bis zu 5 Geräten
- [ ] **AC-003-15**: Program-Target-Bereiche werden als Overlay angezeigt

### Data Export
- [ ] **AC-003-16**: "Export" Button öffnet Export-Dialog
- [ ] **AC-003-17**: CSV-Format ist auswählbar
- [ ] **AC-003-18**: Zeitraum für Export kann definiert werden
- [ ] **AC-003-19**: Export-Datei wird automatisch heruntergeladen
- [ ] **AC-003-20**: Export-Datei enthält alle relevanten Spalten (Zeitstempel, pH, TDS, Device)

## Program Template Editor (AC-004)

### Template Creation
- [ ] **AC-004-01**: "Neues Template" Button öffnet Editor
- [ ] **AC-004-02**: Template-Name und Beschreibung sind editierbar
- [ ] **AC-004-03**: "Phase hinzufügen" Button erstellt neue Phase
- [ ] **AC-004-04**: Phasen können per Drag & Drop sortiert werden
- [ ] **AC-004-05**: Phase-Löschen mit Bestätigungs-Dialog

### Phase Configuration
- [ ] **AC-004-06**: Phase-Name ist editierbar (max. 50 Zeichen)
- [ ] **AC-004-07**: Phase-Dauer mit Slider von 1-90 Tagen einstellbar
- [ ] **AC-004-08**: pH-Zielbereich mit Min/Max-Slidern (4.0-8.5)
- [ ] **AC-004-09**: TDS-Zielbereich mit Min/Max-Slidern (100-2000ppm)
- [ ] **AC-004-10**: Nährstoffverhältnis summiert sich zu 100%

### Pump Cycles Configuration
- [ ] **AC-004-11**: Wasser-Pump-Intervall einstellbar (5min - 24h)
- [ ] **AC-004-12**: Wasser-Pump-Laufzeit einstellbar (30s - 30min)
- [ ] **AC-004-13**: Luft-Pump-Intervall einstellbar (5min - 24h)
- [ ] **AC-004-14**: Luft-Pump-Laufzeit einstellbar (1min - 60min)
- [ ] **AC-004-15**: Pump-Zeiten werden validiert (Laufzeit < Intervall)

### Template Validation & Preview
- [ ] **AC-004-16**: Template-Validierung zeigt Fehler rot markiert
- [ ] **AC-004-17**: "Vorschau" zeigt Timeline aller Phasen
- [ ] **AC-004-18**: Timeline zeigt Phasen-Namen und Dauer
- [ ] **AC-004-19**: Vorschau zeigt pH/TDS-Bereiche grafisch
- [ ] **AC-004-20**: "Speichern" nur aktiviert bei validem Template

### Template Management
- [ ] **AC-004-21**: Template wird in User-Bibliothek gespeichert
- [ ] **AC-004-22**: Template-Liste zeigt alle gespeicherten Templates
- [ ] **AC-004-23**: "Klonen" erstellt Kopie eines Templates
- [ ] **AC-004-24**: "Bearbeiten" öffnet Template im Editor
- [ ] **AC-004-25**: "Löschen" mit Bestätigungs-Dialog

## Program Instance Management (AC-005)

### Program Starting
- [ ] **AC-005-01**: "Programm starten" öffnet Template-Auswahl
- [ ] **AC-005-02**: Device-Zuordnung ist erforderlich
- [ ] **AC-005-03**: Program startet nach Bestätigung
- [ ] **AC-005-04**: Program-Instance erscheint in aktive Programme Liste
- [ ] **AC-005-05**: Start-Zeitpunkt wird korrekt gespeichert

### Progress Monitoring
- [ ] **AC-005-06**: Aktuelle Phase und Fortschritt sind sichtbar
- [ ] **AC-005-07**: Fortschritts-Balken zeigt Phasen-Completion
- [ ] **AC-005-08**: Tage verbleibend in aktueller Phase angezeigt
- [ ] **AC-005-09**: Gesamtfortschritt des Programms sichtbar
- [ ] **AC-005-10**: Nächster Phasen-Übergang-Zeitpunkt angezeigt

### Target vs Actual Values
- [ ] **AC-005-11**: Aktuelle pH/TDS-Werte neben Ziel-Bereichen angezeigt
- [ ] **AC-005-12**: Farbkodierung: Grün=im Ziel, Gelb=leichte Abweichung, Rot=starke Abweichung
- [ ] **AC-005-13**: Abweichungs-Prozentsatz numerisch angezeigt
- [ ] **AC-005-14**: Trend-Indikatoren zeigen Bewegung zu/weg von Zielen
- [ ] **AC-005-15**: Historie der Ziel-Erreichung über Zeit sichtbar

### Program Control
- [ ] **AC-005-16**: "Pausieren" Button stoppt Automatisierung
- [ ] **AC-005-17**: "Fortsetzen" Button reaktiviert pausierte Programme
- [ ] **AC-005-18**: "Stoppen" Button beendet Programm mit Bestätigung
- [ ] **AC-005-19**: "Phase überspringen" funktioniert mit Warnung
- [ ] **AC-005-20**: Programm-Status wird korrekt in Echtzeit aktualisiert

### Action Logging
- [ ] **AC-005-21**: Vollständiges Log aller Automatisierungs-Aktionen
- [ ] **AC-005-22**: Log-Einträge enthalten: Zeitstempel, Aktion, Trigger-Werte, Ergebnis
- [ ] **AC-005-23**: Log ist chronologisch sortiert (neueste zuerst)
- [ ] **AC-005-24**: Log ist filterbar nach Aktions-Typ
- [ ] **AC-005-25**: Log kann als CSV exportiert werden

## Manual Control (AC-006)

### Pump Control Interface
- [ ] **AC-006-01**: Alle 7 Pumpen sind einzeln steuerbar (Wasser, Luft, pH-Down, pH-Up, Nutrient A/B, Cal-Mag)
- [ ] **AC-006-02**: Laufzeit-Slider von 1 Sekunde bis 5 Minuten
- [ ] **AC-006-03**: "Start" Button aktiviert ausgewählte Pumpe
- [ ] **AC-006-04**: Live-Timer zeigt verbleibende Laufzeit
- [ ] **AC-006-05**: Pumpe stoppt automatisch nach eingestellter Zeit

### Emergency Controls
- [ ] **AC-006-06**: "Emergency Stop" Button ist immer prominent sichtbar
- [ ] **AC-006-07**: Emergency Stop stoppt alle Pumpen sofort
- [ ] **AC-006-08**: Emergency Stop pausiert automatische Programme
- [ ] **AC-006-09**: Emergency-Status wird in UI klar angezeigt
- [ ] **AC-006-10**: Manuelle Freigabe erforderlich nach Emergency Stop

### Safety Features
- [ ] **AC-006-11**: Maximale Laufzeit wird enforced (nicht überschreitbar)
- [ ] **AC-006-12**: Warnung bei gleichzeitiger Aktivierung inkompatibler Pumpen
- [ ] **AC-006-13**: Automatische Programme pausieren bei manuellen Aktionen
- [ ] **AC-006-14**: Countdown-Warnung vor automatischer Wiederaufnahme
- [ ] **AC-006-15**: Alle manuellen Aktionen werden geloggt

### Live Feedback
- [ ] **AC-006-16**: Aktive Pumpen haben visuellen Indikator
- [ ] **AC-006-17**: Sound-Feedback bei Button-Klicks (optional)
- [ ] **AC-006-18**: Erfolgs-/Fehler-Meldungen bei Pump-Aktionen
- [ ] **AC-006-19**: Live-Sensor-Werte während manueller Aktionen
- [ ] **AC-006-20**: Status-Updates in Echtzeit via WebSocket

## Mobile PWA (AC-007)

### PWA Installation
- [ ] **AC-007-01**: Installation-Prompt auf iOS/Android erscheint
- [ ] **AC-007-02**: App kann über Browser-Menü installiert werden
- [ ] **AC-007-03**: Installierte App startet ohne Browser-UI
- [ ] **AC-007-04**: App-Icon erscheint auf Home-Screen
- [ ] **AC-007-05**: Splash-Screen beim App-Start angezeigt

### Responsive Design
- [ ] **AC-007-06**: Layout passt sich automatisch an Bildschirmgröße an
- [ ] **AC-007-07**: Navigation ist auf kleinen Bildschirmen zugänglich
- [ ] **AC-007-08**: Text ist ohne Zoom lesbar (min. 16px)
- [ ] **AC-007-09**: Touch-Targets sind mindestens 44x44px
- [ ] **AC-007-10**: Horizontales Scrollen ist vermieden

### Touch Optimization
- [ ] **AC-007-11**: Touch-Gesten (Swipe, Pinch-Zoom) funktionieren
- [ ] **AC-007-12**: Button-Feedback bei Touch-Events
- [ ] **AC-007-13**: Smooth-Scrolling in Listen und Charts
- [ ] **AC-007-14**: Pull-to-Refresh Geste aktualisiert Daten
- [ ] **AC-007-15**: Keine ungewollten Zoom-Effekte bei Doppel-Tap

### Offline Functionality
- [ ] **AC-007-16**: Cached Dashboard ist offline verfügbar
- [ ] **AC-007-17**: Emergency Stop funktioniert offline
- [ ] **AC-007-18**: Offline-Indikator wird angezeigt
- [ ] **AC-007-19**: Daten synchronisieren sich bei Reconnect
- [ ] **AC-007-20**: Offline-Modus zeigt letzte bekannte Daten

### Push Notifications
- [ ] **AC-007-21**: Notification-Permission wird korrekt angefragt
- [ ] **AC-007-22**: Critical Alerts werden als Push-Notification gesendet
- [ ] **AC-007-23**: Notifications enthalten relevante Details
- [ ] **AC-007-24**: Tap auf Notification öffnet relevante App-Sektion
- [ ] **AC-007-25**: Notification-Präferenzen sind konfigurierbar

## System Settings (AC-008)

### Theme Management
- [ ] **AC-008-01**: Theme-Toggle zwischen Light/Dark Mode verfügbar
- [ ] **AC-008-02**: Theme-Wechsel erfolgt sofort ohne Page-Reload
- [ ] **AC-008-03**: Theme-Präferenz wird persistent gespeichert
- [ ] **AC-008-04**: System-Theme wird automatisch erkannt (Auto-Mode)
- [ ] **AC-008-05**: Alle UI-Komponenten respektieren gewähltes Theme

### Safety Limits Configuration
- [ ] **AC-008-06**: pH-Limits für Emergency Stop einstellbar (4.0-8.5)
- [ ] **AC-008-07**: TDS-Limit für Emergency Stop einstellbar (max 5000ppm)
- [ ] **AC-008-08**: Maximale Pump-Laufzeiten konfigurierbar
- [ ] **AC-008-09**: Wartezeiten zwischen Korrekturen einstellbar
- [ ] **AC-008-10**: Safety-Limits werden validiert und enforced

### Data Management
- [ ] **AC-008-11**: Data Retention Periode einstellbar (7-365 Tage)
- [ ] **AC-008-12**: Automatisches Backup konfigurierbar (täglich/wöchentlich/monatlich)
- [ ] **AC-008-13**: "Daten exportieren" lädt komplettes System-Backup herunter
- [ ] **AC-008-14**: "Daten löschen" mit doppelter Bestätigung
- [ ] **AC-008-15**: Import von Backup-Dateien möglich

### System Information
- [ ] **AC-008-16**: App-Version und Build-Datum angezeigt
- [ ] **AC-008-17**: System-Status und Uptime sichtbar
- [ ] **AC-008-18**: Verbindungs-Status zu Umbrel-Services angezeigt
- [ ] **AC-008-19**: Speicherverbrauch und Performance-Metriken
- [ ] **AC-008-20**: Debug-Informationen für Support verfügbar

## Alert System (AC-009)

### Alert Generation
- [ ] **AC-009-01**: Critical Alerts werden bei pH < 4.0 oder > 8.5 generiert
- [ ] **AC-009-02**: Critical Alerts werden bei TDS > 2000ppm generiert
- [ ] **AC-009-03**: Warning Alerts bei 10% Abweichung von Program-Targets
- [ ] **AC-009-04**: Info Alerts bei erfolgreichen Automatisierungs-Aktionen
- [ ] **AC-009-05**: System Alerts bei Device Online/Offline Änderungen

### Alert Display
- [ ] **AC-009-06**: Alert-Counter in Navigation zeigt aktive Alerts
- [ ] **AC-009-07**: Alert-Liste zeigt alle Alerts chronologisch
- [ ] **AC-009-08**: Alert-Details enthalten: Typ, Zeitstempel, Beschreibung, Gerät
- [ ] **AC-009-09**: Farbkodierung: Rot=Critical, Gelb=Warning, Blau=Info, Grau=System
- [ ] **AC-009-10**: "Gelesen markieren" und "Alle löschen" Funktionen

### Notification Delivery
- [ ] **AC-009-11**: In-App Toast-Notifications für alle Alert-Typen
- [ ] **AC-009-12**: Browser-Push für Critical und Warning Alerts
- [ ] **AC-009-13**: Email-Notifications für Critical Alerts (falls konfiguriert)
- [ ] **AC-009-14**: Notification-Inhalt ist aussagekräftig und handlungsrelevant
- [ ] **AC-009-15**: Rate-Limiting verhindert Notification-Spam

### Alert Configuration
- [ ] **AC-009-16**: Alert-Thresholds sind pro Alert-Typ konfigurierbar
- [ ] **AC-009-17**: Notification-Kanäle können pro Alert-Typ ein/ausgeschaltet werden
- [ ] **AC-009-18**: Email-Adresse für Notifications konfigurierbar
- [ ] **AC-009-19**: Quiet-Hours für Notifications einstellbar
- [ ] **AC-009-20**: Test-Notifications können ausgelöst werden

## Performance Criteria (AC-010)

### Response Times
- [ ] **AC-010-01**: Dashboard lädt innerhalb 2 Sekunden
- [ ] **AC-010-02**: API-Responses erfolgen innerhalb 1 Sekunde
- [ ] **AC-010-03**: Chart-Rendering dauert maximal 1 Sekunde
- [ ] **AC-010-04**: WebSocket-Updates haben <500ms Latenz
- [ ] **AC-010-05**: Program-Aktionen werden innerhalb 5 Sekunden ausgeführt

### Scalability Limits
- [ ] **AC-010-06**: System unterstützt bis zu 50 gleichzeitige Geräte
- [ ] **AC-010-07**: 100.000 Sensor-Readings pro Tag ohne Performance-Einbußen
- [ ] **AC-010-08**: 1.000 Program-Actions pro Tag verarbeitbar
- [ ] **AC-010-09**: 100 parallele Program-Instances unterstützt
- [ ] **AC-010-10**: 24/7 Betrieb ohne Neustart erforderlich

### Mobile Performance
- [ ] **AC-010-11**: Mindestens 60fps bei Animationen auf mobilen Geräten
- [ ] **AC-010-12**: App-Start in unter 3 Sekunden auf Mobilgeräten
- [ ] **AC-010-13**: Smooth-Scrolling ohne Ruckeln
- [ ] **AC-010-14**: Touch-Response-Zeit unter 100ms
- [ ] **AC-010-15**: Memory-Usage unter 256MB auf mobilen Geräten

### Browser Compatibility
- [ ] **AC-010-16**: Chrome 90+ vollständig unterstützt
- [ ] **AC-010-17**: Firefox 88+ vollständig unterstützt  
- [ ] **AC-010-18**: Safari 14+ vollständig unterstützt
- [ ] **AC-010-19**: Edge 90+ vollständig unterstützt
- [ ] **AC-010-20**: Mobile Browser (iOS Safari 14+, Chrome Mobile 90+) vollständig unterstützt 