#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import colorlog

class Logger:
    """Konfiguration und Bereitstellung von Loggern für die Anwendung"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """Singleton-Pattern für den Logger"""
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, config=None):
        """Initialisiert den Logger mit der angegebenen Konfiguration"""
        if self._initialized:
            return
        
        self.config = config or {}
        self.setup()
        self._initialized = True
    
    def setup(self):
        """Konfiguriert das Logging-System"""
        log_level = self._get_log_level()
        log_file = self.config.get('file', None)
        
        # Erstelle Handler für Konsole
        console_handler = colorlog.StreamHandler()
        console_handler.setFormatter(colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        ))
        
        # Erstelle Handler für Datei, falls konfiguriert
        handlers = [console_handler]
        if log_file:
            # Stelle sicher, dass das Verzeichnis existiert
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            handlers.append(file_handler)
        
        # Konfiguriere Root-Logger
        logging.basicConfig(
            level=log_level,
            handlers=handlers,
            force=True
        )
        
        # Setze Log-Level für externe Bibliotheken
        logging.getLogger('paho.mqtt').setLevel(logging.WARNING)
        logging.getLogger('pymongo').setLevel(logging.WARNING)
    
    def _get_log_level(self):
        """Ermittelt das Log-Level aus der Konfiguration"""
        level_str = self.config.get('level', 'info').upper()
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return level_map.get(level_str, logging.INFO)
    
    def get_logger(self, name):
        """Gibt einen Logger mit dem angegebenen Namen zurück"""
        return logging.getLogger(name)

# Einfache Funktion zum Abrufen eines Loggers
def get_logger(name):
    """Gibt einen Logger mit dem angegebenen Namen zurück"""
    return Logger().get_logger(name) 