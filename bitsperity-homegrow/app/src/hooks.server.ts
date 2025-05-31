import type { Handle } from '@sveltejs/kit';
import { mqttService } from '$lib/server/mqtt.js';
import { dev } from '$app/environment';

// Initialize MQTT service on server startup
console.log('Initializing MQTT service...');

// Start MQTT simulator (both dev and production until real ESP32 arrives)
// TODO: Remove simulator in production once real ESP32 devices are available
console.log(dev ? 'Development mode: Starting MQTT simulator...' : 'Production mode: Starting MQTT simulator (temporary until ESP32 delivery)...');

// Dynamic import to avoid issues in production
import('$lib/server/mqtt-simulator.js').then(() => {
  console.log('✅ MQTT Simulator started (2 simulated ESP32 devices)');
}).catch(err => {
  console.error('Failed to start MQTT simulator:', err);
});

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