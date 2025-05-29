const EventEmitter = require('events');

class WebSocketService extends EventEmitter {
  constructor() {
    super();
    this.connections = new Map(); // connectionId -> { socket, subscriptions }
    this.deviceSubscriptions = new Map(); // deviceId -> Set of connectionIds
  }

  handleConnection(connection, req) {
    const connectionId = this.generateConnectionId();
    
    this.connections.set(connectionId, {
      socket: connection.socket,
      subscriptions: new Set(),
      connectedAt: new Date()
    });

    console.log(`🔌 WebSocket client connected: ${connectionId}`);

    // Handle messages
    connection.socket.on('message', message => {
      this.handleMessage(connectionId, message);
    });

    // Handle disconnect
    connection.socket.on('close', () => {
      this.handleDisconnect(connectionId);
    });

    // Send welcome message
    this.sendToConnection(connectionId, {
      type: 'connected',
      connectionId,
      timestamp: new Date()
    });
  }

  handleMessage(connectionId, message) {
    try {
      const data = JSON.parse(message);
      
      switch (data.type) {
        case 'subscribe_device':
          this.subscribeToDevice(connectionId, data.deviceId);
          break;
          
        case 'unsubscribe_device':
          this.unsubscribeFromDevice(connectionId, data.deviceId);
          break;
          
        case 'ping':
          this.sendToConnection(connectionId, { type: 'pong', timestamp: Date.now() });
          break;
          
        default:
          console.warn(`Unknown message type: ${data.type}`);
      }
    } catch (error) {
      console.error('❌ WebSocket message error:', error);
      this.sendToConnection(connectionId, {
        type: 'error',
        message: 'Invalid message format'
      });
    }
  }

  subscribeToDevice(connectionId, deviceId) {
    const connection = this.connections.get(connectionId);
    if (!connection) return;

    // Add to connection's subscriptions
    connection.subscriptions.add(deviceId);

    // Add to device subscription map
    if (!this.deviceSubscriptions.has(deviceId)) {
      this.deviceSubscriptions.set(deviceId, new Set());
    }
    this.deviceSubscriptions.get(deviceId).add(connectionId);

    console.log(`📡 Client ${connectionId} subscribed to device: ${deviceId}`);

    // Send confirmation
    this.sendToConnection(connectionId, {
      type: 'subscribed',
      deviceId,
      timestamp: new Date()
    });
  }

  unsubscribeFromDevice(connectionId, deviceId) {
    const connection = this.connections.get(connectionId);
    if (!connection) return;

    // Remove from connection's subscriptions
    connection.subscriptions.delete(deviceId);

    // Remove from device subscription map
    const deviceSubs = this.deviceSubscriptions.get(deviceId);
    if (deviceSubs) {
      deviceSubs.delete(connectionId);
      if (deviceSubs.size === 0) {
        this.deviceSubscriptions.delete(deviceId);
      }
    }

    console.log(`📴 Client ${connectionId} unsubscribed from device: ${deviceId}`);
  }

  handleDisconnect(connectionId) {
    const connection = this.connections.get(connectionId);
    if (!connection) return;

    // Clean up all subscriptions
    for (const deviceId of connection.subscriptions) {
      const deviceSubs = this.deviceSubscriptions.get(deviceId);
      if (deviceSubs) {
        deviceSubs.delete(connectionId);
        if (deviceSubs.size === 0) {
          this.deviceSubscriptions.delete(deviceId);
        }
      }
    }

    // Remove connection
    this.connections.delete(connectionId);
    console.log(`📴 WebSocket client disconnected: ${connectionId}`);
  }

  // Broadcast methods for real-time updates
  broadcastSensorData(deviceId, sensorType, data) {
    this.broadcastToDevice(deviceId, {
      type: 'sensor_data',
      deviceId,
      sensorType,
      data,
      timestamp: new Date()
    });
  }

  broadcastDeviceStatus(deviceId, status) {
    this.broadcastToDevice(deviceId, {
      type: 'device_status',
      deviceId,
      status,
      timestamp: new Date()
    });
  }

  broadcastCommandResponse(deviceId, commandId, response) {
    this.broadcastToDevice(deviceId, {
      type: 'command_response',
      deviceId,
      commandId,
      response,
      timestamp: new Date()
    });
  }

  broadcastDeviceDiscovered(deviceInfo) {
    this.broadcastToAll({
      type: 'device_discovered',
      device: deviceInfo,
      timestamp: new Date()
    });
  }

  broadcastProgramUpdate(programId, update) {
    this.broadcastToAll({
      type: 'program_update',
      programId,
      update,
      timestamp: new Date()
    });
  }

  // Helper methods
  broadcastToDevice(deviceId, message) {
    const subscribers = this.deviceSubscriptions.get(deviceId);
    if (!subscribers) return;

    for (const connectionId of subscribers) {
      this.sendToConnection(connectionId, message);
    }
  }

  broadcastToAll(message) {
    for (const [connectionId] of this.connections) {
      this.sendToConnection(connectionId, message);
    }
  }

  sendToConnection(connectionId, message) {
    const connection = this.connections.get(connectionId);
    if (!connection || connection.socket.readyState !== 1) return; // 1 = OPEN

    try {
      connection.socket.send(JSON.stringify(message));
    } catch (error) {
      console.error(`❌ Error sending to ${connectionId}:`, error);
    }
  }

  generateConnectionId() {
    return `ws_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  getStatus() {
    return {
      connections: this.connections.size,
      device_subscriptions: this.deviceSubscriptions.size,
      total_subscriptions: Array.from(this.connections.values())
        .reduce((sum, conn) => sum + conn.subscriptions.size, 0)
    };
  }
}

module.exports = WebSocketService; 