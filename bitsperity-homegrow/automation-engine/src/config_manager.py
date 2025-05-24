#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import uuid
from typing import Dict, Any, Optional

from .database import get_database
from .mqtt_client import get_mqtt_client
from .device_manager import get_device_manager
from .logger import get_logger

logger = get_logger(__name__)

class ConfigManager:
    """Verwaltet die Konfigurationen der HomeGrow-Geräte"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """Singleton-Pattern für den ConfigManager"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialisiert den ConfigManager"""
        if self._initialized:
            return
            
        self.db = get_database()
        self.mqtt = get_mqtt_client()
        self.device_manager = get_device_manager()
        
        # Registriere MQTT-Callbacks
        self.mqtt.register_config_request_callback(self.handle_config_request)
        
        self._initialized = True
    
    def get_device_config(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Gibt die Konfiguration eines Geräts zurück
        
        Args:
            device_id: ID des Geräts
            
        Returns:
            Konfiguration oder None, wenn nicht gefunden
        """
        return self.db.get_device_config(device_id)
    
    def save_device_config(self, device_id: str, config: Dict[str, Any]) -> bool:
        """
        Speichert die Konfiguration eines Geräts
        
        Args:
            device_id: ID des Geräts
            config: Konfiguration
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        # Speichere die Konfiguration in der Datenbank
        success = self.db.save_device_config(device_id, config)
        
        if success:
            # Aktualisiere die Konfiguration des Geräts im DeviceManager
            device = self.device_manager.get_device(device_id)
            if device:
                device.config = config
                self.device_manager.update_device(device)
            else:
                # Wenn das Gerät noch nicht existiert, erstelle es
                self.device_manager.create_device(device_id)
                
            # Veröffentliche die Konfiguration über MQTT
            self.publish_config(device_id, config)
            
        return success
    
    def create_default_config(self, device_id: str) -> Dict[str, Any]:
        """
        Erstellt eine Standardkonfiguration für ein Gerät
        
        Args:
            device_id: ID des Geräts
            
        Returns:
            Standardkonfiguration
        """
        default_config = {
            "sensors": {
                "ph": {
                    "enabled": True,
                    "pin": 34,
                    "calibration": {
                        "offset": 0.0,
                        "slope": 1.0
                    },
                    "limits": {
                        "min": 5.5,
                        "max": 6.5
                    },
                    "reading_interval": 60  # Sekunden
                },
                "tds": {
                    "enabled": True,
                    "pin": 35,
                    "calibration": {
                        "offset": 0.0,
                        "slope": 1.0
                    },
                    "limits": {
                        "min": 500,
                        "max": 1500
                    },
                    "reading_interval": 60  # Sekunden
                }
            },
            "actuators": {
                "pump_water": {
                    "enabled": True,
                    "pin": 15,
                    "active_low": False,
                    "flow_rate": 10.0  # ml/s
                },
                "pump_air": {
                    "enabled": True,
                    "pin": 14,
                    "active_low": False
                },
                "pump_ph_up": {
                    "enabled": True,
                    "pin": 16,
                    "active_low": False,
                    "flow_rate": 1.0  # ml/s
                },
                "pump_ph_down": {
                    "enabled": True,
                    "pin": 17,
                    "active_low": False,
                    "flow_rate": 1.0  # ml/s
                },
                "pump_nutrient_1": {
                    "enabled": True,
                    "pin": 18,
                    "active_low": False,
                    "flow_rate": 2.0  # ml/s
                },
                "pump_nutrient_2": {
                    "enabled": False,
                    "pin": 19,
                    "active_low": False,
                    "flow_rate": 2.0  # ml/s
                },
                "pump_nutrient_3": {
                    "enabled": False,
                    "pin": 21,
                    "active_low": False,
                    "flow_rate": 2.0  # ml/s
                }
            },
            "automation": {
                "enabled": True,
                "check_interval": 300  # Sekunden
            },
            "network": {
                "mqtt": {
                    "client_id": f"homegrow_client_{device_id}",
                    "topic_prefix": "homegrow"
                }
            },
            # Neue Konfiguration für die Nährstoff-Automatisierung
            "nutrient_control": {
                "water_volume_liters": 20,
                "solution_strengths": {
                    "nutrient1": "standard",
                    "nutrient2": "standard",
                    "nutrient3": "standard",
                    "ph_up": "standard",
                    "ph_down": "standard"
                },
                "dose_limits": {
                    "max_nutrient_percent": 0.1,
                    "min_nutrient_percent": 0.005,
                    "max_ph_percent": 0.025,
                    "min_ph_percent": 0.0025
                },
                "calibration": {
                    "tds_per_ml": 10.0,
                    "ph_up_per_ml": 0.1,
                    "ph_down_per_ml": 0.1
                },
                "wait_times": {
                    "nutrient_minutes": 30,
                    "ph_minutes": 5
                }
            }
        }
        
        return default_config
    
    def handle_config_request(self, device_id: str, data: Dict[str, Any]):
        """
        Verarbeitet Konfigurationsanfragen von Geräten
        
        Args:
            device_id: ID des Geräts
            data: Anfragedaten
        """
        logger.info(f"Konfigurationsanfrage von Gerät {device_id} empfangen")
        logger.info(f"Anfragedaten: {data}")
        
        # Prüfe, ob das Gerät existiert, andernfalls erstelle es
        device = self.device_manager.get_device(device_id)
        if not device:
            logger.info(f"Gerät {device_id} nicht gefunden, erstelle neues Gerät")
            device = self.device_manager.create_device(device_id)
        
        # Hole die Konfiguration aus der Datenbank
        config = self.get_device_config(device_id)
        
        # Wenn keine Konfiguration gefunden wurde, erstelle eine Standardkonfiguration
        if not config:
            logger.info(f"Keine Konfiguration für Gerät {device_id} gefunden, erstelle Standardkonfiguration")
            config = self.create_default_config(device_id)
            self.save_device_config(device_id, config)
        
        # Veröffentliche die Konfiguration
        self.publish_config(device_id, config)
    
    def publish_config(self, device_id: str, config: Dict[str, Any]):
        """
        Veröffentlicht eine Konfiguration für ein Gerät
        
        Args:
            device_id: ID des Geräts
            config: Konfiguration
        """
        try:
            self.mqtt.publish_config(device_id, config)
            logger.info(f"Konfiguration für Gerät {device_id} veröffentlicht")
        except Exception as e:
            logger.error(f"Fehler beim Veröffentlichen der Konfiguration für Gerät {device_id}: {e}")

# Einfache Funktion zum Abrufen des ConfigManagers
def get_config_manager() -> ConfigManager:
    """
    Gibt den ConfigManager zurück
    
    Returns:
        ConfigManager-Instanz
    """
    return ConfigManager() 