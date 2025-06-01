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
    
    // Note: Change streams removed - not supported in standalone MongoDB
    logger.info('MongoDB connection established without change streams');
    
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

// API Routes with real MongoDB data

// Get MCP Tool Documentation (static)
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

// Get tool calls from MongoDB
app.get('/api/tool-calls', async (req, res) => {
  try {
    if (!isConnected) {
      return res.status(503).json({ error: 'Database not connected' });
    }
    
    const limit = parseInt(req.query.limit) || 50;
    const page = parseInt(req.query.page) || 0;
    const skip = page * limit;
    
    // Query actual tool calls from MCP server
    const toolCalls = await db.collection('mcp_tool_calls')
      .find({})
      .sort({ timestamp: -1 })
      .skip(skip)
      .limit(limit)
      .toArray();
    
    // Transform for frontend
    const formattedCalls = toolCalls.map(call => ({
      id: call._id,
      timestamp: call.timestamp,
      tool_name: call.tool_name,
      success: call.success,
      duration_ms: call.duration_ms,
      result_size_kb: call.result_size_kb,
      error: call.error,
      params: call.params
    }));
    
    res.json({
      tool_calls: formattedCalls,
      total: await db.collection('mcp_tool_calls').countDocuments({}),
      page,
      limit
    });
    
  } catch (error) {
    logger.error('Error fetching tool calls:', error);
    res.status(500).json({ error: 'Failed to fetch tool calls' });
  }
});

// Get system logs from MongoDB  
app.get('/api/system-logs', async (req, res) => {
  try {
    if (!isConnected) {
      return res.status(503).json({ error: 'Database not connected' });
    }
    
    const limit = parseInt(req.query.limit) || 100;
    const level = req.query.level; // ERROR, WARN, INFO
    const page = parseInt(req.query.page) || 0;
    const skip = page * limit;
    
    // Build query filter
    const query = {};
    if (level && level !== 'ALL') {
      query.level = level;
    }
    
    // Query actual system logs from MCP server
    const logs = await db.collection('mcp_system_logs')
      .find(query)
      .sort({ timestamp: -1 })
      .skip(skip)
      .limit(limit)
      .toArray();
    
    // Transform for frontend
    const formattedLogs = logs.map(log => ({
      id: log._id,
      timestamp: log.timestamp,
      level: log.level,
      event_type: log.event_type,
      message: log.message,
      metadata: log.metadata
    }));
    
    res.json({
      logs: formattedLogs,
      total: await db.collection('mcp_system_logs').countDocuments(query),
      page,
      limit
    });
    
  } catch (error) {
    logger.error('Error fetching system logs:', error);
    res.status(500).json({ error: 'Failed to fetch system logs' });
  }
});

// Get performance metrics from MongoDB
app.get('/api/performance-metrics', async (req, res) => {
  try {
    if (!isConnected) {
      return res.status(503).json({ error: 'Database not connected' });
    }
    
    const hours = parseInt(req.query.hours) || 24;
    const since = new Date(Date.now() - hours * 60 * 60 * 1000);
    
    // Query actual performance metrics from MCP server
    const metrics = await db.collection('mcp_performance_metrics')
      .find({ timestamp: { $gte: since } })
      .sort({ timestamp: -1 })
      .limit(1000)
      .toArray();
    
    // Group by metric name and calculate stats
    const groupedMetrics = {};
    metrics.forEach(metric => {
      const name = metric.metric_name;
      if (!groupedMetrics[name]) {
        groupedMetrics[name] = {
          name,
          unit: metric.unit,
          values: [],
          avg: 0,
          min: Number.MAX_VALUE,
          max: 0,
          latest: 0
        };
      }
      
      const value = metric.value;
      groupedMetrics[name].values.push({
        timestamp: metric.timestamp,
        value: value
      });
      groupedMetrics[name].min = Math.min(groupedMetrics[name].min, value);
      groupedMetrics[name].max = Math.max(groupedMetrics[name].max, value);
      groupedMetrics[name].latest = value;
    });
    
    // Calculate averages
    Object.values(groupedMetrics).forEach(metric => {
      if (metric.values.length > 0) {
        metric.avg = metric.values.reduce((sum, v) => sum + v.value, 0) / metric.values.length;
        metric.avg = Math.round(metric.avg * 100) / 100;
      }
    });
    
    res.json({
      metrics: Object.values(groupedMetrics),
      hours_queried: hours,
      total_data_points: metrics.length
    });
    
  } catch (error) {
    logger.error('Error fetching performance metrics:', error);
    res.status(500).json({ error: 'Failed to fetch performance metrics' });
  }
});

