const fastify = require('fastify')({ 
  logger: {
    level: process.env.LOG_LEVEL || 'info',
    transport: {
      target: 'pino-pretty',
      options: {
        colorize: true,
        translateTime: 'HH:MM:ss Z',
        ignore: 'pid,hostname'
      }
    }
  }
});

const path = require('path');

// Environment configuration
const config = {
  port: parseInt(process.env.PORT) || 3000,
  host: process.env.HOST || '0.0.0.0',
  mongodb_url: process.env.MONGODB_URL || 'mongodb://localhost:27017/homegrow',
  mqtt_url: process.env.MQTT_URL || 'mqtt://localhost:1883',
  beacon_url: process.env.BEACON_URL || 'http://localhost:8080'
};

// Register plugins
async function registerPlugins() {
  // CORS support
  await fastify.register(require('@fastify/cors'), {
    origin: true,
    credentials: true
  });

  // Static file serving
  await fastify.register(require('@fastify/static'), {
    root: path.join(__dirname, '../build'),
    prefix: '/'
  });

  // WebSocket support
  await fastify.register(require('@fastify/websocket'));

  // Rate limiting
  await fastify.register(require('@fastify/rate-limit'), {
    max: 100,
    timeWindow: '1 minute'
  });

  // Health check
  await fastify.register(require('@fastify/under-pressure'), {
    maxEventLoopDelay: 1000,
    maxHeapUsedBytes: 100000000,
    maxRssBytes: 100000000,
    maxEventLoopUtilization: 0.98
  });
}

// Initialize services
async function initializeServices() {
  try {
    // Initialize database
    const database = require('./services/database');
    await database.connect(config.mongodb_url);
    fastify.log.info('Database connected successfully');

    // Initialize beacon client
    const beaconClient = require('./services/beacon-client');
    await beaconClient.initialize(config.beacon_url);
    fastify.log.info('Beacon client initialized');

    // TODO: Initialize MQTT service
    // TODO: Initialize WebSocket service

  } catch (error) {
    fastify.log.error('Service initialization failed:', error);
    throw error;
  }
}

// Register API routes
async function registerRoutes() {
  // Health check endpoint
  fastify.get('/health', async (request, reply) => {
    return { 
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: process.env.npm_package_version || '3.0.0',
      uptime: process.uptime()
    };
  });

  // API v1 routes
  await fastify.register(async function (fastify) {
    // Device management routes
    await fastify.register(require('./routes/devices'), { prefix: '/devices' });
    
    // TODO: Add more route modules
    // await fastify.register(require('./routes/sensors'), { prefix: '/sensors' });
    // await fastify.register(require('./routes/commands'), { prefix: '/commands' });
    // await fastify.register(require('./routes/programs'), { prefix: '/programs' });
  }, { prefix: '/api/v1' });

  // WebSocket endpoint
  fastify.register(async function (fastify) {
    fastify.get('/ws', { websocket: true }, (connection, req) => {
      fastify.log.info('WebSocket connection established');
      
      connection.socket.on('message', (message) => {
        try {
          const data = JSON.parse(message);
          fastify.log.info('WebSocket message received:', data);
          
          // Handle different message types
          switch (data.type) {
            case 'subscribe_device':
              // TODO: Subscribe to device updates
              connection.socket.send(JSON.stringify({
                type: 'subscription_confirmed',
                device_id: data.device_id
              }));
              break;
            case 'ping':
              connection.socket.send(JSON.stringify({ type: 'pong' }));
              break;
            default:
              fastify.log.warn('Unknown WebSocket message type:', data.type);
          }
        } catch (error) {
          fastify.log.error('WebSocket message parsing failed:', error);
        }
      });

      connection.socket.on('close', () => {
        fastify.log.info('WebSocket connection closed');
      });
    });
  });

  // Catch-all route for SPA
  fastify.setNotFoundHandler(async (request, reply) => {
    if (request.url.startsWith('/api/')) {
      reply.code(404);
      return { 
        success: false, 
        error: 'API endpoint not found',
        path: request.url 
      };
    }
    
    // Serve index.html for SPA routes
    return reply.sendFile('index.html');
  });
}

// Graceful shutdown
async function gracefulShutdown() {
  try {
    fastify.log.info('Starting graceful shutdown...');
    
    // Close database connection
    const database = require('./services/database');
    await database.disconnect();
    
    // Close beacon client
    const beaconClient = require('./services/beacon-client');
    await beaconClient.disconnect();
    
    fastify.log.info('Graceful shutdown completed');
  } catch (error) {
    fastify.log.error('Error during shutdown:', error);
  }
}

// Start server
async function start() {
  try {
    // Register plugins
    await registerPlugins();
    
    // Initialize services
    await initializeServices();
    
    // Register routes
    await registerRoutes();
    
    // Start listening
    await fastify.listen({ 
      port: config.port, 
      host: config.host 
    });
    
    fastify.log.info(`HomeGrow v3 server started on ${config.host}:${config.port}`);
    fastify.log.info('Configuration:', {
      mongodb_url: config.mongodb_url,
      mqtt_url: config.mqtt_url,
      beacon_url: config.beacon_url
    });
    
  } catch (error) {
    fastify.log.error('Server startup failed:', error);
    process.exit(1);
  }
}

// Handle process signals
process.on('SIGTERM', async () => {
  fastify.log.info('SIGTERM received');
  await gracefulShutdown();
  await fastify.close();
  process.exit(0);
});

process.on('SIGINT', async () => {
  fastify.log.info('SIGINT received');
  await gracefulShutdown();
  await fastify.close();
  process.exit(0);
});

process.on('uncaughtException', (error) => {
  fastify.log.error('Uncaught exception:', error);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  fastify.log.error('Unhandled rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

// Start the server
if (require.main === module) {
  start();
}

module.exports = fastify; 