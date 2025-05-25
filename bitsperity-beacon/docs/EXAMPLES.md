# Bitsperity Beacon - Integration Examples

Diese Dokumentation zeigt praktische Beispiele für die Integration von Bitsperity Beacon in verschiedene Anwendungen und Umgebungen.

## HomegrowClient Integration

### Automatische Service Registrierung

```python
# homegrow_client/beacon_integration.py
import requests
import time
import threading
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class BeaconIntegration:
    def __init__(self, beacon_url: str = "http://beacon.local:8080/api/v1"):
        self.beacon_url = beacon_url
        self.service_id: Optional[str] = None
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.running = False
        
    def register_service(self, host: str, port: int) -> bool:
        """Registriere HomegrowClient bei Beacon"""
        service_data = {
            "name": "homegrow-client",
            "type": "iot",
            "host": host,
            "port": port,
            "protocol": "http",
            "tags": ["iot", "agriculture", "sensors", "monitoring"],
            "metadata": {
                "version": "1.0.0",
                "description": "HomegrowClient für Pflanzenüberwachung",
                "capabilities": "sensors,irrigation,monitoring",
                "location": "greenhouse-1"
            },
            "ttl": 300,  # 5 Minuten
            "health_check_url": f"http://{host}:{port}/health",
            "health_check_interval": 60
        }
        
        try:
            response = requests.post(
                f"{self.beacon_url}/services/register",
                json=service_data,
                timeout=10
            )
            response.raise_for_status()
            
            service_info = response.json()
            self.service_id = service_info["service_id"]
            
            logger.info(f"Service bei Beacon registriert: {self.service_id}")
            
            # Starte Heartbeat Thread
            self.start_heartbeat()
            
            return True
            
        except Exception as e:
            logger.error(f"Beacon Registrierung fehlgeschlagen: {e}")
            return False
    
    def start_heartbeat(self):
        """Starte automatische Heartbeats"""
        if self.service_id and not self.running:
            self.running = True
            self.heartbeat_thread = threading.Thread(
                target=self._heartbeat_loop,
                daemon=True
            )
            self.heartbeat_thread.start()
            logger.info("Heartbeat Thread gestartet")
    
    def _heartbeat_loop(self):
        """Heartbeat Loop"""
        while self.running and self.service_id:
            try:
                time.sleep(60)  # Alle 60 Sekunden
                
                response = requests.put(
                    f"{self.beacon_url}/services/{self.service_id}/heartbeat",
                    timeout=5
                )
                response.raise_for_status()
                
                logger.debug("Heartbeat gesendet")
                
            except Exception as e:
                logger.warning(f"Heartbeat fehlgeschlagen: {e}")
                # Bei mehreren Fehlern neu registrieren
                time.sleep(30)
    
    def deregister(self):
        """Deregistriere Service"""
        self.running = False
        
        if self.service_id:
            try:
                response = requests.delete(
                    f"{self.beacon_url}/services/{self.service_id}",
                    timeout=5
                )
                logger.info("Service deregistriert")
                
            except Exception as e:
                logger.warning(f"Deregistrierung fehlgeschlagen: {e}")
            
            self.service_id = None

# Integration in HomegrowClient
class HomegrowClient:
    def __init__(self):
        self.beacon = BeaconIntegration()
        
    def start(self, host: str = "0.0.0.0", port: int = 8080):
        """Starte HomegrowClient mit Beacon Integration"""
        # Registriere bei Beacon
        self.beacon.register_service(host, port)
        
        # Starte Flask App
        self.app.run(host=host, port=port)
    
    def shutdown(self):
        """Graceful Shutdown"""
        self.beacon.deregister()
```

### MQTT Broker Discovery

