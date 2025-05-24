import 'dotenv/config';
import Fastify from 'fastify';
import cors from '@fastify/cors';
import jwt from '@fastify/jwt';
import websocket from '@fastify/websocket';
import { MongoClient } from 'mongodb';
import { createServer } from 'http';
import { Server as SocketIOServer } from 'socket.io';

// Import routes
import authRoutes from './routes/auth.js';
import deviceRoutes from './routes/devices.js';
import sensorRoutes from './routes/sensors.js';
import rulesRoutes from './routes/rules.js';

// Import services
import MQTTBridgeService from './services/mqtt-bridge.js';
import AutomationEngine from './services/automation.js';

// Configuration
const config = {
  port: process.env.PORT || 4001,
  host: process.env.HOST || '0.0.0.0',
  mongoUri: process.env.MONGODB_URI || 'mongodb://umbrel:umbrel@192.168.178.124:27017/admin',
  mqttHost: process.env.MQTT_HOST || 'localhost',
  mqttPort: parseInt(process.env.MQTT_PORT) || 1883,
  jwtSecret: process.env.JWT_SECRET || 'homegrow-secret-key',
  nodeEnv: process.env.NODE_ENV || 'development'
};

// Create Fastify instance
const fastify = Fastify({
  logger: {
    level: config.nodeEnv === 'development' ? 'debug' : 'info',
    transport: config.nodeEnv === 'development' ? {
      target: 'pino-pretty',
      options: {
        colorize: true
      }
    } : undefined
  }
});

// Global error handler
fastify.setErrorHandler((error, request, reply) => {
  fastify.log.error(error);
  
  if (error.validation) {
    reply.status(400).send({
      error: 'Validation Error',
      message: error.message,
      details: error.validation
    });
    return;
  }
  
  if (error.statusCode) {
    reply.status(error.statusCode).send({
      error: error.name,
      message: error.message
    });
    return;
  }
  
  reply.status(500).send({
    error: 'Internal Server Error',
    message: config.nodeEnv === 'development' ? error.message : 'Something went wrong'
  });
});

// Register plugins
await fastify.register(cors, {
  origin: true,
  credentials: true
});

await fastify.register(jwt, {
  secret: config.jwtSecret,
  sign: {
    expiresIn: '24h'
  }
});

await fastify.register(websocket);

// MongoDB connection
let db;
try {
  const client = new MongoClient(config.mongoUri);
  await client.connect();
  db = client.db('homegrow_v3'); // Explizit die homegrow_v3 Datenbank verwenden
  fastify.log.info('Connected to MongoDB (homegrow_v3 database)');
  
  // Make database available to routes
  fastify.decorate('db', db);
} catch (error) {
  fastify.log.error('Failed to connect to MongoDB:', error);
  process.exit(1);
}

// Initialize services
const mqttConfig = {
  MQTT_HOST: config.mqttHost,
  MQTT_PORT: config.mqttPort
};
const mqttBridge = new MQTTBridgeService(mqttConfig);
const automationEngine = new AutomationEngine(mqttBridge, db);

// Make services available to routes
fastify.decorate('mqttBridge', mqttBridge);
fastify.decorate('automationEngine', automationEngine);

// Authentication decorator
fastify.decorate('authenticate', async function (request, reply) {
  try {
    await request.jwtVerify();
  } catch (err) {
    reply.send(err);
  }
});

