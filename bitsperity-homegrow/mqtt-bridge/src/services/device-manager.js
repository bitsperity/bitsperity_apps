import { createLogger } from '../utils/logger.js';

const logger = createLogger('device-manager');

export class DeviceManager {
  constructor(db, config) {
    this.db = db;
    this.config = config;
    this.collections = config.mongodb.collections;
    this.deviceTimeouts = new Map();
    this.offlineCheckInterval = null;
  }

  async start() {
    // Start periodic offline device check
    this.offlineCheckInterval = setInterval(
      () => this.checkOfflineDevices(),
      60000 // Check every minute
    );
    
    logger.info('Device manager started');
  }

  async stop() {
    if (this.offlineCheckInterval) {
      clearInterval(this.offlineCheckInterval);
    }
    logger.info('Device manager stopped');
  }

  async updateLastSeen(deviceId) {
    try {
      const now = new Date();
      
      await this.db.collection(this.collections.devices).updateOne(
        { device_id: deviceId },
        {
          $set: {
            last_seen: now,
            status: 'online',
            updated_at: now
          }
        },
        { upsert: true }
      );

      // Clear any existing timeout for this device
      if (this.deviceTimeouts.has(deviceId)) {
        clearTimeout(this.deviceTimeouts.get(deviceId));
      }

      // Set new timeout to mark device as offline if no heartbeat received
      const timeout = setTimeout(() => {
        this.markDeviceOffline(deviceId);
      }, 300000); // 5 minutes timeout

      this.deviceTimeouts.set(deviceId, timeout);

    } catch (error) {
      logger.error('Error updating device last seen:', { deviceId, error: error.message });
    }
  }

  async markDeviceOffline(deviceId) {
    try {
      await this.db.collection(this.collections.devices).updateOne(
        { device_id: deviceId },
        {
          $set: {
            status: 'offline',
            updated_at: new Date()
          }
        }
      );

      // Create notification for offline device
      await this.createNotification(
        deviceId,
        'device_offline',
        `Device ${deviceId} went offline`,
        { last_seen: new Date() }
      );

      logger.warn('Device marked as offline', { deviceId });

    } catch (error) {
      logger.error('Error marking device offline:', { deviceId, error: error.message });
    }
  }

  async checkOfflineDevices() {
    try {
      const fiveMinutesAgo = new Date(Date.now() - 300000);
      
      // Find devices that haven't been seen in 5 minutes but are still marked as online
      const staleDevices = await this.db.collection(this.collections.devices)
        .find({
          status: 'online',
          last_seen: { $lt: fiveMinutesAgo }
        })
        .toArray();

      for (const device of staleDevices) {
        await this.markDeviceOffline(device.device_id);
      }

      if (staleDevices.length > 0) {
        logger.info('Marked stale devices as offline', { count: staleDevices.length });
      }

    } catch (error) {
      logger.error('Error checking offline devices:', error);
    }
  }

  async getDeviceStatus(deviceId) {
    try {
      const device = await this.db.collection(this.collections.devices)
        .findOne({ device_id: deviceId });
      
      return device ? device.status : 'unknown';
    } catch (error) {
      logger.error('Error getting device status:', { deviceId, error: error.message });
      return 'unknown';
    }
  }

  async getAllDevices() {
    try {
      return await this.db.collection(this.collections.devices)
        .find({})
        .sort({ last_seen: -1 })
        .toArray();
    } catch (error) {
      logger.error('Error getting all devices:', error);
      return [];
    }
  }

  async createNotification(deviceId, type, message, data) {
    try {
      const notification = {
        device_id: deviceId,
        type: type,
        message: message,
        data: data,
        read: false,
        created_at: new Date()
      };

      await this.db.collection(this.collections.notifications).insertOne(notification);
      logger.debug('Notification created', { deviceId, type, message });

    } catch (error) {
      logger.error('Error creating notification:', { deviceId, type, error: error.message });
    }
  }
} 