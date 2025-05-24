#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import time
import threading

from .logger import get_logger
from .database import get_database
from .program_manager import get_program_manager
from .nutrient_calculator import NutrientCalculator
from .mqtt_client import MQTTClient
from .device_manager import get_device_manager
from .models.program_instance import ProgramInstance
from .models.program_template import ProgramTemplate

logger = get_logger(__name__)

class ProgramEngine:
    """
    Die ProgramEngine führt aktive Programminstanzen aus und reagiert
    auf Sensorwerte, um die entsprechenden Aktionen auszuführen.
    
    Sie läuft in einem eigenen Thread und überprüft periodisch alle aktiven Programme.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """Singleton-Pattern für die ProgramEngine"""
        if cls._instance is None:
            cls._instance = super(ProgramEngine, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, mqtt_client: MQTTClient = None):
        """
        Initialisiert die ProgramEngine
        
        Args:
            mqtt_client: MQTT-Client für die Kommunikation mit den Geräten
        """
        if self._initialized:
            return
            
        self.mqtt_client = mqtt_client
        self.db = get_database()
        self.program_manager = get_program_manager()
        self.device_manager = get_device_manager()
        
        # Letzte bekannte Sensorwerte für schnellen Zugriff
        self.latest_sensor_data = {}  # dict: {device_id: {sensor_type: value}}
        
        # Lokaler Cache für Gerätekonfigurationen
        self.device_config_cache = {}  # dict: {device_id: config}
        
        # Zeitstempel der letzten Aktualisierung pro Gerät und Aktion
        self.last_action_time = {}  # dict: {device_id: {action_type: timestamp}}
        
        # Mindestwartezeit zwischen Aktionen (Sekunden)
        self.min_wait_time = {
            'ph_up': 1800,       # 30 Minuten zwischen pH-Up-Aktionen
            'ph_down': 1800,     # 30 Minuten zwischen pH-Down-Aktionen
            'nutrients': 1800,  # 30 Minuten zwischen Nährstoffaktionen
        }
        
        # Maximales Alter für Sensordaten (Sekunden)
        self.max_sensor_age = 60  # 60 Sekunden - guter Kompromiss zwischen Aktualität und Systemlast
        
        # Zustand für die Pumpensteuerung pro Instanz
        # Format: {instance_id: {pump_type: {'last_start': datetime, 'next_start': datetime}}}
        self.pump_control_state = {}
        
        # Flag für laufenden Thread
        self.running = False
        self.thread = None
        
        # Registriere Callback für Konfigurationsantworten
        if self.mqtt_client:
            self.mqtt_client.register_config_response_callback(self._handle_config_response)
            logger.info("MQTT-Callback für Konfigurationsantworten registriert")
        
        self._initialized = True
        logger.info("ProgramEngine initialisiert")
    
    def start(self):
        """Startet die ProgramEngine in einem separaten Thread"""
        if self.running:
            logger.warning("ProgramEngine läuft bereits")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("ProgramEngine gestartet")
    
    def stop(self):
        """Stoppt die ProgramEngine"""
        if not self.running:
            logger.warning("ProgramEngine läuft nicht")
            return
            
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)  # Warte maximal 5 Sekunden
            self.thread = None
            
        # Optional: Reset pump state on stop? Probably better to keep it for next start
        # self.pump_control_state = {}
        logger.info("ProgramEngine gestoppt")
    
    def _run(self):
        """Hauptschleife der ProgramEngine"""
        check_counter = 0
        
        # Initiales Delay beim Programmstart, um dem Client Zeit zum Initialisieren zu geben
        logger.info("Warte 30 Sekunden, bevor die Prüfung der aktiven Programme beginnt...")
        time.sleep(30)
        logger.info("Beginne mit der Prüfung der aktiven Programme")
        
        while self.running:
            try:
                # Verarbeite aktive Programme
                self._process_active_programs()
                
                # Warte etwas länger zwischen den Checks
                time.sleep(30)  # Prüfe alle 30 Sekunden statt 10
                
                # Zähle die Durchläufe
                check_counter += 1
                # Logge nur jeden 10. Durchlauf (alle 5 Minuten) einen Statusbericht
                if check_counter % 10 == 0:
                    logger.info(f"ProgramEngine aktiv: {check_counter} Prüfungen durchgeführt")
                
            except Exception as e:
                logger.error(f"Fehler in ProgramEngine-Schleife: {e}")
                time.sleep(60)  # Bei Fehler längere Pause
    
    def _process_active_programs(self):
        """Verarbeitet alle aktiven Programme"""
        # Hole alle aktiven Programminstanzen
        active_program_instances = self._get_all_active_program_instances()
        
        if not active_program_instances:
            logger.debug("Keine aktiven Programminstanzen gefunden")
            return
            
        logger.debug(f"Verarbeite {len(active_program_instances)} aktive Programminstanzen")
        
        for instance in active_program_instances:
            try:
                # Nur laufende Programme verarbeiten (nicht pausierte)
                if instance.status == ProgramInstance.STATUS_RUNNING:
                    self._process_program_instance(instance)
            except Exception as e:
                logger.error(f"Fehler bei Verarbeitung von Programm {instance.instance_id}: {e}")
    
    def _get_all_active_program_instances(self) -> List[ProgramInstance]:
        """
        Holt alle aktiven Programminstanzen aus der Datenbank
        
        Returns:
            Liste aller aktiven ProgramInstance-Objekte
        """
        # Rufe direkt die Datenbank für bessere Performance ab
        active_instances_data = list(self.db.db.program_instances.find({
            "status": {"$in": [ProgramInstance.STATUS_RUNNING, ProgramInstance.STATUS_PAUSED]}
        }))
        
        logger.info(f"Gefundene aktive Programminstanzen: {len(active_instances_data)}")
        
        active_instances = []
        for instance_data in active_instances_data:
            # Lade die zugehörige Vorlage für jede aktive Instanz
            template = None
            if template_id := instance_data.get('template_id'):
                logger.info(f"Lade Template für Instanz {instance_data.get('instance_id')} mit Template-ID {template_id}")
                template_data = self.db.get_program_template(template_id)
                if template_data:
                    logger.info(f"Template gefunden: {template_data.get('name')}, Phasen: {len(template_data.get('phases', []))}")
                    template = ProgramTemplate.from_dict(template_data)
                else:
                    logger.error(f"Template mit ID {template_id} nicht gefunden für Instanz {instance_data.get('instance_id')}")
            
            # Erstelle Instanz-Objekt
            instance = ProgramInstance.from_dict(instance_data, template)
            
            # Prüfe, ob das Template korrekt geladen wurde
            if not instance.template:
                logger.error(f"Template nicht korrekt mit Instanz {instance.instance_id} verknüpft!")
            else:
                logger.info(f"Instanz {instance.instance_id} hat {len(instance.template.phases)} Phasen")
                
                # Prüfe, ob die aktuelle Phase existiert und die Pumpenzyklus-Werte enthält
                current_phase = instance.get_current_phase()
                if current_phase:
                    logger.info(f"Current phase: {current_phase}")
                    logger.info(f"Aktuelle Phase für Instanz {instance.instance_id}: {current_phase.get('name')}")
                    for key in ['water_pump_cycle_minutes', 'water_pump_on_minutes', 'air_pump_cycle_minutes', 'air_pump_on_minutes']:
                        logger.info(f"  - {key}: {current_phase.get(key, 'Nicht vorhanden!')}")
                else:
                    logger.error(f"Keine aktuelle Phase für Instanz {instance.instance_id} gefunden!")
                
            active_instances.append(instance)
        
        return active_instances
    
    def _process_program_instance(self, instance: ProgramInstance):
        """
        Verarbeitet eine einzelne Programminstanz
        
        Args:
            instance: Zu verarbeitende ProgramInstance
        """
        device_id = instance.device_id
        
        # Prüfe zuerst, ob das Gerät online ist
        device = self.device_manager.get_device(device_id)
        if not device or not device.online:
            # Nur ein DEBUG-Log, wenn das Gerät offline ist, um die Log-Dateien nicht zu überfüllen
            logger.debug(f"Programm für Gerät {device_id} wird übersprungen - Gerät ist offline")
            return
        
        # Dynamische Phasenberechnung
        if not instance.template or not instance.template.phases:
            logger.error(f"Keine Vorlage/Phasen für Programm {instance.instance_id}")
            return
        phase_idx = self._get_current_phase_index(instance.started_at, [p.to_dict() for p in instance.template.phases])
        current_phase = instance.template.phases[phase_idx].to_dict()
        logger.info(f"Berechnete aktuelle Phase für Instanz {instance.instance_id}: {current_phase.get('name')} (Index {phase_idx})")

        # Prüfe, ob ein Phasenwechsel stattgefunden hat (letzter Log-Eintrag)
        last_phase_idx = None
        for log_entry in reversed(instance.log):
            if log_entry.action == "phase_changed":
                last_phase_idx = log_entry.data.get("to_phase")
                break
        if last_phase_idx is None:
            # Finde initiale Phase aus erstem Log oder setze auf 0
            last_phase_idx = 0
        if phase_idx != last_phase_idx:
            self.program_manager.add_program_instance_log(
                instance.instance_id,
                "phase_changed",
                {"from_phase": last_phase_idx, "to_phase": phase_idx}
            )
            logger.info(f"Phasenwechsel geloggt: {last_phase_idx} → {phase_idx} für Instanz {instance.instance_id}")
        
        # Hole aktuelle Sensorwerte
        ph_value = self._get_latest_sensor_value(device_id, 'ph')
        tds_value = self._get_latest_sensor_value(device_id, 'tds')
        
        if ph_value is None and tds_value is None:
            logger.warning(f"Keine gültigen Sensorwerte für Gerät {device_id} - Sensordaten wahrscheinlich veraltet")
            return
        
        if ph_value is None:
            logger.warning(f"Kein gültiger pH-Wert für Gerät {device_id} - pH-Korrekturen nicht möglich")
        else:
            # Logge Sensor-Messung
            self._log_sensor_reading(instance, 'ph', ph_value)
        
        if tds_value is None:
            logger.warning(f"Kein gültiger TDS-Wert für Gerät {device_id} - Nährstoffkorrekturen nicht möglich")
        else:
            # Logge Sensor-Messung
            self._log_sensor_reading(instance, 'tds', tds_value)
        
        # Wenn beide Werte fehlen, wurde bereits früher abgebrochen
        
        # Prüfe auf Konfiguration im Cache, sonst aus Datenbank holen
        device_config = self._get_device_config(device_id)
        
        # Verarbeite pH-Wert falls vorhanden
        if ph_value is not None:
            self._process_ph_value(instance, device_config, ph_value, current_phase)
        
        # Verarbeite TDS-Wert falls vorhanden
        if tds_value is not None:
            self._process_tds_value(instance, device_config, tds_value, current_phase)
            
        # Verarbeite Pumpenzyklen
        self._process_pump_cycles(instance, current_phase)
    
    def _log_sensor_reading(self, instance: ProgramInstance, sensor_type: str, value: float):
        """
        Protokolliert eine Sensormessung in der Programminstanz
        
        Args:
            instance: Programminstanz
            sensor_type: Art des Sensors ('ph' oder 'tds')
            value: Gemessener Wert
        """
        # Prüfe, ob seit der letzten Protokollierung genügend Zeit vergangen ist
        # (Wir wollen nicht jede Messung protokollieren, sondern nur alle 15 Minuten)
        last_log_time = self._get_last_sensor_log_time(instance.instance_id, sensor_type)
        now = datetime.utcnow()
        
        if last_log_time and (now - last_log_time).total_seconds() < 900:  # 15 Minuten = 900 Sekunden
            return
            
        # Logge die Messung
        log_data = {
            "sensor": sensor_type,
            "value": value
        }
        
        self.program_manager.add_program_instance_log(
            instance.instance_id, "sensor_reading", log_data
        )
    
    def _get_last_sensor_log_time(self, instance_id: str, sensor_type: str) -> Optional[datetime]:
        """
        Ermittelt den Zeitpunkt der letzten Sensorprotokollierung
        
        Args:
            instance_id: ID der Programminstanz
            sensor_type: Art des Sensors ('ph' oder 'tds')
            
        Returns:
            Zeitpunkt der letzten Protokollierung oder None
        """
        # Hole die Programminstanz
        instance = self.program_manager.get_program_instance(instance_id)
        if not instance or not instance.log:
            return None
            
        # Suche den letzten Logeintrag für diesen Sensortyp
        for log_entry in reversed(instance.log):
            if (log_entry.action == "sensor_reading" and 
                log_entry.data and 
                log_entry.data.get("sensor") == sensor_type):
                return log_entry.timestamp
                
        return None
    
    def _process_ph_value(self, instance: ProgramInstance, config: Dict[str, Any], ph_value: float, phase: Dict[str, Any]):
        """
        Verarbeitet den pH-Wert und führt bei Bedarf Korrekturen durch
        
        Args:
            instance: Programminstanz
            config: Gerätekonfiguration
            ph_value: Aktueller pH-Wert
            phase: Aktuelle Programmphase
        """
        device_id = instance.device_id
        
        # Hole pH-Zielwerte aus der aktuellen Phase
        targets = phase.get('targets', {})
        ph_min = targets.get('ph_min', 5.5)
        ph_max = targets.get('ph_max', 6.5)
        ph_target = ph_min
        
        # Prüfe, ob pH-Wert im Zielbereich liegt
        if ph_min <= ph_value <= ph_max:
            # Reduziere Logging für Werte im Zielbereich auf DEBUG-Level
            logger.debug(f"pH-Wert im Zielbereich: Gerät {device_id}, pH: {ph_value:.2f} (Ziel: {ph_min:.1f}-{ph_max:.1f})")
            return
        
        # Nur alle 5 Minuten einen INFO-Log für Werte außerhalb des Zielbereichs
        device_key = f"{device_id}_ph_warning"
        if self._should_log_warning(device_key):
            logger.info(f"pH-Wert außerhalb des Zielbereichs: Gerät {device_id}, pH: {ph_value:.2f} (Ziel: {ph_min:.1f}-{ph_max:.1f})")
        
        # Erstelle NutrientCalculator
        calculator = NutrientCalculator(config)
        
        # Prüfe, ob pH-Korrektur erforderlich ist
        correction_needed, pump_type, volume_ml = calculator.calculate_ph_correction(
            ph_value, ph_target, ph_target  # NEU: Zielwert als min und max übergeben
        )
        
        if not correction_needed:
            logger.debug(f"Keine pH-Korrektur erforderlich: Gerät {device_id}, pH: {ph_value:.2f}")
            return
        
        # Prüfe Wartezeit seit letzter Aktion
        if not self._check_action_allowed(device_id, pump_type):
            logger.debug(f"pH-Korrektur zurzeit nicht erlaubt: Gerät {device_id}, pH: {ph_value:.2f}")
            return
        
        # Führe pH-Korrektur durch
        self._execute_ph_correction(instance, config, pump_type, volume_ml, ph_value, [ph_min, ph_max])
    
    def _process_tds_value(self, instance: ProgramInstance, config: Dict[str, Any], tds_value: float, phase: Dict[str, Any]):
        """
        Verarbeitet den TDS-Wert und führt bei Bedarf Korrekturen durch
        
        Args:
            instance: Programminstanz
            config: Gerätekonfiguration
            tds_value: Aktueller TDS-Wert
            phase: Aktuelle Programmphase
        """
        device_id = instance.device_id
        
        # Hole TDS-Zielwerte aus der aktuellen Phase
        targets = phase.get('targets', {})
        tds_min = targets.get('tds_min', 500)
        tds_max = targets.get('tds_max', 700)
        tds_target = tds_max
        
        # Prüfe, ob TDS-Wert im Zielbereich liegt
        if tds_min <= tds_value <= tds_max:
            # Reduziere Logging für Werte im Zielbereich auf DEBUG-Level
            logger.debug(f"TDS-Wert im Zielbereich: Gerät {device_id}, TDS: {tds_value:.1f} (Ziel: {tds_min}-{tds_max})")
            return
        
        # Nur alle 5 Minuten einen INFO-Log für Werte außerhalb des Zielbereichs
        device_key = f"{device_id}_tds_warning"
        if self._should_log_warning(device_key):
            logger.info(f"TDS-Wert außerhalb des Zielbereichs: Gerät {device_id}, TDS: {tds_value:.1f} (Ziel: {tds_min}-{tds_max})")
        
        # Hole Nährstoffverhältnis aus der aktuellen Phase
        nutrient_ratio = phase.get('nutrient_ratio', {})
        
        # Erstelle NutrientCalculator
        calculator = NutrientCalculator(config)
        
        # Prüfe, ob Nährstoffkorrektur erforderlich ist
        correction_needed, nutrient_amounts = calculator.calculate_nutrient_amounts(
            tds_value, tds_target, tds_target, nutrient_ratio  # NEU: Zielwert als min und max übergeben
        )
        
        if not correction_needed:
            logger.debug(f"Keine TDS-Korrektur erforderlich: Gerät {device_id}, TDS: {tds_value:.1f}")
            return
        
        # Prüfe Wartezeit seit letzter Aktion
        if not self._check_action_allowed(device_id, 'nutrients'):
            logger.debug(f"TDS-Korrektur zurzeit nicht erlaubt: Gerät {device_id}, TDS: {tds_value:.1f}")
            return
        
        # Führe Nährstoffkorrektur durch
        self._execute_nutrient_correction(instance, config, nutrient_amounts, tds_value, [tds_min, tds_max])
    
    def _should_log_warning(self, key: str) -> bool:
        """
        Prüft, ob eine Warnung geloggt werden sollte (maximal alle 5 Minuten)
        
        Args:
            key: Eindeutiger Schlüssel für die Warnung
            
        Returns:
            True wenn geloggt werden sollte, False sonst
        """
        now = datetime.utcnow()
        
        # Initialisiere das Dictionary, falls noch nicht vorhanden
        if not hasattr(self, '_last_warning_time'):
            self._last_warning_time = {}
        
        # Prüfe, ob für diesen Schlüssel schon ein Eintrag existiert
        last_time = self._last_warning_time.get(key)
        
        # Wenn noch keine Warnung geloggt wurde, erlaube die erste
        if last_time is None:
            self._last_warning_time[key] = now
            return True
        
        # Berechne vergangene Zeit in Sekunden
        elapsed_seconds = (now - last_time).total_seconds()
        
        # Prüfe, ob Mindestwartezeit eingehalten wurde (5 Minuten = 300 Sekunden)
        if elapsed_seconds < 300:
            return False
        
        # Aktualisiere Zeitstempel
        self._last_warning_time[key] = now
        return True
    
    def _check_action_allowed(self, device_id: str, action_type: str) -> bool:
        """
        Prüft, ob eine Aktion basierend auf der Wartezeit erlaubt ist
        Args:
            device_id: ID des Geräts
            action_type: Art der Aktion ('ph_up', 'ph_down', 'nutrients')
        Returns:
            True wenn Aktion erlaubt, False wenn Wartezeit noch nicht abgelaufen
        """
        now = datetime.utcnow()

        # Initialisiere Daten für Gerät, falls noch nicht vorhanden
        if device_id not in self.last_action_time:
            self.last_action_time[device_id] = {}

        # --- NEU: Gemeinsame Wartezeit für pH-Up und pH-Down ---
        if action_type in ['ph_up', 'ph_down']:
            # Gemeinsamer Schlüssel für beide Richtungen
            ph_last_time = self.last_action_time[device_id].get('ph_correction')
            # Hole die konfigurierte Wartezeit direkt aus der Gerätekonfiguration
            device_config = self._get_device_config(device_id)
            wait_times = device_config.get('nutrient_control', {}).get('wait_times', {})
            ph_minutes = wait_times.get('ph_minutes', 0)
            min_wait = int(ph_minutes * 60) if ph_minutes > 0 else self.min_wait_time.get('ph_up', 1800)
            if ph_last_time is None:
                self.last_action_time[device_id]['ph_correction'] = now
                logger.info(f"Erste pH-Korrektur ({action_type}) für Gerät {device_id} erlaubt")
                return True
            elapsed_seconds = (now - ph_last_time).total_seconds()
            if elapsed_seconds < min_wait:
                logger.debug(f"pH-Korrektur ({action_type}) für Gerät {device_id} noch nicht erlaubt (Wartezeit: {min_wait - elapsed_seconds:.0f}s)")
                return False
            self.last_action_time[device_id]['ph_correction'] = now
            logger.info(f"pH-Korrektur ({action_type}) für Gerät {device_id} erlaubt (nach {elapsed_seconds:.0f}s Wartezeit, konfigurierte Wartezeit: {min_wait}s)")
            return True
        # --- ENDE NEU ---

        # Original für andere Aktionen (z.B. nutrients)
        last_time = self.last_action_time[device_id].get(action_type)
        if last_time is None:
            self.last_action_time[device_id][action_type] = now
            logger.info(f"Erste {action_type} Aktion für Gerät {device_id} erlaubt")
            return True
        elapsed_seconds = (now - last_time).total_seconds()
        device_config = self._get_device_config(device_id)
        wait_times = device_config.get('nutrient_control', {}).get('wait_times', {})
        min_wait = 0
        if action_type == 'nutrients':
            nutrient_minutes = wait_times.get('nutrient_minutes', 0)
            min_wait = int(nutrient_minutes * 60) if nutrient_minutes > 0 else 0
        if min_wait <= 0:
            min_wait = self.min_wait_time.get(action_type, 60)
            logger.info(f"Keine gültige Wartezeit für {action_type} in der Konfiguration, verwende Standardwert: {min_wait}s")
        else:
            logger.info(f"Verwende konfigurierte Wartezeit für {action_type}: {min_wait}s")
        if elapsed_seconds < min_wait:
            logger.debug(f"Aktion {action_type} für Gerät {device_id} noch nicht erlaubt (Wartezeit: {min_wait - elapsed_seconds:.0f}s)")
            return False
        self.last_action_time[device_id][action_type] = now
        logger.info(f"Aktion {action_type} für Gerät {device_id} erlaubt (nach {elapsed_seconds:.0f}s Wartezeit, konfigurierte Wartezeit: {min_wait}s)")
        return True
    
    def _execute_ph_correction(self, 
                              instance: ProgramInstance, 
                              config: Dict[str, Any],
                              pump_type: str, 
                              volume_ml: float, 
                              current_value: float, 
                              target_range: List[float]):
        """
        Führt eine pH-Korrektur aus
        
        Args:
            instance: Programminstanz
            config: Gerätekonfiguration
            pump_type: Art der Pumpe ('ph_up' oder 'ph_down')
            volume_ml: Zu pumpendes Volumen in ml
            current_value: Aktueller pH-Wert
            target_range: Zielbereich [min, max]
        """
        if not self.mqtt_client:
            logger.error("Keine MQTT-Client-Verbindung für Pumpensteuerung")
            return
            
        # Prüfe die Geräte-ID
        device_id = instance.device_id
        template_id = instance.template_id
        instance_id = instance.instance_id
        
        logger.info(f"Sende pH-Korrektur: Instanz {instance_id}, Template {template_id}, Gerät {device_id}")
        
        # Erstelle NutrientCalculator für Pumpdauer
        calculator = NutrientCalculator(config)
        
        # Berechne Pumpenzeit in Millisekunden
        duration_ms = calculator.ml_to_pump_duration(pump_type, volume_ml)
        if duration_ms <= 0:
            logger.warning(f"Ungültige Pumpendauer berechnet: {duration_ms} ms für {volume_ml} ml")
            return
        
        # Mappe den Pumpentyp auf das Format des Frontend
        mqtt_pump_type = ""
        if pump_type == "ph_up":
            mqtt_pump_type = "ph_up_pump"
        elif pump_type == "ph_down":
            mqtt_pump_type = "ph_down_pump"
        else:
            logger.error(f"Unbekannter Pumpentyp: {pump_type}")
            return
        
        # Erstelle MQTT-Befehl im gleichen Format wie das Frontend
        command = {
            "type": mqtt_pump_type,
            "duration": duration_ms
        }
        
        # Sende Befehl an Gerät (im gleichen Format wie das Frontend)
        topic = f"homegrow/{device_id}/command"
        try:
            # Kurze Pause vor dem Senden, damit Befehle nicht zu schnell hintereinander gesendet werden
            time.sleep(0.5)
            
            result = self.mqtt_client.publish(topic, command)
            if result:
                logger.info(f"MQTT-Befehl erfolgreich gesendet: {topic} - {command}")
            else:
                logger.error(f"Fehler beim Senden des MQTT-Befehls: {topic} - {command}")
        except Exception as e:
            logger.error(f"Exception beim Senden des MQTT-Befehls: {topic} - {command}: {e}")
        
        # Logge Aktion in Programminstanz
        log_data = {
            "previous_value": current_value,
            "target_range": target_range,
            "target_value": (target_range[0] + target_range[1]) / 2 if len(target_range) == 2 else target_range[0],
            "pump": pump_type,
            "volume_ml": volume_ml,
            "duration_ms": duration_ms
        }
        
        self.program_manager.add_program_instance_log(
            instance.instance_id, "ph_correction", log_data
        )
        
        logger.info(f"pH-Korrektur ausgeführt: Gerät {device_id}, {pump_type}, {volume_ml:.2f} ml, pH-Wert: {current_value:.2f}")
    
    def _execute_nutrient_correction(self,
                                   instance: ProgramInstance,
                                   config: Dict[str, Any],
                                   nutrient_amounts: Dict[str, float],
                                   current_value: float,
                                   target_range: List[float]):
        """
        Führt eine Nährstoffkorrektur aus
        
        Args:
            instance: Programminstanz
            config: Gerätekonfiguration
            nutrient_amounts: Dictionary mit Nährstoffmengen in ml
            current_value: Aktueller TDS-Wert
            target_range: Zielbereich [min, max]
        """
        if not self.mqtt_client:
            logger.error("Keine MQTT-Client-Verbindung für Pumpensteuerung")
            return
        
        device_id = instance.device_id
        template_id = instance.template_id
        instance_id = instance.instance_id
        
        logger.info(f"Sende Nährstoffkorrektur: Instanz {instance_id}, Template {template_id}, Gerät {device_id}")
        
        # Erstelle NutrientCalculator für Pumpdauer
        calculator = NutrientCalculator(config)
        
        # Mappe Nährstoffpumpen auf Frontend-Befehlstypen
        pump_mappings = {
            'nutrient1': 'nutrient_pump_1',
            'nutrient2': 'nutrient_pump_2',
            'nutrient3': 'nutrient_pump_3'
        }
        
        # Für jede Nährstoffpumpe einen Befehl senden
        pumps = [
            ('nutrient1', nutrient_amounts.get('nutrient1_ml', 0)),
            ('nutrient2', nutrient_amounts.get('nutrient2_ml', 0)),
            ('nutrient3', nutrient_amounts.get('nutrient3_ml', 0))
        ]
        
        # Sammle Daten für Log
        log_data = {
            "previous_value": current_value,
            "target_range": target_range,
            "target_value": (target_range[0] + target_range[1]) / 2 if len(target_range) == 2 else target_range[0],
            "nutrient_mix": {
                "nutrient1_ml": nutrient_amounts.get('nutrient1_ml', 0),
                "nutrient2_ml": nutrient_amounts.get('nutrient2_ml', 0),
                "nutrient3_ml": nutrient_amounts.get('nutrient3_ml', 0)
            }
        }
        
        # Zähle die tatsächlich aktiven Pumpen
        active_pumps = sum(1 for _, volume in pumps if volume > 0)
        
        if active_pumps == 0:
            logger.info(f"Keine Nährstoffkorrektur notwendig für Gerät {device_id}")
            return
            
        logger.info(f"Nährstoffkorrektur ausgeführt: Gerät {device_id}, TDS: {current_value:.1f}, Pumpen aktiv: {active_pumps}")
        
        # Sende Befehle für jeden Nährstoff
        for pump_type, volume_ml in pumps:
            if volume_ml <= 0:
                continue
                
            # Berechne Pumpenzeit in Millisekunden
            duration_ms = calculator.ml_to_pump_duration(pump_type, volume_ml)
            if duration_ms <= 0:
                logger.warning(f"Ungültige Pumpendauer berechnet: {duration_ms} ms für {volume_ml} ml")
                continue
            
            # Hole den entsprechenden Frontend-Pumpentyp
            mqtt_pump_type = pump_mappings.get(pump_type)
            if not mqtt_pump_type:
                logger.error(f"Keine Frontend-Pumpentyp für {pump_type} gefunden")
                continue
            
            # Erstelle MQTT-Befehl im gleichen Format wie das Frontend
            command = {
                "type": mqtt_pump_type,
                "duration": duration_ms
            }
            
            # Sende Befehl an Gerät (im gleichen Format wie das Frontend)
            topic = f"homegrow/{device_id}/command"
            try:
                # Kurze Pause vor dem Senden, damit Befehle nicht zu schnell hintereinander gesendet werden
                time.sleep(0.5)
                
                result = self.mqtt_client.publish(topic, command)
                if result:
                    logger.info(f"MQTT-Befehl erfolgreich gesendet: {topic} - {command}")
                else:
                    logger.error(f"Fehler beim Senden des MQTT-Befehls: {topic} - {command}")
            except Exception as e:
                logger.error(f"Exception beim Senden des MQTT-Befehls: {topic} - {command}: {e}")
                
            logger.debug(f"  - {pump_type}: {volume_ml:.1f} ml ({duration_ms} ms)")
        
        # Logge Aktion in Programminstanz
        self.program_manager.add_program_instance_log(
            instance.instance_id, "tds_correction", log_data
        )
    
    def _get_latest_sensor_value(self, device_id: str, sensor_type: str) -> Optional[float]:
        """
        Holt den aktuellsten Sensorwert aus dem Cache oder der Datenbank
        Gibt None zurück, wenn die Sensordaten zu alt sind.
        
        Args:
            device_id: ID des Geräts
            sensor_type: Art des Sensors ('ph' oder 'tds')
            
        Returns:
            Aktueller Sensorwert oder None, wenn nicht verfügbar
        """
        # Prüfung, ob das Gerät online ist, erfolgt bereits in _process_program_instance
            
        # Versuche, aus dem Cache zu lesen
        if device_id in self.latest_sensor_data and sensor_type in self.latest_sensor_data[device_id]:
            sensor_data = self.latest_sensor_data[device_id][sensor_type]
            timestamp = sensor_data.get('timestamp')
            
            # Prüfe, ob der Wert noch aktuell ist (nicht älter als max_sensor_age)
            if timestamp:
                age_seconds = (datetime.utcnow() - timestamp).total_seconds()
                if age_seconds < self.max_sensor_age:
                    logger.debug(f"Verwende Cache-Wert für {device_id}/{sensor_type}: {sensor_data.get('value')}")
                    return sensor_data.get('value')
                else:
                    logger.debug(f"Sensordaten für {device_id}/{sensor_type} sind veraltet ({age_seconds:.0f}s alt)")
                    return None
        
        # Hole den neuesten Wert aus der Datenbank
        sensor_data = self.db.get_sensor_data(device_id, sensor_type, limit=1)
        if not sensor_data:
            logger.debug(f"Keine Sensordaten für {device_id}/{sensor_type} in der Datenbank gefunden")
            return None
            
        # Prüfe auch hier das Alter der Daten
        value = sensor_data[0].get('value')
        timestamp = sensor_data[0].get('timestamp')
        
        if timestamp:
            age_seconds = (datetime.utcnow() - timestamp).total_seconds()
            if age_seconds >= self.max_sensor_age:
                logger.debug(f"Sensordaten aus Datenbank für {device_id}/{sensor_type} sind veraltet ({age_seconds:.0f}s alt)")
                return None
        
        # Aktualisiere den Cache
        if device_id not in self.latest_sensor_data:
            self.latest_sensor_data[device_id] = {}
            
        self.latest_sensor_data[device_id][sensor_type] = {
            'value': value,
            'timestamp': timestamp
        }
        
        logger.debug(f"Aktualisierter Sensorwert aus DB für {device_id}/{sensor_type}: {value}")
        return value
    
    def update_sensor_cache(self, device_id: str, sensor_type: str, value: float):
        """
        Aktualisiert den Sensor-Cache mit einem neuen Wert
        
        Args:
            device_id: ID des Geräts
            sensor_type: Art des Sensors ('ph' oder 'tds')
            value: Sensorwert
        """
        if device_id not in self.latest_sensor_data:
            self.latest_sensor_data[device_id] = {}
        
        # Prüfe, ob der Wert tatsächlich neu ist
        current_value = None
        if sensor_type in self.latest_sensor_data[device_id]:
            current_value = self.latest_sensor_data[device_id][sensor_type].get('value')
            
        # Aktualisiere den Cache nur, wenn sich der Wert geändert hat
        self.latest_sensor_data[device_id][sensor_type] = {
            'value': value,
            'timestamp': datetime.utcnow()
        }
        
        if current_value is not None and current_value != value:
            logger.debug(f"Sensor-Cache aktualisiert: {device_id}/{sensor_type}: {current_value} → {value}")
        else:
            logger.debug(f"Sensor-Cache gesetzt: {device_id}/{sensor_type}: {value}")

    def _handle_config_response(self, device_id: str, config: Dict[str, Any]):
        """
        Callback für Konfigurationsantworten von Geräten über MQTT
        
        Args:
            device_id: ID des Geräts
            config: Empfangene Konfiguration
        """
        try:
            logger.info(f"Konfigurationsantwort für Gerät {device_id} empfangen")
            
            # Aktualisiere den lokalen Cache
            self.device_config_cache[device_id] = config
            
            logger.debug(f"Konfigurationscache für Gerät {device_id} aktualisiert")
        except Exception as e:
            logger.error(f"Fehler beim Verarbeiten der Konfigurationsantwort für Gerät {device_id}: {e}")
    
    def _get_device_config(self, device_id: str) -> Dict[str, Any]:
        """
        Holt die Konfiguration eines Geräts aus dem Cache oder der Datenbank
        
        Args:
            device_id: ID des Geräts
            
        Returns:
            Konfiguration des Geräts (leeres Dict, wenn nicht vorhanden)
        """
        # Zuerst im Cache nachsehen
        if device_id in self.device_config_cache:
            logger.debug(f"Verwende gecachte Konfiguration für Gerät {device_id}")
            return self.device_config_cache[device_id]
        
        # Wenn nicht im Cache, aus Datenbank holen und im Cache speichern
        config = self.db.get_device_config(device_id) or {}
        
        # Speichere im Cache für zukünftige Verwendung
        self.device_config_cache[device_id] = config
        
        return config

    def _process_pump_cycles(self, instance: ProgramInstance, phase: Dict[str, Any]):
        """Verarbeitet die Wasser- und Luftpumpenzyklen für eine Programminstanz."""
        device_id = instance.device_id
        instance_id = instance.instance_id
        now = datetime.utcnow()

        pump_configs = {
            'water_pump': {
                'cycle_key': 'water_pump_cycle_minutes',
                'on_key': 'water_pump_on_minutes',
                'mqtt_type': 'water_pump'
            },
            'air_pump': {
                'cycle_key': 'air_pump_cycle_minutes',
                'on_key': 'air_pump_on_minutes',
                'mqtt_type': 'air_pump'
            }
        }

        for pump_key, config in pump_configs.items():
            cycle_minutes = phase.get(config['cycle_key'], 0)
            on_minutes = phase.get(config['on_key'], 0)

            logger.info(f"Pumpenzyklus für {pump_key} bei Gerät {device_id}: Zyklus={cycle_minutes} Minuten, Laufzeit={on_minutes} Minuten")

            # Überspringe, wenn Zyklus oder Einschaltdauer 0 oder negativ ist
            if cycle_minutes <= 0 or on_minutes <= 0:
                # Logge nur, wenn der Zustand zuvor aktiv war und entferne ihn
                if instance_id in self.pump_control_state and pump_key in self.pump_control_state[instance_id]:
                    logger.info(f"Pumpenzyklus für {pump_key} bei Gerät {device_id} (Instanz {instance_id}) ist deaktiviert. Entferne Zustand.")
                    del self.pump_control_state[instance_id][pump_key]
                    # Wenn der Pumpenkey der letzte im Dictionary der Instanz war, entferne auch die Instanz
                    if not self.pump_control_state[instance_id]:
                        del self.pump_control_state[instance_id]
                continue

            # Initialisiere Zustand für diese Instanz und Pumpe, falls nicht vorhanden
            self._initialize_pump_state_if_needed(instance_id, pump_key, now)
            
            # Prüfe, ob die Pumpe gestartet werden soll und starte sie gegebenenfalls
            self._check_and_start_pump(instance, pump_key, config['mqtt_type'], cycle_minutes, on_minutes, now)


    def _initialize_pump_state_if_needed(self, instance_id: str, pump_key: str, current_time: datetime):
        """Initialisiert den Zustand für eine Pumpe einer Instanz, wenn er noch nicht existiert."""
        if instance_id not in self.pump_control_state:
            self.pump_control_state[instance_id] = {}
            logger.info(f"Initialisiere Pumpensteuerungszustand für Instanz {instance_id}")

        if pump_key not in self.pump_control_state[instance_id]:
            # Erste Ausführung oder nach Phasenwechsel/Neustart: Starte sofort
            next_start_time = current_time
            self.pump_control_state[instance_id][pump_key] = {
                'last_start': None, # Wird gesetzt, wenn die Pumpe tatsächlich startet
                'next_start': next_start_time
            }
            logger.info(f"Initialisiere Pumpenzyklus für {pump_key} bei Instanz {instance_id}. Erster Start geplant für: {next_start_time.isoformat()}")


    def _check_and_start_pump(self, 
                             instance: ProgramInstance, 
                             pump_key: str, 
                             mqtt_type: str, 
                             cycle_minutes: float, 
                             on_minutes: float, 
                             current_time: datetime):
        """Prüft, ob eine Pumpe gestartet werden soll und führt den Start aus."""
        instance_id = instance.instance_id
        device_id = instance.device_id

        # Stelle sicher, dass der Zustand existiert (sollte durch _initialize_pump_state_if_needed sichergestellt sein)
        if instance_id not in self.pump_control_state or pump_key not in self.pump_control_state[instance_id]:
             logger.error(f"Pumpenzustand für {pump_key} bei Instanz {instance_id} nicht gefunden, obwohl Zyklus aktiv ist.")
             return

        pump_state = self.pump_control_state[instance_id][pump_key]
        next_start_time = pump_state.get('next_start')

        if not next_start_time:
            logger.error(f"Kein next_start_time für {pump_key} bei Instanz {instance_id} definiert!")
            return

        # Ausführlicheres Logging für den Entscheidungsprozess
        time_difference_seconds = (current_time - next_start_time).total_seconds()
        time_info = f"jetzt={current_time.isoformat()}, nächster Start={next_start_time.isoformat()}, Differenz: {time_difference_seconds:.1f}s"

        if current_time >= next_start_time:
            logger.info(f"Zeit für {pump_key}-Start bei Instanz {instance_id} erreicht. {time_info}")

            duration_ms = int(on_minutes * 60 * 1000)

            # Sende MQTT Befehl
            success = self._send_pump_command(device_id, mqtt_type, duration_ms)

            if success:
                # Aktualisiere Zustand
                last_start = current_time
                next_start = last_start + timedelta(minutes=cycle_minutes)
                self.pump_control_state[instance_id][pump_key]['last_start'] = last_start
                self.pump_control_state[instance_id][pump_key]['next_start'] = next_start
                logger.info(f"{pump_key} für Gerät {device_id} (Instanz {instance_id}) gestartet ({on_minutes} Min.). Nächster Start um {next_start.isoformat()}")

                # Logge die Aktion in Programminstanz
                log_data = {
                    "pump_type": pump_key,
                    "duration_minutes": on_minutes,
                    "cycle_minutes": cycle_minutes,
                    "next_start_time": next_start.isoformat()
                }
                self.program_manager.add_program_instance_log(
                    instance_id, "pump_cycle_start", log_data
                )
            else:
                 # Bei Fehler: Versuche es beim nächsten Durchlauf erneut (next_start bleibt gleich)
                logger.error(f"Fehler beim Starten von {pump_key} für Gerät {device_id} (Instanz {instance_id}). Erneuter Versuch im nächsten Zyklus.")
        else:
            # Das Logging hier kann sehr häufig sein, vielleicht auf DEBUG reduzieren?
            # Oder nur loggen, wenn sich der nächste Start nähert?
            if time_difference_seconds < 60 and time_difference_seconds % 10 == 0: # Nur loggen, wenn der nächste Start weniger als 60s entfernt ist
                 logger.debug(f"Noch nicht Zeit für {pump_key}-Start bei Instanz {instance_id}. {time_info}")
            else:
                 # Logge nur auf DEBUG Level, wenn der nächste Start noch weiter entfernt ist
                 logger.debug(f"Warte auf {pump_key}-Start bei Instanz {instance_id}. {time_info}")


    def _send_pump_command(self, device_id: str, pump_type: str, duration_ms: int) -> bool:
        """Sendet einen MQTT-Befehl zum Starten einer Pumpe für eine bestimmte Dauer."""
        if not self.mqtt_client:
            logger.error("Kein MQTT-Client verfügbar, um Pumpenbefehl zu senden.")
            return False

        if duration_ms <= 0:
             logger.warning(f"Versuch, Pumpe {pump_type} für Gerät {device_id} mit ungültiger Dauer ({duration_ms}ms) zu starten. Ignoriert.")
             return False # Nicht als Fehler behandeln, aber auch nicht senden

        topic = f"homegrow/{device_id}/command" # Festes Topic-Präfix "homegrow" verwenden
        command = {
            "type": pump_type,
            "duration": duration_ms
        }

        logger.info(f"Sende Pumpenbefehl an {topic}: {command}")
        try:
            # Kurze Pause vor dem Senden, um Befehle nicht zu schnell zu senden (0.2s)
            time.sleep(0.2)
            success = self.mqtt_client.publish(topic, command, qos=1) # QoS=1 für garantierte Zustellung
            if success:
                logger.info(f"Pumpenbefehl erfolgreich an {topic} gesendet.")
                return True
            else:
                # publish sollte bei Misserfolg False zurückgeben oder eine Exception werfen
                logger.error(f"Fehler beim Senden des Pumpenbefehls an {topic} (qos=1). MQTT publish call returned False.")
                return False
        except Exception as e:
            logger.error(f"Exception beim Senden des Pumpenbefehls an {topic}: {e}")
            return False

    def remove_instance_state(self, instance_id: str):
        """Entfernt den internen Zustand einer Programminstanz (z.B. wenn sie gelöscht/gestoppt wird)."""
        if instance_id in self.pump_control_state:
            del self.pump_control_state[instance_id]
            logger.info(f"Pumpensteuerungszustand für Instanz {instance_id} entfernt.")

    def _get_current_phase_index(self, started_at: datetime, phases: List[dict], now: datetime = None) -> int:
        """
        Berechnet den aktuellen Phasenindex basierend auf dem Startzeitpunkt und den Phasendauern.
        Args:
            started_at: Startzeitpunkt des Programms
            phases: Liste der Phasen (als Dicts)
            now: Optional aktueller Zeitpunkt (sonst UTC now)
        Returns:
            Index der aktuellen Phase (0-basiert)
        """
        if not started_at or not phases:
            return 0
        if now is None:
            now = datetime.utcnow()
        days_passed = (now - started_at).days
        day_sum = 0
        for idx, phase in enumerate(phases):
            day_sum += phase.get('duration_days', 0)
            if days_passed < day_sum:
                return idx
        return len(phases) - 1  # Letzte Phase, falls alle vorbei

# Singleton-Instanz der ProgramEngine
_program_engine_instance = None

def get_program_engine(mqtt_client=None) -> ProgramEngine:
    """
    Gibt die ProgramEngine-Instanz zurück
    
    Args:
        mqtt_client: Optional MQTT-Client für die Kommunikation
        
    Returns:
        ProgramEngine-Instanz
    """
    global _program_engine_instance
    if _program_engine_instance is None:
        _program_engine_instance = ProgramEngine(mqtt_client)
    return _program_engine_instance 