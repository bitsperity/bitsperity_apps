import { z } from 'zod';
import EventEmitter from 'events';

// Rule validation schema
const RuleSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().optional(),
  enabled: z.boolean().default(true),
  conditions: z.array(z.object({
    deviceId: z.string(),
    sensorType: z.string(),
    operator: z.enum(['>', '<', '>=', '<=', '==', '!=']),
    value: z.number(),
    unit: z.string().optional()
  })),
  actions: z.array(z.object({
    deviceId: z.string(),
    command: z.string(),
    params: z.object({}).optional(),
    delay: z.number().optional().default(0)
  })),
  cooldown: z.number().optional().default(300), // 5 minutes default cooldown
  priority: z.number().min(1).max(10).default(5)
});

class AutomationEngine extends EventEmitter {
  constructor(mqttBridge, db) {
    super();
    this.mqttBridge = mqttBridge;
    this.db = db;
    this.isRunning = false;
    this.rules = new Map();
    this.checkInterval = null;
    
    // Automation-Konfiguration
    this.config = {
      checkIntervalMs: 30000, // Alle 30 Sekunden prüfen
      maxActionsPerRule: 5,   // Max 5 Aktionen pro Regel pro Stunde
      cooldownMs: 300000      // 5 Minuten Abkühlung zwischen Aktionen
    };
    
    this.actionHistory = new Map(); // Tracking für Rate-Limiting
  }

  async start() {
    console.log('🤖 Automation Engine wird gestartet...');
    
    try {
      // Lade alle aktiven Regeln
      await this.loadRules();
      
      // Starte Regel-Prüfung
      this.startRuleEngine();
      
      this.isRunning = true;
      console.log('✅ Automation Engine gestartet');
      this.emit('started');
      
    } catch (error) {
      console.error('❌ Fehler beim Starten der Automation Engine:', error);
      throw error;
    }
  }

  async stop() {
    console.log('🛑 Automation Engine wird gestoppt...');
    
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }
    
