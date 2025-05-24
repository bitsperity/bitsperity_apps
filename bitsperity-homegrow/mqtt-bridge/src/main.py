#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import signal
import sys
import time
from datetime import datetime

import colorlog
import paho.mqtt.client as mqtt
from pymongo import MongoClient

# Konfiguration
MQTT_BROKER = "mqtt_broker"
MQTT_PORT = 1883
MONGO_URI = "mongodb://mongo_server:27017/"
DB_NAME = "homegrow"

# Logging-Konfiguration
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
))

logger = colorlog.getLogger('mqtt_mongo_bridge')
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Globale Variablen
mqtt_client = None
db = None
running = True

def setup_mqtt():
    """Richtet die MQTT-Verbindung ein"""
    global mqtt_client
    
    logger.info(f"Verbinde mit MQTT-Broker {MQTT_BROKER}:{MQTT_PORT}...")
    
    mqtt_client = mqtt.Client()
    
    # Callbacks
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_message = on_mqtt_message
    
    # Verbindung herstellen
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

def on_mqtt_connect(client, userdata, flags, rc):
    """Callback für MQTT-Verbindung"""
    if rc == 0:
        logger.info("Verbunden mit MQTT-Broker")
        # Topics abonnieren
        client.subscribe("homegrow/#")
        logger.info("Abonniert: homegrow/#")
        
        # Spezifische Topics für bessere Lesbarkeit
        specific_topics = [
            "homegrow/+/sensor/ph",
            "homegrow/+/sensor/tds",
            "homegrow/+/status/pumps",
            "homegrow/+/heartbeat"
        ]
        
        for topic in specific_topics:
            client.subscribe(topic)
            logger.info(f"Abonniert: {topic}")
    else:
        logger.error(f"Verbindung mit MQTT-Broker fehlgeschlagen mit Code {rc}")

def on_mqtt_message(client, userdata, msg):
    """Callback für MQTT-Nachrichten"""
    try:
        topic = msg.topic
        payload = msg.payload.decode()
        
        # Versuche, JSON zu parsen
        try:
            payload_data = json.loads(payload)
        except json.JSONDecodeError:
            payload_data = {"raw": payload}
        
        logger.debug(f"MQTT-Nachricht empfangen: {topic}")
        
        # Daten in MongoDB speichern
        store_mqtt_data(topic, payload_data)
    
    except Exception as e:
        logger.error(f"Fehler bei der Verarbeitung der MQTT-Nachricht: {e}")

def store_mqtt_data(topic, payload):
    """Speichert MQTT-Daten in der MongoDB"""
    global db
    
    try:
        # Topic-Teile extrahieren
        parts = topic.split('/')
        collection_name = "mqtt_messages"
        
        # Spezielle Behandlung für bestimmte Topics
        if len(parts) >= 3:
            if parts[2] == "sensor":
                if parts[3] == "ph":
                    collection_name = "ph_sensor_data"
                elif parts[3] == "tds":
                    collection_name = "tds_sensor_data"
            elif parts[2] == "status":
                if len(parts) >= 4 and parts[3] == "pumps":
                    collection_name = "pump_status"
                else:
                    collection_name = "device_status"
            elif parts[2] == "command":
                collection_name = "device_commands"
            elif parts[2] == "config":
                # Unterscheide zwischen Konfigurationsanfragen und -antworten
                if len(parts) >= 4 and parts[3] == "response":
                    collection_name = "config_responses"
                else:
                    collection_name = "config_requests"
        
        # Dokument erstellen
        document = {
            "topic": topic,
            "topic_parts": parts,
            "payload": payload,
            "timestamp": datetime.now()
        }
        
        # Gerät-ID hinzufügen, wenn vorhanden
        if len(parts) >= 2:
            document["device_id"] = parts[1]
        
        # In Datenbank speichern
        db[collection_name].insert_one(document)
        logger.debug(f"MQTT-Daten gespeichert in {collection_name}: {topic}")
        
        # Zusätzliche Verarbeitung für Pumpenstatus
        if collection_name == "pump_status" and "pumps" in payload:
            try:
                # Extrahiere Pumpendaten und speichere sie in einer separaten Sammlung
                pumps_data = payload["pumps"]
                for pump_id, pump_status in pumps_data.items():
                    pump_document = {
                        "device_id": document["device_id"],
                        "pump_id": pump_id,
                        "active": pump_status.get("active", False),
                        "remaining_time": pump_status.get("remaining_time", 0),
                        "timestamp": document["timestamp"]
                    }
                    db["pumps"].insert_one(pump_document)
                logger.debug(f"Pumpendaten für {len(pumps_data)} Pumpen gespeichert")
            except Exception as e:
                logger.error(f"Fehler bei der Verarbeitung der Pumpendaten: {e}")
    
    except Exception as e:
        logger.error(f"Fehler beim Speichern der MQTT-Daten: {e}")

def signal_handler(sig, frame):
    """Signal-Handler für sauberes Beenden"""
    global running
    logger.info("Beende MQTT-MongoDB-Bridge...")
    running = False

def main():
    """Hauptfunktion"""
    global db
    
    # Signal-Handler registrieren
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # MongoDB-Verbindung herstellen
        mongo_client = MongoClient(MONGO_URI)
        db = mongo_client[DB_NAME]
        logger.info(f"Verbunden mit MongoDB: {MONGO_URI}")
        
        # MQTT einrichten
        setup_mqtt()
        
        # MQTT-Loop starten
        mqtt_client.loop_start()
        
        logger.info("MQTT-MongoDB-Bridge läuft")
        
        # Hauptschleife
        while running:
            time.sleep(1)
        
        # Aufräumen
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        logger.info("MQTT-Client beendet")
        
        logger.info("MQTT-MongoDB-Bridge wurde sauber beendet")
    
    except Exception as e:
        logger.critical(f"Fehler beim Ausführen der MQTT-MongoDB-Bridge: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 