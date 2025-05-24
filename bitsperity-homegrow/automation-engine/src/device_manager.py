#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .models.device import Device
from .models.sensor_data import SensorData
from .database import get_database
from .mqtt_client import get_mqtt_client
from .logger import get_logger

logger = get_logger(__name__)

class DeviceManager:
    """Verwaltet die HomeGrow-Geräte und deren Daten"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """Singleton-Pattern für den DeviceManager"""
        if cls._instance is None:
            cls._instance = super(DeviceManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialisiert den DeviceManager"""
        if self._initialized:
            return
            
        self.db = get_database()
        self.mqtt = get_mqtt_client()
        
        # Cache für Geräte
        self.devices = {}
        
        # Registriere MQTT-Callbacks
        self.mqtt.register_heartbeat_callback(self.handle_heartbeat)
        self.mqtt.register_sensor_callback(self.handle_sensor_data)
        self.mqtt.register_actuator_status_callback(self.handle_actuator_status)
        self.mqtt.register_config_response_callback(self.handle_config_response)
        
        # Lade Geräte aus der Datenbank
        self._load_devices()
        
        self._initialized = True
    
    def _load_devices(self):
        """Lädt alle Geräte aus der Datenbank (nur Konfigurationen aus configs Collection)"""
        try:
            # Hole alle Konfigurationen aus der configs Collection
            configs_data = list(self.db.db.configs.find({}))
            for config_doc in configs_data:
                device_id = config_doc.get("device_id")
                if not device_id:
                    continue
                
                # Erstelle Device-Objekt nur mit Grundinformationen
                device_name = config_doc.get("device_name", f"HomeGrow Device {device_id}")
                config = config_doc.get("config", {})
                
                # Device-Objekt erstellen und zum Cache hinzufügen - ohne Sensordaten oder Aktuatoren
                # Diese werden später über MQTT-Updates aktualisiert
                device = Device(
                    device_id=device_id,
                    name=device_name,
                    config=config
                )
                self.devices[device_id] = device
                
            logger.info(f"{len(self.devices)} Geräte aus den Konfigurationen geladen")
        except Exception as e:
            logger.error(f"Fehler beim Laden der Geräte: {e}")
    
    def get_device(self, device_id: str) -> Optional[Device]:
        """
        Gibt ein Gerät anhand seiner ID zurück
        
        Args:
            device_id: ID des Geräts
            
        Returns:
            Device-Objekt oder None, wenn nicht gefunden
        """
        # Versuche zuerst, das Gerät aus dem Cache zu holen
        if device_id in self.devices:
            return self.devices[device_id]
            
        # Wenn nicht im Cache, versuche aus der configs Collection zu laden
        config_doc = self.db.db.configs.find_one({"device_id": device_id})
        if config_doc:
            device_name = config_doc.get("device_name", f"HomeGrow Device {device_id}")
            config = config_doc.get("config", {})
            
            # Erstelle ein neues Gerät
            device = Device(
                device_id=device_id,
                name=device_name,
                config=config
            )
            
            # Füge das Gerät zum Cache hinzu
            self.devices[device_id] = device
            return device
            
        return None
    
    def get_all_devices(self) -> List[Device]:
        """
        Gibt alle Geräte zurück
        
        Returns:
            Liste aller Geräte
        """
        return list(self.devices.values())
    
    def create_device(self, device_id: str, name: Optional[str] = None) -> Device:
        """
        Erstellt ein neues Gerät im Cache (schreibt keine Konfiguration)
        
        Args:
            device_id: ID des Geräts
            name: Name des Geräts
            
        Returns:
            Neu erstelltes Device-Objekt
        """
        # Prüfe, ob das Gerät bereits existiert
        existing_device = self.get_device(device_id)
        if existing_device:
            return existing_device
            
        # Erstelle ein neues Gerät
        device = Device(device_id=device_id, name=name)
        
        # Füge das Gerät zum Cache hinzu
        self.devices[device_id] = device
        
        logger.info(f"Neues Gerät im Cache erstellt: {device_id}")
        return device
    
    def update_device(self, device: Device) -> bool:
        """
        Aktualisiert ein Gerät im Cache (schreibt keine Konfiguration)
        
        Args:
            device: Device-Objekt
            
        Returns:
            True bei Erfolg
        """
        # Aktualisiere den Cache
        self.devices[device.device_id] = device
        return True
    
    def handle_heartbeat(self, device_id: str, data: Dict[str, Any]):
        """
        Verarbeitet Heartbeat-Nachrichten von Geräten
        
        Args:
            device_id: ID des Geräts
            data: Heartbeat-Daten
        """
        # Hole oder erstelle das Gerät
        device = self.get_device(device_id)
        if not device:
            device = self.create_device(device_id)
        
        # Aktualisiere den Zeitstempel der letzten Aktivität
        device.update_last_seen()
        
        # Speichere das aktualisierte Gerät
        self.update_device(device)
        
        logger.debug(f"Heartbeat von Gerät {device_id} empfangen")
    
    def handle_sensor_data(self, device_id: str, sensor_type: str, data: Dict[str, Any]):
        """
        Verarbeitet Sensordaten von Geräten
        
        Args:
            device_id: ID des Geräts
            sensor_type: Typ des Sensors
            data: Sensordaten
        """
        # Hole oder erstelle das Gerät
        device = self.get_device(device_id)
        if not device:
            device = self.create_device(device_id)
        
        # Extrahiere den Sensorwert
        value = data.get('value')
        if value is None:
            logger.warning(f"Sensorwert fehlt in den Daten: {data}")
            return
        
        # Aktualisiere die Sensordaten des Geräts
        device.update_sensor_data(sensor_type, value)
        
        # Aktualisiere den Zeitstempel der letzten Aktivität
        device.update_last_seen()
        
        # Speichere das aktualisierte Gerät
        self.update_device(device)
        
        # Speichere die Sensordaten in der Datenbank
        sensor_data = SensorData(
            device_id=device_id,
            sensor_type=sensor_type,
            value=value,
            timestamp=datetime.utcnow(),
            metadata=data.get('metadata', {})
        )
        self.db.save_sensor_data(sensor_data.to_dict())
        
        logger.debug(f"Sensordaten für Gerät {device_id}, Sensor {sensor_type}: {value}")
    
    def handle_actuator_status(self, device_id: str, actuator_id: str, data: Dict[str, Any]):
        """
        Verarbeitet Aktuator-Status-Updates von Geräten
        
        Args:
            device_id: ID des Geräts
            actuator_id: ID des Aktuators
            data: Statusdaten
        """
        # Hole oder erstelle das Gerät
        device = self.get_device(device_id)
        if not device:
            device = self.create_device(device_id)
        
        # Extrahiere den Status
        status = data.get('status')
        if status is None:
            logger.warning(f"Aktuatorstatus fehlt in den Daten: {data}")
            return
        
        # Aktualisiere den Aktuatorstatus des Geräts
        device.update_actuator_status(actuator_id, status)
        
        # Aktualisiere den Zeitstempel der letzten Aktivität
        device.update_last_seen()
        
        # Speichere das aktualisierte Gerät
        self.update_device(device)
        
        logger.debug(f"Aktuatorstatus für Gerät {device_id}, Aktuator {actuator_id}: {status}")
    
    def handle_config_response(self, device_id: str, data: Dict[str, Any]):
        """
        Verarbeitet Konfigurationsantworten von Geräten
        
        Args:
            device_id: ID des Geräts
            data: Konfigurationsantwort
        """
        logger.info(f"Konfigurationsantwort für Gerät {device_id} empfangen - nur lokale Aktualisierung")
        
        try:
            # Hole oder erstelle das Gerät
            device = self.get_device(device_id)
            if not device:
                device = self.create_device(device_id)
            
            # Aktualisiere die Konfiguration des Geräts im lokalen Cache
            device.update_config(data)
            
            # Aktualisiere den Zeitstempel der letzten Aktivität
            device.update_last_seen()
            
            # Speichere das aktualisierte Gerät im lokalen Cache 
            # (ohne Datenbankaktualisierung)
            self.update_device(device)
            
            logger.info(f"Konfiguration für Gerät {device_id} erfolgreich im lokalen Cache aktualisiert")
        except Exception as e:
            logger.error(f"Fehler bei der lokalen Aktualisierung der Konfiguration für Gerät {device_id}: {e}")
    
    def send_actuator_command(self, device_id: str, actuator_id: str, command: Dict[str, Any]) -> bool:
        """
        Sendet einen Befehl an einen Aktuator
        
        Args:
            device_id: ID des Geräts
            actuator_id: ID des Aktuators
            command: Befehl als Dictionary
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Prüfe, ob das Gerät existiert
            device = self.get_device(device_id)
            if not device:
                logger.warning(f"Gerät {device_id} nicht gefunden")
                return False
                
            # Sende den Befehl über MQTT
            self.mqtt.publish_actuator_command(device_id, actuator_id, command)
            
            return True
        except Exception as e:
            logger.error(f"Fehler beim Senden des Aktuatorbefehls: {e}")
            return False
    
    def check_device_status(self):
        """Überprüft den Status aller Geräte und markiert inaktive Geräte als offline"""
        now = datetime.utcnow()
        offline_threshold = timedelta(seconds=30)  # 30 Sekunden ohne Aktivität = offline
        
        for device_id, device in self.devices.items():
            if device.online and now - device.last_seen > offline_threshold:
                device.set_offline()
                self.update_device(device)
                logger.info(f"Gerät {device_id} wurde als offline markiert")

# Einfache Funktion zum Abrufen des DeviceManager
def get_device_manager() -> DeviceManager:
    """
    Gibt die DeviceManager-Instanz zurück
    
    Returns:
        DeviceManager-Instanz
    """
    return DeviceManager() 