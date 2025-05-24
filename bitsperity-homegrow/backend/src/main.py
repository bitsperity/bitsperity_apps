#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os
import numpy as np
from datetime import datetime, timedelta

import colorlog
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from bson import json_util, ObjectId

# Konfiguration
MONGO_URI = "mongodb://mongo_server:27017/"  # Bleibt unverändert, da der server_backend im Standard-Docker-Netzwerk läuft
DB_NAME = "homegrow"
HOMEGROW_SERVER_HOST = "localhost"  # Da wir network_mode: "host" verwenden
HOMEGROW_SERVER_PORT = 8080
HOMEGROW_SERVER_PATH = "/homegrow"

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

logger = colorlog.getLogger('server_backend')
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Flask-App initialisieren
app = Flask(__name__)
CORS(app)

# MongoDB-Verbindung
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]

# Hilfsfunktion zum Konvertieren von MongoDB-Dokumenten in JSON
def mongo_to_json(data):
    return json.loads(json_util.dumps(data))

@app.route('/api/health', methods=['GET'])
def health_check():
    """Einfacher Health-Check-Endpunkt"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Gibt eine einfache Liste aller bekannten Geräte zurück (nur ID und Name)"""
    try:
        # Geräte aus der configs Collection abrufen
        configs_data = list(db.configs.find({}, {"device_id": 1, "device_name": 1}))
        devices_list = []
        
        for config in configs_data:
            device_id = config.get("device_id")
            device_name = config.get("device_name", f"HomeGrow Device {device_id}")
            
            # Prüfe, ob das Gerät online ist (optional)
            heartbeat = db.mqtt_messages.find_one(
                {"device_id": device_id, "topic_parts.2": "heartbeat"},
                sort=[("timestamp", -1)]
            )
            online = heartbeat.get("payload", {}).get("status") == "online" if heartbeat else False
            
            # Füge nur die grundlegenden Informationen hinzu
            devices_list.append({
                "device_id": device_id,
                "name": device_name,
                "online": online
            })
        
        # Konvertiere die Daten in JSON
        devices_json = mongo_to_json(devices_list)
        
        return jsonify(devices_json)
    
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Geräteliste: {e}")
        return jsonify({"error": str(e)}), 500

def validate_automation_config(automation_config):
    """Validiert die Automatisierungskonfiguration"""
    if not automation_config:
        return True, None  # Keine Konfiguration ist gültig
    
    errors = []
    
    # Prüfe ob nutrient_control existiert
    if "nutrient_control" not in automation_config:
        return True, None  # Optional, keine Fehler
    
    nutrient_control = automation_config.get("nutrient_control", {})
    
    # Validiere water_volume_liters
    water_volume = nutrient_control.get("water_volume_liters")
    if water_volume is not None:
        if not isinstance(water_volume, (int, float)) or water_volume <= 0 or water_volume > 100:
            errors.append("Wasservolumen muss zwischen 1 und 100 Litern liegen")
    
    # Validiere solution_strengths
    strengths = nutrient_control.get("solution_strengths", {})
    valid_strengths = ["schwach", "standard", "stark"]
    for key, value in strengths.items():
        if value not in valid_strengths:
            errors.append(f"Ungültige Lösungsstärke '{value}' für {key}")
    
    # Validiere dose_limits
    dose_limits = nutrient_control.get("dose_limits", {})
    if dose_limits:
        # Validiere max_nutrient_percent
        max_nutrient = dose_limits.get("max_nutrient_percent")
        if max_nutrient is not None:
            if not isinstance(max_nutrient, (int, float)) or max_nutrient <= 0 or max_nutrient > 1:
                errors.append("max_nutrient_percent muss größer als 0 und maximal 1 sein")
        
        # Validiere min_nutrient_percent
        min_nutrient = dose_limits.get("min_nutrient_percent")
        if min_nutrient is not None:
            if not isinstance(min_nutrient, (int, float)) or min_nutrient <= 0 or min_nutrient > 1:
                errors.append("min_nutrient_percent muss größer als 0 und maximal 1 sein")
        
        # Validiere max_ph_percent
        max_ph = dose_limits.get("max_ph_percent")
        if max_ph is not None:
            if not isinstance(max_ph, (int, float)) or max_ph <= 0 or max_ph > 1:
                errors.append("max_ph_percent muss größer als 0 und maximal 1 sein")
        
        # Validiere min_ph_percent
        min_ph = dose_limits.get("min_ph_percent")
        if min_ph is not None:
            logger.info(f"Validiere min_ph_percent: {min_ph}, Typ: {type(min_ph)}")
            
            # Prüfe den Typ
            if not isinstance(min_ph, (int, float)):
                errors.append(f"min_ph_percent muss eine Zahl sein, nicht {type(min_ph)}")
            # Prüfe den Wertebereich - flexiblere Grenzen
            elif min_ph <= 0:
                errors.append(f"min_ph_percent ({min_ph}) muss größer als 0 sein")
            elif min_ph > 1:
                errors.append(f"min_ph_percent ({min_ph}) darf maximal 1 sein")
    
    # Validiere calibration
    calibration = nutrient_control.get("calibration", {})
    if calibration:
        # Validiere tds_per_ml
        tds_per_ml = calibration.get("tds_per_ml")
        if tds_per_ml is not None:
            if not isinstance(tds_per_ml, (int, float)) or tds_per_ml < 0.1 or tds_per_ml > 100:
                errors.append("tds_per_ml muss zwischen 0.1 und 100 liegen")
        
        # Validiere ph_up_per_ml
        ph_up_per_ml = calibration.get("ph_up_per_ml")
        if ph_up_per_ml is not None:
            if not isinstance(ph_up_per_ml, (int, float)) or ph_up_per_ml < 0.01 or ph_up_per_ml > 1:
                errors.append("ph_up_per_ml muss zwischen 0.01 und 1 liegen")
        
        # Validiere ph_down_per_ml
        ph_down_per_ml = calibration.get("ph_down_per_ml")
        if ph_down_per_ml is not None:
            if not isinstance(ph_down_per_ml, (int, float)) or ph_down_per_ml < 0.01 or ph_down_per_ml > 1:
                errors.append("ph_down_per_ml muss zwischen 0.01 und 1 liegen")
    
    # Validiere wait_times
    wait_times = nutrient_control.get("wait_times", {})
    if wait_times:
        # Validiere nutrient_minutes
        nutrient_minutes = wait_times.get("nutrient_minutes")
        if nutrient_minutes is not None:
            if not isinstance(nutrient_minutes, (int, float)) or nutrient_minutes < 1 or nutrient_minutes > 240:
                errors.append("nutrient_minutes muss zwischen 1 und 240 liegen")
        
        # Validiere ph_minutes
        ph_minutes = wait_times.get("ph_minutes")
        if ph_minutes is not None:
            if not isinstance(ph_minutes, (int, float)) or ph_minutes < 1 or ph_minutes > 60:
                errors.append("ph_minutes muss zwischen 1 und 60 liegen")
    
    return len(errors) == 0, errors