    this.isRunning = false;
    console.log('✅ Automation Engine gestoppt');
    this.emit('stopped');
  }

  async loadRules() {
    try {
      const rulesFromDb = await this.db.collection('automation_rules')
        .find({ enabled: true })
        .toArray();
      
      console.log(`📋 ${rulesFromDb.length} aktive Regeln geladen`);
      
      this.rules.clear();
      rulesFromDb.forEach(rule => {
        this.rules.set(rule._id.toString(), rule);
      });
      
    } catch (error) {
      console.error('❌ Fehler beim Laden der Regeln:', error);
      throw error;
    }
  }

  startRuleEngine() {
    this.checkInterval = setInterval(async () => {
      if (this.isRunning) {
        await this.processRules();
      }
    }, this.config.checkIntervalMs);
    
    console.log(`⏱️ Regel-Engine läuft alle ${this.config.checkIntervalMs / 1000}s`);
  }

  async processRules() {
    try {
      for (const [ruleId, rule] of this.rules) {
        await this.evaluateRule(ruleId, rule);
      }
    } catch (error) {
      console.error('❌ Fehler beim Verarbeiten der Regeln:', error);
    }
  }

  async evaluateRule(ruleId, rule) {
    try {
      // Prüfe Cooldown
      if (this.isRuleOnCooldown(ruleId)) {
        return;
      }

      // Evaluiere Regel-Trigger
      const shouldTrigger = await this.evaluateTrigger(rule.trigger);
      
      if (shouldTrigger) {
        console.log(`🎯 Regel "${rule.name}" wird ausgelöst`);
        
        // Führe Aktionen aus
        await this.executeActions(ruleId, rule.actions);
        
        // Update letzte Ausführung
        await this.updateRuleExecution(ruleId);
        
        this.emit('ruleTriggered', { ruleId, rule });
      }
      
    } catch (error) {
      console.error(`❌ Fehler bei Regel "${rule.name}":`, error);
      this.emit('ruleError', { ruleId, rule, error });
    }
  }

  async evaluateTrigger(trigger) {
    switch (trigger.type) {
      case 'sensor_value':
        return await this.evaluateSensorTrigger(trigger);
      case 'time':
        return this.evaluateTimeTrigger(trigger);
      case 'compound':
        return await this.evaluateCompoundTrigger(trigger);
      default:
        console.warn(`⚠️ Unbekannter Trigger-Typ: ${trigger.type}`);
        return false;
    }
  }

  async evaluateSensorTrigger(trigger) {
    const { deviceId, sensorType, operator, value, timeRange = 5 } = trigger;
    
    try {
      // Hole neueste Sensor-Daten
      const latestReading = await this.db.collection('sensor_data').findOne(
        { deviceId, sensorType },
        { sort: { timestamp: -1 } }
      );
      
      if (!latestReading) {
        console.warn(`⚠️ Keine Sensordaten für ${deviceId}/${sensorType}`);
        return false;
      }
      
      // Prüfe ob Daten nicht zu alt sind
      const maxAge = timeRange * 60 * 1000; // Minuten zu Millisekunden
      const dataAge = Date.now() - new Date(latestReading.timestamp).getTime();
      
      if (dataAge > maxAge) {
        console.warn(`⚠️ Sensordaten zu alt: ${deviceId}/${sensorType}`);
        return false;
      }
      
      // Evaluiere Operator
      const sensorValue = latestReading.value;
      
      switch (operator) {
        case 'gt': return sensorValue > value;
        case 'lt': return sensorValue < value;
        case 'gte': return sensorValue >= value;
        case 'lte': return sensorValue <= value;
        case 'eq': return Math.abs(sensorValue - value) < 0.01;
        case 'between': 
          return sensorValue >= value.min && sensorValue <= value.max;
        case 'outside':
          return sensorValue < value.min || sensorValue > value.max;
        default:
          console.warn(`⚠️ Unbekannter Operator: ${operator}`);
          return false;
      }
      
    } catch (error) {
      console.error('❌ Fehler bei Sensor-Trigger:', error);
      return false;
    }
  }

  evaluateTimeTrigger(trigger) {
    const now = new Date();
    const { schedule, timezone = 'Europe/Berlin' } = trigger;
    
    // TODO: Implementiere Zeitbasierte Trigger (Cron-ähnlich)
    // Für jetzt einfache Implementierung
    if (schedule.type === 'interval') {
      const lastExecution = this.getLastExecution(trigger.ruleId);
      const intervalMs = schedule.intervalMinutes * 60 * 1000;
      
      return !lastExecution || (now.getTime() - lastExecution.getTime()) > intervalMs;
    }
    
    return false;
  }

  async evaluateCompoundTrigger(trigger) {
    const { operator, conditions } = trigger;
    
    const results = await Promise.all(
      conditions.map(condition => this.evaluateTrigger(condition))
    );
    
    switch (operator) {
      case 'AND': return results.every(result => result);
      case 'OR': return results.some(result => result);
      case 'NOT': return !results[0];
      default: return false;
    }
  }

  async executeActions(ruleId, actions) {
    for (const action of actions) {
      try {
        await this.executeAction(ruleId, action);
        
        // Kurze Pause zwischen Aktionen
        await new Promise(resolve => setTimeout(resolve, 1000));
        
      } catch (error) {
        console.error(`❌ Fehler bei Aktion:`, error);
        // Weiter mit nächster Aktion
      }
    }
  }

  async executeAction(ruleId, action) {
    switch (action.type) {
      case 'pump':
        await this.executePumpAction(ruleId, action);
        break;
      case 'notification':
        await this.executeNotificationAction(ruleId, action);
        break;
      case 'wait':
        await this.executeWaitAction(action);
        break;
      default:
        console.warn(`⚠️ Unbekannter Aktions-Typ: ${action.type}`);
    }
  }

  async executePumpAction(ruleId, action) {
    const { deviceId, pumpType, duration = 5000 } = action;
    
    console.log(`🚰 Aktiviere ${pumpType} auf ${deviceId} für ${duration}ms`);
    
    try {
      // Sende MQTT-Kommando über Bridge
      await this.mqttBridge.sendPumpCommand(deviceId, pumpType, duration);
      
      // Speichere Aktion in Historie
      await this.logAction(ruleId, action, 'success');
      
    } catch (error) {
      console.error('❌ Fehler beim Aktivieren der Pumpe:', error);
      await this.logAction(ruleId, action, 'error', error.message);
      throw error;
    }
  }

  async executeNotificationAction(ruleId, action) {
    const { message, severity = 'info' } = action;
    
    console.log(`📢 Benachrichtigung: ${message}`);
    
    try {
      // Speichere Notification in DB
      await this.db.collection('notifications').insertOne({
        ruleId,
        message,
        severity,
        timestamp: new Date(),
        read: false
      });
      
      await this.logAction(ruleId, action, 'success');
      this.emit('notification', { message, severity, ruleId });
      
    } catch (error) {
      console.error('❌ Fehler bei Benachrichtigung:', error);
      await this.logAction(ruleId, action, 'error', error.message);
    }
  }

  async executeWaitAction(action) {
    const { duration = 1000 } = action;
    console.log(`⏳ Warte ${duration}ms`);
    await new Promise(resolve => setTimeout(resolve, duration));
  }

  async logAction(ruleId, action, status, errorMessage = null) {
    try {
      await this.db.collection('automation_logs').insertOne({
        ruleId,
        action,
        status,
        errorMessage,
        timestamp: new Date()
      });
    } catch (error) {
      console.error('❌ Fehler beim Loggen der Aktion:', error);
    }
  }

  isRuleOnCooldown(ruleId) {
    const history = this.actionHistory.get(ruleId) || [];
    const cutoff = Date.now() - this.config.cooldownMs;
    
    // Entferne alte Einträge
    const recentActions = history.filter(timestamp => timestamp > cutoff);
    this.actionHistory.set(ruleId, recentActions);
    
    // Prüfe Rate-Limit
    return recentActions.length >= this.config.maxActionsPerRule;
  }

  async updateRuleExecution(ruleId) {
    try {
      // Update in DB
      await this.db.collection('automation_rules').updateOne(
        { _id: this.db.ObjectId(ruleId) },
        { 
          $set: { lastTriggered: new Date() },
          $inc: { executionCount: 1 }
        }
      );
      
      // Update Action History für Rate-Limiting
      const history = this.actionHistory.get(ruleId) || [];
      history.push(Date.now());
      this.actionHistory.set(ruleId, history);
      
    } catch (error) {
      console.error('❌ Fehler beim Update der Regel-Ausführung:', error);
    }
  }

  // API-Methoden für Regel-Management
  async createRule(ruleData) {
    try {
      const rule = {
        ...ruleData,
        enabled: true,
        createdAt: new Date(),
        updatedAt: new Date(),
        executionCount: 0,
        lastTriggered: null
      };
      
      const result = await this.db.collection('automation_rules').insertOne(rule);
      const ruleId = result.insertedId.toString();
      
      // Lade Regel in Memory
      this.rules.set(ruleId, { ...rule, _id: result.insertedId });
      
      console.log(`✅ Neue Regel erstellt: ${ruleData.name}`);
      this.emit('ruleCreated', { ruleId, rule });
      
      return ruleId;
    } catch (error) {
      console.error('❌ Fehler beim Erstellen der Regel:', error);
      throw error;
    }
  }

  async updateRule(ruleId, updateData) {
    try {
      const update = {
        ...updateData,
        updatedAt: new Date()
      };
      
      await this.db.collection('automation_rules').updateOne(
        { _id: this.db.ObjectId(ruleId) },
        { $set: update }
      );
      
      // Update in Memory
      if (this.rules.has(ruleId)) {
        const existingRule = this.rules.get(ruleId);
        this.rules.set(ruleId, { ...existingRule, ...update });
      }
      
      console.log(`✅ Regel aktualisiert: ${ruleId}`);
      this.emit('ruleUpdated', { ruleId, update });
      
    } catch (error) {
      console.error('❌ Fehler beim Aktualisieren der Regel:', error);
      throw error;
    }
  }

  async deleteRule(ruleId) {
    try {
      await this.db.collection('automation_rules').deleteOne(
        { _id: this.db.ObjectId(ruleId) }
      );
      
      this.rules.delete(ruleId);
      this.actionHistory.delete(ruleId);
      
      console.log(`✅ Regel gelöscht: ${ruleId}`);
      this.emit('ruleDeleted', { ruleId });
      
    } catch (error) {
      console.error('❌ Fehler beim Löschen der Regel:', error);
      throw error;
    }
  }

  getStatus() {
    return {
      isRunning: this.isRunning,
      rulesCount: this.rules.size,
      checkInterval: this.config.checkIntervalMs,
      lastCheck: new Date()
    };
  }
}

export default AutomationEngine; 