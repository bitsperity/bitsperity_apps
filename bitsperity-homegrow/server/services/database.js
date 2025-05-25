import { MongoClient } from 'mongodb';

export class DatabaseService {
  constructor(connectionString) {
    this.connectionString = connectionString;
    this.client = null;
    this.db = null;
  }

  async connect() {
    try {
      this.client = new MongoClient(this.connectionString, {
        maxPoolSize: 10,
        serverSelectionTimeoutMS: 5000,
        socketTimeoutMS: 45000,
      });

      await this.client.connect();
      this.db = this.client.db();
      
      // Test connection
      await this.db.admin().ping();
      
      console.log('Connected to MongoDB successfully');
      return true;
    } catch (error) {
      console.error('Failed to connect to MongoDB:', error);
      throw error;
    }
  }

  async disconnect() {
    if (this.client) {
      await this.client.close();
      console.log('Disconnected from MongoDB');
    }
  }

  async createIndexes() {
    try {
      // Device indexes
      await this.db.collection('devices').createIndex({ device_id: 1 }, { unique: true });
      await this.db.collection('devices').createIndex({ status: 1 });
      await this.db.collection('devices').createIndex({ last_seen: 1 });

      // Sensor data indexes
      await this.db.collection('sensor_data').createIndex({ 
        device_id: 1, 
        sensor_type: 1, 
        timestamp: -1 
      });
      await this.db.collection('sensor_data').createIndex(
        { timestamp: 1 }, 
        { expireAfterSeconds: 30 * 24 * 60 * 60 } // 30 days TTL
      );

      // Command indexes
      await this.db.collection('device_commands').createIndex({ device_id: 1, timestamp: -1 });
      await this.db.collection('device_commands').createIndex({ status: 1 });

      console.log('Database indexes created successfully');
    } catch (error) {
      console.error('Error creating indexes:', error);
    }
  }

  getCollection(name) {
    return this.db.collection(name);
  }
} 