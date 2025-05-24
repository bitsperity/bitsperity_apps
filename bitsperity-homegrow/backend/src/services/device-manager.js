export class DeviceManager {
  constructor(db, logger) {
    this.db = db;
    this.logger = logger;
    this.deviceTimeouts = new Map(); // Track device last seen times
    this.offlineCheckInterval = null;
  }

  async start() {
    try {
      this.logger.info('Starting Device Manager...');
      
      // Start periodic offline device checking
      this.offlineCheckInterval = setInterval(() => {
        this.checkOfflineDevices();
      }, 30000); // Check every 30 seconds
      
      this.logger.info('Device Manager started successfully');
    } catch (error) {
      this.logger.error('Failed to start Device Manager:', error);
      throw error;
    }
  }

  async stop() {
    this.logger.info('Stopping Device Manager...');
    
    if (this.offlineCheckInterval) {
      clearInterval(this.offlineCheckInterval);
      this.offlineCheckInterval = null;
    }
    
    this.logger.info('Device Manager stopped');
  }

  async checkOfflineDevices() {
    try {
      const offlineThreshold = new Date(Date.now() - 5 * 60 * 1000); // 5 minutes ago
      
      // Find devices that haven't been seen recently
      const staleDevices = await this.db.collection('devices').find({
        lastSeen: { $lt: offlineThreshold },
        status: { $ne: 'offline' }
      }).toArray();

      for (const device of staleDevices) {
        await this.markDeviceOffline(device.deviceId);
      }

      if (staleDevices.length > 0) {
        this.logger.info(`Marked ${staleDevices.length} devices as offline`);
      }

    } catch (error) {
      this.logger.error('Error checking offline devices:', error);
    }
  }

  async markDeviceOffline(deviceId) {
    try {
      await this.db.collection('devices').updateOne(
        { deviceId },
        {
          $set: {
            status: 'offline',
            lastStatusChange: new Date()
          }
        }
      );

      this.logger.debug(`Device ${deviceId} marked as offline`);
      
      // Could emit real-time update here
      this.emitDeviceStatusChange(deviceId, 'offline');

    } catch (error) {
      this.logger.error(`Error marking device ${deviceId} as offline:`, error);
    }
  }

  async markDeviceOnline(deviceId) {
    try {
      const result = await this.db.collection('devices').updateOne(
        { deviceId },
        {
          $set: {
            status: 'online',
            lastSeen: new Date(),
            lastStatusChange: new Date()
          }
        }
      );

      if (result.matchedCount > 0) {
        this.logger.debug(`Device ${deviceId} marked as online`);
        this.emitDeviceStatusChange(deviceId, 'online');
      }

    } catch (error) {
      this.logger.error(`Error marking device ${deviceId} as online:`, error);
    }
  }

  async registerDevice(deviceInfo) {
    try {
      const { deviceId, name, type, location, capabilities } = deviceInfo;
      
      const deviceData = {
        deviceId,
        name: name || `Device ${deviceId}`,
        type: type || 'unknown',
        location: location || 'Unknown',
        capabilities: capabilities || [],
        status: 'online',
        firstSeen: new Date(),
        lastSeen: new Date(),
        lastStatusChange: new Date(),
        metadata: {}
      };

      await this.db.collection('devices').replaceOne(
        { deviceId },
        deviceData,
        { upsert: true }
      );

      this.logger.info(`Device registered: ${deviceId} (${name})`);
      return deviceData;

    } catch (error) {
      this.logger.error(`Error registering device ${deviceInfo.deviceId}:`, error);
      throw error;
    }
  }

  async updateDeviceHeartbeat(deviceId, metadata = {}) {
    try {
      await this.db.collection('devices').updateOne(
        { deviceId },
        {
          $set: {
            lastSeen: new Date(),
            metadata: { ...metadata, lastHeartbeat: new Date() }
          },
          $setOnInsert: {
            deviceId,
            status: 'online',
            firstSeen: new Date()
          }
        },
        { upsert: true }
      );

      // Mark as online if it was offline
      const device = await this.db.collection('devices').findOne({ deviceId });
      if (device && device.status === 'offline') {
        await this.markDeviceOnline(deviceId);
      }

    } catch (error) {
      this.logger.error(`Error updating heartbeat for device ${deviceId}:`, error);
    }
  }

  async getDeviceStats() {
    try {
      const stats = await this.db.collection('devices').aggregate([
        {
          $group: {
            _id: null,
            total: { $sum: 1 },
            online: {
              $sum: {
                $cond: [{ $eq: ['$status', 'online'] }, 1, 0]
              }
            },
            offline: {
              $sum: {
                $cond: [{ $eq: ['$status', 'offline'] }, 1, 0]
              }
            }
          }
        }
      ]).toArray();

      const result = stats[0] || { total: 0, online: 0, offline: 0 };
      
      return {
        ...result,
        _id: undefined // Remove MongoDB _id field
      };

    } catch (error) {
      this.logger.error('Error getting device stats:', error);
      return { total: 0, online: 0, offline: 0 };
    }
  }

  async getDevicesByType() {
    try {
      const devicesByType = await this.db.collection('devices').aggregate([
        {
          $group: {
            _id: '$type',
            count: { $sum: 1 },
            online: {
              $sum: {
                $cond: [{ $eq: ['$status', 'online'] }, 1, 0]
              }
            }
          }
        },
        {
          $sort: { count: -1 }
        }
      ]).toArray();

      return devicesByType.map(item => ({
        type: item._id,
        count: item.count,
        online: item.online,
        offline: item.count - item.online
      }));

    } catch (error) {
      this.logger.error('Error getting devices by type:', error);
      return [];
    }
  }

  async getRecentlySeenDevices(limit = 10) {
    try {
      return await this.db.collection('devices')
        .find({})
        .sort({ lastSeen: -1 })
        .limit(limit)
        .toArray();

    } catch (error) {
      this.logger.error('Error getting recently seen devices:', error);
      return [];
    }
  }

  async removeStaleDevices(daysSinceLastSeen = 30) {
    try {
      const cutoffDate = new Date(Date.now() - daysSinceLastSeen * 24 * 60 * 60 * 1000);
      
      const result = await this.db.collection('devices').deleteMany({
        lastSeen: { $lt: cutoffDate },
        status: 'offline'
      });

      if (result.deletedCount > 0) {
        this.logger.info(`Removed ${result.deletedCount} stale devices`);
      }

      return result.deletedCount;

    } catch (error) {
      this.logger.error('Error removing stale devices:', error);
      return 0;
    }
  }

  // Emit device status changes (would integrate with WebSocket service)
  emitDeviceStatusChange(deviceId, status) {
    // This would emit real-time updates to connected clients
    this.logger.debug(`Device status change: ${deviceId} -> ${status}`);
  }

  // Get device capabilities for automation rules
  async getDeviceCapabilities(deviceId) {
    try {
      const device = await this.db.collection('devices').findOne(
        { deviceId },
        { projection: { capabilities: 1, type: 1 } }
      );

      if (!device) {
        return null;
      }

      return {
        deviceId,
        type: device.type,
        capabilities: device.capabilities || [],
        supportedCommands: this.getSupportedCommands(device.type, device.capabilities)
      };

    } catch (error) {
      this.logger.error(`Error getting capabilities for device ${deviceId}:`, error);
      return null;
    }
  }

  getSupportedCommands(deviceType, capabilities = []) {
    // Define commands based on device type and capabilities
    const commandMap = {
      'hydroponic_controller': [
        'water_pump',
        'nutrient_pump_1', 
        'nutrient_pump_2',
        'air_pump',
        'ph_adjustment'
      ],
      'lighting_controller': [
        'led_strip',
        'set_brightness',
        'set_color',
        'light_schedule'
      ],
      'climate_controller': [
        'fan',
        'heater',
        'humidity_control',
        'ventilation'
      ],
      'sensor_node': [
        'calibrate_sensors',
        'reading_interval',
        'alert_thresholds'
      ]
    };

    const baseCommands = commandMap[deviceType] || [];
    
    // Add capability-specific commands
    const capabilityCommands = capabilities.flatMap(cap => {
      switch (cap) {
        case 'pump_control':
          return ['pump_on', 'pump_off', 'pump_duration'];
        case 'led_control':
          return ['led_on', 'led_off', 'led_brightness'];
        case 'sensor_calibration':
          return ['calibrate_ph', 'calibrate_ec', 'calibrate_temp'];
        default:
          return [];
      }
    });

    return [...new Set([...baseCommands, ...capabilityCommands])];
  }
} 