import { json, type RequestHandler } from '@sveltejs/kit';
import { findDeviceById, updateDevice, deleteDevice } from '$lib/server/db.js';

export const GET: RequestHandler = async ({ params }) => {
  try {
    if (!params.id) {
      return json(
        { error: 'Device ID is required' }, 
        { status: 400 }
      );
    }
    
    const device = await findDeviceById(params.id);
    
    if (!device) {
      return json(
        { error: 'Device not found' }, 
        { status: 404 }
      );
    }
    
    return json(device);
  } catch (error) {
    console.error('API Error - GET /api/v1/devices/[id]:', error);
    return json(
      { error: 'Failed to fetch device' }, 
      { status: 500 }
    );
  }
};

export const PUT: RequestHandler = async ({ params, request }) => {
  try {
    if (!params.id) {
      return json(
        { error: 'Device ID is required' }, 
        { status: 400 }
      );
    }
    
    const updates = await request.json();
    const success = await updateDevice(params.id, updates);
    
    if (!success) {
      return json(
        { error: 'Device not found or no changes made' }, 
        { status: 404 }
      );
    }
    
    return json({ success: true });
  } catch (error) {
    console.error('API Error - PUT /api/v1/devices/[id]:', error);
    return json(
      { error: 'Failed to update device' }, 
      { status: 500 }
    );
  }
};

export const DELETE: RequestHandler = async ({ params }) => {
  try {
    if (!params.id) {
      return json(
        { error: 'Device ID is required' }, 
        { status: 400 }
      );
    }
    
    const success = await deleteDevice(params.id);
    
    if (!success) {
      return json(
        { error: 'Device not found' }, 
        { status: 404 }
      );
    }
    
    return json({ success: true });
  } catch (error) {
    console.error('API Error - DELETE /api/v1/devices/[id]:', error);
    return json(
      { error: 'Failed to delete device' }, 
      { status: 500 }
    );
  }
}; 