import { EventEmitter } from 'events';
import ProgramModel from '../models/program.js';
import deviceModel from '../models/device.js';
import sensorDataModel from '../models/sensor-data.js';

class ProgramEngine extends EventEmitter {
  constructor() {
    super();
    this.isRunning = false;
    this.schedulerInterval = null;
    this.runningPrograms = new Map(); // programId -> execution info
    this.mqttBridge = null;
    this.programModel = null;
  }

  /**
   * Initialisiert die Program Engine
   */
  async initialize(mqttBridge, db) {
    this.mqttBridge = mqttBridge;
    
    // Initialisiere Program Model
    this.programModel = new ProgramModel(db);
    await this.programModel.initialize();
    
    console.log('Program Engine initialized');
  }

  /**
   * Startet die Program Engine
   */
  start() {
    if (this.isRunning) {
      console.log('Program Engine is already running');
      return;
    }

    this.isRunning = true;
    
    // Starte Scheduler (prüft jede Minute)
    this.schedulerInterval = setInterval(() => {
      this.runScheduler();
    }, 60000); // 60 Sekunden

    // Führe Scheduler sofort einmal aus
    this.runScheduler();

    console.log('Program Engine started');
    this.emit('engine-started');
  }

  /**
   * Stoppt die Program Engine
   */
  stop() {
    if (!this.isRunning) {
      console.log('Program Engine is not running');
      return;
    }

    this.isRunning = false;

    if (this.schedulerInterval) {
      clearInterval(this.schedulerInterval);
      this.schedulerInterval = null;
    }

    // Stoppe alle laufenden Programme
    for (const [programId, execution] of this.runningPrograms) {
      this.stopProgramExecution(programId);
    }

    console.log('Program Engine stopped');
    this.emit('engine-stopped');
  }

  /**
   * Scheduler - prüft welche Programme ausgeführt werden sollen
   */
  async runScheduler() {
    if (!this.isRunning) return;

    try {
      // Hole Programme die ausgeführt werden sollen
      const programsToRun = await this.programModel.getProgramsToRun();
      
      for (const program of programsToRun) {
        // Prüfe ob Programm bereits läuft
        if (this.runningPrograms.has(program._id.toString())) {
          continue;
        }

        // Prüfe Bedingungen
        const conditionsMet = await this.checkProgramConditions(program);
        if (!conditionsMet) {
          continue;
        }

        // Führe Programm aus
        this.executeProgram(program);
      }
    } catch (error) {
      console.error('Error in scheduler:', error);
      this.emit('scheduler-error', error);
    }
  }

  /**
   * Prüft ob alle Bedingungen eines Programms erfüllt sind
   */
  async checkProgramConditions(program) {
    const conditions = program.conditions || [];
    
    for (const condition of conditions) {
      switch (condition.type) {
        case 'sensor':
          const sensorMet = await this.checkSensorCondition(program.device_id, condition);
          if (!sensorMet) return false;
          break;
          
        case 'time':
          const timeMet = this.checkTimeCondition(condition);
          if (!timeMet) return false;
          break;
          
        case 'device_status':
          const deviceMet = await this.checkDeviceCondition(program.device_id, condition);
          if (!deviceMet) return false;
          break;
          
        default:
          console.warn(`Unknown condition type: ${condition.type}`);
          return false;
      }
    }
    
    return true;
  }

  /**
   * Prüft Sensor-Bedingung
   */
  async checkSensorCondition(deviceId, condition) {
    try {
      const latestReading = await sensorDataModel.getLatestReading(deviceId, condition.sensor_type);
      if (!latestReading) return false;

      const sensorValue = latestReading.values.calibrated;
      const operator = condition.operator;
      const threshold = condition.value;

      switch (operator) {
        case 'greater_than':
          return sensorValue > threshold;
        case 'less_than':
          return sensorValue < threshold;
        case 'equals':
          return Math.abs(sensorValue - threshold) <= 0.1;
        case 'between':
          return sensorValue >= condition.min_value && sensorValue <= condition.max_value;
        default:
          return false;
      }
    } catch (error) {
      console.error('Error checking sensor condition:', error);
      return false;
    }
  }

