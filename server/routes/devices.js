const Device = require('../models/device');
const beaconClient = require('../services/beacon-client');

async function deviceRoutes(fastify, options) {
  // Get all devices
  fastify.get('/', async (request, reply) => {
    try {
      const devices = await Device.find({}).sort({ created_at: -1 });
      
      return {
        success: true,
        data: devices,
        count: devices.length
      };
    } catch (error) {
      fastify.log.error('Failed to fetch devices:', error);
      reply.code(500);
      return {
        success: false,
        error: 'Failed to fetch devices',
        message: error.message
      };
    }
  });

  // Get device by ID
  fastify.get('/:deviceId', async (request, reply) => {
    try {
      const { deviceId } = request.params;
      const device = await Device.findOne({ device_id: deviceId });
      
      if (!device) {
        reply.code(404);
        return {
          success: false,
          error: 'Device not found',
          message: `Device with ID ${deviceId} not found`
        };
      }
      
      return {
        success: true,
        data: device
      };
    } catch (error) {
      fastify.log.error('Failed to fetch device:', error);
      reply.code(500);
      return {
        success: false,
        error: 'Failed to fetch device',
        message: error.message
      };
    }
  });

  // Create new device
  fastify.post('/', {
    schema: {
      body: {
        type: 'object',
        required: ['device_id'],
        properties: {
          device_id: { type: 'string' },
          name: { type: 'string' },
          location: { type: 'string' },
          description: { type: 'string' },
          configuration: { type: 'object' }
        }
      }
    }
  }, async (request, reply) => {
    try {
      const deviceData = request.body;
      
      // Check if device already exists
      const existingDevice = await Device.findOne({ device_id: deviceData.device_id });
      if (existingDevice) {
        reply.code(409);
        return {
          success: false,
          error: 'Device already exists',
          message: `Device with ID ${deviceData.device_id} already exists`
        };
      }
      
      const device = new Device(deviceData);
      await device.save();
      
      fastify.log.info(`Device created: ${device.device_id}`);
      
      reply.code(201);
      return {
        success: true,
        data: device,
        message: 'Device created successfully'
      };
    } catch (error) {
      fastify.log.error('Failed to create device:', error);
      reply.code(500);
      return {
        success: false,
        error: 'Failed to create device',
        message: error.message
      };
    }
  });

  // Update device
  fastify.put('/:deviceId', {
    schema: {
      body: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          location: { type: 'string' },
          description: { type: 'string' },
          configuration: { type: 'object' },
          status: { type: 'string', enum: ['online', 'offline', 'warning', 'error'] }
        }
      }
    }
  }, async (request, reply) => {
    try {
      const { deviceId } = request.params;
      const updateData = request.body;
      
      const device = await Device.findOneAndUpdate(
        { device_id: deviceId },
        { 
          ...updateData,
          updated_at: new Date()
        },
        { new: true, runValidators: true }
      );
      
      if (!device) {
        reply.code(404);
        return {
          success: false,
          error: 'Device not found',
          message: `Device with ID ${deviceId} not found`
        };
      }
      
      fastify.log.info(`Device updated: ${deviceId}`);
      
      return {
        success: true,
        data: device,
        message: 'Device updated successfully'
      };
    } catch (error) {
      fastify.log.error('Failed to update device:', error);
      reply.code(500);
      return {
        success: false,
        error: 'Failed to update device',
        message: error.message
      };
    }
  });

  // Delete device
  fastify.delete('/:deviceId', async (request, reply) => {
    try {
      const { deviceId } = request.params;
      
      const device = await Device.findOneAndDelete({ device_id: deviceId });
      
      if (!device) {
        reply.code(404);
        return {
          success: false,
          error: 'Device not found',
          message: `Device with ID ${deviceId} not found`
        };
      }
      
      fastify.log.info(`Device deleted: ${deviceId}`);
      
      return {
        success: true,
        message: 'Device deleted successfully'
      };
    } catch (error) {
      fastify.log.error('Failed to delete device:', error);
      reply.code(500);
      return {
        success: false,
        error: 'Failed to delete device',
        message: error.message
      };
    }
  });

  // Discover devices via Beacon
  fastify.post('/discover', async (request, reply) => {
    try {
      fastify.log.info('Starting device discovery...');
      
      const discoveredServices = await beaconClient.discoverServices();
      let newDevices = 0;
      let totalDiscovered = 0;
      
      for (const service of discoveredServices) {
        totalDiscovered++;
        
        // Check if device already exists
        const existingDevice = await Device.findOne({ device_id: service.device_id });
        
        if (!existingDevice) {
          // Create new device from discovered service
          const deviceData = {
            device_id: service.device_id,
            name: service.name || `ESP32-${service.device_id}`,
            location: service.location || 'Unknown',
            ip_address: service.ip,
            port: service.port,
            status: 'online',
            last_seen: new Date(),
            configuration: {
              mqtt: {
                client_id: service.device_id,
                topics: {
                  sensors: `homegrow/devices/${service.device_id}/sensors`,
                  commands: `homegrow/devices/${service.device_id}/commands`,
                  status: `homegrow/devices/${service.device_id}/status`
                }
              },
              ...service.configuration
            }
          };
          
          const device = new Device(deviceData);
          await device.save();
          newDevices++;
          
          fastify.log.info(`New device discovered and registered: ${service.device_id}`);
        } else {
          // Update existing device status
          await Device.updateOne(
            { device_id: service.device_id },
            { 
              status: 'online',
              last_seen: new Date(),
              ip_address: service.ip,
              port: service.port
            }
          );
          
          fastify.log.info(`Existing device updated: ${service.device_id}`);
        }
      }
      
      return {
        success: true,
        data: {
          discovered: totalDiscovered,
          new_devices: newDevices,
          existing_devices: totalDiscovered - newDevices
        },
        message: `Discovery completed. Found ${totalDiscovered} devices, ${newDevices} new.`
      };
    } catch (error) {
      fastify.log.error('Device discovery failed:', error);
      reply.code(500);
      return {
        success: false,
        error: 'Device discovery failed',
        message: error.message
      };
    }
  });

  // Get device status
  fastify.get('/:deviceId/status', async (request, reply) => {
    try {
      const { deviceId } = request.params;
      
      const device = await Device.findOne({ device_id: deviceId });
      if (!device) {
        reply.code(404);
        return {
          success: false,
          error: 'Device not found'
        };
      }
      
      // Calculate uptime and other metrics
      const now = new Date();
      const lastSeen = device.last_seen || device.created_at;
      const timeDiff = now - lastSeen;
      const isOnline = timeDiff < 60000; // Consider offline if no update in 1 minute
      
      const status = {
        device_id: deviceId,
        status: isOnline ? device.status : 'offline',
        last_seen: lastSeen,
        uptime_minutes: Math.floor(timeDiff / 60000),
        ip_address: device.ip_address,
        port: device.port,
        configuration_valid: !!device.configuration
      };
      
      return {
        success: true,
        data: status
      };
    } catch (error) {
      fastify.log.error('Failed to get device status:', error);
      reply.code(500);
      return {
        success: false,
        error: 'Failed to get device status',
        message: error.message
      };
    }
  });

  // Update device configuration
  fastify.put('/:deviceId/configuration', {
    schema: {
      body: {
        type: 'object',
        properties: {
          sensors: { type: 'object' },
          actuators: { type: 'object' },
          safety: { type: 'object' },
          mqtt: { type: 'object' },
          wifi: { type: 'object' }
        }
      }
    }
  }, async (request, reply) => {
    try {
      const { deviceId } = request.params;
      const configUpdate = request.body;
      
      const device = await Device.findOneAndUpdate(
        { device_id: deviceId },
        { 
          $set: {
            'configuration': configUpdate,
            'updated_at': new Date()
          }
        },
        { new: true, runValidators: true }
      );
      
      if (!device) {
        reply.code(404);
        return {
          success: false,
          error: 'Device not found'
        };
      }
      
      fastify.log.info(`Device configuration updated: ${deviceId}`);
      
      return {
        success: true,
        data: device.configuration,
        message: 'Configuration updated successfully'
      };
    } catch (error) {
      fastify.log.error('Failed to update device configuration:', error);
      reply.code(500);
      return {
        success: false,
        error: 'Failed to update configuration',
        message: error.message
      };
    }
  });
}

module.exports = deviceRoutes; 