import Fastify from 'fastify';
import { handler } from '../build/handler.js';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Import services
import { DatabaseService } from './services/database.js';
import { MQTTBridge } from './services/mqtt-bridge.js';
import { BeaconServiceDiscovery } from './services/beacon-client.js';
import { WebSocketService } from './services/websocket.js';
import { AutomationEngine } from './services/automation-engine.js';
import { ProgramEngine } from './services/program-engine.js';
import { NotificationService } from './services/notification.js';

// Import models
import { DeviceModel } from './models/device.js';
import { SensorDataModel } from './models/sensor-data.js';
import { CommandModel } from './models/command.js';
import { ProgramModel } from './models/program.js';

// Import routes
import deviceRoutes from './routes/devices.js';
import sensorRoutes from './routes/sensors.js';
import commandRoutes from './routes/commands.js';
import programRoutes from './routes/programs.js';
import systemRoutes from './routes/system.js';

const fastify = Fastify({
  logger: {
    level: process.env.NODE_ENV === 'production' ? 'info' : 'debug'
  }
});

// Global error handler
fastify.setErrorHandler((error, request, reply) => {
  fastify.log.error(error);
  
  if (error.validation) {
    reply.status(400).send({
      success: false,
      error: 'Validation Error',
      details: error.validation
    });
  } else {
    reply.status(500).send({
      success: false,
      error: 'Internal Server Error',
      message: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong'
    });
  }
});

// Register plugins
await fastify.register(import('@fastify/cors'), {
  origin: true,
  credentials: true
});

await fastify.register(import('@fastify/static'), {
  root: path.join(__dirname, '../build/client'),
  prefix: '/assets/'
});

await fastify.register(import('@fastify/websocket'));

// Health check endpoint
fastify.get('/health', async (request, reply) => {
  return {
    status: 'ok',
    timestamp: new Date().toISOString(),
    version: process.env.npm_package_version || '3.0.0',
    services: {
      database: fastify.database ? 'connected' : 'disconnected',
      mqtt: fastify.mqttBridge ? 'connected' : 'disconnected',
      beacon: fastify.beaconClient ? 'connected' : 'disconnected'
    }
  };
});

