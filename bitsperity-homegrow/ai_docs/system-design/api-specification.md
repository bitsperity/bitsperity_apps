# HomeGrow v3 - API Specification

## API Übersicht

HomeGrow v3 stellt eine **RESTful API** mit **WebSocket Real-time Updates** bereit. Alle API-Endpoints folgen dem `/api/v1/` Präfix und verwenden standardisierte JSON-Responses mit TypeScript-Typisierung.

```
API Architecture:
├── REST API          # CRUD operations, configuration
├── WebSocket API     # Real-time updates, live data
└── MQTT Integration  # ESP32 device communication
```

## Standard Response Format

### Success Response
```typescript
interface ApiResponse<T> {
  success: true;
  data: T;
  timestamp: string;       // ISO 8601 timestamp
  request_id?: string;     // Optional request tracking
}
```

### Error Response
```typescript
interface ApiError {
  success: false;
  error: {
    code: string;          // Error code (e.g., "DEVICE_NOT_FOUND")
    message: string;       // Human-readable error message
    details?: any;         // Optional error details
  };
  timestamp: string;
  request_id?: string;
}
```

### HTTP Status Codes
- **200 OK**: Successful operation
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid input data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource conflict (duplicate device_id)
- **422 Unprocessable Entity**: Validation errors
- **500 Internal Server Error**: Server error

## Device Management API

### GET /api/v1/devices
**Zweck**: Liste aller registrierten Geräte mit aktuellem Status

```typescript
// Query Parameters
interface DeviceQuery {
  status?: 'online' | 'offline' | 'error' | 'unknown';
  location?: string;
  limit?: number;      // Default: 50, Max: 100
  offset?: number;     // Default: 0
}

// Response
interface DeviceListResponse {
  devices: Device[];
  total: number;
  has_more: boolean;
}
```

**Beispiel**:
```bash
GET /api/v1/devices?status=online&limit=10
```

### POST /api/v1/devices
**Zweck**: Neues Gerät registrieren

```typescript
// Request Body
interface CreateDeviceRequest {
  device_id: string;           // Must be unique
  name: string;
  location?: string;
  beacon_service_name?: string; // For automatic discovery
  config?: Partial<DeviceConfig>; // Optional initial configuration
}

// Response: 201 Created
interface CreateDeviceResponse {
  device: Device;
  setup_required: boolean;     // True if device needs configuration
}
```

### GET /api/v1/devices/{deviceId}
**Zweck**: Detaillierte Geräteinformationen mit aktuellen Sensor-Werten

```typescript
// Response
interface DeviceDetailResponse {
  device: Device;
  current_sensors: Array<{
    sensor_type: string;
    value: number;
    unit: string;
    quality: 'good' | 'warning' | 'error';
    timestamp: string;
  }>;
  active_program?: {
    instance_id: string;
    template_name: string;
    current_phase: string;
    progress_percentage: number;
  };
  recent_commands: Array<{
    command_id: string;
    action: string;
    timestamp: string;
    status: 'success' | 'error' | 'pending';
  }>;
}
```

### PUT /api/v1/devices/{deviceId}
**Zweck**: Gerät-Konfiguration aktualisieren

```typescript
// Request Body
interface UpdateDeviceRequest {
  name?: string;
  location?: string;
  config?: Partial<DeviceConfig>;
}

// Response: 200 OK
interface UpdateDeviceResponse {
  device: Device;
  config_changes: string[];    // List of changed configuration keys
}
```

### DELETE /api/v1/devices/{deviceId}
**Zweck**: Gerät entfernen (mit Bestätigung)

```typescript
// Query Parameters
interface DeleteDeviceQuery {
  confirm: 'true';             // Required confirmation
  cleanup_data?: 'true';       // Also delete sensor data
}

// Response: 200 OK
interface DeleteDeviceResponse {
  device_id: string;
  deleted_sensor_data_count?: number;
}
```

### POST /api/v1/devices/{deviceId}/commands
**Zweck**: Manuellen Befehl an Gerät senden

