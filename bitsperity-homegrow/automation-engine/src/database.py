#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymongo
from typing import Dict, Any, List, Optional
from datetime import datetime

from .config import get_config
from .logger import get_logger

logger = get_logger(__name__)

class Database:
    """Datenbankverbindung und -operationen für den HomeGrow Server"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """Singleton-Pattern für die Datenbankverbindung"""
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialisiert die Datenbankverbindung"""
        if self._initialized:
            return
            
        self.config = get_config()
        self.db_config = self.config.get_mongodb_config()
        
        self.client = None
        self.db = None
        self.connect()
        
        self._initialized = True
    
    def connect(self):
        """Stellt eine Verbindung zur Datenbank her"""
        try:
            uri = self.db_config.get('uri')
            db_name = self.db_config.get('database')
            
            logger.info(f"Verbinde mit MongoDB: {uri}, Datenbank: {db_name}")
            self.client = pymongo.MongoClient(uri)
            self.db = self.client[db_name]
            
            # Ping zur Überprüfung der Verbindung
            self.client.admin.command('ping')
            logger.info("MongoDB-Verbindung erfolgreich hergestellt")
            
            # Erstelle Indizes
            self._create_indexes()
        except Exception as e:
            logger.error(f"Fehler bei der Verbindung zur MongoDB: {e}")
            raise
    
    def _create_indexes(self):
        """Erstellt Indizes für die Collections"""
        try:
            # Sensordaten-Collection
            self.db.sensor_data.create_index([
                ("device_id", pymongo.ASCENDING),
                ("sensor_type", pymongo.ASCENDING),
                ("timestamp", pymongo.DESCENDING)
            ])
            
            # Regeln-Collection
            self.db.rules.create_index([("rule_id", pymongo.ASCENDING)], unique=True)
            self.db.rules.create_index([("device_id", pymongo.ASCENDING)])
            
            # Konfigurationen-Collection
            self.db.configs.create_index([("device_id", pymongo.ASCENDING)], unique=True)
            
            # Programmvorlagen-Collection
            self.db.program_templates.create_index([("template_id", pymongo.ASCENDING)], unique=True)
            
            # Programminstanzen-Collection
            self.db.program_instances.create_index([("instance_id", pymongo.ASCENDING)], unique=True)
            self.db.program_instances.create_index([("device_id", pymongo.ASCENDING)])
            self.db.program_instances.create_index([
                ("device_id", pymongo.ASCENDING),
                ("status", pymongo.ASCENDING)
            ])
            
            logger.info("MongoDB-Indizes erfolgreich erstellt")
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der MongoDB-Indizes: {e}")
    
    def close(self):
        """Schließt die Datenbankverbindung"""
        if self.client:
            self.client.close()
            logger.info("MongoDB-Verbindung geschlossen")
    
    # Sensordaten-Operationen
    
    def save_sensor_data(self, sensor_data: Dict[str, Any]) -> bool:
        """
        Speichert Sensordaten
        
        Args:
            sensor_data: Sensordaten
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            result = self.db.sensor_data.insert_one(sensor_data)
            return result.acknowledged
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Sensordaten: {e}")
            return False
    
    def get_sensor_data(self, device_id: str, sensor_type: str, 
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """
        Gibt Sensordaten für ein Gerät und einen Sensortyp zurück
        
        Args:
            device_id: ID des Geräts
            sensor_type: Typ des Sensors
            start_time: Startzeit für die Abfrage
            end_time: Endzeit für die Abfrage
            limit: Maximale Anzahl der zurückgegebenen Datensätze
            
        Returns:
            Liste der Sensordaten
        """
        query = {
            "device_id": device_id,
            "sensor_type": sensor_type
        }
        
        if start_time or end_time:
            query["timestamp"] = {}
            if start_time:
                query["timestamp"]["$gte"] = start_time
            if end_time:
                query["timestamp"]["$lte"] = end_time
        
        return list(self.db.sensor_data.find(query).sort("timestamp", -1).limit(limit))
    
    # Konfigurationen-Operationen
    
    def get_device_config(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Gibt die Konfiguration eines Geräts zurück
        
        Args:
            device_id: ID des Geräts
            
        Returns:
            Konfiguration oder None, wenn nicht gefunden
        """
        config_doc = self.db.configs.find_one({"device_id": device_id})
        return config_doc.get("config") if config_doc else None
    
    def save_device_config(self, device_id: str, config: Dict[str, Any]) -> bool:
        """
        Speichert die Konfiguration eines Geräts
        
        Args:
            device_id: ID des Geräts
            config: Konfiguration
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            result = self.db.configs.update_one(
                {"device_id": device_id},
                {"$set": {
                    "device_id": device_id,
                    "config": config,
                    "updated_at": datetime.utcnow()
                }},
                upsert=True
            )
            
            return result.acknowledged
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Gerätekonfiguration: {e}")
            return False
    
    # Regeln-Operationen
    
    def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """
        Gibt eine Regel anhand ihrer ID zurück
        
        Args:
            rule_id: ID der Regel
            
        Returns:
            Regeldaten oder None, wenn nicht gefunden
        """
        return self.db.rules.find_one({"rule_id": rule_id})
    
    def get_rules_for_device(self, device_id: str) -> List[Dict[str, Any]]:
        """
        Gibt alle Regeln für ein Gerät zurück
        
        Args:
            device_id: ID des Geräts
            
        Returns:
            Liste der Regeln
        """
        return list(self.db.rules.find({"device_id": device_id, "enabled": True}))
    
    def save_rule(self, rule_data: Dict[str, Any]) -> bool:
        """
        Speichert oder aktualisiert eine Regel
        
        Args:
            rule_data: Regeldaten
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            rule_id = rule_data.get("rule_id")
            if not rule_id:
                logger.error("Regel ohne rule_id kann nicht gespeichert werden")
                return False
                
            result = self.db.rules.update_one(
                {"rule_id": rule_id},
                {"$set": rule_data},
                upsert=True
            )
            
            return result.acknowledged
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Regel: {e}")
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
            result = self.db.rules.delete_one({"rule_id": rule_id})
            return result.acknowledged and result.deleted_count > 0
        except Exception as e:
            logger.error(f"Fehler beim Löschen der Regel: {e}")
            return False
    
    # Programmvorlagen-Operationen
    
    def get_program_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Gibt eine Programmvorlage anhand ihrer ID zurück
        
        Args:
            template_id: ID der Programmvorlage
            
        Returns:
            Programmvorlagendaten oder None, wenn nicht gefunden
        """
        return self.db.program_templates.find_one({"template_id": template_id})
    
    def get_all_program_templates(self) -> List[Dict[str, Any]]:
        """
        Gibt alle Programmvorlagen zurück
        
        Returns:
            Liste aller Programmvorlagen
        """
        return list(self.db.program_templates.find().sort("name", 1))
    
    def save_program_template(self, template_data: Dict[str, Any]) -> bool:
        """
        Speichert oder aktualisiert eine Programmvorlage
        
        Args:
            template_data: Programmvorlagendaten
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            template_id = template_data.get("template_id")
            if not template_id:
                logger.error("Programmvorlage ohne template_id kann nicht gespeichert werden")
                return False
            
            # Aktualisiere updated_at Zeitstempel
            if "updated_at" not in template_data:
                template_data["updated_at"] = datetime.utcnow()
                
            result = self.db.program_templates.update_one(
                {"template_id": template_id},
                {"$set": template_data},
                upsert=True
            )
            
            return result.acknowledged
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Programmvorlage: {e}")
            return False
    
    def delete_program_template(self, template_id: str) -> bool:
        """
        Löscht eine Programmvorlage
        
        Args:
            template_id: ID der Programmvorlage
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            result = self.db.program_templates.delete_one({"template_id": template_id})
            return result.acknowledged and result.deleted_count > 0
        except Exception as e:
            logger.error(f"Fehler beim Löschen der Programmvorlage: {e}")
            return False
    
    # Programminstanzen-Operationen
    
    def get_program_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """
        Gibt eine Programminstanz anhand ihrer ID zurück
        
        Args:
            instance_id: ID der Programminstanz
            
        Returns:
            Programminstanzdaten oder None, wenn nicht gefunden
        """
        return self.db.program_instances.find_one({"instance_id": instance_id})
    
    def get_active_program_instance(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Gibt die aktive Programminstanz für ein Gerät zurück
        
        Args:
            device_id: ID des Geräts
            
        Returns:
            Aktive Programminstanz oder None, wenn keine gefunden
        """
        # Aktive Programminstanzen haben den Status "running" oder "paused"
        return self.db.program_instances.find_one({
            "device_id": device_id,
            "status": {"$in": ["running", "paused"]}
        })
    
    def get_program_instances_for_device(self, device_id: str) -> List[Dict[str, Any]]:
        """
        Gibt alle Programminstanzen für ein Gerät zurück
        
        Args:
            device_id: ID des Geräts
            
        Returns:
            Liste der Programminstanzen
        """
        return list(self.db.program_instances.find(
            {"device_id": device_id}
        ).sort("created_at", -1))
    
    def save_program_instance(self, instance_data: Dict[str, Any]) -> bool:
        """
        Speichert oder aktualisiert eine Programminstanz
        
        Args:
            instance_data: Programminstanzdaten
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            instance_id = instance_data.get("instance_id")
            if not instance_id:
                logger.error("Programminstanz ohne instance_id kann nicht gespeichert werden")
                return False
                
            result = self.db.program_instances.update_one(
                {"instance_id": instance_id},
                {"$set": instance_data},
                upsert=True
            )
            
            return result.acknowledged
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Programminstanz: {e}")
            return False
    
    def add_program_instance_log(self, instance_id: str, log_entry: Dict[str, Any]) -> bool:
        """
        Fügt einen Logeintrag zu einer Programminstanz hinzu
        
        Args:
            instance_id: ID der Programminstanz
            log_entry: Logeintrag
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Stellt sicher, dass der Logeintrag einen Zeitstempel hat
            if "timestamp" not in log_entry:
                log_entry["timestamp"] = datetime.utcnow()
                
            result = self.db.program_instances.update_one(
                {"instance_id": instance_id},
                {"$push": {"log": log_entry}}
            )
            
            return result.acknowledged
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen des Logeintrags: {e}")
            return False

# Einfache Funktion zum Abrufen der Datenbankinstanz
def get_database() -> Database:
    """
    Gibt die Datenbankinstanz zurück
    
    Returns:
        Database-Instanz
    """
    return Database() 