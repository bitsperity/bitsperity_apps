import { z } from 'zod';
import { subHours, subDays, subWeeks } from 'date-fns';

// Time range mapping
const timeRanges = {
  '1h': () => subHours(new Date(), 1),
  '6h': () => subHours(new Date(), 6),
  '24h': () => subHours(new Date(), 24),
  '7d': () => subDays(new Date(), 7),
  '30d': () => subDays(new Date(), 30),
  '3m': () => subDays(new Date(), 90)
};

export default async function sensorRoutes(fastify, options) {
  
  // Get latest sensor readings (public for development)
  fastify.get('/latest', async (request, reply) => {
    try {
      const latestReadings = await fastify.db.collection('latest_readings').find({}).toArray();
      
      // Group by device
      const sensorsByDevice = latestReadings.reduce((acc, reading) => {
        if (!acc[reading.deviceId]) {
          acc[reading.deviceId] = {};
        }
        
        acc[reading.deviceId][reading.sensorType] = {
          value: reading.value,
          rawValue: reading.rawValue,
          timestamp: reading.timestamp,
          receivedAt: reading.receivedAt,
          status: getSensorStatus(reading.sensorType, reading.value)
        };
        
        return acc;
      }, {});

      return { 
        success: true, 
        data: sensorsByDevice,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      fastify.log.error('Error fetching latest sensor data:', error);
      reply.status(500).send({ 
        success: false, 
        error: 'Failed to fetch latest sensor data' 
      });
    }
  });
  
  // Get all latest sensor readings
  fastify.get('/', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const latestReadings = await fastify.db.collection('latest_readings').find({}).toArray();
      
      // Group by device
      const sensorsByDevice = latestReadings.reduce((acc, reading) => {
        if (!acc[reading.deviceId]) {
          acc[reading.deviceId] = {};
        }
        
        acc[reading.deviceId][reading.sensorType] = {
          value: reading.value,
          unit: reading.unit,
          status: reading.status || 'ok',
          timestamp: reading.timestamp
        };
        
        return acc;
      }, {});

      return { data: sensorsByDevice };
    } catch (error) {
      fastify.log.error('Error fetching sensor data:', error);
      reply.status(500).send({ error: 'Failed to fetch sensor data' });
    }
  });

  // Get sensor readings for specific device
  fastify.get('/device/:deviceId', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const { deviceId } = request.params;
      
      const readings = await fastify.db.collection('latest_readings')
        .find({ deviceId })
        .toArray();

      const sensorData = readings.reduce((acc, reading) => {
        acc[reading.sensorType] = {
          value: reading.value,
          unit: reading.unit,
          status: reading.status || 'ok',
          timestamp: reading.timestamp
        };
        return acc;
      }, {});

      return { data: sensorData };
    } catch (error) {
      fastify.log.error('Error fetching device sensors:', error);
      reply.status(500).send({ error: 'Failed to fetch device sensor data' });
    }
  });

  // Get historical data for specific sensor
  fastify.get('/history/:deviceId/:sensorType', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const { deviceId, sensorType } = request.params;
      const { range = '24h', limit = 1000 } = request.query;

      // Validate time range
      if (!timeRanges[range]) {
        return reply.status(400).send({ 
          error: 'Invalid time range',
          message: 'Supported ranges: 1h, 6h, 24h, 7d, 30d, 3m'
        });
      }

      const startTime = timeRanges[range]();
      
      const historicalData = await fastify.db.collection('sensor_data')
        .find({
          deviceId,
          sensorType,
          timestamp: { $gte: startTime.toISOString() }
        })
        .sort({ timestamp: 1 })
        .limit(parseInt(limit))
        .toArray();

      // Transform data for frontend charting
      const chartData = historicalData.map(reading => ({
        timestamp: reading.timestamp,
        value: reading.value,
        status: reading.status || 'ok'
      }));

      return { 
        data: chartData,
        meta: {
          deviceId,
          sensorType,
          range,
          count: chartData.length,
          startTime: startTime.toISOString(),
          endTime: new Date().toISOString()
        }
      };
    } catch (error) {
      fastify.log.error('Error fetching historical data:', error);
      reply.status(500).send({ error: 'Failed to fetch historical data' });
    }
  });

  // Get sensor statistics
  fastify.get('/stats/:deviceId/:sensorType', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const { deviceId, sensorType } = request.params;
      const { range = '24h' } = request.query;

      if (!timeRanges[range]) {
        return reply.status(400).send({ 
          error: 'Invalid time range',
          message: 'Supported ranges: 1h, 6h, 24h, 7d, 30d, 3m'
        });
      }

      const startTime = timeRanges[range]();

      const stats = await fastify.db.collection('sensor_data').aggregate([
        {
          $match: {
            deviceId,
            sensorType,
            timestamp: { $gte: startTime.toISOString() }
          }
        },
        {
          $group: {
            _id: null,
            min: { $min: '$value' },
            max: { $max: '$value' },
            avg: { $avg: '$value' },
            count: { $sum: 1 },
            latest: { $last: '$value' }
          }
        }
      ]).toArray();

      const result = stats[0] || {
        min: null,
        max: null,
        avg: null,
        count: 0,
        latest: null
      };

      return {
        data: {
          ...result,
          avg: result.avg ? Number(result.avg.toFixed(2)) : null,
          range,
          deviceId,
          sensorType
        }
      };
    } catch (error) {
      fastify.log.error('Error fetching sensor stats:', error);
      reply.status(500).send({ error: 'Failed to fetch sensor statistics' });
    }
  });

  // Get sensor alerts/warnings
  fastify.get('/alerts', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const { deviceId, status = 'alert,warning' } = request.query;
      
      const statusFilter = status.split(',');
      const matchFilter = {
        status: { $in: statusFilter }
      };

      if (deviceId) {
        matchFilter.deviceId = deviceId;
      }

      const alerts = await fastify.db.collection('latest_readings')
        .find(matchFilter)
        .sort({ timestamp: -1 })
        .toArray();

      const alertsWithDeviceInfo = await Promise.all(
        alerts.map(async (alert) => {
          const device = await fastify.db.collection('devices').findOne(
            { deviceId: alert.deviceId },
            { projection: { name: 1, location: 1 } }
          );

          return {
            id: alert._id,
            deviceId: alert.deviceId,
            deviceName: device?.name || `Device ${alert.deviceId}`,
            deviceLocation: device?.location,
            sensorType: alert.sensorType,
            value: alert.value,
            unit: alert.unit,
            status: alert.status,
            timestamp: alert.timestamp,
            message: generateAlertMessage(alert)
          };
        })
      );

      return { data: alertsWithDeviceInfo };
    } catch (error) {
      fastify.log.error('Error fetching sensor alerts:', error);
      reply.status(500).send({ error: 'Failed to fetch sensor alerts' });
    }
  });

  // Export sensor data
  fastify.get('/export/:deviceId/:sensorType', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const { deviceId, sensorType } = request.params;
      const { range = '24h', format = 'csv' } = request.query;

      if (!timeRanges[range]) {
        return reply.status(400).send({ 
          error: 'Invalid time range',
          message: 'Supported ranges: 1h, 6h, 24h, 7d, 30d, 3m'
        });
      }

      const startTime = timeRanges[range]();
      
      const data = await fastify.db.collection('sensor_data')
        .find({
          deviceId,
          sensorType,
          timestamp: { $gte: startTime.toISOString() }
        })
        .sort({ timestamp: 1 })
        .toArray();

      if (format === 'csv') {
        const csvHeader = 'Timestamp,Device ID,Sensor Type,Value,Unit,Status\n';
        const csvData = data.map(row => 
          `${row.timestamp},${row.deviceId},${row.sensorType},${row.value},${row.unit || ''},${row.status || 'ok'}`
        ).join('\n');

        reply.header('Content-Type', 'text/csv');
        reply.header('Content-Disposition', `attachment; filename="${deviceId}_${sensorType}_${range}.csv"`);
        
        return csvHeader + csvData;
      } else {
        // JSON format
        reply.header('Content-Type', 'application/json');
        reply.header('Content-Disposition', `attachment; filename="${deviceId}_${sensorType}_${range}.json"`);
        
        return { data };
      }
    } catch (error) {
      fastify.log.error('Error exporting sensor data:', error);
      reply.status(500).send({ error: 'Failed to export sensor data' });
    }
  });

  // Configure sensor thresholds
  fastify.post('/:deviceId/:sensorType/thresholds', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const { deviceId, sensorType } = request.params;
      const thresholds = request.body;

      await fastify.db.collection('sensor_thresholds').replaceOne(
        { deviceId, sensorType },
        {
          deviceId,
          sensorType,
          thresholds,
          updatedAt: new Date(),
          updatedBy: request.user.userId
        },
        { upsert: true }
      );

      return { message: 'Sensor thresholds updated successfully', data: thresholds };
    } catch (error) {
      fastify.log.error('Error updating sensor thresholds:', error);
      reply.status(500).send({ error: 'Failed to update sensor thresholds' });
    }
  });

  // Get sensor thresholds
  fastify.get('/:deviceId/:sensorType/thresholds', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const { deviceId, sensorType } = request.params;

      const config = await fastify.db.collection('sensor_thresholds').findOne({
        deviceId,
        sensorType
      });

      return { 
        data: config?.thresholds || {
          min: null,
          max: null,
          warningMin: null,
          warningMax: null,
          enabled: true
        }
      };
    } catch (error) {
      fastify.log.error('Error fetching sensor thresholds:', error);
      reply.status(500).send({ error: 'Failed to fetch sensor thresholds' });
    }
  });
}

