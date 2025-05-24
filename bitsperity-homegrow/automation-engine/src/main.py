#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import signal
import time
import argparse
from typing import Dict, Any

from .config import Config, get_config
from .logger import Logger, get_logger
from .database import get_database
from .mqtt_client import get_mqtt_client
from .device_manager import get_device_manager
from .config_manager import get_config_manager
from .rules_engine import get_rules_engine
from .automation import get_automation
from .program_engine import get_program_engine

# Initialisiere den Logger
logger = get_logger(__name__)

class HomeGrowServer:
    """Hauptklasse für den HomeGrow Server"""
    
    def __init__(self, config_path: str = None):
        """
        Initialisiert den HomeGrow Server
        
        Args:
            config_path: Pfad zur Konfigurationsdatei
        """
        # Initialisiere die Konfiguration
        self.config = Config(config_path)
        
        # Initialisiere den Logger
        self.logger = Logger(self.config.get_logging_config())
        
        # Initialisiere die Komponenten
        self.db = get_database()
        self.mqtt = get_mqtt_client()
        self.device_manager = get_device_manager()
        self.config_manager = get_config_manager()
        self.rules_engine = get_rules_engine()
        self.automation = get_automation()
        
        # Initialisiere die ProgramEngine
        # Übergebe den MQTT-Client, damit die Engine Befehle senden kann
        self.program_engine = get_program_engine(mqtt_client=self.mqtt)
        
        # Flag für den Serverstatus
        self.running = False
        
        # Signalhandler für sauberes Beenden
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def start(self):
        """Startet den HomeGrow Server"""
        try:
            logger.info("HomeGrow Server wird gestartet...")
            
            # Verbinde mit der Datenbank
            # (Wird bereits im Konstruktor von Database aufgerufen)
            
            # Verbinde mit dem MQTT-Broker
            self.mqtt.connect()
            
            # Starte die Automatisierung
            self.automation.start()
            
            # Starte die ProgramEngine
            self.program_engine.start()
            
            self.running = True
            logger.info("HomeGrow Server erfolgreich gestartet")
            
            # Hauptschleife
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Server wird durch Benutzer beendet")
        except Exception as e:
            logger.error(f"Fehler beim Starten des Servers: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stoppt den HomeGrow Server"""
        logger.info("HomeGrow Server wird beendet...")
        
        # Stoppe die ProgramEngine
        self.program_engine.stop()
        
        # Stoppe die Automatisierung
        self.automation.stop()
        
        # Trenne die MQTT-Verbindung
        self.mqtt.disconnect()
        
        # Schließe die Datenbankverbindung
        self.db.close()
        
        self.running = False
        logger.info("HomeGrow Server erfolgreich beendet")
    
    def _signal_handler(self, sig, frame):
        """Handler für Signale"""
        logger.info(f"Signal {sig} empfangen, Server wird beendet")
        self.stop()
        sys.exit(0)

def parse_arguments():
    """Parst die Kommandozeilenargumente"""
    parser = argparse.ArgumentParser(description='HomeGrow Server')
    parser.add_argument('-c', '--config', help='Pfad zur Konfigurationsdatei')
    return parser.parse_args()

def main():
    """Hauptfunktion"""
    # Parse Kommandozeilenargumente
    args = parse_arguments()
    
    # Starte den Server
    server = HomeGrowServer(args.config)
    server.start()

if __name__ == '__main__':
    main() 