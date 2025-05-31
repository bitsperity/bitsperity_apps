# HomeGrow v3 - Umbrel Integration

## Übersicht

HomeGrow v3 ist als **native Umbrel-App** konzipiert und integriert sich nahtlos in das Umbrel-Ökosystem. Die Integration erfolgt über **Service Dependencies**, **Container Networking** und **standardisierte Umbrel-Konfiguration**.

```
Umbrel Ecosystem Integration:
├── HomeGrow v3 Container       # Main application
├── bitsperity-mongodb         # Shared database service
├── mosquitto                  # MQTT broker service  
├── bitsperity-beacon          # Service discovery
└── Container Networking       # Inter-service communication
```

## Umbrel App Manifest

### umbrel-app.yml
```yaml
manifestVersion: 1
id: homegrow-v3
category: automation
name: HomeGrow v3
version: "3.0.0"
tagline: Professional hydroponic automation system
description: >-
  HomeGrow v3 is a comprehensive hydroponic automation platform that manages 
  ESP32-based IoT devices for optimal plant growth. Features include real-time 
  monitoring, automated pH/TDS control, growth programs, and mobile PWA support.

developer: Bitsperity Labs
website: https://github.com/bitsperity/homegrow-v3
dependencies:
  - bitsperity-mongodb
  - mosquitto  
  - bitsperity-beacon
repo: https://github.com/bitsperity/homegrow-v3
support: https://github.com/bitsperity/homegrow-v3/issues
port: 3420
gallery:
  - 1.jpg
  - 2.jpg  
  - 3.jpg
path: ""
defaultUsername: ""
defaultPassword: ""
```

## Docker Compose Configuration

### docker-compose.yml
```yaml
version: "3.8"

services:
  app:
    image: homegrow-v3:${APP_VERSION:-latest}
    container_name: homegrow-v3_app_1
    restart: unless-stopped
    
    # Port mapping
    ports:
      - "${APP_PORT:-3420}:3000"
    
    # Environment configuration
    environment:
      - NODE_ENV=production
      - PORT=3000
      
      # Database connection (bitsperity-mongodb)
      - MONGODB_URL=mongodb://umbrel:umbrel@bitsperity-mongodb_mongodb_1:27017/homegrow
      - MONGODB_DB_NAME=homegrow
      
      # MQTT connection (mosquitto)
      - MQTT_HOST=mosquitto_broker_1
      - MQTT_PORT=1883
      - MQTT_USERNAME=
      - MQTT_PASSWORD=
      - MQTT_CLIENT_ID=homegrow-v3
      
      # Service discovery (bitsperity-beacon)
      - BEACON_URL=http://bitsperity-beacon_web_1:8097
      - BEACON_SERVICE_NAME=homegrow-v3
      
      # WebSocket configuration
      - WEBSOCKET_PORT=3000
      - WEBSOCKET_PATH=/api/v1/ws
      
      # Security settings
      - SECRET_KEY=${APP_SECRET:-generate-random-secret}
      - CORS_ORIGIN=${DEVICE_DOMAIN_NAME}
      
      # Logging
      - LOG_LEVEL=info
      - LOG_FORMAT=json
      
    # Volume mounts
    volumes:
      - ${APP_DATA_DIR}/data:/app/data              # Persistent app data
      - ${APP_DATA_DIR}/logs:/app/logs              # Application logs
      - ${APP_DATA_DIR}/backups:/app/backups        # Backup storage
      - ${APP_DATA_DIR}/uploads:/app/uploads        # User uploads
    
    # Network configuration
    networks:
      - default                                      # Default Umbrel network
      - bitsperity-mongodb_default                   # MongoDB network
      - mosquitto_default                            # MQTT network
      - bitsperity-beacon_default                    # Beacon network
    
    # Health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    
    # Resource limits
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
    
    # Dependency management
    depends_on:
      bitsperity-mongodb:
        condition: service_healthy
      mosquitto:
        condition: service_started
      bitsperity-beacon:
        condition: service_started

# External networks (managed by dependency apps)
networks:
  bitsperity-mongodb_default:
    external: true
  mosquitto_default:
    external: true
  bitsperity-beacon_default:
    external: true
```

