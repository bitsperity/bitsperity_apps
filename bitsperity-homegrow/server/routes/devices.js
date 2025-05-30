import express from 'express';

class DeviceRoutes {
  constructor(deviceModel, mqttBridge, beaconClient) {
    this.deviceModel = deviceModel;
    this.mqttBridge = mqttBridge;
    this.beaconClient = beaconClient;
    this.router = express.Router();
    this.setupRoutes();
  }

  setupRoutes() {
    // Get all devices
    this.router.get('/', async (req, res) => {
      try {
        const devices = await this.deviceModel.findAll();
        
        // Enrich with beacon discovery data
        const discoveredDevices = this.beaconClient.getDiscoveredDevices();
        const enrichedDevices = devices.map(device => {
          const discovered = discoveredDevices.find(d => d.device_id === device.device_id);
          return {
            ...device,
            beacon_status: discovered ? 'discovered' : 'not_discovered',
            beacon_last_seen: discovered?.last_seen || null
          };
        });

        return {
          success: true,
          data: enrichedDevices,
          count: enrichedDevices.length
        };
      } catch (error) {
        console.error('Error getting devices:', error);
        res.status(500);
        return {
          success: false,
          error: error.message
        };
      }
    });

    // Get device by ID
    this.router.get('/:deviceId', async (req, res) => {
      try {
        const device = await this.deviceModel.findByDeviceId(req.params.deviceId);
        
        if (!device) {
          return res.status(404).json({
            success: false,
            error: 'Device not found'
          });
        }

        // Add beacon info if available
        const beaconDevice = this.beaconClient.getDeviceByDeviceId(req.params.deviceId);
        if (beaconDevice) {
          device.beacon_info = beaconDevice;
        }

        return {
          success: true,
          data: device
        };
      } catch (error) {
        console.error('Error getting device:', error);
        res.status(500);
        return {
          success: false,
          error: error.message
        };
      }
    });

    // Create new device
    this.router.post('/', async (req, res) => {
      try {
        const deviceData = req.body;
        
        // Validate required fields
        if (!deviceData.device_id) {
          return res.status(400).json({
            success: false,
            error: 'device_id is required'
          });
        }

        // Check if device already exists
        const existing = await this.deviceModel.findByDeviceId(deviceData.device_id);
        if (existing) {
          return res.status(409).json({
            success: false,
            error: 'Device already exists'
          });
        }

        const device = await this.deviceModel.create(deviceData);
        
        // Subscribe to device MQTT topics
        await this.mqttBridge.subscribeToDevice(device.device_id);

        console.log(`✅ Device created: ${device.device_id}`);

        return {
          success: true,
          data: device
        };
      } catch (error) {
        console.error('Error creating device:', error);
        res.status(500);
        return {
          success: false,
          error: error.message
        };
      }
    });

    // Update device configuration
    this.router.put('/:deviceId/config', async (req, res) => {
      try {
        const deviceId = req.params.deviceId;
        const configUpdate = req.body;

        const device = await this.deviceModel.findByDeviceId(deviceId);
        if (!device) {
          return res.status(404).json({
            success: false,
            error: 'Device not found'
          });
        }

        await this.deviceModel.updateConfig(deviceId, configUpdate);

        // Send config update command to device
        const command = {
          command_id: `config_${Date.now()}`,
          command: 'update_config',
          params: configUpdate,
          timestamp: new Date().toISOString()
        };

        try {
          await this.mqttBridge.publishCommand(deviceId, command);
          console.log(`⚙️ Config update sent to ${deviceId}`);
        } catch (mqttError) {
          console.warn(`⚠️ Failed to send config to device ${deviceId}:`, mqttError.message);
        }

        return {
          success: true,
          message: 'Configuration updated'
        };
      } catch (error) {
        console.error('Error updating device config:', error);
        res.status(500);
        return {
          success: false,
          error: error.message
        };
      }
    });

    // Update device info
    this.router.put('/:deviceId', async (req, res) => {
      try {
        const deviceId = req.params.deviceId;
        const updates = req.body;

        const device = await this.deviceModel.findByDeviceId(deviceId);
        if (!device) {
          return res.status(404).json({
            success: false,
            error: 'Device not found'
          });
        }

        // Update allowed fields
        const allowedFields = ['name', 'location', 'description'];
        const updateData = {};
        
        allowedFields.forEach(field => {
          if (updates[field] !== undefined) {
            updateData[field] = updates[field];
          }
        });

        if (Object.keys(updateData).length === 0) {
          return res.status(400).json({
            success: false,
            error: 'No valid fields to update'
          });
        }

        updateData.updated_at = new Date();

        await this.deviceModel.collection.updateOne(
          { device_id: deviceId },
          { $set: updateData }
        );

        return {
          success: true,
          message: 'Device updated successfully'
        };
      } catch (error) {
        console.error('Error updating device:', error);
        res.status(500);
        return {
          success: false,
          error: error.message
        };
      }
    });

    // Delete device
    this.router.delete('/:deviceId', async (req, res) => {
      try {
        const deviceId = req.params.deviceId;
        
        const result = await this.deviceModel.delete(deviceId);

        if (result.deletedCount === 0) {
          return res.status(404).json({
            success: false,
            error: 'Device not found'
          });
        }

        // Unsubscribe from MQTT topics
        await this.mqttBridge.unsubscribeFromDevice(deviceId);

        console.log(`🗑️ Device deleted: ${deviceId}`);

        return {
          success: true,
          message: 'Device deleted'
        };
      } catch (error) {
        console.error('Error deleting device:', error);
        res.status(500);
        return {
          success: false,
          error: error.message
        };
      }
    });

    // Discover devices via Beacon
    this.router.post('/discover', async (req, res) => {
      try {
        const discoveredDevices = await this.beaconClient.refreshDiscovery();
        
        // Auto-register discovered devices
        const newDevices = [];
        for (const discovered of discoveredDevices) {
          const existing = await this.deviceModel.findByDeviceId(discovered.device_id);
          if (!existing) {
            const deviceData = {
              device_id: discovered.device_id,
              name: discovered.name,
              type: 'homegrow-client'
            };
            
            const device = await this.deviceModel.create(deviceData);
            await this.deviceModel.updateBeaconInfo(discovered.device_id, discovered);
            await this.mqttBridge.subscribeToDevice(discovered.device_id);
            
            newDevices.push(device);
            console.log(`🆕 Auto-registered device: ${discovered.device_id}`);
          }
        }

        return {
          success: true,
          discovered: discoveredDevices.length,
          new_devices: newDevices.length,
          data: newDevices
        };
      } catch (error) {
        console.error('Error discovering devices:', error);
        res.status(500);
        return {
          success: false,
          error: error.message
        };
      }
    });

    // Send command to device
    this.router.post('/:deviceId/commands', async (req, res) => {
      try {
        const deviceId = req.params.deviceId;
        const { command, params = {} } = req.body;

        if (!command) {
          return res.status(400).json({
            success: false,
            error: 'Command is required'
          });
        }

        const device = await this.deviceModel.findByDeviceId(deviceId);
        if (!device) {
          return res.status(404).json({
            success: false,
            error: 'Device not found'
          });
        }

        const commandData = {
          command_id: `cmd_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          command: command,
          params: params,
          timestamp: new Date().toISOString()
        };

        await this.mqttBridge.publishCommand(deviceId, commandData);

        return {
          success: true,
          command_id: commandData.command_id,
          message: 'Command sent successfully'
        };
      } catch (error) {
        console.error('Error sending command:', error);
        res.status(500);
        return {
          success: false,
          error: error.message
        };
      }
    });

    // Emergency stop
    this.router.post('/:deviceId/emergency-stop', async (req, res) => {
      try {
        const deviceId = req.params.deviceId;

        const device = await this.deviceModel.findByDeviceId(deviceId);
        if (!device) {
          return res.status(404).json({
            success: false,
            error: 'Device not found'
          });
        }

        await this.mqttBridge.publishEmergencyStop(deviceId);

        console.log(`🚨 Emergency stop sent to ${deviceId}`);

        return {
          success: true,
          message: 'Emergency stop command sent'
        };
      } catch (error) {
        console.error('Error sending emergency stop:', error);
        res.status(500);
        return {
          success: false,
          error: error.message
        };
      }
    });

    // Get device statistics
    this.router.get('/:deviceId/stats', async (req, res) => {
      try {
        const deviceId = req.params.deviceId;
        
        const device = await this.deviceModel.findByDeviceId(deviceId);
        if (!device) {
          return res.status(404).json({
            success: false,
            error: 'Device not found'
          });
        }

        return {
          success: true,
          data: device.stats
        };
      } catch (error) {
        console.error('Error getting device stats:', error);
        res.status(500);
        return {
          success: false,
          error: error.message
        };
      }
    });
  }

  getRouter() {
    return this.router;
  }
}

export default DeviceRoutes; 