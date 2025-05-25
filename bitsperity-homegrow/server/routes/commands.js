const express = require('express');
const router = express.Router();
const Command = require('../models/command');

// GET /api/v1/commands - Alle Befehle abrufen
router.get('/', async (req, res) => {
  try {
    const {
      deviceId,
      status,
      commandType,
      source,
      priority,
      startDate,
      endDate,
      limit = 50,
      skip = 0,
      sortBy = 'createdAt',
      sortOrder = 'desc'
    } = req.query;

    // Query-Filter aufbauen
    const query = {};
    
    if (deviceId) query.deviceId = deviceId;
    if (status) query.status = status;
    if (commandType) query.commandType = commandType;
    if (source) query.source = source;
    if (priority) query.priority = priority;
    
    if (startDate || endDate) {
      query.createdAt = {};
      if (startDate) query.createdAt.$gte = new Date(startDate);
      if (endDate) query.createdAt.$lte = new Date(endDate);
    }

    // Sortierung
    const sort = {};
    sort[sortBy] = sortOrder === 'asc' ? 1 : -1;

    // Befehle abrufen
    const commands = await Command.find(query)
      .sort(sort)
      .limit(parseInt(limit))
      .skip(parseInt(skip))
      .lean();

    const total = await Command.countDocuments(query);

    res.json({
      success: true,
      data: {
        commands: commands.map(cmd => ({
          ...cmd,
          isCompleted: ['completed', 'failed', 'timeout'].includes(cmd.status),
          isActive: ['pending', 'sent', 'acknowledged', 'executing'].includes(cmd.status),
          duration: cmd.completedAt && cmd.sentAt ? 
            cmd.completedAt.getTime() - cmd.sentAt.getTime() : null
        })),
        pagination: {
          total,
          limit: parseInt(limit),
          skip: parseInt(skip),
          hasMore: total > parseInt(skip) + commands.length
        }
      }
    });

  } catch (error) {
    console.error('Fehler beim Abrufen der Befehle:', error);
    res.status(500).json({
      success: false,
      error: 'Fehler beim Abrufen der Befehle',
      details: error.message
    });
  }
});

// GET /api/v1/commands/stats - Befehlsstatistiken
router.get('/stats', async (req, res) => {
  try {
    const { deviceId, timeRange = '24h' } = req.query;

    const stats = await Command.getCommandStats(deviceId, timeRange);

    // Zusätzliche Statistiken
    const activeCommands = await Command.getActiveCommands(deviceId);
    const recentFailures = await Command.find({
      ...(deviceId && { deviceId }),
      status: 'failed',
      createdAt: { $gte: new Date(Date.now() - 60 * 60 * 1000) } // Letzte Stunde
    }).countDocuments();

    res.json({
      success: true,
      data: {
        ...stats,
        activeCommands: activeCommands.length,
        recentFailures,
        successRate: stats.total > 0 ? 
          Math.round((stats.completed / stats.total) * 100) : 0
      }
    });

  } catch (error) {
    console.error('Fehler beim Abrufen der Befehlsstatistiken:', error);
    res.status(500).json({
      success: false,
      error: 'Fehler beim Abrufen der Befehlsstatistiken',
      details: error.message
    });
  }
});

// GET /api/v1/commands/active - Aktive Befehle
router.get('/active', async (req, res) => {
  try {
    const { deviceId } = req.query;

    const activeCommands = await Command.getActiveCommands(deviceId);

    res.json({
      success: true,
      data: {
        commands: activeCommands,
        count: activeCommands.length
      }
    });

  } catch (error) {
    console.error('Fehler beim Abrufen aktiver Befehle:', error);
    res.status(500).json({
      success: false,
      error: 'Fehler beim Abrufen aktiver Befehle',
      details: error.message
    });
  }
});

// GET /api/v1/commands/:commandId - Einzelnen Befehl abrufen
router.get('/:commandId', async (req, res) => {
  try {
    const { commandId } = req.params;

    const command = await Command.findOne({ commandId });

    if (!command) {
      return res.status(404).json({
        success: false,
        error: 'Befehl nicht gefunden'
      });
    }

    res.json({
      success: true,
      data: command.toAPIResponse()
    });

  } catch (error) {
    console.error('Fehler beim Abrufen des Befehls:', error);
    res.status(500).json({
      success: false,
      error: 'Fehler beim Abrufen des Befehls',
      details: error.message
    });
  }
});