## Service Discovery Integration

### Beacon Service Registration
```typescript
// src/lib/server/beacon-client.js
import axios from 'axios';

class BeaconClient {
  constructor() {
    this.beaconUrl = process.env.BEACON_URL || 'http://bitsperity-beacon:8097';
    this.serviceName = process.env.BEACON_SERVICE_NAME || 'homegrow-v3';
    this.registrationInterval = null;
  }

  async start() {
    console.log('🔍 Initializing Beacon Service Discovery...');
    
    // Register HomeGrow server for mDNS discovery by ESP32s
    await this.registerService();
    
    // Periodic re-registration (every 5 minutes)
    this.registrationInterval = setInterval(() => {
      this.registerService().catch(console.error);
    }, 5 * 60 * 1000);
  }

  async registerService() {
    try {
      const registration = {
        service_name: this.serviceName,
        service_type: 'homegrow_server',
        ip_address: this.getContainerIP(),
        port: parseInt(process.env.PORT || '3000'),
        capabilities: [
          'hydroponic_automation',
          'device_management', 
          'sensor_monitoring',
          'program_execution',
          'mqtt_integration'
        ],
        metadata: {
          version: process.env.APP_VERSION || '3.0.0',
          api_version: 'v1',
          websocket_endpoint: '/api/v1/ws',
          health_endpoint: '/api/v1/health',
          mqtt_broker: 'mosquitto_broker_1:1883'  // Important for ESP32s
        }
      };

      const response = await axios.post(
        `${this.beaconUrl}/api/register`, 
        registration,
        { timeout: 10000 }
      );

      console.log('✅ HomeGrow server registered with Beacon for mDNS discovery:', response.data);
    } catch (error) {
      console.error('❌ Beacon registration failed:', error.message);
    }
  }

  getContainerIP() {
    // Get container IP for registration
    const os = require('os');
    const interfaces = os.networkInterfaces();
    
    for (const name of Object.keys(interfaces)) {
      for (const iface of interfaces[name]) {
        if (iface.family === 'IPv4' && !iface.internal) {
          return iface.address;
        }
      }
    }
    
    return '127.0.0.1';
  }

  async stop() {
    if (this.registrationInterval) {
      clearInterval(this.registrationInterval);
    }
    
    try {
      await axios.delete(`${this.beaconUrl}/api/services/${this.serviceName}`);
      console.log('✅ Service deregistered from Beacon');
    } catch (error) {
      console.error('❌ Beacon deregistration failed:', error.message);
    }
  }
}

export const beaconClient = new BeaconClient();
```

## MongoDB Integration

