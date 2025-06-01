const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const { MongoClient } = require('mongodb');
const path = require('path');
const winston = require('winston');
const helmet = require('helmet');
const compression = require('compression');
const cors = require('cors');

// Configure Winston logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.simple()
    }),
    new winston.transports.File({ filename: 'logs/web-server.log' })
  ]
});

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

// Middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com"],
      scriptSrc: ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'", "ws:", "wss:"]
    }
  }
}));
app.use(compression());
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// MongoDB connection
const MONGODB_URL = process.env.MONGODB_URL || 'mongodb://192.168.178.57:27017';
const DATABASE_NAME = 'bitsperity_mqtt_mcp';

let db = null;
let isConnected = false;

// Connect to MongoDB
async function connectMongoDB() {
  try {
    const client = new MongoClient(MONGODB_URL);
    await client.connect();
    db = client.db(DATABASE_NAME);
    isConnected = true;
    logger.info('Connected to MongoDB');
    
    // Ensure TTL indexes exist
    await ensureTTLIndexes();
    
    // Start watching for changes
    startChangeStreams();
    
  } catch (error) {
    logger.error('MongoDB connection failed:', error);
    isConnected = false;
  }
}

// Ensure TTL indexes for data cleanup
async function ensureTTLIndexes() {
  try {
    // Tool calls collection - 24 hour TTL
    await db.collection('mcp_tool_calls').createIndex(
      { timestamp: 1 },
      { expireAfterSeconds: 86400 }
    );
    
    // System logs collection - 7 day TTL  
    await db.collection('mcp_system_logs').createIndex(
      { timestamp: 1 },
      { expireAfterSeconds: 604800 }
    );
    
    // Performance metrics collection - 7 day TTL
    await db.collection('mcp_performance_metrics').createIndex(
      { timestamp: 1 },
      { expireAfterSeconds: 604800 }
    );
    
    logger.info('TTL indexes ensured');
  } catch (error) {
    logger.error('Failed to create TTL indexes:', error);
  }
}

// Watch MongoDB changes for real-time updates
function startChangeStreams() {
  if (!db) return;
  
  try {
    // Watch tool calls
    const toolCallsStream = db.collection('mcp_tool_calls').watch();
    toolCallsStream.on('change', (change) => {
      io.emit('tool_call_update', {
        operationType: change.operationType,
        document: change.fullDocument,
        timestamp: new Date()
      });
    });
    
    // Watch system logs
    const systemLogsStream = db.collection('mcp_system_logs').watch();
    systemLogsStream.on('change', (change) => {
      io.emit('system_log_update', {
        operationType: change.operationType,
        document: change.fullDocument,
        timestamp: new Date()
      });
    });
    
    // Watch performance metrics
    const metricsStream = db.collection('mcp_performance_metrics').watch();
    metricsStream.on('change', (change) => {
      io.emit('performance_update', {
        operationType: change.operationType,
        document: change.fullDocument,
        timestamp: new Date()
      });
    });
    
    logger.info('Change streams started');
  } catch (error) {
    logger.error('Failed to start change streams:', error);
  }
}

// API Routes

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date(),
    mongodb: isConnected,
    uptime: process.uptime()
  });
});

// Get MCP Tool Documentation
app.get('/api/tools', async (req, res) => {
  try {
    // Static tool definitions based on MCP Server implementation
    const tools = [
      {
        name: 'establish_connection',
        description: 'Establish connection to MQTT broker',
        parameters: {
          connection_string: 'MQTT connection string (mqtt://[username:password@]broker:port[/client_id])'
        },
        example: 'establish_connection("mqtt://192.168.178.57:1883")',
        category: 'connection'
      },
      {
        name: 'list_active_connections', 
        description: 'List all active MQTT connections',
        parameters: {
          random_string: 'Dummy parameter for no-parameter tools'
        },
        example: 'list_active_connections("dummy")',
        category: 'connection'
      },
      {
        name: 'close_connection',
        description: 'Close an active MQTT connection',
        parameters: {
          session_id: 'Session ID of the connection to close'
        },
        example: 'close_connection("session-uuid")',
        category: 'connection'
      },
      {
        name: 'list_topics',
        description: 'Discover available MQTT topics',
        parameters: {
          session_id: 'Session ID of active connection',
          pattern: 'Topic pattern for discovery (default: "#")'
        },
        example: 'list_topics("session-uuid", "sensor/+/temperature")',
        category: 'discovery'
      },
      {
        name: 'subscribe_and_collect',
        description: 'Subscribe to topic and collect messages',
        parameters: {
          session_id: 'Session ID of active connection',
          topic_pattern: 'MQTT topic pattern to subscribe to',
          duration_seconds: 'Collection duration (10-300 seconds)'
        },
        example: 'subscribe_and_collect("session-uuid", "device/+/data", 60)',
        category: 'data'
      },
      {
        name: 'publish_message',
        description: 'Publish message to MQTT topic',
        parameters: {
          session_id: 'Session ID of active connection',
          topic: 'MQTT topic to publish to',
          payload: 'Message payload as string',
          qos: 'Quality of Service (0, 1, or 2)',
          retain: 'Whether to retain message'
        },
        example: 'publish_message("session-uuid", "device/pump1/command", "START", 1, false)',
        category: 'data'
      },
      {
        name: 'get_topic_schema',
        description: 'Analyze message structures for schema patterns',
        parameters: {
          session_id: 'Session ID of active connection',
          topic_pattern: 'Topic pattern to analyze'
        },
        example: 'get_topic_schema("session-uuid", "sensor/+/data")',
        category: 'analysis'
      },
      {
        name: 'debug_device',
        description: 'Device-specific monitoring and debugging',
        parameters: {
          session_id: 'Session ID of active connection',
          device_id: 'Device identifier to debug'
        },
        example: 'debug_device("session-uuid", "pump1")',
        category: 'debugging'
      },
      {
        name: 'monitor_performance',
        description: 'Monitor connection and broker performance',
        parameters: {
          session_id: 'Session ID of active connection'
        },
        example: 'monitor_performance("session-uuid")',
        category: 'monitoring'
      },
      {
        name: 'test_connection',
        description: 'Comprehensive connection health check',
        parameters: {
          session_id: 'Session ID of active connection'
        },
        example: 'test_connection("session-uuid")',
        category: 'monitoring'
      }
    ];
    
    res.json(tools);
  } catch (error) {
    logger.error('Failed to get tools:', error);
    res.status(500).json({ error: 'Failed to retrieve tools' });
  }
});

