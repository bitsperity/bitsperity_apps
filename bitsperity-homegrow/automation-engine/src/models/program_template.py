#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

class NutrientRatio:
    """Klasse zur Repräsentation des Nährstoffverhältnisses für eine Phase"""
    
    def __init__(self, 
                 nutrient1_percent: float = 33.33,
                 nutrient2_percent: float = 33.33,
                 nutrient3_percent: float = 33.34):
        """
        Initialisiert das Nährstoffverhältnis
        
        Args:
            nutrient1_percent: Prozentanteil Nährstoff 1 (0-100)
            nutrient2_percent: Prozentanteil Nährstoff 2 (0-100)
            nutrient3_percent: Prozentanteil Nährstoff 3 (0-100)
        """
        # Sicherstellen, dass die Summe 100% ergibt
        total = nutrient1_percent + nutrient2_percent + nutrient3_percent
        if abs(total - 100) > 0.1:  # Kleine Toleranz für Rundungsfehler
            # Normalisieren auf 100%
            factor = 100 / total
            nutrient1_percent *= factor
            nutrient2_percent *= factor
            nutrient3_percent *= factor
        
        self.nutrient1_percent = round(nutrient1_percent, 2)
        self.nutrient2_percent = round(nutrient2_percent, 2)
        self.nutrient3_percent = round(nutrient3_percent, 2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NutrientRatio':
        """
        Erstellt ein NutrientRatio-Objekt aus einem Dictionary
        
        Args:
            data: Dictionary mit Nährstoffverhältnis-Daten
            
        Returns:
            NutrientRatio-Objekt
        """
        return cls(
            nutrient1_percent=data.get('nutrient1_percent', 33.33),
            nutrient2_percent=data.get('nutrient2_percent', 33.33),
            nutrient3_percent=data.get('nutrient3_percent', 33.34)
        )
    
    def to_dict(self) -> Dict[str, float]:
        """
        Konvertiert das Nährstoffverhältnis in ein Dictionary
        
        Returns:
            Dictionary-Repräsentation des Nährstoffverhältnisses
        """
        return {
            'nutrient1_percent': self.nutrient1_percent,
            'nutrient2_percent': self.nutrient2_percent,
            'nutrient3_percent': self.nutrient3_percent
        }


class SensorTargets:
    """Klasse zur Repräsentation der Zielwerte für Sensoren in einer Phase"""
    
    def __init__(self, 
                 ph_min: float = 5.5,
                 ph_max: float = 6.5,
                 tds_min: float = 500,
                 tds_max: float = 700):
        """
        Initialisiert die Sensor-Zielwerte
        
        Args:
            ph_min: Minimaler pH-Wert
            ph_max: Maximaler pH-Wert
            tds_min: Minimaler TDS-Wert
            tds_max: Maximaler TDS-Wert
        """
        self.ph_min = ph_min
        self.ph_max = ph_max
        self.tds_min = tds_min
        self.tds_max = tds_max
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SensorTargets':
        """
        Erstellt ein SensorTargets-Objekt aus einem Dictionary
        
        Args:
            data: Dictionary mit Sensor-Zielwerte-Daten
            
        Returns:
            SensorTargets-Objekt
        """
        return cls(
            ph_min=data.get('ph_min', 5.5),
            ph_max=data.get('ph_max', 6.5),
            tds_min=data.get('tds_min', 500),
            tds_max=data.get('tds_max', 700)
        )
    
    def to_dict(self) -> Dict[str, float]:
        """
        Konvertiert die Sensor-Zielwerte in ein Dictionary
        
        Returns:
            Dictionary-Repräsentation der Sensor-Zielwerte
        """
        return {
            'ph_min': self.ph_min,
            'ph_max': self.ph_max,
            'tds_min': self.tds_min,
            'tds_max': self.tds_max
        }


class Phase:
    """Klasse zur Repräsentation einer Phase in einem Programm"""
    
    def __init__(self,
                 name: str,
                 targets: Optional[SensorTargets] = None,
                 nutrient_ratio: Optional[NutrientRatio] = None,
                 duration_days: int = 14,
                 phase_id: Optional[str] = None,
                 water_pump_cycle_minutes: int = 0,
                 water_pump_on_minutes: int = 0,
                 air_pump_cycle_minutes: int = 0,
                 air_pump_on_minutes: int = 0):
        """
        Initialisiert eine Phase
        
        Args:
            name: Name der Phase
            targets: Zielwerte für Sensoren, wird mit Standardwerten initialisiert falls nicht angegeben
            nutrient_ratio: Nährstoffverhältnis, wird mit Standardwerten initialisiert falls nicht angegeben
            duration_days: Dauer der Phase in Tagen
            phase_id: ID der Phase, wird generiert falls nicht angegeben
            water_pump_cycle_minutes: Zyklusdauer der Wasserpumpe in Minuten (0 = deaktiviert)
            water_pump_on_minutes: Einschaltdauer der Wasserpumpe in Minuten
            air_pump_cycle_minutes: Zyklusdauer der Luftpumpe in Minuten (0 = deaktiviert)
            air_pump_on_minutes: Einschaltdauer der Luftpumpe in Minuten
        """
        self.phase_id = phase_id or str(uuid.uuid4())
        self.name = name
        self.targets = targets or SensorTargets()
        self.nutrient_ratio = nutrient_ratio or NutrientRatio()
        self.duration_days = duration_days
        
        # Pumpenzykluswerte speichern
        self.water_pump_cycle_minutes = water_pump_cycle_minutes
        self.water_pump_on_minutes = water_pump_on_minutes
        self.air_pump_cycle_minutes = air_pump_cycle_minutes
        self.air_pump_on_minutes = air_pump_on_minutes
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Phase':
        """
        Erstellt ein Phase-Objekt aus einem Dictionary
        
        Args:
            data: Dictionary mit Phasen-Daten
            
        Returns:
            Phase-Objekt
        """
        targets = SensorTargets.from_dict(data.get('targets', {}))
        nutrient_ratio = NutrientRatio.from_dict(data.get('nutrient_ratio', {}))
        
        # Pumpenzykluswerte auslesen
        water_pump_cycle_minutes = data.get('water_pump_cycle_minutes', 0)
        water_pump_on_minutes = data.get('water_pump_on_minutes', 0)
        air_pump_cycle_minutes = data.get('air_pump_cycle_minutes', 0)
        air_pump_on_minutes = data.get('air_pump_on_minutes', 0)
        
        return cls(
            name=data.get('name', 'Standard-Phase'),
            targets=targets,
            nutrient_ratio=nutrient_ratio,
            duration_days=data.get('duration_days', 14),
            phase_id=data.get('phase_id'),
            water_pump_cycle_minutes=water_pump_cycle_minutes,
            water_pump_on_minutes=water_pump_on_minutes,
            air_pump_cycle_minutes=air_pump_cycle_minutes,
            air_pump_on_minutes=air_pump_on_minutes
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert die Phase in ein Dictionary
        
        Returns:
            Dictionary-Repräsentation der Phase
        """
        result = {
            'phase_id': self.phase_id,
            'name': self.name,
            'targets': self.targets.to_dict(),
            'nutrient_ratio': self.nutrient_ratio.to_dict(),
            'duration_days': self.duration_days
        }
        
        # Pumpenzykluswerte hinzufügen
        result['water_pump_cycle_minutes'] = self.water_pump_cycle_minutes
        result['water_pump_on_minutes'] = self.water_pump_on_minutes
        result['air_pump_cycle_minutes'] = self.air_pump_cycle_minutes
        result['air_pump_on_minutes'] = self.air_pump_on_minutes
        
        return result


class ProgramTemplate:
    """Klasse zur Repräsentation einer Programmvorlage"""
    
    def __init__(self,
                 name: str,
                 description: str = "",
                 phases: Optional[List[Phase]] = None,
                 template_id: Optional[str] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        """
        Initialisiert eine Programmvorlage
        
        Args:
            name: Name der Programmvorlage
            description: Beschreibung der Programmvorlage
            phases: Liste der Phasen, wird mit einer Standardphase initialisiert falls nicht angegeben
            template_id: ID der Programmvorlage, wird generiert falls nicht angegeben
            created_at: Erstellungszeitpunkt, wird auf jetzt gesetzt falls nicht angegeben
            updated_at: Aktualisierungszeitpunkt, wird auf jetzt gesetzt falls nicht angegeben
        """
        self.template_id = template_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        
        # Mindestens eine Phase ist erforderlich
        if not phases:
            phases = [Phase(name="Standard-Phase")]
        self.phases = phases
        
        now = datetime.utcnow()
        self.created_at = created_at or now
        self.updated_at = updated_at or now
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProgramTemplate':
        """
        Erstellt ein ProgramTemplate-Objekt aus einem Dictionary
        
        Args:
            data: Dictionary mit Programmvorlagen-Daten
            
        Returns:
            ProgramTemplate-Objekt
        """
        # Phasen verarbeiten
        phases = []
        phase_data = data.get('phases', [])
        if phase_data:
            for phase_item in phase_data:
                phases.append(Phase.from_dict(phase_item))
        
        # Zeitstempel verarbeiten
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
        updated_at = data.get('updated_at')
        if updated_at and isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        
        return cls(
            name=data.get('name', 'Unbenannte Vorlage'),
            description=data.get('description', ''),
            phases=phases,
            template_id=data.get('template_id'),
            created_at=created_at,
            updated_at=updated_at
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert die Programmvorlage in ein Dictionary
        
        Returns:
            Dictionary-Repräsentation der Programmvorlage
        """
        phases_dict = [phase.to_dict() for phase in self.phases]
        
        return {
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'phases': phases_dict,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def update(self, data: Dict[str, Any]) -> None:
        """
        Aktualisiert die Programmvorlage mit neuen Daten
        
        Args:
            data: Dictionary mit Aktualisierungsdaten
        """
        if 'name' in data:
            self.name = data['name']
            
        if 'description' in data:
            self.description = data['description']
            
        if 'phases' in data:
            phases = []
            for phase_item in data['phases']:
                phases.append(Phase.from_dict(phase_item))
            self.phases = phases
            
        self.updated_at = datetime.utcnow() 