```typescript
// Request Body
interface DeviceCommandRequest {
  action: 'activate_pump' | 'emergency_stop' | 'calibrate_sensor' | 'test_connection';
  params: Record<string, any>;
  reason?: string;             // Optional user-provided reason
}

// Pump Command Example
interface PumpCommandParams {
  pump_type: 'water' | 'air' | 'ph_down' | 'ph_up' | 'nutrient_a' | 'nutrient_b' | 'cal_mag';
  duration: number;            // Seconds (1-300)
}

// Response: 201 Created
interface CommandResponse {
  command_id: string;
  status: 'pending' | 'sent' | 'acknowledged';
  estimated_completion: string; // ISO timestamp
}
```

## Device Discovery API

### GET /api/v1/devices/discovery
**Zweck**: Liste der über MQTT registrierten Geräte

```typescript
// Response
interface DiscoveryResponse {
  registered_devices: Array<{
    device_id: string;
    device_type: string;
    ip_address: string;
    capabilities: string[];
    firmware_version: string;
    status: 'online' | 'offline' | 'error';
    last_seen: string;
    registration_source: 'mqtt_auto_register';
  }>;
  total_devices: number;
  online_devices: number;
}
```

**Hinweis**: Device Discovery erfolgt automatisch über MQTT. ESP32-Clients finden den MQTT Broker über Beacon/mDNS und registrieren sich selbst.

## Sensor Data API

### GET /api/v1/sensors/current
**Zweck**: Aktuelle Sensor-Werte aller Geräte

```typescript
// Query Parameters
interface CurrentSensorQuery {
  device_ids?: string;         // Comma-separated device IDs
  sensor_types?: string;       // Comma-separated sensor types (ph, tds)
  quality?: 'good' | 'warning' | 'error';
}

// Response
interface CurrentSensorResponse {
  readings: Array<{
    device_id: string;
    device_name: string;
    sensor_type: 'ph' | 'tds';
    value: number;
    unit: string;
    quality: string;
    timestamp: string;
    age_seconds: number;       // Seconds since reading
  }>;
  total_devices: number;
  offline_devices: string[];
}
```

### GET /api/v1/sensors/{deviceId}/history
**Zweck**: Historische Sensor-Daten für Charts und Analyse

```typescript
// Query Parameters
interface SensorHistoryQuery {
  sensor_type?: string;        // Filter by sensor type
  from: string;                // ISO timestamp
  to: string;                  // ISO timestamp
  aggregation?: 'raw' | 'minute' | 'hour' | 'day'; // Data granularity
  limit?: number;              // Max 10000 points
}

// Response
interface SensorHistoryResponse {
  data: Array<{
    timestamp: string;
    sensor_type: string;
    value: number;
    quality: string;
  }>;
  aggregation_used: string;
  total_points: number;
  time_range: {
    from: string;
    to: string;
    duration_hours: number;
  };
}
```

### POST /api/v1/sensors/{deviceId}/data
**Zweck**: Sensor-Daten von ESP32-Client empfangen (intern)

```typescript
// Request Body (from ESP32 via MQTT bridge)
interface SensorDataIngestion {
  readings: Array<{
    sensor_type: string;
    value: number;
    raw_value: number;
    timestamp?: string;        // Optional, server time used if missing
    quality?: string;          // Default: 'good'
  }>;
  batch_id?: string;           // For batch processing
}

// Response: 201 Created
interface IngestionResponse {
  processed: number;
  duplicates_skipped: number;
  errors: Array<{
    reading_index: number;
    error: string;
  }>;
}
```

### GET /api/v1/sensors/export
**Zweck**: Sensor-Daten als CSV exportieren

```typescript
// Query Parameters
interface ExportQuery {
  device_ids?: string;         // Comma-separated
  sensor_types?: string;       // Comma-separated (ph, tds)
  from: string;                // ISO timestamp
  to: string;                  // ISO timestamp
  format: 'csv' | 'json';      // Export format
  include_raw?: 'true';        // Include raw values
}

// Response: File download
// Content-Type: text/csv or application/json
// Content-Disposition: attachment; filename="homegrow_export_YYYY-MM-DD.csv"
```

## Program Management API

### GET /api/v1/programs/templates
**Zweck**: Verfügbare Program-Templates auflisten

