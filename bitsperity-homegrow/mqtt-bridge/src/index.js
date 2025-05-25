import dotenv from 'dotenv';
import { MQTTBridge } from './services/mqtt-bridge.js';
import { logger } from './utils/logger.js';
import { config } from './config/index.js';

// Load environment variables
dotenv.config();

// Initialize and start the MQTT Bridge
async function start() {
  try {
    logger.info('Starting HomeGrow MQTT Bridge v3...');
    
    const bridge = new MQTTBridge(config);
    await bridge.start();
    
    logger.info('MQTT Bridge started successfully');
    
    // Graceful shutdown
    process.on('SIGTERM', async () => {
      logger.info('SIGTERM received, shutting down gracefully...');
      await bridge.stop();
      process.exit(0);
    });
    
    process.on('SIGINT', async () => {
      logger.info('SIGINT received, shutting down gracefully...');
      await bridge.stop();
      process.exit(0);
    });
    
  } catch (error) {
    logger.error('Failed to start MQTT Bridge:', error);
    process.exit(1);
  }
}

start(); 