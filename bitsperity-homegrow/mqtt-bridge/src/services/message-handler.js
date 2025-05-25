import { createLogger } from '../utils/logger.js';
import { validateSensorData, validateCommand } from '../utils/validators.js';

const logger = createLogger('message-handler');

export class MessageHandler {
  constructor(db, config) {
    this.db = db;
    this.config = config;
    this.collections = config.mongodb.collections;
  }

  async handleSensorData(topic, payload) {
    try {
      // Extract device ID and sensor type from topic
      const topicParts = topic.split('/');
      const deviceId = topicParts[2];
      const sensorType = topicParts[4];

      // Validate sensor data
      const validatedData = validateSensorData(payload);

      // Prepare document for MongoDB
      const sensorDoc = {
        device_id: deviceId,
        sensor_type: sensorType,
        timestamp: new Date(validatedData.timestamp || Date.now()),
        device_timestamp: validatedData.device_timestamp,
        values: validatedData.values,
        unit: validatedData.unit,
        quality: validatedData.quality || 'unknown',
        calibration_status: validatedData.calibration_status,
        filter_config: validatedData.filter_config,
        created_at: new Date()
      };

      // Insert sensor data
      await this.db.collection(this.collections.sensorData).insertOne(sensorDoc);

      // Update device sensor status
      await this.updateDeviceSensorStatus(deviceId, sensorType, validatedData);

      logger.debug('Sensor data stored', { deviceId, sensorType, values: validatedData.values });

    } catch (error) {
      logger.error('Error handling sensor data:', { topic, error: error.message });
    }
  }

  async handleCommandResponse(topic, payload) {
    try {
      const topicParts = topic.split('/');
      const deviceId = topicParts[2];

      const commandUpdate = {
        device_id: deviceId,
        command_id: payload.command_id,
        status: payload.status,
        result: payload.result,
        error: payload.error,
        execution_time_ms: payload.execution_time_ms,
        completed_at: new Date(payload.timestamp || Date.now())
      };

      // Update command status
      await this.db.collection(this.collections.commands).updateOne(
        { command_id: payload.command_id, device_id: deviceId },
        { 
          $set: {
            status: payload.status,
            result: payload.result,
            error: payload.error,
            execution_time_ms: payload.execution_time_ms,
            completed_at: commandUpdate.completed_at,
            updated_at: new Date()
          }
        }
      );

      logger.debug('Command response processed', { deviceId, commandId: payload.command_id, status: payload.status });

    } catch (error) {
      logger.error('Error handling command response:', { topic, error: error.message });
    }
  }

  async handleHeartbeat(topic, payload) {
    try {
      const topicParts = topic.split('/');
      const deviceId = topicParts[2];

      const heartbeatData = {
        device_id: deviceId,
        timestamp: new Date(payload.timestamp || Date.now()),
        uptime_seconds: payload.uptime_seconds,
        free_heap: payload.free_heap,
        wifi_rssi: payload.wifi_rssi,
        mqtt_connected: payload.mqtt_connected,
        sensor_status: payload.sensor_status,
        pump_status: payload.pump_status,
        active_program: payload.active_program,
        system_health: payload.system_health
      };

      // Update device status
      await this.db.collection(this.collections.devices).updateOne(
        { device_id: deviceId },
        {
          $set: {
            status: 'online',
            last_heartbeat: heartbeatData.timestamp,
            system_stats: {
              uptime_seconds: heartbeatData.uptime_seconds,
              free_heap: heartbeatData.free_heap,
              wifi_rssi: heartbeatData.wifi_rssi
            },
            sensor_status: heartbeatData.sensor_status,
            pump_status: heartbeatData.pump_status,
            active_program: heartbeatData.active_program,
            system_health: heartbeatData.system_health,
            updated_at: new Date()
          }
        },
        { upsert: true }
      );

      logger.debug('Heartbeat processed', { deviceId, uptime: payload.uptime_seconds });

    } catch (error) {
      logger.error('Error handling heartbeat:', { topic, error: error.message });
    }
  }

  async handleStatus(topic, payload) {
    try {
      const topicParts = topic.split('/');
      const deviceId = topicParts[2];

      const statusDoc = {
        device_id: deviceId,
        timestamp: new Date(payload.timestamp || Date.now()),
        status_type: payload.status_type,
        data: payload.data,
        created_at: new Date()
      };

      // Store status update
      await this.db.collection(this.collections.systemLogs).insertOne({
        ...statusDoc,
        log_type: 'status_update'
      });

      // Update device with latest status
      if (payload.status_type === 'system') {
        await this.db.collection(this.collections.devices).updateOne(
          { device_id: deviceId },
          {
            $set: {
              system_status: payload.data,
              updated_at: new Date()
            }
          }
        );
      }

      logger.debug('Status update processed', { deviceId, statusType: payload.status_type });

    } catch (error) {
      logger.error('Error handling status:', { topic, error: error.message });
    }
  }