### Database Connection Configuration
```typescript
// src/lib/server/database/connection.js
import { MongoClient } from 'mongodb';

class DatabaseConnection {
  constructor() {
    this.client = null;
    this.db = null;
    this.connectionString = this.buildConnectionString();
  }

  buildConnectionString() {
    // Environment-aware connection string
    const baseUrl = process.env.MONGODB_URL || 'mongodb://localhost:27017';
    const dbName = process.env.MONGODB_DB_NAME || 'homegrow';
    
    // Production: Use Umbrel container network
    if (process.env.NODE_ENV === 'production') {
      return `mongodb://umbrel:umbrel@bitsperity-mongodb_mongodb_1:27017/${dbName}`;
    }
    
    // Development: Use external access for MCP integration
    return `mongodb://192.168.178.57:27017/${dbName}`;
  }

  async connect() {
    try {
      console.log('🔌 Connecting to MongoDB...');
      console.log(`📍 Connection: ${this.connectionString.replace(/\/\/.*@/, '//***@')}`);

      this.client = new MongoClient(this.connectionString, {
        // Connection pool settings
        maxPoolSize: 10,
        minPoolSize: 5,
        maxIdleTimeMS: 30000,
        serverSelectionTimeoutMS: 5000,
        
        // Retry settings
        retryWrites: true,
        retryReads: true,
        
        // Compression
        compressors: ['zlib'],
        
        // Monitoring
        monitorCommands: process.env.NODE_ENV === 'development'
      });

      await this.client.connect();
      this.db = this.client.db();

      // Verify connection
      await this.db.admin().ping();
      console.log('✅ MongoDB connected successfully');

      // Initialize indexes
      await this.createIndexes();

      return this.db;
    } catch (error) {
      console.error('❌ MongoDB connection failed:', error);
      throw error;
    }
  }

  async createIndexes() {
    console.log('📋 Creating database indexes...');

    // Device indexes
    await this.db.collection('devices').createIndex(
      { device_id: 1 }, 
      { unique: true }
    );
    await this.db.collection('devices').createIndex({ status: 1, type: 1 });

    // Sensor data indexes (with TTL)
    await this.db.collection('sensor_data').createIndex(
      { device_id: 1, timestamp: -1 }
    );
    await this.db.collection('sensor_data').createIndex(
      { timestamp: 1 }, 
      { expireAfterSeconds: 2592000 } // 30 days TTL
    );

    // Program templates indexes
    await this.db.collection('program_templates').createIndex(
      { template_id: 1 }, 
      { unique: true }
    );
    await this.db.collection('program_templates').createIndex({ type: 1 });

    console.log('✅ Database indexes created');
  }

  async getDB() {
    if (!this.db) {
      await this.connect();
    }
    return this.db;
  }

  async close() {
    if (this.client) {
      await this.client.close();
      console.log('🔌 MongoDB connection closed');
    }
  }
}

const dbConnection = new DatabaseConnection();
export const getDB = () => dbConnection.getDB();
export const closeDB = () => dbConnection.close();
```

## MQTT Integration

### MQTT Bridge Configuration
```typescript
// src/lib/server/mqtt-bridge.js
import mqtt from 'mqtt';
import { getDB } from './database/connection.js';

class MQTTBridge {
  constructor() {
    this.client = null;
    this.isConnected = false;
    this.reconnectDelay = 5000;
    this.topicPrefix = 'homegrow';
  }

  async connect() {
    const options = {
      host: process.env.MQTT_HOST || 'mosquitto',
      port: parseInt(process.env.MQTT_PORT || '1883'),
      clientId: process.env.MQTT_CLIENT_ID || 'homegrow-v3',
      username: process.env.MQTT_USERNAME || undefined,
      password: process.env.MQTT_PASSWORD || undefined,
      
      // Connection settings
      keepalive: 60,
      connectTimeout: 30000,
      reconnectPeriod: this.reconnectDelay,
      clean: true,
      
      // Will message for graceful disconnection detection
      will: {
        topic: `${this.topicPrefix}/server/status`,
        payload: JSON.stringify({
          status: 'offline',
          timestamp: new Date().toISOString()
        }),
        qos: 1,
        retain: true
      }
    };

    console.log('🔌 Connecting to MQTT broker...');
    console.log(`📍 Broker: ${options.host}:${options.port}`);

    this.client = mqtt.connect(options);

    this.client.on('connect', () => {
      console.log('✅ MQTT connected successfully');
      this.isConnected = true;
      this.setupSubscriptions();
      this.publishServerStatus('online');
    });

    this.client.on('error', (error) => {
      console.error('❌ MQTT connection error:', error);
      this.isConnected = false;
    });

    this.client.on('disconnect', () => {
      console.log('🔌 MQTT disconnected');
      this.isConnected = false;
    });

    this.client.on('reconnect', () => {
      console.log('🔄 MQTT reconnecting...');
    });

    this.client.on('message', this.handleMessage.bind(this));
  }

