<script>
  import { onMount } from 'svelte';
  import { deviceStore, onlineDevices, offlineDevices } from '$lib/stores/deviceStore.js';
  import { sensorStore, allLatestReadings } from '$lib/stores/sensorStore.js';
  import { showSuccess, showError, showDeviceConnected } from '$lib/stores/notification.js';
  import DeviceCard from '$lib/components/device/DeviceCard.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';

  let searchTerm = '';
  let statusFilter = 'all'; // all, online, offline
  let loading = false;
  let discoveryInProgress = false;

  onMount(async () => {
    await loadDevices();
  });

  async function loadDevices() {
    loading = true;
    try {
      await deviceStore.initialize();
      
      // Lade aktuelle Sensordaten für alle Online-Geräte
      const promises = $onlineDevices.map(device => 
        sensorStore.getLatestReadings(device.device_id)
      );
      await Promise.all(promises);
      
    } catch (error) {
      console.error('Failed to load devices:', error);
      showError('Fehler beim Laden der Geräte');
    } finally {
      loading = false;
    }
  }

  async function handleDiscoverDevices() {
    discoveryInProgress = true;
    try {
      await deviceStore.discoverDevices();
      showSuccess('Geräte-Suche gestartet');
      
      // Warte kurz und lade dann die Geräte neu
      setTimeout(async () => {
        await loadDevices();
        discoveryInProgress = false;
      }, 3000);
      
    } catch (error) {
      showError('Fehler bei der Geräte-Suche: ' + error.message);
      discoveryInProgress = false;
    }
  }

  async function handleRefresh() {
    await loadDevices();
    showSuccess('Geräteliste aktualisiert');
  }

  function handleDeviceAction(event) {
    const { type, detail } = event;
    
    switch (type) {
      case 'view-details':
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

  // Gefilterte Geräte basierend auf Suchterm und Status
  $: filteredDevices = (() => {
    let devices = [];
    
    switch (statusFilter) {
      case 'online':
        devices = $onlineDevices;
        break;
      case 'offline':
        devices = $offlineDevices;
        break;
      default:
        devices = [...$onlineDevices, ...$offlineDevices];
    }

    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      devices = devices.filter(device => 
        device.name.toLowerCase().includes(term) ||
        device.device_id.toLowerCase().includes(term) ||
        (device.location && device.location.toLowerCase().includes(term))
      );
    }

    return devices;
  })();

  $: deviceStats = {
    total: $onlineDevices.length + $offlineDevices.length,
    online: $onlineDevices.length,
    offline: $offlineDevices.length
  };
</script>

<svelte:head>
  <title>Geräte - HomeGrow v3</title>
</svelte:head>

<div class="devices-page">
  <!-- Header -->
  <div class="page-header">
    <div class="header-content">
      <h1 class="page-title">Geräte</h1>
      <p class="page-subtitle">Verwaltung aller HomeGrow-Geräte</p>
    </div>
    
    <div class="header-actions">
      <Button 
        variant="secondary" 
        size="sm" 
        on:click={handleRefresh}
        loading={loading}
      >
        Aktualisieren
      </Button>
      
      <Button 
        variant="primary" 
        size="sm" 
        on:click={handleDiscoverDevices}
        loading={discoveryInProgress}
      >
        Geräte suchen
      </Button>
    </div>
  </div>

  <!-- Stats Cards -->
  <div class="stats-grid">
    <Card padding="md">
      <div class="stat-card">
        <div class="stat-icon total">📱</div>
        <div class="stat-content">
          <div class="stat-value">{deviceStats.total}</div>
          <div class="stat-label">Geräte gesamt</div>
        </div>
      </div>
    </Card>
    
    <Card padding="md">
      <div class="stat-card">
        <div class="stat-icon online">🟢</div>
        <div class="stat-content">
          <div class="stat-value">{deviceStats.online}</div>
          <div class="stat-label">Online</div>
        </div>
      </div>
    </Card>
    
    <Card padding="md">
      <div class="stat-card">
        <div class="stat-icon offline">🔴</div>
        <div class="stat-content">
          <div class="stat-value">{deviceStats.offline}</div>
          <div class="stat-label">Offline</div>
        </div>
      </div>
    </Card>
  </div>

  <!-- Filters and Search -->
  <Card title="Filter & Suche" padding="md">
    <div class="filters-container">
      <div class="search-group">
        <label for="search">Suche:</label>
        <input 
          id="search"
          type="text" 
          placeholder="Name, ID oder Standort..."
          bind:value={searchTerm}
          class="search-input"
        />
      </div>
      
      <div class="filter-group">
        <label for="status-filter">Status:</label>
        <select 
          id="status-filter"
          bind:value={statusFilter}
          class="filter-select"
        >
          <option value="all">Alle</option>
          <option value="online">Online ({deviceStats.online})</option>
          <option value="offline">Offline ({deviceStats.offline})</option>
        </select>
      </div>
    </div>
  </Card>

  <!-- Device List -->
  <div class="devices-section">
    {#if loading}
      <Card padding="lg">
        <LoadingSpinner size="lg" text="Lade Geräte..." centered />
      </Card>
    {:else if filteredDevices.length === 0}
      <Card padding="lg">
        <div class="no-devices">
          {#if deviceStats.total === 0}
            <div class="no-devices-icon">📱</div>
            <h3>Keine Geräte gefunden</h3>
            <p>Es sind noch keine HomeGrow-Geräte registriert.</p>
            <Button 
              variant="primary" 
              on:click={handleDiscoverDevices}
              loading={discoveryInProgress}
            >
              Erste Geräte-Suche starten
            </Button>
          {:else}
            <div class="no-devices-icon">🔍</div>
            <h3>Keine Geräte gefunden</h3>
            <p>Keine Geräte entsprechen den aktuellen Filterkriterien.</p>
            <Button variant="secondary" on:click={() => { searchTerm = ''; statusFilter = 'all'; }}>
              Filter zurücksetzen
            </Button>
          {/if}
        </div>
      </Card>
    {:else}
      <div class="devices-grid">
        {#each filteredDevices as device (device.device_id)}
          <DeviceCard 
            {device}
            sensorReadings={$allLatestReadings[device.device_id] || {}}
            showActions={true}
            on:view-details={(e) => handleDeviceAction({ type: 'view-details', detail: e.detail })}
            on:emergency-stop={(e) => handleDeviceAction({ type: 'emergency-stop', detail: e.detail })}
            on:send-command={(e) => handleDeviceAction({ type: 'send-command', detail: e.detail })}
          />
        {/each}
      </div>
    {/if}
  </div>

  <!-- Discovery Status -->
  {#if discoveryInProgress}
    <Card padding="md">
      <div class="discovery-status">
        <LoadingSpinner size="sm" />
        <div class="discovery-text">
          <h4>Suche nach Geräten...</h4>
          <p>Durchsuche das Netzwerk nach neuen HomeGrow-Geräten. Dies kann einige Sekunden dauern.</p>
        </div>
      </div>
    </Card>
  {/if}
</div>

<style>
  .devices-page {
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
    flex-wrap: wrap;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }

  .stat-card {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .stat-icon {
    font-size: 2rem;
    width: 3rem;
    height: 3rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 0.75rem;
  }

  .stat-icon.total {
    background: #dbeafe;
  }

  .stat-icon.online {
    background: #d1fae5;
  }

  .stat-icon.offline {
    background: #fee2e2;
  }

  .stat-content {
    flex: 1;
  }

  .stat-value {
    font-size: 1.875rem;
    font-weight: 700;
    color: #1f2937;
    line-height: 1;
  }

  .stat-label {
    font-size: 0.875rem;
    color: #6b7280;
    margin-top: 0.25rem;
  }

  .filters-container {
    display: flex;
    gap: 2rem;
    flex-wrap: wrap;
    align-items: end;
  }

  .search-group,
  .filter-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    min-width: 200px;
  }

  .search-group label,
  .filter-group label {
    font-size: 0.875rem;
    font-weight: 500;
    color: #374151;
  }

  .search-input,
  .filter-select {
    padding: 0.5rem;
    border: 1px solid #d1d5db;
    border-radius: 0.375rem;
    background: white;
    font-size: 0.875rem;
    color: #1f2937;
  }

  .search-input:focus,
  .filter-select:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 1px #3b82f6;
  }

  .search-input::placeholder {
    color: #9ca3af;
  }

  .devices-section {
    min-height: 400px;
  }

  .devices-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 1.5rem;
  }

  .no-devices {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 3rem 1rem;
  }

  .no-devices-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
    opacity: 0.5;
  }

  .no-devices h3 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0 0 0.5rem 0;
  }

  .no-devices p {
    color: #6b7280;
    margin: 0 0 1.5rem 0;
    max-width: 400px;
  }

  .discovery-status {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .discovery-text {
    flex: 1;
  }

  .discovery-text h4 {
    font-size: 1rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0 0 0.25rem 0;
  }

  .discovery-text p {
    font-size: 0.875rem;
    color: #6b7280;
    margin: 0;
  }

  @media (max-width: 768px) {
    .devices-page {
      padding: 0.5rem;
    }

    .page-header {
      flex-direction: column;
      align-items: stretch;
    }

    .header-actions {
      justify-content: space-between;
    }

    .stats-grid {
      grid-template-columns: 1fr;
    }

    .filters-container {
      flex-direction: column;
      gap: 1rem;
    }

    .search-group,
    .filter-group {
      min-width: auto;
    }

    .devices-grid {
      grid-template-columns: 1fr;
    }

    .discovery-status {
      flex-direction: column;
      text-align: center;
      gap: 0.5rem;
    }
  }
</style> 