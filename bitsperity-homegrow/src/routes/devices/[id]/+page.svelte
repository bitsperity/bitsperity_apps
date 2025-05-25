<script>
  import { onMount, onDestroy } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { deviceStore } from '$lib/stores/deviceStore.js';
  import { sensorStore } from '$lib/stores/sensorStore.js';
  import { showSuccess, showError, showCommandSent } from '$lib/stores/notification.js';
  import SensorChart from '$lib/components/charts/SensorChart.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';

  let deviceId = '';
  let device = null;
  let sensorReadings = {};
  let historicalData = {};
  let loading = true;
  let refreshInterval;
  let selectedTimeRange = '24h';
  let showConfigModal = false;
  let configForm = {};

  const timeRanges = [
    { value: '1h', label: '1 Stunde' },
    { value: '6h', label: '6 Stunden' },
    { value: '24h', label: '24 Stunden' },
    { value: '7d', label: '7 Tage' },
    { value: '30d', label: '30 Tage' }
  ];

  const sensorTypes = [
    { value: 'ph', label: 'pH-Wert', unit: 'pH', color: '#3b82f6' },
    { value: 'tds', label: 'TDS', unit: 'ppm', color: '#10b981' },
    { value: 'temperature', label: 'Temperatur', unit: '°C', color: '#f59e0b' },
    { value: 'humidity', label: 'Luftfeuchtigkeit', unit: '%', color: '#8b5cf6' }
  ];

  onMount(async () => {
    deviceId = $page.params.id;
    await loadDeviceData();
    startAutoRefresh();
  });

  onDestroy(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
  });

  async function loadDeviceData() {
    loading = true;
    try {
      // Lade Gerätedaten
      const devices = await deviceStore.getDevices();
      device = devices.find(d => d.device_id === deviceId);
      
      if (!device) {
        showError('Gerät nicht gefunden');
        goto('/devices');
        return;
      }

      // Lade aktuelle Sensordaten
      sensorReadings = await sensorStore.getLatestReadings(deviceId);

      // Lade historische Daten für alle Sensoren
      await loadHistoricalData();

    } catch (error) {
      console.error('Failed to load device data:', error);
      showError('Fehler beim Laden der Gerätedaten');
    } finally {
      loading = false;
    }
  }

  async function loadHistoricalData() {
    const timeRangeMap = {
      '1h': { start_time: new Date(Date.now() - 60 * 60 * 1000).toISOString() },
      '6h': { start_time: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString() },
      '24h': { start_time: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString() },
      '7d': { start_time: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString() },
      '30d': { start_time: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString() }
    };

    const promises = sensorTypes.map(async (sensor) => {
      try {
        const data = await sensorStore.getHistoricalData(
          deviceId,
          sensor.value,
          timeRangeMap[selectedTimeRange]
        );
        return [sensor.value, data];
      } catch (error) {
        console.error(`Failed to load ${sensor.value} data:`, error);
        return [sensor.value, []];
      }
    });

    const results = await Promise.all(promises);
    historicalData = Object.fromEntries(results);
  }

  function startAutoRefresh() {
    refreshInterval = setInterval(async () => {
      if (device && device.status === 'online') {
        sensorReadings = await sensorStore.getLatestReadings(deviceId);
      }
    }, 30000); // Every 30 seconds
  }

  async function handleTimeRangeChange() {
    await loadHistoricalData();
  }

  async function handleRefresh() {
    await loadDeviceData();
    showSuccess('Daten aktualisiert');
  }

  async function handleEmergencyStop() {
    try {
      await deviceStore.emergencyStop(deviceId);
      showSuccess('Notaus aktiviert');
      await loadDeviceData();
    } catch (error) {
      showError('Fehler beim Notaus: ' + error.message);
    }
  }

  async function handleSendCommand(command, params = {}) {
    try {
      await deviceStore.sendCommand(deviceId, command, params);
      showCommandSent(device.name, command);
    } catch (error) {
      showError(`Befehl fehlgeschlagen: ${error.message}`);
    }
  }

  function openConfigModal() {
    configForm = { ...device.config };
    showConfigModal = true;
  }

  async function saveConfig() {
    try {
      await deviceStore.updateDeviceConfig(deviceId, configForm);
      showSuccess('Konfiguration gespeichert');
      showConfigModal = false;
      await loadDeviceData();
    } catch (error) {
      showError('Fehler beim Speichern: ' + error.message);
    }
  }

  function formatValue(value, unit, precision = 1) {
    if (value === null || value === undefined) return '--';
    return `${Number(value).toFixed(precision)} ${unit}`;
  }

  function getStatusColor(status) {
    switch (status) {
      case 'online': return 'text-green-600';
      case 'offline': return 'text-red-600';
      default: return 'text-gray-600';
    }
  }