```typescript
// Query Parameters
interface TemplateQuery {
  crop_type?: string;
  tags?: string;               // Comma-separated
  is_public?: 'true' | 'false';
  author?: string;
  limit?: number;
  offset?: number;
}

// Response
interface TemplateListResponse {
  templates: Array<{
    template_id: string;
    name: string;
    description: string;
    crop_type: string;
    duration_days: number;
    tags: string[];
    author: string;
    version: string;
    usage_count: number;
    is_public: boolean;
    created_at: string;
  }>;
  total: number;
  has_more: boolean;
}
```

### POST /api/v1/programs/templates
**Zweck**: Neues Program-Template erstellen

```typescript
// Request Body
interface CreateTemplateRequest {
  name: string;
  description?: string;
  crop_type?: string;
  tags?: string[];
  phases: Array<ProgramPhase>;
  is_public?: boolean;
}

// Response: 201 Created
interface CreateTemplateResponse {
  template: ProgramTemplate;
  validation_warnings: string[]; // Non-blocking warnings
}
```

### GET /api/v1/programs/templates/{templateId}
**Zweck**: Detaillierte Template-Informationen

```typescript
// Response
interface TemplateDetailResponse {
  template: ProgramTemplate;
  usage_statistics: {
    total_instances: number;
    success_rate: number;       // % completed successfully
    avg_duration_days: number;
    performance_metrics: {
      avg_ph_achievement: number;
      avg_tds_achievement: number;
    };
  };
  similar_templates: Array<{
    template_id: string;
    name: string;
    similarity_score: number;  // 0-1
  }>;
}
```

### POST /api/v1/programs/instances
**Zweck**: Program-Instance starten

```typescript
// Request Body
interface StartProgramRequest {
  template_id: string;
  device_id: string;
  custom_name?: string;        // Override template name
  phase_overrides?: Record<string, Partial<ProgramPhase>>; // Custom phase settings
  notification_preferences?: Record<string, boolean>;
}

// Response: 201 Created
interface StartProgramResponse {
  instance: ProgramInstance;
  estimated_completion: string; // ISO timestamp
  next_phase_transition: string; // ISO timestamp
}
```

### GET /api/v1/programs/instances
**Zweck**: Aktive Program-Instances auflisten

```typescript
// Query Parameters
interface InstanceQuery {
  status?: 'running' | 'paused' | 'completed' | 'error' | 'stopped';
  device_id?: string;
  limit?: number;
  offset?: number;
}

// Response
interface InstanceListResponse {
  instances: Array<{
    instance_id: string;
    template_name: string;
    device_id: string;
    device_name: string;
    status: string;
    current_phase: string;
    progress_percentage: number;
    started_at: string;
    estimated_completion: string;
  }>;
  total: number;
  has_more: boolean;
}
```

### PUT /api/v1/programs/instances/{instanceId}/control
**Zweck**: Program-Instance steuern (pause, resume, stop)

```typescript
// Request Body
interface ProgramControlRequest {
  action: 'pause' | 'resume' | 'stop' | 'skip_phase' | 'restart_phase';
  reason?: string;             // User-provided reason
}

// Response: 200 OK
interface ProgramControlResponse {
  instance: ProgramInstance;
  action_result: 'success' | 'already_in_state' | 'error';
  next_action_available_at?: string; // Cooldown period
}
```

### GET /api/v1/programs/instances/{instanceId}/log
**Zweck**: Program Action-Log abrufen

```typescript
// Query Parameters
interface LogQuery {
  from?: string;               // ISO timestamp
  to?: string;                 // ISO timestamp
  action_types?: string;       // Comma-separated
  limit?: number;              // Default: 100
}

// Response
interface ProgramLogResponse {
  log_entries: Array<{
    timestamp: string;
    action_type: string;
    details: Record<string, any>;
    triggered_by: string;
    result: string;
    sensor_values_at_time?: Record<string, number>;
  }>;
  total_entries: number;
  time_range: {
    from: string;
    to: string;
  };
}
```

## Alert Management API

### GET /api/v1/alerts
**Zweck**: Alert-Historie und aktive Alerts

