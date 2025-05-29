require('dotenv').config();
const fastify = require('fastify')({ logger: true });
const path = require('path');

// Import services and models
const DatabaseConfig = require('./config/database');
const DeviceModel = require('./models/device');
const SensorDataModel = require('./models/sensor-data');
const Command = require('./models/command');
const BeaconServiceDiscovery = require('./services/beacon-client');
const MQTTBridge = require('./services/mqtt-bridge');
const ProgramEngine = require('./services/program-engine');
const DeviceRoutes = require('./routes/devices');
const SensorRoutes = require('./routes/sensors');
const ProgramRoutes = require('./routes/programs');
const CommandRoutes = require('./routes/commands');
const { DatabaseService } = require('./services/database');
const WebSocketService = require('./services/websocket');

// Global services
let db, deviceModel, sensorDataModel, beaconClient, mqttBridge, programEngine, databaseService, webSocketService;

// Register plugins
fastify.register(require('@fastify/static'), {
  root: path.join(__dirname, '../build'),
  prefix: '/',
});

fastify.register(require('@fastify/cors'), {
  origin: true
});

fastify.register(require('@fastify/websocket'));

// Initialize services
async function initializeServices() {
  try {
    console.log('🚀 Initializing HomeGrow v3 services...');

    // Initialize database
    const dbConfig = new DatabaseConfig();
    db = await dbConfig.connect();
    
    // Initialize models
    deviceModel = new DeviceModel(db);
    sensorDataModel = new SensorDataModel(db);
    
    // Initialize Beacon Service Discovery
    beaconClient = new BeaconServiceDiscovery(process.env.BEACON_URL || 'http://bitsperity-beacon:8097');
    await beaconClient.initialize();
    
    // Initialize MQTT Bridge
    mqttBridge = new MQTTBridge(
      process.env.MQTT_URL,
      deviceModel,
      sensorDataModel,
      Command // Command model now implemented
    );
    await mqttBridge.connect();
    
    // Initialize Program Engine
    programEngine = ProgramEngine;
    await programEngine.initialize(mqttBridge);
    programEngine.start();
    
    // Initialize Database Service
    databaseService = new DatabaseService();
    
    // Initialize WebSocket Service
    webSocketService = new WebSocketService();
    
    // Setup event listeners
    setupEventListeners();
    
    console.log('✅ All services initialized successfully');
    
  } catch (error) {
    console.error('❌ Failed to initialize services:', error);
    throw error;
  }
}

function setupEventListeners() {
  // Beacon events
  beaconClient.on('device_discovered', async (deviceInfo) => {
    console.log(`🔍 New device discovered via Beacon: ${deviceInfo.device_id}`);
    
    // Auto-register if not exists
    const existing = await deviceModel.findByDeviceId(deviceInfo.device_id);
    if (!existing) {
      try {
        const device = await deviceModel.create({
          device_id: deviceInfo.device_id,
          name: deviceInfo.name,
          type: 'homegrow-client'
        });
        
        await deviceModel.updateBeaconInfo(deviceInfo.device_id, deviceInfo);
        await mqttBridge.subscribeToDevice(deviceInfo.device_id);
        
        console.log(`✅ Auto-registered device: ${deviceInfo.device_id}`);
        
        // Broadcast to WebSocket clients
        webSocketService.broadcastDeviceDiscovered(deviceInfo);
      } catch (error) {
        console.error(`❌ Failed to auto-register device ${deviceInfo.device_id}:`, error);
      }
    }
  });

  beaconClient.on('device_removed', async (deviceInfo) => {
    console.log(`📤 Device removed from Beacon: ${deviceInfo.device_id}`);
    await deviceModel.updateStatus(deviceInfo.device_id, 'offline');
    
    // Broadcast status update
    webSocketService.broadcastDeviceStatus(deviceInfo.device_id, 'offline');
  });

  // MQTT events
  mqttBridge.on('sensor_data', (data) => {
    // Real-time sensor data received - broadcast via WebSocket
    console.log(`📊 Real-time sensor data: ${data.device_id}/${data.sensor_type}`);
    
    // Broadcast to WebSocket clients
    webSocketService.broadcastSensorData(data.device_id, data.sensor_type, data.data);
    
    // Trigger sensor-based programs
    if (programEngine) {
      programEngine.handleSensorTrigger(data.device_id, data.sensor_type, data.data.values.calibrated);
    }
  });

  mqttBridge.on('device_heartbeat', async (data) => {
    // Device heartbeat received
    await deviceModel.updateStatus(data.device_id, 'online');
    
    // Broadcast status update
    webSocketService.broadcastDeviceStatus(data.device_id, 'online');
  });

  mqttBridge.on('device_status', (data) => {
    // Device status changed - broadcast via WebSocket
    webSocketService.broadcastDeviceStatus(data.device_id, data.status);
  });

  mqttBridge.on('command_response', (data) => {
    // Command response received - broadcast via WebSocket
    webSocketService.broadcastCommandResponse(data.device_id, data.command_id, data.response);
  });
  
  // Program Engine events
  if (programEngine) {
    programEngine.on('program_started', (program) => {
      console.log(`▶️ Program started: ${program.name}`);
      webSocketService.broadcastProgramUpdate(program._id, { status: 'started' });
    });
    
    programEngine.on('program_completed', (program) => {
      console.log(`✅ Program completed: ${program.name}`);
      webSocketService.broadcastProgramUpdate(program._id, { status: 'completed' });
    });
    
    programEngine.on('program_error', (program, error) => {
      console.error(`❌ Program error: ${program.name}`, error);
      webSocketService.broadcastProgramUpdate(program._id, { status: 'error', error: error.message });
    });
  }

  // Periodic cleanup of stale devices
  setInterval(async () => {
    try {
      const result = await deviceModel.markOfflineIfStale(5); // 5 minutes
      if (result.modifiedCount > 0) {
        console.log(`📴 Marked ${result.modifiedCount} devices as offline due to inactivity`);
      }
    } catch (error) {
      console.error('❌ Error during device cleanup:', error);
    }
  }, 60000); // Every minute

  // Periodic command timeout check
  setInterval(async () => {
    try {
      const timeoutCount = await Command.markTimeoutCommands();
      if (timeoutCount > 0) {
        console.log(`⏰ Marked ${timeoutCount} commands as timeout`);
      }
    } catch (error) {
      console.error('❌ Error during command timeout check:', error);
    }
  }, 30000); // Every 30 seconds
}

