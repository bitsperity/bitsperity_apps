import express from 'express';
const router = express.Router();
const programModel = require('../models/program');
const programEngine = require('../services/program-engine');

/**
 * GET /api/programs
 * Holt alle Programme oder Programme für ein bestimmtes Gerät
 */
router.get('/', async (req, res) => {
  try {
    const { device_id } = req.query;
    
    let programs;
    if (device_id) {
      programs = await programModel.getProgramsByDevice(device_id);
    } else {
      programs = await programModel.getActivePrograms();
    }
    
    res.json({
      success: true,
      data: programs
    });
  } catch (error) {
    console.error('Error fetching programs:', error);
    res.status(500).json({
      success: false,
      error: 'Fehler beim Laden der Programme'
    });
  }
});

/**
 * GET /api/programs/:id
 * Holt ein bestimmtes Programm
 */
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const program = await programModel.getProgramById(id);
    
    if (!program) {
      return res.status(404).json({
        success: false,
        error: 'Programm nicht gefunden'
      });
    }
    
    res.json({
      success: true,
      data: program
    });
  } catch (error) {
    console.error('Error fetching program:', error);
    res.status(500).json({
      success: false,
      error: 'Fehler beim Laden des Programms'
    });
  }
});

/**
 * POST /api/programs
 * Erstellt ein neues Programm
 */
router.post('/', async (req, res) => {
  try {
    const programData = req.body;
    
    // Validiere Programm-Daten
    const validationErrors = programModel.validateProgram(programData);
    if (validationErrors.length > 0) {
      return res.status(400).json({
        success: false,
        error: 'Validierungsfehler',
        details: validationErrors
      });
    }
    
    const program = await programModel.createProgram(programData);
    
    res.status(201).json({
      success: true,
      data: program,
      message: 'Programm erfolgreich erstellt'
    });
  } catch (error) {
    console.error('Error creating program:', error);
    res.status(500).json({
      success: false,
      error: 'Fehler beim Erstellen des Programms'
    });
  }
});

/**
 * PUT /api/programs/:id
 * Aktualisiert ein Programm
 */
router.put('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const updateData = req.body;
    
    // Prüfe ob Programm existiert
    const existingProgram = await programModel.getProgramById(id);
    if (!existingProgram) {
      return res.status(404).json({
        success: false,
        error: 'Programm nicht gefunden'
      });
    }
    
    // Validiere Update-Daten
    const mergedData = { ...existingProgram, ...updateData };
    const validationErrors = programModel.validateProgram(mergedData);
    if (validationErrors.length > 0) {
      return res.status(400).json({
        success: false,
        error: 'Validierungsfehler',
        details: validationErrors
      });
    }
    
    const success = await programModel.updateProgram(id, updateData);
    
    if (!success) {
      return res.status(500).json({
        success: false,
        error: 'Fehler beim Aktualisieren des Programms'
      });
    }
    
    const updatedProgram = await programModel.getProgramById(id);
    
    res.json({
      success: true,
      data: updatedProgram,
      message: 'Programm erfolgreich aktualisiert'
    });
  } catch (error) {
    console.error('Error updating program:', error);
    res.status(500).json({
      success: false,
      error: 'Fehler beim Aktualisieren des Programms'
    });
  }
});

/**
 * DELETE /api/programs/:id
 * Löscht ein Programm
 */
router.delete('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    // Prüfe ob Programm läuft
    const runningPrograms = programEngine.getRunningPrograms();
    const isRunning = runningPrograms.some(p => p.programId === id);
    
    if (isRunning) {
      // Stoppe Programm zuerst
      programEngine.stopProgramExecution(id);
    }
    
    const success = await programModel.deleteProgram(id);
    
    if (!success) {
      return res.status(404).json({
        success: false,
        error: 'Programm nicht gefunden'
      });
    }
    
    res.json({
      success: true,
      message: 'Programm erfolgreich gelöscht'
    });
  } catch (error) {
    console.error('Error deleting program:', error);
    res.status(500).json({
      success: false,
      error: 'Fehler beim Löschen des Programms'
    });
  }
});

/**
 * POST /api/programs/:id/toggle
 * Aktiviert/Deaktiviert ein Programm
 */