</script>

<svelte:head>
  <title>{device ? `${device.name} - HomeGrow v3` : 'Gerät laden...'}</title>
</svelte:head>

{#if loading}
  <div class="loading-container">
    <LoadingSpinner size="lg" text="Lade Gerätedaten..." centered />
  </div>
{:else if device}
  <div class="device-detail-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-content">
        <div class="breadcrumb">
          <a href="/devices" class="breadcrumb-link">Geräte</a>
          <span class="breadcrumb-separator">›</span>
          <span class="breadcrumb-current">{device.name}</span>
        </div>
        
        <h1 class="page-title">{device.name}</h1>
        <div class="device-meta">
          <span class="device-id">ID: {device.device_id}</span>
          <span class="device-status {getStatusColor(device.status)}">
            <div class="status-dot {device.status}"></div>
            {device.status}
          </span>
          {#if device.location}
            <span class="device-location">📍 {device.location}</span>
          {/if}
        </div>
      </div>
      
      <div class="header-actions">
        <Button variant="secondary" size="sm" on:click={handleRefresh}>
          Aktualisieren
        </Button>
        <Button variant="secondary" size="sm" on:click={openConfigModal}>
          Konfiguration
        </Button>
        {#if device.status === 'online'}
          <Button variant="danger" size="sm" on:click={handleEmergencyStop}>
            Notaus
          </Button>
        {/if}
      </div>
    </div>

    <!-- Current Status -->
    <Card title="Aktueller Status" padding="md">
      {#if Object.keys(sensorReadings).length > 0}
        <div class="sensor-grid">
          {#each sensorTypes as sensor}
            {#if sensorReadings[sensor.value]}
              <div class="sensor-card" style="border-left-color: {sensor.color}">
                <div class="sensor-header">
                  <span class="sensor-label">{sensor.label}</span>
                  <span class="sensor-value" style="color: {sensor.color}">
                    {formatValue(sensorReadings[sensor.value].values.calibrated, sensor.unit)}
                  </span>
                </div>
                <div class="sensor-meta">
                  <span class="sensor-timestamp">
                    {new Date(sensorReadings[sensor.value].timestamp).toLocaleString()}
                  </span>
                  <span class="sensor-quality">
                    Qualität: {sensorReadings[sensor.value].quality || 'Gut'}
                  </span>
                </div>
              </div>
            {/if}
          {/each}
        </div>
      {:else}
        <div class="no-data">
          <p>Keine aktuellen Sensordaten verfügbar</p>
        </div>
      {/if}
    </Card>

    <!-- Time Range Selector -->
    <Card title="Historische Daten" padding="md">
      <div class="time-range-selector">
        <label for="time-range">Zeitraum:</label>
        <select 
          id="time-range" 
          bind:value={selectedTimeRange} 
          on:change={handleTimeRangeChange}
          class="time-range-select"
        >
          {#each timeRanges as range}
            <option value={range.value}>{range.label}</option>
          {/each}
        </select>
      </div>
    </Card>

    <!-- Charts -->
    <div class="charts-grid">
      {#each sensorTypes as sensor}
        {#if historicalData[sensor.value] && historicalData[sensor.value].length > 0}
          <SensorChart 
            data={historicalData[sensor.value]}
            sensorType={sensor.value}
            unit={sensor.unit}
            timeRange={selectedTimeRange}
            height={300}
          />
        {/if}
      {/each}
    </div>

    <!-- Device Info -->
    <div class="device-info-grid">
      <!-- System Info -->
      <Card title="System-Informationen" padding="md">
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">Firmware:</span>
            <span class="info-value">{device.firmware_version || 'Unbekannt'}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Uptime:</span>
            <span class="info-value">{device.stats?.uptime_hours || 0}h</span>
          </div>
          <div class="info-item">
            <span class="info-label">WiFi Signal:</span>
            <span class="info-value">{device.stats?.wifi_signal_strength || 0}%</span>
          </div>
          <div class="info-item">
            <span class="info-label">Letzte Verbindung:</span>
            <span class="info-value">
              {device.last_seen ? new Date(device.last_seen).toLocaleString() : 'Nie'}
            </span>
          </div>
        </div>
      </Card>

      <!-- Quick Actions -->
      <Card title="Schnellaktionen" padding="md">
        <div class="actions-grid">
          <Button 
            variant="primary" 
            size="sm" 
            fullWidth
            disabled={device.status !== 'online'}
            on:click={() => handleSendCommand('calibrate_sensors')}
          >
            Sensoren kalibrieren
          </Button>
          <Button 
            variant="secondary" 
            size="sm" 
            fullWidth
            disabled={device.status !== 'online'}
            on:click={() => handleSendCommand('restart_system')}
          >
            System neustarten
          </Button>
          <Button 
            variant="secondary" 
            size="sm" 
            fullWidth
            disabled={device.status !== 'online'}
            on:click={() => handleSendCommand('run_diagnostics')}
          >
            Diagnose ausführen
          </Button>
        </div>
      </Card>
    </div>
  </div>
{:else}
  <div class="error-container">
    <h1>Gerät nicht gefunden</h1>
    <p>Das angeforderte Gerät konnte nicht gefunden werden.</p>
    <Button variant="primary" href="/devices">Zurück zur Geräteliste</Button>
  </div>
{/if}

<!-- Config Modal -->
{#if showConfigModal}
  <div class="modal-overlay" on:click={() => showConfigModal = false}>
    <div class="modal" on:click|stopPropagation>
      <div class="modal-header">
        <h3>Gerätekonfiguration</h3>
        <button class="modal-close" on:click={() => showConfigModal = false}>×</button>
      </div>
      
      <div class="modal-content">
        <div class="config-section">
          <h4>Allgemein</h4>
          <div class="form-group">
            <label for="device-name">Gerätename:</label>
            <input 
              id="device-name" 
              type="text" 
              bind:value={configForm.name}
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label for="device-location">Standort:</label>
            <input 
              id="device-location" 
              type="text" 
              bind:value={configForm.location}
              class="form-input"
            />
          </div>
        </div>
      </div>
      
      <div class="modal-actions">
        <Button variant="secondary" on:click={() => showConfigModal = false}>
          Abbrechen
        </Button>
        <Button variant="primary" on:click={saveConfig}>
          Speichern
        </Button>
      </div>
    </div>
  </div>
{/if}

<style>
  .device-detail-page {
    max-width: 1400px;
    margin: 0 auto;
    padding: 1rem;
    display: grid;
    gap: 1.5rem;
  }

  .loading-container,
  .error-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 400px;
    text-align: center;
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

  .breadcrumb {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
  }

  .breadcrumb-link {
    color: #3b82f6;
    text-decoration: none;
  }

  .breadcrumb-link:hover {
    text-decoration: underline;
  }

  .breadcrumb-separator {
    color: #9ca3af;
  }

  .breadcrumb-current {
    color: #6b7280;
  }

  .page-title {
    font-size: 2rem;
    font-weight: 700;
    color: #1f2937;
    margin: 0 0 0.5rem 0;
  }

  .device-meta {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .device-id {
    font-family: monospace;
    font-size: 0.875rem;
    color: #6b7280;
  }

  .device-status {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    font-size: 0.875rem;
    font-weight: 500;
  }

  .status-dot {
    width: 0.5rem;
    height: 0.5rem;
    border-radius: 50%;
  }

  .status-dot.online {
    background: #10b981;
  }

  .status-dot.offline {
    background: #ef4444;
  }

  .device-location {
    font-size: 0.875rem;
    color: #6b7280;
  }

  .header-actions {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .sensor-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
  }

  .sensor-card {
    padding: 1rem;
    border: 1px solid #e5e7eb;
    border-left: 4px solid;
    border-radius: 0.5rem;
    background: #f9fafb;
  }

  .sensor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .sensor-label {
    font-size: 0.875rem;
    color: #6b7280;
    font-weight: 500;
  }

  .sensor-value {
    font-size: 1.25rem;
    font-weight: 700;
    font-family: monospace;
  }

  .sensor-meta {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .sensor-timestamp,
  .sensor-quality {
    font-size: 0.75rem;
    color: #9ca3af;
  }

  .no-data {
    text-align: center;
    padding: 2rem;
    color: #9ca3af;
  }

  .time-range-selector {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .time-range-selector label {
    font-size: 0.875rem;
    font-weight: 500;
    color: #374151;
  }

  .time-range-select {
    padding: 0.5rem;
    border: 1px solid #d1d5db;
    border-radius: 0.375rem;
    background: white;
    font-size: 0.875rem;
  }

  .charts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 1.5rem;
  }

  .device-info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
  }

  .info-grid {
    display: grid;
    gap: 0.75rem;
  }

  .info-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem;
    background: #f9fafb;
    border-radius: 0.375rem;
  }

  .info-label {
    font-size: 0.875rem;
    color: #6b7280;
  }

  .info-value {
    font-size: 0.875rem;
    font-weight: 600;
    color: #374151;
  }

  .actions-grid {
    display: grid;
    gap: 0.75rem;
  }

  .modal-overlay {
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

  .modal {
    background: white;
    border-radius: 0.75rem;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
    max-width: 500px;
    width: 90%;
    max-height: 90vh;
    overflow: auto;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem 1.5rem 0;
  }

  .modal-header h3 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0;
  }

  .modal-close {
    font-size: 1.5rem;
    color: #9ca3af;
    background: none;
    border: none;
    cursor: pointer;
  }

  .modal-content {
    padding: 1rem 1.5rem;
  }

  .config-section {
    margin-bottom: 1.5rem;
  }

  .config-section h4 {
    font-size: 1rem;
    font-weight: 600;
    color: #374151;
    margin: 0 0 1rem 0;
  }

  .form-group {
    margin-bottom: 1rem;
  }

  .form-group label {
    display: block;
    font-size: 0.875rem;
    font-weight: 500;
    color: #374151;
    margin-bottom: 0.25rem;
  }

  .form-input {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #d1d5db;
    border-radius: 0.375rem;
    font-size: 0.875rem;
  }

  .form-input:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 1px #3b82f6;
  }

  .modal-actions {
    padding: 0 1.5rem 1.5rem;
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
  }

  @media (max-width: 768px) {
    .device-detail-page {
      padding: 0.5rem;
    }

    .page-header {
      flex-direction: column;
      align-items: stretch;
    }

    .device-meta {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.5rem;
    }

    .sensor-grid {
      grid-template-columns: 1fr;
    }

    .charts-grid {
      grid-template-columns: 1fr;
    }

    .device-info-grid {
      grid-template-columns: 1fr;
    }
  }
</style> 