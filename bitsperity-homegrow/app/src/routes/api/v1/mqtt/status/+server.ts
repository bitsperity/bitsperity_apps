import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ locals }) => {
  try {
    const mqttStatus = locals.mqtt.getStatus();
    
    return json({
      success: true,
      data: {
        ...mqttStatus,
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    console.error('Error getting MQTT status:', error);
    return json(
      { 
        success: false, 
        error: 'Failed to get MQTT status',
        data: {
          connected: false,
          reconnectAttempts: 0,
          topics: [],
          timestamp: new Date().toISOString()
        }
      }, 
      { status: 500 }
    );
  }
}; 