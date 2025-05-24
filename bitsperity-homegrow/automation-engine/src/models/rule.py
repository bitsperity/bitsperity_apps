#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Dict, Any, Optional, List, Callable

class Rule:
    """Repräsentiert eine Automatisierungsregel im System"""
    
    def __init__(self, rule_id: str, name: str, description: str,
                 device_id: str, condition: Dict[str, Any],
                 actions: List[Dict[str, Any]], enabled: bool = True,
                 created_at: Optional[datetime] = None,
                 last_triggered: Optional[datetime] = None):
        """
        Initialisiert eine neue Regel
        
        Args:
            rule_id: Eindeutige ID der Regel
            name: Name der Regel
            description: Beschreibung der Regel
            device_id: ID des Geräts, für das die Regel gilt
            condition: Bedingung, die erfüllt sein muss, um die Regel auszulösen
            actions: Liste von Aktionen, die ausgeführt werden sollen
            enabled: Gibt an, ob die Regel aktiviert ist
            created_at: Zeitpunkt der Erstellung
            last_triggered: Zeitpunkt der letzten Auslösung
        """
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.device_id = device_id
        self.condition = condition
        self.actions = actions
        self.enabled = enabled
        self.created_at = created_at or datetime.utcnow()
        self.last_triggered = last_triggered
    
    def check_condition(self, device_data: Dict[str, Any]) -> bool:
        """
        Überprüft, ob die Bedingung der Regel erfüllt ist
        
        Args:
            device_data: Aktuelle Daten des Geräts
            
        Returns:
            True, wenn die Bedingung erfüllt ist, sonst False
        """
        sensor_type = self.condition.get('sensor_type')
        operator = self.condition.get('operator')
        value = self.condition.get('value')
        
        if not sensor_type or not operator or value is None:
            return False
        
        # Hole den aktuellen Sensorwert
        sensor_data = device_data.get('sensors', {}).get(sensor_type, {})
        current_value = sensor_data.get('value')
        
        if current_value is None:
            return False
        
        # Überprüfe die Bedingung
        if operator == 'eq':
            return current_value == value
        elif operator == 'neq':
            return current_value != value
        elif operator == 'gt':
            return current_value > value
        elif operator == 'gte':
            return current_value >= value
        elif operator == 'lt':
            return current_value < value
        elif operator == 'lte':
            return current_value <= value
        elif operator == 'between':
            min_val, max_val = value
            return min_val <= current_value <= max_val
        
        return False
    
    def mark_triggered(self):
        """Markiert die Regel als ausgelöst"""
        self.last_triggered = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert die Regel in ein Dictionary für die Speicherung"""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'device_id': self.device_id,
            'condition': self.condition,
            'actions': self.actions,
            'enabled': self.enabled,
            'created_at': self.created_at,
            'last_triggered': self.last_triggered
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Rule':
        """
        Erstellt eine Regel aus einem Dictionary
        
        Args:
            data: Dictionary mit Regeldaten
            
        Returns:
            Ein neues Rule-Objekt
        """
        return cls(
            rule_id=data['rule_id'],
            name=data['name'],
            description=data['description'],
            device_id=data['device_id'],
            condition=data['condition'],
            actions=data['actions'],
            enabled=data.get('enabled', True),
            created_at=data.get('created_at'),
            last_triggered=data.get('last_triggered')
        ) 