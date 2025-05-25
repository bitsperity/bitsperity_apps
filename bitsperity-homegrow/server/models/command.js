const mongoose = require('mongoose');

// Command Schema für Befehlshistorie und -status
const commandSchema = new mongoose.Schema({
  // Eindeutige Command-ID
  commandId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  
  // Gerät, an das der Befehl gesendet wurde
  deviceId: {
    type: String,
    required: true,
    index: true
  },
  
  // Befehlstyp (z.B. 'water_pump', 'ph_calibration', 'emergency_stop')
  commandType: {
    type: String,
    required: true,
    enum: [
      'water_pump',
      'air_pump', 
      'dosing_pump',
      'ph_calibration',
      'tds_calibration',
      'emergency_stop',
      'system_restart',
      'config_update',
      'sensor_reading'
    ]
  },
  
  // Befehlsparameter
  parameters: {
    type: mongoose.Schema.Types.Mixed,
    default: {}
  },
  
  // Aktueller Status des Befehls
  status: {
    type: String,
    required: true,
    enum: ['pending', 'sent', 'acknowledged', 'executing', 'completed', 'failed', 'timeout'],
    default: 'pending',
    index: true
  },
  
  // Quelle des Befehls
  source: {
    type: String,
    required: true,
    enum: ['manual', 'program', 'emergency', 'system', 'websocket', 'api'],
    default: 'manual'
  },
  
  // Benutzer-ID (falls verfügbar)
  userId: {
    type: String,
    default: null
  },
  
  // Priorität des Befehls
  priority: {
    type: String,
    enum: ['low', 'normal', 'high', 'emergency'],
    default: 'normal',
    index: true
  },
  
  // Zeitstempel
  createdAt: {
    type: Date,
    default: Date.now,
    index: true
  },
  
  sentAt: {
    type: Date,
    default: null
  },
  
  acknowledgedAt: {
    type: Date,
    default: null
  },
  
  completedAt: {
    type: Date,
    default: null
  },
  
  // Ausführungszeit in Millisekunden
  executionTimeMs: {
    type: Number,
    default: null
  },
  
  // Antwort vom Gerät
  response: {
    type: mongoose.Schema.Types.Mixed,
    default: null
  },
  
  // Fehlermeldung (falls vorhanden)
  error: {
    type: String,
    default: null
  },
  
  // Timeout-Einstellung (in Millisekunden)
  timeoutMs: {
    type: Number,
    default: 30000 // 30 Sekunden Standard-Timeout
  },
  
  // Anzahl der Wiederholungsversuche
  retryCount: {
    type: Number,
    default: 0
  },
  
  maxRetries: {
    type: Number,
    default: 3
  },
  
  // Metadaten
  metadata: {
    type: mongoose.Schema.Types.Mixed,
    default: {}
  }
}, {
  timestamps: true,
  collection: 'commands'
});

// Indizes für bessere Performance
commandSchema.index({ deviceId: 1, createdAt: -1 });
commandSchema.index({ status: 1, createdAt: -1 });
commandSchema.index({ commandType: 1, createdAt: -1 });
commandSchema.index({ source: 1, createdAt: -1 });
commandSchema.index({ priority: 1, status: 1 });

// TTL-Index für automatische Bereinigung alter Befehle (nach 30 Tagen)
commandSchema.index({ createdAt: 1 }, { expireAfterSeconds: 30 * 24 * 60 * 60 });

// Virtuelle Felder
commandSchema.virtual('isCompleted').get(function() {
  return ['completed', 'failed', 'timeout'].includes(this.status);
});

commandSchema.virtual('isActive').get(function() {
  return ['pending', 'sent', 'acknowledged', 'executing'].includes(this.status);
});

commandSchema.virtual('duration').get(function() {
  if (this.completedAt && this.sentAt) {
    return this.completedAt.getTime() - this.sentAt.getTime();
  }
  return null;
});

