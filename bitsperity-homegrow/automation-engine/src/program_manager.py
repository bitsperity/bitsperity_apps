#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import uuid

from .database import get_database
from .logger import get_logger
from .models.program_template import ProgramTemplate, Phase
from .models.program_instance import ProgramInstance

logger = get_logger(__name__)

class ProgramManager:
    """
    Verwaltet Programmvorlagen und -instanzen für das HomeGrow-System.
    Stellt eine Schnittstelle zwischen der Datenbank und der Programmausführung dar.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton-Pattern für den ProgramManager"""
        if cls._instance is None:
            cls._instance = super(ProgramManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialisiert den ProgramManager"""
        if self._initialized:
            return
            
        self.db = get_database()
        self._initialized = True
        logger.info("ProgramManager initialisiert")
    
    # Programmvorlagen-Methoden
    
    def get_program_template(self, template_id: str) -> Optional[ProgramTemplate]:
        """
        Lädt eine Programmvorlage aus der Datenbank
        
        Args:
            template_id: ID der Programmvorlage
            
        Returns:
            ProgramTemplate-Objekt oder None, wenn nicht gefunden
        """
        template_data = self.db.get_program_template(template_id)
        if not template_data:
            return None
            
        return ProgramTemplate.from_dict(template_data)
    
    def get_all_program_templates(self) -> List[ProgramTemplate]:
        """
        Lädt alle Programmvorlagen aus der Datenbank
        
        Returns:
            Liste von ProgramTemplate-Objekten
        """
        templates_data = self.db.get_all_program_templates()
        return [ProgramTemplate.from_dict(template) for template in templates_data]
    
    def save_program_template(self, template: ProgramTemplate) -> bool:
        """
        Speichert eine Programmvorlage in der Datenbank
        
        Args:
            template: ProgramTemplate-Objekt
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        # Aktualisiere updated_at Zeitstempel
        template.updated_at = datetime.utcnow()
        
        template_dict = template.to_dict()
        return self.db.save_program_template(template_dict)
    
    def create_program_template(self, name: str, description: str = "", phases: Optional[List[Dict[str, Any]]] = None) -> ProgramTemplate:
        """
        Erstellt eine neue Programmvorlage
        
        Args:
            name: Name der Programmvorlage
            description: Beschreibung der Programmvorlage
            phases: Optionale Liste von Phasen-Dictionaries
            
        Returns:
            Erstelltes ProgramTemplate-Objekt
        """
        phase_objects = []
        if phases:
            for phase_data in phases:
                phase_objects.append(Phase.from_dict(phase_data))
                
        template = ProgramTemplate(
            name=name,
            description=description,
            phases=phase_objects
        )
        
        # In Datenbank speichern
        self.save_program_template(template)
        
        return template
    
    def update_program_template(self, template_id: str, update_data: Dict[str, Any]) -> Optional[ProgramTemplate]:
        """
        Aktualisiert eine vorhandene Programmvorlage
        
        Args:
            template_id: ID der Programmvorlage
            update_data: Dictionary mit zu aktualisierenden Feldern
            
        Returns:
            Aktualisiertes ProgramTemplate-Objekt oder None, wenn nicht gefunden
        """
        template = self.get_program_template(template_id)
        if not template:
            logger.error(f"Programmvorlage mit ID {template_id} nicht gefunden")
            return None
            
        template.update(update_data)
        success = self.save_program_template(template)
        
        return template if success else None
    
    def delete_program_template(self, template_id: str) -> bool:
        """
        Löscht eine Programmvorlage
        
        Args:
            template_id: ID der Programmvorlage
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        return self.db.delete_program_template(template_id)
    
    # Programminstanzen-Methoden
    
    def get_program_instance(self, instance_id: str) -> Optional[ProgramInstance]:
        """
        Lädt eine Programminstanz aus der Datenbank
        
        Args:
            instance_id: ID der Programminstanz
            
        Returns:
            ProgramInstance-Objekt oder None, wenn nicht gefunden
        """
        instance_data = self.db.get_program_instance(instance_id)
        if not instance_data:
            return None
        
        # Lade zugehörige Vorlage
        template = None
        if template_id := instance_data.get('template_id'):
            template = self.get_program_template(template_id)
            
        return ProgramInstance.from_dict(instance_data, template)
    
    def get_active_program_instance(self, device_id: str) -> Optional[ProgramInstance]:
        """
        Lädt die aktive Programminstanz für ein Gerät
        
        Args:
            device_id: ID des Geräts
            
        Returns:
            Aktive ProgramInstance oder None, wenn keine gefunden
        """
        instance_data = self.db.get_active_program_instance(device_id)
        if not instance_data:
            return None
            
        # Lade zugehörige Vorlage
        template = None
        if template_id := instance_data.get('template_id'):
            template = self.get_program_template(template_id)
            
        return ProgramInstance.from_dict(instance_data, template)
    
    def get_program_instances_for_device(self, device_id: str) -> List[ProgramInstance]:
        """
        Lädt alle Programminstanzen für ein Gerät
        
        Args:
            device_id: ID des Geräts
            
        Returns:
            Liste von ProgramInstance-Objekten
        """
        instances_data = self.db.get_program_instances_for_device(device_id)
        
        instances = []
        for instance_data in instances_data:
            # Lade zugehörige Vorlage
            template = None
            if template_id := instance_data.get('template_id'):
                template = self.get_program_template(template_id)
                
            instances.append(ProgramInstance.from_dict(instance_data, template))
            
        return instances
    
    def save_program_instance(self, instance: ProgramInstance) -> bool:
        """
        Speichert eine Programminstanz in der Datenbank
        
        Args:
            instance: ProgramInstance-Objekt
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        instance_dict = instance.to_dict()
        return self.db.save_program_instance(instance_dict)
    
    def create_program_instance(self, device_id: str, template_id: str) -> Optional[ProgramInstance]:
        """
        Erstellt eine neue Programminstanz
        
        Args:
            device_id: ID des Geräts
            template_id: ID der Programmvorlage
            
        Returns:
            Erstellte ProgramInstance oder None bei Fehler
        """
        # Prüfe, ob bereits ein aktives Programm für dieses Gerät läuft
        active_instance = self.get_active_program_instance(device_id)
        if active_instance:
            logger.error(f"Es läuft bereits ein Programm für Gerät {device_id}")
            return None
            
        # Lade die Vorlage
        template = self.get_program_template(template_id)
        if not template:
            logger.error(f"Programmvorlage mit ID {template_id} nicht gefunden")
            return None
            
        # Erstelle neue Instanz
        instance = ProgramInstance(
            template_id=template_id,
            device_id=device_id,
            template=template
        )
        
        # Speichere in Datenbank
        success = self.save_program_instance(instance)
        
        return instance if success else None
    
    def start_program_instance(self, instance_id: str) -> Optional[ProgramInstance]:
        """
        Startet eine Programminstanz
        
        Args:
            instance_id: ID der Programminstanz
            
        Returns:
            Aktualisierte ProgramInstance oder None bei Fehler
        """
        instance = self.get_program_instance(instance_id)
        if not instance:
            logger.error(f"Programminstanz mit ID {instance_id} nicht gefunden")
            return None
            
        if instance.start():
            self.save_program_instance(instance)
            logger.info(f"Programminstanz {instance_id} für Gerät {instance.device_id} gestartet")
            return instance
        else:
            logger.error(f"Programminstanz {instance_id} konnte nicht gestartet werden (Status: {instance.status})")
            return None
    
    def pause_program_instance(self, instance_id: str) -> Optional[ProgramInstance]:
        """
        Pausiert eine Programminstanz
        
        Args:
            instance_id: ID der Programminstanz
            
        Returns:
            Aktualisierte ProgramInstance oder None bei Fehler
        """
        instance = self.get_program_instance(instance_id)
        if not instance:
            logger.error(f"Programminstanz mit ID {instance_id} nicht gefunden")
            return None
            
        if instance.pause():
            self.save_program_instance(instance)
            logger.info(f"Programminstanz {instance_id} pausiert")
            return instance
        else:
            logger.error(f"Programminstanz {instance_id} konnte nicht pausiert werden (Status: {instance.status})")
            return None
    
    def resume_program_instance(self, instance_id: str) -> Optional[ProgramInstance]:
        """
        Setzt eine pausierte Programminstanz fort
        
        Args:
            instance_id: ID der Programminstanz
            
        Returns:
            Aktualisierte ProgramInstance oder None bei Fehler
        """
        # Identisch zur start-Methode, da ProgramInstance.start() auch ein Resume durchführt
        return self.start_program_instance(instance_id)
    
    def stop_program_instance(self, instance_id: str) -> Optional[ProgramInstance]:
        """
        Stoppt eine Programminstanz
        
        Args:
            instance_id: ID der Programminstanz
            
        Returns:
            Aktualisierte ProgramInstance oder None bei Fehler
        """
        instance = self.get_program_instance(instance_id)
        if not instance:
            logger.error(f"Programminstanz mit ID {instance_id} nicht gefunden")
            return None
            
        if instance.stop():
            self.save_program_instance(instance)
            logger.info(f"Programminstanz {instance_id} gestoppt")
            return instance
        else:
            logger.error(f"Programminstanz {instance_id} konnte nicht gestoppt werden (Status: {instance.status})")
            return None
    
    def add_program_instance_log(self, instance_id: str, action: str, data: Dict[str, Any] = None) -> bool:
        """
        Fügt einen Logeintrag zu einer Programminstanz hinzu
        
        Args:
            instance_id: ID der Programminstanz
            action: Art der Aktion
            data: Zusätzliche Daten zur Aktion
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        instance = self.get_program_instance(instance_id)
        if not instance:
            logger.error(f"Programminstanz mit ID {instance_id} nicht gefunden")
            return False
            
        # Füge Logeintrag zum Objekt hinzu
        log_entry = instance.add_log_entry(action, data)
        
        # Direkter Datenbankzugriff für bessere Performance (nur Logeintrag hinzufügen)
        return self.db.add_program_instance_log(instance_id, log_entry.to_dict())


# Einfache Funktion zum Abrufen des ProgramManagers
def get_program_manager() -> ProgramManager:
    """
    Gibt den ProgramManager zurück
    
    Returns:
        ProgramManager-Instanz
    """
    return ProgramManager() 