<script>
  import { onMount, onDestroy } from 'svelte';
  import { deviceStore, onlineDevices } from '$lib/stores/deviceStore.js';
  import { sensorStore, allLatestReadings } from '$lib/stores/sensorStore.js';
  import SensorChart from '$lib/components/charts/SensorChart.svelte';
  import DeviceCard from '$lib/components/device/DeviceCard.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';

  let selectedDevice = null;
  let selectedSensorType = 'ph';
  let timeRange = '24h';
  let autoRefresh = true;
  let refreshInterval;
  let chartData = [];
  let loading = false;

  const sensorTypes = [
    { value: 'ph', label: 'pH-Wert', unit: 'pH' },
    { value: 'tds', label: 'TDS', unit: 'ppm' },
    { value: 'temperature', label: 'Temperatur', unit: '°C' },
    { value: 'humidity', label: 'Luftfeuchtigkeit', unit: '%' }
  ];

  const timeRanges = [
    { value: '1h', label: '1 Stunde' },
    { value: '6h', label: '6 Stunden' },
    { value: '24h', label: '24 Stunden' },
    { value: '7d', label: '7 Tage' },
    { value: '30d', label: '30 Tage' }
  ];

  onMount(async () => {
    await deviceStore.initialize();
    
    // Select first online device if available
    if ($onlineDevices.length > 0) {
      selectedDevice = $onlineDevices[0];
      await loadChartData();
    }

    // Start auto-refresh
    if (autoRefresh) {
      startAutoRefresh();
    }
  });

  onDestroy(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
  });

  function startAutoRefresh() {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
    
    refreshInterval = setInterval(async () => {
      if (selectedDevice) {
        await sensorStore.getLatestReadings(selectedDevice.device_id);
        if (timeRange === '1h' || timeRange === '6h') {
          await loadChartData();
        }
      }
    }, 30000); // Every 30 seconds
  }

  function stopAutoRefresh() {
    if (refreshInterval) {
      clearInterval(refreshInterval);
      refreshInterval = null;
    }
  }

  async function loadChartData() {
    if (!selectedDevice || !selectedSensorType) return;

    loading = true;
    try {
      const timeRangeMap = {
        '1h': { start_time: new Date(Date.now() - 60 * 60 * 1000).toISOString() },
        '6h': { start_time: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString() },
        '24h': { start_time: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString() },
        '7d': { start_time: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString() },
        '30d': { start_time: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString() }
      };

      chartData = await sensorStore.getHistoricalData(
        selectedDevice.device_id,
        selectedSensorType,
        timeRangeMap[timeRange]
      );
    } catch (error) {
      console.error('Failed to load chart data:', error);
    } finally {
      loading = false;
    }
  }

  async function handleDeviceSelect(device) {
    selectedDevice = device;
    await sensorStore.getLatestReadings(device.device_id);
    await loadChartData();
  }

  async function handleSensorTypeChange() {
    await loadChartData();
  }

  async function handleTimeRangeChange() {
    await loadChartData();
  }

  function handleAutoRefreshToggle() {
    autoRefresh = !autoRefresh;
    if (autoRefresh) {
      startAutoRefresh();
    } else {
      stopAutoRefresh();
    }
  }

  async function handleRefresh() {
    await deviceStore.initialize();
    if (selectedDevice) {
      await sensorStore.getLatestReadings(selectedDevice.device_id);
      await loadChartData();
    }
  }

  function handleDeviceAction(event) {
    const { type, detail } = event;
    
    switch (type) {
      case 'view-details':
        // Navigate to device details
        window.location.href = `/devices/${detail.device_id}`;
        break;
      case 'emergency-stop':
        deviceStore.emergencyStop(detail.device_id);
        break;
      case 'send-command':
        // Open command modal (to be implemented)
        console.log('Send command to:', detail.device_id);
        break;
    }
  }

  $: selectedSensor = sensorTypes.find(s => s.value === selectedSensorType);
  $: deviceReadings = selectedDevice ? $allLatestReadings[selectedDevice.device_id] || {} : {};
</script>

<svelte:head>
  <title>Live Monitoring - HomeGrow v3</title>
</svelte:head>