router.post('/:id/toggle', async (req, res) => {
  try {
    const { id } = req.params;
    const { enabled } = req.body;
    
    if (typeof enabled !== 'boolean') {
      return res.status(400).json({
        success: false,
        error: 'enabled muss ein Boolean-Wert sein'
      });
    }
    
    // Wenn Programm deaktiviert wird und läuft, stoppe es
    if (!enabled) {
      const runningPrograms = programEngine.getRunningPrograms();
      const isRunning = runningPrograms.some(p => p.programId === id);
      
      if (isRunning) {
        programEngine.stopProgramExecution(id);
      }
    }
    
    const success = await programModel.toggleProgram(id, enabled);
    
    if (!success) {
      return res.status(404).json({
        success: false,
        error: 'Programm nicht gefunden'
      });
    }
    
    const program = await programModel.getProgramById(id);
    
    res.json({
      success: true,
      data: program,
      message: `Programm ${enabled ? 'aktiviert' : 'deaktiviert'}`
    });
  } catch (error) {
    console.error('Error toggling program:', error);
    res.status(500).json({
      success: false,
      error: 'Fehler beim Umschalten des Programms'
    });
  }
});

/**
 * POST /api/programs/:id/run
 * Führt ein Programm manuell aus
 */
router.post('/:id/run', async (req, res) => {
  try {
    const { id } = req.params;
    
    const result = await programEngine.runProgramManually(id);
    
    res.json({
      success: true,
      data: result,
      message: 'Programm wird ausgeführt'
    });
  } catch (error) {
    console.error('Error running program manually:', error);
    
    let statusCode = 500;
    let errorMessage = 'Fehler beim Ausführen des Programms';
    
    if (error.message === 'Program not found') {
      statusCode = 404;
      errorMessage = 'Programm nicht gefunden';
    } else if (error.message === 'Program is disabled') {
      statusCode = 400;
      errorMessage = 'Programm ist deaktiviert';
    } else if (error.message === 'Program is already running') {
      statusCode = 409;
      errorMessage = 'Programm läuft bereits';
    } else if (error.message === 'Program conditions not met') {
      statusCode = 400;
      errorMessage = 'Programm-Bedingungen nicht erfüllt';
    }
    
    res.status(statusCode).json({
      success: false,
      error: errorMessage
    });
  }
});

/**
 * POST /api/programs/:id/stop
 * Stoppt ein laufendes Programm
 */
router.post('/:id/stop', async (req, res) => {
  try {
    const { id } = req.params;
    
    const runningPrograms = programEngine.getRunningPrograms();
    const isRunning = runningPrograms.some(p => p.programId === id);
    
    if (!isRunning) {
      return res.status(400).json({
        success: false,
        error: 'Programm läuft nicht'
      });
    }
    
    programEngine.stopProgramExecution(id);
    
    res.json({
      success: true,
      message: 'Programm gestoppt'
    });
  } catch (error) {
    console.error('Error stopping program:', error);
    res.status(500).json({
      success: false,
      error: 'Fehler beim Stoppen des Programms'
    });
  }
});

/**
 * GET /api/programs/engine/status
 * Holt den Status der Program Engine
 */
router.get('/engine/status', async (req, res) => {
  try {
    const status = programEngine.getStatus();
    
    res.json({
      success: true,
      data: status
    });
  } catch (error) {
    console.error('Error getting engine status:', error);
    res.status(500).json({
      success: false,
      error: 'Fehler beim Laden des Engine-Status'
    });
  }
});

/**
 * GET /api/programs/running
 * Holt alle laufenden Programme
 */
router.get('/running', async (req, res) => {
  try {
    const runningPrograms = programEngine.getRunningPrograms();
    
    res.json({
      success: true,
      data: runningPrograms
    });
  } catch (error) {
    console.error('Error getting running programs:', error);
    res.status(500).json({
      success: false,
      error: 'Fehler beim Laden der laufenden Programme'
    });
  }
});

/**
 * GET /api/programs/templates
 * Holt Programm-Vorlagen
 */
