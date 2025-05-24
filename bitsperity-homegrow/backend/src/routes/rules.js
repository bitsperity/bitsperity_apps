import { z } from 'zod';

// Validation schemas
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
  cooldown: z.number().optional().default(300),
  priority: z.number().min(1).max(10).default(5)
});

export default async function rulesRoutes(fastify, options) {
  
  // Get all automation rules
  fastify.get('/', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const rules = await fastify.automationEngine.getAllRules();
      
      // Transform for frontend
      const rulesWithStats = await Promise.all(
        rules.map(async (rule) => {
          // Get execution stats
          const executions = await fastify.db.collection('rule_executions')
            .find({ ruleId: rule._id.toString() })
            .sort({ timestamp: -1 })
            .limit(10)
            .toArray();

          const lastExecution = executions[0];
          const successCount = executions.filter(e => e.status === 'executed').length;
          const errorCount = executions.filter(e => e.status === 'error').length;

          return {
            id: rule._id.toString(),
            name: rule.name,
            description: rule.description,
            enabled: rule.enabled,
            conditions: rule.conditions,
            actions: rule.actions,
            cooldown: rule.cooldown,
            priority: rule.priority,
            createdAt: rule.createdAt,
            updatedAt: rule.updatedAt,
            stats: {
              lastExecution: lastExecution?.timestamp,
              lastStatus: lastExecution?.status,
              recentSuccesses: successCount,
              recentErrors: errorCount,
              totalExecutions: executions.length
            }
          };
        })
      );

      return { data: rulesWithStats };
    } catch (error) {
      fastify.log.error('Error fetching rules:', error);
      reply.status(500).send({ error: 'Failed to fetch automation rules' });
    }
  });

  // Get single rule
  fastify.get('/:ruleId', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const { ruleId } = request.params;
      
      const rule = await fastify.db.collection('automation_rules').findOne({
        _id: new fastify.db.constructor.ObjectId(ruleId)
      });

      if (!rule) {
        return reply.status(404).send({ error: 'Rule not found' });
      }

      // Get execution history
      const executions = await fastify.automationEngine.getRuleExecutionHistory(ruleId, 20);

      return {
        data: {
          id: rule._id.toString(),
          name: rule.name,
          description: rule.description,
          enabled: rule.enabled,
          conditions: rule.conditions,
          actions: rule.actions,
          cooldown: rule.cooldown,
          priority: rule.priority,
          createdAt: rule.createdAt,
          updatedAt: rule.updatedAt,
          executions: executions.map(exec => ({
            id: exec._id.toString(),
            timestamp: exec.timestamp,
            status: exec.status,
            errorMessage: exec.errorMessage,
            evaluationResults: exec.evaluationResults
          }))
        }
      };
    } catch (error) {
      fastify.log.error('Error fetching rule:', error);
      reply.status(500).send({ error: 'Failed to fetch rule' });
    }
  });

  // Create new automation rule
  fastify.post('/', {
    preHandler: [fastify.authenticate]
    // Temporarily disabled: schema: { body: RuleSchema }
  }, async (request, reply) => {
    try {
      const ruleData = request.body;
      
      // Validate that referenced devices exist
      const deviceIds = new Set([
        ...ruleData.conditions.map(c => c.deviceId),
        ...ruleData.actions.map(a => a.deviceId)
      ]);

      for (const deviceId of deviceIds) {
        const device = await fastify.db.collection('devices').findOne({ deviceId });
        if (!device) {
          return reply.status(400).send({ 
            error: 'Invalid device reference',
            message: `Device ${deviceId} does not exist`
          });
        }
      }

      const newRule = await fastify.automationEngine.createRule(ruleData);

      return { 
        data: {
          id: newRule.id,
          name: newRule.name,
          description: newRule.description,
          enabled: newRule.enabled,
          conditions: newRule.conditions,
          actions: newRule.actions,
          cooldown: newRule.cooldown,
          priority: newRule.priority,
          createdAt: newRule.createdAt,
          updatedAt: newRule.updatedAt
        }
      };
    } catch (error) {
      if (error.name === 'ZodError') {
        return reply.status(400).send({ 
          error: 'Validation Error',
          message: 'Invalid rule data',
          details: error.errors
        });
      }
      
      fastify.log.error('Error creating rule:', error);
      reply.status(500).send({ error: 'Failed to create automation rule' });
    }
  });

  // Update automation rule
  fastify.put('/:ruleId', {
    preHandler: [fastify.authenticate]
    // Temporarily disabled: schema: { body: RuleSchema.partial() }
  }, async (request, reply) => {
    try {
      const { ruleId } = request.params;
      const updateData = request.body;

      // Check if rule exists
      const existingRule = await fastify.db.collection('automation_rules').findOne({
        _id: new fastify.db.constructor.ObjectId(ruleId)
      });

      if (!existingRule) {
        return reply.status(404).send({ error: 'Rule not found' });
      }

      // Validate device references if conditions or actions are being updated
      if (updateData.conditions || updateData.actions) {
        const conditions = updateData.conditions || existingRule.conditions;
        const actions = updateData.actions || existingRule.actions;
        
        const deviceIds = new Set([
          ...conditions.map(c => c.deviceId),
          ...actions.map(a => a.deviceId)
        ]);

        for (const deviceId of deviceIds) {
          const device = await fastify.db.collection('devices').findOne({ deviceId });
          if (!device) {
            return reply.status(400).send({ 
              error: 'Invalid device reference',
              message: `Device ${deviceId} does not exist`
            });
          }
        }
      }

      await fastify.automationEngine.updateRule(ruleId, updateData);

      // Get updated rule
      const updatedRule = await fastify.db.collection('automation_rules').findOne({
        _id: new fastify.db.constructor.ObjectId(ruleId)
      });

      return { 
        data: {
          id: updatedRule._id.toString(),
          name: updatedRule.name,
          description: updatedRule.description,
          enabled: updatedRule.enabled,
          conditions: updatedRule.conditions,
          actions: updatedRule.actions,
          cooldown: updatedRule.cooldown,
          priority: updatedRule.priority,
          createdAt: updatedRule.createdAt,
          updatedAt: updatedRule.updatedAt
        }
      };
    } catch (error) {
      if (error.name === 'ZodError') {
        return reply.status(400).send({ 
          error: 'Validation Error',
          message: 'Invalid rule data',
          details: error.errors
        });
      }
      
      fastify.log.error('Error updating rule:', error);
      reply.status(500).send({ error: 'Failed to update automation rule' });
    }
  });

  // Delete automation rule
  fastify.delete('/:ruleId', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const { ruleId } = request.params;

      // Check if rule exists
      const existingRule = await fastify.db.collection('automation_rules').findOne({
        _id: new fastify.db.constructor.ObjectId(ruleId)
      });

      if (!existingRule) {
        return reply.status(404).send({ error: 'Rule not found' });
      }

      await fastify.automationEngine.deleteRule(ruleId);

      return { message: 'Rule deleted successfully' };
    } catch (error) {
      fastify.log.error('Error deleting rule:', error);
      reply.status(500).send({ error: 'Failed to delete automation rule' });
    }
  });

  // Toggle rule enabled/disabled
  fastify.patch('/:ruleId/toggle', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const { ruleId } = request.params;

      const rule = await fastify.db.collection('automation_rules').findOne({
        _id: new fastify.db.constructor.ObjectId(ruleId)
      });

      if (!rule) {
        return reply.status(404).send({ error: 'Rule not found' });
      }

      const newEnabledState = !rule.enabled;
      
      await fastify.automationEngine.updateRule(ruleId, { enabled: newEnabledState });

      return { 
        data: { 
          id: ruleId, 
          enabled: newEnabledState 
        },
        message: `Rule ${newEnabledState ? 'enabled' : 'disabled'} successfully`
      };
    } catch (error) {
      fastify.log.error('Error toggling rule:', error);
      reply.status(500).send({ error: 'Failed to toggle rule' });
    }
  });

  // Get rule execution history
  fastify.get('/:ruleId/executions', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const { ruleId } = request.params;
      const { limit = 50, offset = 0 } = request.query;

      const executions = await fastify.db.collection('rule_executions')
        .find({ ruleId })
        .sort({ timestamp: -1 })
        .limit(parseInt(limit))
        .skip(parseInt(offset))
        .toArray();

      const totalCount = await fastify.db.collection('rule_executions')
        .countDocuments({ ruleId });

      return {
        data: executions.map(exec => ({
          id: exec._id.toString(),
          timestamp: exec.timestamp,
          status: exec.status,
          errorMessage: exec.errorMessage,
          evaluationResults: exec.evaluationResults,
          conditions: exec.conditions,
          actions: exec.actions
        })),
        meta: {
          total: totalCount,
          limit: parseInt(limit),
          offset: parseInt(offset),
          hasMore: (parseInt(offset) + parseInt(limit)) < totalCount
        }
      };
    } catch (error) {
      fastify.log.error('Error fetching rule executions:', error);
      reply.status(500).send({ error: 'Failed to fetch rule execution history' });
    }
  });

  // Test rule (simulate execution without actually running actions)
  fastify.post('/:ruleId/test', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const { ruleId } = request.params;

      const rule = await fastify.db.collection('automation_rules').findOne({
        _id: new fastify.db.constructor.ObjectId(ruleId)
      });

      if (!rule) {
        return reply.status(404).send({ error: 'Rule not found' });
      }

      // Get current sensor data
      const latestReadings = await fastify.db.collection('latest_readings').find({}).toArray();
      
      const sensorData = latestReadings.reduce((acc, reading) => {
        const key = `${reading.deviceId}_${reading.sensorType}`;
        acc[key] = reading;
        return acc;
      }, {});

      // Evaluate conditions
      const evaluationResults = [];
      let allConditionsMet = true;

      for (const condition of rule.conditions) {
        const sensorKey = `${condition.deviceId}_${condition.sensorType}`;
        const sensorReading = sensorData[sensorKey];

        if (!sensorReading) {
          evaluationResults.push({
            condition,
            sensorValue: null,
            result: false,
            error: 'No sensor data available'
          });
          allConditionsMet = false;
          continue;
        }

        const result = evaluateCondition(condition, sensorReading.value);
        evaluationResults.push({
          condition,
          sensorValue: sensorReading.value,
          result,
          timestamp: sensorReading.timestamp
        });

        if (!result) {
          allConditionsMet = false;
        }
      }

      return {
        data: {
          ruleName: rule.name,
          wouldExecute: allConditionsMet && rule.conditions.length > 0,
          conditionsEvaluated: evaluationResults,
          actionsToExecute: allConditionsMet ? rule.actions : [],
          testTimestamp: new Date()
        }
      };
    } catch (error) {
      fastify.log.error('Error testing rule:', error);
      reply.status(500).send({ error: 'Failed to test rule' });
    }
  });

  // Get available sensor types and commands for rule builder
  fastify.get('/builder/options', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      // Get available devices
      const devices = await fastify.db.collection('devices').find({}).toArray();
      
      // Get unique sensor types from latest readings
      const sensorTypes = await fastify.db.collection('latest_readings')
        .distinct('sensorType');

      // Available commands (could be made configurable)
      const availableCommands = [
        { command: 'water_pump', name: 'Wasserpumpe', params: { duration_sec: 'number' } },
        { command: 'nutrient_pump_1', name: 'Nährstoffpumpe 1', params: { volume_ml: 'number' } },
        { command: 'nutrient_pump_2', name: 'Nährstoffpumpe 2', params: { volume_ml: 'number' } },
        { command: 'air_pump', name: 'Luftpumpe', params: { state: 'boolean' } },
        { command: 'led_strip', name: 'LED-Beleuchtung', params: { brightness: 'number', color: 'string' } },
        { command: 'fan', name: 'Lüfter', params: { speed: 'number' } }
      ];

      // Available operators
      const operators = [
        { value: '>', label: 'größer als (>)' },
        { value: '<', label: 'kleiner als (<)' },
        { value: '>=', label: 'größer oder gleich (>=)' },
        { value: '<=', label: 'kleiner oder gleich (<=)' },
        { value: '==', label: 'gleich (==)' },
        { value: '!=', label: 'ungleich (!=)' }
      ];

      return {
        data: {
          devices: devices.map(d => ({
            id: d.deviceId,
            name: d.name || `Device ${d.deviceId}`,
            type: d.type,
            location: d.location
          })),
          sensorTypes: sensorTypes.map(type => ({
            value: type,
            label: getSensorTypeName(type)
          })),
          commands: availableCommands,
          operators
        }
      };
    } catch (error) {
      fastify.log.error('Error fetching builder options:', error);
      reply.status(500).send({ error: 'Failed to fetch rule builder options' });
    }
  });
}

// Helper functions
function evaluateCondition(condition, sensorValue) {
  const { operator, value } = condition;
  
  switch (operator) {
    case '>':
      return sensorValue > value;
    case '<':
      return sensorValue < value;
    case '>=':
      return sensorValue >= value;
    case '<=':
      return sensorValue <= value;
    case '==':
      return Math.abs(sensorValue - value) < 0.01;
    case '!=':
      return Math.abs(sensorValue - value) >= 0.01;
    default:
      return false;
  }
}

function getSensorTypeName(sensorType) {
  const names = {
    'ph': 'pH-Wert',
    'temperature': 'Temperatur',
    'humidity': 'Luftfeuchtigkeit',
    'ec': 'Leitfähigkeit',
    'water_level': 'Wasserstand',
    'light_intensity': 'Lichtintensität',
    'dissolved_oxygen': 'Gelöster Sauerstoff',
    'co2': 'CO2-Gehalt'
  };
  
  return names[sensorType] || sensorType;
} 