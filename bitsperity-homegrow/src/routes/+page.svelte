<script>
  import { onMount, onDestroy } from 'svelte';
  import { deviceStore, deviceCount } from '$lib/stores/deviceStore.js';
  import { sensorStore, allLatestReadings } from '$lib/stores/sensorStore.js';

  let refreshInterval;
  let lastRefresh = new Date();
  let systemStatus = {
    devices: { total: 0, online: 0, offline: 0 },
    alerts: 0,
    programs: 0,
    uptime: '99.9%'
  };

  onMount(async () => {
    // Initial data load
    await refreshDashboard();
    
    // Set up auto-refresh every 30 seconds
    refreshInterval = setInterval(refreshDashboard, 30000);
  });

  onDestroy(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
  });

  async function refreshDashboard() {
    try {
      await deviceStore.initialize();
      
      // Get latest sensor readings for all online devices
      const devices = $deviceStore.devices.filter(d => d.status === 'online');
      
      if (devices.length > 0) {
        await sensorStore.getOverviewData(devices.map(d => d.device_id));
      }
      
      lastRefresh = new Date();
    } catch (error) {
      console.error('Dashboard refresh failed:', error);
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

  function getTrendIcon(trend) {
    switch (trend) {
      case 'up': return '↗️';
      case 'down': return '↘️';
      default: return '➡️';
    }
  }

  $: systemStatus.devices = $deviceCount;
</script>

<svelte:head>
  <title>Dashboard - HomeGrow v3</title>
</svelte:head>

<div class="dashboard">
  <!-- Header -->
  <div class="header">
    <div class="header-content">
      <h1 class="title">Dashboard</h1>
      <p class="subtitle">Übersicht über alle hydroponischen Systeme</p>
    </div>
    
    <div class="header-actions">
      <button 
        class="refresh-button"
        on:click={refreshDashboard}
        disabled={$deviceStore.loading}
      >
        {#if $deviceStore.loading}
          <div class="spinner"></div>
        {:else}
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        {/if}
        Aktualisieren
      </button>
      
      <span class="last-refresh">
        Zuletzt: {lastRefresh.toLocaleTimeString()}
      </span>
    </div>
  </div>

  <!-- System Status Cards -->
  <div class="status-grid">
    <div class="status-card">
      <div class="status-card-header">
        <h3>Geräte</h3>
        <svg class="status-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
      </div>
      <div class="status-value">
        {systemStatus.devices.online}/{systemStatus.devices.total}
      </div>
      <div class="status-label">Online</div>
      <div class="status-trend {systemStatus.devices.online > 0 ? 'positive' : 'negative'}">
        {systemStatus.devices.online > 0 ? '↗️' : '↘️'} 
        {systemStatus.devices.online > 0 ? 'Aktiv' : 'Offline'}
      </div>
    </div>
    
    <div class="status-card">
      <div class="status-card-header">
        <h3>Aktive Alerts</h3>
        <svg class="status-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
      </div>
      <div class="status-value">{systemStatus.alerts}</div>
      <div class="status-label">Benötigen Aufmerksamkeit</div>
      <div class="status-trend neutral">
        ➡️ Alles OK
      </div>
    </div>
    
    <div class="status-card">
      <div class="status-card-header">
        <h3>Programme</h3>
        <svg class="status-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
        </svg>
      </div>
      <div class="status-value">{systemStatus.programs}</div>
      <div class="status-label">Aktiv</div>
      <div class="status-trend neutral">
        ➡️ Bereit
      </div>
    </div>
    
    <div class="status-card">
      <div class="status-card-header">
        <h3>System Uptime</h3>
        <svg class="status-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <div class="status-value">{systemStatus.uptime}</div>
      <div class="status-label">Verfügbarkeit</div>
      <div class="status-trend positive">
        ↗️ Stabil
      </div>
    </div>
  </div>

  <!-- Device Overview -->
  <div class="content-section">
    <h2 class="section-title">Geräte-Übersicht</h2>
    
    {#if $deviceStore.devices.length === 0}
      <div class="empty-state">
        <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
        <h3>Keine Geräte gefunden</h3>
        <p>Starten Sie die Geräte-Erkennung um ESP32 Clients zu finden.</p>
        <button 
          class="discover-button"
          on:click={() => deviceStore.discoverDevices()}
        >
          Geräte suchen
        </button>
      </div>
    {:else}
      <div class="device-grid">
        {#each $deviceStore.devices as device}
          <div class="device-card">
            <div class="device-header">
              <h3 class="device-name">{device.name}</h3>
              <span class="device-status {getStatusColor(device.status)}">
                <div class="status-dot {device.status}"></div>
                {device.status}
              </span>
            </div>
            
            <div class="device-info">
              <div class="device-id">ID: {device.device_id}</div>
              {#if device.location}
                <div class="device-location">📍 {device.location}</div>
              {/if}
              {#if device.last_seen}
                <div class="device-last-seen">
                  Zuletzt gesehen: {new Date(device.last_seen).toLocaleString()}
                </div>
              {/if}
            </div>

            {#if $allLatestReadings[device.device_id]}
              <div class="sensor-readings">
                {#if $allLatestReadings[device.device_id].ph}
                  <div class="sensor-reading">
                    <span class="sensor-label">pH:</span>
                    <span class="sensor-value">
                      {formatValue($allLatestReadings[device.device_id].ph.values.calibrated, 'pH')}
                    </span>
                  </div>
                {/if}
                
                {#if $allLatestReadings[device.device_id].tds}
                  <div class="sensor-reading">
                    <span class="sensor-label">TDS:</span>
                    <span class="sensor-value">
                      {formatValue($allLatestReadings[device.device_id].tds.values.calibrated, 'ppm', 0)}
                    </span>
                  </div>
                {/if}
              </div>
            {:else if device.status === 'online'}
              <div class="sensor-readings">
                <div class="no-data">Warte auf Sensordaten...</div>
              </div>
            {/if}

            <div class="device-actions">
              <a href="/devices/{device.device_id}" class="action-button primary">
                Details
              </a>
              {#if device.status === 'online'}
                <button 
                  class="action-button secondary"
                  on:click={() => deviceStore.emergencyStop(device.device_id)}
                >
                  Stopp
                </button>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Quick Actions -->
  <div class="content-section">
    <h2 class="section-title">Schnellaktionen</h2>
    <div class="quick-actions">
      <button 
        class="quick-action-button"
        on:click={() => deviceStore.discoverDevices()}
      >
        <svg class="action-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <span>Geräte suchen</span>
      </button>
      
      <a href="/monitoring" class="quick-action-button">
        <svg class="action-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <span>Live Monitoring</span>
      </a>
      
      <a href="/manual" class="quick-action-button">
        <svg class="action-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
        </svg>
        <span>Manuelle Steuerung</span>
      </a>
      
      <a href="/programs" class="quick-action-button">
        <svg class="action-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
        </svg>
        <span>Programme</span>
      </a>
    </div>
  </div>
</div>

<style>
  .dashboard {
    max-width: 1400px;
    margin: 0 auto;
    padding: 1rem;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 2rem;
    gap: 1rem;
  }

  .header-content {
    flex: 1;
  }

  .title {
    font-size: 2rem;
    font-weight: 700;
    color: #1f2937;
    margin: 0 0 0.5rem 0;
  }

  .subtitle {
    color: #6b7280;
    margin: 0;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .refresh-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 0.5rem;
    cursor: pointer;
    transition: background-color 0.2s ease;
    font-size: 0.875rem;
  }

  .refresh-button:hover:not(:disabled) {
    background: #2563eb;
  }

  .refresh-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .spinner {
    width: 1rem;
    height: 1rem;
    border: 2px solid transparent;
    border-top: 2px solid currentColor;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .last-refresh {
    font-size: 0.875rem;
    color: #6b7280;
    white-space: nowrap;
  }

  .status-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .status-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 0.75rem;
    padding: 1.5rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  }

  .status-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .status-card-header h3 {
    font-size: 0.875rem;
    font-weight: 600;
    color: #6b7280;
    margin: 0;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .status-icon {
    width: 1.25rem;
    height: 1.25rem;
    color: #9ca3af;
  }

  .status-value {
    font-size: 2rem;
    font-weight: 700;
    color: #1f2937;
    margin-bottom: 0.25rem;
  }

  .status-label {
    font-size: 0.875rem;
    color: #6b7280;
    margin-bottom: 0.5rem;
  }

  .status-trend {
    font-size: 0.75rem;
    font-weight: 500;
  }

  .status-trend.positive {
    color: #059669;
  }

  .status-trend.negative {
    color: #dc2626;
  }

  .status-trend.neutral {
    color: #6b7280;
  }

  .content-section {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 0.75rem;
    padding: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  }

  .section-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0 0 1rem 0;
  }

  .empty-state {
    text-align: center;
    padding: 3rem 1rem;
  }

  .empty-icon {
    width: 4rem;
    height: 4rem;
    color: #9ca3af;
    margin: 0 auto 1rem;
  }

  .empty-state h3 {
    font-size: 1.125rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0 0 0.5rem 0;
  }

  .empty-state p {
    color: #6b7280;
    margin: 0 0 1.5rem 0;
  }

  .discover-button {
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 0.5rem;
    padding: 0.75rem 1.5rem;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s ease;
  }

  .discover-button:hover {
    background: #2563eb;
  }

  .device-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.5rem;
  }

  .device-card {
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    padding: 1rem;
    background: #f9fafb;
  }

  .device-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
  }

  .device-name {
    font-size: 1rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0;
  }

  .device-status {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
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

  .device-info {
    margin-bottom: 1rem;
  }

  .device-id,
  .device-location,
  .device-last-seen {
    font-size: 0.75rem;
    color: #6b7280;
    margin-bottom: 0.25rem;
  }

  .sensor-readings {
    margin-bottom: 1rem;
    padding: 0.75rem;
    background: white;
    border-radius: 0.375rem;
    border: 1px solid #e5e7eb;
  }

  .sensor-reading {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .sensor-reading:last-child {
    margin-bottom: 0;
  }

  .sensor-label {
    font-size: 0.875rem;
    color: #6b7280;
  }

  .sensor-value {
    font-size: 0.875rem;
    font-weight: 600;
    color: #1f2937;
  }

  .no-data {
    font-size: 0.75rem;
    color: #9ca3af;
    text-align: center;
    font-style: italic;
  }

  .device-actions {
    display: flex;
    gap: 0.5rem;
  }

  .action-button {
    flex: 1;
    padding: 0.5rem 1rem;
    border-radius: 0.375rem;
    font-size: 0.875rem;
    font-weight: 500;
    text-align: center;
    text-decoration: none;
    border: none;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .action-button.primary {
    background: #3b82f6;
    color: white;
  }

  .action-button.primary:hover {
    background: #2563eb;
  }

  .action-button.secondary {
    background: #f3f4f6;
    color: #374151;
    border: 1px solid #d1d5db;
  }

  .action-button.secondary:hover {
    background: #e5e7eb;
  }

  .quick-actions {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }

  .quick-action-button {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 1.5rem 1rem;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    text-decoration: none;
    color: #374151;
    transition: all 0.2s ease;
    cursor: pointer;
  }

  .quick-action-button:hover {
    background: #f3f4f6;
    border-color: #d1d5db;
    transform: translateY(-1px);
  }

  .action-icon {
    width: 2rem;
    height: 2rem;
    color: #6b7280;
  }

  .quick-action-button span {
    font-size: 0.875rem;
    font-weight: 500;
  }

  @media (max-width: 768px) {
    .dashboard {
      padding: 0.5rem;
    }

    .header {
      flex-direction: column;
      align-items: stretch;
    }

    .header-actions {
      justify-content: space-between;
    }

    .status-grid {
      grid-template-columns: 1fr;
      gap: 1rem;
    }

    .device-grid {
      grid-template-columns: 1fr;
    }

    .quick-actions {
      grid-template-columns: repeat(2, 1fr);
    }
  }
</style> 