// Get recent tool calls
app.get('/api/tool-calls', async (req, res) => {
  try {
    if (!db) {
      return res.status(503).json({ error: 'Database not connected' });
    }
    
    const limit = parseInt(req.query.limit) || 50;
    const toolFilter = req.query.tool;
    const statusFilter = req.query.status;
    
    let query = {};
    if (toolFilter) query.tool_name = toolFilter;
    if (statusFilter) query.status = statusFilter;
    
    const toolCalls = await db.collection('mcp_tool_calls')
      .find(query)
      .sort({ timestamp: -1 })
      .limit(limit)
      .toArray();
    
    res.json(toolCalls);
  } catch (error) {
    logger.error('Failed to get tool calls:', error);
    res.status(500).json({ error: 'Failed to retrieve tool calls' });
  }
});

// Get system logs
app.get('/api/system-logs', async (req, res) => {
  try {
    if (!db) {
      return res.status(503).json({ error: 'Database not connected' });
    }
    
    const limit = parseInt(req.query.limit) || 100;
    const level = req.query.level;
    
    let query = {};
    if (level) query.level = level;
    
    const logs = await db.collection('mcp_system_logs')
      .find(query)
      .sort({ timestamp: -1 })
      .limit(limit)
      .toArray();
    
    res.json(logs);
  } catch (error) {
    logger.error('Failed to get system logs:', error);
    res.status(500).json({ error: 'Failed to retrieve system logs' });
  }
});

// Get performance metrics
app.get('/api/performance-metrics', async (req, res) => {
  try {
    if (!db) {
      return res.status(503).json({ error: 'Database not connected' });
    }
    
    const hours = parseInt(req.query.hours) || 24;
    const startTime = new Date(Date.now() - hours * 60 * 60 * 1000);
    
    const metrics = await db.collection('mcp_performance_metrics')
      .find({ timestamp: { $gte: startTime } })
      .sort({ timestamp: 1 })
      .toArray();
    
    res.json(metrics);
  } catch (error) {
    logger.error('Failed to get performance metrics:', error);
    res.status(500).json({ error: 'Failed to retrieve performance metrics' });
  }
});

// Get connection statistics
app.get('/api/connections', async (req, res) => {
  try {
    // This would typically query the MCP server directly
    // For now, return mock data based on recent tool calls
    if (!db) {
      return res.status(503).json({ error: 'Database not connected' });
    }
    
    const recentCalls = await db.collection('mcp_tool_calls')
      .find({ timestamp: { $gte: new Date(Date.now() - 60 * 60 * 1000) } })
      .toArray();
    
    // Extract unique sessions
    const sessions = {};
    recentCalls.forEach(call => {
      if (call.session_id && !sessions[call.session_id]) {
        sessions[call.session_id] = {
          session_id: call.session_id,
          status: 'active',
          last_activity: call.timestamp,
          tool_calls: 0
        };
      }
      if (call.session_id) {
        sessions[call.session_id].tool_calls++;
      }
    });
    
    res.json(Object.values(sessions));
  } catch (error) {
    logger.error('Failed to get connections:', error);
    res.status(500).json({ error: 'Failed to retrieve connections' });
  }
});

// WebSocket connection handling
io.on('connection', (socket) => {
  logger.info(`Client connected: ${socket.id}`);
  
  socket.on('disconnect', () => {
    logger.info(`Client disconnected: ${socket.id}`);
  });
  
  // Send initial data to new clients
  socket.emit('connected', {
    message: 'Connected to MQTT MCP Frontend',
    timestamp: new Date()
  });
});

// Start server
const PORT = process.env.PORT || 8091;

// Connect to MongoDB first, then start server
connectMongoDB().then(() => {
  server.listen(PORT, '0.0.0.0', () => {
    logger.info(`MQTT MCP Frontend server running on port ${PORT}`);
    logger.info(`Health check: http://localhost:${PORT}/health`);
  });
}).catch(error => {
  logger.error('Failed to start server:', error);
  process.exit(1);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('Received SIGTERM, shutting down gracefully');
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  logger.info('Received SIGINT, shutting down gracefully');
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
}); 