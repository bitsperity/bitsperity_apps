const mqtt = require('mqtt');
const EventEmitter = require('events');

class MQTTBridge extends EventEmitter {
  constructor(mqttUrl, deviceModel, sensorDataModel, commandModel) {
    super();
    this.mqttUrl = mqttUrl || 'mqtt://umbrel-mqtt:1883';
    this.client = null;
    this.deviceModel = deviceModel;
    this.sensorDataModel = sensorDataModel;
    this.commandModel = commandModel;
    this.subscribedTopics = new Set();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.isConnected = false;
  }

  async connect() {
    return new Promise((resolve, reject) => {
      console.log(`🔌 Connecting to MQTT broker: ${this.mqttUrl}`);
      
      this.client = mqtt.connect(this.mqttUrl, {
        clientId: `homegrow-server-${Date.now()}`,
        clean: true,
        connectTimeout: 30000,
        reconnectPeriod: 5000,
        keepalive: 60
      });

      this.client.on('connect', () => {
        console.log('✅ Connected to MQTT broker');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.subscribeToTopics();
        resolve();
      });

      this.client.on('error', (error) => {
        console.error('❌ MQTT connection error:', error);
        this.isConnected = false;
        reject(error);
      });

      this.client.on('message', (topic, message) => {
        this.handleMessage(topic, message);
      });

      this.client.on('reconnect', () => {
        this.reconnectAttempts++;
        console.log(`🔄 MQTT reconnecting (attempt ${this.reconnectAttempts})`);
      });

      this.client.on('offline', () => {
        console.log('📴 MQTT client offline');
        this.isConnected = false;
      });

      this.client.on('close', () => {
        console.log('📴 MQTT connection closed');
        this.isConnected = false;
      });
    });
  }

  subscribeToTopics() {
    const topics = [
      'homegrow/devices/+/sensors/+',
      'homegrow/devices/+/heartbeat',
      'homegrow/devices/+/status',
      'homegrow/devices/+/commands/response',
      'homegrow/devices/+/logs'
    ];

    topics.forEach(topic => {
      this.client.subscribe(topic, (err) => {
        if (err) {
          console.error(`❌ Failed to subscribe to ${topic}:`, err);
        } else {
          console.log(`📡 Subscribed to ${topic}`);
          this.subscribedTopics.add(topic);
        }
      });
    });
  }

  async handleMessage(topic, message) {
    try {
      const topicParts = topic.split('/');
      const deviceId = topicParts[2];
      const messageType = topicParts[3];
      
      let payload;
      try {
        payload = JSON.parse(message.toString());
      } catch (error) {
        console.error(`❌ Invalid JSON in message from ${topic}:`, error);
        return;
      }

      switch (messageType) {
        case 'sensors':
          await this.handleSensorData(deviceId, topicParts[4], payload);
          break;
        case 'heartbeat':
          await this.handleHeartbeat(deviceId, payload);
          break;
        case 'status':
          await this.handleStatusUpdate(deviceId, payload);
          break;
        case 'commands':
          if (topicParts[4] === 'response') {
            await this.handleCommandResponse(deviceId, payload);
          }
          break;
        case 'logs':
          await this.handleLogMessage(deviceId, payload);
          break;
        default:
          console.log(`❓ Unknown message type: ${messageType}`);
      }
    } catch (error) {
      console.error('❌ Error handling MQTT message:', error);
    }
  }

  async handleSensorData(deviceId, sensorType, payload) {
    // Validate sensor data
    if (!this.validateSensorData(payload)) {
      console.error(`❌ Invalid sensor data from ${deviceId}:`, payload);
      return;
    }

    // Store in database
    const sensorData = {
      device_id: deviceId,
      sensor_type: sensorType,
      timestamp: payload.timestamp || new Date().toISOString(),
      device_timestamp: payload.device_timestamp,
      values: payload.values,
      unit: payload.unit,
      quality: payload.quality,
      calibration_status: payload.calibration_status,
      filter_config: payload.filter_config
    };

    try {
      await this.sensorDataModel.insert(sensorData);

      // Update device last seen
      await this.deviceModel.updateStatus(deviceId, 'online');

      // Emit event for real-time updates
      this.emit('sensor_data', {
        device_id: deviceId,
        sensor_type: sensorType,
        data: sensorData
      });

      console.log(`📊 Sensor data: ${deviceId}/${sensorType} = ${payload.values.calibrated} ${payload.unit}`);
    } catch (error) {
      console.error(`❌ Error storing sensor data for ${deviceId}:`, error);
    }
  }

  async handleHeartbeat(deviceId, payload) {
    try {
      await this.deviceModel.updateStatus(deviceId, 'online');
      
      // Update device stats if provided
      if (payload.stats) {
        await this.deviceModel.updateStats(deviceId, payload.stats);
      }

      this.emit('device_heartbeat', { device_id: deviceId, payload });
      console.log(`💓 Heartbeat from ${deviceId}`);
    } catch (error) {
      console.error(`❌ Error handling heartbeat from ${deviceId}:`, error);
    }
  }

