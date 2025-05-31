import { json, type RequestHandler } from '@sveltejs/kit';
import { findDevices, insertDevice } from '$lib/server/db.js';

export const GET: RequestHandler = async () => {
  try {
    const devices = await findDevices();
    return json(devices);
  } catch (error) {
    console.error('API Error - GET /api/v1/devices:', error);
    return json(
      { error: 'Failed to fetch devices' }, 
      { status: 500 }
    );
  }
};

export const POST: RequestHandler = async ({ request }) => {
  try {
    const deviceData = await request.json();
    
    // Validation
    if (!deviceData.device_id || !deviceData.name || !deviceData.type) {
      return json(
        { error: 'Missing required fields: device_id, name, type' }, 
        { status: 400 }
      );
    }

    const result = await insertDevice(deviceData);
    return json({ 
      success: true, 
      id: result.insertedId,
      device_id: deviceData.device_id 
    });
  } catch (error) {
    console.error('API Error - POST /api/v1/devices:', error);
    return json(
      { error: 'Failed to create device' }, 
      { status: 500 }
    );
  }
}; 