<div class="monitoring-page">
  <!-- Header -->
  <div class="page-header">
    <div class="header-content">
      <h1 class="page-title">Live Monitoring</h1>
      <p class="page-subtitle">Echtzeit-Überwachung der hydroponischen Systeme</p>
    </div>
    
    <div class="header-actions">
      <Button 
        variant="secondary" 
        size="sm" 
        on:click={handleRefresh}
        loading={$deviceStore.loading}
      >
        Aktualisieren
      </Button>
      
      <Button 
        variant={autoRefresh ? 'success' : 'secondary'} 
        size="sm" 
        on:click={handleAutoRefreshToggle}
      >
        {autoRefresh ? 'Auto-Refresh AN' : 'Auto-Refresh AUS'}
      </Button>
    </div>
  </div>

  <div class="monitoring-content">
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
      <!-- Chart Controls -->
      <Card title="Chart-Einstellungen" padding="md">
        <div class="chart-controls">
          <div class="control-group">
            <label for="sensor-type">Sensor-Typ:</label>
            <select 
              id="sensor-type" 
              bind:value={selectedSensorType} 
              on:change={handleSensorTypeChange}
              class="control-select"
            >
              {#each sensorTypes as sensor}
                <option value={sensor.value}>{sensor.label}</option>
              {/each}
            </select>
          </div>
          
          <div class="control-group">
            <label for="time-range">Zeitraum:</label>
            <select 
              id="time-range" 
              bind:value={timeRange} 
              on:change={handleTimeRangeChange}
              class="control-select"
            >
              {#each timeRanges as range}
                <option value={range.value}>{range.label}</option>
              {/each}
            </select>
          </div>
        </div>
      </Card>

      <!-- Chart -->
      <div class="chart-section">
        {#if loading}
          <Card padding="lg">
            <div class="loading-state">
              <div class="spinner"></div>
              <p>Lade Chart-Daten...</p>
            </div>
          </Card>
        {:else if selectedSensor}
          <SensorChart 
            data={chartData}
            sensorType={selectedSensorType}
            unit={selectedSensor.unit}
            timeRange={timeRange}
            height={400}
          />
        {/if}
      </div>

      <!-- Current Device Status -->
      <div class="device-status-section">
        <DeviceCard 
          device={selectedDevice}
          sensorReadings={deviceReadings}
          showActions={true}
          on:view-details={(e) => handleDeviceAction({ type: 'view-details', detail: e.detail })}
          on:emergency-stop={(e) => handleDeviceAction({ type: 'emergency-stop', detail: e.detail })}
          on:send-command={(e) => handleDeviceAction({ type: 'send-command', detail: e.detail })}
        />
      </div>
    {/if}
  </div>
</div>

<style>
  .monitoring-page {
    max-width: 1400px;
    margin: 0 auto;
    padding: 1rem;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 2rem;
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
    flex-wrap: wrap;
  }

  .monitoring-content {
    display: grid;
    gap: 1.5rem;
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

  .chart-controls {
    display: flex;
    gap: 2rem;
    flex-wrap: wrap;
  }

  .control-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    min-width: 150px;
  }

  .control-group label {
    font-size: 0.875rem;
    font-weight: 500;
    color: #374151;
  }

  .control-select {
    padding: 0.5rem;
    border: 1px solid #d1d5db;
    border-radius: 0.375rem;
    background: white;
    font-size: 0.875rem;
    color: #1f2937;
  }

  .control-select:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 1px #3b82f6;
  }

  .chart-section {
    min-height: 450px;
  }

  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem;
    gap: 1rem;
  }

  .spinner {
    width: 2rem;
    height: 2rem;
    border: 3px solid #f3f4f6;
    border-top: 3px solid #3b82f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .loading-state p {
    color: #6b7280;
    margin: 0;
  }

  .device-status-section {
    max-width: 600px;
  }

  @media (max-width: 768px) {
    .monitoring-page {
      padding: 0.5rem;
    }

    .page-header {
      flex-direction: column;
      align-items: stretch;
    }

    .header-actions {
      justify-content: space-between;
    }

    .chart-controls {
      flex-direction: column;
      gap: 1rem;
    }

    .control-group {
      min-width: auto;
    }
  }
</style> 