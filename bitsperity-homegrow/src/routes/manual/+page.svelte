<script>
  import { onMount } from 'svelte';
  import { deviceStore, onlineDevices } from '$lib/stores/deviceStore.js';
  import { sensorStore, allLatestReadings } from '$lib/stores/sensorStore.js';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';

  let selectedDevice = null;
  let commandInProgress = false;
  let lastCommandResult = null;
  let showConfirmDialog = false;
  let pendingCommand = null;

  // Pump configurations
  const pumpTypes = [
    { 
      id: 'water', 
      name: 'Wasserpumpe', 
      icon: '💧',
      description: 'Hauptwasserzufuhr',
      color: 'blue'
    },
    { 
      id: 'air', 
      name: 'Luftpumpe', 
      icon: '💨',
      description: 'Belüftung des Wassers',
      color: 'gray'
    },
    { 
      id: 'ph_down', 
      name: 'pH- Pumpe', 
      icon: '🔻',
      description: 'pH-Wert senken',
      color: 'red'
    },
    { 
      id: 'ph_up', 
      name: 'pH+ Pumpe', 
      icon: '🔺',
      description: 'pH-Wert erhöhen',
      color: 'green'
    },
    { 
      id: 'nutrient_a', 
      name: 'Nährstoff A', 
      icon: '🧪',
      description: 'Hauptnährstoffe',
      color: 'purple'
    },
    { 
      id: 'nutrient_b', 
      name: 'Nährstoff B', 
      icon: '⚗️',
      description: 'Mikronährstoffe',
      color: 'orange'
    },
    { 
      id: 'cal_mag', 
      name: 'Cal-Mag', 
      icon: '🧲',
      description: 'Calcium & Magnesium',
      color: 'yellow'
    }
  ];

  onMount(async () => {
    await deviceStore.initialize();
    
    // Select first online device if available
    if ($onlineDevices.length > 0) {
      selectedDevice = $onlineDevices[0];
      await loadDeviceReadings();
    }
  });

  async function loadDeviceReadings() {
    if (selectedDevice) {
      await sensorStore.getLatestReadings(selectedDevice.device_id);
    }
  }

  async function handleDeviceSelect(device) {
    selectedDevice = device;
    await loadDeviceReadings();
  }

  async function sendPumpCommand(pumpId, duration) {
    if (!selectedDevice) return;

    const command = {
      command: 'activate_pump',
      params: {
        pump_id: pumpId,
        duration_seconds: duration
      }
    };

    pendingCommand = { pumpId, duration, command };
    showConfirmDialog = true;
  }

  async function confirmCommand() {
    if (!pendingCommand || !selectedDevice) return;

    commandInProgress = true;
    showConfirmDialog = false;

    try {
      const result = await deviceStore.sendCommand(
        selectedDevice.device_id,
        pendingCommand.command.command,
        pendingCommand.command.params
      );

      lastCommandResult = {
        success: true,
        message: `${getPumpName(pendingCommand.pumpId)} für ${pendingCommand.duration}s aktiviert`,
        timestamp: new Date()
      };

      console.log('Command sent successfully:', result);
    } catch (error) {
      lastCommandResult = {
        success: false,
        message: `Fehler beim Senden des Befehls: ${error.message}`,
        timestamp: new Date()
      };
    } finally {
      commandInProgress = false;
      pendingCommand = null;
      
      // Clear result after 5 seconds
      setTimeout(() => {
        lastCommandResult = null;
      }, 5000);
    }
  }

  function cancelCommand() {
    showConfirmDialog = false;
    pendingCommand = null;
  }

  async function emergencyStop() {
    if (!selectedDevice) return;

    commandInProgress = true;
    try {
      await deviceStore.emergencyStop(selectedDevice.device_id);
      lastCommandResult = {
        success: true,
        message: 'Notaus aktiviert - alle Pumpen gestoppt',
        timestamp: new Date()
      };
    } catch (error) {
      lastCommandResult = {
        success: false,
        message: `Fehler beim Notaus: ${error.message}`,
        timestamp: new Date()
      };
    } finally {
      commandInProgress = false;
      
      setTimeout(() => {
        lastCommandResult = null;
      }, 5000);
    }
  }

  function getPumpName(pumpId) {
    const pump = pumpTypes.find(p => p.id === pumpId);
    return pump ? pump.name : pumpId;
  }

  function getPumpConfig(pumpId) {
    if (!selectedDevice?.config?.actuators?.pumps) return null;
    return selectedDevice.config.actuators.pumps[pumpId];
  }

  function formatValue(value, unit, precision = 1) {
    if (value === null || value === undefined) return '--';
    return `${Number(value).toFixed(precision)} ${unit}`;
  }

  $: deviceReadings = selectedDevice ? $allLatestReadings[selectedDevice.device_id] || {} : {};
