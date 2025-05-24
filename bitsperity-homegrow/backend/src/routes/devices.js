import { z } from 'zod';

// Validation schemas
const DeviceSchema = z.object({
  name: z.string().min(1).max(100),
  type: z.string().min(1).max(50),
  location: z.string().optional(),
  description: z.string().optional(),
  config: z.object({}).optional()
});

const CommandSchema = z.object({
  command: z.string().min(1),
  params: z.object({}).optional()
});

export default async function deviceRoutes(fastify, options) {
  
  // Get all devices
  fastify.get('/', {
    // preHandler: [fastify.authenticate] // Temporär deaktiviert für Tests
  }, async (request, reply) => {
    try {
      // Finde alle Geräte basierend auf MQTT-Aktivität
      const devices = await fastify.db.collection('devices').find({}).toArray();
      
      // Erweitere mit Online-Status
      const devicesWithStatus = await Promise.all(devices.map(async (device) => {
        // Prüfe letzte Sensor-Daten (letzten 2 Minuten = online, use latest_readings for current status)
        const recentSensorData = await fastify.db.collection('latest_readings').findOne(
          { 
            deviceId: device.deviceId,
            receivedAt: { $gte: new Date(Date.now() - 2 * 60 * 1000) }
          },
          { sort: { receivedAt: -1 } }
        );
        
        return {
          ...device,
          status: recentSensorData ? 'online' : 'offline',
          lastSeen: recentSensorData?.receivedAt || device.lastSeen
        };
      }));
      
      return reply.send({
        success: true,
        data: {
          devices: devicesWithStatus,
          total: devicesWithStatus.length,
          online: devicesWithStatus.filter(d => d.status === 'online').length
        }
      });
      
    } catch (error) {
      fastify.log.error('Fehler beim Abrufen der Geräte:', error);
      return reply.status(500).send({
        success: false,
        error: 'Fehler beim Laden der Geräte'
      });
    }
  });

  // Get single device
  fastify.get('/:deviceId', {
    // preHandler: [fastify.authenticate] // Temporär deaktiviert
  }, async (request, reply) => {
    try {
      const { deviceId } = request.params;
      
      const device = await fastify.db.collection('devices').findOne({ deviceId });
      if (!device) {
        return reply.status(404).send({
          success: false,
          error: 'Gerät nicht gefunden'
        });
      }

      // Hole aktuelle Sensor-Werte
      const sensorData = {};
      for (const sensorType of fastify.mqttBridge.sensorTypes) {
        const latestReading = await fastify.db.collection('sensor_data').findOne(
          { deviceId, sensorType },
          { sort: { timestamp: -1 } }
        );
        if (latestReading) {
          sensorData[sensorType] = latestReading;
        }
      }

      // Hole Pumpen-Status (letzte Kommandos)
      const pumpStatus = {};
      for (const pumpType of fastify.mqttBridge.pumpTypes) {
        const lastCommand = await fastify.db.collection('device_commands').findOne(
          { deviceId, 'command.type': pumpType },
          { sort: { timestamp: -1 } }
        );
        pumpStatus[pumpType] = {
          lastActivated: lastCommand?.timestamp || null,
          lastDuration: lastCommand?.command?.duration || null
        };
      }

      return reply.send({
        success: true,
        data: {
          ...device,
          sensors: sensorData,
          pumps: pumpStatus,
          capabilities: {
            sensors: fastify.mqttBridge.sensorTypes,
            pumps: fastify.mqttBridge.pumpTypes
          }
        }
      });

    } catch (error) {
      fastify.log.error('Fehler beim Abrufen des Geräts:', error);
      return reply.status(500).send({
        success: false,
        error: 'Fehler beim Laden des Geräts'
      });
    }
  });

  // Add new device
  fastify.post('/', {
    preHandler: [fastify.authenticate]
    // Temporarily disabled: schema: { body: DeviceSchema }
  }, async (request, reply) => {
    try {
      const deviceData = request.body;
      const deviceId = `device_${Date.now()}`;

      const newDevice = {
        deviceId,
        ...deviceData,
        status: 'offline',
        createdAt: new Date(),
        updatedAt: new Date()
      };

      await fastify.db.collection('devices').insertOne(newDevice);

      return { 
        data: { 
          ...newDevice, 
          id: deviceId 
        } 
      };
    } catch (error) {
      fastify.log.error('Error adding device:', error);
      reply.status(500).send({ error: 'Failed to add device' });
    }
  });

  // Update device
  fastify.put('/:deviceId', {
    preHandler: [fastify.authenticate]
    // Temporarily disabled: schema: { body: DeviceSchema.partial() }
  }, async (request, reply) => {
    try {
      const { deviceId } = request.params;
      const updateData = request.body;

      const result = await fastify.db.collection('devices').updateOne(
        { deviceId },
        {
          $set: {
            ...updateData,
            updatedAt: new Date()
          }
        }
      );

      if (result.matchedCount === 0) {
        return reply.status(404).send({ error: 'Device not found' });
      }

      const updatedDevice = await fastify.db.collection('devices').findOne({ deviceId });
      return { 
        data: { 
          ...updatedDevice, 
          id: deviceId 
        } 
      };
    } catch (error) {
      fastify.log.error('Error updating device:', error);
      reply.status(500).send({ error: 'Failed to update device' });
    }
  });

  // Delete device
  fastify.delete('/:deviceId', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const { deviceId } = request.params;

      const result = await fastify.db.collection('devices').deleteOne({ deviceId });
      
      if (result.deletedCount === 0) {
        return reply.status(404).send({ error: 'Device not found' });
      }

      // Also delete related data
      await Promise.all([
        fastify.db.collection('sensor_data').deleteMany({ deviceId }),
        fastify.db.collection('latest_readings').deleteMany({ deviceId }),
        fastify.db.collection('device_configs').deleteMany({ deviceId })
      ]);

      return { message: 'Device deleted successfully' };
    } catch (error) {
      fastify.log.error('Error deleting device:', error);
      reply.status(500).send({ error: 'Failed to delete device' });
    }
  });

  // Get device configuration
  fastify.get('/:deviceId/config', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const { deviceId } = request.params;

      const config = await fastify.db.collection('device_configs').findOne({ deviceId });
      
      if (!config) {
        return reply.status(404).send({ error: 'Device configuration not found' });
      }

      return { data: config.config };
    } catch (error) {
      fastify.log.error('Error fetching device config:', error);
      reply.status(500).send({ error: 'Failed to fetch device configuration' });
    }
  });

  // Update device configuration
  fastify.put('/:deviceId/config', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const { deviceId } = request.params;
      const config = request.body;

      await fastify.db.collection('device_configs').replaceOne(
        { deviceId },
        {
          deviceId,
          config,
          updatedAt: new Date()
        },
        { upsert: true }
      );

      // Send updated config to device via MQTT
      await fastify.mqttBridge.sendDeviceConfig(deviceId);

      return { data: config };
    } catch (error) {
      fastify.log.error('Error updating device config:', error);
      reply.status(500).send({ error: 'Failed to update device configuration' });
    }
  });

  // Send command to device
  fastify.post('/:deviceId/commands', {
    preHandler: [fastify.authenticate]
    // Temporarily disabled: schema: { body: CommandSchema }
  }, async (request, reply) => {
    try {
      const { deviceId } = request.params;
      const command = request.body;

      // Verify device exists
      const device = await fastify.db.collection('devices').findOne({ deviceId });
      if (!device) {
        return reply.status(404).send({ error: 'Device not found' });
      }

      // Send command via MQTT
      const success = await fastify.mqttBridge.sendCommand(deviceId, command);
      
      if (!success) {
        return reply.status(500).send({ error: 'Failed to send command to device' });
      }

      // Log command
      await fastify.db.collection('device_commands').insertOne({
        deviceId,
        command: command.command,
        params: command.params || {},
        timestamp: new Date(),
        status: 'sent'
      });

      return { message: 'Command sent successfully' };
    } catch (error) {
      fastify.log.error('Error sending command:', error);
      reply.status(500).send({ error: 'Failed to send command' });
    }
  });

  // Get device command history
  fastify.get('/:deviceId/commands', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const { deviceId } = request.params;
      const { limit = 50, offset = 0 } = request.query;

      const commands = await fastify.db.collection('device_commands')
        .find({ deviceId })
        .sort({ timestamp: -1 })
        .limit(parseInt(limit))
        .skip(parseInt(offset))
        .toArray();

      return { data: commands };
    } catch (error) {
      fastify.log.error('Error fetching command history:', error);
      reply.status(500).send({ error: 'Failed to fetch command history' });
    }
  });

  // POST /api/devices/:deviceId/pumps/:pumpType/activate - Pumpe aktivieren
  fastify.post('/:deviceId/pumps/:pumpType/activate', {
    // preHandler: [fastify.authenticate] // Temporär deaktiviert
  }, async (request, reply) => {
    try {
      const { deviceId, pumpType } = request.params;
      const { duration = 5000 } = request.body; // Standard: 5 Sekunden

      // Validiere Pumpen-Typ
      if (!fastify.mqttBridge.pumpTypes.includes(pumpType)) {
        return reply.status(400).send({
          success: false,
          error: `Unbekannter Pumpen-Typ: ${pumpType}. Verfügbar: ${fastify.mqttBridge.pumpTypes.join(', ')}`
        });
      }

      // Validiere Duration
      const durationMs = parseInt(duration);
      if (isNaN(durationMs) || durationMs < 100 || durationMs > 60000) {
        return reply.status(400).send({
          success: false,
          error: 'Duration muss zwischen 100ms und 60000ms liegen'
        });
      }

      // Prüfe ob Gerät existiert
      const device = await fastify.db.collection('devices').findOne({ deviceId });
      if (!device) {
        return reply.status(404).send({
          success: false,
          error: 'Gerät nicht gefunden'
        });
      }

      // Sende MQTT-Kommando
      const command = await fastify.mqttBridge.sendPumpCommand(deviceId, pumpType, durationMs);

      // Speichere Kommando in DB
      await fastify.db.collection('device_commands').insertOne({
        deviceId,
        command,
        timestamp: new Date(),
        source: 'manual', // Manuell über API
        status: 'sent'
      });

      reply.send({
        success: true,
        data: {
          deviceId,
          pumpType,
          duration: durationMs,
          command,
          message: `${pumpType} wurde für ${durationMs}ms aktiviert`
        }
      });

    } catch (error) {
      fastify.log.error('Fehler beim Aktivieren der Pumpe:', error);
      reply.status(500).send({
        success: false,
        error: error.message || 'Fehler beim Aktivieren der Pumpe'
      });
    }
  });

  // GET /api/devices/:deviceId/sensors - Aktuelle Sensor-Werte
  fastify.get('/:deviceId/sensors', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const { deviceId } = request.params;

      const sensorData = {};
      for (const sensorType of fastify.mqttBridge.sensorTypes) {
        const latestReading = await fastify.db.collection('sensor_data').findOne(
          { deviceId, sensorType },
          { sort: { timestamp: -1 } }
        );
        if (latestReading) {
          sensorData[sensorType] = {
            value: latestReading.value,
            rawValue: latestReading.rawValue,
            timestamp: latestReading.timestamp,
            status: getSensorStatus(sensorType, latestReading.value)
          };
        }
      }

      reply.send({
        success: true,
        data: sensorData
      });

    } catch (error) {
      fastify.log.error('Fehler beim Abrufen der Sensor-Daten:', error);
      reply.status(500).send({
        success: false,
        error: 'Fehler beim Laden der Sensor-Daten'
      });
    }
  });

  // GET /api/devices/:deviceId/sensors/:sensorType/history - Sensor-Verlauf
  fastify.get('/:deviceId/sensors/:sensorType/history', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const { deviceId, sensorType } = request.params;
      const { hours = 24, limit = 100 } = request.query;

      if (!fastify.mqttBridge.sensorTypes.includes(sensorType)) {
        return reply.status(400).send({
          success: false,
          error: `Unbekannter Sensor-Typ: ${sensorType}`
        });
      }

      const hoursAgo = new Date(Date.now() - parseInt(hours) * 60 * 60 * 1000);

      const history = await fastify.db.collection('sensor_data')
        .find({
          deviceId,
          sensorType,
          timestamp: { $gte: hoursAgo }
        })
        .sort({ timestamp: -1 })
        .limit(parseInt(limit))
        .toArray();

      reply.send({
        success: true,
        data: {
          deviceId,
          sensorType,
          timeRange: { from: hoursAgo, to: new Date() },
          readings: history.reverse() // Chronologisch sortieren
        }
      });

    } catch (error) {
      fastify.log.error('Fehler beim Abrufen der Sensor-Historie:', error);
      reply.status(500).send({
        success: false,
        error: 'Fehler beim Laden der Sensor-Historie'
      });
    }
  });

  // GET /api/devices/:deviceId/commands/history - Command-Historie
  fastify.get('/:deviceId/commands/history', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const { deviceId } = request.params;
      const { limit = 50 } = request.query;

      const commands = await fastify.db.collection('device_commands')
        .find({ deviceId })
        .sort({ timestamp: -1 })
        .limit(parseInt(limit))
        .toArray();

      reply.send({
        success: true,
        data: {
          deviceId,
          commands
        }
      });

    } catch (error) {
      fastify.log.error('Fehler beim Abrufen der Command-Historie:', error);
      reply.status(500).send({
        success: false,
        error: 'Fehler beim Laden der Command-Historie'
      });
    }
  });

  // POST /api/devices/:deviceId/calibrate - Sensor kalibrieren
  fastify.post('/:deviceId/calibrate', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const { deviceId } = request.params;
      const { sensorType, calibrationData } = request.body;

      if (!fastify.mqttBridge.sensorTypes.includes(sensorType)) {
        return reply.status(400).send({
          success: false,
          error: `Unbekannter Sensor-Typ: ${sensorType}`
        });
      }

      // Sende Kalibrierungs-Kommando
      const command = await fastify.mqttBridge.sendCalibrationCommand(deviceId, sensorType, calibrationData);

      // Speichere Kalibrierungs-Kommando
      await fastify.db.collection('device_commands').insertOne({
        deviceId,
        command,
        timestamp: new Date(),
        source: 'calibration',
        status: 'sent'
      });

      reply.send({
        success: true,
        data: {
          deviceId,
          sensorType,
          calibrationData,
          message: `Kalibrierungs-Kommando für ${sensorType} gesendet`
        }
      });

    } catch (error) {
      fastify.log.error('Fehler beim Kalibrieren:', error);
      reply.status(500).send({
        success: false,
        error: 'Fehler beim Kalibrieren'
      });
    }
  });
}

// Hilfsfunktion: Sensor-Status bestimmen
function getSensorStatus(sensorType, value) {
  switch (sensorType) {
    case 'ph':
      if (value >= 5.5 && value <= 6.5) return 'optimal';
      if (value >= 5.0 && value <= 7.0) return 'warning';
      return 'critical';
    
    case 'tds':
      if (value >= 800 && value <= 1500) return 'optimal';
      if (value >= 600 && value <= 2000) return 'warning';
      return 'critical';
    
    default:
      return 'unknown';
  }
}