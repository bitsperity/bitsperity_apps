#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import time
from typing import Dict, Any, Optional, List

from .config import get_config
from .device_manager import get_device_manager
from .rules_engine import get_rules_engine
from .logger import get_logger

logger = get_logger(__name__)

class Automation:
    """Automatisierungsmanager für den HomeGrow Server"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """Singleton-Pattern für die Automation"""
        if cls._instance is None:
            cls._instance = super(Automation, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialisiert die Automation"""
        if self._initialized:
            return
            
        self.config = get_config()
        self.device_manager = get_device_manager()
        self.rules_engine = get_rules_engine()
        
        # Konfiguration für die Automatisierung
        self.automation_config = self.config.get_automation_config()
        self.enabled = self.automation_config.get('enabled', True)
        self.check_interval = self.automation_config.get('check_interval', 60)
        
        # Thread für die Statusprüfung
        self.running = False
        self.thread = None
        
        self._initialized = True
    
    def start(self):
        """Startet die Automatisierung"""
        if not self.enabled:
            logger.info("Automatisierung ist deaktiviert")
            return
            
        if self.running:
            logger.warning("Automatisierung läuft bereits")
            return
            
        # Starte die Regelauswertung
        self.rules_engine.start(self.check_interval)
        
        # Starte den Thread für die Statusprüfung
        self.running = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()
        
        logger.info("Automatisierung gestartet")
    
    def stop(self):
        """Stoppt die Automatisierung"""
        if not self.running:
            logger.warning("Automatisierung läuft nicht")
            return
            
        # Stoppe die Regelauswertung
        self.rules_engine.stop()
        
        # Stoppe den Thread für die Statusprüfung
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
            self.thread = None
            
        logger.info("Automatisierung gestoppt")
    
    def _run_loop(self):
        """Hauptschleife für die Statusprüfung"""
        status_check_interval = 60  # Sekunden
        
        while self.running:
            try:
                # Überprüfe den Status aller Geräte
                self.device_manager.check_device_status()
                
                # Warte bis zum nächsten Intervall
                time.sleep(status_check_interval)
            except Exception as e:
                logger.error(f"Fehler in der Automatisierungsschleife: {e}")
                time.sleep(5)  # Kurze Pause bei Fehler
    
    def create_rule(self, name: str, description: str, device_id: str,
                   condition: Dict[str, Any], actions: List[Dict[str, Any]],
                   enabled: bool = True):
        """
        Erstellt eine neue Regel
        
        Args:
            name: Name der Regel
            description: Beschreibung der Regel
            device_id: ID des Geräts, für das die Regel gilt
            condition: Bedingung, die erfüllt sein muss, um die Regel auszulösen
            actions: Liste von Aktionen, die ausgeführt werden sollen
            enabled: Gibt an, ob die Regel aktiviert ist
            
        Returns:
            Neu erstellte Regel oder None bei Fehler
        """
        return self.rules_engine.create_rule(
            name=name,
            description=description,
            device_id=device_id,
            condition=condition,
            actions=actions,
            enabled=enabled
        )
    
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
        return self.device_manager.send_actuator_command(device_id, actuator_id, command)

# Einfache Funktion zum Abrufen der Automation
def get_automation() -> Automation:
    """
    Gibt die Automation zurück
    
    Returns:
        Automation-Instanz
    """
    return Automation() 