// Statische Methoden
commandSchema.statics = {
  
  // Neuen Befehl erstellen
  async createCommand(commandData) {
    try {
      const command = new this({
        commandId: commandData.commandId || `cmd_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        deviceId: commandData.deviceId,
        commandType: commandData.commandType,
        parameters: commandData.parameters || {},
        source: commandData.source || 'manual',
        userId: commandData.userId || null,
        priority: commandData.priority || 'normal',
        timeoutMs: commandData.timeoutMs || 30000,
        maxRetries: commandData.maxRetries || 3,
        metadata: commandData.metadata || {}
      });
      
      await command.save();
      return command;
    } catch (error) {
      throw new Error(`Fehler beim Erstellen des Befehls: ${error.message}`);
    }
  },
  
  // Befehl als gesendet markieren
  async markAsSent(commandId) {
    try {
      const command = await this.findOneAndUpdate(
        { commandId },
        { 
          status: 'sent',
          sentAt: new Date()
        },
        { new: true }
      );
      
      if (!command) {
        throw new Error(`Befehl ${commandId} nicht gefunden`);
      }
      
      return command;
    } catch (error) {
      throw new Error(`Fehler beim Markieren als gesendet: ${error.message}`);
    }
  },
  
  // Antwort vom Gerät verarbeiten
  async updateResponse(commandId, responseData) {
    try {
      const updateData = {
        response: responseData,
        acknowledgedAt: new Date()
      };
      
      // Status basierend auf Antwort setzen
      if (responseData.status === 'completed') {
        updateData.status = 'completed';
        updateData.completedAt = new Date();
        updateData.executionTimeMs = responseData.execution_time_ms || null;
      } else if (responseData.status === 'failed') {
        updateData.status = 'failed';
        updateData.completedAt = new Date();
        updateData.error = responseData.error || 'Unbekannter Fehler';
      } else if (responseData.status === 'executing') {
        updateData.status = 'executing';
      } else {
        updateData.status = 'acknowledged';
      }
      
      const command = await this.findOneAndUpdate(
        { commandId },
        updateData,
        { new: true }
      );
      
      if (!command) {
        throw new Error(`Befehl ${commandId} nicht gefunden`);
      }
      
      return command;
    } catch (error) {
      throw new Error(`Fehler beim Aktualisieren der Antwort: ${error.message}`);
    }
  },
  
  // Timeout-Befehle markieren
  async markTimeoutCommands() {
    try {
      const timeoutThreshold = new Date(Date.now() - 60000); // 1 Minute
      
      const result = await this.updateMany(
        {
          status: { $in: ['pending', 'sent', 'acknowledged', 'executing'] },
          createdAt: { $lt: timeoutThreshold }
        },
        {
          status: 'timeout',
          completedAt: new Date(),
          error: 'Befehl-Timeout erreicht'
        }
      );
      
      return result.modifiedCount;
    } catch (error) {
      throw new Error(`Fehler beim Markieren von Timeout-Befehlen: ${error.message}`);
    }
  },
  
  // Befehle für ein Gerät abrufen
  async getDeviceCommands(deviceId, options = {}) {
    try {
      const {
        limit = 50,
        skip = 0,
        status = null,
        commandType = null,
        startDate = null,
        endDate = null
      } = options;
      
      const query = { deviceId };
      
      if (status) {
        query.status = status;
      }
      
      if (commandType) {
        query.commandType = commandType;
      }
      
      if (startDate || endDate) {
        query.createdAt = {};
        if (startDate) query.createdAt.$gte = new Date(startDate);
        if (endDate) query.createdAt.$lte = new Date(endDate);
      }
      
      const commands = await this.find(query)
        .sort({ createdAt: -1 })
        .limit(limit)
        .skip(skip)
        .lean();
      
      const total = await this.countDocuments(query);
      
      return {
        commands,
        total,
        hasMore: total > skip + commands.length
      };
    } catch (error) {
      throw new Error(`Fehler beim Abrufen der Gerätebefehle: ${error.message}`);
    }
  },
  
  // Befehlsstatistiken abrufen
  async getCommandStats(deviceId = null, timeRange = '24h') {
    try {
      const timeRanges = {
        '1h': 60 * 60 * 1000,
        '24h': 24 * 60 * 60 * 1000,
        '7d': 7 * 24 * 60 * 60 * 1000,
        '30d': 30 * 24 * 60 * 60 * 1000
      };
      
      const timeMs = timeRanges[timeRange] || timeRanges['24h'];
      const startDate = new Date(Date.now() - timeMs);
      
      const matchStage = {
        createdAt: { $gte: startDate }
      };
      
      if (deviceId) {
        matchStage.deviceId = deviceId;
      }
      
      const pipeline = [
        { $match: matchStage },
        {
          $group: {
            _id: '$status',
            count: { $sum: 1 },
            avgExecutionTime: { $avg: '$executionTimeMs' }
          }
        }
      ];
      
      const stats = await this.aggregate(pipeline);
      
      // Formatiere Statistiken
      const result = {
        total: 0,
        completed: 0,
        failed: 0,
        timeout: 0,
        pending: 0,
        avgExecutionTime: 0
      };
      
      stats.forEach(stat => {
        result.total += stat.count;
        result[stat._id] = stat.count;
        if (stat._id === 'completed' && stat.avgExecutionTime) {
          result.avgExecutionTime = Math.round(stat.avgExecutionTime);
        }
      });
      
      return result;
    } catch (error) {
      throw new Error(`Fehler beim Abrufen der Befehlsstatistiken: ${error.message}`);
    }
  },
  
  // Aktive Befehle abrufen
  async getActiveCommands(deviceId = null) {
    try {
      const query = {
        status: { $in: ['pending', 'sent', 'acknowledged', 'executing'] }
      };
      
      if (deviceId) {
        query.deviceId = deviceId;
      }
      
      const commands = await this.find(query)
        .sort({ priority: -1, createdAt: 1 })
        .lean();
      
      return commands;
    } catch (error) {
      throw new Error(`Fehler beim Abrufen aktiver Befehle: ${error.message}`);
    }
  },
  
  // Befehl wiederholen
  async retryCommand(commandId) {
    try {
      const command = await this.findOne({ commandId });
      
      if (!command) {
        throw new Error(`Befehl ${commandId} nicht gefunden`);
      }
      
      if (command.retryCount >= command.maxRetries) {
        throw new Error(`Maximale Anzahl von Wiederholungen erreicht`);
      }
      
      // Neuen Befehl mit erhöhtem Retry-Counter erstellen
      const retryCommand = await this.createCommand({
        deviceId: command.deviceId,
        commandType: command.commandType,
        parameters: command.parameters,
        source: command.source,
        userId: command.userId,
        priority: command.priority,
        timeoutMs: command.timeoutMs,
        maxRetries: command.maxRetries,
        retryCount: command.retryCount + 1,
        metadata: {
          ...command.metadata,
          originalCommandId: command.commandId,
          isRetry: true
        }
      });
      
      return retryCommand;
    } catch (error) {
      throw new Error(`Fehler beim Wiederholen des Befehls: ${error.message}`);
    }
  }
};

// Instance-Methoden
commandSchema.methods = {
  
  // Befehl als fehlgeschlagen markieren
  async markAsFailed(errorMessage) {
    this.status = 'failed';
    this.completedAt = new Date();
    this.error = errorMessage;
    await this.save();
    return this;
  },
  
  // Befehl als abgeschlossen markieren
  async markAsCompleted(responseData = {}) {
    this.status = 'completed';
    this.completedAt = new Date();
    this.response = responseData;
    
    if (this.sentAt) {
      this.executionTimeMs = this.completedAt.getTime() - this.sentAt.getTime();
    }
    
    await this.save();
    return this;
  },
  
  // Prüfen ob Befehl abgelaufen ist
  isExpired() {
    if (!this.sentAt) return false;
    const now = Date.now();
    const expireTime = this.sentAt.getTime() + this.timeoutMs;
    return now > expireTime;
  },
  
  // JSON-Darstellung für API
  toAPIResponse() {
    return {
      commandId: this.commandId,
      deviceId: this.deviceId,
      commandType: this.commandType,
      parameters: this.parameters,
      status: this.status,
      source: this.source,
      priority: this.priority,
      createdAt: this.createdAt,
      sentAt: this.sentAt,
      acknowledgedAt: this.acknowledgedAt,
      completedAt: this.completedAt,
      executionTimeMs: this.executionTimeMs,
      response: this.response,
      error: this.error,
      retryCount: this.retryCount,
      isCompleted: this.isCompleted,
      isActive: this.isActive,
      duration: this.duration
    };
  }
};

// Pre-save Hook für Validierung
commandSchema.pre('save', function(next) {
  // Automatische Zeitstempel-Updates
  if (this.isModified('status')) {
    const now = new Date();
    
    switch (this.status) {
      case 'sent':
        if (!this.sentAt) this.sentAt = now;
        break;
      case 'acknowledged':
        if (!this.acknowledgedAt) this.acknowledgedAt = now;
        break;
      case 'completed':
      case 'failed':
      case 'timeout':
        if (!this.completedAt) this.completedAt = now;
        break;
    }
  }
  
  next();
});

const Command = mongoose.model('Command', commandSchema);

module.exports = Command; 