  setupSubscriptions() {
    // Subscribe to all device topics
    const subscriptions = [
      `${this.topicPrefix}/devices/+/sensors/+`,          // Sensor data
      `${this.topicPrefix}/devices/+/commands/response`,  // Command responses
      `${this.topicPrefix}/devices/+/config/request`,     // Config requests
      `${this.topicPrefix}/devices/+/heartbeat`,          // Heartbeat messages
      `${this.topicPrefix}/devices/+/status`,             // Device status
      `${this.topicPrefix}/devices/+/logs`                // System logs
    ];

    subscriptions.forEach(topic => {
      this.client.subscribe(topic, { qos: 1 }, (err) => {
        if (err) {
          console.error(`❌ Failed to subscribe to ${topic}:`, err);
        } else {
          console.log(`📡 Subscribed to ${topic}`);
        }
      });
    });
  }

  async handleMessage(topic, message) {
    try {
      const parts = topic.split('/');
      const data = JSON.parse(message.toString());

      if (parts[2] === 'devices' && parts[4] === 'sensors') {
        // Sensor data message
        await this.handleSensorData(parts[3], parts[5], data);
      } else if (parts[2] === 'devices' && parts[4] === 'config' && parts[5] === 'request') {
        // Config request message (device registration)
        await this.handleConfigRequest(parts[3], data);
      } else if (parts[2] === 'devices' && parts[4] === 'commands' && parts[5] === 'response') {
        // Command response message
        await this.handleCommandResponse(parts[3], data);
      } else if (parts[2] === 'devices' && parts[4] === 'heartbeat') {
        // Heartbeat message
        await this.handleHeartbeat(parts[3], data);
      } else if (parts[2] === 'devices' && parts[4] === 'status') {
        // Device status message
        await this.handleDeviceStatus(parts[3], data);
      } else if (parts[2] === 'devices' && parts[4] === 'logs') {
        // System logs message
        await this.handleDeviceLogs(parts[3], data);
      }
    } catch (error) {
      console.error('❌ Error processing MQTT message:', error);
    }
  }

  async handleConfigRequest(deviceId, data) {
    const db = await getDB();
    
    console.log(`📋 Config request from device ${deviceId}:`, data);
    
    // Check if device already exists
    let existingDevice = await db.collection('devices').findOne({
      device_id: deviceId
    });

    if (!existingDevice) {
      // Create new device with default configuration
      console.log(`🆕 Creating new device ${deviceId} from config request`);
      existingDevice = await this.createDefaultDevice(deviceId, data);
    } else {
      // Update existing device with request info
      await db.collection('devices').updateOne(
        { device_id: deviceId },
        { 
          $set: { 
            status: 'online',
            last_seen: new Date(),
            'mqtt_info.firmware_version': data.firmware_version,
            'mqtt_info.capabilities': data.capabilities
          } 
        }
      );
      console.log(`✅ Existing device ${deviceId} updated from config request`);
    }

    // Send config response
    await this.sendConfigResponse(deviceId, existingDevice.config);
    
    // Broadcast device registration/update to WebSocket clients
    const { websocketServer } = await import('./websocket-server.js');
    websocketServer.broadcast('device_status', {
      device_id: deviceId,
      status: 'online',
      action: existingDevice ? 'device_updated' : 'device_registered',
      device_info: existingDevice
    });
  }

