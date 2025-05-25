import Joi from 'joi';

// Sensor data validation schema
const sensorDataSchema = Joi.object({
  timestamp: Joi.number().optional(),
  device_timestamp: Joi.number().optional(),
  values: Joi.object({
    raw: Joi.number().required(),
    calibrated: Joi.number().required(),
    filtered: Joi.number().optional()
  }).required(),
  unit: Joi.string().optional(),
  quality: Joi.string().valid('good', 'poor', 'unknown', 'error').optional(),
  calibration_status: Joi.string().valid('calibrated', 'uncalibrated', 'needs_calibration').optional(),
  filter_config: Joi.object().optional()
});

// Command validation schema
const commandSchema = Joi.object({
  command_id: Joi.string().required(),
  command: Joi.string().required(),
  params: Joi.object().optional(),
  timestamp: Joi.number().optional(),
  timeout_ms: Joi.number().optional()
});

// Heartbeat validation schema
const heartbeatSchema = Joi.object({
  timestamp: Joi.number().optional(),
  uptime_seconds: Joi.number().required(),
  free_heap: Joi.number().optional(),
  wifi_rssi: Joi.number().optional(),
  mqtt_connected: Joi.boolean().optional(),
  sensor_status: Joi.object().optional(),
  pump_status: Joi.object().optional(),
  active_program: Joi.string().optional(),
  system_health: Joi.string().valid('healthy', 'warning', 'error').optional()
});

export function validateSensorData(data) {
  const { error, value } = sensorDataSchema.validate(data);
  if (error) {
    throw new Error(`Invalid sensor data: ${error.message}`);
  }
  return value;
}

export function validateCommand(data) {
  const { error, value } = commandSchema.validate(data);
  if (error) {
    throw new Error(`Invalid command: ${error.message}`);
  }
  return value;
}

export function validateHeartbeat(data) {
  const { error, value } = heartbeatSchema.validate(data);
  if (error) {
    throw new Error(`Invalid heartbeat: ${error.message}`);
  }
  return value;
} 