```typescript
// Query Parameters
interface AlertQuery {
  status?: 'active' | 'acknowledged' | 'resolved';
  severity?: 'critical' | 'warning' | 'info' | 'system';
  device_id?: string;
  from?: string;               // ISO timestamp
  to?: string;                 // ISO timestamp
  limit?: number;
  offset?: number;
}

// Response
interface AlertListResponse {
  alerts: Array<{
    alert_id: string;
    severity: string;
    title: string;
    message: string;
    device_id?: string;
    device_name?: string;
    status: string;
    created_at: string;
    acknowledged_at?: string;
    resolved_at?: string;
    trigger_value?: number;
    threshold_value?: number;
  }>;
  total: number;
  active_count: number;
  has_more: boolean;
}
```

### PUT /api/v1/alerts/{alertId}/acknowledge
**Zweck**: Alert als gelesen markieren

```typescript
// Request Body
interface AcknowledgeAlertRequest {
  note?: string;               // Optional user note
}

// Response: 200 OK
interface AcknowledgeAlertResponse {
  alert_id: string;
  status: 'acknowledged';
  acknowledged_at: string;
}
```

### POST /api/v1/alerts/bulk-action
**Zweck**: Mehrere Alerts gleichzeitig verwalten

```typescript
// Request Body
interface BulkAlertAction {
  alert_ids: string[];
  action: 'acknowledge' | 'resolve' | 'delete';
  note?: string;
}

// Response: 200 OK
interface BulkAlertResponse {
  processed: number;
  failed: Array<{
    alert_id: string;
    error: string;
  }>;
}
```

## System Settings API

### GET /api/v1/settings
**Zweck**: System-Konfiguration abrufen

```typescript
// Response
interface SystemSettings {
  theme: 'light' | 'dark' | 'auto';
  notifications: {
    browser_push: boolean;
    email_alerts: boolean;
    email_address?: string;
    quiet_hours?: {
      enabled: boolean;
      from: string;            // HH:MM format
      to: string;              // HH:MM format
    };
  };
  safety_limits: {
    ph_emergency_min: number;
    ph_emergency_max: number;
    tds_emergency_max: number;
    max_pump_duration: number;
  };
  data_retention: {
    sensor_data_days: number;
    program_logs_days: number;
    alert_history_days: number;
  };
  automation: {
    enabled: boolean;
    ph_correction_enabled: boolean;
    tds_correction_enabled: boolean;
    cooldown_minutes: number;
  };
}
```

### PUT /api/v1/settings
**Zweck**: System-Konfiguration aktualisieren

```typescript
// Request Body: Partial<SystemSettings>
// Response: 200 OK
interface UpdateSettingsResponse {
  settings: SystemSettings;
  restart_required: boolean;   // True if changes require restart
  validation_errors: string[];
}
```

### POST /api/v1/settings/backup
**Zweck**: System-Backup erstellen

```typescript
// Request Body
interface BackupRequest {
  include_sensor_data: boolean;
  include_program_instances: boolean;
  compression?: 'gzip' | 'none';
}

// Response: File download
// Content-Type: application/octet-stream
// Content-Disposition: attachment; filename="homegrow_backup_YYYY-MM-DD.tar.gz"
```

### POST /api/v1/settings/restore
**Zweck**: System-Backup wiederherstellen

```typescript
// Request: Multipart form data
// File: backup file
// Response: 200 OK
interface RestoreResponse {
  status: 'success' | 'partial' | 'failed';
  restored_items: {
    devices: number;
    templates: number;
    settings: boolean;
  };
  errors: string[];
  restart_required: boolean;
}
```

## WebSocket API

### Connection: /api/v1/ws
**Zweck**: Real-time Updates für Frontend

### Subscription Topics
```typescript
// Subscribe to specific data streams
interface WebSocketSubscription {
  action: 'subscribe' | 'unsubscribe';
  topics: Array<
    | 'devices'                    // Device status changes
    | 'sensors'                    // All sensor data updates
    | 'sensors:{deviceId}'         // Device-specific sensor data
    | 'programs'                   // Program execution updates
    | 'alerts'                     // Real-time alert notifications
    | 'commands'                   // Command execution results
  >;
}
```

