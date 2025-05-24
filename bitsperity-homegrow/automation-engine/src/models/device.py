#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Dict, Any, Optional, List

class Device:
    """Repräsentiert ein HomeGrow-Gerät im System"""
    
    def __init__(self, device_id: str, name: Optional[str] = None, 
                 config: Optional[Dict[str, Any]] = None, 
                 last_seen: Optional[datetime] = None,
                 sensors: Optional[Dict[str, Any]] = None,
                 actuators: Optional[Dict[str, Any]] = None):
        """
        Initialisiert ein neues Gerät
        
        Args:
            device_id: Eindeutige ID des Geräts
            name: Benutzerfreundlicher Name des Geräts
            config: Konfiguration des Geräts
            last_seen: Zeitpunkt der letzten Aktivität
            sensors: Sensordaten des Geräts
            actuators: Aktuatorstatus des Geräts
        """
        self.device_id = device_id
        self.name = name or f"HomeGrow Device {device_id}"
        self.config = config or {}
        self.last_seen = last_seen or datetime.utcnow()
        self.sensors = sensors or {}
        self.actuators = actuators or {}
        self.online = False
    
    def update_last_seen(self):
        """Aktualisiert den Zeitstempel der letzten Aktivität"""
        self.last_seen = datetime.utcnow()
        self.online = True
    
    def set_offline(self):
        """Markiert das Gerät als offline"""
        self.online = False
    
    def update_sensor_data(self, sensor_type: str, value: Any):
        """
        Aktualisiert die Daten eines bestimmten Sensors
        
        Args:
            sensor_type: Typ des Sensors (z.B. 'ph', 'tds')
            value: Neuer Sensorwert
        """
        self.sensors[sensor_type] = {
            'value': value,
            'timestamp': datetime.utcnow()
        }
    
    def update_config(self, config: Dict[str, Any]):
        """
        Aktualisiert die Konfiguration des Geräts
        
        Args:
            config: Neue Konfiguration
        """
        # Wenn "config" in config ist, nehmen wir diesen Wert, sonst das ganze Dictionary
        if "config" in config:
            self.config = config["config"]
        else:
            self.config = config
    
    def update_actuator_status(self, actuator_id: str, status: Any):
        """
        Aktualisiert den Status eines Aktuators
        
        Args:
            actuator_id: ID des Aktuators
            status: Neuer Status des Aktuators
        """
        self.actuators[actuator_id] = {
            'status': status,
            'timestamp': datetime.utcnow()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert das Gerät in ein Dictionary für die Speicherung"""
        return {
            'device_id': self.device_id,
            'name': self.name,
            'config': self.config,
            'last_seen': self.last_seen,
            'sensors': self.sensors,
            'actuators': self.actuators,
            'online': self.online
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Device':
        """
        Erstellt ein Gerät aus einem Dictionary
        
        Args:
            data: Dictionary mit Gerätedaten
            
        Returns:
            Ein neues Device-Objekt
        """
        return cls(
            device_id=data['device_id'],
            name=data.get('name'),
            config=data.get('config', {}),
            last_seen=data.get('last_seen'),
            sensors=data.get('sensors', {}),
            actuators=data.get('actuators', {})
        ) 