```python
# homegrow_client/mqtt_discovery.py
import requests
from typing import Optional, Dict, Any

class MQTTDiscovery:
    def __init__(self, beacon_url: str = "http://beacon.local:8080/api/v1"):
        self.beacon_url = beacon_url
    
    def find_mqtt_broker(self) -> Optional[Dict[str, Any]]:
        """Finde MQTT Broker über Beacon"""
        try:
            response = requests.get(
                f"{self.beacon_url}/services/discover",
                params={"type": "mqtt", "status": "active"},
                timeout=10
            )
            response.raise_for_status()
            
            discovery_result = response.json()
            services = discovery_result.get("services", [])
            
            if services:
                # Nimm den ersten verfügbaren MQTT Broker
                mqtt_service = services[0]
                return {
                    "host": mqtt_service["host"],
                    "port": mqtt_service["port"],
                    "service_id": mqtt_service["service_id"],
                    "metadata": mqtt_service.get("metadata", {})
                }
            
            return None
            
        except Exception as e:
            print(f"MQTT Discovery fehlgeschlagen: {e}")
            return None

# Verwendung in HomegrowClient
mqtt_discovery = MQTTDiscovery()
mqtt_broker = mqtt_discovery.find_mqtt_broker()

if mqtt_broker:
    import paho.mqtt.client as mqtt
    
    client = mqtt.Client()
    client.connect(mqtt_broker["host"], mqtt_broker["port"], 60)
    
    # Publiziere Sensor-Daten
    client.publish("homegrow/sensors/temperature", "23.5")
    client.publish("homegrow/sensors/humidity", "65.2")
```

## Arduino/ESP32 Integration

### mDNS Service Discovery

```cpp
// arduino_beacon_client.ino
#include <WiFi.h>
#include <ESPmDNS.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

class BeaconClient {
private:
    String beaconHost;
    int beaconPort;
    String serviceId;
    unsigned long lastHeartbeat;
    
public:
    BeaconClient() : beaconHost(""), beaconPort(8080), lastHeartbeat(0) {}
    
    bool discoverBeacon() {
        Serial.println("Suche nach Beacon Service...");
        
        // mDNS Query für Beacon
        int n = MDNS.queryService("http", "tcp");
        
        for (int i = 0; i < n; i++) {
            String hostname = MDNS.hostname(i);
            int port = MDNS.port(i);
            
            // Prüfe ob es Beacon ist (über TXT Records oder Name)
            if (hostname.indexOf("beacon") >= 0) {
                beaconHost = hostname;
                beaconPort = port;
                Serial.printf("Beacon gefunden: %s:%d\n", hostname.c_str(), port);
                return true;
            }
        }
        
        Serial.println("Kein Beacon Service gefunden");
        return false;
    }
    
    bool registerService(String name, String type, String host, int port) {
        if (beaconHost.isEmpty()) {
            if (!discoverBeacon()) {
                return false;
            }
        }
        
        HTTPClient http;
        http.begin(String("http://") + beaconHost + ":" + beaconPort + "/api/v1/services/register");
        http.addHeader("Content-Type", "application/json");
        
        // JSON Payload erstellen
        DynamicJsonDocument doc(1024);
        doc["name"] = name;
        doc["type"] = type;
        doc["host"] = host;
        doc["port"] = port;
        doc["protocol"] = "http";
        doc["ttl"] = 300;
        
        JsonArray tags = doc.createNestedArray("tags");
        tags.add("arduino");
        tags.add("esp32");
        tags.add("iot");
        
        JsonObject metadata = doc.createNestedObject("metadata");
        metadata["version"] = "1.0.0";
        metadata["platform"] = "ESP32";
        metadata["chip_id"] = String(ESP.getChipId());
        
        String payload;
        serializeJson(doc, payload);
        
        int httpResponseCode = http.POST(payload);
        
        if (httpResponseCode == 201) {
            String response = http.getString();
            
            DynamicJsonDocument responseDoc(1024);
            deserializeJson(responseDoc, response);
            
            serviceId = responseDoc["service_id"].as<String>();
            Serial.printf("Service registriert: %s\n", serviceId.c_str());
            
            http.end();
            return true;
        } else {
            Serial.printf("Registrierung fehlgeschlagen: %d\n", httpResponseCode);
            http.end();
            return false;
        }
    }
    
    void sendHeartbeat() {
        if (serviceId.isEmpty() || beaconHost.isEmpty()) {
            return;
        }
        
        unsigned long now = millis();
        if (now - lastHeartbeat < 60000) { // Alle 60 Sekunden
            return;
        }
        
        HTTPClient http;
        String url = String("http://") + beaconHost + ":" + beaconPort + 
                    "/api/v1/services/" + serviceId + "/heartbeat";
        http.begin(url);
        
        int httpResponseCode = http.PUT("");
        
        if (httpResponseCode == 200) {
            Serial.println("Heartbeat gesendet");
            lastHeartbeat = now;
        } else {
            Serial.printf("Heartbeat fehlgeschlagen: %d\n", httpResponseCode);
        }
        
        http.end();
    }
    
    String discoverMQTTBroker() {
        // mDNS Query für MQTT Service
        int n = MDNS.queryService("mqtt", "tcp");
        
        if (n > 0) {
            String host = MDNS.hostname(0);
            int port = MDNS.port(0);
            
            Serial.printf("MQTT Broker gefunden: %s:%d\n", host.c_str(), port);
            return host + ":" + String(port);
        }
        
        Serial.println("Kein MQTT Broker gefunden");
        return "";
    }
};

// Global instance
BeaconClient beacon;

void setup() {
    Serial.begin(115200);
    
    // WiFi verbinden
    WiFi.begin("SSID", "PASSWORD");
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Verbinde mit WiFi...");
    }
    
    // mDNS starten
    if (!MDNS.begin("esp32-sensor")) {
        Serial.println("mDNS Start fehlgeschlagen");
    }
    
    // Bei Beacon registrieren
    String localIP = WiFi.localIP().toString();
    beacon.registerService("esp32-sensor", "iot", localIP, 80);
    
    // MQTT Broker finden
    String mqttBroker = beacon.discoverMQTTBroker();
    if (!mqttBroker.isEmpty()) {
        // MQTT Client initialisieren
        // ...
    }
}

void loop() {
    // Heartbeat senden
    beacon.sendHeartbeat();
    
    // Sensor-Daten lesen und senden
    // ...
    
    delay(1000);
}
```