// Health check
fastify.get('/health', async (request, reply) => {
  const { cleanup } = request.query;
  
  // Optional cleanup of duplicate devices
  if (cleanup === 'devices') {
    try {
      const allDevices = await db.collection('devices').find({}).toArray();
      const deviceGroups = {};
      
      allDevices.forEach(device => {
        if (!deviceGroups[device.deviceId]) {
          deviceGroups[device.deviceId] = [];
        }
        deviceGroups[device.deviceId].push(device);
      });
      
      let cleanupCount = 0;
      
      for (const [deviceId, devices] of Object.entries(deviceGroups)) {
        if (devices.length > 1) {
          devices.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
          const toDelete = devices.slice(1);
          
          for (const device of toDelete) {
            await db.collection('devices').deleteOne({ _id: device._id });
            cleanupCount++;
          }
        }
      }
      
      fastify.log.info(`Cleaned up ${cleanupCount} duplicate devices`);
    } catch (error) {
      fastify.log.error('Error during cleanup:', error);
    }
  }
  
  return {
    status: 'ok',
    timestamp: new Date().toISOString(),
    version: '3.0.0',
    services: {
      mongodb: db ? 'connected' : 'disconnected',
      mqtt: mqttBridge.isConnected ? 'connected' : 'disconnected',
      automation: automationEngine.isRunning ? 'running' : 'stopped'
    },
    mqttStatus: mqttBridge.getStatus()
  };
});

// Register API routes
await fastify.register(authRoutes, { prefix: '/api/auth' });
await fastify.register(deviceRoutes, { prefix: '/api/devices' });
await fastify.register(sensorRoutes, { prefix: '/api/sensors' });
await fastify.register(rulesRoutes, { prefix: '/api/rules' });

// Temporary cleanup route for device duplicates
fastify.post('/admin/cleanup-devices', async (request, reply) => {
  try {
    // Find all devices and group by deviceId
    const allDevices = await db.collection('devices').find({}).toArray();
    const deviceGroups = {};
    
    allDevices.forEach(device => {
      if (!deviceGroups[device.deviceId]) {
        deviceGroups[device.deviceId] = [];
      }
      deviceGroups[device.deviceId].push(device);
    });
    
    let cleanupCount = 0;
    
    // Remove duplicates, keep the most recent one
    for (const [deviceId, devices] of Object.entries(deviceGroups)) {
      if (devices.length > 1) {
        // Sort by createdAt, keep the newest
        devices.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
        const toKeep = devices[0];
        const toDelete = devices.slice(1);
        
        // Delete duplicates
        for (const device of toDelete) {
          await db.collection('devices').deleteOne({ _id: device._id });
          cleanupCount++;
        }
        
        fastify.log.info(`Cleaned up ${toDelete.length} duplicates for device ${deviceId}, kept ${toKeep._id}`);
      }
    }
    
    return {
      success: true,
      message: `Cleaned up ${cleanupCount} duplicate devices`,
      remainingDevices: Object.keys(deviceGroups).length
    };
    
  } catch (error) {
    fastify.log.error('Error during device cleanup:', error);
    return reply.status(500).send({
      success: false,
      error: error.message
    });
  }
});

// WebSocket for real-time updates
fastify.register(async function (fastify) {
  fastify.get('/ws', { websocket: true }, (connection, req) => {
    fastify.log.info('WebSocket client connected');
    
    connection.on('message', (message) => {
      try {
        const data = JSON.parse(message.toString());
        fastify.log.debug('WebSocket message received:', data);
        
        // Handle different message types
        switch (data.type) {
          case 'subscribe':
            // Subscribe to specific device updates
            connection.deviceId = data.deviceId;
            break;
          case 'ping':
            connection.send(JSON.stringify({ type: 'pong' }));
            break;
        }
      } catch (error) {
        fastify.log.error('WebSocket message error:', error);
      }
    });
    
    connection.on('close', () => {
      fastify.log.info('WebSocket client disconnected');
    });
  });
});