// Helper function to generate alert messages
function generateAlertMessage(alert) {
  const { sensorType, value, unit, status } = alert;
  
  const sensorNames = {
    'ph': 'pH-Wert',
    'temperature': 'Temperatur',
    'humidity': 'Luftfeuchtigkeit',
    'ec': 'Leitfähigkeit',
    'water_level': 'Wasserstand',
    'light_intensity': 'Lichtintensität'
  };

  const sensorName = sensorNames[sensorType] || sensorType;
  const unitStr = unit ? ` ${unit}` : '';
  
  if (status === 'alert') {
    return `Kritischer ${sensorName}: ${value}${unitStr}`;
  } else if (status === 'warning') {
    return `Warnung ${sensorName}: ${value}${unitStr}`;
  }
  
  return `${sensorName}: ${value}${unitStr}`;
}

// Hilfsfunktion: Sensor-Status bestimmen
function getSensorStatus(sensorType, value) {
  switch (sensorType) {
    case 'ph':
      if (value >= 5.5 && value <= 6.5) return 'optimal';
      if (value >= 5.0 && value <= 7.0) return 'warning';
      return 'critical';
    
    case 'tds':
      if (value >= 800 && value <= 1500) return 'optimal';
      if (value >= 600 && value <= 2000) return 'warning';
      return 'critical';
    
    default:
      return 'unknown';
  }
} 