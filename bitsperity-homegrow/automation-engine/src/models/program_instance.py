#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import uuid

from .program_template import ProgramTemplate

class LogEntry:
    """Klasse zur Repräsentation eines Logeintrags in einer Programminstanz"""
    
    def __init__(self,
                 action: str,
                 data: Dict[str, Any] = None,
                 timestamp: Optional[datetime] = None):
        """
        Initialisiert einen Logeintrag
        
        Args:
            action: Art der Aktion (z.B. "program_started", "ph_correction")
            data: Zusätzliche Daten zur Aktion
            timestamp: Zeitstempel, wird auf jetzt gesetzt falls nicht angegeben
        """
        self.action = action
        self.data = data or {}
        self.timestamp = timestamp or datetime.utcnow()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """
        Erstellt ein LogEntry-Objekt aus einem Dictionary
        
        Args:
            data: Dictionary mit Logeintrag-Daten
            
        Returns:
            LogEntry-Objekt
        """
        timestamp = data.get('timestamp')
        if timestamp and isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
        return cls(
            action=data.get('action', 'unknown'),
            data=data.get('data', {}),
            timestamp=timestamp
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert den Logeintrag in ein Dictionary
        
        Returns:
            Dictionary-Repräsentation des Logeintrags
        """
        return {
            'action': self.action,
            'data': self.data,
            'timestamp': self.timestamp.isoformat()
        }


class ProgramInstance:
    """Klasse zur Repräsentation einer laufenden Programminstanz"""
    
    # Mögliche Status einer Programminstanz
    STATUS_CREATED = "created"       # Erstellt, aber noch nicht gestartet
    STATUS_RUNNING = "running"       # Läuft aktiv
    STATUS_PAUSED = "paused"         # Pausiert
    STATUS_COMPLETED = "completed"   # Normal beendet
    STATUS_STOPPED = "stopped"       # Manuell gestoppt
    STATUS_ERROR = "error"           # Fehler aufgetreten
    
    def __init__(self,
                 template_id: str,
                 device_id: str,
                 template: Optional[ProgramTemplate] = None,
                 instance_id: Optional[str] = None,
                 status: str = STATUS_CREATED,
                 current_phase: int = 0,
                 log: Optional[List[LogEntry]] = None,
                 created_at: Optional[datetime] = None,
                 started_at: Optional[datetime] = None,
                 paused_at: Optional[datetime] = None,
                 completed_at: Optional[datetime] = None):
        """
        Initialisiert eine Programminstanz
        
        Args:
            template_id: ID der zugrundeliegenden Programmvorlage
            device_id: ID des zugehörigen Geräts
            template: Optional die vollständige Programmvorlage
            instance_id: ID der Programminstanz, wird generiert falls nicht angegeben
            status: Status der Programminstanz
            current_phase: Index der aktuellen Phase (0-basiert)
            log: Liste von Logeinträgen
            created_at: Erstellungszeitpunkt, wird auf jetzt gesetzt falls nicht angegeben
            started_at: Startzeitpunkt, None wenn noch nicht gestartet
            paused_at: Zeitpunkt der Pausierung, None wenn nicht pausiert
            completed_at: Zeitpunkt der Beendigung, None wenn nicht beendet
        """
        self.instance_id = instance_id or str(uuid.uuid4())
        self.template_id = template_id
        self.device_id = device_id
        self.template = template
        self.status = status
        self.current_phase = current_phase
        self.log = log or []
        
        now = datetime.utcnow()
        self.created_at = created_at or now
        self.started_at = started_at
        self.paused_at = paused_at
        self.completed_at = completed_at
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], template: Optional[ProgramTemplate] = None) -> 'ProgramInstance':
        """
        Erstellt ein ProgramInstance-Objekt aus einem Dictionary
        
        Args:
            data: Dictionary mit Programminstanz-Daten
            template: Optional die vollständige Programmvorlage
            
        Returns:
            ProgramInstance-Objekt
        """
        # Logeinträge verarbeiten
        log_entries = []
        log_data = data.get('log', [])
        if log_data:
            for log_item in log_data:
                log_entries.append(LogEntry.from_dict(log_item))
        
        # Zeitstempel verarbeiten
        def parse_timestamp(ts):
            if ts and isinstance(ts, str):
                return datetime.fromisoformat(ts.replace('Z', '+00:00'))
            return ts
            
        created_at = parse_timestamp(data.get('created_at'))
        started_at = parse_timestamp(data.get('started_at'))
        paused_at = parse_timestamp(data.get('paused_at'))
        completed_at = parse_timestamp(data.get('completed_at'))
        
        return cls(
            template_id=data.get('template_id'),
            device_id=data.get('device_id'),
            template=template,
            instance_id=data.get('instance_id'),
            status=data.get('status', cls.STATUS_CREATED),
            current_phase=data.get('current_phase', 0),
            log=log_entries,
            created_at=created_at,
            started_at=started_at,
            paused_at=paused_at,
            completed_at=completed_at
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert die Programminstanz in ein Dictionary
        
        Returns:
            Dictionary-Repräsentation der Programminstanz
        """
        log_dict = [entry.to_dict() for entry in self.log]
        
        result = {
            'instance_id': self.instance_id,
            'template_id': self.template_id,
            'device_id': self.device_id,
            'status': self.status,
            'current_phase': self.current_phase,
            'log': log_dict,
            'created_at': self.created_at.isoformat()
        }
        
        # Optionale Zeitstempel nur hinzufügen, wenn vorhanden
        if self.started_at:
            result['started_at'] = self.started_at.isoformat()
        if self.paused_at:
            result['paused_at'] = self.paused_at.isoformat()
        if self.completed_at:
            result['completed_at'] = self.completed_at.isoformat()
            
        return result
    
    def add_log_entry(self, action: str, data: Dict[str, Any] = None) -> LogEntry:
        """
        Fügt einen neuen Logeintrag hinzu
        
        Args:
            action: Art der Aktion
            data: Zusätzliche Daten zur Aktion
            
        Returns:
            Erstellter LogEntry
        """
        entry = LogEntry(action, data)
        self.log.append(entry)
        return entry
    
    def start(self) -> bool:
        """
        Startet die Programminstanz
        
        Returns:
            True wenn erfolgreich gestartet, False wenn nicht (z.B. bereits laufend)
        """
        if self.status in [self.STATUS_CREATED, self.STATUS_PAUSED]:
            self.status = self.STATUS_RUNNING
            
            # Wenn zum ersten Mal gestartet, Startzeit setzen
            if not self.started_at:
                self.started_at = datetime.utcnow()
                self.add_log_entry("program_started")
            else:
                # Wenn aus Pause fortgesetzt
                self.paused_at = None
                self.add_log_entry("program_resumed")
                
            return True
        return False
    
    def pause(self) -> bool:
        """
        Pausiert die Programminstanz
        
        Returns:
            True wenn erfolgreich pausiert, False wenn nicht (z.B. nicht laufend)
        """
        if self.status == self.STATUS_RUNNING:
            self.status = self.STATUS_PAUSED
            self.paused_at = datetime.utcnow()
            self.add_log_entry("program_paused")
            return True
        return False
    
    def stop(self) -> bool:
        """
        Stoppt die Programminstanz
        
        Returns:
            True wenn erfolgreich gestoppt, False wenn nicht (z.B. bereits beendet)
        """
        if self.status in [self.STATUS_RUNNING, self.STATUS_PAUSED]:
            self.status = self.STATUS_STOPPED
            self.completed_at = datetime.utcnow()
            self.add_log_entry("program_stopped")
            return True
        return False
    
    def complete(self) -> bool:
        """
        Markiert die Programminstanz als erfolgreich abgeschlossen
        
        Returns:
            True wenn erfolgreich markiert, False wenn nicht (z.B. bereits beendet)
        """
        if self.status in [self.STATUS_RUNNING, self.STATUS_PAUSED]:
            self.status = self.STATUS_COMPLETED
            self.completed_at = datetime.utcnow()
            self.add_log_entry("program_completed")
            return True
        return False
    
    def set_error(self, error_message: str) -> bool:
        """
        Markiert die Programminstanz als fehlerhaft
        
        Args:
            error_message: Fehlermeldung
            
        Returns:
            True wenn erfolgreich markiert, False wenn nicht (z.B. bereits beendet)
        """
        if self.status in [self.STATUS_RUNNING, self.STATUS_PAUSED]:
            self.status = self.STATUS_ERROR
            self.completed_at = datetime.utcnow()
            self.add_log_entry("program_error", {"error_message": error_message})
            return True
        return False
    
    def is_active(self) -> bool:
        """
        Prüft, ob die Programminstanz aktiv ist (laufend oder pausiert)
        
        Returns:
            True wenn aktiv, False wenn nicht
        """
        return self.status in [self.STATUS_RUNNING, self.STATUS_PAUSED]
    
    def get_current_phase(self) -> Optional[Dict[str, Any]]:
        """
        Gibt die aktuelle Phase als Dictionary zurück
        
        Returns:
            Aktuelle Phase als Dictionary oder None, wenn keine Vorlage oder ungültiger Index
        """
        if not self.template or not self.template.phases:
            return None
            
        if 0 <= self.current_phase < len(self.template.phases):
            return self.template.phases[self.current_phase].to_dict()
            
        return None 