  async createDefaultDevice(deviceId, requestData) {
    const db = await getDB();
    
    const newDevice = {
      device_id: deviceId,
      name: `HomeGrow Device ${deviceId}`,
      type: 'hydroponic_controller',
      status: 'online',
      config: {
        mqtt_topics: {
          sensors: `${this.topicPrefix}/devices/${deviceId}/sensors`,
          commands: `${this.topicPrefix}/devices/${deviceId}/commands`,
          status: `${this.topicPrefix}/devices/${deviceId}/status`,
          config_request: `${this.topicPrefix}/devices/${deviceId}/config/request`,
          config_response: `${this.topicPrefix}/devices/${deviceId}/config/response`
        },
        sensors: {
          ph: {
            enabled: true,
            pin: 34,
            calibration: { slope: 3.5, offset: 0.0 },
            update_interval: 60,
            noise_filter: {
              enabled: true,
              type: "moving_average",
              window_size: 10
            }
          },
          tds: {
            enabled: true,
            pin: 35,
            calibration: { factor: 0.5 },
            update_interval: 60,
            noise_filter: {
              enabled: true,
              type: "exponential",
              alpha: 0.1
            }
          }
        },
        pumps: {
          water: { enabled: true, pin: 16, max_duration: 300, flow_rate_ml_per_sec: 50.0 },
          air: { enabled: true, pin: 17, max_duration: 3600, flow_rate_ml_per_sec: 0 },
          ph_down: { enabled: true, pin: 18, max_duration: 60, flow_rate_ml_per_sec: 2.67 },
          ph_up: { enabled: true, pin: 19, max_duration: 60, flow_rate_ml_per_sec: 2.67 },
          nutrient_a: { enabled: true, pin: 20, max_duration: 30, flow_rate_ml_per_sec: 2.67 },
          nutrient_b: { enabled: true, pin: 21, max_duration: 30, flow_rate_ml_per_sec: 2.67 },
          cal_mag: { enabled: true, pin: 22, max_duration: 20, flow_rate_ml_per_sec: 2.67 }
        },
        safety: {
          ph_min: 4.0,
          ph_max: 8.5,
          tds_max: 2000,
          max_pump_duration: 300,
          pump_cooldown: 30
        },
        system: {
          heartbeat_interval: 30,
          log_level: "INFO",
          ota_enabled: true,
          watchdog_enabled: true
        }
      },
      mqtt_info: {
        first_seen: new Date(),
        capabilities: requestData.capabilities || ['ph_sensor', 'tds_sensor', 'pumps_7x'],
        firmware_version: requestData.firmware_version || 'v3.0.0'
      },
      stats: {
        total_runtime: 0,
        command_count: 0,
        sensor_readings: 0
      },
      created_at: new Date(),
      updated_at: new Date(),
      last_seen: new Date()
    };

    await db.collection('devices').insertOne(newDevice);
    console.log(`✅ Device ${deviceId} created with default configuration`);
    
    return newDevice;
  }

  async sendConfigResponse(deviceId, config) {
    const configTopic = `${this.topicPrefix}/devices/${deviceId}/config/response`;
    
    const configResponse = {
      device_id: deviceId,
      timestamp: new Date().toISOString(),
      config: {
        sensors: config.sensors,
        pumps: config.pumps,
        safety: config.safety,
        system: config.system
      },
      mqtt_topics: config.mqtt_topics
    };

    const payload = JSON.stringify(configResponse);
    
    return new Promise((resolve, reject) => {
      this.client.publish(configTopic, payload, { qos: 1 }, (error) => {
        if (error) {
          console.error(`❌ Failed to send config response to ${deviceId}:`, error);
          reject(error);
        } else {
          console.log(`📤 Config response sent to ${deviceId}`);
          resolve();
        }
      });
    });
  }

  async handleSensorData(deviceId, sensorType, data) {
    const db = await getDB();
    
    // Store sensor data
    const sensorReading = {
      device_id: deviceId,
      sensor_type: sensorType,
      timestamp: new Date(data.timestamp || Date.now()),
      values: {
        raw: data.values?.raw || data.raw,
        calibrated: data.values?.calibrated || data.calibrated,
        filtered: data.values?.filtered || data.filtered || data.values?.calibrated || data.calibrated
      },
      unit: data.unit,
      quality: data.quality || 'good'
    };

    await db.collection('sensor_data').insertOne(sensorReading);

    // Update device last_seen
    await db.collection('devices').updateOne(
      { device_id: deviceId },
      { 
        $set: { 
          last_seen: sensorReading.timestamp,
          status: 'online'
        } 
      }
    );

    // Trigger automation engine
    const { automationEngine } = await import('./automation-engine.js');
    await automationEngine.processSensorData(deviceId, sensorType, sensorReading.values.calibrated);

    // Broadcast to WebSocket clients
    const { websocketServer } = await import('./websocket-server.js');
    websocketServer.broadcast('sensor_data', {
      device_id: deviceId,
      sensor_type: sensorType,
      value: sensorReading.values.calibrated,
      unit: data.unit,
      quality: data.quality,
      timestamp: sensorReading.timestamp.toISOString()
    });
  }

