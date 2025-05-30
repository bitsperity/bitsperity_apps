import { MongoClient } from 'mongodb';

class DatabaseConfig {
  constructor() {
    this.client = null;
    this.db = null;
    this.connectionString = process.env.MONGODB_URL || 'mongodb://bitsperity-mongodb:27017/homegrow';
  }

  async connect() {
    try {
      this.client = new MongoClient(this.connectionString, {
        maxPoolSize: 10,
        serverSelectionTimeoutMS: 5000,
        socketTimeoutMS: 45000,
      });

      await this.client.connect();
      this.db = this.client.db('homegrow');
      
      console.log('✅ MongoDB connected successfully');
      
      // Create indexes
      await this.createIndexes();
      
      return this.db;
    } catch (error) {
      console.error('❌ MongoDB connection failed:', error);
      throw error;
    }
  }

  async createIndexes() {
    try {
      // Device indexes
      await this.db.collection('devices').createIndex({ device_id: 1 }, { unique: true });
      await this.db.collection('devices').createIndex({ status: 1 });
      await this.db.collection('devices').createIndex({ last_seen: 1 });
      await this.db.collection('devices').createIndex({ 'beacon.service_id': 1 });

      // Sensor data indexes
      await this.db.collection('sensor_data').createIndex({ 
        device_id: 1, 
        sensor_type: 1, 
        timestamp: -1 
      });
      
      // TTL index for automatic data cleanup (30 days)
      await this.db.collection('sensor_data').createIndex(
        { timestamp: 1 }, 
        { expireAfterSeconds: 30 * 24 * 60 * 60 }
      );

      // Command indexes
      await this.db.collection('device_commands').createIndex({ device_id: 1, timestamp: -1 });
      await this.db.collection('device_commands').createIndex({ command_id: 1 }, { unique: true });
      await this.db.collection('device_commands').createIndex({ status: 1 });

      // Program indexes
      await this.db.collection('program_templates').createIndex({ name: 1 });
      await this.db.collection('program_instances').createIndex({ device_id: 1, status: 1 });
      await this.db.collection('program_instances').createIndex({ template_id: 1 });

      console.log('✅ Database indexes created');
    } catch (error) {
      console.warn('⚠️ Could not create indexes (auth required):', error.message);
      console.log('📝 Continuing without indexes for local testing...');
    }
  }

  getDb() {
    if (!this.db) {
      throw new Error('Database not connected. Call connect() first.');
    }
    return this.db;
  }

  async disconnect() {
    if (this.client) {
      await this.client.close();
      console.log('📴 MongoDB disconnected');
    }
  }

  async healthCheck() {
    try {
      await this.db.admin().ping();
      return { status: 'healthy', timestamp: new Date() };
    } catch (error) {
      return { status: 'unhealthy', error: error.message, timestamp: new Date() };
    }
  }
}

export default DatabaseConfig; 