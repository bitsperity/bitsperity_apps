import express from 'express';

class SensorRoutes {
  constructor(sensorDataModel, deviceModel) {
    this.sensorDataModel = sensorDataModel;
    this.deviceModel = deviceModel;
    this.router = express.Router();
    this.setupRoutes();
  }

  setupRoutes() {
    // Get latest sensor readings for a device
    this.router.get('/:deviceId/latest', async (req, res) => {
      try {
        const deviceId = req.params.deviceId;
        
        // Verify device exists
        const device = await this.deviceModel.findByDeviceId(deviceId);
        if (!device) {
          return res.status(404).json({
            success: false,
            error: 'Device not found'
          });
        }

        const latestReadings = await this.sensorDataModel.getLatestAll(deviceId);

        res.json({
          success: true,
          device_id: deviceId,
          data: latestReadings,
          timestamp: new Date()
        });
      } catch (error) {
        console.error('Error getting latest sensor data:', error);
        res.status(500).json({
          success: false,
          error: error.message
        });
      }
    });

    // Get latest reading for specific sensor type
    this.router.get('/:deviceId/:sensorType/latest', async (req, res) => {
      try {
        const { deviceId, sensorType } = req.params;
        
        const device = await this.deviceModel.findByDeviceId(deviceId);
        if (!device) {
          return res.status(404).json({
            success: false,
            error: 'Device not found'
          });
        }

        const latestReading = await this.sensorDataModel.getLatest(deviceId, sensorType);

        if (!latestReading) {
          return res.status(404).json({
            success: false,
            error: 'No sensor data found'
          });
        }

        res.json({
          success: true,
          data: latestReading
        });
      } catch (error) {
        console.error('Error getting latest sensor reading:', error);
        res.status(500).json({
          success: false,
          error: error.message
        });
      }
    });

    // Get historical sensor data
    this.router.get('/:deviceId/:sensorType/history', async (req, res) => {
      try {
        const { deviceId, sensorType } = req.params;
        const { 
          start_time, 
          end_time, 
          limit = 1000,
          interval = null 
        } = req.query;

        const device = await this.deviceModel.findByDeviceId(deviceId);
        if (!device) {
          return res.status(404).json({
            success: false,
            error: 'Device not found'
          });
        }

        // Parse time parameters
        let startTime, endTime;
        
        if (start_time) {
          startTime = new Date(start_time);
        } else {
          // Default to last 24 hours
          startTime = new Date(Date.now() - 24 * 60 * 60 * 1000);
        }

        if (end_time) {
          endTime = new Date(end_time);
        } else {
          endTime = new Date();
        }

        let data;
        
        if (interval) {
          // Get aggregated data
          data = await this.sensorDataModel.getAggregated(
            deviceId, 
            sensorType, 
            interval, 
            startTime, 
            endTime
          );
        } else {
          // Get raw data
          data = await this.sensorDataModel.getRange(
            deviceId, 
            sensorType, 
            startTime, 
            endTime, 
            parseInt(limit)
          );
        }

        res.json({
          success: true,
          device_id: deviceId,
          sensor_type: sensorType,
          start_time: startTime,
          end_time: endTime,
          interval: interval,
          count: data.length,
          data: data
        });
      } catch (error) {
        console.error('Error getting sensor history:', error);
        res.status(500).json({
          success: false,
          error: error.message
        });
      }
    });

    // Get sensor statistics
    this.router.get('/:deviceId/:sensorType/stats', async (req, res) => {
      try {
        const { deviceId, sensorType } = req.params;
        const { hours = 24 } = req.query;

        const device = await this.deviceModel.findByDeviceId(deviceId);
        if (!device) {
          return res.status(404).json({
            success: false,
            error: 'Device not found'
          });
        }

        const stats = await this.sensorDataModel.getStatistics(
          deviceId, 
          sensorType, 
          parseInt(hours)
        );

        if (!stats) {
          return res.status(404).json({
            success: false,
            error: 'No data available for statistics'
          });
        }

        // Get trend information
        const trend = await this.sensorDataModel.getRecentTrend(
          deviceId, 
          sensorType, 
          60 // Last 60 minutes
        );

        res.json({
          success: true,
          device_id: deviceId,
          sensor_type: sensorType,
          period_hours: parseInt(hours),
          statistics: stats,
          trend: trend,
          timestamp: new Date()
        });
      } catch (error) {
        console.error('Error getting sensor statistics:', error);
        res.status(500).json({
          success: false,
          error: error.message
        });
      }
    });

    // Get data quality report
    this.router.get('/:deviceId/quality', async (req, res) => {
      try {
        const deviceId = req.params.deviceId;
        const { hours = 24 } = req.query;

        const device = await this.deviceModel.findByDeviceId(deviceId);
        if (!device) {
          return res.status(404).json({
            success: false,
            error: 'Device not found'
          });
        }

        const qualityReport = await this.sensorDataModel.getDataQualityReport(
          deviceId, 
          parseInt(hours)
        );

        res.json({
          success: true,
          device_id: deviceId,
          period_hours: parseInt(hours),
          quality_report: qualityReport,
          timestamp: new Date()
        });
      } catch (error) {
        console.error('Error getting data quality report:', error);
        res.status(500).json({
          success: false,
          error: error.message
        });
      }
    });

    // Get sensor trend analysis
    this.router.get('/:deviceId/:sensorType/trend', async (req, res) => {
      try {
        const { deviceId, sensorType } = req.params;
        const { minutes = 60 } = req.query;

        const device = await this.deviceModel.findByDeviceId(deviceId);
        if (!device) {
          return res.status(404).json({
            success: false,
            error: 'Device not found'
          });
        }

        const trend = await this.sensorDataModel.getRecentTrend(
          deviceId, 
          sensorType, 
          parseInt(minutes)
        );

        res.json({
          success: true,
          device_id: deviceId,
          sensor_type: sensorType,
          period_minutes: parseInt(minutes),
          trend: trend,
          timestamp: new Date()
        });
      } catch (error) {
        console.error('Error getting sensor trend:', error);
        res.status(500).json({
          success: false,
          error: error.message
        });
      }
    });

    // Get multiple devices latest readings (dashboard overview)
    this.router.get('/overview/latest', async (req, res) => {
      try {
        const { device_ids } = req.query;
        
        let deviceIds;
        if (device_ids) {
          deviceIds = device_ids.split(',');
        } else {
          // Get all online devices
          const onlineDevices = await this.deviceModel.getOnlineDevices();
          deviceIds = onlineDevices.map(d => d.device_id);
        }

        const overview = {};
        
        for (const deviceId of deviceIds) {
          try {
            const latestReadings = await this.sensorDataModel.getLatestAll(deviceId);
            overview[deviceId] = latestReadings;
          } catch (error) {
            console.warn(`Failed to get readings for device ${deviceId}:`, error.message);
            overview[deviceId] = null;
          }
        }

        res.json({
          success: true,
          device_count: deviceIds.length,
          data: overview,
          timestamp: new Date()
        });
      } catch (error) {
        console.error('Error getting overview data:', error);
        res.status(500).json({
          success: false,
          error: error.message
        });
      }
    });

    // Export sensor data (CSV format)
    this.router.get('/:deviceId/:sensorType/export', async (req, res) => {
      try {
        const { deviceId, sensorType } = req.params;
        const { start_time, end_time, format = 'csv' } = req.query;

        const device = await this.deviceModel.findByDeviceId(deviceId);
        if (!device) {
          return res.status(404).json({
            success: false,
            error: 'Device not found'
          });
        }

        const startTime = start_time ? new Date(start_time) : new Date(Date.now() - 24 * 60 * 60 * 1000);
        const endTime = end_time ? new Date(end_time) : new Date();

        const data = await this.sensorDataModel.getRange(
          deviceId, 
          sensorType, 
          startTime, 
          endTime, 
          10000 // Max 10k records for export
        );

        if (format === 'csv') {
          // Generate CSV
          const csvHeader = 'timestamp,device_timestamp,raw_value,calibrated_value,filtered_value,unit,quality\n';
          const csvRows = data.map(row => 
            `${row.timestamp.toISOString()},${row.device_timestamp},${row.values.raw},${row.values.calibrated},${row.values.filtered},${row.unit},${row.quality}`
          ).join('\n');
          
          const csv = csvHeader + csvRows;
          
          res.setHeader('Content-Type', 'text/csv');
          res.setHeader('Content-Disposition', `attachment; filename="${deviceId}_${sensorType}_${startTime.toISOString().split('T')[0]}_${endTime.toISOString().split('T')[0]}.csv"`);
          res.send(csv);
        } else {
          // JSON format
          res.json({
            success: true,
            device_id: deviceId,
            sensor_type: sensorType,
            start_time: startTime,
            end_time: endTime,
            count: data.length,
            data: data
          });
        }
      } catch (error) {
        console.error('Error exporting sensor data:', error);
        res.status(500).json({
          success: false,
          error: error.message
        });
      }
    });
  }

  getRouter() {
    return this.router;
  }
}

export default SensorRoutes; 