// POST /api/v1/commands - Neuen Befehl erstellen
router.post('/', async (req, res) => {
  try {
    const {
      deviceId,
      commandType,
      parameters = {},
      source = 'api',
      userId = null,
      priority = 'normal',
      timeoutMs = 30000,
      maxRetries = 3,
      metadata = {}
    } = req.body;

    // Validierung
    if (!deviceId || !commandType) {
      return res.status(400).json({
        success: false,
        error: 'deviceId und commandType sind erforderlich'
      });
    }

    // Befehl erstellen
    const command = await Command.createCommand({
      deviceId,
      commandType,
      parameters,
      source,
      userId,
      priority,
      timeoutMs,
      maxRetries,
      metadata
    });

    // Befehl über MQTT senden (falls MQTT Bridge verfügbar)
    if (req.app.locals.mqttBridge) {
      try {
        const mqttCommand = {
          command_id: command.commandId,
          command: commandType,
          params: parameters,
          timestamp: Date.now()
        };

        await req.app.locals.mqttBridge.publishCommand(deviceId, mqttCommand);
        await Command.markAsSent(command.commandId);

        console.log(`✅ Befehl ${command.commandId} über MQTT gesendet`);
      } catch (mqttError) {
        console.error('Fehler beim Senden über MQTT:', mqttError);
        await command.markAsFailed(`MQTT-Fehler: ${mqttError.message}`);
      }
    }

    res.status(201).json({
      success: true,
      data: command.toAPIResponse(),
      message: 'Befehl erfolgreich erstellt'
    });

  } catch (error) {
    console.error('Fehler beim Erstellen des Befehls:', error);
    res.status(500).json({
      success: false,
      error: 'Fehler beim Erstellen des Befehls',
      details: error.message
    });
  }
});

// POST /api/v1/commands/:commandId/retry - Befehl wiederholen
router.post('/:commandId/retry', async (req, res) => {
  try {
    const { commandId } = req.params;

    const retryCommand = await Command.retryCommand(commandId);

    // Befehl über MQTT senden
    if (req.app.locals.mqttBridge) {
      try {
        const mqttCommand = {
          command_id: retryCommand.commandId,
          command: retryCommand.commandType,
          params: retryCommand.parameters,
          timestamp: Date.now()
        };

        await req.app.locals.mqttBridge.publishCommand(retryCommand.deviceId, mqttCommand);
        await Command.markAsSent(retryCommand.commandId);

        console.log(`✅ Wiederholungsbefehl ${retryCommand.commandId} über MQTT gesendet`);
      } catch (mqttError) {
        console.error('Fehler beim Senden der Wiederholung über MQTT:', mqttError);
        await retryCommand.markAsFailed(`MQTT-Fehler: ${mqttError.message}`);
      }
    }

    res.json({
      success: true,
      data: retryCommand.toAPIResponse(),
      message: 'Befehl wird wiederholt'
    });

  } catch (error) {
    console.error('Fehler beim Wiederholen des Befehls:', error);
    res.status(500).json({
      success: false,
      error: 'Fehler beim Wiederholen des Befehls',
      details: error.message
    });
  }
});

// PUT /api/v1/commands/:commandId/status - Befehlsstatus aktualisieren
router.put('/:commandId/status', async (req, res) => {
  try {
    const { commandId } = req.params;
    const { status, response, error } = req.body;

    if (!status) {
      return res.status(400).json({
        success: false,
        error: 'Status ist erforderlich'
      });
    }

    const validStatuses = ['pending', 'sent', 'acknowledged', 'executing', 'completed', 'failed', 'timeout'];
    if (!validStatuses.includes(status)) {
      return res.status(400).json({
        success: false,
        error: `Ungültiger Status. Erlaubt: ${validStatuses.join(', ')}`
      });
    }

    const command = await Command.findOne({ commandId });
    if (!command) {
      return res.status(404).json({
        success: false,
        error: 'Befehl nicht gefunden'
      });
    }

    // Status aktualisieren
    command.status = status;
    
    if (response) {
      command.response = response;
    }
    
    if (error) {
      command.error = error;
    }

    await command.save();

    res.json({
      success: true,
      data: command.toAPIResponse(),
      message: 'Befehlsstatus aktualisiert'
    });

  } catch (error) {
    console.error('Fehler beim Aktualisieren des Befehlsstatus:', error);
    res.status(500).json({
      success: false,
      error: 'Fehler beim Aktualisieren des Befehlsstatus',
      details: error.message
    });
  }
});