## Node.js Microservice Integration

### Express.js Service mit Beacon

```javascript
// microservice/beacon-client.js
const axios = require('axios');
const WebSocket = require('ws');

class BeaconClient {
    constructor(beaconUrl = 'http://beacon.local:8080/api/v1') {
        this.beaconUrl = beaconUrl;
        this.serviceId = null;
        this.heartbeatInterval = null;
        this.ws = null;
    }
    
    async registerService(serviceData) {
        try {
            const response = await axios.post(`${this.beaconUrl}/services/register`, serviceData);
            this.serviceId = response.data.service_id;
            
            console.log(`Service registriert: ${this.serviceId}`);
            
            // Starte Heartbeat
            this.startHeartbeat();
            
            // Verbinde WebSocket für Updates
            this.connectWebSocket();
            
            return response.data;
        } catch (error) {
            console.error('Service Registrierung fehlgeschlagen:', error.message);
            throw error;
        }
    }
    
    startHeartbeat() {
        if (this.serviceId) {
            this.heartbeatInterval = setInterval(async () => {
                try {
                    await axios.put(`${this.beaconUrl}/services/${this.serviceId}/heartbeat`);
                    console.log('Heartbeat gesendet');
                } catch (error) {
                    console.error('Heartbeat fehlgeschlagen:', error.message);
                }
            }, 60000); // Alle 60 Sekunden
        }
    }
    
    connectWebSocket() {
        const wsUrl = this.beaconUrl.replace('http', 'ws') + '/ws';
        this.ws = new WebSocket(wsUrl);
        
        this.ws.on('open', () => {
            console.log('WebSocket zu Beacon verbunden');
        });
        
        this.ws.on('message', (data) => {
            const message = JSON.parse(data);
            this.handleWebSocketMessage(message);
        });
        
        this.ws.on('close', () => {
            console.log('WebSocket Verbindung geschlossen');
            // Reconnect nach 5 Sekunden
            setTimeout(() => this.connectWebSocket(), 5000);
        });
    }
    
    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'service_registered':
                console.log('Neuer Service registriert:', message.data.name);
                break;
            case 'service_deregistered':
                console.log('Service deregistriert:', message.data.service_id);
                break;
            default:
                console.log('WebSocket Message:', message);
        }
    }
    
    async discoverServices(filters = {}) {
        try {
            const response = await axios.get(`${this.beaconUrl}/services/discover`, {
                params: filters
            });
            return response.data.services;
        } catch (error) {
            console.error('Service Discovery fehlgeschlagen:', error.message);
            return [];
        }
    }
    
    async deregister() {
        if (this.serviceId) {
            try {
                await axios.delete(`${this.beaconUrl}/services/${this.serviceId}`);
                console.log('Service deregistriert');
            } catch (error) {
                console.error('Deregistrierung fehlgeschlagen:', error.message);
            }
        }
        
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }
        
        if (this.ws) {
            this.ws.close();
        }
    }
}

module.exports = BeaconClient;
```

