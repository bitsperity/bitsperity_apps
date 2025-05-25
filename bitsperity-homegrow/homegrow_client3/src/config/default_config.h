#ifndef DEFAULT_CONFIG_H
#define DEFAULT_CONFIG_H

// HomeGrow Client v3 Default-Konfiguration
const char* DEFAULT_CONFIG_JSON = R"({
  "device": {
    "id": "homegrow_client_001",
    "name": "HomeGrow Client v3",
    "location": "Gewächshaus",
    "firmware_version": "3.0.0",
    "hardware_version": "1.0"
  },
  "wifi": {
    "ssid": "",
    "password": "",
    "hostname": "homegrow-client-001",
    "static_ip": null,
    "dns_servers": ["8.8.8.8", "8.8.4.4"]
  },
  "mqtt": {
    "broker_discovery": {
      "enabled": true,
      "service_name": "_mqtt._tcp",
      "fallback_host": "192.168.1.100",
      "fallback_port": 1883
    },
    "auth": {
      "username": "homegrow_client",
      "password": ""
    },
    "qos": 1,
    "retain": false,
    "keepalive": 60,
    "clean_session": true
  },
  "sensors": {
    "ph": {
      "enabled": true,
      "pin": 34,
      "calibration": {
        "type": "multi_point",
        "points": [
          {"raw": 2252, "ph": 4.0},
          {"raw": 1721, "ph": 7.0}
        ]
      },
      "noise_filter": {
        "enabled": true,
        "type": "moving_average",
        "window_size": 10,
        "outlier_threshold": 2.0
      },
      "publishing": {
        "rate_hz": 1.0,
        "publish_raw": true,
        "publish_calibrated": true,
        "publish_filtered": true
      }
    },
    "tds": {
      "enabled": true,
      "pin": 35,
      "calibration": {
        "type": "single_point",
        "reference_point": {"raw": 1156, "tds": 342}
      },
      "noise_filter": {
        "enabled": true,
        "type": "exponential",
        "alpha": 0.1,
        "outlier_threshold": 100.0
      },
      "publishing": {
        "rate_hz": 0.5,
        "publish_raw": true,
        "publish_calibrated": true,
        "publish_filtered": true
      }
    }
  },
  "actuators": {
    "water_pump": {
      "enabled": true,
      "pin": 16,
      "type": "relay",
      "flow_rate_ml_per_sec": 50.0,
      "max_runtime_sec": 300,
      "cooldown_sec": 60,
      "scheduled": {
        "enabled": false,
        "interval_minutes": 30,
        "duration_seconds": 120
      }
    },
    "air_pump": {
      "enabled": true,
      "pin": 17,
      "type": "relay",
      "max_runtime_sec": 1800,
      "cooldown_sec": 30,
      "scheduled": {
        "enabled": false,
        "interval_minutes": 15,
        "duration_seconds": 300
      }
    },
    "dosing_pumps": [
      {
        "id": "ph_down",
        "enabled": true,
        "pin": 18,
        "type": "peristaltic",
        "flow_rate_ml_per_sec": 0.5,
        "max_runtime_sec": 60,
        "cooldown_sec": 300,
        "substance": "pH Down",
        "concentration": "85%"
      },
      {
        "id": "ph_up",
        "enabled": true,
        "pin": 19,
        "type": "peristaltic",
        "flow_rate_ml_per_sec": 0.5,
        "max_runtime_sec": 60,
        "cooldown_sec": 300,
        "substance": "pH Up",
        "concentration": "40%"
      },
      {
        "id": "nutrient_a",
        "enabled": true,
        "pin": 20,
        "type": "peristaltic",
        "flow_rate_ml_per_sec": 1.0,
        "max_runtime_sec": 120,
        "cooldown_sec": 60,
        "substance": "Nutrient A",
        "concentration": "100%"
      },
      {
        "id": "nutrient_b",
        "enabled": true,
        "pin": 21,
        "type": "peristaltic",
        "flow_rate_ml_per_sec": 1.0,
        "max_runtime_sec": 120,
        "cooldown_sec": 60,
        "substance": "Nutrient B",
        "concentration": "100%"
      },
      {
        "id": "cal_mag",
        "enabled": true,
        "pin": 22,
        "type": "peristaltic",
        "flow_rate_ml_per_sec": 0.8,
        "max_runtime_sec": 90,
        "cooldown_sec": 120,
        "substance": "Cal-Mag",
        "concentration": "100%"
      }
    ]
  },
  "safety": {
    "emergency_stop_conditions": {
      "ph_min": 4.0,
      "ph_max": 8.5,
      "tds_max": 2000
    },
    "pump_protection": {
      "max_runtime_sec": 300,
      "cooldown_sec": 60
    },
    "sensor_validation": {
      "outlier_threshold": 2.0,
      "plausibility_checks": true
    }
  },
  "system": {
    "watchdog": {
      "enabled": true,
      "timeout_sec": 30
    },
    "ota": {
      "enabled": true,
      "password": "homegrow_ota",
      "port": 3232
    },
    "logging": {
      "level": "INFO",
      "serial": true,
      "mqtt": true
    },
    "status": {
      "heartbeat_interval_sec": 30
    }
  }
})";

#endif // DEFAULT_CONFIG_H 