  async handleCommandResponse(deviceId, data) {
    const db = await getDB();
    
    // Store command response
    const commandResponse = {
      device_id: deviceId,
      command_id: data.command_id,
      action: data.action,
      params: data.params,
      timestamp: new Date(data.timestamp || Date.now()),
      response: data.response,
      status: data.status
    };

    await db.collection('command_responses').insertOne(commandResponse);

    // Update device last_seen
    await db.collection('devices').updateOne(
      { device_id: deviceId },
      { 
        $set: { 
          last_seen: commandResponse.timestamp,
          status: 'online'
        } 
      }
    );

    // Trigger automation engine
    const { automationEngine } = await import('./automation-engine.js');
    await automationEngine.processCommandResponse(deviceId, commandResponse);

    // Broadcast to WebSocket clients
    const { websocketServer } = await import('./websocket-server.js');
    websocketServer.broadcast('command_response', {
      device_id: deviceId,
      command_id: commandResponse.command_id,
      action: commandResponse.action,
      response: commandResponse.response,
      status: commandResponse.status,
      timestamp: commandResponse.timestamp.toISOString()
    });
  }

  async handleHeartbeat(deviceId, data) {
    const db = await getDB();
    
    // Store heartbeat
    const heartbeat = {
      device_id: deviceId,
      timestamp: new Date(data.timestamp || Date.now()),
      heartbeat: data.heartbeat
    };

    await db.collection('heartbeats').insertOne(heartbeat);

    // Update device last_seen
    await db.collection('devices').updateOne(
      { device_id: deviceId },
      { 
        $set: { 
          last_seen: heartbeat.timestamp,
          status: 'online'
        } 
      }
    );

    // Trigger automation engine
    const { automationEngine } = await import('./automation-engine.js');
    await automationEngine.processHeartbeat(deviceId, heartbeat);

    // Broadcast to WebSocket clients
    const { websocketServer } = await import('./websocket-server.js');
    websocketServer.broadcast('heartbeat', {
      device_id: deviceId,
      timestamp: heartbeat.timestamp.toISOString(),
      heartbeat: heartbeat.heartbeat
    });
  }

  async handleDeviceStatus(deviceId, data) {
    const db = await getDB();
    
    // Store device status
    const deviceStatus = {
      device_id: deviceId,
      status: data.status,
      timestamp: new Date(data.timestamp || Date.now())
    };

    await db.collection('device_statuses').insertOne(deviceStatus);

    // Update device last_seen
    await db.collection('devices').updateOne(
      { device_id: deviceId },
      { 
        $set: { 
          last_seen: deviceStatus.timestamp,
          status: data.status
        } 
      }
    );

    // Trigger automation engine
    const { automationEngine } = await import('./automation-engine.js');
    await automationEngine.processDeviceStatus(deviceId, data.status);

    // Broadcast to WebSocket clients
    const { websocketServer } = await import('./websocket-server.js');
    websocketServer.broadcast('device_status', {
      device_id: deviceId,
      status: data.status,
      action: 'status_updated',
      device_info: deviceStatus
    });
  }

  async handleDeviceLogs(deviceId, data) {
    const db = await getDB();
    
    // Store device logs
    const deviceLog = {
      device_id: deviceId,
      log_type: data.log_type,
      message: data.message,
      timestamp: new Date(data.timestamp || Date.now())
    };

    await db.collection('device_logs').insertOne(deviceLog);

    // Update device last_seen
    await db.collection('devices').updateOne(
      { device_id: deviceId },
      { 
        $set: { 
          last_seen: deviceLog.timestamp,
          status: 'online'
        } 
      }
    );

    // Trigger automation engine
    const { automationEngine } = await import('./automation-engine.js');
    await automationEngine.processDeviceLogs(deviceId, deviceLog);

    // Broadcast to WebSocket clients
    const { websocketServer } = await import('./websocket-server.js');
    websocketServer.broadcast('device_log', {
      device_id: deviceId,
      log_type: deviceLog.log_type,
      message: deviceLog.message,
      timestamp: deviceLog.timestamp.toISOString()
    });
  }

