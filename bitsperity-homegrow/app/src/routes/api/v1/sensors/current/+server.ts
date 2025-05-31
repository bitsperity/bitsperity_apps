import { json, type RequestHandler } from '@sveltejs/kit';
import { findDevices, findLatestSensorData } from '$lib/server/db.js';
import type { CurrentSensorData } from '$lib/types/sensor.js';

export const GET: RequestHandler = async ({ url }) => {
  try {
    const deviceId = url.searchParams.get('device_id');
    
    if (deviceId) {
      // Get current sensor data for specific device
      const sensorData = await findLatestSensorData(deviceId, 4); // pH, TDS, temp, water_level
      
      const currentData: CurrentSensorData = {
        device_id: deviceId,
        last_updated: new Date().toISOString()
      };
      
      // Group by sensor type and get the latest reading for each
      sensorData.forEach(reading => {
        const sensorReading = {
          device_id: reading.device_id,
          sensor_type: reading.sensor_type,
          value: reading.value,
          unit: reading.unit,
          quality: reading.quality,
          timestamp: reading.timestamp.toISOString(),
          raw_value: reading.raw_value
        };
        
        switch (reading.sensor_type) {
          case 'ph':
            currentData.ph = sensorReading;
            break;
          case 'tds':
            currentData.tds = sensorReading;
            break;
          case 'temperature':
            currentData.temperature = sensorReading;
            break;
          case 'water_level':
            currentData.water_level = sensorReading;
            break;
        }
      });
      
      return json(currentData);
    } else {
      // Get current sensor data for all devices
      const devices = await findDevices();
      const allCurrentData: CurrentSensorData[] = [];
      
      for (const device of devices) {
        const sensorData = await findLatestSensorData(device.device_id, 4);
        
        const currentData: CurrentSensorData = {
          device_id: device.device_id,
          last_updated: new Date().toISOString()
        };
        
        sensorData.forEach(reading => {
          const sensorReading = {
            device_id: reading.device_id,
            sensor_type: reading.sensor_type,
            value: reading.value,
            unit: reading.unit,
            quality: reading.quality,
            timestamp: reading.timestamp.toISOString(),
            raw_value: reading.raw_value
          };
          
          switch (reading.sensor_type) {
            case 'ph':
              currentData.ph = sensorReading;
              break;
            case 'tds':
              currentData.tds = sensorReading;
              break;
            case 'temperature':
              currentData.temperature = sensorReading;
              break;
            case 'water_level':
              currentData.water_level = sensorReading;
              break;
          }
        });
        
        allCurrentData.push(currentData);
      }
      
      return json(allCurrentData);
    }
  } catch (error) {
    console.error('API Error - GET /api/v1/sensors/current:', error);
    return json(
      { error: 'Failed to fetch current sensor data' }, 
      { status: 500 }
    );
  }
}; 