// Initialize services
async function initializeServices() {
  try {
    // Database
    const database = new DatabaseService(
      process.env.MONGODB_URL || 'mongodb://bitsperity-mongodb:27017/homegrow'
    );
    await database.connect();
    fastify.decorate('database', database);
    
    // Models
    const deviceModel = new DeviceModel(database.db);
    const sensorDataModel = new SensorDataModel(database.db);
    const commandModel = new CommandModel(database.db);
    const programModel = new ProgramModel(database.db);
    
    fastify.decorate('models', {
      device: deviceModel,
      sensorData: sensorDataModel,
      command: commandModel,
      program: programModel
    });
    
    // Beacon Service Discovery
    const beaconClient = new BeaconServiceDiscovery(
      process.env.BEACON_URL || 'http://bitsperity-beacon:8080'
    );
    
    const beaconInitialized = await beaconClient.initialize();
    if (beaconInitialized) {
      fastify.decorate('beaconClient', beaconClient);
      fastify.log.info('Beacon Service Discovery initialized');
    } else {
      fastify.log.warn('Beacon Service Discovery not available, continuing without it');
    }
    
    // MQTT Bridge
    const mqttBridge = new MQTTBridge(
      process.env.MQTT_URL || 'mqtt://umbrel-mqtt:1883',
      deviceModel,
      sensorDataModel,
      commandModel
    );
    
    await mqttBridge.connect();
    fastify.decorate('mqttBridge', mqttBridge);
    fastify.log.info('MQTT Bridge connected');
    
    // WebSocket Service
    const wsService = new WebSocketService(
      fastify.server,
      mqttBridge,
      deviceModel,
      sensorDataModel
    );
    fastify.decorate('wsService', wsService);
    fastify.log.info('WebSocket Service initialized');
    
    // Automation Engine
    const automationEngine = new AutomationEngine(
      mqttBridge,
      deviceModel,
      sensorDataModel,
      commandModel
    );
    await automationEngine.initialize();
    fastify.decorate('automationEngine', automationEngine);
    fastify.log.info('Automation Engine initialized');
    
    // Program Engine
    const programEngine = new ProgramEngine(
      mqttBridge,
      deviceModel,
      programModel,
      commandModel
    );
    await programEngine.initialize();
    fastify.decorate('programEngine', programEngine);
    fastify.log.info('Program Engine initialized');
    
    // Notification Service
    const notificationService = new NotificationService();
    fastify.decorate('notificationService', notificationService);
    fastify.log.info('Notification Service initialized');
    
    // Connect Beacon events to device management
    if (beaconClient) {
      beaconClient.on('device_discovered', async (deviceInfo) => {
        try {
          const existing = await deviceModel.findByDeviceId(deviceInfo.device_id);
          if (!existing) {
            const device = await deviceModel.create({
              device_id: deviceInfo.device_id,
              name: deviceInfo.name,
              type: 'homegrow-client'
            });
            
            await deviceModel.updateBeaconInfo(deviceInfo.device_id, deviceInfo);
            await mqttBridge.subscribeToDevice(deviceInfo.device_id);
            
            fastify.log.info(`Auto-registered new device: ${deviceInfo.device_id}`);
          }
        } catch (error) {
          fastify.log.error('Error auto-registering device:', error);
        }
      });
      
      beaconClient.on('device_removed', async (deviceInfo) => {
        try {
          await deviceModel.updateStatus(deviceInfo.device_id, 'offline');
          fastify.log.info(`Device went offline: ${deviceInfo.device_id}`);
        } catch (error) {
          fastify.log.error('Error updating device status:', error);
        }
      });
    }
    
  } catch (error) {
    fastify.log.error('Failed to initialize services:', error);
    throw error;
  }
}

// Register API routes
fastify.register(async function (fastify) {
  fastify.register(deviceRoutes, { prefix: '/api/v1/devices' });
  fastify.register(sensorRoutes, { prefix: '/api/v1/sensors' });
  fastify.register(commandRoutes, { prefix: '/api/v1/commands' });
  fastify.register(programRoutes, { prefix: '/api/v1/programs' });
  fastify.register(systemRoutes, { prefix: '/api/v1/system' });
});

// WebSocket endpoint
fastify.register(async function (fastify) {
  fastify.get('/ws', { websocket: true }, (connection, req) => {
    if (fastify.wsService) {
      fastify.wsService.handleConnection(connection, req);
    }
  });
});

// SvelteKit handler for all other routes
fastify.all('/*', async (request, reply) => {
  return handler(request.raw, reply.raw);
});

// Graceful shutdown
const gracefulShutdown = async (signal) => {
  fastify.log.info(`Received ${signal}, shutting down gracefully...`);
  
  try {
    if (fastify.beaconClient) {
      await fastify.beaconClient.shutdown();
    }
    
    if (fastify.mqttBridge) {
      fastify.mqttBridge.disconnect();
    }
    
    if (fastify.database) {
      await fastify.database.disconnect();
    }
    
    await fastify.close();
    process.exit(0);
  } catch (error) {
    fastify.log.error('Error during shutdown:', error);
    process.exit(1);
  }
};

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

// Start server
const start = async () => {
  try {
    await initializeServices();
    
    const port = parseInt(process.env.PORT) || 3000;
    const host = process.env.HOST || '0.0.0.0';
    
    await fastify.listen({ port, host });
    
    fastify.log.info(`HomeGrow v3 server running on http://${host}:${port}`);
    fastify.log.info('Services initialized successfully');
    
  } catch (error) {
    fastify.log.error('Error starting server:', error);
    process.exit(1);
  }
};

start(); 