### WebSocket Message Types
```typescript
interface WebSocketMessage {
  type: 'sensor_data' | 'device_status' | 'program_update' | 'alert' | 'command_result' | 'system_status';
  topic: string;
  data: any;
  timestamp: string;
  device_id?: string;
}

// Sensor Data Update
interface SensorDataMessage {
  type: 'sensor_data';
  topic: 'sensors' | 'sensors:{deviceId}';
  data: {
    device_id: string;
    sensor_type: 'ph' | 'tds';
    value: number;
    unit: string;
    quality: string;
    timestamp: string;
  };
}

// Device Status Change
interface DeviceStatusMessage {
  type: 'device_status';
  topic: 'devices';
  data: {
    device_id: string;
    status: 'online' | 'offline' | 'error';
    last_seen: string;
    change_reason?: string;
    action?: 'device_registered' | 'status_change';
  };
}

// Program Update
interface ProgramUpdateMessage {
  type: 'program_update';
  topic: 'programs';
  data: {
    instance_id: string;
    device_id: string;
    status: string;
    current_phase?: string;
    progress_percentage: number;
    action_performed?: {
      type: string;
      details: Record<string, any>;
    };
  };
}

// Alert Notification
interface AlertMessage {
  type: 'alert';
  topic: 'alerts';
  data: {
    alert_id: string;
    severity: 'critical' | 'warning' | 'info' | 'system';
    title: string;
    message: string;
    device_id?: string;
    requires_immediate_action: boolean;
  };
}
```

### Connection Management
```typescript
// Heartbeat every 30 seconds
interface HeartbeatMessage {
  type: 'heartbeat';
  timestamp: string;
}

// Connection authentication (optional future feature)
interface AuthMessage {
  type: 'auth';
  token?: string;
}

// Error handling
interface ErrorMessage {
  type: 'error';
  error: {
    code: string;
    message: string;
  };
}
```

## Health Check API

### GET /api/v1/health
**Zweck**: System-Status und Health-Check für Monitoring

```typescript
// Response
interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  uptime_seconds: number;
  version: string;
  components: {
    database: {
      status: 'connected' | 'disconnected' | 'error';
      response_time_ms?: number;
    };
    mqtt: {
      status: 'connected' | 'disconnected' | 'error';
      broker_url: string;
    };
    beacon: {
      status: 'reachable' | 'unreachable' | 'error';
      last_discovery?: string;
    };
    websocket: {
      status: 'running' | 'stopped' | 'error';
      active_connections: number;
    };
  };
  statistics: {
    total_devices: number;
    online_devices: number;
    active_programs: number;
    active_alerts: number;
    sensor_readings_24h: number;
  };
}
```

## Rate Limiting

### Limits per Endpoint
- **Device Discovery**: 10 requests/minute
- **Command Sending**: 30 requests/minute per device
- **Sensor Data Queries**: 100 requests/minute
- **WebSocket Connections**: 5 connections per IP
- **Bulk Operations**: 10 requests/minute

### Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1643723400
```

## Error Codes

### Device Management
- `DEVICE_NOT_FOUND`: Device ID not found
- `DEVICE_OFFLINE`: Device is offline
- `DEVICE_DUPLICATE`: Device ID already exists
- `DEVICE_CONFIG_INVALID`: Invalid device configuration

### Sensor Data
- `SENSOR_TYPE_INVALID`: Unknown sensor type
- `SENSOR_VALUE_OUT_OF_RANGE`: Sensor value outside valid range
- `SENSOR_DATA_TOO_OLD`: Sensor data timestamp too old

### Program Management
- `TEMPLATE_NOT_FOUND`: Program template not found
- `PROGRAM_ALREADY_RUNNING`: Device already has active program
- `PROGRAM_VALIDATION_FAILED`: Program validation errors
- `PROGRAM_NOT_FOUND`: Program instance not found

### System
- `VALIDATION_ERROR`: Input validation failed
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server error
- `SERVICE_UNAVAILABLE`: Required service unavailable

Diese API-Spezifikation bietet eine vollständige, typisierte Schnittstelle für HomeGrow v3 mit klarer Dokumentation und konsistenter Fehlerbehandlung. 