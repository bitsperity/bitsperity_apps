import mqtt from 'mqtt';
import { MongoClient } from 'mongodb';
import { createLogger } from '../utils/logger.js';
import { MessageHandler } from './message-handler.js';
import { DataRetentionService } from './data-retention.js';
import { DeviceManager } from './device-manager.js';

const logger = createLogger('mqtt-bridge');

export class MQTTBridge {
  constructor(config) {
    this.config = config;
    this.mqttClient = null;
    this.mongoClient = null;
    this.db = null;
    this.messageHandler = null;
    this.dataRetentionService = null;
    this.deviceManager = null;
    this.isRunning = false;
  }

  async start() {
    try {
      // Connect to MongoDB
      await this.connectMongoDB();
      
      // Initialize services
      this.messageHandler = new MessageHandler(this.db, this.config);
      this.deviceManager = new DeviceManager(this.db, this.config);
      this.dataRetentionService = new DataRetentionService(this.db, this.config);
      
      // Connect to MQTT
      await this.connectMQTT();
      
      // Start data retention service
      await this.dataRetentionService.start();
      
      this.isRunning = true;
      logger.info('MQTT Bridge started successfully');
      
    } catch (error) {
      logger.error('Failed to start MQTT Bridge:', error);
      throw error;
    }
  }

  async stop() {
    try {
      this.isRunning = false;
      
      // Stop data retention service
      if (this.dataRetentionService) {
        await this.dataRetentionService.stop();
      }
      
      // Disconnect from MQTT
      if (this.mqttClient) {
        await new Promise((resolve) => {
          this.mqttClient.end(true, {}, resolve);
        });
        logger.info('Disconnected from MQTT broker');
      }
      
      // Disconnect from MongoDB
      if (this.mongoClient) {
        await this.mongoClient.close();
        logger.info('Disconnected from MongoDB');
      }
      
    } catch (error) {
      logger.error('Error during shutdown:', error);
      throw error;
    }
  }

  async connectMongoDB() {
    try {
      logger.info('Connecting to MongoDB...', { uri: this.config.mongodb.uri });
      
      this.mongoClient = new MongoClient(this.config.mongodb.uri, this.config.mongodb.options);
      await this.mongoClient.connect();
      
      this.db = this.mongoClient.db(this.config.mongodb.database);
      
      // Create indexes
      await this.createIndexes();
      
      logger.info('Connected to MongoDB successfully');
      
    } catch (error) {
      logger.error('Failed to connect to MongoDB:', error);
      throw error;
    }
  }

  async createIndexes() {
    try {
      const collections = this.config.mongodb.collections;
      
      // Devices collection indexes
      await this.db.collection(collections.devices).createIndex({ device_id: 1 }, { unique: true });
      await this.db.collection(collections.devices).createIndex({ status: 1 });
      await this.db.collection(collections.devices).createIndex({ last_seen: -1 });
      
      // Sensor data collection indexes
      await this.db.collection(collections.sensorData).createIndex({ device_id: 1, timestamp: -1 });
      await this.db.collection(collections.sensorData).createIndex({ timestamp: -1 });
      await this.db.collection(collections.sensorData).createIndex({ sensor_type: 1 });
      
      // Commands collection indexes
      await this.db.collection(collections.commands).createIndex({ device_id: 1, timestamp: -1 });
      await this.db.collection(collections.commands).createIndex({ command_id: 1 });
      await this.db.collection(collections.commands).createIndex({ status: 1 });
      
      // System logs collection indexes
      await this.db.collection(collections.systemLogs).createIndex({ device_id: 1, timestamp: -1 });
      await this.db.collection(collections.systemLogs).createIndex({ level: 1 });
      
      logger.info('Database indexes created successfully');
      
    } catch (error) {
      logger.error('Failed to create indexes:', error);
      throw error;
    }
  }

  async connectMQTT() {
    return new Promise((resolve, reject) => {
      const mqttOptions = {
        clientId: this.config.mqtt.clientId,
        clean: this.config.mqtt.clean,
        reconnectPeriod: this.config.mqtt.reconnectPeriod,
        connectTimeout: this.config.mqtt.connectTimeout,
      };

      if (this.config.mqtt.username) {
        mqttOptions.username = this.config.mqtt.username;
        mqttOptions.password = this.config.mqtt.password;
      }

      const brokerUrl = `mqtt://${this.config.mqtt.host}:${this.config.mqtt.port}`;
      logger.info('Connecting to MQTT broker...', { url: brokerUrl });

      this.mqttClient = mqtt.connect(brokerUrl, mqttOptions);

      this.mqttClient.on('connect', () => {
        logger.info('Connected to MQTT broker');
        this.subscribeToTopics();
        resolve();
      });

      this.mqttClient.on('error', (error) => {
        logger.error('MQTT connection error:', error);
        if (!this.isRunning) {
          reject(error);
        }
      });

      this.mqttClient.on('reconnect', () => {
        logger.info('Reconnecting to MQTT broker...');
      });

      this.mqttClient.on('close', () => {
        logger.warn('MQTT connection closed');
      });

      this.mqttClient.on('message', this.handleMessage.bind(this));
    });
  }

  subscribeToTopics() {
    const topics = Object.values(this.config.mqtt.topics);
    
    this.mqttClient.subscribe(topics, { qos: 1 }, (error) => {
      if (error) {
        logger.error('Failed to subscribe to topics:', error);
      } else {
        logger.info('Subscribed to MQTT topics', { topics });
      }
    });
  }

  async handleMessage(topic, message) {
    try {
      const payload = JSON.parse(message.toString());
      logger.debug('Received MQTT message', { topic, payload });
      
      // Extract device ID from topic
      const topicParts = topic.split('/');
      const deviceId = topicParts[2];
      
      // Update device last seen
      if (deviceId && deviceId !== '+') {
        await this.deviceManager.updateLastSeen(deviceId);
      }
      
      // Handle message based on topic pattern
      if (topic.includes('/sensors/')) {
        await this.messageHandler.handleSensorData(topic, payload);
      } else if (topic.includes('/commands/response')) {
        await this.messageHandler.handleCommandResponse(topic, payload);
      } else if (topic.includes('/heartbeat')) {
        await this.messageHandler.handleHeartbeat(topic, payload);
      } else if (topic.includes('/status')) {
        await this.messageHandler.handleStatus(topic, payload);
      } else if (topic.includes('/logs')) {
        await this.messageHandler.handleLogs(topic, payload);
      } else if (topic.includes('/config/response')) {
        await this.messageHandler.handleConfigResponse(topic, payload);
      } else if (topic.includes('/discovery/')) {
        await this.messageHandler.handleDiscovery(topic, payload);
      } else if (topic.includes('/programs/')) {
        await this.messageHandler.handleProgramUpdate(topic, payload);
      }
      
    } catch (error) {
      logger.error('Error handling MQTT message:', { topic, error: error.message });
    }
  }

  // Publish message to MQTT
  async publish(topic, payload) {
    return new Promise((resolve, reject) => {
      if (!this.mqttClient || !this.mqttClient.connected) {
        reject(new Error('MQTT client not connected'));
        return;
      }

      const message = JSON.stringify(payload);
      this.mqttClient.publish(topic, message, { qos: 1 }, (error) => {
        if (error) {
          logger.error('Failed to publish MQTT message:', { topic, error });
          reject(error);
        } else {
          logger.debug('Published MQTT message', { topic, payload });
          resolve();
        }
      });
    });
  }
} 