def validate_pump_parameters(phase_data):
    """Validiert die Pumpenparameter für eine Phase"""
    errors = []
    
    # Validiere Wasserpumpe
    water_cycle = phase_data.get('water_pump_cycle_minutes')
    water_on = phase_data.get('water_pump_on_minutes')
    
    if water_cycle is None or not isinstance(water_cycle, (int, float)) or water_cycle < 1:
        errors.append("Zyklusdauer der Wasserpumpe muss mindestens 1 Minute betragen")
    
    if water_on is None or not isinstance(water_on, (int, float)) or water_on < 0:
        errors.append("Einschaltdauer der Wasserpumpe muss 0 oder größer sein")
    
    if water_cycle and water_on and water_on > water_cycle and water_on != water_cycle:
        errors.append("Einschaltdauer der Wasserpumpe muss kleiner oder gleich Zyklusdauer sein")
    
    # Validiere Luftpumpe
    air_cycle = phase_data.get('air_pump_cycle_minutes')
    air_on = phase_data.get('air_pump_on_minutes')
    
    if air_cycle is None or not isinstance(air_cycle, (int, float)) or air_cycle < 1:
        errors.append("Zyklusdauer der Luftpumpe muss mindestens 1 Minute betragen")
    
    if air_on is None or not isinstance(air_on, (int, float)) or air_on < 0:
        errors.append("Einschaltdauer der Luftpumpe muss 0 oder größer sein")
    
    if air_cycle and air_on and air_on > air_cycle and air_on != air_cycle:
        errors.append("Einschaltdauer der Luftpumpe muss kleiner oder gleich Zyklusdauer sein")
    
    return len(errors) == 0, errors

@app.route('/api/devices/<device_id>/config', methods=['GET', 'POST', 'DELETE'])
def device_config(device_id):
    """Ruft die Konfiguration eines Geräts ab, aktualisiert oder löscht sie"""
    try:
        if request.method == 'GET':
            # Konfiguration aus der configs Collection abrufen
            config = db.configs.find_one({"device_id": device_id})
            
            if not config:
                # Erstelle eine Default-Konfiguration für neue Geräte
                default_config = create_default_config(device_id)
                
                # Speichere die Default-Konfiguration in der Datenbank
                db.configs.insert_one({
                    "device_id": device_id,
                    "config": default_config,
                    "device_name": f"HomeGrow Device {device_id}",
                    "updated_at": datetime.now(),
                    "source": "default"
                })
                
                # Hole die gerade erstellte Konfiguration
                config = db.configs.find_one({"device_id": device_id})
                logger.info(f"Default-Konfiguration für neues Gerät {device_id} erstellt")
            
            # Konvertiere die Daten in JSON
            config_json = mongo_to_json(config)
            
            return jsonify(config_json)
        
        elif request.method == 'POST':
            # Konfiguration aktualisieren
            config_data = request.json
            
            if not config_data or "config" not in config_data:
                return jsonify({"error": "Konfiguration fehlt"}), 400
            
            # Validiere die Automatisierungskonfiguration, falls vorhanden
            if "nutrient_control" in config_data["config"]:
                # Detailliertes Logging für Debugging
                logger.info(f"Validiere Automatisierungskonfiguration für Gerät {device_id}")
                logger.info(f"Dose_limits: {config_data['config'].get('nutrient_control', {}).get('dose_limits')}")
                
                is_valid, errors = validate_automation_config(config_data["config"])
                
                if not is_valid:
                    logger.error(f"Validierungsfehler bei Gerät {device_id}: {errors}")
                    return jsonify({
                        "error": "Ungültige Automatisierungskonfiguration",
                        "details": errors
                    }), 400
            
            # Hole den Gerätenamen aus der bestehenden Konfiguration, falls vorhanden
            device_name = None
            existing_config = db.configs.find_one({"device_id": device_id})
            if existing_config and "device_name" in existing_config:
                device_name = existing_config["device_name"]
            
            # Aktualisiere die Konfiguration in der configs Collection
            update_data = {
                "device_id": device_id,
                "config": config_data["config"],
                "updated_at": datetime.now(),
                "source": "api"
            }
            
            # Füge den Gerätenamen hinzu, wenn vorhanden
            if device_name:
                update_data["device_name"] = device_name
            
            result = db.configs.update_one(
                {"device_id": device_id},
                {"$set": update_data},
                upsert=True
            )
            
            logger.info(f"Konfiguration für Gerät {device_id} in der Datenbank aktualisiert")
            
            return jsonify({
                "success": True,
                "message": f"Konfiguration für Gerät {device_id} aktualisiert",
                "timestamp": datetime.now().isoformat()
            })
            
        elif request.method == 'DELETE':
            # Konfiguration löschen
            result = db.configs.delete_one({"device_id": device_id})
            
            if result.deleted_count == 0:
                return jsonify({"error": f"Keine Konfiguration für Gerät {device_id} gefunden"}), 404
            
            return jsonify({
                "success": True,
                "message": f"Konfiguration für Gerät {device_id} gelöscht",
                "timestamp": datetime.now().isoformat()
            })
    
    except Exception as e:
        logger.error(f"Fehler bei der Verarbeitung der Konfiguration für Gerät {device_id}: {e}")
        return jsonify({"error": str(e)}), 500

