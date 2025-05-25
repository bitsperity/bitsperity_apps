const { MongoClient, ObjectId } = require('mongodb');
const { getDatabase } = require('../config/database');

class ProgramModel {
  constructor() {
    this.collection = null;
  }

  async initialize() {
    const db = await getDatabase();
    this.collection = db.collection('programs');
    
    // Erstelle Indizes
    await this.collection.createIndex({ device_id: 1 });
    await this.collection.createIndex({ name: 1 });
    await this.collection.createIndex({ enabled: 1 });
    await this.collection.createIndex({ created_at: 1 });
    await this.collection.createIndex({ last_run: 1 });
  }

  /**
   * Erstellt ein neues Programm
   */
  async createProgram(programData) {
    const program = {
      name: programData.name,
      description: programData.description || '',
      device_id: programData.device_id,
      enabled: programData.enabled !== undefined ? programData.enabled : true,
      
      // Programm-Konfiguration
      schedule: {
        type: programData.schedule?.type || 'manual', // manual, interval, cron, sensor_trigger
        interval_minutes: programData.schedule?.interval_minutes || null,
        cron_expression: programData.schedule?.cron_expression || null,
        start_time: programData.schedule?.start_time || null,
        end_time: programData.schedule?.end_time || null
      },
      
      // Bedingungen (alle müssen erfüllt sein)
      conditions: programData.conditions || [],
      
      // Aktionen (werden nacheinander ausgeführt)
      actions: programData.actions || [],
      
      // Statistiken
      stats: {
        total_runs: 0,
        successful_runs: 0,
        failed_runs: 0,
        last_run: null,
        last_success: null,
        last_failure: null,
        average_duration_ms: 0
      },
      
      // Metadaten
      created_at: new Date(),
      updated_at: new Date(),
      created_by: programData.created_by || 'system'
    };

    const result = await this.collection.insertOne(program);
    return { ...program, _id: result.insertedId };
  }

  /**
   * Holt alle Programme für ein Gerät
   */
  async getProgramsByDevice(deviceId) {
    return await this.collection
      .find({ device_id: deviceId })
      .sort({ created_at: -1 })
      .toArray();
  }

  /**
   * Holt alle aktiven Programme
   */
  async getActivePrograms() {
    return await this.collection
      .find({ enabled: true })
      .sort({ created_at: -1 })
      .toArray();
  }

  /**
   * Holt ein Programm nach ID
   */
  async getProgramById(programId) {
    return await this.collection.findOne({ _id: new ObjectId(programId) });
  }

  /**
   * Aktualisiert ein Programm
   */
  async updateProgram(programId, updateData) {
    const update = {
      ...updateData,
      updated_at: new Date()
    };

    const result = await this.collection.updateOne(
      { _id: new ObjectId(programId) },
      { $set: update }
    );

    return result.modifiedCount > 0;
  }

  /**
   * Aktiviert/Deaktiviert ein Programm
   */
  async toggleProgram(programId, enabled) {
    const result = await this.collection.updateOne(
      { _id: new ObjectId(programId) },
      { 
        $set: { 
          enabled: enabled,
          updated_at: new Date()
        }
      }
    );

    return result.modifiedCount > 0;
  }

  /**
   * Löscht ein Programm
   */
  async deleteProgram(programId) {
    const result = await this.collection.deleteOne({ _id: new ObjectId(programId) });
    return result.deletedCount > 0;
  }

  /**
   * Aktualisiert Programm-Statistiken nach Ausführung
   */
  async updateProgramStats(programId, success, durationMs, error = null) {
    const program = await this.getProgramById(programId);
    if (!program) return false;

    const stats = program.stats;
    const newTotalRuns = stats.total_runs + 1;
    const newSuccessfulRuns = success ? stats.successful_runs + 1 : stats.successful_runs;
    const newFailedRuns = success ? stats.failed_runs : stats.failed_runs + 1;
    
    // Berechne durchschnittliche Ausführungszeit
    const avgDuration = stats.average_duration_ms || 0;
    const newAvgDuration = ((avgDuration * stats.total_runs) + durationMs) / newTotalRuns;

    const update = {
      'stats.total_runs': newTotalRuns,
      'stats.successful_runs': newSuccessfulRuns,
      'stats.failed_runs': newFailedRuns,
      'stats.last_run': new Date(),
      'stats.average_duration_ms': Math.round(newAvgDuration),
      updated_at: new Date()
    };

    if (success) {
      update['stats.last_success'] = new Date();
    } else {
      update['stats.last_failure'] = new Date();
      update['stats.last_error'] = error;
    }

    const result = await this.collection.updateOne(
      { _id: new ObjectId(programId) },
      { $set: update }
    );

    return result.modifiedCount > 0;
  }

