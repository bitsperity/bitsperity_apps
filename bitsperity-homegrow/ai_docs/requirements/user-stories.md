# HomeGrow v3 - User Stories

## Primary User: Hobby-Gärtner mit hydroponischen Systemen

### Epic 1: Device Management
**Als** hydroponischer Gärtner  
**möchte ich** meine ESP32-basierten Clients zentral verwalten  
**damit** ich mein gesamtes Grow-Setup effizient überwachen und steuern kann

#### User Stories:
- **US-001**: Als Benutzer möchte ich alle verbundenen Geräte in einem Dashboard sehen, damit ich einen Überblick über mein System habe
- **US-002**: Als Benutzer möchte ich neue ESP32-Clients automatisch erkennen lassen, damit ich sie einfach hinzufügen kann
- **US-003**: Als Benutzer möchte ich den Online/Offline-Status meiner Geräte sehen, damit ich Probleme schnell identifizieren kann
- **US-004**: Als Benutzer möchte ich Sensoren und Pumpen pro Gerät konfigurieren können, damit ich mein Setup anpassen kann
- **US-005**: Als Benutzer möchte ich manuelle Geräte-Registrierung durchführen können, falls automatische Erkennung fehlschlägt

### Epic 2: Sensor Monitoring
**Als** hydroponischer Gärtner  
**möchte ich** Sensor-Daten in Echtzeit überwachen  
**damit** ich optimale Wachstumsbedingungen sicherstellen kann

#### User Stories:
- **US-006**: Als Benutzer möchte ich live pH-Werte anzeigen lassen, damit ich die Nährlösung überwachen kann
- **US-007**: Als Benutzer möchte ich live TDS/EC-Werte sehen, damit ich die Nährstoffkonzentration verfolgen kann
- **US-008**: Als Benutzer möchte ich historische Datenvisualisierung mit Charts sehen, damit ich Trends analysieren kann
- **US-009**: Als Benutzer möchte ich verschiedene Zeiträume auswählen können (1h, 6h, 24h, 7d, 30d), damit ich unterschiedliche Analyse-Perspektiven habe
- **US-010**: Als Benutzer möchte ich Sensor-Daten exportieren können (CSV), damit ich externe Analysen durchführen kann

### Epic 3: Wachstumsprogramme & Automatisierung
**Als** hydroponischer Gärtner  
**möchte ich** vollautomatische Wachstumsprogramme erstellen und verwenden  
**damit** ich optimale Ergebnisse ohne ständige manuelle Eingriffe erzielen kann

#### User Stories:
- **US-011**: Als Benutzer möchte ich eigene Wachstumsprogramme mit einem Template-Editor erstellen, damit ich meine individuellen Anbaumethoden umsetzen kann
- **US-012**: Als Benutzer möchte ich Multi-Phasen-Programme definieren (Setzling, Wachstum, Blüte), damit ich phasenspezifische Bedingungen festlegen kann
- **US-013**: Als Benutzer möchte ich automatische pH/TDS-Korrekturen basierend auf Phasen-Targets, damit das System selbstständig optimiert
- **US-014**: Als Benutzer möchte ich zeitbasierte Pump-Zyklen (Wasser/Luft) programmieren, damit die Bewässerung automatisiert wird
- **US-015**: Als Benutzer möchte ich Template-Bibliothek mit Starter-Templates nutzen (Salat, Kräuter, Tomaten), damit ich schnell beginnen kann
- **US-016**: Als Benutzer möchte ich Templates klonen und anpassen können, damit ich auf bewährten Programmen aufbauen kann
- **US-017**: Als Benutzer möchte ich laufende Programme überwachen und den Fortschritt verfolgen, damit ich den Status verstehe

### Epic 4: Manuelle Steuerung
**Als** hydroponischer Gärtner  
**möchte ich** direkte manuelle Kontrolle über alle Aktoren haben  
**damit** ich bei Bedarf sofort eingreifen oder Tests durchführen kann

#### User Stories:
- **US-018**: Als Benutzer möchte ich alle Pumpen einzeln aktivieren können (Wasser, Luft, pH-Down, pH-Up, Nutrient A/B, Cal-Mag), damit ich gezielte Aktionen ausführen kann
- **US-019**: Als Benutzer möchte ich die Laufzeit für Pumpen einstellen können (1s bis 5min), damit ich die Dosierung kontrollieren kann
- **US-020**: Als Benutzer möchte ich einen Emergency-Stop Button haben, damit ich alle Systeme sofort stoppen kann
- **US-021**: Als Benutzer möchte ich Test-Funktionen für alle Aktoren nutzen, damit ich die Funktionalität überprüfen kann
- **US-022**: Als Benutzer möchte ich Sensoren kalibrieren können, damit ich genaue Messwerte erhalte

