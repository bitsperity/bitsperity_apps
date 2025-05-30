class SensorDataModel {
  constructor(db) {
    this.collection = db.collection('sensor_data');
  }

  async insert(sensorData) {
    const document = {
      device_id: sensorData.device_id,
      sensor_type: sensorData.sensor_type,
      timestamp: new Date(sensorData.timestamp),
      device_timestamp: sensorData.device_timestamp,
      values: {
        raw: sensorData.values.raw,
        calibrated: sensorData.values.calibrated,
        filtered: sensorData.values.filtered
      },
      unit: sensorData.unit,
      quality: sensorData.quality || 'good',
      calibration_status: sensorData.calibration_status || 'valid',
      filter_config: sensorData.filter_config
    };

    return await this.collection.insertOne(document);
  }

  async getLatest(deviceId, sensorType) {
    return await this.collection.findOne(
      { device_id: deviceId, sensor_type: sensorType },
      { sort: { timestamp: -1 } }
    );
  }

  async getLatestAll(deviceId) {
    const pipeline = [
      { $match: { device_id: deviceId } },
      { $sort: { timestamp: -1 } },
      {
        $group: {
          _id: '$sensor_type',
          latest: { $first: '$$ROOT' }
        }
      }
    ];

    const results = await this.collection.aggregate(pipeline).toArray();
    
    const latestReadings = {};
    results.forEach(result => {
      latestReadings[result._id] = result.latest;
    });
    
    return latestReadings;
  }

  async getRange(deviceId, sensorType, startTime, endTime, limit = 1000) {
    return await this.collection.find({
      device_id: deviceId,
      sensor_type: sensorType,
      timestamp: { $gte: startTime, $lte: endTime }
    })
    .sort({ timestamp: -1 })
    .limit(limit)
    .toArray();
  }

  async getAggregated(deviceId, sensorType, interval, startTime, endTime) {
    const pipeline = [
      {
        $match: {
          device_id: deviceId,
          sensor_type: sensorType,
          timestamp: { $gte: startTime, $lte: endTime }
        }
      },
      {
        $group: {
          _id: {
            $dateTrunc: {
              date: "$timestamp",
              unit: interval // "hour", "day", etc.
            }
          },
          avg_value: { $avg: "$values.calibrated" },
          min_value: { $min: "$values.calibrated" },
          max_value: { $max: "$values.calibrated" },
          count: { $sum: 1 },
          first_timestamp: { $min: "$timestamp" },
          last_timestamp: { $max: "$timestamp" }
        }
      },
      { $sort: { "_id": 1 } }
    ];

    return await this.collection.aggregate(pipeline).toArray();
  }

  async getRecentTrend(deviceId, sensorType, minutes = 60) {
    const startTime = new Date(Date.now() - minutes * 60 * 1000);
    
    const data = await this.collection.find({
      device_id: deviceId,
      sensor_type: sensorType,
      timestamp: { $gte: startTime }
    })
    .sort({ timestamp: 1 })
    .toArray();

    if (data.length < 2) {
      return { trend: 'neutral', change: 0 };
    }

    const first = data[0].values.calibrated;
    const last = data[data.length - 1].values.calibrated;
    const change = last - first;
    const percentChange = (change / first) * 100;

    let trend = 'neutral';
    if (Math.abs(percentChange) > 1) {
      trend = change > 0 ? 'up' : 'down';
    }

    return { trend, change, percentChange };
  }

  async getStatistics(deviceId, sensorType, hours = 24) {
    const startTime = new Date(Date.now() - hours * 60 * 60 * 1000);
    
    const pipeline = [
      {
        $match: {
          device_id: deviceId,
          sensor_type: sensorType,
          timestamp: { $gte: startTime }
        }
      },
      {
        $group: {
          _id: null,
          avg: { $avg: "$values.calibrated" },
          min: { $min: "$values.calibrated" },
          max: { $max: "$values.calibrated" },
          count: { $sum: 1 },
          stdDev: { $stdDevPop: "$values.calibrated" }
        }
      }
    ];

    const result = await this.collection.aggregate(pipeline).toArray();
    return result[0] || null;
  }

  async deleteOldData(daysToKeep = 30) {
    const cutoffDate = new Date(Date.now() - daysToKeep * 24 * 60 * 60 * 1000);
    
    return await this.collection.deleteMany({
      timestamp: { $lt: cutoffDate }
    });
  }

  async getDataQualityReport(deviceId, hours = 24) {
    const startTime = new Date(Date.now() - hours * 60 * 60 * 1000);
    
    const pipeline = [
      {
        $match: {
          device_id: deviceId,
          timestamp: { $gte: startTime }
        }
      },
      {
        $group: {
          _id: {
            sensor_type: "$sensor_type",
            quality: "$quality"
          },
          count: { $sum: 1 }
        }
      },
      {
        $group: {
          _id: "$_id.sensor_type",
          qualities: {
            $push: {
              quality: "$_id.quality",
              count: "$count"
            }
          },
          total: { $sum: "$count" }
        }
      }
    ];

    return await this.collection.aggregate(pipeline).toArray();
  }
}

export default SensorDataModel; 