  /**
   * Holt Programme die ausgeführt werden sollen (basierend auf Schedule)
   */
  async getProgramsToRun() {
    const now = new Date();
    
    // Hole alle aktiven Programme
    const activePrograms = await this.getActivePrograms();
    
    const programsToRun = [];
    
    for (const program of activePrograms) {
      const schedule = program.schedule;
      
      switch (schedule.type) {
        case 'interval':
          if (this.shouldRunInterval(program, now)) {
            programsToRun.push(program);
          }
          break;
          
        case 'cron':
          if (this.shouldRunCron(program, now)) {
            programsToRun.push(program);
          }
          break;
          
        case 'sensor_trigger':
          // Sensor-basierte Trigger werden separat behandelt
          break;
      }
    }
    
    return programsToRun;
  }

  /**
   * Prüft ob ein Intervall-Programm ausgeführt werden soll
   */
  shouldRunInterval(program, now) {
    const schedule = program.schedule;
    const lastRun = program.stats.last_run;
    
    if (!schedule.interval_minutes || schedule.interval_minutes <= 0) {
      return false;
    }
    
    // Prüfe Start-/Endzeit
    if (schedule.start_time || schedule.end_time) {
      const currentTime = now.getHours() * 60 + now.getMinutes();
      
      if (schedule.start_time) {
        const [startHour, startMin] = schedule.start_time.split(':').map(Number);
        const startTime = startHour * 60 + startMin;
        if (currentTime < startTime) return false;
      }
      
      if (schedule.end_time) {
        const [endHour, endMin] = schedule.end_time.split(':').map(Number);
        const endTime = endHour * 60 + endMin;
        if (currentTime > endTime) return false;
      }
    }
    
    // Prüfe Intervall
    if (!lastRun) {
      return true; // Erstes Mal ausführen
    }
    
    const intervalMs = schedule.interval_minutes * 60 * 1000;
    const timeSinceLastRun = now.getTime() - lastRun.getTime();
    
    return timeSinceLastRun >= intervalMs;
  }

  /**
   * Prüft ob ein Cron-Programm ausgeführt werden soll
   */
  shouldRunCron(program, now) {
    // Vereinfachte Cron-Implementierung
    // Format: "minute hour day month weekday"
    const schedule = program.schedule;
    const cronExpression = schedule.cron_expression;
    
    if (!cronExpression) return false;
    
    try {
      const parts = cronExpression.split(' ');
      if (parts.length !== 5) return false;
      
      const [minute, hour, day, month, weekday] = parts;
      
      const currentMinute = now.getMinutes();
      const currentHour = now.getHours();
      const currentDay = now.getDate();
      const currentMonth = now.getMonth() + 1;
      const currentWeekday = now.getDay();
      
      // Prüfe jedes Feld
      if (!this.matchesCronField(minute, currentMinute)) return false;
      if (!this.matchesCronField(hour, currentHour)) return false;
      if (!this.matchesCronField(day, currentDay)) return false;
      if (!this.matchesCronField(month, currentMonth)) return false;
      if (!this.matchesCronField(weekday, currentWeekday)) return false;
      
      // Prüfe ob bereits in dieser Minute ausgeführt
      const lastRun = program.stats.last_run;
      if (lastRun) {
        const lastRunMinute = lastRun.getMinutes();
        const lastRunHour = lastRun.getHours();
        const lastRunDay = lastRun.getDate();
        
        if (lastRunMinute === currentMinute && 
            lastRunHour === currentHour && 
            lastRunDay === currentDay) {
          return false;
        }
      }
      
      return true;
    } catch (error) {
      console.error('Error parsing cron expression:', error);
      return false;
    }
  }

