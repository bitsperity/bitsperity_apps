# HomeGrow v3 - Database Schema

## Übersicht

HomeGrow v3 nutzt eine **minimalistische 3-Collection MongoDB-Architektur** für optimale Performance und Einfachheit. Jede Collection ist für spezifische Anwendungsfälle optimiert und mit strategischen Indexes versehen.

```
MongoDB Database: homegrow
├── devices          # Device registration & configuration
├── sensor_data      # Time series sensor readings  
└── program_templates # Growth program definitions
```

## Collection Schemas

### 1. devices Collection

**Zweck**: Zentrale Verwaltung aller ESP32-Clients mit Konfiguration und Status

```typescript
interface Device {
  _id: ObjectId;                        // MongoDB internal ID
  device_id: string;                    // Unique device identifier (e.g., "HG-001")
  name: string;                         // User-friendly name (e.g., "Lettuce Grow Box")
  type: 'hydroponic_controller';        // Device type (fixed for v1)
  status: 'online' | 'offline' | 'error' | 'unknown';
  
  // Configuration
  config: {
    ip_address?: string;                // Last known IP
    mqtt_topics: {
      sensors: string;                  // e.g., "homegrow/devices/HG-001/sensors"
      commands: string;                 // e.g., "homegrow/devices/HG-001/commands"
      status: string;                   // e.g., "homegrow/devices/HG-001/status"
    };
    
    // Sensor configuration
    sensors: {
      ph: {
        enabled: boolean;
        calibration: {
          slope: number;                // pH calibration slope
          offset: number;               // pH calibration offset
        };
        update_interval: number;        // Seconds between readings
      };
      tds: {
        enabled: boolean;
        calibration: {
          factor: number;               // TDS conversion factor
        };
        update_interval: number;
      };
    };
    
    // Pump configuration
    pumps: {
      water: { enabled: boolean; max_duration: number; };
      air: { enabled: boolean; max_duration: number; };
      ph_down: { enabled: boolean; max_duration: number; };
      ph_up: { enabled: boolean; max_duration: number; };
      nutrient_a: { enabled: boolean; max_duration: number; };
      nutrient_b: { enabled: boolean; max_duration: number; };
      cal_mag: { enabled: boolean; max_duration: number; };
    };
    
    // Safety limits
    safety: {
      ph_min: number;                   // Emergency stop below this pH
      ph_max: number;                   // Emergency stop above this pH
      tds_max: number;                  // Emergency stop above this TDS
      max_pump_duration: number;        // Max single pump run (seconds)
    };
  };
  
  // Location & grouping
  location?: string;                    // Physical location description
  
  // MQTT registration info
  mqtt_info?: {
    last_registration: Date;            // Last MQTT registration
    client_id: string;                  // MQTT client identifier
    capabilities: string[];             // Device capability tags
    firmware_version: string;
  };
  
  // Statistics
  stats: {
    total_runtime: number;              // Total hours online
    command_count: number;              // Total commands processed
    sensor_readings: number;            // Total sensor readings
    last_maintenance?: Date;
  };
  
  // Timestamps
  created_at: Date;
  updated_at: Date;
  last_seen?: Date;                     // Last heartbeat/communication
}
```

**Beispiel-Dokument**:
```json
{
  "_id": ObjectId("..."),
  "device_id": "HG-001",
  "name": "Lettuce Grow Box #1",
  "type": "hydroponic_controller",
  "status": "online",
  "config": {
    "ip_address": "192.168.1.100",
    "mqtt_topics": {
      "sensors": "homegrow/devices/HG-001/sensors",
      "commands": "homegrow/devices/HG-001/commands",
      "status": "homegrow/devices/HG-001/status"
    },
    "sensors": {
      "ph": {
        "enabled": true,
        "calibration": { "slope": 3.5, "offset": 0.0 },
        "update_interval": 60
      },
      "tds": {
        "enabled": true,
        "calibration": { "factor": 0.5 },
        "update_interval": 60
      }
    },
    "pumps": {
      "water": { "enabled": true, "max_duration": 300 },
      "air": { "enabled": true, "max_duration": 3600 },
      "ph_down": { "enabled": true, "max_duration": 60 },
      "ph_up": { "enabled": true, "max_duration": 60 },
      "nutrient_a": { "enabled": true, "max_duration": 30 },
      "nutrient_b": { "enabled": true, "max_duration": 30 },
      "cal_mag": { "enabled": true, "max_duration": 20 }
    },
    "safety": {
      "ph_min": 4.0,
      "ph_max": 8.5,
      "tds_max": 2000,
      "max_pump_duration": 300
    }
  },
  "location": "Greenhouse A - Section 1",
  "mqtt_info": {
    "last_registration": "2024-01-15T10:00:00Z",
    "client_id": "homegrow-client-001",
    "capabilities": ["ph_sensor", "tds_sensor", "pumps_7x"],
    "firmware_version": "1.2.0"
  },
  "stats": {
    "total_runtime": 2160,
    "command_count": 1547,
    "sensor_readings": 87340,
    "last_maintenance": "2024-01-10T09:00:00Z"
  },
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "last_seen": "2024-01-15T10:29:45Z"
}
```

