const EventEmitter = require('events');
const WebSocket = require('ws');

class BeaconServiceDiscovery extends EventEmitter {
  constructor(beaconUrl = 'http://bitsperity-beacon:8080') {
    super();
    this.beaconUrl = beaconUrl;
    this.serviceId = null;
    this.discoveredDevices = new Map();
    this.wsConnection = null;
    this.heartbeatInterval = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.isInitialized = false;
  }

  async initialize() {
    try {
      await this.registerHomeGrowServer();
      await this.discoverExistingDevices();
      this.connectWebSocket();
      this.startHeartbeat();
      
      this.isInitialized = true;
      console.log('✅ Beacon Service Discovery initialized successfully');
      return true;
    } catch (error) {
      console.warn('⚠️ Beacon Service Discovery initialization failed:', error.message);
      console.warn('📱 Continuing without service discovery...');
      return false;
    }
  }

  async registerHomeGrowServer() {
    const serviceData = {
      name: "homegrow-server",
      type: "web",
      host: process.env.HOMEGROW_HOST || "homegrow-app",
      port: parseInt(process.env.HOMEGROW_PORT) || 3000,
      protocol: "http",
      tags: ["homegrow", "hydroponics", "web-interface", "management"],
      metadata: {
        version: "3.0.0",
        description: "HomeGrow Hydroponic Management Server",
        capabilities: ["device_management", "monitoring", "automation"],
        endpoints: {
          api: "/api/v1",
          websocket: "/ws",
          dashboard: "/"
        },
        supported_clients: ["homegrow-client-v3"]
      },
      ttl: 300
    };

    const response = await fetch(`${this.beaconUrl}/api/v1/services/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(serviceData)
    });

    if (!response.ok) {
      throw new Error(`Registration failed: ${response.status}`);
    }

    const result = await response.json();
    this.serviceId = result.service_id;
    
    console.log(`🚀 HomeGrow Server registered with Beacon: ${this.serviceId}`);
    return result;
  }

  async discoverExistingDevices() {
    const response = await fetch(
      `${this.beaconUrl}/api/v1/services/discover?type=iot&tags=homegrow`
    );

    if (!response.ok) {
      throw new Error(`Discovery failed: ${response.status}`);
    }

    const services = await response.json();
    
    for (const service of services) {
      if (service.tags.includes('homegrow') && service.name.startsWith('homegrow-client')) {
        this.handleDeviceDiscovered(service);
      }
    }

    console.log(`🔍 Discovered ${this.discoveredDevices.size} existing HomeGrow devices`);
  }

  connectWebSocket() {
    try {
      const wsUrl = this.beaconUrl.replace('http', 'ws') + '/api/v1/ws';
      this.wsConnection = new WebSocket(wsUrl);

      this.wsConnection.on('open', () => {
        console.log('🔌 WebSocket connection to Beacon established');
        this.reconnectAttempts = 0;
      });

      this.wsConnection.on('message', (data) => {
        try {
          const update = JSON.parse(data.toString());
          this.handleWebSocketMessage(update);
        } catch (error) {
          console.error('❌ Error parsing WebSocket message:', error);
        }
      });

      this.wsConnection.on('close', () => {
        console.log('📴 WebSocket connection to Beacon closed');
        this.scheduleReconnect();
      });

      this.wsConnection.on('error', (error) => {
        console.error('❌ WebSocket error:', error);
      });

    } catch (error) {
      console.warn('⚠️ Failed to establish WebSocket connection:', error);
      this.scheduleReconnect();
    }
  }

  handleWebSocketMessage(update) {
    switch (update.type) {
      case 'service_registered':
        if (this.isHomeGrowClient(update.service)) {
          this.handleDeviceDiscovered(update.service);
        }
        break;
        
      case 'service_deregistered':
        this.handleDeviceRemoved(update.service_id);
        break;
        
      case 'service_updated':
        if (this.isHomeGrowClient(update.service)) {
          this.handleDeviceUpdated(update.service);
        }
        break;
    }
  }

  isHomeGrowClient(service) {
    return service.tags.includes('homegrow') && 
           service.name.startsWith('homegrow-client') &&
           service.type === 'iot';
  }

  handleDeviceDiscovered(service) {
    const deviceInfo = {
      service_id: service.service_id,
      device_id: this.extractDeviceId(service.name),
      name: service.name,
      host: service.host,
      port: service.port,
      metadata: service.metadata,
      last_seen: new Date(service.updated_at),
      status: 'online'
    };

    this.discoveredDevices.set(service.service_id, deviceInfo);
    
    console.log(`🆕 New HomeGrow device discovered: ${deviceInfo.device_id}`);
    this.emit('device_discovered', deviceInfo);
  }

  handleDeviceUpdated(service) {
    if (this.discoveredDevices.has(service.service_id)) {
      const deviceInfo = this.discoveredDevices.get(service.service_id);
      deviceInfo.last_seen = new Date(service.updated_at);
      deviceInfo.metadata = service.metadata;
      
      this.emit('device_updated', deviceInfo);
    }
  }

  handleDeviceRemoved(serviceId) {
    const deviceInfo = this.discoveredDevices.get(serviceId);
    if (deviceInfo) {
      this.discoveredDevices.delete(serviceId);
      console.log(`📤 HomeGrow device removed: ${deviceInfo.device_id}`);
      this.emit('device_removed', deviceInfo);
    }
  }

  extractDeviceId(serviceName) {
    // Extract device ID from service name like "homegrow-client-001"
    const match = serviceName.match(/homegrow-client-(.+)$/);
    return match ? match[1] : serviceName;
  }

  startHeartbeat() {
    if (this.serviceId) {
      this.heartbeatInterval = setInterval(async () => {
        try {
          const response = await fetch(
            `${this.beaconUrl}/api/v1/services/${this.serviceId}/heartbeat`,
            { method: 'PUT' }
          );
          
          if (!response.ok) {
            console.warn(`💓 Heartbeat failed: ${response.status}`);
          }
        } catch (error) {
          console.warn('💓 Heartbeat error:', error.message);
        }
      }, 60000); // Every 60 seconds
    }
  }

  scheduleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      const delay = Math.pow(2, this.reconnectAttempts) * 1000; // Exponential backoff
      this.reconnectAttempts++;
      
      setTimeout(() => {
        console.log(`🔄 Attempting to reconnect to Beacon (attempt ${this.reconnectAttempts})`);
        this.connectWebSocket();
      }, delay);
    } else {
      console.error('❌ Max reconnection attempts reached. Service discovery disabled.');
    }
  }

  getDiscoveredDevices() {
    return Array.from(this.discoveredDevices.values());
  }

  getDeviceByServiceId(serviceId) {
    return this.discoveredDevices.get(serviceId);
  }

  getDeviceByDeviceId(deviceId) {
    for (const device of this.discoveredDevices.values()) {
      if (device.device_id === deviceId) {
        return device;
      }
    }
    return null;
  }

  isDeviceDiscovered(deviceId) {
    return this.getDeviceByDeviceId(deviceId) !== null;
  }

  async refreshDiscovery() {
    try {
      await this.discoverExistingDevices();
      return this.getDiscoveredDevices();
    } catch (error) {
      console.error('❌ Failed to refresh discovery:', error);
      return [];
    }
  }

  async shutdown() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }
    
    if (this.wsConnection) {
      this.wsConnection.close();
    }
    
    if (this.serviceId) {
      try {
        await fetch(`${this.beaconUrl}/api/v1/services/${this.serviceId}`, {
          method: 'DELETE'
        });
        console.log('📴 HomeGrow Server deregistered from Beacon');
      } catch (error) {
        console.warn('⚠️ Failed to deregister from Beacon:', error);
      }
    }
  }

  getStatus() {
    return {
      initialized: this.isInitialized,
      service_id: this.serviceId,
      discovered_devices: this.discoveredDevices.size,
      websocket_connected: this.wsConnection?.readyState === WebSocket.OPEN,
      reconnect_attempts: this.reconnectAttempts
    };
  }
}

module.exports = BeaconServiceDiscovery;