### Express.js App mit Beacon Integration

```javascript
// microservice/app.js
const express = require('express');
const BeaconClient = require('./beacon-client');
const os = require('os');

const app = express();
const port = process.env.PORT || 3000;
const beacon = new BeaconClient();

app.use(express.json());

// Health Check Endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        memory: process.memoryUsage()
    });
});

// API Endpoints
app.get('/api/data', (req, res) => {
    res.json({
        message: 'Hello from Microservice',
        timestamp: new Date().toISOString()
    });
});

// Graceful Shutdown
process.on('SIGTERM', async () => {
    console.log('SIGTERM empfangen, starte Graceful Shutdown...');
    await beacon.deregister();
    process.exit(0);
});

process.on('SIGINT', async () => {
    console.log('SIGINT empfangen, starte Graceful Shutdown...');
    await beacon.deregister();
    process.exit(0);
});

// Server starten
app.listen(port, async () => {
    console.log(`Microservice läuft auf Port ${port}`);
    
    // Lokale IP ermitteln
    const networkInterfaces = os.networkInterfaces();
    const localIP = Object.values(networkInterfaces)
        .flat()
        .find(iface => iface.family === 'IPv4' && !iface.internal)?.address;
    
    // Bei Beacon registrieren
    try {
        await beacon.registerService({
            name: 'my-microservice',
            type: 'api',
            host: localIP || 'localhost',
            port: port,
            protocol: 'http',
            tags: ['api', 'microservice', 'nodejs'],
            metadata: {
                version: '1.0.0',
                description: 'Example Node.js Microservice',
                platform: 'nodejs',
                hostname: os.hostname()
            },
            ttl: 300,
            health_check_url: `http://${localIP || 'localhost'}:${port}/health`,
            health_check_interval: 60
        });
        
        // Entdecke andere Services
        const services = await beacon.discoverServices({ type: 'api' });
        console.log(`${services.length} andere API Services gefunden`);
        
    } catch (error) {
        console.error('Beacon Integration fehlgeschlagen:', error.message);
    }
});
```

## Docker Compose Service Discovery

### Multi-Service Setup mit Beacon

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Bitsperity Beacon
  beacon:
    image: bitsperity/beacon:latest
    container_name: beacon
    network_mode: host
    environment:
      BEACON_MONGODB_URL: mongodb://mongodb:27017/beacon
    depends_on:
      - mongodb
    
  # MongoDB
  mongodb:
    image: mongo:7
    container_name: mongodb
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
    volumes:
      - mongodb_data:/data/db
  
  # MQTT Broker
  mosquitto:
    image: eclipse-mosquitto:2
    container_name: mosquitto
    ports:
      - "1883:1883"
      - "9001:9001"
    volumes:
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf
    depends_on:
      - beacon
    environment:
      BEACON_URL: http://beacon:8080/api/v1
    command: >
      sh -c "
        # Registriere MQTT Broker bei Beacon
        curl -X POST http://beacon:8080/api/v1/services/register \
          -H 'Content-Type: application/json' \
          -d '{
            \"name\": \"mosquitto-broker\",
            \"type\": \"mqtt\",
            \"host\": \"mosquitto\",
            \"port\": 1883,
            \"protocol\": \"mqtt\",
            \"tags\": [\"mqtt\", \"broker\", \"messaging\"],
            \"metadata\": {
              \"version\": \"2.0\",
              \"description\": \"Eclipse Mosquitto MQTT Broker\"
            },
            \"ttl\": 600
          }' &&
        # Starte Mosquitto
        /usr/sbin/mosquitto -c /mosquitto/config/mosquitto.conf
      "
  
  # API Service
  api-service:
    build: ./api-service
    container_name: api-service
    ports:
      - "3000:3000"
    environment:
      BEACON_URL: http://beacon:8080/api/v1
      MQTT_BROKER_URL: mqtt://mosquitto:1883
    depends_on:
      - beacon
      - mosquitto

volumes:
  mongodb_data:
```