### 2. sensor_data Collection

**Zweck**: Hochperformante Time-Series Speicherung für alle Sensor-Readings

```typescript
interface SensorData {
  _id: ObjectId;                        // MongoDB internal ID
  device_id: string;                    // Reference to Device.device_id
  sensor_type: 'ph' | 'tds';            // Available sensor types
  timestamp: Date;                      // Measurement timestamp
  
  // Multi-format values for different use cases
  values: {
    raw: number;                        // Raw ADC/sensor value
    calibrated: number;                 // Calibrated real-world value  
    filtered: number;                   // Moving average filtered value
  };
  
  // Data quality & metadata
  unit: string;                         // 'pH', 'ppm'
  quality: 'good' | 'warning' | 'error'; // Data quality assessment
  
  // Optional context
  context?: {
    program_instance?: string;          // Associated program (if any)
    trigger_event?: string;             // What triggered this reading
    batch_id?: string;                  // For batched sensor readings
  };
}
```

**Beispiel-Dokument**:
```json
{
  "_id": ObjectId("..."),
  "device_id": "HG-001",
  "sensor_type": "ph",
  "timestamp": "2024-01-15T10:30:00Z",
  "values": {
    "raw": 2048,
    "calibrated": 6.2,
    "filtered": 6.18
  },
  "unit": "pH",
  "quality": "good",
  "context": {
    "program_instance": "lettuce_30day_001",
    "trigger_event": "scheduled_reading"
  }
}
```

### 3. program_templates Collection  

**Zweck**: Definition von Wachstumsprogrammen und aktive Program-Instances

```typescript
interface ProgramTemplate {
  _id: ObjectId;                        // MongoDB internal ID
  template_id: string;                  // Unique template identifier
  name: string;                         // Template name (e.g., "Lettuce 30-Day")
  description?: string;                 // Template description
  type: 'template' | 'instance';        // Template definition vs active instance
  
  // Template metadata
  tags: string[];                       // Search/categorization tags
  crop_type?: string;                   // Target crop (lettuce, tomato, herbs)
  duration_days: number;                // Total program duration
  
  // Multi-phase program definition
  phases: Array<{
    phase_id: string;                   // Unique phase identifier
    name: string;                       // Phase name (e.g., "Germination")
    duration_days: number;              // Phase duration
    start_day: number;                  // Day when phase starts (0-based)
    
    // Target ranges for this phase
    targets: {
      ph: { min: number; max: number; optimal: number; };
      tds: { min: number; max: number; optimal: number; };
    };
    
    // Nutrient ratios for this phase
    nutrients: {
      nutrient_a: number;               // Percentage (0-100)
      nutrient_b: number;               // Percentage (0-100)  
      cal_mag: number;                  // Percentage (0-100)
      // Total must sum to 100
    };
    
    // Automated pump cycles
    pump_cycles: {
      water: {
        interval_minutes: number;       // How often to run
        duration_seconds: number;       // How long to run
        enabled: boolean;
      };
      air: {
        interval_minutes: number;
        duration_seconds: number;
        enabled: boolean;
      };
    };
    
    // Phase transition conditions (optional)
    transition_conditions?: {
      auto_advance: boolean;            // Auto-advance after duration
      manual_approval: boolean;         // Require user confirmation
      sensor_triggers?: Array<{         // Advance based on sensor values
        sensor_type: string;
        condition: 'above' | 'below' | 'stable';
        value: number;
        duration_hours: number;
      }>;
    };
  }>;
  
  // Instance-specific data (only for type: 'instance')
  instance_data?: {
    device_id: string;                  // Associated device
    started_at: Date;                   // Program start time
    current_phase: string;              // Current phase_id
    status: 'running' | 'paused' | 'completed' | 'error' | 'stopped';
    
    // Progress tracking
    progress: {
      total_days_elapsed: number;
      current_phase_days_elapsed: number;
      completion_percentage: number;
    };
    
    // Action log for this instance
    action_log: Array<{
      timestamp: Date;
      action_type: 'pump_command' | 'phase_transition' | 'user_intervention' | 'alert';
      details: Record<string, any>;
      triggered_by: 'automation' | 'user' | 'schedule' | 'sensor_threshold';
      result: 'success' | 'error' | 'skipped';
    }>;
    
    // Performance metrics
    metrics: {
      ph_target_achievement: number;    // % time in target range
      tds_target_achievement: number;   // % time in target range
      total_corrections: number;        // Total automation actions
      water_usage_liters?: number;      // Estimated water consumption
      nutrient_usage?: Record<string, number>; // Nutrient consumption tracking
    };
    
    // Instance settings (can override template)
    overrides?: {
      phase_modifications?: Record<string, Partial<any>>; // Phase-specific overrides
      safety_limits?: Record<string, number>; // Custom safety limits
      notification_preferences?: Record<string, boolean>; // Alert preferences
    };
  };
  
  // Template metadata
  author?: string;                      // Template creator
  version: string;                      // Template version (e.g., "1.0.0")
  is_public: boolean;                   // Available to other users
  usage_count?: number;                 // How often template is used
  
  // Timestamps
  created_at: Date;
  updated_at: Date;
  last_used?: Date;                     // Last time template was instantiated
}
```