  async publishCommand(deviceId, command) {
    if (!this.isConnected) {
      throw new Error('MQTT not connected');
    }

    const topic = `${this.topicPrefix}/devices/${deviceId}/commands`;
    const payload = JSON.stringify({
      command_id: command.command_id,
      action: command.action,
      params: command.params,
      timestamp: new Date().toISOString()
    });

    return new Promise((resolve, reject) => {
      this.client.publish(topic, payload, { qos: 1 }, (error) => {
        if (error) {
          reject(error);
        } else {
          console.log(`📤 Command sent to ${deviceId}:`, command.action);
          resolve();
        }
      });
    });
  }

  publishServerStatus(status) {
    if (this.client) {
      this.client.publish(
        `${this.topicPrefix}/server/status`,
        JSON.stringify({
          status,
          timestamp: new Date().toISOString(),
          version: process.env.APP_VERSION
        }),
        { qos: 1, retain: true }
      );
    }
  }

  async disconnect() {
    if (this.client) {
      this.publishServerStatus('offline');
      this.client.end();
      console.log('🔌 MQTT disconnected');
    }
  }
}

export const mqttBridge = new MQTTBridge();
```

## Environment Configuration

### Development vs Production
```typescript
// src/lib/server/config.js
export const config = {
  // Database configuration
  database: {
    url: process.env.NODE_ENV === 'production'
      ? 'mongodb://umbrel:umbrel@bitsperity-mongodb_mongodb_1:27017/homegrow'
      : 'mongodb://192.168.178.57:27017/homegrow',
    options: {
      maxPoolSize: 10,
      serverSelectionTimeoutMS: 5000
    }
  },

  // MQTT configuration  
  mqtt: {
    host: process.env.NODE_ENV === 'production'
      ? 'mosquitto_broker_1'
      : '192.168.178.57',
    port: 1883,
    clientId: 'homegrow-v3'
  },

  // Beacon service discovery
  beacon: {
    url: process.env.NODE_ENV === 'production'
      ? 'http://bitsperity-beacon_web_1:8097'
      : 'http://192.168.178.57:8097',
    serviceName: 'homegrow-v3'
  },

  // WebSocket configuration
  websocket: {
    port: parseInt(process.env.PORT || '3000'),
    path: '/api/v1/ws'
  },

  // Security
  security: {
    secretKey: process.env.SECRET_KEY || 'dev-secret-key',
    corsOrigin: process.env.CORS_ORIGIN || '*'
  },

  // Application settings
  app: {
    port: parseInt(process.env.PORT || '3000'),
    logLevel: process.env.LOG_LEVEL || 'info',
    dataDir: process.env.APP_DATA_DIR || './data'
  }
};
```

## Umbrel App Store Integration

### app-store.yml (für Bitsperity Store)
```yaml
id: homegrow-v3
name: HomeGrow v3
tagline: Professional hydroponic automation
icon: https://raw.githubusercontent.com/bitsperity/homegrow-v3/main/assets/icon.svg
category: automation
version: "3.0.0"
port: 3420