// API Routes
fastify.get('/api/health', async (request, reply) => {
  const health = {
    status: 'ok',
    timestamp: new Date(),
    services: {
      database: db ? 'connected' : 'disconnected',
      mqtt: mqttBridge ? mqttBridge.getConnectionStatus() : 'not_initialized',
      beacon: beaconClient ? beaconClient.getStatus() : 'not_initialized'
    }
  };
  
  return health;
});

fastify.get('/api/v1/system/status', async (request, reply) => {
  const status = {
    server: 'running',
    version: '3.0.0',
    uptime: process.uptime(),
    timestamp: new Date(),
    services: {
      database: databaseService.getStatus(),
      mqtt: mqttBridge ? mqttBridge.getConnectionStatus() : { connected: false },
      beacon: beaconClient.getStatus(),
      websocket: webSocketService.getStatus(),
      program_engine: programEngine ? programEngine.getStatus() : { running: false }
    },
    memory: {
      used: process.memoryUsage().heapUsed / 1024 / 1024,
      total: process.memoryUsage().heapTotal / 1024 / 1024
    }
  };
  
  return reply.send(status);
});

// Register API routes after services are initialized
fastify.register(async function (fastify) {
  // Wait for services to be ready
  if (!deviceModel || !sensorDataModel) {
    throw new Error('Services not initialized');
  }
  
  // Device routes
  const deviceRoutes = new DeviceRoutes(deviceModel, mqttBridge, beaconClient);
  fastify.register(async function (fastify) {
    fastify.register(deviceRoutes.getRouter(), { prefix: '/api/v1/devices' });
  });
  
  // Sensor routes  
  const sensorRoutes = new SensorRoutes(sensorDataModel, deviceModel);
  fastify.register(async function (fastify) {
    fastify.register(sensorRoutes.getRouter(), { prefix: '/api/v1/sensors' });
  });
  
  // Program routes
  fastify.register(async function (fastify) {
    fastify.register(ProgramRoutes, { prefix: '/api/v1/programs' });
  });
  
  // Command routes
  fastify.register(async function (fastify) {
    // Make MQTT bridge available to command routes
    fastify.decorate('mqttBridge', mqttBridge);
    fastify.register(CommandRoutes, { prefix: '/api/v1/commands' });
  });
});

// WebSocket endpoint for real-time updates
fastify.register(async function (fastify) {
  fastify.get('/ws', { websocket: true }, (connection, req) => {
    webSocketService.handleConnection(connection, req);
  });
});

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n🛑 Shutting down HomeGrow v3...');
  
  if (mqttBridge) {
    mqttBridge.disconnect();
  }
  
  if (beaconClient) {
    await beaconClient.shutdown();
  }
  
  await fastify.close();
  process.exit(0);
});

// Start server
const start = async () => {
  try {
    // Initialize all services first
    await initializeServices();
    
    // Start HTTP server
    await fastify.listen({ port: 3000, host: '0.0.0.0' });
    console.log('🌐 HomeGrow v3 server listening on port 3000');
    console.log('🎯 Dashboard: http://localhost:3000');
    console.log('🔧 API: http://localhost:3000/api/v1');
    
  } catch (err) {
    console.error('❌ Server startup failed:', err);
    process.exit(1);
  }
};

start(); 