### Epic 5: Mobile & Real-time Features
**Als** hydroponischer Gärtner  
**möchte ich** mein System von überall mobil überwachen und steuern  
**damit** ich flexibel und reaktionsfähig bleiben kann

#### User Stories:
- **US-023**: Als Benutzer möchte ich die App als PWA auf meinem Smartphone installieren, damit ich native App-Erfahrung habe
- **US-024**: Als Benutzer möchte ich Push-Benachrichtigungen bei kritischen Events erhalten, damit ich sofort reagieren kann
- **US-025**: Als Benutzer möchte ich Live-Updates alle 10 Sekunden für Sensordaten, damit ich aktuelle Werte sehe
- **US-026**: Als Benutzer möchte ich Offline-Funktionalität für kritische Features, damit ich auch ohne Internet grundlegende Kontrolle habe
- **US-027**: Als Benutzer möchte ich Touch-optimierte Bedienung auf mobilen Geräten, damit die Nutzung intuitiv ist

### Epic 6: System Management & Settings
**Als** hydroponischer Gärtner  
**möchte ich** das System konfigurieren und verwalten  
**damit** es optimal auf meine Bedürfnisse eingestellt ist

#### User Stories:
- **US-028**: Als Benutzer möchte ich zwischen Dark/Light Mode wechseln können, damit ich die für mich angenehme Darstellung wählen kann
- **US-029**: Als Benutzer möchte ich alle Daten exportieren können, damit ich Backups erstellen kann
- **US-030**: Als Benutzer möchte ich automatische Backup-Funktionen konfigurieren, damit meine Daten sicher sind
- **US-031**: Als Benutzer möchte ich Data Retention Einstellungen verwalten, damit ich Speicherplatz kontrollieren kann
- **US-032**: Als Benutzer möchte ich Safety-Limits konfigurieren können, damit das System sicher operiert

### Epic 7: Alerts & Notifications
**Als** hydroponischer Gärtner  
**möchte ich** über wichtige Ereignisse und Probleme informiert werden  
**damit** ich rechtzeitig reagieren kann

#### User Stories:
- **US-033**: Als Benutzer möchte ich Critical Alerts bei pH/TDS außerhalb Safety-Bereich erhalten, damit Programme pausiert werden
- **US-034**: Als Benutzer möchte ich Warning Alerts bei Sensor-Abweichungen von Program-Targets bekommen, damit ich Anpassungen vornehmen kann
- **US-035**: Als Benutzer möchte ich Info-Notifications bei erfolgreichen Program-Actions erhalten, damit ich den Fortschritt verfolgen kann
- **US-036**: Als Benutzer möchte ich System Alerts bei Device Online/Offline Änderungen bekommen, damit ich über den System-Status informiert bin
- **US-037**: Als Benutzer möchte ich verschiedene Benachrichtigungskanäle konfigurieren können (In-App, Browser Push, Email), damit ich die für mich passende Methode wählen kann

## Secondary Users

### Semi-professionelle Grow-Setups
- Erweiterte Analytics und Reporting Features
- Multi-Device Management (bis zu 50 Geräte)
- Program-Performance Metriken

### Technisch versierte Benutzer
- API-Zugang für eigene Integrationen
- Erweiterte Konfigurationsmöglichkeiten
- Custom Program-Templates

## User Journey: Typischer Arbeitsablauf

### Ersteinrichtung
1. HomeGrow App öffnen
2. Auf "Geräte entdecken" klicken → ESP32-Clients werden automatisch erkannt
3. Geräte bestätigen und benennen
4. Eigenes erstes Programm erstellen oder Starter-Template nutzen

### Tägliche Nutzung
1. Dashboard öffnen → Program-Status prüfen
2. Live-Monitoring → Charts mit Program-Targets vergleichen
3. Program-Logs → Letzte Aktionen überprüfen
4. Bei Anomalien → Program pausieren, manuell korrigieren

### Program-Management
1. Neues Template mit Editor erstellen
2. Phasen visuell definieren (Name, Dauer, Targets)
3. Pump-Zyklen intuitiv konfigurieren
4. Template-Vorschau mit Timeline anzeigen
5. Template in eigener Bibliothek speichern
6. Program-Instance von eigenem Template starten 