router.get('/templates', async (req, res) => {
  try {
    const templates = [
      {
        id: 'daily_watering',
        name: 'Tägliche Bewässerung',
        description: 'Bewässert die Pflanzen täglich zu einer bestimmten Zeit',
        schedule: {
          type: 'cron',
          cron_expression: '0 8 * * *' // Täglich um 8:00
        },
        conditions: [],
        actions: [
          {
            type: 'pump',
            pump_id: 'water_pump',
            duration_seconds: 30,
            flow_rate: 100
          }
        ]
      },
      {
        id: 'ph_adjustment',
        name: 'pH-Wert Anpassung',
        description: 'Passt den pH-Wert an wenn er außerhalb des Bereichs liegt',
        schedule: {
          type: 'sensor_trigger'
        },
        conditions: [
          {
            type: 'sensor',
            sensor_type: 'ph',
            operator: 'between',
            min_value: 5.5,
            max_value: 6.5
          }
        ],
        actions: [
          {
            type: 'pump',
            pump_id: 'ph_down_pump',
            duration_seconds: 5,
            flow_rate: 50
          },
          {
            type: 'wait',
            duration_seconds: 300
          },
          {
            type: 'sensor_reading',
            sensor_types: ['ph']
          }
        ]
      },
      {
        id: 'nutrient_feeding',
        name: 'Nährstoff-Fütterung',
        description: 'Fügt Nährstoffe hinzu basierend auf TDS-Werten',
        schedule: {
          type: 'interval',
          interval_minutes: 360, // Alle 6 Stunden
          start_time: '06:00',
          end_time: '22:00'
        },
        conditions: [
          {
            type: 'sensor',
            sensor_type: 'tds',
            operator: 'less_than',
            value: 800
          }
        ],
        actions: [
          {
            type: 'pump',
            pump_id: 'nutrient_a_pump',
            duration_seconds: 10,
            flow_rate: 75
          },
          {
            type: 'pump',
            pump_id: 'nutrient_b_pump',
            duration_seconds: 10,
            flow_rate: 75
          },
          {
            type: 'wait',
            duration_seconds: 180
          },
          {
            type: 'sensor_reading',
            sensor_types: ['tds']
          }
        ]
      }
    ];
    
    res.json({
      success: true,
      data: templates
    });
  } catch (error) {
    console.error('Error getting program templates:', error);
    res.status(500).json({
      success: false,
      error: 'Fehler beim Laden der Programm-Vorlagen'
    });
  }
});

/**
 * POST /api/programs/from-template
 * Erstellt ein Programm aus einer Vorlage
 */
router.post('/from-template', async (req, res) => {
  try {
    const { template_id, device_id, name, customizations } = req.body;
    
    if (!template_id || !device_id) {
      return res.status(400).json({
        success: false,
        error: 'template_id und device_id sind erforderlich'
      });
    }
    
    // Hole Vorlage (vereinfacht - in echter Implementierung aus DB)
    const templatesResponse = await new Promise((resolve) => {
      router.handle({ method: 'GET', url: '/templates' }, { 
        json: (data) => resolve(data) 
      });
    });
    
    const template = templatesResponse.data.find(t => t.id === template_id);
    if (!template) {
      return res.status(404).json({
        success: false,
        error: 'Vorlage nicht gefunden'
      });
    }
    
    // Erstelle Programm aus Vorlage
    const programData = {
      name: name || template.name,
      description: template.description,
      device_id: device_id,
      schedule: { ...template.schedule, ...customizations?.schedule },
      conditions: customizations?.conditions || template.conditions,
      actions: customizations?.actions || template.actions,
      enabled: true
    };
    
    // Validiere Programm-Daten
    const validationErrors = programModel.validateProgram(programData);
    if (validationErrors.length > 0) {
      return res.status(400).json({
        success: false,
        error: 'Validierungsfehler',
        details: validationErrors
      });
    }
    
    const program = await programModel.createProgram(programData);
    
    res.status(201).json({
      success: true,
      data: program,
      message: 'Programm aus Vorlage erstellt'
    });
  } catch (error) {
    console.error('Error creating program from template:', error);
    res.status(500).json({
      success: false,
      error: 'Fehler beim Erstellen des Programms aus Vorlage'
    });
  }
});

export default router; 