// Setup MQTT Bridge event handlers
mqttBridge.on('sensorData', async (sensorReading) => {
  try {
    fastify.log.debug('Attempting to save sensor data:', sensorReading);
    
    // Validate sensor reading data
    if (!sensorReading.deviceId || !sensorReading.sensorType || sensorReading.value === undefined) {
      throw new Error('Invalid sensor reading data: missing required fields');
    }
    
    // Ensure timestamp is valid
    if (!(sensorReading.timestamp instanceof Date) || isNaN(sensorReading.timestamp)) {
      sensorReading.timestamp = new Date();
    }
    
    if (!(sensorReading.receivedAt instanceof Date) || isNaN(sensorReading.receivedAt)) {
      sensorReading.receivedAt = new Date();
    }
    
    // Auto-register device if not exists (with proper duplicate prevention)
    const deviceUpdateResult = await db.collection('devices').updateOne(
      { deviceId: sensorReading.deviceId },
      {
        $set: { 
          lastSeen: new Date(), 
          status: 'online',
          updatedAt: new Date()
        },
        $setOnInsert: {
          name: `ESP32 Device (${sensorReading.deviceId})`,
          type: 'hydroponic',
          location: 'Hydroponic System',
          description: 'Automatisch erkanntes ESP32 Gerät',
          capabilities: {
            sensors: ['ph', 'tds'],
            pumps: ['water_pump', 'air_pump', 'ph_up_pump', 'ph_down_pump', 'nutrient_pump_1', 'nutrient_pump_2', 'nutrient_pump_3']
          },
          createdAt: new Date()
        }
      },
      { upsert: true }
    );
    
    if (deviceUpdateResult.upsertedCount > 0) {
      fastify.log.info(`🔍 Auto-registered new device: ${sensorReading.deviceId}`);
    }
    
    // Speichere Sensor-Daten in MongoDB
    const insertResult = await db.collection('sensor_data').insertOne(sensorReading);
    fastify.log.debug('Sensor data insert result:', insertResult.insertedId);
    
    // Update latest readings (avoid _id conflicts by using updateOne instead of replaceOne)
    const latestReadingData = {
      deviceId: sensorReading.deviceId,
      sensorType: sensorReading.sensorType,
      value: sensorReading.value,
      rawValue: sensorReading.rawValue,
      timestamp: sensorReading.timestamp,
      receivedAt: sensorReading.receivedAt
    };
    
    const latestUpdateResult = await db.collection('latest_readings').updateOne(
      { 
        deviceId: sensorReading.deviceId, 
        sensorType: sensorReading.sensorType 
      },
      { $set: latestReadingData },
      { upsert: true }
    );
    fastify.log.debug('Latest reading update result:', latestUpdateResult);
    
    fastify.log.info(`✅ Sensor data saved: ${sensorReading.deviceId}/${sensorReading.sensorType} = ${sensorReading.value}`);
  } catch (error) {
    fastify.log.error('❌ Error saving sensor data:', error.message);
    fastify.log.error('❌ Error stack:', error.stack);
    fastify.log.error('❌ Sensor reading data was:', JSON.stringify(sensorReading, null, 2));
    fastify.log.error('❌ Full error details:', {
      name: error.name,
      message: error.message,
      code: error.code,
      stack: error.stack
    });
  }
});

mqttBridge.on('commandResponse', async (commandResponse) => {
  try {
    // Update command status
    await db.collection('device_commands').updateOne(
      { 
        deviceId: commandResponse.deviceId,
        'command.type': commandResponse.commandType,
        timestamp: { $gte: new Date(Date.now() - 10000) } // Last 10 seconds
      },
      { 
        $set: { 
          status: 'acknowledged',
          acknowledgedAt: commandResponse.receivedAt
        }
      }
    );
    
    fastify.log.debug(`Command acknowledged: ${commandResponse.deviceId}/${commandResponse.commandType}`);
  } catch (error) {
    fastify.log.error('Error updating command status:', error);
  }
});

// Start services
try {
  await mqttBridge.connect();
  await automationEngine.start();
  fastify.log.info('All services started successfully');
} catch (error) {
  fastify.log.error('Failed to start services:', error);
  process.exit(1);
}

// Start server
try {
  await fastify.listen({ port: config.port, host: config.host });
  fastify.log.info(`HomeGrow Backend v3 running on http://${config.host}:${config.port}`);
  fastify.log.info('ESP32 devices can now discover this server via mDNS');
} catch (err) {
  fastify.log.error(err);
  process.exit(1);
}

// Graceful shutdown
process.on('SIGINT', async () => {
  fastify.log.info('Shutting down gracefully...');
  
  try {
    mqttBridge.disconnect();
    await automationEngine.stop();
    await fastify.close();
    process.exit(0);
  } catch (error) {
    fastify.log.error('Error during shutdown:', error);
    process.exit(1);
  }
}); 