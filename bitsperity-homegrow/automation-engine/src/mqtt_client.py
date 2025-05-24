#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import uuid
from typing import Dict, Any, Callable, Optional, List
import paho.mqtt.client as mqtt

from .config import get_config
from .logger import get_logger

logger = get_logger(__name__)

class MQTTClient:
    """MQTT-Client für die Kommunikation mit den HomeGrow-Geräten"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """Singleton-Pattern für den MQTT-Client"""
        if cls._instance is None:
            cls._instance = super(MQTTClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialisiert den MQTT-Client"""
        if self._initialized:
            return
            
        self.config = get_config()
        self.mqtt_config = self.config.get_mqtt_config()
        
        self.client_id = self.mqtt_config.get('client_id', 'homegrow_server')
        if self.mqtt_config.get('use_random_client_id', False):
            self.client_id = f"{self.client_id}_{uuid.uuid4().hex[:8]}"
            
        self.topic_prefix = self.mqtt_config.get('topic_prefix', 'homegrow')
        
        # Callbacks für verschiedene Nachrichtentypen
        self.callbacks = {
            'sensor': [],
            'heartbeat': [],
            'config_request': [],
            'config_response': [],
            'actuator_status': []
        }
        
        # MQTT-Client erstellen
        self.client = mqtt.Client(client_id=self.client_id, protocol=mqtt.MQTTv5)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # Authentifizierung, falls konfiguriert
        username = self.mqtt_config.get('username')
        password = self.mqtt_config.get('password')
        if username:
            self.client.username_pw_set(username, password)
        
        self._initialized = True
    
    def connect(self):
        """Stellt eine Verbindung zum MQTT-Broker her"""
        try:
            host = self.mqtt_config.get('host', 'localhost')
            port = self.mqtt_config.get('port', 1883)
            keepalive = self.mqtt_config.get('keepalive', 60)
            
            logger.info(f"Verbinde mit MQTT-Broker: {host}:{port}")
            self.client.connect(host, port, keepalive)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Fehler bei der Verbindung zum MQTT-Broker: {e}")
            raise
    
    def disconnect(self):
        """Trennt die Verbindung zum MQTT-Broker"""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT-Verbindung getrennt")
    
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Callback für erfolgreiche Verbindung"""
        if rc == 0:
            logger.info("Erfolgreich mit MQTT-Broker verbunden")
            self._subscribe_to_topics()
        else:
            logger.error(f"Fehler bei der Verbindung zum MQTT-Broker: {rc}")
    
    def _on_disconnect(self, client, userdata, rc, properties=None):
        """Callback für Verbindungstrennung"""
        if rc != 0:
            logger.warning(f"Unerwartete Trennung vom MQTT-Broker: {rc}")
            # Versuche, die Verbindung wiederherzustellen
            time.sleep(5)
            try:
                self.connect()
            except Exception as e:
                logger.error(f"Fehler bei der Wiederverbindung: {e}")
    
    def _subscribe_to_topics(self):
        """Abonniert die benötigten Topics"""
        # Sensordaten von allen Geräten
        sensor_topic = f"{self.topic_prefix}/+/sensor/#"
        self.client.subscribe(sensor_topic)
        logger.info(f"Abonniere Topic: {sensor_topic}")
        
        # Heartbeats von allen Geräten
        heartbeat_topic = f"{self.topic_prefix}/+/heartbeat"
        self.client.subscribe(heartbeat_topic)
        logger.info(f"Abonniere Topic: {heartbeat_topic}")
        
        # Konfigurationsanfragen von allen Geräten
        config_request_topic = f"{self.topic_prefix}/+/config/request"
        self.client.subscribe(config_request_topic)
        logger.info(f"Abonniere Topic: {config_request_topic}")
        
        # Konfigurationsantworten/Änderungen von allen Geräten
        config_response_topic = f"{self.topic_prefix}/+/config/response"
        self.client.subscribe(config_response_topic)
        logger.info(f"Abonniere Topic: {config_response_topic}")
        
        # Aktuatorstatus von allen Geräten
        actuator_topic = f"{self.topic_prefix}/+/actuator/#"
        self.client.subscribe(actuator_topic)
        logger.info(f"Abonniere Topic: {actuator_topic}")
        
        # Command-Response von allen Geräten (für künftige Erweiterungen)
        command_response_topic = f"{self.topic_prefix}/+/commands/response"
        self.client.subscribe(command_response_topic)
        logger.info(f"Abonniere Topic: {command_response_topic}")
        
        logger.info("MQTT-Topics abonniert")
    
    def _on_message(self, client, userdata, msg):
        """Callback für eingehende Nachrichten"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.debug(f"MQTT-Nachricht empfangen: {topic} - {payload}")
            
            # Extrahiere device_id aus dem Topic
            topic_parts = topic.split('/')
            if len(topic_parts) < 3:
                logger.warning(f"Ungültiges Topic-Format: {topic}")
                return
                
            device_id = topic_parts[1]
            message_type = topic_parts[2]
            
            # Verarbeite die Nachricht je nach Typ
            if message_type == 'sensor':
                sensor_type = topic_parts[3] if len(topic_parts) > 3 else None
                self._handle_sensor_data(device_id, sensor_type, payload)
            elif message_type == 'heartbeat':
                self._handle_heartbeat(device_id, payload)
            elif message_type == 'config':
                if len(topic_parts) > 3:
                    if topic_parts[3] == 'request':
                        self._handle_config_request(device_id, payload)
                    elif topic_parts[3] == 'response':
                        self._handle_config_response(device_id, payload)
            elif message_type == 'actuator':
                actuator_id = topic_parts[3] if len(topic_parts) > 3 else None
                self._handle_actuator_status(device_id, actuator_id, payload)
        except Exception as e:
            logger.error(f"Fehler bei der Verarbeitung der MQTT-Nachricht: {e}")
    
    def _handle_sensor_data(self, device_id: str, sensor_type: Optional[str], payload: str):
        """
        Verarbeitet Sensordaten
        
        Args:
            device_id: ID des Geräts
            sensor_type: Typ des Sensors (pH, TDS, etc.)
            payload: JSON-Payload als String
        """
        try:
            data = json.loads(payload)
            
            # Füge device_id und sensor_type hinzu, falls nicht vorhanden
            if 'device_id' not in data:
                data['device_id'] = device_id
            if sensor_type and 'sensor_type' not in data:
                data['sensor_type'] = sensor_type
            
            # Aktualisiere den Sensor-Cache in der ProgramEngine, falls es sich um pH oder TDS handelt
            if sensor_type in ['ph', 'tds'] and 'value' in data:
                try:
                    from .program_engine import get_program_engine
                    program_engine = get_program_engine()
                    program_engine.update_sensor_cache(device_id, sensor_type, data['value'])
                    logger.debug(f"Sensor-Cache für {device_id}/{sensor_type} aktualisiert: {data['value']}")
                except Exception as e:
                    logger.warning(f"Fehler beim Aktualisieren des Sensor-Caches: {e}")
                
            # Rufe alle registrierten Callbacks auf
            for callback in self.callbacks['sensor']:
                callback(device_id, sensor_type, data)
        except json.JSONDecodeError:
            logger.warning(f"Ungültiges JSON in Sensordaten: {payload}")
        except Exception as e:
            logger.error(f"Fehler bei der Verarbeitung von Sensordaten: {e}")
    
    def _handle_heartbeat(self, device_id: str, payload: str):
        """Verarbeitet Heartbeat-Nachrichten"""
        try:
            data = json.loads(payload) if payload else {}
            
            # Rufe alle registrierten Callbacks auf
            for callback in self.callbacks['heartbeat']:
                callback(device_id, data)
        except json.JSONDecodeError:
            logger.warning(f"Ungültiges JSON in Heartbeat: {payload}")
        except Exception as e:
            logger.error(f"Fehler bei der Verarbeitung von Heartbeat: {e}")
    
    def _handle_config_request(self, device_id: str, payload: str):
        """Verarbeitet Konfigurationsanfragen"""
        try:
            logger.info(f"Konfigurationsanfrage empfangen von Gerät {device_id}")
            logger.info(f"Anfrage-Topic: {self.topic_prefix}/{device_id}/config/request")
            logger.info(f"Payload: {payload}")
            
            data = json.loads(payload) if payload else {}
            
            # Rufe alle registrierten Callbacks auf
            for callback in self.callbacks['config_request']:
                callback(device_id, data)
        except json.JSONDecodeError:
            logger.warning(f"Ungültiges JSON in Konfigurationsanfrage: {payload}")
        except Exception as e:
            logger.error(f"Fehler bei der Verarbeitung von Konfigurationsanfrage: {e}")
    
    def _handle_config_response(self, device_id: str, payload: str):
        """Verarbeitet Konfigurationsantworten"""
        try:
            logger.info(f"Konfigurationsantwort empfangen von Gerät {device_id}")
            logger.info(f"Antwort-Topic: {self.topic_prefix}/{device_id}/config/response")
            logger.info(f"Payload: {payload}")
            
            data = json.loads(payload) if payload else {}
            
            # Rufe alle registrierten Callbacks auf
            for callback in self.callbacks['config_response']:
                callback(device_id, data)
        except json.JSONDecodeError:
            logger.warning(f"Ungültiges JSON in Konfigurationsantwort: {payload}")
        except Exception as e:
            logger.error(f"Fehler bei der Verarbeitung von Konfigurationsantwort: {e}")
    
    def _handle_actuator_status(self, device_id: str, actuator_id: Optional[str], payload: str):
        """Verarbeitet Aktuatorstatus-Nachrichten"""
        try:
            data = json.loads(payload)
            
            # Füge device_id und actuator_id hinzu, falls nicht vorhanden
            if 'device_id' not in data:
                data['device_id'] = device_id
            if actuator_id and 'actuator_id' not in data:
                data['actuator_id'] = actuator_id
                
            # Rufe alle registrierten Callbacks auf
            for callback in self.callbacks['actuator_status']:
                callback(device_id, actuator_id, data)
        except json.JSONDecodeError:
            logger.warning(f"Ungültiges JSON in Aktuatorstatus: {payload}")
        except Exception as e:
            logger.error(f"Fehler bei der Verarbeitung von Aktuatorstatus: {e}")
    
    def publish_config(self, device_id: str, config: Dict[str, Any]):
        """
        Veröffentlicht eine Konfiguration für ein Gerät
        
        Args:
            device_id: ID des Geräts
            config: Konfiguration als Dictionary
        """
        topic = f"{self.topic_prefix}/{device_id}/config/response"
        
        # Kopiere die Konfiguration, um das Original nicht zu verändern
        config_to_send = config.copy()
        
        payload = json.dumps(config_to_send)
        
        logger.info(f"Veröffentliche Konfiguration auf Topic: {topic}")
        logger.info(f"Payload: {payload[:100]}..." if len(payload) > 100 else f"Payload: {payload}")
        
        self.client.publish(topic, payload, qos=1, retain=True)
        logger.info(f"Konfiguration für Gerät {device_id} veröffentlicht")
    
    def publish(self, topic: str, payload: Dict[str, Any], qos: int = 0):
        """
        Veröffentlicht eine Nachricht auf einem Topic
        
        Args:
            topic: MQTT-Topic
            payload: Nachrichteninhalt als Dictionary (wird zu JSON konvertiert)
            qos: Quality of Service (0, 1 oder 2)
        """
        if not self.client or not self.client.is_connected():
            logger.error(f"MQTT-Client nicht verbunden. Nachricht auf {topic} wird nicht gesendet.")
            return False
            
        try:
            # Konvertiere Payload zu JSON
            json_payload = json.dumps(payload)
            
            # Debug-Ausgabe
            logger.debug(f"Sende MQTT-Nachricht an {topic}: {json_payload}")
            
            # Nachricht veröffentlichen
            info = self.client.publish(topic, json_payload, qos=qos)
            
            # Fehlerprüfung für die publish-Operation
            if info.rc != 0:
                logger.error(f"MQTT-Fehler beim Veröffentlichen: {info.rc}")
                return False
                
            # Warte, bis die Nachricht gesendet wurde (bei QoS > 0)
            if qos > 0:
                info.wait_for_publish(timeout=2.0)
                if not info.is_published():
                    logger.warning(f"Timeout beim Veröffentlichen der Nachricht auf {topic}")
                    return False
            
            logger.debug(f"Nachricht erfolgreich veröffentlicht auf {topic}")
            return True
        except json.JSONDecodeError as e:
            logger.error(f"JSON-Fehler beim Veröffentlichen der Nachricht: {e}")
            return False
        except Exception as e:
            logger.error(f"Fehler beim Veröffentlichen der Nachricht auf {topic}: {e}")
            return False
    
    def publish_actuator_command(self, device_id: str, actuator_id: str, command: Dict[str, Any]):
        """
        Veröffentlicht einen Befehl für einen Aktuator
        
        Args:
            device_id: ID des Geräts
            actuator_id: ID des Aktuators
            command: Befehl als Dictionary
        """
        topic = f"{self.topic_prefix}/{device_id}/actuator/{actuator_id}/command"
        payload = json.dumps(command)
        
        self.client.publish(topic, payload, qos=1)
        logger.info(f"Befehl für Aktuator {actuator_id} an Gerät {device_id} gesendet")
    
    def register_sensor_callback(self, callback: Callable[[str, str, Dict[str, Any]], None]):
        """
        Registriert einen Callback für Sensordaten
        
        Args:
            callback: Funktion, die aufgerufen wird, wenn Sensordaten empfangen werden
                      mit den Argumenten (device_id, sensor_type, data)
        """
        self.callbacks['sensor'].append(callback)
    
    def register_heartbeat_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """
        Registriert einen Callback für Heartbeat-Nachrichten
        
        Args:
            callback: Funktion, die aufgerufen wird, wenn ein Heartbeat empfangen wird
        """
        self.callbacks['heartbeat'].append(callback)
    
    def register_config_request_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """
        Registriert einen Callback für Konfigurationsanfragen
        
        Args:
            callback: Funktion, die aufgerufen wird, wenn eine Konfigurationsanfrage empfangen wird
        """
        self.callbacks['config_request'].append(callback)
    
    def register_config_response_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """
        Registriert einen Callback für Konfigurationsantworten
        
        Args:
            callback: Funktion, die aufgerufen wird, wenn eine Konfigurationsantwort empfangen wird
        """
        self.callbacks['config_response'].append(callback)
    
    def register_actuator_status_callback(self, callback: Callable[[str, Optional[str], Dict[str, Any]], None]):
        """
        Registriert einen Callback für Aktuatorstatus-Nachrichten
        
        Args:
            callback: Funktion, die aufgerufen wird, wenn ein Aktuatorstatus empfangen wird
        """
        self.callbacks['actuator_status'].append(callback)

# Einfache Funktion zum Abrufen des MQTT-Clients
def get_mqtt_client() -> MQTTClient:
    """
    Gibt den MQTT-Client zurück
    
    Returns:
        MQTTClient-Instanz
    """
    return MQTTClient() 