import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { wsService } from '$lib/server/websocket.js';

export const GET: RequestHandler = async () => {
  try {
    const wsStatus = wsService.getStatus();
    
    return json({
      success: true,
      data: {
        ...wsStatus,
        endpoint: '/ws',
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    console.error('Error getting WebSocket status:', error);
    return json(
      { 
        success: false, 
        error: 'Failed to get WebSocket status',
        data: {
          initialized: false,
          connectedClients: 0,
          clients: [],
          endpoint: '/ws',
          timestamp: new Date().toISOString()
        }
      }, 
      { status: 500 }
    );
  }
}; 