#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import yaml
from typing import Dict, Any, Optional

class Config:
    """Konfigurationsmanager für den HomeGrow Server"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """Singleton-Pattern für die Konfiguration"""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisiert die Konfiguration
        
        Args:
            config_path: Pfad zur Konfigurationsdatei
        """
        if self._initialized:
            return
            
        self.config_path = config_path or os.environ.get('HOMEGROW_CONFIG', 'config/config.yaml')
        self.config = self._load_config()
        self._initialized = True
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Lädt die Konfiguration aus der Datei
        
        Returns:
            Dictionary mit der Konfiguration
        """
        default_config = {
            'mqtt': {
                'host': 'localhost',
                'port': 1883,
                'username': None,
                'password': None,
                'client_id': 'homegrow_server',
                'topic_prefix': 'homegrow'
            },
            'mongodb': {
                'uri': 'mongodb://localhost:27017/',
                'database': 'homegrow'
            },
            'logging': {
                'level': 'info',
                'file': 'logs/homegrow_server.log'
            },
            'automation': {
                'enabled': True,
                'check_interval': 60  # Sekunden
            }
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        # Rekursives Update der Konfiguration
                        return self._deep_update(default_config, user_config)
        except Exception as e:
            print(f"Fehler beim Laden der Konfiguration: {e}")
        
        return default_config
    
    def _deep_update(self, d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aktualisiert ein Dictionary rekursiv
        
        Args:
            d: Ziel-Dictionary
            u: Quell-Dictionary
            
        Returns:
            Aktualisiertes Dictionary
        """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                d[k] = self._deep_update(d[k], v)
            else:
                d[k] = v
        return d
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Gibt einen Konfigurationswert zurück
        
        Args:
            key: Schlüssel des Konfigurationswerts (mit Punktnotation für verschachtelte Werte)
            default: Standardwert, falls der Schlüssel nicht existiert
            
        Returns:
            Konfigurationswert oder Standardwert
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
    
    def get_mqtt_config(self) -> Dict[str, Any]:
        """
        Gibt die MQTT-Konfiguration zurück
        
        Returns:
            Dictionary mit der MQTT-Konfiguration
        """
        return self.config.get('mqtt', {})
    
    def get_mongodb_config(self) -> Dict[str, Any]:
        """
        Gibt die MongoDB-Konfiguration zurück
        
        Returns:
            Dictionary mit der MongoDB-Konfiguration
        """
        return self.config.get('mongodb', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Gibt die Logging-Konfiguration zurück
        
        Returns:
            Dictionary mit der Logging-Konfiguration
        """
        return self.config.get('logging', {})
    
    def get_automation_config(self) -> Dict[str, Any]:
        """
        Gibt die Automatisierungskonfiguration zurück
        
        Returns:
            Dictionary mit der Automatisierungskonfiguration
        """
        return self.config.get('automation', {})
    
    def save(self) -> bool:
        """
        Speichert die aktuelle Konfiguration in die Datei
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Stelle sicher, dass das Verzeichnis existiert
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            return True
        except Exception as e:
            print(f"Fehler beim Speichern der Konfiguration: {e}")
            return False

# Einfache Funktion zum Abrufen der Konfiguration
def get_config() -> Config:
    """
    Gibt die Konfigurationsinstanz zurück
    
    Returns:
        Config-Instanz
    """
    return Config() 