// Get active MQTT connections (from sessions collection)
app.get('/api/connections', async (req, res) => {
  try {
    if (!isConnected) {
      return res.status(503).json({ error: 'Database not connected' });
    }
    
    // Query active sessions (not expired)
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
    const activeSessions = await db.collection('sessions')
      .find({ 
        created_at: { $gte: oneHourAgo }
      })
      .sort({ created_at: -1 })
      .limit(50)
      .toArray();
    
    // Transform for frontend
    const connections = activeSessions.map(session => ({
      session_id: session._id,
      broker: session.broker,
      port: session.port,
      client_id: session.client_id,
      created_at: session.created_at,
      last_accessed: session.last_accessed,
      is_active: true // If in DB and not expired, it's active
    }));
    
    res.json({
      connections,
      total_active: connections.length
    });
    
  } catch (error) {
    logger.error('Error fetching connections:', error);
    res.status(500).json({ error: 'Failed to fetch connections' });
  }
});

// Health check with real data
app.get('/api/health', async (req, res) => {
  try {
    const health = {
      status: 'healthy',
      timestamp: new Date(),
      database: {
        connected: isConnected,
        collections: []
      },
      mcp_server: {
        recent_tool_calls: 0,
        recent_errors: 0,
        uptime_minutes: 0
      }
    };
    
    if (isConnected) {
      // Check collections exist and get counts
      try {
        const toolCallsCount = await db.collection('mcp_tool_calls').countDocuments({});
        const systemLogsCount = await db.collection('mcp_system_logs').countDocuments({});
        const metricsCount = await db.collection('mcp_performance_metrics').countDocuments({});
        const sessionsCount = await db.collection('sessions').countDocuments({});
        
        health.database.collections = [
          { name: 'mcp_tool_calls', count: toolCallsCount },
          { name: 'mcp_system_logs', count: systemLogsCount },
          { name: 'mcp_performance_metrics', count: metricsCount },
          { name: 'sessions', count: sessionsCount }
        ];
        
        // Recent activity (last hour)
        const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
        const recentCalls = await db.collection('mcp_tool_calls')
          .countDocuments({ timestamp: { $gte: oneHourAgo } });
        const recentErrors = await db.collection('mcp_system_logs')
          .countDocuments({ 
            timestamp: { $gte: oneHourAgo },
            level: 'ERROR'
          });
        
        health.mcp_server.recent_tool_calls = recentCalls;
        health.mcp_server.recent_errors = recentErrors;
        
        // Estimate uptime from first log entry
        const firstLog = await db.collection('mcp_system_logs')
          .findOne({ event_type: 'server_start' }, { sort: { timestamp: -1 } });
        if (firstLog) {
          health.mcp_server.uptime_minutes = Math.round(
            (Date.now() - firstLog.timestamp.getTime()) / (1000 * 60)
          );
        }
        
      } catch (dbError) {
        health.database.error = dbError.message;
      }
    }
    
    res.json(health);
    
  } catch (error) {
    logger.error('Error getting health status:', error);
    res.status(500).json({ 
      status: 'unhealthy',
      error: error.message,
      timestamp: new Date()
    });
  }
});

// WebSocket connection handling
io.on('connection', (socket) => {
  logger.info(`Client connected: ${socket.id}`);
  
  // Send initial connection confirmation
  socket.emit('connected', {
    message: 'Connected to MQTT MCP Frontend',
    timestamp: new Date(),
    realTimeUpdates: false // No change streams available
  });
  
  // Simple heartbeat every 30 seconds
  const heartbeat = setInterval(() => {
    socket.emit('heartbeat', { timestamp: new Date() });
  }, 30000);
  
  socket.on('disconnect', () => {
    logger.info(`Client disconnected: ${socket.id}`);
    clearInterval(heartbeat);
  });
  
  // Handle manual refresh requests
  socket.on('refresh_data', async (type) => {
    try {
      if (type === 'tool_calls') {
        const toolCalls = await db.collection('mcp_tool_calls')
          .find({})
          .sort({ timestamp: -1 })
          .limit(50)
          .toArray();
        socket.emit('tool_calls_data', toolCalls);
      }
    } catch (error) {
      logger.error('Error handling refresh request:', error);
    }
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