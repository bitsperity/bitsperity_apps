import type { Handle } from '@sveltejs/kit';
import { mqttService } from '$lib/server/mqtt.js';
import { dev } from '$app/environment';

// Initialize MQTT service on server startup
console.log('Initializing MQTT service...');

// Start MQTT simulator in development mode
if (dev) {
  console.log('Development mode: Starting MQTT simulator...');
  // Dynamic import to avoid issues in production
  import('$lib/server/mqtt-simulator.js').then(() => {
    console.log('✅ MQTT Simulator started (2 simulated ESP32 devices)');
  }).catch(err => {
    console.error('Failed to start MQTT simulator:', err);
  });
}

export const handle: Handle = async ({ event, resolve }) => {
  // Add MQTT status to locals for API access
  event.locals.mqtt = {
    isConnected: () => mqttService.isConnected(),
    getStatus: () => mqttService.getStatus(),
    sendCommand: (deviceId: string, command: any) => mqttService.sendCommand(deviceId, command)
  };

  const response = await resolve(event);
  return response;
}; 