def create_default_config(device_id):
    """Erstellt eine Default-Konfiguration für ein neues Gerät"""
    return {
        "sensors": {
            "ph": {
                "enabled": True,
                "pin": 1,  # A0 (GPIO1)
                "calibration": {
                    "offset": 0.0,
                    "slope": 1.0
                },
                "reading_interval": 60
            },
            "tds": {
                "enabled": True,
                "pin": 2,  # A1 (GPIO2)
                "calibration": {
                    "offset": 0.0,
                    "slope": 1.0
                },
                "reading_interval": 60
            }
        },
        "actuators": {
            "pump_water": {
                "enabled": True,
                "pin": 3,  # D3
                "active_low": True,
                "flow_rate": 100.0
            },
            "pump_air": {
                "enabled": True,
                "pin": 4,  # D4
                "active_low": True
            },
            "pump_ph_up": {
                "enabled": True,
                "pin": 5,  # D5
                "active_low": True,
                "flow_rate": 10.0
            },
            "pump_ph_down": {
                "enabled": True,
                "pin": 6,  # D6
                "active_low": True,
                "flow_rate": 10.0
            },
            "pump_nutrient_1": {
                "enabled": True,
                "pin": 7,  # D7
                "active_low": True,
                "flow_rate": 10.0
            },
            "pump_nutrient_2": {
                "enabled": True,
                "pin": 8,  # D8
                "active_low": True,
                "flow_rate": 10.0
            },
            "pump_nutrient_3": {
                "enabled": True,
                "pin": 9,  # D9
                "active_low": True,
                "flow_rate": 10.0
            }
        },
        "automation": {
            "enabled": True,
            "check_interval": 300,
            "rules": {
                "ph": {
                    "min": 5.5,
                    "max": 6.5,
                    "actions": {
                        "below_min": "activate_ph_up",
                        "above_max": "activate_ph_down"
                    }
                },
                "tds": {
                    "min": 500,
                    "max": 1500,
                    "actions": {
                        "below_min": "activate_nutrients"
                    }
                }
            }
        },
        "nutrient_control": {
            "water_volume_liters": 20,
            "solution_strengths": {
                "nutrient1": "standard",
                "nutrient2": "standard",
                "nutrient3": "standard",
                "ph_up": "standard",
                "ph_down": "standard"
            },
            "dose_limits": {
                "max_nutrient_percent": 0.1,
                "min_nutrient_percent": 0.005,
                "max_ph_percent": 0.025,
                "min_ph_percent": 0.0025
            },
            "calibration": {
                "tds_per_ml": 10.0,
                "ph_up_per_ml": 0.1,
                "ph_down_per_ml": 0.1
            },
            "wait_times": {
                "nutrient_minutes": 30,
                "ph_minutes": 5
            }
        }
    }

