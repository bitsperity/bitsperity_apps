import mqtt from 'mqtt';
import EventEmitter from 'events';

class MQTTBridgeService extends EventEmitter {
    constructor(config) {
        super();
        this.config = config;
        this.client = null;
        this.isConnected = false;
        
        // ESP32 System Konfiguration basierend auf echtem System
        this.sensorTypes = ['ph', 'tds']; // Nur diese 2 Sensoren!
        this.pumpTypes = [
            'water_pump',
            'air_pump', 
            'ph_up_pump',
            'ph_down_pump',
            'nutrient_pump_1',
            'nutrient_pump_2', 
            'nutrient_pump_3'
        ]; // 7 Pumpen total
        
        this.devicePrefix = 'homegrow'; // Fixed prefix aus ESP32 Code
    }

    async connect() {
        try {
            const mqttUrl = `mqtt://${this.config.MQTT_HOST}:${this.config.MQTT_PORT}`;
            console.log(`Verbinde mit MQTT Broker: ${mqttUrl}`);
            
            this.client = mqtt.connect(mqttUrl, {
                clientId: `homegrow_backend_v3_${Date.now()}`,
                clean: true,
                reconnectPeriod: 5000,
                connectTimeout: 30000
            });

            this.client.on('connect', () => {
                console.log('✅ MQTT Bridge erfolgreich verbunden');
                this.isConnected = true;
                this.subscribeToTopics();
                this.emit('connected');
            });

            this.client.on('error', (error) => {
                console.error('❌ MQTT Bridge Fehler:', error);
                this.emit('error', error);
            });

            this.client.on('message', (topic, message) => {
                this.handleMessage(topic, message.toString());
            });

            this.client.on('close', () => {
                console.log('📡 MQTT Bridge Verbindung geschlossen');
                this.isConnected = false;
                this.emit('disconnected');
            });

        } catch (error) {
            console.error('❌ Fehler beim Verbinden mit MQTT:', error);
            throw error;
        }
    }

    subscribeToTopics() {
        // Subscribe zu Sensor-Daten (alle Geräte)
        // Topic Format: homegrow/{device_id}/sensor/{ph|tds}
        this.sensorTypes.forEach(sensorType => {
            const topic = `${this.devicePrefix}/+/sensor/${sensorType}`;
            this.client.subscribe(topic, (err) => {
                if (err) {
                    console.error(`❌ Fehler beim Abonnieren von ${topic}:`, err);
                } else {
                    console.log(`📡 Abonniert: ${topic}`);
                }
            });
        });

        // Subscribe zu Command-Responses
        // Topic Format: homegrow/{device_id}/command/response
        const responsesTopic = `${this.devicePrefix}/+/command/response`;
        this.client.subscribe(responsesTopic, (err) => {
            if (err) {
                console.error(`❌ Fehler beim Abonnieren von ${responsesTopic}:`, err);
            } else {
                console.log(`📡 Abonniert: ${responsesTopic}`);
            }
        });
    }

    handleMessage(topic, messageStr) {
        try {
            const topicParts = topic.split('/');
            if (topicParts.length < 3 || topicParts[0] !== this.devicePrefix) {
                return; // Nicht unser Topic-Format
            }

            const deviceId = topicParts[1];
            const messageType = topicParts[2];

            if (messageType === 'sensor' && topicParts.length === 4) {
                // Sensor-Daten: homegrow/{device_id}/sensor/{ph|tds}
                const sensorType = topicParts[3];
                this.handleSensorData(deviceId, sensorType, messageStr);
                
            } else if (messageType === 'command' && topicParts[3] === 'response') {
                // Command-Response: homegrow/{device_id}/command/response
                this.handleCommandResponse(deviceId, messageStr);
            }

        } catch (error) {
            console.error('❌ Fehler beim Verarbeiten der MQTT-Nachricht:', error);
        }
    }

