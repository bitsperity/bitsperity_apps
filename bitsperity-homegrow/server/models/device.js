import { ObjectId } from 'mongodb';

export class DeviceModel {
  constructor(db) {
    this.collection = db.collection('devices');
    this.createIndexes();
  }

  async createIndexes() {
    await this.collection.createIndex({ device_id: 1 }, { unique: true });
    await this.collection.createIndex({ status: 1 });
    await this.collection.createIndex({ last_seen: 1 });
    await this.collection.createIndex({ 'beacon.service_id': 1 });
  }

  async create(deviceData) {
    const device = {
      device_id: deviceData.device_id,
      name: deviceData.name || `Device ${deviceData.device_id}`,
      type: deviceData.type || 'homegrow-client',
      location: deviceData.location || '',
      description: deviceData.description || '',
      status: 'offline',
      created_at: new Date(),
      updated_at: new Date(),
      last_seen: null,
      config: {
        wifi: {
          ssid: '',
          signal_strength: 0
        },
        mqtt: {
          broker: process.env.MQTT_URL || 'mqtt://umbrel-mqtt:1883',
          topics: {
            sensors: `homegrow/devices/${deviceData.device_id}/sensors`,
            commands: `homegrow/devices/${deviceData.device_id}/commands`,
            heartbeat: `homegrow/devices/${deviceData.device_id}/heartbeat`
          }
        },
        sensors: {
          ph: {
            enabled: true,
            calibration: {
              point_4: 1854,
              point_7: 1654,
              point_10: 1454,
              last_calibrated: null
            },
            filter: {
              type: 'moving_average',
              window_size: 10
            }
          },
          tds: {
            enabled: true,
            calibration: {
              reference_value: 1413,
              last_calibrated: null
            },
            filter: {
              type: 'moving_average',
              window_size: 10
            }
          }
        },
        actuators: {
          pumps: {
            water: { enabled: true, flow_rate_ml_per_sec: 10, max_runtime_sec: 300 },
            air: { enabled: true, flow_rate_ml_per_sec: 0, max_runtime_sec: 3600 },
            ph_down: { enabled: true, flow_rate_ml_per_sec: 1, max_runtime_sec: 60 },
            ph_up: { enabled: true, flow_rate_ml_per_sec: 1, max_runtime_sec: 60 },
            nutrient_a: { enabled: true, flow_rate_ml_per_sec: 2, max_runtime_sec: 120 },
            nutrient_b: { enabled: true, flow_rate_ml_per_sec: 2, max_runtime_sec: 120 },
            cal_mag: { enabled: true, flow_rate_ml_per_sec: 1, max_runtime_sec: 60 }
          }
        },
        safety: {
          ph_min: 4.0,
          ph_max: 8.5,
          tds_max: 2000,
          emergency_stop_enabled: true
        }
      },
      stats: {
        uptime_hours: 0,
        memory_usage_percent: 0,
        wifi_signal_strength: 0,
        total_commands_processed: 0,
        total_sensor_readings: 0,
        total_pump_activations: 0
      },
      beacon: {
        service_id: null,
        registered: false,
        last_heartbeat: null
      }
    };

    const result = await this.collection.insertOne(device);
    return { ...device, _id: result.insertedId };
  }

  async findByDeviceId(deviceId) {
    return await this.collection.findOne({ device_id: deviceId });
  }

  async updateStatus(deviceId, status, lastSeen = new Date()) {
    return await this.collection.updateOne(
      { device_id: deviceId },
      { 
        $set: { 
          status, 
          last_seen: lastSeen,
          updated_at: new Date()
        } 
      }
    );
  }

  async updateBeaconInfo(deviceId, beaconData) {
    return await this.collection.updateOne(
      { device_id: deviceId },
      { 
        $set: { 
          'beacon.service_id': beaconData.service_id,
          'beacon.registered': true,
          'beacon.last_heartbeat': new Date(),
          updated_at: new Date()
        } 
      }
    );
  }

  async findAll(filter = {}) {
    return await this.collection.find(filter).toArray();
  }

  async updateConfig(deviceId, configUpdate) {
    return await this.collection.updateOne(
      { device_id: deviceId },
      { 
        $set: { 
          config: configUpdate,
          updated_at: new Date()
        } 
      }
    );
  }

  async updateStats(deviceId, stats) {
    return await this.collection.updateOne(
      { device_id: deviceId },
      { 
        $set: { 
          stats: stats,
          updated_at: new Date()
        } 
      }
    );
  }

  async delete(deviceId) {
    return await this.collection.deleteOne({ device_id: deviceId });
  }

  async getDeviceCount() {
    const total = await this.collection.countDocuments();
    const online = await this.collection.countDocuments({ status: 'online' });
    const offline = await this.collection.countDocuments({ status: 'offline' });
    
    return { total, online, offline };
  }

  async getDevicesWithLastSeen(hoursAgo = 24) {
    const cutoff = new Date(Date.now() - hoursAgo * 60 * 60 * 1000);
    
    return await this.collection.find({
      last_seen: { $gte: cutoff }
    }).toArray();
  }
} 