### Service Registration Script

```bash
#!/bin/bash
# register-services.sh

BEACON_URL="http://localhost:8080/api/v1"

# Registriere API Service
curl -X POST $BEACON_URL/services/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "api-service",
    "type": "api",
    "host": "localhost",
    "port": 3000,
    "protocol": "http",
    "tags": ["api", "rest", "nodejs"],
    "metadata": {
      "version": "1.0.0",
      "description": "Main API Service"
    },
    "ttl": 300,
    "health_check_url": "http://localhost:3000/health"
  }'

# Registriere Database Service
curl -X POST $BEACON_URL/services/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "mongodb",
    "type": "database",
    "host": "localhost",
    "port": 27017,
    "protocol": "mongodb",
    "tags": ["database", "mongodb", "nosql"],
    "metadata": {
      "version": "7.0",
      "description": "MongoDB Database"
    },
    "ttl": 600
  }'

echo "Services registriert!"
```

## Kubernetes Integration

### Service Registration mit Init Container

```yaml
# k8s-service-with-beacon.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      initContainers:
      - name: beacon-register
        image: curlimages/curl:latest
        env:
        - name: BEACON_URL
          value: "http://beacon.default.svc.cluster.local:8080/api/v1"
        - name: SERVICE_NAME
          value: "my-app"
        - name: SERVICE_TYPE
          value: "api"
        - name: SERVICE_PORT
          value: "3000"
        command:
        - sh
        - -c
        - |
          # Warte auf Beacon
          until curl -f $BEACON_URL/health; do
            echo "Warte auf Beacon..."
            sleep 5
          done
          
          # Registriere Service
          curl -X POST $BEACON_URL/services/register \
            -H "Content-Type: application/json" \
            -d "{
              \"name\": \"$SERVICE_NAME\",
              \"type\": \"$SERVICE_TYPE\",
              \"host\": \"$SERVICE_NAME.default.svc.cluster.local\",
              \"port\": $SERVICE_PORT,
              \"protocol\": \"http\",
              \"tags\": [\"kubernetes\", \"api\"],
              \"metadata\": {
                \"namespace\": \"default\",
                \"deployment\": \"my-app\"
              },
              \"ttl\": 300
            }"
      
      containers:
      - name: my-app
        image: my-app:latest
        ports:
        - containerPort: 3000
        env:
        - name: BEACON_URL
          value: "http://beacon.default.svc.cluster.local:8080/api/v1"
        
        # Heartbeat Sidecar
      - name: beacon-heartbeat
        image: curlimages/curl:latest
        env:
        - name: BEACON_URL
          value: "http://beacon.default.svc.cluster.local:8080/api/v1"
        command:
        - sh
        - -c
        - |
          # Hole Service ID (vereinfacht)
          SERVICE_ID=$(curl -s "$BEACON_URL/services?name=my-app" | jq -r '.services[0].service_id')
          
          # Heartbeat Loop
          while true; do
            sleep 60
            curl -X PUT "$BEACON_URL/services/$SERVICE_ID/heartbeat" || true
          done

---
apiVersion: v1
kind: Service
metadata:
  name: my-app
spec:
  selector:
    app: my-app
  ports:
  - port: 3000
    targetPort: 3000
```

Diese Beispiele zeigen, wie Bitsperity Beacon in verschiedene Umgebungen und Technologien integriert werden kann, um automatische Service Discovery und Management zu ermöglichen. 