description: |
  HomeGrow v3 is a comprehensive hydroponic automation platform designed for 
  serious growers. It provides real-time monitoring, automated control, and 
  data-driven insights for optimal plant growth.

  **Key Features:**
  - 🌱 Automated pH and TDS control
  - 📊 Real-time sensor monitoring with charts
  - 📱 Mobile PWA with offline support  
  - 🤖 Growth program automation
  - 🔔 Smart alerts and notifications
  - 📈 Performance analytics and reporting

  **ESP32 Integration:**
  HomeGrow v3 integrates with ESP32-based hydroponic controllers that include:
  - pH and TDS sensors with automatic calibration
  - 7 pump types (water, air, nutrients, pH correction)
  - WiFi connectivity with automatic discovery
  - Over-the-air firmware updates

  **Getting Started:**
  1. Install HomeGrow v3 from the Umbrel app store
  2. Set up your ESP32 hydroponic controller
  3. Connect devices through automatic discovery
  4. Create or select a growth program template
  5. Monitor and enjoy optimal plant growth!

releaseNotes: |
  **v3.0.0 - Initial Release**
  - Complete rewrite with modern SvelteKit architecture
  - Improved performance and mobile experience
  - Enhanced automation engine with safety features
  - Real-time charts and monitoring dashboard
  - Growth program templates for common crops
  - Comprehensive alert system

developer: Bitsperity Labs
website: https://bitsperity.com/homegrow
repo: https://github.com/bitsperity/homegrow-v3
support: https://github.com/bitsperity/homegrow-v3/discussions

dependencies:
  - bitsperity-mongodb
  - mosquitto
  - bitsperity-beacon

screenshots:
  - https://raw.githubusercontent.com/bitsperity/homegrow-v3/main/screenshots/dashboard.png
  - https://raw.githubusercontent.com/bitsperity/homegrow-v3/main/screenshots/monitoring.png
  - https://raw.githubusercontent.com/bitsperity/homegrow-v3/main/screenshots/programs.png
  - https://raw.githubusercontent.com/bitsperity/homegrow-v3/main/screenshots/mobile.png

submitter: Bitsperity Labs
submission: https://github.com/getumbrel/umbrel-apps/pull/XXXX
```

## Deployment Considerations

### Resource Requirements
```yaml
# Minimum system requirements
resources:
  minimum:
    memory: 256MB
    cpu: 0.25 cores
    storage: 2GB
  
  recommended:
    memory: 512MB
    cpu: 0.5 cores
    storage: 10GB
    
  scaling:
    max_devices: 50
    max_sensor_readings_per_day: 100000
    max_concurrent_programs: 100
```

### Health Monitoring
```typescript
// Health check endpoint implementation
export async function GET() {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime_seconds: process.uptime(),
    version: process.env.APP_VERSION,
    components: {
      database: await checkDatabase(),
      mqtt: await checkMQTT(),
      beacon: await checkBeacon(),
      websocket: checkWebSocket()
    }
  };

  const unhealthyComponents = Object.values(health.components)
    .filter(component => component.status !== 'connected' && component.status !== 'running');

  if (unhealthyComponents.length > 0) {
    health.status = unhealthyComponents.length === Object.keys(health.components).length 
      ? 'unhealthy' 
      : 'degraded';
  }

  return new Response(JSON.stringify(health), {
    status: health.status === 'healthy' ? 200 : 503,
    headers: { 'Content-Type': 'application/json' }
  });
}
```

### Backup Integration
```bash
#!/bin/bash
# backup-script.sh - Integrated with Umbrel backup system

BACKUP_DIR="/app/backups"
DATA_DIR="/app/data" 
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Export MongoDB data
mongodump --host bitsperity-mongodb_mongodb_1:27017 \
  --db homegrow \
  --out $BACKUP_DIR/mongodb_$TIMESTAMP

# Archive application data
tar -czf $BACKUP_DIR/app_data_$TIMESTAMP.tar.gz \
  -C $DATA_DIR \
  --exclude="logs" \
  --exclude="temp" \
  .

# Cleanup old backups (keep last 7 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "mongodb_*" -mtime +7 -exec rm -rf {} \;

echo "Backup completed: $TIMESTAMP"
```

Diese Umbrel-Integration stellt sicher, dass HomeGrow v3 nahtlos in das Umbrel-Ökosystem integriert wird und alle Standard-Praktiken für Umbrel-Apps befolgt. 