@app.route('/api/device_name/<device_id>', methods=['GET', 'POST'])
def device_name(device_id):
    """Ruft den Namen eines Geräts ab oder aktualisiert ihn"""
    try:
        if request.method == 'GET':
            # In der configs Collection nachsehen
            config = db.configs.find_one({"device_id": device_id})
            if config and "device_name" in config:
                return jsonify({"device_name": config["device_name"]})
            
            # Fallback: Verwende die device_id als Namen
            return jsonify({"device_name": f"HomeGrow Device {device_id}"})
        
        elif request.method == 'POST':
            # Namen aktualisieren
            name_data = request.json
            
            if not name_data or "device_name" not in name_data:
                return jsonify({"error": "Gerätename fehlt"}), 400
            
            device_name = name_data["device_name"]
            
            # Aktualisiere den Namen in der configs Collection
            result = db.configs.update_one(
                {"device_id": device_id},
                {"$set": {"device_name": device_name}},
                upsert=True
            )
            
            # Wenn kein vollständiger Konfigurationseintrag existiert, erstelle einen mit Default-Konfiguration
            if result.matched_count == 0:
                default_config = create_default_config(device_id)
                db.configs.update_one(
                    {"device_id": device_id},
                    {"$set": {
                        "config": default_config,
                        "updated_at": datetime.now(),
                        "source": "default"
                    }},
                    upsert=True
                )
                logger.info(f"Default-Konfiguration für neues Gerät {device_id} erstellt bei Namensänderung")
            
            return jsonify({
                "success": True,
                "message": f"Name für Gerät {device_id} aktualisiert",
                "timestamp": datetime.now().isoformat()
            })
    
    except Exception as e:
        logger.error(f"Fehler bei der Verarbeitung des Gerätenamens für {device_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/sensor-data/<device_id>', methods=['GET'])
def get_sensor_data(device_id):
    """Ruft historische Sensordaten für ein bestimmtes Gerät ab"""
    try:
        # Parameter für Zeitraum und Sensortyp
        sensor_type = request.args.get('type', 'all')
        
        # Moving Average Parameter
        ma_window = request.args.get('ma_window')
        if ma_window is not None:
            try:
                ma_window = int(ma_window)
                logger.info(f"Moving Average angefordert mit Fenstergröße: {ma_window}")
                if ma_window <= 0:
                    logger.warning(f"Ungültige MA-Fenstergröße: {ma_window}, deaktiviere MA")
                    ma_window = None
            except ValueError:
                logger.warning(f"Kann MA-Fenstergröße nicht konvertieren: {ma_window}")
                ma_window = None
        
        # Zeitraum kann entweder über hours oder start_time/end_time definiert werden
        time_range = request.args.get('time_range', '24h')  # Neuer Parameter für vordefinierte Zeiträume (1d, 7d, 30d, 365d)
        
        # Unterstützt auch explizite Zeitbereiche mit ISO-Zeitstempeln
        start_time_str = request.args.get('start_time')
        end_time_str = request.args.get('end_time')
        
        # Standardmäßig bis jetzt
        end_time = datetime.now()
        
        # Zeitraum basierend auf den Parametern berechnen
        if start_time_str and end_time_str:
            # Explizite Start- und Endzeit
            try:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({"error": "Ungültiges Datumsformat. Verwende ISO-Format (YYYY-MM-DDTHH:MM:SS)"}), 400
        else:
            # Vordefinierte Zeiträume
            if time_range == '1d' or time_range == '24h':
                start_time = end_time - timedelta(hours=24)
            elif time_range == '7d' or time_range == '1w':
                start_time = end_time - timedelta(days=7)
            elif time_range == '30d' or time_range == '1m':
                start_time = end_time - timedelta(days=30)
            elif time_range == '365d' or time_range == '1y':
                start_time = end_time - timedelta(days=365)
            else:
                # Fallback auf den hours Parameter für Abwärtskompatibilität
                try:
                    hours = int(request.args.get('hours', 24))
                    start_time = end_time - timedelta(hours=hours)
                except ValueError:
                    return jsonify({"error": "Ungültiger Wert für 'hours'"}), 400
        
        # Abfrage vorbereiten
        query = {
            "device_id": device_id,
            "timestamp": {"$gte": start_time, "$lte": end_time}
        }
        
        # Sensordaten abrufen
        sensor_data = []
        
        if sensor_type == 'ph' or sensor_type == 'all':
            # pH-Sensordaten abrufen
            ph_data = list(db.ph_sensor_data.find(
                query,
                sort=[("timestamp", 1)]
            ))
            
            for data in ph_data:
                sensor_data.append({
                    "type": "ph",
                    "value": data.get("payload", {}).get("value", 0),
                    "timestamp": data.get("timestamp")
                })
        
        if sensor_type == 'tds' or sensor_type == 'all':
            # TDS-Sensordaten abrufen
            tds_data = list(db.tds_sensor_data.find(
                query,
                sort=[("timestamp", 1)]
            ))
            
            for data in tds_data:
                sensor_data.append({
                    "type": "tds",
                    "value": data.get("payload", {}).get("value", 0),
                    "timestamp": data.get("timestamp")
                })
        
        # Sortiere die Daten nach Zeitstempel
        sensor_data.sort(key=lambda x: x["timestamp"])
        
        # Berechne den Moving Average, falls angefordert
        if ma_window and sensor_data:
            logger.info(f"Berechne Moving Average für {len(sensor_data)} Datenpunkte mit Fenster {ma_window}")
            ma_data = calculate_moving_average(sensor_data, ma_window)
            
            # Debug: Überprüfe, ob MA-Werte berechnet wurden
            if len(ma_data) > 0:
                has_ma = "ma_value" in ma_data[0]
                logger.info(f"MA-Werte berechnet: {has_ma}")
                if has_ma and len(ma_data) > 3:
                    # Zeige einige Beispielwerte zur Überprüfung
                    examples = [(d["value"], d["ma_value"]) for d in ma_data[:3]]
                    logger.info(f"Beispiele (Original, MA): {examples}")
            
            # Füge Moving Average zu den Ergebnissen hinzu
            for i, data in enumerate(ma_data):
                sensor_data[i]["ma_value"] = data["ma_value"]
        
        # Konvertiere die Daten in JSON
        sensor_data_json = mongo_to_json(sensor_data)
        
        return jsonify(sensor_data_json)
    
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Sensordaten für Gerät {device_id}: {e}")
        return jsonify({"error": str(e)}), 500

def calculate_moving_average(data, window_size):
    """
    Berechnet den gleitenden Durchschnitt (Moving Average) für Sensordaten
    
    Args:
        data: Liste von Sensordaten-Dictionaries mit 'value' und 'timestamp'
        window_size: Größe des Fensters für den gleitenden Durchschnitt
        
    Returns:
        Liste von Dictionaries mit den Originaldaten und zusätzlichem 'ma_value'
    """
    if not data or window_size <= 0:
        return data
    
    # Debug-Ausgabe
    logger.info(f"Berechne Moving Average mit Fenstergröße {window_size} für {len(data)} Datenpunkte")
    
    # Extrahiere die Werte für die Berechnung
    values = [item["value"] for item in data]
    
    # Debug-Ausgabe für die ersten und letzten Werte
    if len(values) > 5:
        logger.info(f"Erste 5 Werte: {values[:5]}")
        logger.info(f"Letzte 5 Werte: {values[-5:]}")
    
    # Berechne den gleitenden Durchschnitt mit NumPy für bessere Performance und Genauigkeit
    try:
        import numpy as np
        
        # Verwende NumPy für effiziente Berechnung
        values_array = np.array(values)
        ma_values = []
        
        for i in range(len(values_array)):
            # Berechne das Fenster von max(0, i-window_size+1) bis i (inklusive)
            start_idx = max(0, i - window_size + 1)
            window = values_array[start_idx:i+1]
            ma_values.append(float(np.mean(window)))
        
        # Debug-Ausgabe für die berechneten MA-Werte
        if len(ma_values) > 5:
            logger.info(f"Erste 5 MA-Werte (Fenstergröße {window_size}): {ma_values[:5]}")
            logger.info(f"Letzte 5 MA-Werte (Fenstergröße {window_size}): {ma_values[-5:]}")
        
    except ImportError:
        # Fallback für den Fall, dass NumPy nicht verfügbar ist
        logger.warning("NumPy nicht verfügbar, verwende Standard-Berechnung für Moving Average")
        ma_values = []
        
        for i in range(len(values)):
            start_idx = max(0, i - window_size + 1)
            window = values[start_idx:i+1]
            ma_values.append(sum(window) / len(window))
    
    # Erstelle das Ergebnis
    result = []
    for i, item in enumerate(data):
        ma_item = item.copy()  # Kopiere das Originalelement
        ma_item["ma_value"] = ma_values[i]  # Füge den MA-Wert hinzu
        result.append(ma_item)
    
    return result

@app.route('/api/logs/<device_id>/<topic>', methods=['GET'])
def get_logs(device_id, topic):
    """Ruft Logs für ein bestimmtes Gerät und einen bestimmten Topic ab"""
    try:
        # Parameter für Zeitraum
        hours = int(request.args.get('hours', 24))
        
        # Zeitraum berechnen
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Abfrage vorbereiten
        query = {
            "device_id": device_id,
            "timestamp": {"$gte": start_time, "$lte": end_time}
        }
        
        # Logs abrufen
        logs = []
        
        if topic == 'ph':
            # pH-Sensordaten abrufen
            ph_data = list(db.ph_sensor_data.find(
                query,
                sort=[("timestamp", 1)]
            ))
            
            for data in ph_data:
                logs.append({
                    "timestamp": data.get("timestamp"),
                    "event": {
                        "type": "sensor_data",
                        "sensor": "ph",
                        "value": data.get("payload", {}).get("value", 0)
                    }
                })
        
        elif topic == 'tds':
            # TDS-Sensordaten abrufen
            tds_data = list(db.tds_sensor_data.find(
                query,
                sort=[("timestamp", 1)]
            ))
            
            for data in tds_data:
                logs.append({
                    "timestamp": data.get("timestamp"),
                    "event": {
                        "type": "sensor_data",
                        "sensor": "tds",
                        "value": data.get("payload", {}).get("value", 0)
                    }
                })
        
        elif topic == 'heartbeat':
            # Heartbeat-Daten abrufen
            heartbeat_data = list(db.mqtt_messages.find(
                {**query, "topic_parts.2": "heartbeat"},
                sort=[("timestamp", 1)]
            ))
            
            for data in heartbeat_data:
                logs.append({
                    "timestamp": data.get("timestamp"),
                    "event": {
                        "type": "heartbeat",
                        "status": data.get("payload", {}).get("status", "unknown")
                    }
                })
        
        # Konvertiere die Daten in JSON
        logs_json = mongo_to_json(logs)
        
        return jsonify(logs_json)
    
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Logs für Gerät {device_id} und Topic {topic}: {e}")
        return jsonify({"error": str(e)}), 500

# ----------------------------------------
# Neue API-Endpunkte für Programmvorlagen
# ----------------------------------------

@app.route('/api/program-templates', methods=['GET'])
def get_program_templates():
    """Gibt alle Programmvorlagen zurück"""
    try:
        # Alle Programmvorlagen aus der Datenbank abrufen
        templates = list(db.program_templates.find().sort("name", 1))
        
        # Konvertiere die Daten in JSON
        templates_json = mongo_to_json(templates)
        
        return jsonify(templates_json)
    
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Programmvorlagen: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/program-templates', methods=['POST'])
def create_program_template():
    """Erstellt eine neue Programmvorlage"""
    try:
        template_data = request.json
        
        if not template_data or "name" not in template_data:
            return jsonify({"error": "Name der Programmvorlage fehlt"}), 400
        
        # Standard-Phase hinzufügen, falls keine vorhanden
        if "phases" not in template_data or not template_data["phases"]:
            template_data["phases"] = [{
                "phase_id": str(ObjectId()),
                "name": "Standard-Phase",
                "targets": {
                    "ph_min": 5.5,
                    "ph_max": 6.5,
                    "tds_min": 500,
                    "tds_max": 700
                },
                "nutrient_ratio": {
                    "nutrient1_percent": 33.33,
                    "nutrient2_percent": 33.33,
                    "nutrient3_percent": 33.34
                },
                "duration_days": 14,
                "water_pump_cycle_minutes": 60,
                "water_pump_on_minutes": 10,
                "air_pump_cycle_minutes": 60,
                "air_pump_on_minutes": 10
            }]
        else:
            # Validiere die Pumpenparameter jeder Phase
            for phase in template_data["phases"]:
                # Füge Standardwerte für Pumpenparameter hinzu, falls nicht vorhanden
                if "water_pump_cycle_minutes" not in phase:
                    phase["water_pump_cycle_minutes"] = 60
                if "water_pump_on_minutes" not in phase:
                    phase["water_pump_on_minutes"] = 10
                if "air_pump_cycle_minutes" not in phase:
                    phase["air_pump_cycle_minutes"] = 60
                if "air_pump_on_minutes" not in phase:
                    phase["air_pump_on_minutes"] = 10
                
                # Validiere die Pumpenparameter
                valid, errors = validate_pump_parameters(phase)
                if not valid:
                    return jsonify({"error": f"Ungültige Pumpenparameter: {', '.join(errors)}"}), 400
        
        # Füge Metadaten hinzu
        now = datetime.now()
        template_data["template_id"] = str(ObjectId())
        template_data["created_at"] = now
        template_data["updated_at"] = now
        
        # Speichere die Vorlage in der Datenbank
        result = db.program_templates.insert_one(template_data)
        
        logger.info(f"Neue Programmvorlage erstellt: {template_data['name']}")
        
        # Gib die erstellte Vorlage zurück
        created_template = db.program_templates.find_one({"_id": result.inserted_id})
        created_template_json = mongo_to_json(created_template)
        
        return jsonify(created_template_json), 201
    
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Programmvorlage: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/program-templates/<template_id>', methods=['GET'])
def get_program_template(template_id):
    """Gibt eine bestimmte Programmvorlage zurück"""
    try:
        # Programmvorlage aus der Datenbank abrufen
        template = db.program_templates.find_one({"template_id": template_id})
        
        if not template:
            return jsonify({"error": f"Programmvorlage mit ID {template_id} nicht gefunden"}), 404
        
        # Konvertiere die Daten in JSON
        template_json = mongo_to_json(template)
        
        return jsonify(template_json)
    
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Programmvorlage {template_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/program-templates/<template_id>', methods=['PUT'])
def update_program_template(template_id):
    """Aktualisiert eine bestimmte Programmvorlage"""
    try:
        template_data = request.json
        
        if not template_data:
            return jsonify({"error": "Keine Daten zur Aktualisierung der Programmvorlage"}), 400
        
        # Prüfe, ob die Vorlage existiert
        existing_template = db.program_templates.find_one({"template_id": template_id})
        if not existing_template:
            return jsonify({"error": f"Programmvorlage mit ID {template_id} nicht gefunden"}), 404
        
        # Wenn Phasen aktualisiert werden, validiere die Pumpenparameter
        if "phases" in template_data:
            for phase in template_data["phases"]:
                # Füge Standardwerte für Pumpenparameter hinzu, falls nicht vorhanden
                if "water_pump_cycle_minutes" not in phase:
                    phase["water_pump_cycle_minutes"] = 60
                if "water_pump_on_minutes" not in phase:
                    phase["water_pump_on_minutes"] = 10
                if "air_pump_cycle_minutes" not in phase:
                    phase["air_pump_cycle_minutes"] = 60
                if "air_pump_on_minutes" not in phase:
                    phase["air_pump_on_minutes"] = 10
                
                # Validiere die Pumpenparameter
                valid, errors = validate_pump_parameters(phase)
                if not valid:
                    return jsonify({"error": f"Ungültige Pumpenparameter: {', '.join(errors)}"}), 400
        
        # Aktualisiere das updated_at Feld
        template_data["updated_at"] = datetime.now()
        
        # Template-ID nicht ändern
        if "template_id" in template_data:
            del template_data["template_id"]
        
        # Aktualisiere die Vorlage in der Datenbank
        result = db.program_templates.update_one(
            {"template_id": template_id},
            {"$set": template_data}
        )
        
        if result.modified_count == 0:
            return jsonify({"warning": "Keine Änderungen vorgenommen"}), 200
        
        logger.info(f"Programmvorlage {template_id} aktualisiert")
        
        # Gib die aktualisierte Vorlage zurück
        updated_template = db.program_templates.find_one({"template_id": template_id})
        updated_template_json = mongo_to_json(updated_template)
        
        return jsonify(updated_template_json)
    
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren der Programmvorlage {template_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/program-templates/<template_id>', methods=['DELETE'])
def delete_program_template(template_id):
    """Löscht eine bestimmte Programmvorlage"""
    try:
        # Prüfe, ob die Vorlage existiert
        existing_template = db.program_templates.find_one({"template_id": template_id})
        if not existing_template:
            return jsonify({"error": f"Programmvorlage mit ID {template_id} nicht gefunden"}), 404
        
        # Prüfe, ob aktive Programminstanzen existieren, die diese Vorlage verwenden
        active_instances = db.program_instances.find_one({
            "template_id": template_id,
            "status": {"$in": ["running", "paused"]}
        })
        
        if active_instances:
            return jsonify({
                "error": "Programmvorlage kann nicht gelöscht werden, da aktive Programminstanzen existieren"
            }), 400
        
        # Lösche die Vorlage aus der Datenbank
        result = db.program_templates.delete_one({"template_id": template_id})
        
        if result.deleted_count == 0:
            return jsonify({"error": "Programmvorlage konnte nicht gelöscht werden"}), 500
        
        logger.info(f"Programmvorlage {template_id} gelöscht")
        
        return jsonify({
            "success": True,
            "message": f"Programmvorlage {template_id} gelöscht",
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Fehler beim Löschen der Programmvorlage {template_id}: {e}")
        return jsonify({"error": str(e)}), 500

# ----------------------------------------
# Neue API-Endpunkte für Programminstanzen
# ----------------------------------------

@app.route('/api/devices/<device_id>/program-instances', methods=['GET'])
def get_device_program_instances(device_id):
    """Gibt alle Programminstanzen für ein bestimmtes Gerät zurück"""
    try:
        # Alle Programminstanzen für das Gerät aus der Datenbank abrufen
        instances = list(db.program_instances.find(
            {"device_id": device_id}
        ).sort("created_at", -1))
        
        # Template-Daten für aktive Instanzen einbetten
        for instance in instances:
            if (instance.get('status') in ['running', 'paused']) and (template_id := instance.get('template_id')):
                template = db.program_templates.find_one({"template_id": template_id})
                if template:
                    # Entferne MongoDB-spezifische Felder aus dem Template
                    if '_id' in template:
                        del template['_id']
                    # Füge Template-Daten zur Instanz hinzu
                    instance['template'] = template
        
        # Konvertiere die Daten in JSON
        instances_json = mongo_to_json(instances)
        
        return jsonify(instances_json)
    
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Programminstanzen für Gerät {device_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/program-instances/<instance_id>', methods=['GET'])
def get_program_instance(instance_id):
    """Gibt eine bestimmte Programminstanz zurück"""
    try:
        # Programminstanz aus der Datenbank abrufen
        instance = db.program_instances.find_one({"instance_id": instance_id})
        
        if not instance:
            return jsonify({"error": f"Programminstanz mit ID {instance_id} nicht gefunden"}), 404
        
        # Template-Daten einbetten
        if template_id := instance.get('template_id'):
            template = db.program_templates.find_one({"template_id": template_id})
            if template:
                # Entferne MongoDB-spezifische Felder aus dem Template
                if '_id' in template:
                    del template['_id']
                # Füge Template-Daten zur Instanz hinzu
                instance['template'] = template
        
        # Konvertiere die Daten in JSON
        instance_json = mongo_to_json(instance)
        
        return jsonify(instance_json)
    
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Programminstanz {instance_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/program-instances/start', methods=['POST'])
def start_program_instance():
    """Startet ein neues Programm für ein Gerät"""
    try:
        data = request.json
        
        if not data or "device_id" not in data or "template_id" not in data:
            return jsonify({"error": "Gerät-ID und Vorlage-ID werden benötigt"}), 400
        
        device_id = data["device_id"]
        template_id = data["template_id"]
        
        # Prüfe, ob das Gerät existiert
        device = db.configs.find_one({"device_id": device_id})
        if not device:
            return jsonify({"error": f"Gerät mit ID {device_id} nicht gefunden"}), 404
        
        # Prüfe, ob die Vorlage existiert
        template = db.program_templates.find_one({"template_id": template_id})
        if not template:
            return jsonify({"error": f"Programmvorlage mit ID {template_id} nicht gefunden"}), 404
        
        # Prüfe, ob bereits ein aktives Programm für dieses Gerät läuft
        active_instance = db.program_instances.find_one({
            "device_id": device_id,
            "status": {"$in": ["running", "paused"]}
        })
        
        if active_instance:
            return jsonify({
                "error": f"Es läuft bereits ein Programm für Gerät {device_id}",
                "instance_id": active_instance["instance_id"]
            }), 400
        
        # Erstelle eine neue Programminstanz
        now = datetime.now()
        new_instance = {
            "instance_id": str(ObjectId()),
            "template_id": template_id,
            "device_id": device_id,
            "status": "created",
            "current_phase": 0,
            "log": [{
                "timestamp": now.isoformat(),
                "action": "program_created",
                "data": {}
            }],
            "created_at": now.isoformat()
        }
        
        # Speichere die Instanz in der Datenbank
        result = db.program_instances.insert_one(new_instance)
        
        logger.info(f"Neue Programminstanz für Gerät {device_id} mit Vorlage {template_id} erstellt")
        
        # Starte das Programm
        new_instance["status"] = "running"
        new_instance["started_at"] = now.isoformat()
        new_instance["log"].append({
            "timestamp": now.isoformat(),
            "action": "program_started",
            "data": {}
        })
        
        # Aktualisiere die Instanz in der Datenbank
        db.program_instances.update_one(
            {"instance_id": new_instance["instance_id"]},
            {"$set": {
                "status": "running",
                "started_at": now.isoformat(),
                "log": new_instance["log"]
            }}
        )
        
        logger.info(f"Programminstanz {new_instance['instance_id']} gestartet")
        
        # Gib die erstellte Instanz zurück
        instance_json = mongo_to_json(new_instance)
        
        return jsonify(instance_json), 201
    
    except Exception as e:
        logger.error(f"Fehler beim Starten einer Programminstanz: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/program-instances/<instance_id>/pause', methods=['PUT'])
def pause_program_instance(instance_id):
    """Pausiert eine laufende Programminstanz"""
    try:
        # Prüfe, ob die Instanz existiert und läuft
        instance = db.program_instances.find_one({
            "instance_id": instance_id,
            "status": "running"
        })
        
        if not instance:
            return jsonify({"error": f"Keine laufende Programminstanz mit ID {instance_id} gefunden"}), 404
        
        # Aktualisiere Status und Logs
        now = datetime.now()
        
        # Füge neuen Log-Eintrag hinzu
        log_entry = {
            "timestamp": now.isoformat(),
            "action": "program_paused",
            "data": {}
        }
        
        # Aktualisiere die Instanz in der Datenbank
        result = db.program_instances.update_one(
            {"instance_id": instance_id},
            {
                "$set": {
                    "status": "paused",
                    "paused_at": now.isoformat()
                },
                "$push": {"log": log_entry}
            }
        )
        
        if result.modified_count == 0:
            return jsonify({"error": "Programminstanz konnte nicht pausiert werden"}), 500
        
        logger.info(f"Programminstanz {instance_id} pausiert")
        
        # Gib die aktualisierte Instanz zurück
        updated_instance = db.program_instances.find_one({"instance_id": instance_id})
        updated_instance_json = mongo_to_json(updated_instance)
        
        return jsonify(updated_instance_json)
    
    except Exception as e:
        logger.error(f"Fehler beim Pausieren der Programminstanz {instance_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/program-instances/<instance_id>/resume', methods=['PUT'])
def resume_program_instance(instance_id):
    """Setzt eine pausierte Programminstanz fort"""
    try:
        # Prüfe, ob die Instanz existiert und pausiert ist
        instance = db.program_instances.find_one({
            "instance_id": instance_id,
            "status": "paused"
        })
        
        if not instance:
            return jsonify({"error": f"Keine pausierte Programminstanz mit ID {instance_id} gefunden"}), 404
        
        # Aktualisiere Status und Logs
        now = datetime.now()
        
        # Füge neuen Log-Eintrag hinzu
        log_entry = {
            "timestamp": now.isoformat(),
            "action": "program_resumed",
            "data": {}
        }
        
        # Aktualisiere die Instanz in der Datenbank
        result = db.program_instances.update_one(
            {"instance_id": instance_id},
            {
                "$set": {"status": "running"},
                "$unset": {"paused_at": ""},
                "$push": {"log": log_entry}
            }
        )
        
        if result.modified_count == 0:
            return jsonify({"error": "Programminstanz konnte nicht fortgesetzt werden"}), 500
        
        logger.info(f"Programminstanz {instance_id} fortgesetzt")
        
        # Gib die aktualisierte Instanz zurück
        updated_instance = db.program_instances.find_one({"instance_id": instance_id})
        updated_instance_json = mongo_to_json(updated_instance)
        
        return jsonify(updated_instance_json)
    
    except Exception as e:
        logger.error(f"Fehler beim Fortsetzen der Programminstanz {instance_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/program-instances/<instance_id>/stop', methods=['PUT'])
def stop_program_instance(instance_id):
    """Stoppt eine laufende oder pausierte Programminstanz"""
    try:
        # Prüfe, ob die Instanz existiert und aktiv ist
        instance = db.program_instances.find_one({
            "instance_id": instance_id,
            "status": {"$in": ["running", "paused"]}
        })
        
        if not instance:
            return jsonify({"error": f"Keine aktive Programminstanz mit ID {instance_id} gefunden"}), 404
        
        # Aktualisiere Status und Logs
        now = datetime.now()
        
        # Füge neuen Log-Eintrag hinzu
        log_entry = {
            "timestamp": now.isoformat(),
            "action": "program_stopped",
            "data": {}
        }
        
        # Aktualisiere die Instanz in der Datenbank
        update_fields = {
            "$set": {
                "status": "stopped",
                "completed_at": now.isoformat()
            },
            "$push": {"log": log_entry}
        }
        
        # Entferne paused_at, falls vorhanden
        if instance.get("status") == "paused":
            update_fields["$unset"] = {"paused_at": ""}
        
        result = db.program_instances.update_one(
            {"instance_id": instance_id},
            update_fields
        )
        
        if result.modified_count == 0:
            return jsonify({"error": "Programminstanz konnte nicht gestoppt werden"}), 500
        
        logger.info(f"Programminstanz {instance_id} gestoppt")
        
        # Gib die aktualisierte Instanz zurück
        updated_instance = db.program_instances.find_one({"instance_id": instance_id})
        updated_instance_json = mongo_to_json(updated_instance)
        
        return jsonify(updated_instance_json)
    
    except Exception as e:
        logger.error(f"Fehler beim Stoppen der Programminstanz {instance_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/devices/<device_id>/command-history', methods=['GET'])
def get_command_history(device_id):
    """Gibt die Command-History für ein bestimmtes Gerät zurück (device_commands Collection)"""
    try:
        # Zeitraum-Parameter (optional)
        hours = request.args.get('hours')
        end_time = datetime.now()
        query = {"device_id": device_id}
        if hours:
            try:
                hours = int(hours)
                start_time = end_time - timedelta(hours=hours)
                query["timestamp"] = {"$gte": start_time, "$lte": end_time}
            except ValueError:
                return jsonify({"error": "Ungültiger Wert für 'hours'"}), 400
        # Finde alle relevanten Commands (inkl. responses)
        commands = list(db.device_commands.find(query).sort("timestamp", 1))
        return jsonify(mongo_to_json(commands))
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Command-History für Gerät {device_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/devices/<device_id>/calibrate/ph', methods=['POST'])
def calibrate_ph_sensor(device_id):
    """Aktualisiert die pH-Kalibrierung für ein Gerät"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Keine Kalibrierdaten übergeben"}), 400
        # Erwartet: point1_raw, point1_value, point2_raw, point2_value
        required = ["point1_raw", "point1_value", "point2_raw", "point2_value"]
        if not all(k in data for k in required):
            return jsonify({"error": f"Fehlende Felder, erwartet: {required}"}), 400
        config = db.configs.find_one({"device_id": device_id})
        if not config:
            return jsonify({"error": f"Gerät {device_id} nicht gefunden"}), 404
        # Update durchführen
        update = {
            "config.sensors.ph.calibration.point1_raw": data["point1_raw"],
            "config.sensors.ph.calibration.point1_value": data["point1_value"],
            "config.sensors.ph.calibration.point2_raw": data["point2_raw"],
            "config.sensors.ph.calibration.point2_value": data["point2_value"],
            "updated_at": datetime.now(),
            "source": "api"
        }
        db.configs.update_one({"device_id": device_id}, {"$set": update})
        logger.info(f"pH-Kalibrierung für Gerät {device_id} aktualisiert: {data}")
        return jsonify({"success": True, "message": "pH-Kalibrierung aktualisiert"})
    except Exception as e:
        logger.error(f"Fehler bei pH-Kalibrierung für Gerät {device_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/devices/<device_id>/calibrate/tds', methods=['POST'])
def calibrate_tds_sensor(device_id):
    """Aktualisiert die TDS-Kalibrierung für ein Gerät"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Keine Kalibrierdaten übergeben"}), 400
        # Erwartet: raw, value
        required = ["raw", "value"]
        if not all(k in data for k in required):
            return jsonify({"error": f"Fehlende Felder, erwartet: {required}"}), 400
        config = db.configs.find_one({"device_id": device_id})
        if not config:
            return jsonify({"error": f"Gerät {device_id} nicht gefunden"}), 404
        # Update durchführen
        update = {
            "config.sensors.tds.calibration.raw": data["raw"],
            "config.sensors.tds.calibration.value": data["value"],
            "updated_at": datetime.now(),
            "source": "api"
        }
        db.configs.update_one({"device_id": device_id}, {"$set": update})
        logger.info(f"TDS-Kalibrierung für Gerät {device_id} aktualisiert: {data}")
        return jsonify({"success": True, "message": "TDS-Kalibrierung aktualisiert"})
    except Exception as e:
        logger.error(f"Fehler bei TDS-Kalibrierung für Gerät {device_id}: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    logger.info("Server Backend wird gestartet...")
    app.run(host="0.0.0.0", port=5005) 