// DELETE /api/v1/commands/:commandId - Befehl löschen
router.delete('/:commandId', async (req, res) => {
  try {
    const { commandId } = req.params;

    const command = await Command.findOne({ commandId });
    if (!command) {
      return res.status(404).json({
        success: false,
        error: 'Befehl nicht gefunden'
      });
    }

    // Nur abgeschlossene Befehle können gelöscht werden
    if (command.isActive) {
      return res.status(400).json({
        success: false,
        error: 'Aktive Befehle können nicht gelöscht werden'
      });
    }

    await Command.deleteOne({ commandId });

    res.json({
      success: true,
      message: 'Befehl erfolgreich gelöscht'
    });

  } catch (error) {
    console.error('Fehler beim Löschen des Befehls:', error);
    res.status(500).json({
      success: false,
      error: 'Fehler beim Löschen des Befehls',
      details: error.message
    });
  }
});

// POST /api/v1/commands/cleanup - Alte Befehle bereinigen
router.post('/cleanup', async (req, res) => {
  try {
    const { olderThanDays = 30 } = req.body;

    const cutoffDate = new Date(Date.now() - olderThanDays * 24 * 60 * 60 * 1000);

    const result = await Command.deleteMany({
      createdAt: { $lt: cutoffDate },
      status: { $in: ['completed', 'failed', 'timeout'] }
    });

    res.json({
      success: true,
      data: {
        deletedCount: result.deletedCount,
        cutoffDate
      },
      message: `${result.deletedCount} alte Befehle wurden bereinigt`
    });

  } catch (error) {
    console.error('Fehler beim Bereinigen der Befehle:', error);
    res.status(500).json({
      success: false,
      error: 'Fehler beim Bereinigen der Befehle',
      details: error.message
    });
  }
});

// POST /api/v1/commands/timeout-check - Timeout-Befehle markieren
router.post('/timeout-check', async (req, res) => {
  try {
    const timeoutCount = await Command.markTimeoutCommands();

    res.json({
      success: true,
      data: {
        timeoutCount
      },
      message: `${timeoutCount} Befehle als Timeout markiert`
    });

  } catch (error) {
    console.error('Fehler beim Timeout-Check:', error);
    res.status(500).json({
      success: false,
      error: 'Fehler beim Timeout-Check',
      details: error.message
    });
  }
});

// GET /api/v1/commands/device/:deviceId - Befehle für ein bestimmtes Gerät
router.get('/device/:deviceId', async (req, res) => {
  try {
    const { deviceId } = req.params;
    const {
      status,
      commandType,
      startDate,
      endDate,
      limit = 50,
      skip = 0
    } = req.query;

    const options = {
      limit: parseInt(limit),
      skip: parseInt(skip),
      status,
      commandType,
      startDate,
      endDate
    };

    const result = await Command.getDeviceCommands(deviceId, options);

    res.json({
      success: true,
      data: result
    });

  } catch (error) {
    console.error('Fehler beim Abrufen der Gerätebefehle:', error);
    res.status(500).json({
      success: false,
      error: 'Fehler beim Abrufen der Gerätebefehle',
      details: error.message
    });
  }
});

// POST /api/v1/commands/emergency-stop - Notaus für alle Geräte
router.post('/emergency-stop', async (req, res) => {
  try {
    const { deviceId, userId = null } = req.body;

    if (!deviceId) {
      return res.status(400).json({
        success: false,
        error: 'deviceId ist erforderlich'
      });
    }

    // Notaus-Befehl erstellen
    const emergencyCommand = await Command.createCommand({
      deviceId,
      commandType: 'emergency_stop',
      parameters: { reason: 'Manual emergency stop' },
      source: 'emergency',
      userId,
      priority: 'emergency',
      timeoutMs: 5000, // Kurzes Timeout für Notaus
      maxRetries: 0 // Keine Wiederholungen für Notaus
    });

    // Sofort über MQTT senden
    if (req.app.locals.mqttBridge) {
      try {
        const mqttCommand = {
          command_id: emergencyCommand.commandId,
          command: 'emergency_stop',
          params: { reason: 'Manual emergency stop' },
          timestamp: Date.now()
        };

        await req.app.locals.mqttBridge.publishCommand(deviceId, mqttCommand);
        await Command.markAsSent(emergencyCommand.commandId);

        console.log(`🚨 Notaus-Befehl ${emergencyCommand.commandId} gesendet`);
      } catch (mqttError) {
        console.error('Fehler beim Senden des Notaus-Befehls:', mqttError);
        await emergencyCommand.markAsFailed(`MQTT-Fehler: ${mqttError.message}`);
      }
    }

    res.json({
      success: true,
      data: emergencyCommand.toAPIResponse(),
      message: 'Notaus-Befehl gesendet'
    });

  } catch (error) {
    console.error('Fehler beim Notaus:', error);
    res.status(500).json({
      success: false,
      error: 'Fehler beim Notaus',
      details: error.message
    });
  }
});

module.exports = router; 