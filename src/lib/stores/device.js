import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

function createDeviceStore() {
  const { subscribe, set, update } = writable({
    devices: [],
    selectedDevice: null,
    loading: false,
    error: null,
    lastUpdate: null
  });

  return {
    subscribe,
    
    async initialize() {
      if (!browser) return;
      
      update(state => ({ ...state, loading: true, error: null }));
      
      try {
        const response = await fetch('/api/v1/devices');
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        update(state => ({
          ...state,
          devices: data.data || [],
          loading: false,
          lastUpdate: new Date()
        }));
      } catch (error) {
        console.error('Device initialization failed:', error);
        update(state => ({
          ...state,
          loading: false,
          error: error.message
        }));
      }
    },

    async createDevice(deviceData) {
      try {
        const response = await fetch('/api/v1/devices', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(deviceData)
        });
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        update(state => ({
          ...state,
          devices: [...state.devices, data.data]
        }));
        
        return data.data;
      } catch (error) {
        update(state => ({ ...state, error: error.message }));
        throw error;
      }
    },

    async updateDevice(deviceId, updates) {
      try {
        const response = await fetch(`/api/v1/devices/${deviceId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updates)
        });
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        update(state => ({
          ...state,
          devices: state.devices.map(device => 
            device.device_id === deviceId 
              ? { ...device, ...updates }
              : device
          )
        }));
      } catch (error) {
        update(state => ({ ...state, error: error.message }));
        throw error;
      }
    },

    async deleteDevice(deviceId) {
      try {
        const response = await fetch(`/api/v1/devices/${deviceId}`, {
          method: 'DELETE'
        });
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        update(state => ({
          ...state,
          devices: state.devices.filter(device => device.device_id !== deviceId),
          selectedDevice: state.selectedDevice?.device_id === deviceId ? null : state.selectedDevice
        }));
      } catch (error) {
        update(state => ({ ...state, error: error.message }));
        throw error;
      }
    },

    async discoverDevices() {
      try {
        const response = await fetch('/api/v1/devices/discover', {
          method: 'POST'
        });
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Refresh device list after discovery
        await this.initialize();
        
        return data;
      } catch (error) {
        update(state => ({ ...state, error: error.message }));
        throw error;
      }
    },

    selectDevice(deviceId) {
      update(state => ({
        ...state,
        selectedDevice: state.devices.find(d => d.device_id === deviceId) || null
      }));
    },

    updateDeviceStatus(deviceId, status, lastSeen = new Date()) {
      update(state => ({
        ...state,
        devices: state.devices.map(device =>
          device.device_id === deviceId
            ? { ...device, status, last_seen: lastSeen }
            : device
        )
      }));
    },

    addDevice(device) {
      update(state => ({
        ...state,
        devices: [...state.devices, device]
      }));
    },

    removeDevice(deviceId) {
      update(state => ({
        ...state,
        devices: state.devices.filter(d => d.device_id !== deviceId),
        selectedDevice: state.selectedDevice?.device_id === deviceId ? null : state.selectedDevice
      }));
    },

    clearError() {
      update(state => ({ ...state, error: null }));
    }
  };
}

export const deviceStore = createDeviceStore();

// Derived stores for computed values
export const onlineDevices = derived(
  deviceStore,
  $deviceStore => $deviceStore.devices.filter(d => d.status === 'online')
);

export const offlineDevices = derived(
  deviceStore,
  $deviceStore => $deviceStore.devices.filter(d => d.status === 'offline')
);

export const deviceCount = derived(
  deviceStore,
  $deviceStore => ({
    total: $deviceStore.devices.length,
    online: $deviceStore.devices.filter(d => d.status === 'online').length,
    offline: $deviceStore.devices.filter(d => d.status === 'offline').length
  })
); 