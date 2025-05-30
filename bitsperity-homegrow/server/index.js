import 'dotenv/config';
import fastify from 'fastify';
import path from 'path';
import { fileURLToPath } from 'url';
import fastifyStatic from '@fastify/static';
import fastifyCors from '@fastify/cors';
import fastifyWebsocket from '@fastify/websocket';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Services and models werden dynamisch geladen in initializeServices()

async function startServer() {
  const app = fastify({ logger: true });

  // Global services
  let db, deviceModel, sensorDataModel, beaconClient, mqttBridge, programEngine, databaseService, webSocketService;

  // Register plugins
  app.register(fastifyStatic, {
    root: path.join(__dirname, '../build'),
    prefix: '/',
  });

  app.register(fastifyCors, {
    origin: true
  });

  app.register(fastifyWebsocket);

  // Initialize services
  async function initializeServices() {
    try {
      console.log('🚀 Initializing HomeGrow v3 services...');

      // Dynamic imports for CommonJS modules
      const DatabaseConfigModule = await import('./config/database.js');
      const DatabaseConfig = DatabaseConfigModule.default || DatabaseConfigModule;
      
      const DeviceModelModule = await import('./models/device.js');
      const DeviceModel = DeviceModelModule.default || DeviceModelModule;
      
      const SensorDataModelModule = await import('./models/sensor-data.js');
      const SensorDataModel = SensorDataModelModule.default || SensorDataModelModule;
      
      const CommandModule = await import('./models/command.js');
      const Command = CommandModule.default || CommandModule;
      
      const BeaconServiceDiscoveryModule = await import('./services/beacon-client.js');
      const BeaconServiceDiscovery = BeaconServiceDiscoveryModule.default || BeaconServiceDiscoveryModule;
      
      const MQTTBridgeModule = await import('./services/mqtt-bridge.js');
      const MQTTBridge = MQTTBridgeModule.default || MQTTBridgeModule;
      
      const ProgramEngineModule = await import('./services/program-engine.js');
      const ProgramEngine = ProgramEngineModule.default || ProgramEngineModule;
      
      const DatabaseServiceModule = await import('./services/database.js');
      const { DatabaseService } = DatabaseServiceModule;
      
      const WebSocketServiceModule = await import('./services/websocket.js');
      const WebSocketService = WebSocketServiceModule.default || WebSocketServiceModule;

      // Initialize database
      const dbConfig = new DatabaseConfig();
      db = await dbConfig.connect();
      
      // Initialize models
      deviceModel = new DeviceModel(db);
      sensorDataModel = new SensorDataModel(db);
      
      // Initialize Beacon Service Discovery
      beaconClient = new BeaconServiceDiscovery(process.env.BEACON_URL || 'http://bitsperity-beacon_web_1:80');
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
      programEngine = new ProgramEngine();
      await programEngine.initialize(mqttBridge, db);
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
  app.get('/api/health', async (request, reply) => {
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

  app.get('/api/v1/system/status', async (request, reply) => {
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
  app.register(async function (fastify) {
    // Wait for services to be ready
    if (!deviceModel || !sensorDataModel) {
      throw new Error('Services not initialized');
    }
    
    // Dynamic imports for routes
    const DeviceRoutesModule = await import('./routes/devices.js');
    const DeviceRoutes = DeviceRoutesModule.default || DeviceRoutesModule;
    
    const SensorRoutesModule = await import('./routes/sensors.js');
    const SensorRoutes = SensorRoutesModule.default || SensorRoutesModule;
    
    const ProgramRoutesModule = await import('./routes/programs.js');
    const ProgramRoutes = ProgramRoutesModule.default || ProgramRoutesModule;
    
    const CommandRoutesModule = await import('./routes/commands.js');
    const CommandRoutes = CommandRoutesModule.default || CommandRoutesModule;
    
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
  app.register(async function (fastify) {
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
    
    await app.close();
    process.exit(0);
  });

  // Start server
  const start = async () => {
    try {
      // Initialize all services first
      await initializeServices();
      
      // Get port from environment
      const port = process.env.PORT || 3001;
      
      // Start HTTP server
      await app.listen({ port: parseInt(port), host: '0.0.0.0' });
      console.log(`🌐 HomeGrow v3 server listening on port ${port}`);
      console.log(`🎯 Dashboard: http://localhost:${port}`);
      console.log(`🔧 API: http://localhost:${port}/api/v1`);
      
    } catch (err) {
      console.error('❌ Server startup failed:', err);
      process.exit(1);
    }
  };

  start();
}

startServer(); 