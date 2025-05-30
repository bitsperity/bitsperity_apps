import { ObjectId } from 'mongodb';

class CommandModel {
  constructor(db) {
    this.collection = db.collection('device_commands');
    this.createIndexes();
  }

  async createIndexes() {
    try {
      await this.collection.createIndex({ command_id: 1 }, { unique: true });
      await this.collection.createIndex({ device_id: 1, timestamp: -1 });
      await this.collection.createIndex({ status: 1 });
      await this.collection.createIndex({ command_type: 1 });
      await this.collection.createIndex({ priority: 1, status: 1 });
      // TTL index for automatic cleanup after 30 days
      await this.collection.createIndex({ created_at: 1 }, { expireAfterSeconds: 30 * 24 * 60 * 60 });
      console.log('✅ Command indexes created');
    } catch (error) {
      console.warn('⚠️ Could not create command indexes:', error.message);
    }
  }

  async createCommand(commandData) {
    const command = {
      command_id: commandData.command_id || `cmd_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      device_id: commandData.device_id,
      command_type: commandData.command_type,
      parameters: commandData.parameters || {},
      status: 'pending',
      source: commandData.source || 'manual',
      user_id: commandData.user_id || null,
      priority: commandData.priority || 'normal',
      created_at: new Date(),
      sent_at: null,
      acknowledged_at: null,
      completed_at: null,
      execution_time_ms: null,
      response: null,
      error: null,
      timeout_ms: commandData.timeout_ms || 30000,
      retry_count: commandData.retry_count || 0,
      max_retries: commandData.max_retries || 3,
      metadata: commandData.metadata || {}
    };

    const result = await this.collection.insertOne(command);
    return { ...command, _id: result.insertedId };
  }

  async markAsSent(commandId) {
    return await this.collection.findOneAndUpdate(
      { command_id: commandId },
      { 
        $set: { 
          status: 'sent',
          sent_at: new Date()
        }
      },
      { returnDocument: 'after' }
    );
  }

  async markAsAcknowledged(commandId) {
    return await this.collection.findOneAndUpdate(
      { command_id: commandId },
      { 
        $set: { 
          status: 'acknowledged',
          acknowledged_at: new Date()
        }
      },
      { returnDocument: 'after' }
    );
  }

  async markAsExecuting(commandId) {
    return await this.collection.findOneAndUpdate(
      { command_id: commandId },
      { 
        $set: { 
          status: 'executing'
        }
      },
      { returnDocument: 'after' }
    );
  }

  async markAsCompleted(commandId, response = null) {
    const now = new Date();
    const command = await this.collection.findOne({ command_id: commandId });
    const executionTime = command?.sent_at ? now.getTime() - command.sent_at.getTime() : null;

    return await this.collection.findOneAndUpdate(
      { command_id: commandId },
      { 
        $set: { 
          status: 'completed',
          completed_at: now,
          response: response,
          execution_time_ms: executionTime
        }
      },
      { returnDocument: 'after' }
    );
  }

  async markAsFailed(commandId, error) {
    const now = new Date();
    const command = await this.collection.findOne({ command_id: commandId });
    const executionTime = command?.sent_at ? now.getTime() - command.sent_at.getTime() : null;

    return await this.collection.findOneAndUpdate(
      { command_id: commandId },
      { 
        $set: { 
          status: 'failed',
          completed_at: now,
          error: error,
          execution_time_ms: executionTime
        }
      },
      { returnDocument: 'after' }
    );
  }

  async markTimeoutCommands() {
    const now = new Date();
    
    // Find commands that have been sent but not completed and are past their timeout
    const timeoutQuery = {
      status: { $in: ['sent', 'acknowledged', 'executing'] },
      $expr: {
        $lt: [
          { $add: ['$sent_at', '$timeout_ms'] },
          now
        ]
      }
    };

    const result = await this.collection.updateMany(
      timeoutQuery,
      { 
        $set: { 
          status: 'timeout',
          completed_at: now,
          error: 'Command timeout'
        }
      }
    );

    return result.modifiedCount;
  }

  async getDeviceCommands(deviceId, options = {}) {
    const {
      status = null,
      command_type = null,
      limit = 50,
      skip = 0,
      sort = { created_at: -1 }
    } = options;

    const query = { device_id: deviceId };
    
    if (status) {
      query.status = status;
    }
    
    if (command_type) {
      query.command_type = command_type;
    }

    const [commands, total] = await Promise.all([
      this.collection.find(query)
        .sort(sort)
        .limit(limit)
        .skip(skip)
        .toArray(),
      this.collection.countDocuments(query)
    ]);

    return {
      commands,
      total,
      hasMore: total > skip + commands.length
    };
  }

  async getActiveCommands(deviceId = null) {
    const query = { 
      status: { $in: ['pending', 'sent', 'acknowledged', 'executing'] }
    };
    
    if (deviceId) {
      query.device_id = deviceId;
    }

    return await this.collection.find(query)
      .sort({ priority: 1, created_at: 1 })
      .toArray();
  }

  async getCommandStats(deviceId = null, timeRange = '24h') {
    const timeRanges = {
      '1h': 1 * 60 * 60 * 1000,
      '24h': 24 * 60 * 60 * 1000,
      '7d': 7 * 24 * 60 * 60 * 1000,
      '30d': 30 * 24 * 60 * 60 * 1000
    };

    const startTime = new Date(Date.now() - timeRanges[timeRange]);
    const query = { created_at: { $gte: startTime } };
    
    if (deviceId) {
      query.device_id = deviceId;
    }

    const pipeline = [
      { $match: query },
      {
        $group: {
          _id: '$status',
          count: { $sum: 1 },
          avg_execution_time: { $avg: '$execution_time_ms' }
        }
      }
    ];

    const stats = await this.collection.aggregate(pipeline).toArray();
    
    const result = {
      total: 0,
      pending: 0,
      sent: 0,
      acknowledged: 0,
      executing: 0,
      completed: 0,
      failed: 0,
      timeout: 0,
      avg_execution_time: 0
    };

    stats.forEach(stat => {
      result[stat._id] = stat.count;
      result.total += stat.count;
      if (stat._id === 'completed' && stat.avg_execution_time) {
        result.avg_execution_time = Math.round(stat.avg_execution_time);
      }
    });

    return result;
  }

  async findByCommandId(commandId) {
    return await this.collection.findOne({ command_id: commandId });
  }

  async retryCommand(commandId) {
    const command = await this.findByCommandId(commandId);
    
    if (!command) {
      throw new Error(`Command ${commandId} not found`);
    }

    if (command.retry_count >= command.max_retries) {
      throw new Error(`Maximum retries exceeded for command ${commandId}`);
    }

    const retryCommand = await this.createCommand({
      device_id: command.device_id,
      command_type: command.command_type,
      parameters: command.parameters,
      source: command.source,
      user_id: command.user_id,
      priority: command.priority,
      timeout_ms: command.timeout_ms,
      max_retries: command.max_retries,
      retry_count: command.retry_count + 1,
      metadata: {
        ...command.metadata,
        original_command_id: command.command_id,
        retry_of: commandId
      }
    });

    return retryCommand;
  }
}

export default CommandModel; 