    handleSensorData(deviceId, sensorType, messageStr) {
        try {
            let data;
            
            // Try to parse as JSON first, fallback to plain number
            try {
                data = JSON.parse(messageStr);
                // If it's a valid JSON object with value property
                if (typeof data === 'object' && data.value !== undefined) {
                    // ESP32 sendet: {"value": 6.2, "raw": 1023, "timestamp": 1234567890}
                } else if (typeof data === 'number') {
                    // JSON number
                    data = { value: data };
                } else {
                    throw new Error('Unexpected JSON format');
                }
            } catch (jsonError) {
                // Try to parse as plain number
                const numValue = parseFloat(messageStr);
                if (isNaN(numValue)) {
                    throw new Error(`Cannot parse sensor value: ${messageStr}`);
                }
                data = { value: numValue };
            }
            
            const sensorReading = {
                deviceId,
                sensorType,
                value: data.value,
                rawValue: data.raw || null,
                timestamp: new Date(data.timestamp || Date.now()),
                receivedAt: new Date()
            };

            console.log(`📊 Sensor-Daten erhalten - ${deviceId}/${sensorType}: ${data.value}`);
            this.emit('sensorData', sensorReading);

        } catch (error) {
            console.error(`❌ Fehler beim Parsen der Sensor-Daten von ${deviceId}/${sensorType}:`, error);
            console.error(`❌ Rohe Nachricht: "${messageStr}"`);
        }
    }

    handleCommandResponse(deviceId, messageStr) {
        try {
            const response = JSON.parse(messageStr);
            
            // ESP32 sendet: {"type": "water_pump", "status": "received", "timestamp": 1234567890}
            const commandResponse = {
                deviceId,
                commandType: response.type,
                status: response.status,
                timestamp: new Date(response.timestamp || Date.now()),
                receivedAt: new Date()
            };

            console.log(`✅ Command-Response erhalten - ${deviceId}: ${response.type} = ${response.status}`);
            this.emit('commandResponse', commandResponse);

        } catch (error) {
            console.error(`❌ Fehler beim Parsen der Command-Response von ${deviceId}:`, error);
        }
    }

    // Pumpen-Kommando senden
    sendPumpCommand(deviceId, pumpType, durationMs) {
        if (!this.isConnected) {
            throw new Error('MQTT Bridge nicht verbunden');
        }

        if (!this.pumpTypes.includes(pumpType)) {
            throw new Error(`Unbekannter Pumpen-Typ: ${pumpType}`);
        }

        const command = {
            type: pumpType,
            duration: parseInt(durationMs),
            timestamp: Date.now()
        };

        const topic = `${this.devicePrefix}/${deviceId}/command`;
        const payload = JSON.stringify(command);

        console.log(`🚰 Sende Pumpen-Kommando: ${topic} = ${payload}`);

        return new Promise((resolve, reject) => {
            this.client.publish(topic, payload, { qos: 1 }, (error) => {
                if (error) {
                    console.error(`❌ Fehler beim Senden des Kommandos:`, error);
                    reject(error);
                } else {
                    console.log(`✅ Kommando erfolgreich gesendet: ${pumpType} für ${durationMs}ms`);
                    resolve(command);
                }
            });
        });
    }

    // Kalibrierung anfordern (für pH/TDS Sensoren)
    sendCalibrationCommand(deviceId, sensorType, calibrationData) {
        if (!this.isConnected) {
            throw new Error('MQTT Bridge nicht verbunden');
        }

        if (!this.sensorTypes.includes(sensorType)) {
            throw new Error(`Unbekannter Sensor-Typ: ${sensorType}`);
        }

        const command = {
            type: `${sensorType}_calibration`,
            data: calibrationData,
            timestamp: Date.now()
        };

        const topic = `${this.devicePrefix}/${deviceId}/command`;
        const payload = JSON.stringify(command);

        console.log(`🔬 Sende Kalibrierungs-Kommando: ${topic} = ${payload}`);

        return new Promise((resolve, reject) => {
            this.client.publish(topic, payload, { qos: 1 }, (error) => {
                if (error) {
                    reject(error);
                } else {
                    resolve(command);
                }
            });
        });
    }

    disconnect() {
        if (this.client && this.isConnected) {
            console.log('📡 MQTT Bridge wird getrennt...');
            this.client.end();
            this.isConnected = false;
        }
    }

    getStatus() {
        return {
            connected: this.isConnected,
            supportedSensors: this.sensorTypes,
            supportedPumps: this.pumpTypes,
            devicePrefix: this.devicePrefix
        };
    }
}

export default MQTTBridgeService; 