export const config = {
  mqtt: {
    host: process.env.MQTT_HOST || 'localhost',
    port: parseInt(process.env.MQTT_PORT || '1883'),
    clientId: `homegrow-mqtt-bridge-${Date.now()}`,
    username: process.env.MQTT_USERNAME,
    password: process.env.MQTT_PASSWORD,
    reconnectPeriod: 5000,
    connectTimeout: 30000,
    clean: true,
    topics: {
      // Sensor data topics
      sensorData: 'homegrow/devices/+/sensors/+',
      // Command topics
      commands: 'homegrow/devices/+/commands',
      commandResponses: 'homegrow/devices/+/commands/response',
      // System topics
      heartbeat: 'homegrow/devices/+/heartbeat',
      status: 'homegrow/devices/+/status',
      logs: 'homegrow/devices/+/logs',
      // Configuration topics
      configRequest: 'homegrow/devices/+/config/request',
      configResponse: 'homegrow/devices/+/config/response',
      // Discovery topics
      discovery: 'homegrow/discovery/+',
      // Program topics
      programStatus: 'homegrow/programs/+/status',
      programLogs: 'homegrow/programs/+/logs'
    }
  },
  
  mongodb: {
    uri: process.env.MONGODB_URI || 'mongodb://localhost:27017',
    database: process.env.MONGODB_DATABASE || 'homegrow',
    options: {
      maxPoolSize: 10,
      minPoolSize: 2,
      serverSelectionTimeoutMS: 5000,
      socketTimeoutMS: 45000,
    },
    collections: {
      devices: 'devices',
      sensorData: 'sensor_data',
      commands: 'device_commands',
      pumpStatus: 'pump_status',
      systemLogs: 'system_logs',
      programs: 'programs',
      programInstances: 'program_instances',
      automationRules: 'automation_rules',
      notifications: 'notifications'
    }
  },
  
  dataRetention: {
    // Hot data: Full resolution for 7 days
    hotDataDays: 7,
    // Warm data: Hourly aggregates for 30 days
    warmDataDays: 30,
    // Cold data: Daily aggregates after 30 days
    coldDataDays: 365,
    // Cleanup interval in milliseconds (daily)
    cleanupInterval: 24 * 60 * 60 * 1000
  },
  
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    format: process.env.LOG_FORMAT || 'json',
    maxFiles: 5,
    maxSize: '10m'
  }
}; 