  /**
   * Prüft Zeit-Bedingung
   */
  checkTimeCondition(condition) {
    const now = new Date();
    const currentTime = now.getHours() * 60 + now.getMinutes();

    if (condition.start_time) {
      const [startHour, startMin] = condition.start_time.split(':').map(Number);
      const startTime = startHour * 60 + startMin;
      if (currentTime < startTime) return false;
    }

    if (condition.end_time) {
      const [endHour, endMin] = condition.end_time.split(':').map(Number);
      const endTime = endHour * 60 + endMin;
      if (currentTime > endTime) return false;
    }

    return true;
  }

  /**
   * Prüft Geräte-Status-Bedingung
   */
  async checkDeviceCondition(deviceId, condition) {
    try {
      const device = await deviceModel.getDeviceById(deviceId);
      if (!device) return false;

      switch (condition.operator) {
        case 'equals':
          return device.status === condition.value;
        case 'not_equals':
          return device.status !== condition.value;
        default:
          return false;
      }
    } catch (error) {
      console.error('Error checking device condition:', error);
      return false;
    }
  }

  /**
   * Führt ein Programm aus
   */
  async executeProgram(program) {
    const programId = program._id.toString();
    const startTime = Date.now();

    console.log(`Executing program: ${program.name} (${programId})`);

    // Markiere Programm als laufend
    this.runningPrograms.set(programId, {
      program,
      startTime,
      currentActionIndex: 0
    });

    this.emit('program-started', { programId, program });

    try {
      // Führe alle Aktionen nacheinander aus
      for (let i = 0; i < program.actions.length; i++) {
        const action = program.actions[i];
        
        // Update current action index
        const execution = this.runningPrograms.get(programId);
        if (execution) {
          execution.currentActionIndex = i;
        }

        await this.executeAction(program.device_id, action);
        
        // Warte zwischen Aktionen (falls konfiguriert)
        if (action.delay_after_seconds && action.delay_after_seconds > 0) {
          await this.sleep(action.delay_after_seconds * 1000);
        }
      }

      // Programm erfolgreich abgeschlossen
      const duration = Date.now() - startTime;
      await this.programModel.updateProgramStats(programId, true, duration);
      
      console.log(`Program completed successfully: ${program.name} (${duration}ms)`);
      this.emit('program-completed', { programId, program, duration, success: true });

    } catch (error) {
      // Programm fehlgeschlagen
      const duration = Date.now() - startTime;
      await this.programModel.updateProgramStats(programId, false, duration, error.message);
      
      console.error(`Program failed: ${program.name}`, error);
      this.emit('program-failed', { programId, program, duration, error: error.message });

    } finally {
      // Entferne Programm aus laufenden Programmen
      this.runningPrograms.delete(programId);
    }
  }

  /**
   * Führt eine einzelne Aktion aus
   */
  async executeAction(deviceId, action) {
    console.log(`Executing action: ${action.type}`, action);

    switch (action.type) {
      case 'pump':
        await this.executePumpAction(deviceId, action);
        break;
        
      case 'wait':
        await this.executeWaitAction(action);
        break;
        
      case 'notification':
        await this.executeNotificationAction(action);
        break;
        
      case 'sensor_reading':
        await this.executeSensorReadingAction(deviceId, action);
        break;
        
      default:
        throw new Error(`Unknown action type: ${action.type}`);
    }
  }

  /**
   * Führt Pumpen-Aktion aus
   */
  async executePumpAction(deviceId, action) {
    if (!this.mqttBridge) {
      throw new Error('MQTT Bridge not available');
    }

    const command = {
      type: 'pump_control',
      pump_id: action.pump_id,
      duration_seconds: action.duration_seconds,
      flow_rate: action.flow_rate || 100 // Default 100%
    };

    // Sende Befehl über MQTT
    await this.mqttBridge.sendCommand(deviceId, command);
    
    // Warte bis Pumpe fertig ist
    await this.sleep(action.duration_seconds * 1000);
  }

  /**
   * Führt Warte-Aktion aus
   */
  async executeWaitAction(action) {
    const waitTime = action.duration_seconds * 1000;
    await this.sleep(waitTime);
  }