  /**
   * Prüft ob ein Cron-Feld mit dem aktuellen Wert übereinstimmt
   */
  matchesCronField(cronField, currentValue) {
    if (cronField === '*') return true;
    
    // Einzelwert
    if (!isNaN(cronField)) {
      return parseInt(cronField) === currentValue;
    }
    
    // Bereich (z.B. "1-5")
    if (cronField.includes('-')) {
      const [start, end] = cronField.split('-').map(Number);
      return currentValue >= start && currentValue <= end;
    }
    
    // Liste (z.B. "1,3,5")
    if (cronField.includes(',')) {
      const values = cronField.split(',').map(Number);
      return values.includes(currentValue);
    }
    
    // Schritt (z.B. "*/5")
    if (cronField.includes('/')) {
      const [base, step] = cronField.split('/');
      const stepValue = parseInt(step);
      
      if (base === '*') {
        return currentValue % stepValue === 0;
      }
    }
    
    return false;
  }

  /**
   * Holt Programme die durch Sensor-Trigger ausgeführt werden sollen
   */
  async getProgramsForSensorTrigger(deviceId, sensorType, sensorValue) {
    const programs = await this.collection
      .find({ 
        device_id: deviceId,
        enabled: true,
        'schedule.type': 'sensor_trigger'
      })
      .toArray();
    
    const triggeredPrograms = [];
    
    for (const program of programs) {
      if (this.checkSensorConditions(program, sensorType, sensorValue)) {
        triggeredPrograms.push(program);
      }
    }
    
    return triggeredPrograms;
  }

  /**
   * Prüft ob Sensor-Bedingungen erfüllt sind
   */
  checkSensorConditions(program, sensorType, sensorValue) {
    const conditions = program.conditions || [];
    
    for (const condition of conditions) {
      if (condition.type === 'sensor' && condition.sensor_type === sensorType) {
        const operator = condition.operator;
        const threshold = condition.value;
        
        switch (operator) {
          case 'greater_than':
            if (sensorValue <= threshold) return false;
            break;
          case 'less_than':
            if (sensorValue >= threshold) return false;
            break;
          case 'equals':
            if (Math.abs(sensorValue - threshold) > 0.1) return false;
            break;
          case 'between':
            const min = condition.min_value;
            const max = condition.max_value;
            if (sensorValue < min || sensorValue > max) return false;
            break;
          default:
            return false;
        }
      }
    }
    
    return true;
  }

  /**
   * Validiert Programm-Daten
   */
  validateProgram(programData) {
    const errors = [];
    
    if (!programData.name || programData.name.trim().length === 0) {
      errors.push('Programmname ist erforderlich');
    }
    
    if (!programData.device_id) {
      errors.push('Geräte-ID ist erforderlich');
    }
    
    if (!programData.schedule || !programData.schedule.type) {
      errors.push('Schedule-Typ ist erforderlich');
    }
    
    if (programData.schedule?.type === 'interval' && !programData.schedule.interval_minutes) {
      errors.push('Intervall in Minuten ist erforderlich');
    }
    
    if (programData.schedule?.type === 'cron' && !programData.schedule.cron_expression) {
      errors.push('Cron-Ausdruck ist erforderlich');
    }
    
    if (!programData.actions || programData.actions.length === 0) {
      errors.push('Mindestens eine Aktion ist erforderlich');
    }
    
    // Validiere Aktionen
    if (programData.actions) {
      programData.actions.forEach((action, index) => {
        if (!action.type) {
          errors.push(`Aktion ${index + 1}: Typ ist erforderlich`);
        }
        
        if (action.type === 'pump' && !action.pump_id) {
          errors.push(`Aktion ${index + 1}: Pumpen-ID ist erforderlich`);
        }
        
        if (action.type === 'pump' && (!action.duration_seconds || action.duration_seconds <= 0)) {
          errors.push(`Aktion ${index + 1}: Gültige Dauer ist erforderlich`);
        }
      });
    }
    
    return errors;
  }
}

module.exports = new ProgramModel(); 