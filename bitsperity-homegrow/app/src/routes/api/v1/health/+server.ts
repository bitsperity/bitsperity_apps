import { json, type RequestHandler } from '@sveltejs/kit';
import { testConnection } from '$lib/server/db.js';

export const GET: RequestHandler = async ({ locals }) => {
  try {
    const dbHealthy = await testConnection();
    const mqttHealthy = locals.mqtt.isConnected();
    
    const health = {
      status: (dbHealthy && mqttHealthy) ? 'healthy' : 'degraded',
      timestamp: new Date().toISOString(),
      services: {
        database: {
          status: dbHealthy ? 'connected' : 'disconnected',
          type: 'mongodb'
        },
        mqtt: {
          status: mqttHealthy ? 'connected' : 'disconnected',
          type: 'mosquitto'
        },
        api: {
          status: 'running',
          version: '1.0.0'
        }
      },
      uptime: process.uptime(),
      memory: {
        used: Math.round(process.memoryUsage().heapUsed / 1024 / 1024),
        total: Math.round(process.memoryUsage().heapTotal / 1024 / 1024)
      }
    };
    
    const statusCode = (dbHealthy && mqttHealthy) ? 200 : 503;
    return json(health, { status: statusCode });
  } catch (error) {
    console.error('API Error - GET /api/v1/health:', error);
    return json(
      { 
        status: 'error',
        timestamp: new Date().toISOString(),
        error: 'Health check failed' 
      }, 
      { status: 500 }
    );
  }
}; 