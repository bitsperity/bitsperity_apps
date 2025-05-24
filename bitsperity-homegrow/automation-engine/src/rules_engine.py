#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import uuid
import time
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime

from .models.rule import Rule
from .models.device import Device
from .database import get_database
from .device_manager import get_device_manager
from .logger import get_logger

logger = get_logger(__name__)

class RulesEngine:
    """Regelwerk für die Automatisierung der HomeGrow-Geräte"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """Singleton-Pattern für die RulesEngine"""
        if cls._instance is None:
            cls._instance = super(RulesEngine, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialisiert die RulesEngine"""
        if self._initialized:
            return
            
        self.db = get_database()
        self.device_manager = get_device_manager()
        
        # Cache für Regeln
        self.rules = {}
        
        # Lade Regeln aus der Datenbank
        self._load_rules()
        
        # Thread für die Regelauswertung
        self.running = False
        self.thread = None
        
        self._initialized = True
    
    def _load_rules(self):
        """Lädt alle Regeln aus der Datenbank"""
        try:
            # Hole alle Geräte
            devices = self.device_manager.get_all_devices()
            
            for device in devices:
                # Hole Regeln für jedes Gerät
                rules_data = self.db.get_rules_for_device(device.device_id)
                
                for rule_data in rules_data:
                    rule = Rule.from_dict(rule_data)
                    
                    # Speichere die Regel im Cache
                    if device.device_id not in self.rules:
                        self.rules[device.device_id] = []
                    
                    self.rules[device.device_id].append(rule)
            
            total_rules = sum(len(rules) for rules in self.rules.values())
            logger.info(f"{total_rules} Regeln aus der Datenbank geladen")
        except Exception as e:
            logger.error(f"Fehler beim Laden der Regeln: {e}")
    
    def get_rules_for_device(self, device_id: str) -> List[Rule]:
        """
        Gibt alle Regeln für ein Gerät zurück
        
        Args:
            device_id: ID des Geräts
            
        Returns:
            Liste der Regeln
        """
        return self.rules.get(device_id, [])
    
    def create_rule(self, name: str, description: str, device_id: str,
                   condition: Dict[str, Any], actions: List[Dict[str, Any]],
                   enabled: bool = True) -> Optional[Rule]:
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
        try:
            # Generiere eine eindeutige ID für die Regel
            rule_id = str(uuid.uuid4())
            
            # Erstelle die Regel
            rule = Rule(
                rule_id=rule_id,
                name=name,
                description=description,
                device_id=device_id,
                condition=condition,
                actions=actions,
                enabled=enabled
            )
            
            # Speichere die Regel in der Datenbank
            if not self.db.save_rule(rule.to_dict()):
                logger.error(f"Fehler beim Speichern der Regel {rule_id}")
                return None
            
            # Füge die Regel zum Cache hinzu
            if device_id not in self.rules:
                self.rules[device_id] = []
            
            self.rules[device_id].append(rule)
            
            logger.info(f"Neue Regel erstellt: {rule_id} - {name}")
            return rule
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Regel: {e}")
            return None
    
    def update_rule(self, rule: Rule) -> bool:
        """
        Aktualisiert eine Regel
        
        Args:
            rule: Rule-Objekt
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Aktualisiere die Regel in der Datenbank
            if not self.db.save_rule(rule.to_dict()):
                logger.error(f"Fehler beim Aktualisieren der Regel {rule.rule_id}")
                return False
            
            # Aktualisiere die Regel im Cache
            device_id = rule.device_id
            if device_id in self.rules:
                # Finde die Regel im Cache
                for i, cached_rule in enumerate(self.rules[device_id]):
                    if cached_rule.rule_id == rule.rule_id:
                        # Ersetze die Regel
                        self.rules[device_id][i] = rule
                        break
            
            logger.info(f"Regel aktualisiert: {rule.rule_id} - {rule.name}")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Regel: {e}")
            return False
    
    def delete_rule(self, rule_id: str) -> bool:
        """
        Löscht eine Regel
        
        Args:
            rule_id: ID der Regel
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Lösche die Regel aus der Datenbank
            if not self.db.delete_rule(rule_id):
                logger.error(f"Fehler beim Löschen der Regel {rule_id}")
                return False
            
            # Lösche die Regel aus dem Cache
            for device_id, rules in self.rules.items():
                for i, rule in enumerate(rules):
                    if rule.rule_id == rule_id:
                        # Entferne die Regel
                        self.rules[device_id].pop(i)
                        break
            
            logger.info(f"Regel gelöscht: {rule_id}")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Löschen der Regel: {e}")
            return False
    
    def evaluate_rules(self):
        """Wertet alle Regeln für alle Geräte aus"""
        try:
            # Hole alle Geräte
            devices = self.device_manager.get_all_devices()
            
            for device in devices:
                # Überspringe offline Geräte
                if not device.online:
                    continue
                
                # Hole Regeln für das Gerät
                device_rules = self.get_rules_for_device(device.device_id)
                
                # Überspringe, wenn keine Regeln vorhanden sind
                if not device_rules:
                    continue
                
                # Werte jede Regel aus
                for rule in device_rules:
                    # Überspringe deaktivierte Regeln
                    if not rule.enabled:
                        continue
                    
                    # Überprüfe die Bedingung
                    if rule.check_condition(device.to_dict()):
                        # Führe die Aktionen aus
                        self._execute_actions(rule, device)
                        
                        # Markiere die Regel als ausgelöst
                        rule.mark_triggered()
                        self.update_rule(rule)
        except Exception as e:
            logger.error(f"Fehler bei der Regelauswertung: {e}")
    
    def _execute_actions(self, rule: Rule, device: Device):
        """
        Führt die Aktionen einer Regel aus
        
        Args:
            rule: Ausgelöste Regel
            device: Gerät, für das die Regel gilt
        """
        try:
            logger.info(f"Regel '{rule.name}' für Gerät {device.device_id} ausgelöst")
            
            for action in rule.actions:
                action_type = action.get('type')
                
                if action_type == 'actuator':
                    # Aktuator-Aktion
                    actuator_id = action.get('actuator_id')
                    command = action.get('command', {})
                    
                    if actuator_id:
                        # Sende den Befehl an den Aktuator
                        self.device_manager.send_actuator_command(
                            device.device_id, actuator_id, command
                        )
                        logger.info(f"Aktuatorbefehl an {actuator_id} gesendet: {command}")
                elif action_type == 'notification':
                    # Benachrichtigungs-Aktion (hier nur Logging)
                    message = action.get('message', 'Keine Nachricht')
                    logger.info(f"Benachrichtigung für Gerät {device.device_id}: {message}")
                else:
                    logger.warning(f"Unbekannter Aktionstyp: {action_type}")
        except Exception as e:
            logger.error(f"Fehler beim Ausführen der Aktionen: {e}")
    
    def start(self, check_interval: int = 60):
        """
        Startet die Regelauswertung in einem separaten Thread
        
        Args:
            check_interval: Intervall für die Regelauswertung in Sekunden
        """
        if self.running:
            logger.warning("RulesEngine läuft bereits")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, args=(check_interval,))
        self.thread.daemon = True
        self.thread.start()
        
        logger.info(f"RulesEngine gestartet (Intervall: {check_interval} Sekunden)")
    
    def stop(self):
        """Stoppt die Regelauswertung"""
        if not self.running:
            logger.warning("RulesEngine läuft nicht")
            return
            
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
            self.thread = None
            
        logger.info("RulesEngine gestoppt")
    
    def _run_loop(self, check_interval: int):
        """
        Hauptschleife für die Regelauswertung
        
        Args:
            check_interval: Intervall für die Regelauswertung in Sekunden
        """
        while self.running:
            try:
                # Werte alle Regeln aus
                self.evaluate_rules()
                
                # Warte bis zum nächsten Intervall
                time.sleep(check_interval)
            except Exception as e:
                logger.error(f"Fehler in der RulesEngine-Schleife: {e}")
                time.sleep(5)  # Kurze Pause bei Fehler

# Einfache Funktion zum Abrufen der RulesEngine
def get_rules_engine() -> RulesEngine:
    """
    Gibt die RulesEngine zurück
    
    Returns:
        RulesEngine-Instanz
    """
    return RulesEngine() 