</script>

<svelte:head>
  <title>Manuelle Steuerung - HomeGrow v3</title>
</svelte:head>

<div class="manual-control-page">
  <!-- Header -->
  <div class="page-header">
    <div class="header-content">
      <h1 class="page-title">Manuelle Steuerung</h1>
      <p class="page-subtitle">Direkte Kontrolle der Pumpen und Aktoren</p>
    </div>
    
    <div class="header-actions">
      <Button 
        variant="danger" 
        size="lg" 
        on:click={emergencyStop}
        disabled={!selectedDevice || commandInProgress}
      >
        🚨 NOTAUS
      </Button>
    </div>
  </div>

  <!-- Device Selection -->
  <Card title="Gerät auswählen" padding="md">
    {#if $onlineDevices.length === 0}
      <div class="no-devices">
        <svg class="no-devices-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
        <p>Keine Online-Geräte verfügbar</p>
        <Button variant="primary" size="sm" on:click={() => deviceStore.discoverDevices()}>
          Geräte suchen
        </Button>
      </div>
    {:else}
      <div class="device-selector">
        {#each $onlineDevices as device}
          <button 
            class="device-option"
            class:selected={selectedDevice?.device_id === device.device_id}
            on:click={() => handleDeviceSelect(device)}
          >
            <div class="device-option-info">
              <span class="device-option-name">{device.name}</span>
              <span class="device-option-id">{device.device_id}</span>
            </div>
            <div class="device-option-status">
              <div class="status-dot online"></div>
            </div>
          </button>
        {/each}
      </div>
    {/if}
  </Card>

  {#if selectedDevice}
    <!-- Current Sensor Readings -->
    <Card title="Aktuelle Messwerte" padding="md">
      {#if Object.keys(deviceReadings).length > 0}
        <div class="sensor-grid">
          {#if deviceReadings.ph}
            <div class="sensor-card ph">
              <div class="sensor-icon">🧪</div>
              <div class="sensor-info">
                <span class="sensor-label">pH-Wert</span>
                <span class="sensor-value">
                  {formatValue(deviceReadings.ph.values.calibrated, '')}
                </span>
              </div>
            </div>
          {/if}
          
          {#if deviceReadings.tds}
            <div class="sensor-card tds">
              <div class="sensor-icon">⚡</div>
              <div class="sensor-info">
                <span class="sensor-label">TDS</span>
                <span class="sensor-value">
                  {formatValue(deviceReadings.tds.values.calibrated, 'ppm', 0)}
                </span>
              </div>
            </div>
          {/if}
          
          {#if deviceReadings.temperature}
            <div class="sensor-card temperature">
              <div class="sensor-icon">🌡️</div>
              <div class="sensor-info">
                <span class="sensor-label">Temperatur</span>
                <span class="sensor-value">
                  {formatValue(deviceReadings.temperature.values.calibrated, '°C')}
                </span>
              </div>
            </div>
          {/if}
        </div>
      {:else}
        <div class="no-readings">
          <p>Keine aktuellen Messwerte verfügbar</p>
        </div>
      {/if}
    </Card>

    <!-- Pump Controls -->
    <Card title="Pumpen-Steuerung" padding="md">
      <div class="pump-grid">
        {#each pumpTypes as pump}
          {@const pumpConfig = getPumpConfig(pump.id)}
          <div class="pump-card {pump.color}">
            <div class="pump-header">
              <div class="pump-icon">{pump.icon}</div>
              <div class="pump-info">
                <h3 class="pump-name">{pump.name}</h3>
                <p class="pump-description">{pump.description}</p>
              </div>
            </div>
            
            {#if pumpConfig && pumpConfig.enabled}
              <div class="pump-config">
                <div class="config-item">
                  <span class="config-label">Durchfluss:</span>
                  <span class="config-value">{pumpConfig.flow_rate_ml_per_sec} ml/s</span>
                </div>
                <div class="config-item">
                  <span class="config-label">Max. Laufzeit:</span>
                  <span class="config-value">{pumpConfig.max_runtime_sec}s</span>
                </div>
              </div>
              
              <div class="pump-controls">
                <div class="duration-buttons">
                  <Button 
                    variant="secondary" 
                    size="sm" 
                    on:click={() => sendPumpCommand(pump.id, 5)}
                    disabled={commandInProgress}
                  >
                    5s
                  </Button>
                  <Button 
                    variant="secondary" 
                    size="sm" 
                    on:click={() => sendPumpCommand(pump.id, 10)}
                    disabled={commandInProgress}
                  >
                    10s
                  </Button>
                  <Button 
                    variant="secondary" 
                    size="sm" 
                    on:click={() => sendPumpCommand(pump.id, 30)}
                    disabled={commandInProgress}
                  >
                    30s
                  </Button>
                  <Button 
                    variant="primary" 
                    size="sm" 
                    on:click={() => sendPumpCommand(pump.id, 60)}
                    disabled={commandInProgress}
                  >
                    60s
                  </Button>
                </div>
              </div>
            {:else}
              <div class="pump-disabled">
                <p>Pumpe deaktiviert</p>
              </div>
            {/if}
          </div>
        {/each}
      </div>
    </Card>

    <!-- Command Status -->
    {#if lastCommandResult}
      <Card padding="md">
        <div class="command-result {lastCommandResult.success ? 'success' : 'error'}">
          <div class="result-icon">
            {lastCommandResult.success ? '✅' : '❌'}
          </div>
          <div class="result-content">
            <p class="result-message">{lastCommandResult.message}</p>
            <span class="result-timestamp">
              {lastCommandResult.timestamp.toLocaleTimeString()}
            </span>
          </div>
        </div>
      </Card>
    {/if}
  {/if}
</div>

<!-- Confirmation Dialog -->
{#if showConfirmDialog && pendingCommand}
  <div class="dialog-overlay" on:click={cancelCommand}>
    <div class="dialog" on:click|stopPropagation>
      <div class="dialog-header">
        <h3>Befehl bestätigen</h3>
      </div>
      
      <div class="dialog-content">
        <p>
          Möchten Sie die <strong>{getPumpName(pendingCommand.pumpId)}</strong> 
          für <strong>{pendingCommand.duration} Sekunden</strong> aktivieren?
        </p>
        
        <div class="warning">
          ⚠️ Stellen Sie sicher, dass alle Behälter ausreichend gefüllt sind.
        </div>
      </div>
      
      <div class="dialog-actions">
        <Button variant="secondary" on:click={cancelCommand}>
          Abbrechen
        </Button>
        <Button variant="primary" on:click={confirmCommand} loading={commandInProgress}>
          Bestätigen
        </Button>
      </div>
    </div>
  </div>
{/if}

<style>
  .manual-control-page {
    max-width: 1400px;
    margin: 0 auto;
    padding: 1rem;
    display: grid;
    gap: 1.5rem;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
  }

  .header-content {
    flex: 1;
  }

  .page-title {
    font-size: 2rem;
    font-weight: 700;
    color: #1f2937;
    margin: 0 0 0.5rem 0;
  }

  .page-subtitle {
    color: #6b7280;
    margin: 0;
  }

  .header-actions {
    display: flex;
    gap: 0.5rem;
  }

  .no-devices {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 2rem;
    text-align: center;
  }

  .no-devices-icon {
    width: 3rem;
    height: 3rem;
    color: #9ca3af;
    margin-bottom: 1rem;
  }

  .no-devices p {
    color: #6b7280;
    margin: 0 0 1rem 0;
  }

  .device-selector {
    display: grid;
    gap: 0.5rem;
  }

  .device-option {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .device-option:hover {
    background: #f3f4f6;
  }

  .device-option.selected {
    background: #dbeafe;
    border-color: #3b82f6;
  }

  .device-option-info {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .device-option-name {
    font-weight: 500;
    color: #1f2937;
  }

  .device-option-id {
    font-size: 0.75rem;
    color: #6b7280;
    font-family: monospace;
  }

  .device-option-status {
    display: flex;
    align-items: center;
  }

  .status-dot {
    width: 0.5rem;
    height: 0.5rem;
    border-radius: 50%;
  }

  .status-dot.online {
    background: #10b981;
  }

  .sensor-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }

  .sensor-card {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    border-radius: 0.5rem;
    border: 1px solid #e5e7eb;
  }

  .sensor-card.ph {
    background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  }

  .sensor-card.tds {
    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  }

  .sensor-card.temperature {
    background: linear-gradient(135deg, #fed7d7 0%, #feb2b2 100%);
  }

  .sensor-icon {
    font-size: 1.5rem;
  }

  .sensor-info {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .sensor-label {
    font-size: 0.875rem;
    color: #6b7280;
    font-weight: 500;
  }

  .sensor-value {
    font-size: 1.25rem;
    font-weight: 700;
    color: #1f2937;
    font-family: monospace;
  }

  .no-readings {
    text-align: center;
    padding: 2rem;
    color: #9ca3af;
  }

  .pump-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
  }

  .pump-card {
    border: 1px solid #e5e7eb;
    border-radius: 0.75rem;
    padding: 1.5rem;
    background: white;
  }

  .pump-card.blue {
    border-left: 4px solid #3b82f6;
  }

  .pump-card.gray {
    border-left: 4px solid #6b7280;
  }

  .pump-card.red {
    border-left: 4px solid #ef4444;
  }

  .pump-card.green {
    border-left: 4px solid #10b981;
  }

  .pump-card.purple {
    border-left: 4px solid #8b5cf6;
  }

  .pump-card.orange {
    border-left: 4px solid #f59e0b;
  }

  .pump-card.yellow {
    border-left: 4px solid #eab308;
  }

  .pump-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .pump-icon {
    font-size: 2rem;
  }

  .pump-info {
    flex: 1;
  }

  .pump-name {
    font-size: 1.125rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0 0 0.25rem 0;
  }

  .pump-description {
    font-size: 0.875rem;
    color: #6b7280;
    margin: 0;
  }

  .pump-config {
    margin-bottom: 1rem;
    padding: 0.75rem;
    background: #f9fafb;
    border-radius: 0.375rem;
    border: 1px solid #f3f4f6;
  }

  .config-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.25rem;
  }

  .config-item:last-child {
    margin-bottom: 0;
  }

  .config-label {
    font-size: 0.875rem;
    color: #6b7280;
  }

  .config-value {
    font-size: 0.875rem;
    font-weight: 600;
    color: #374151;
    font-family: monospace;
  }

  .pump-controls {
    margin-top: 1rem;
  }

  .duration-buttons {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.5rem;
  }

  .pump-disabled {
    text-align: center;
    padding: 1rem;
    color: #9ca3af;
    font-style: italic;
  }

  .command-result {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    border-radius: 0.5rem;
  }

  .command-result.success {
    background: #d1fae5;
    border: 1px solid #a7f3d0;
  }

  .command-result.error {
    background: #fee2e2;
    border: 1px solid #fecaca;
  }

  .result-icon {
    font-size: 1.5rem;
  }

  .result-content {
    flex: 1;
  }

  .result-message {
    margin: 0 0 0.25rem 0;
    font-weight: 500;
    color: #1f2937;
  }

  .result-timestamp {
    font-size: 0.75rem;
    color: #6b7280;
  }

  .dialog-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .dialog {
    background: white;
    border-radius: 0.75rem;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
    max-width: 400px;
    width: 90%;
    max-height: 90vh;
    overflow: auto;
  }

  .dialog-header {
    padding: 1.5rem 1.5rem 0;
  }

  .dialog-header h3 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0;
  }

  .dialog-content {
    padding: 1rem 1.5rem;
  }

  .dialog-content p {
    margin: 0 0 1rem 0;
    color: #374151;
  }

  .warning {
    padding: 0.75rem;
    background: #fef3c7;
    border: 1px solid #f59e0b;
    border-radius: 0.375rem;
    font-size: 0.875rem;
    color: #92400e;
  }

  .dialog-actions {
    padding: 0 1.5rem 1.5rem;
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
  }

  @media (max-width: 768px) {
    .manual-control-page {
      padding: 0.5rem;
    }

    .page-header {
      flex-direction: column;
      align-items: stretch;
    }

    .sensor-grid {
      grid-template-columns: 1fr;
    }

    .pump-grid {
      grid-template-columns: 1fr;
    }

    .duration-buttons {
      grid-template-columns: repeat(2, 1fr);
    }
  }
</style> 