  async handleLogs(topic, payload) {
    try {
      const topicParts = topic.split('/');
      const deviceId = topicParts[2];

      const logDoc = {
        device_id: deviceId,
        timestamp: new Date(payload.timestamp || Date.now()),
        level: payload.level || 'info',
        message: payload.message,
        module: payload.module,
        data: payload.data,
        created_at: new Date()
      };

      // Store log entry
      await this.db.collection(this.collections.systemLogs).insertOne(logDoc);

      // Check for critical errors
      if (payload.level === 'error' || payload.level === 'critical') {
        await this.createNotification(deviceId, 'error', payload.message, payload.data);
      }

      logger.debug('Log entry stored', { deviceId, level: payload.level });

    } catch (error) {
      logger.error('Error handling logs:', { topic, error: error.message });
    }
  }

  async handleConfigResponse(topic, payload) {
    try {
      const topicParts = topic.split('/');
      const deviceId = topicParts[2];

      // Update device configuration
      await this.db.collection(this.collections.devices).updateOne(
        { device_id: deviceId },
        {
          $set: {
            config: payload.config,
            config_version: payload.version,
            config_updated_at: new Date(payload.timestamp || Date.now()),
            updated_at: new Date()
          }
        }
      );

      logger.info('Device configuration updated', { deviceId, version: payload.version });

    } catch (error) {
      logger.error('Error handling config response:', { topic, error: error.message });
    }
  }

  async handleDiscovery(topic, payload) {
    try {
      const deviceInfo = {
        device_id: payload.device_id,
        device_type: payload.device_type || 'homegrow_client',
        firmware_version: payload.firmware_version,
        hardware_version: payload.hardware_version,
        ip_address: payload.ip_address,
        mac_address: payload.mac_address,
        capabilities: payload.capabilities,
        discovered_at: new Date(),
        status: 'discovered'
      };

      // Upsert device information
      await this.db.collection(this.collections.devices).updateOne(
        { device_id: payload.device_id },
        {
          $setOnInsert: {
            created_at: new Date(),
            name: payload.device_id,
            location: 'Unknown',
            description: 'Auto-discovered device'
          },
          $set: {
            ...deviceInfo,
            updated_at: new Date()
          }
        },
        { upsert: true }
      );

      // Create notification for new device
      const existingDevice = await this.db.collection(this.collections.devices)
        .findOne({ device_id: payload.device_id });
      
      if (!existingDevice) {
        await this.createNotification(
          payload.device_id,
          'discovery',
          'New device discovered',
          deviceInfo
        );
      }

      logger.info('Device discovered', { deviceId: payload.device_id });

    } catch (error) {
      logger.error('Error handling discovery:', { topic, error: error.message });
    }
  }

  async handleProgramUpdate(topic, payload) {
    try {
      const topicParts = topic.split('/');
      const programId = topicParts[2];
      const updateType = topicParts[3]; // status or logs

      if (updateType === 'status') {
        await this.db.collection(this.collections.programInstances).updateOne(
          { program_id: programId },
          {
            $set: {
              status: payload.status,
              current_phase: payload.current_phase,
              phase_progress: payload.phase_progress,
              last_action: payload.last_action,
              updated_at: new Date()
            }
          }
        );
      } else if (updateType === 'logs') {
        await this.db.collection(this.collections.programInstances).updateOne(
          { program_id: programId },
          {
            $push: {
              logs: {
                timestamp: new Date(payload.timestamp || Date.now()),
                level: payload.level,
                message: payload.message,
                data: payload.data
              }
            },
            $set: { updated_at: new Date() }
          }
        );
      }

      logger.debug('Program update processed', { programId, updateType });

    } catch (error) {
      logger.error('Error handling program update:', { topic, error: error.message });
    }
  }

  // Helper methods
  async updateDeviceSensorStatus(deviceId, sensorType, sensorData) {
    const updatePath = `sensors.${sensorType}`;
    await this.db.collection(this.collections.devices).updateOne(
      { device_id: deviceId },
      {
        $set: {
          [`${updatePath}.last_value`]: sensorData.values.calibrated,
          [`${updatePath}.last_raw_value`]: sensorData.values.raw,
          [`${updatePath}.quality`]: sensorData.quality,
          [`${updatePath}.calibration_status`]: sensorData.calibration_status,
          [`${updatePath}.last_update`]: new Date(),
          updated_at: new Date()
        }
      }
    );
  }

  async createNotification(deviceId, type, message, data) {
    const notification = {
      device_id: deviceId,
      type: type,
      message: message,
      data: data,
      read: false,
      created_at: new Date()
    };

    await this.db.collection(this.collections.notifications).insertOne(notification);
    logger.info('Notification created', { deviceId, type, message });
  }
} 