  async handleStatusUpdate(deviceId, payload) {
    try {
      const updateData = {
        status: payload.status,
        updated_at: new Date()
      };

      if (payload.wifi_signal) {
        updateData['config.wifi.signal_strength'] = payload.wifi_signal;
      }

      await this.deviceModel.collection.updateOne(
        { device_id: deviceId },
        { $set: updateData }
      );

      this.emit('device_status', { device_id: deviceId, status: payload.status });
      console.log(`📱 Status update from ${deviceId}: ${payload.status}`);
    } catch (error) {
      console.error(`❌ Error handling status update from ${deviceId}:`, error);
    }
  }

  async handleCommandResponse(deviceId, payload) {
    try {
      // Update command status in database if commandModel is available
      if (this.commandModel) {
        await this.commandModel.updateResponse(payload.command_id, payload);
      }

      this.emit('command_response', {
        device_id: deviceId,
        command_id: payload.command_id,
        response: payload
      });

      console.log(`⚡ Command response: ${deviceId}/${payload.command_id} = ${payload.status}`);
    } catch (error) {
      console.error(`❌ Error handling command response from ${deviceId}:`, error);
    }
  }

  async handleLogMessage(deviceId, payload) {
    // Store log message
    console.log(`📝 Device log [${deviceId}]: ${payload.level} - ${payload.message}`);
    
    this.emit('device_log', {
      device_id: deviceId,
      log: payload
    });
  }

  validateSensorData(payload) {
    return payload &&
           payload.values &&
           typeof payload.values.raw === 'number' &&
           typeof payload.values.calibrated === 'number' &&
           typeof payload.values.filtered === 'number' &&
           payload.unit &&
           payload.timestamp;
  }

  async publishCommand(deviceId, command) {
    if (!this.isConnected) {
      throw new Error('MQTT client not connected');
    }

    const topic = `homegrow/devices/${deviceId}/commands`;
    const payload = JSON.stringify(command);

    return new Promise((resolve, reject) => {
      this.client.publish(topic, payload, { qos: 1 }, (error) => {
        if (error) {
          console.error(`❌ Failed to publish command to ${deviceId}:`, error);
          reject(error);
        } else {
          console.log(`⚡ Command published to ${deviceId}: ${command.command}`);
          resolve();
        }
      });
    });
  }

  async subscribeToDevice(deviceId) {
    if (!this.isConnected) {
      console.warn(`⚠️ Cannot subscribe to device ${deviceId}: MQTT not connected`);
      return;
    }

    const topics = [
      `homegrow/devices/${deviceId}/sensors/+`,
      `homegrow/devices/${deviceId}/heartbeat`,
      `homegrow/devices/${deviceId}/status`,
      `homegrow/devices/${deviceId}/commands/response`,
      `homegrow/devices/${deviceId}/logs`
    ];

    for (const topic of topics) {
      if (!this.subscribedTopics.has(topic)) {
        await new Promise((resolve, reject) => {
          this.client.subscribe(topic, (err) => {
            if (err) {
              console.error(`❌ Failed to subscribe to ${topic}:`, err);
              reject(err);
            } else {
              console.log(`📡 Subscribed to device topic: ${topic}`);
              this.subscribedTopics.add(topic);
              resolve();
            }
          });
        });
      }
    }
  }

  async unsubscribeFromDevice(deviceId) {
    if (!this.isConnected) {
      return;
    }

    const topics = [
      `homegrow/devices/${deviceId}/sensors/+`,
      `homegrow/devices/${deviceId}/heartbeat`,
      `homegrow/devices/${deviceId}/status`,
      `homegrow/devices/${deviceId}/commands/response`,
      `homegrow/devices/${deviceId}/logs`
    ];

    for (const topic of topics) {
      if (this.subscribedTopics.has(topic)) {
        await new Promise((resolve) => {
          this.client.unsubscribe(topic, (err) => {
            if (err) {
              console.error(`❌ Failed to unsubscribe from ${topic}:`, err);
            } else {
              console.log(`📡 Unsubscribed from device topic: ${topic}`);
              this.subscribedTopics.delete(topic);
            }
            resolve();
          });
        });
      }
    }
  }

  async publishConfigUpdate(deviceId, config) {
    const command = {
      command_id: `config_${Date.now()}`,
      command: 'update_config',
      params: config,
      timestamp: new Date().toISOString()
    };

    return await this.publishCommand(deviceId, command);
  }

  async publishEmergencyStop(deviceId) {
    const command = {
      command_id: `emergency_${Date.now()}`,
      command: 'emergency_stop',
      params: {},
      priority: 'high',
      timestamp: new Date().toISOString()
    };

    return await this.publishCommand(deviceId, command);
  }

  getConnectionStatus() {
    return {
      connected: this.isConnected,
      reconnect_attempts: this.reconnectAttempts,
      subscribed_topics: Array.from(this.subscribedTopics)
    };
  }

  disconnect() {
    if (this.client) {
      console.log('📴 Disconnecting from MQTT broker');
      this.client.end();
      this.isConnected = false;
    }
  }
}

module.exports = MQTTBridge; 