**Beispiel Template-Dokument**:
```json
{
  "_id": ObjectId("..."),
  "template_id": "lettuce_30day_v1",
  "name": "Lettuce 30-Day Growth",
  "description": "Optimized 30-day lettuce growth program with 3 phases",
  "type": "template",
  "tags": ["lettuce", "leafy_greens", "beginner", "30_days"],
  "crop_type": "lettuce",
  "duration_days": 30,
  "phases": [
    {
      "phase_id": "germination",
      "name": "Germination",
      "duration_days": 7,
      "start_day": 0,
      "targets": {
        "ph": { "min": 5.8, "max": 6.2, "optimal": 6.0 },
        "tds": { "min": 200, "max": 350, "optimal": 275 }
      },
      "nutrients": {
        "nutrient_a": 40,
        "nutrient_b": 40,
        "cal_mag": 20
      },
      "pump_cycles": {
        "water": {
          "interval_minutes": 60,
          "duration_seconds": 180,
          "enabled": true
        },
        "air": {
          "interval_minutes": 30,
          "duration_seconds": 300,
          "enabled": true
        }
      }
    }
    // ... weitere Phasen
  ],
  "author": "HomeGrow Team",
  "version": "1.0.0",
  "is_public": true,
  "usage_count": 0,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

## Indexing Strategy

### devices Collection Indexes
```javascript
// Primary device lookup
db.devices.createIndex({ device_id: 1 }, { unique: true });

// Status and type filtering
db.devices.createIndex({ status: 1, type: 1 });

// MQTT client discovery
db.devices.createIndex({ "mqtt_info.client_id": 1 });

// Location-based queries
db.devices.createIndex({ location: 1 });

// Maintenance scheduling
db.devices.createIndex({ "stats.last_maintenance": 1 });
```

### sensor_data Collection Indexes
```javascript
// Primary time-series queries (device + time)
db.sensor_data.createIndex({ device_id: 1, timestamp: -1 });

// Recent data queries (all devices)
db.sensor_data.createIndex({ timestamp: -1 });

// Sensor type filtering
db.sensor_data.createIndex({ device_id: 1, sensor_type: 1, timestamp: -1 });

// Data quality analysis
db.sensor_data.createIndex({ quality: 1, timestamp: -1 });

// Program correlation
db.sensor_data.createIndex({ "context.program_instance": 1, timestamp: -1 });

// TTL Index for automatic cleanup (30 days)
db.sensor_data.createIndex({ timestamp: 1 }, { expireAfterSeconds: 2592000 });
```

### program_templates Collection Indexes
```javascript
// Template lookups
db.program_templates.createIndex({ template_id: 1 }, { unique: true });

// Type separation (templates vs instances)
db.program_templates.createIndex({ type: 1 });

// Instance device lookup
db.program_templates.createIndex({ "instance_data.device_id": 1, type: 1 });

