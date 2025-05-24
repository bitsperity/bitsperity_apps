import bonjour from 'bonjour-service';
import { networkInterfaces } from 'os';

export class DiscoveryService {
  constructor(config, logger) {
    this.config = config;
    this.logger = logger;
    this.bonjourInstance = null;
    this.publishedServices = [];
  }

  async start() {
    try {
      this.logger.info('Starting HomeGrow Discovery Service...');
      
      // Skip mDNS in development to avoid system-level issues
      if (process.env.NODE_ENV === 'development') {
        this.logger.info('Discovery Service running in development mode - mDNS disabled');
        return;
      }
      
      // Initialize Bonjour/mDNS
      this.bonjourInstance = bonjour();
      
      // Get local IP address
      const localIP = this.getLocalIPAddress();
      
      // Define services to announce
      const services = [
        {
          name: 'HomeGrow-v3-API',
          type: 'http',
          port: parseInt(this.config.port) || 4000,
          txt: {
            version: '3.0.0',
            api: 'rest',
            features: 'sensors,automation,mqtt,websocket'
          }
        },
        {
          name: 'HomeGrow-v3-MQTT',
          type: 'mqtt',
          port: parseInt(this.config.mqttPort) || 1883,
          txt: {
            version: '3.0.0',
            protocol: 'mqtt',
            topics: 'homegrow/devices/+/sensors/+,homegrow/devices/+/status'
          }
        },
        {
          name: 'HomeGrow-v3-WebSocket',
          type: 'ws',
          port: parseInt(this.config.port) || 4000,
          txt: {
            version: '3.0.0',
            protocol: 'websocket',
            path: '/ws'
          }
        }
      ];

      // Publish each service
      for (const service of services) {
        await this.publishService(service, localIP);
      }

      this.logger.info(`Discovery Service started - announcing ${this.publishedServices.length} services on ${localIP}`);
      
    } catch (error) {
      this.logger.error('Failed to start Discovery Service:', error);
      throw error;
    }
  }

  async stop() {
    try {
      this.logger.info('Stopping Discovery Service...');
      
      // Unpublish all services
      for (const service of this.publishedServices) {
        service.stop();
        this.logger.debug(`Unpublished service: ${service.name}`);
      }
      
      // Destroy Bonjour instance
      if (this.bonjourInstance) {
        this.bonjourInstance.destroy();
      }
      
      this.publishedServices = [];
      this.logger.info('Discovery Service stopped');
      
    } catch (error) {
      this.logger.error('Error stopping Discovery Service:', error);
    }
  }

  async publishService(serviceConfig, ipAddress) {
    try {
      const service = this.bonjourInstance.publish({
        name: serviceConfig.name,
        type: serviceConfig.type,
        port: serviceConfig.port,
        host: ipAddress,
        txt: serviceConfig.txt || {}
      });

      this.publishedServices.push(service);
      
      this.logger.info(`Published service: ${serviceConfig.name} (${serviceConfig.type}) on ${ipAddress}:${serviceConfig.port}`);
      
      return service;
    } catch (error) {
      this.logger.error(`Failed to publish service ${serviceConfig.name}:`, error);
      throw error;
    }
  }

  getLocalIPAddress() {
    const interfaces = networkInterfaces();
    
    // Priority order for interface selection
    const priorityOrder = ['eth0', 'en0', 'wlan0', 'Wi-Fi', 'Ethernet'];
    
    // First try priority interfaces
    for (const ifaceName of priorityOrder) {
      const iface = interfaces[ifaceName];
      if (iface) {
        for (const alias of iface) {
          if (alias.family === 'IPv4' && !alias.internal) {
            this.logger.debug(`Using IP address from interface ${ifaceName}: ${alias.address}`);
            return alias.address;
          }
        }
      }
    }
    
    // Fallback: use any non-internal IPv4 address
    for (const ifaceName in interfaces) {
      const iface = interfaces[ifaceName];
      for (const alias of iface) {
        if (alias.family === 'IPv4' && !alias.internal) {
          this.logger.debug(`Using fallback IP address from interface ${ifaceName}: ${alias.address}`);
          return alias.address;
        }
      }
    }
    
    // Last resort
    this.logger.warn('Could not determine local IP address, using localhost');
    return '127.0.0.1';
  }

  // Browse for other HomeGrow instances on the network
  async browseServices(timeout = 5000) {
    return new Promise((resolve) => {
      const foundServices = [];
      
      const browser = this.bonjourInstance.find({ type: 'http' }, (service) => {
        if (service.name && service.name.includes('HomeGrow')) {
          foundServices.push({
            name: service.name,
            host: service.host,
            port: service.port,
            addresses: service.addresses,
            txt: service.txt || {}
          });
          
          this.logger.debug(`Found HomeGrow service: ${service.name} at ${service.host}:${service.port}`);
        }
      });

      // Stop browsing after timeout
      setTimeout(() => {
        browser.stop();
        resolve(foundServices);
      }, timeout);
    });
  }

  // Get service status for health checks
  getServiceStatus() {
    if (process.env.NODE_ENV === 'development') {
      return {
        isRunning: true,
        publishedServices: 0,
        mode: 'development',
        services: []
      };
    }
    
    return {
      isRunning: this.bonjourInstance !== null,
      publishedServices: this.publishedServices.length,
      services: this.publishedServices.map(service => ({
        name: service.name,
        type: service.type,
        port: service.port,
        published: service.published || false
      }))
    };
  }
} 