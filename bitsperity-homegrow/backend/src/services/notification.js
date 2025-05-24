export class NotificationService {
  constructor(db, logger) {
    this.db = db;
    this.logger = logger;
    this.isRunning = false;
    this.alertCheckInterval = null;
    this.notificationChannels = new Map();
  }

  async start() {
    try {
      this.logger.info('Starting Notification Service...');
      
      // Initialize notification channels
      await this.initializeChannels();
      
      // Start periodic alert checking
      this.isRunning = true;
      this.alertCheckInterval = setInterval(() => {
        this.processAlerts();
      }, 30000); // Check every 30 seconds
      
      this.logger.info('Notification Service started successfully');
    } catch (error) {
      this.logger.error('Failed to start Notification Service:', error);
      throw error;
    }
  }

  async stop() {
    this.logger.info('Stopping Notification Service...');
    this.isRunning = false;
    
    if (this.alertCheckInterval) {
      clearInterval(this.alertCheckInterval);
      this.alertCheckInterval = null;
    }
    
    this.logger.info('Notification Service stopped');
  }

  async initializeChannels() {
    // Initialize different notification channels
    this.notificationChannels.set('database', {
      name: 'Database Storage',
      enabled: true,
      send: this.sendDatabaseNotification.bind(this)
    });

    this.notificationChannels.set('websocket', {
      name: 'WebSocket Real-time',
      enabled: true,
      send: this.sendWebSocketNotification.bind(this)
    });

    // Future channels: email, webhook, push notifications
    this.notificationChannels.set('webhook', {
      name: 'Webhook',
      enabled: false,
      send: this.sendWebhookNotification.bind(this)
    });

    this.logger.debug(`Initialized ${this.notificationChannels.size} notification channels`);
  }

  async processAlerts() {
    if (!this.isRunning) return;

    try {
      // Get current alerts from latest readings
      const alerts = await this.db.collection('latest_readings').find({
        status: { $in: ['alert', 'warning'] }
      }).toArray();

      for (const alert of alerts) {
        await this.processAlert(alert);
      }

    } catch (error) {
      this.logger.error('Error processing alerts:', error);
    }
  }

  async processAlert(alertData) {
    try {
      const alertId = `${alertData.deviceId}_${alertData.sensorType}`;
      
      // Check if we've already processed this alert recently
      const recentAlert = await this.db.collection('notifications').findOne({
        alertId,
        timestamp: { $gte: new Date(Date.now() - 15 * 60 * 1000) }, // 15 minutes ago
        status: alertData.status
      });

      if (recentAlert) {
        return; // Don't spam notifications
      }

      // Get device information
      const device = await this.db.collection('devices').findOne({
        deviceId: alertData.deviceId
      });

      // Create notification
      const notification = {
        alertId,
        type: 'sensor_alert',
        severity: alertData.status,
        deviceId: alertData.deviceId,
        deviceName: device?.name || `Device ${alertData.deviceId}`,
        sensorType: alertData.sensorType,
        value: alertData.value,
        unit: alertData.unit,
        message: this.generateAlertMessage(alertData, device),
        timestamp: new Date(),
        acknowledged: false,
        channels: []
      };

      // Send notification through all enabled channels
      for (const [channelName, channel] of this.notificationChannels) {
        if (channel.enabled) {
          try {
            await channel.send(notification);
            notification.channels.push(channelName);
          } catch (error) {
            this.logger.error(`Failed to send notification via ${channelName}:`, error);
          }
        }
      }

      this.logger.info(`Processed alert: ${notification.message}`);

    } catch (error) {
      this.logger.error('Error processing individual alert:', error);
    }
  }

  generateAlertMessage(alertData, device) {
    const sensorNames = {
      'ph': 'pH-Wert',
      'temperature': 'Temperatur',
      'humidity': 'Luftfeuchtigkeit',
      'ec': 'Leitfähigkeit',
      'water_level': 'Wasserstand',
      'light_intensity': 'Lichtintensität'
    };

    const sensorName = sensorNames[alertData.sensorType] || alertData.sensorType;
    const deviceName = device?.name || `Gerät ${alertData.deviceId}`;
    const unitStr = alertData.unit ? ` ${alertData.unit}` : '';
    
    if (alertData.status === 'alert') {
      return `🚨 Kritischer Alarm: ${sensorName} bei ${deviceName} ist ${alertData.value}${unitStr}`;
    } else if (alertData.status === 'warning') {
      return `⚠️ Warnung: ${sensorName} bei ${deviceName} ist ${alertData.value}${unitStr}`;
    }
    
    return `ℹ️ ${sensorName} bei ${deviceName}: ${alertData.value}${unitStr}`;
  }

  async sendDatabaseNotification(notification) {
    try {
      await this.db.collection('notifications').insertOne(notification);
      this.logger.debug(`Notification stored in database: ${notification.alertId}`);
    } catch (error) {
      this.logger.error('Error storing notification in database:', error);
      throw error;
    }
  }

  async sendWebSocketNotification(notification) {
    try {
      // This would integrate with the WebSocket service to emit real-time notifications
      // For now, just log it
      this.logger.debug(`WebSocket notification: ${notification.message}`);
      
      // In a real implementation, this would emit to all connected clients:
      // this.webSocketService.emit('notification', notification);
    } catch (error) {
      this.logger.error('Error sending WebSocket notification:', error);
      throw error;
    }
  }

  async sendWebhookNotification(notification) {
    try {
      // Get webhook configuration
      const webhookConfig = await this.getWebhookConfig();
      
      if (!webhookConfig || !webhookConfig.url) {
        return;
      }

      const payload = {
        type: notification.type,
        severity: notification.severity,
        message: notification.message,
        device: {
          id: notification.deviceId,
          name: notification.deviceName
        },
        sensor: {
          type: notification.sensorType,
          value: notification.value,
          unit: notification.unit
        },
        timestamp: notification.timestamp
      };

      // In a real implementation, this would make an HTTP request
      this.logger.debug(`Webhook notification payload:`, payload);
      
    } catch (error) {
      this.logger.error('Error sending webhook notification:', error);
      throw error;
    }
  }

  async getWebhookConfig() {
    try {
      return await this.db.collection('settings').findOne({
        key: 'webhook_notifications'
      });
    } catch (error) {
      this.logger.error('Error getting webhook config:', error);
      return null;
    }
  }

  // Public API methods

  async getNotifications(options = {}) {
    try {
      const {
        limit = 50,
        offset = 0,
        severity = null,
        acknowledged = null,
        deviceId = null
      } = options;

      const query = {};
      
      if (severity) {
        query.severity = severity;
      }
      
      if (acknowledged !== null) {
        query.acknowledged = acknowledged;
      }
      
      if (deviceId) {
        query.deviceId = deviceId;
      }

      const notifications = await this.db.collection('notifications')
        .find(query)
        .sort({ timestamp: -1 })
        .limit(limit)
        .skip(offset)
        .toArray();

      const total = await this.db.collection('notifications').countDocuments(query);

      return {
        notifications: notifications.map(n => ({
          id: n._id.toString(),
          type: n.type,
          severity: n.severity,
          message: n.message,
          deviceId: n.deviceId,
          deviceName: n.deviceName,
          timestamp: n.timestamp,
          acknowledged: n.acknowledged,
          channels: n.channels
        })),
        total,
        hasMore: (offset + limit) < total
      };

    } catch (error) {
      this.logger.error('Error getting notifications:', error);
      throw error;
    }
  }

  async acknowledgeNotification(notificationId) {
    try {
      const result = await this.db.collection('notifications').updateOne(
        { _id: new this.db.constructor.ObjectId(notificationId) },
        {
          $set: {
            acknowledged: true,
            acknowledgedAt: new Date()
          }
        }
      );

      if (result.matchedCount === 0) {
        throw new Error('Notification not found');
      }

      this.logger.debug(`Notification acknowledged: ${notificationId}`);
      return true;

    } catch (error) {
      this.logger.error('Error acknowledging notification:', error);
      throw error;
    }
  }

  async acknowledgeAllNotifications(deviceId = null) {
    try {
      const query = { acknowledged: false };
      
      if (deviceId) {
        query.deviceId = deviceId;
      }

      const result = await this.db.collection('notifications').updateMany(
        query,
        {
          $set: {
            acknowledged: true,
            acknowledgedAt: new Date()
          }
        }
      );

      this.logger.info(`Acknowledged ${result.modifiedCount} notifications`);
      return result.modifiedCount;

    } catch (error) {
      this.logger.error('Error acknowledging all notifications:', error);
      throw error;
    }
  }

  async deleteOldNotifications(daysSinceCreation = 30) {
    try {
      const cutoffDate = new Date(Date.now() - daysSinceCreation * 24 * 60 * 60 * 1000);
      
      const result = await this.db.collection('notifications').deleteMany({
        timestamp: { $lt: cutoffDate },
        acknowledged: true
      });

      if (result.deletedCount > 0) {
        this.logger.info(`Deleted ${result.deletedCount} old notifications`);
      }

      return result.deletedCount;

    } catch (error) {
      this.logger.error('Error deleting old notifications:', error);
      return 0;
    }
  }

  async getNotificationStats() {
    try {
      const stats = await this.db.collection('notifications').aggregate([
        {
          $group: {
            _id: null,
            total: { $sum: 1 },
            unacknowledged: {
              $sum: {
                $cond: [{ $eq: ['$acknowledged', false] }, 1, 0]
              }
            },
            alerts: {
              $sum: {
                $cond: [{ $eq: ['$severity', 'alert'] }, 1, 0]
              }
            },
            warnings: {
              $sum: {
                $cond: [{ $eq: ['$severity', 'warning'] }, 1, 0]
              }
            }
          }
        }
      ]).toArray();

      const result = stats[0] || { 
        total: 0, 
        unacknowledged: 0, 
        alerts: 0, 
        warnings: 0 
      };
      
      return {
        ...result,
        _id: undefined
      };

    } catch (error) {
      this.logger.error('Error getting notification stats:', error);
      return { total: 0, unacknowledged: 0, alerts: 0, warnings: 0 };
    }
  }

  // Configure notification channels
  async configureChannel(channelName, config) {
    try {
      const channel = this.notificationChannels.get(channelName);
      
      if (!channel) {
        throw new Error(`Unknown notification channel: ${channelName}`);
      }

      // Update channel configuration
      Object.assign(channel, config);
      
      // Store configuration in database
      await this.db.collection('settings').replaceOne(
        { key: `notification_channel_${channelName}` },
        {
          key: `notification_channel_${channelName}`,
          value: config,
          updatedAt: new Date()
        },
        { upsert: true }
      );

      this.logger.info(`Configured notification channel: ${channelName}`);
      return true;

    } catch (error) {
      this.logger.error(`Error configuring channel ${channelName}:`, error);
      throw error;
    }
  }
} 