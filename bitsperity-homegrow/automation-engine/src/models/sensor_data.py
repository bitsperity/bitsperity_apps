#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Dict, Any, Optional, List

class SensorData:
    """Repräsentiert Sensordaten eines Geräts"""
    
    def __init__(self, device_id: str, sensor_type: str, value: Any,
                 timestamp: Optional[datetime] = None, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialisiert neue Sensordaten
        
        Args:
            device_id: ID des Geräts, von dem die Daten stammen
            sensor_type: Typ des Sensors (z.B. 'ph', 'tds')
            value: Sensorwert
            timestamp: Zeitpunkt der Messung
            metadata: Zusätzliche Metadaten zur Messung
        """
        self.device_id = device_id
        self.sensor_type = sensor_type
        self.value = value
        self.timestamp = timestamp or datetime.utcnow()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert die Sensordaten in ein Dictionary für die Speicherung"""
        return {
            'device_id': self.device_id,
            'sensor_type': self.sensor_type,
            'value': self.value,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SensorData':
        """
        Erstellt Sensordaten aus einem Dictionary
        
        Args:
            data: Dictionary mit Sensordaten
            
        Returns:
            Ein neues SensorData-Objekt
        """
        return cls(
            device_id=data['device_id'],
            sensor_type=data['sensor_type'],
            value=data['value'],
            timestamp=data.get('timestamp'),
            metadata=data.get('metadata', {})
        )
    
    @classmethod
    def from_mqtt_payload(cls, device_id: str, payload: Dict[str, Any]) -> List['SensorData']:
        """
        Erstellt Sensordaten aus einer MQTT-Nachricht
        
        Args:
            device_id: ID des Geräts
            payload: MQTT-Payload als Dictionary
            
        Returns:
            Liste von SensorData-Objekten
        """
        sensor_data_list = []
        timestamp = datetime.utcnow()
        
        # Verarbeite jeden Sensortyp im Payload
        for sensor_type, value in payload.items():
            # Ignoriere nicht-sensorische Daten
            if sensor_type in ['timestamp', 'device_id', 'client_id']:
                continue
                
            # Erstelle ein SensorData-Objekt
            sensor_data = cls(
                device_id=device_id,
                sensor_type=sensor_type,
                value=value,
                timestamp=timestamp
            )
            sensor_data_list.append(sensor_data)
            
        return sensor_data_list 