// Instance status filtering
db.program_templates.createIndex({ "instance_data.status": 1, type: 1 });

// Public template discovery
db.program_templates.createIndex({ is_public: 1, type: 1 });

// Tag-based search
db.program_templates.createIndex({ tags: 1, type: 1 });

// Crop type filtering
db.program_templates.createIndex({ crop_type: 1, type: 1 });
```

## Data Aggregation Pipelines

### Current Device Status
```javascript
// Get current status of all devices with latest sensor readings
db.devices.aggregate([
  {
    $lookup: {
      from: "sensor_data",
      let: { deviceId: "$device_id" },
      pipeline: [
        { $match: { $expr: { $eq: ["$device_id", "$$deviceId"] } } },
        { $sort: { timestamp: -1 } },
        { $group: {
          _id: "$sensor_type",
          latest_value: { $first: "$values.calibrated" },
          latest_timestamp: { $first: "$timestamp" },
          quality: { $first: "$quality" }
        }}
      ],
      as: "latest_sensors"
    }
  },
  {
    $project: {
      device_id: 1,
      name: 1,
      status: 1,
      last_seen: 1,
      latest_sensors: 1
    }
  }
]);
```

### Program Performance Analytics
```javascript
// Analyze program performance metrics
db.program_templates.aggregate([
  { $match: { type: "instance", "instance_data.status": { $in: ["completed", "running"] } } },
  {
    $group: {
      _id: "$template_id",
      total_instances: { $sum: 1 },
      avg_ph_achievement: { $avg: "$instance_data.metrics.ph_target_achievement" },
      avg_tds_achievement: { $avg: "$instance_data.metrics.tds_target_achievement" },
      total_corrections: { $sum: "$instance_data.metrics.total_corrections" },
      completion_rate: {
        $avg: {
          $cond: [
            { $eq: ["$instance_data.status", "completed"] },
            1,
            0
          ]
        }
      }
    }
  },
  {
    $lookup: {
      from: "program_templates",
      localField: "_id",
      foreignField: "template_id",
      as: "template_info"
    }
  }
]);
```

## Data Retention Strategy

### Automatic Cleanup
```javascript
// TTL Index cleanup für sensor_data (30 Tage)
db.sensor_data.createIndex({ timestamp: 1 }, { expireAfterSeconds: 2592000 });

// Manual cleanup für alte program instances (90 Tage nach completion)
db.program_templates.deleteMany({
  type: "instance",
  "instance_data.status": { $in: ["completed", "stopped"] },
  updated_at: { $lt: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000) }
});
```

### Data Archiving
```javascript
// Aggregate alte sensor readings in hourly summaries
db.sensor_data_hourly.insertMany(
  db.sensor_data.aggregate([
    {
      $match: {
        timestamp: { $lt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) }
      }
    },
    {
      $group: {
        _id: {
          device_id: "$device_id",
          sensor_type: "$sensor_type",
          hour: { $dateToString: { format: "%Y-%m-%d-%H", date: "$timestamp" } }
        },
        avg_value: { $avg: "$values.calibrated" },
        min_value: { $min: "$values.calibrated" },
        max_value: { $max: "$values.calibrated" },
        count: { $sum: 1 },
        first_timestamp: { $min: "$timestamp" },
        last_timestamp: { $max: "$timestamp" }
      }
    }
  ])
);
```

## Performance Considerations

### Collection Size Estimates
- **devices**: ~50 documents @ 5KB each = 250KB
- **sensor_data**: ~100K documents/month @ 500B each = 50MB/month
- **program_templates**: ~100 templates + 500 instances @ 10KB each = 6MB

**Total: ~56MB/month storage growth**

### Query Performance
- Primary indexes unterstützen 95% der App-Queries
- Time-series queries für sensor_data sind hochoptimiert
- Aggregation pipelines verwenden nur indexierte Fields
- TTL Index verhindert unbegrenztes Wachstum

### Connection Pooling
```javascript
// MongoDB connection configuration
const mongoConfig = {
  maxPoolSize: 10,          // Maximum connections
  minPoolSize: 5,           // Minimum connections
  maxIdleTimeMS: 30000,     // Close connections after 30s idle
  serverSelectionTimeoutMS: 5000, // Timeout for server selection
  compressors: ['zlib']     // Data compression
};
```

Diese Database-Schema bietet eine solide, skalierbare Grundlage für HomeGrow v3 mit optimaler Performance und minimaler Komplexität. 