  /**
   * Führt Benachrichtigungs-Aktion aus
   */
  async executeNotificationAction(action) {
    this.emit('program-notification', {
      type: action.notification_type || 'info',
      title: action.title || 'Programm-Benachrichtigung',
      message: action.message || 'Aktion ausgeführt'
    });
  }

  /**
   * Führt Sensor-Lesung-Aktion aus
   */
  async executeSensorReadingAction(deviceId, action) {
    if (!this.mqttBridge) {
      throw new Error('MQTT Bridge not available');
    }

    const command = {
      type: 'read_sensors',
      sensor_types: action.sensor_types || ['ph', 'tds', 'temperature']
    };

    // Sende Befehl über MQTT
    await this.mqttBridge.sendCommand(deviceId, command);
  }

  /**
   * Stoppt die Ausführung eines Programms
   */
  stopProgramExecution(programId) {
    if (this.runningPrograms.has(programId)) {
      const execution = this.runningPrograms.get(programId);
      this.runningPrograms.delete(programId);
      
      console.log(`Program execution stopped: ${execution.program.name}`);
      this.emit('program-stopped', { programId, program: execution.program });
    }
  }

  /**
   * Führt ein Programm manuell aus
   */
  async runProgramManually(programId) {
    try {
      const program = await this.programModel.getProgramById(programId);
      if (!program) {
        throw new Error('Program not found');
      }

      if (!program.enabled) {
        throw new Error('Program is disabled');
      }

      // Prüfe ob Programm bereits läuft
      if (this.runningPrograms.has(programId)) {
        throw new Error('Program is already running');
      }

      // Prüfe Bedingungen (außer Schedule)
      const conditionsMet = await this.checkProgramConditions(program);
      if (!conditionsMet) {
        throw new Error('Program conditions not met');
      }

      // Führe Programm aus
      await this.executeProgram(program);
      
      return { success: true, message: 'Program executed successfully' };
    } catch (error) {
      console.error('Error running program manually:', error);
      throw error;
    }
  }

  /**
   * Behandelt Sensor-Trigger
   */
  async handleSensorTrigger(deviceId, sensorType, sensorValue) {
    try {
      const triggeredPrograms = await this.programModel.getProgramsForSensorTrigger(
        deviceId, 
        sensorType, 
        sensorValue
      );

      for (const program of triggeredPrograms) {
        // Prüfe ob Programm bereits läuft
        if (this.runningPrograms.has(program._id.toString())) {
          continue;
        }

        // Prüfe andere Bedingungen (außer Sensor-Trigger)
        const otherConditionsMet = await this.checkNonSensorConditions(program);
        if (!otherConditionsMet) {
          continue;
        }

        // Führe Programm aus
        this.executeProgram(program);
      }
    } catch (error) {
      console.error('Error handling sensor trigger:', error);
    }
  }

  /**
   * Prüft alle Bedingungen außer Sensor-Trigger
   */
  async checkNonSensorConditions(program) {
    const conditions = program.conditions || [];
    
    for (const condition of conditions) {
      if (condition.type === 'sensor') continue; // Skip sensor conditions
      
      switch (condition.type) {
        case 'time':
          const timeMet = this.checkTimeCondition(condition);
          if (!timeMet) return false;
          break;
          
        case 'device_status':
          const deviceMet = await this.checkDeviceCondition(program.device_id, condition);
          if (!deviceMet) return false;
          break;
      }
    }
    
    return true;
  }

  /**
   * Holt Status aller laufenden Programme
   */
  getRunningPrograms() {
    const running = [];
    
    for (const [programId, execution] of this.runningPrograms) {
      running.push({
        programId,
        programName: execution.program.name,
        deviceId: execution.program.device_id,
        startTime: execution.startTime,
        currentActionIndex: execution.currentActionIndex,
        totalActions: execution.program.actions.length,
        duration: Date.now() - execution.startTime
      });
    }
    
    return running;
  }

  /**
   * Holt Engine-Status
   */
  getStatus() {
    return {
      isRunning: this.isRunning,
      runningPrograms: this.getRunningPrograms(),
      totalRunningPrograms: this.runningPrograms.size
    };
  }

  /**
   * Hilfsfunktion für Sleep
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

export default ProgramEngine;