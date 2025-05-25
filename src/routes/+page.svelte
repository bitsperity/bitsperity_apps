<script>
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  
  // Import real stores
  import { deviceStore, deviceCount } from '$lib/stores/device.js';
  import { notificationStore } from '$lib/stores/notification.js';
  
  // Import components
  import PageHeader from '$lib/components/ui/PageHeader.svelte';
  import StatusCard from '$lib/components/dashboard/StatusCard.svelte';
  import DeviceGrid from '$lib/components/dashboard/DeviceGrid.svelte';
  import QuickActions from '$lib/components/dashboard/QuickActions.svelte';
  import RecentActivity from '$lib/components/dashboard/RecentActivity.svelte';

  let refreshInterval;
  let lastRefresh = new Date();
  let sensorReadings = new Map(); // Will be populated with real sensor data

  onMount(async () => {
    if (browser) {
      await refreshDashboard();
      
      // Set up auto-refresh every 30 seconds
      refreshInterval = setInterval(refreshDashboard, 30000);
      
      return () => {
        if (refreshInterval) {
          clearInterval(refreshInterval);
        }
      };
    }
  });

  async function refreshDashboard() {
    try {
      await deviceStore.initialize();
      lastRefresh = new Date();
      
      notificationStore.success(
        'Dashboard aktualisiert',
        'Alle Daten wurden erfolgreich geladen'
      );
    } catch (error) {
      console.error('Dashboard refresh failed:', error);
      notificationStore.error(
        'Aktualisierung fehlgeschlagen',
        error.message
      );
    }
  }

  function handleQuickAction(event) {
    const action = event.detail;
    
    switch (action.id) {
      case 'discover_devices':
        discoverDevices();
        break;
      case 'emergency_stop':
        emergencyStop();
        break;
      case 'refresh_data':
        refreshDashboard();
        break;
      case 'system_status':
        showSystemStatus();
        break;
    }
  }

  async function discoverDevices() {
    try {
      notificationStore.info(
        'Gerätesuche gestartet',
        'Suche nach ESP32-Clients im Netzwerk...'
      );
      
      const result = await deviceStore.discoverDevices();
      
      notificationStore.success(
        'Gerätesuche abgeschlossen',
        `${result.discovered || 0} Geräte gefunden, ${result.new_devices || 0} neue Geräte hinzugefügt`
      );
    } catch (error) {
      console.error('Device discovery failed:', error);
      notificationStore.error(
        'Gerätesuche fehlgeschlagen',
        error.message
      );
    }
  }

  async function emergencyStop() {
    try {
      const response = await fetch('/api/v1/commands/emergency-stop', { 
        method: 'POST' 
      });
      
      if (response.ok) {
        notificationStore.warning(
          'Notfall-Stop aktiviert',
          'Alle Pumpen wurden gestoppt'
        );
      } else {
        throw new Error('Emergency stop failed');
      }
    } catch (error) {
      console.error('Emergency stop failed:', error);
      notificationStore.error(
        'Notfall-Stop fehlgeschlagen',
        error.message
      );
    }
  }

  function showSystemStatus() {
    notificationStore.info(
      'System-Status',
      'Detaillierte Systeminfo wird geladen...'
    );
  }

  // Reactive statements for system status
  $: systemStatus = {
    devices: $deviceCount,
    alerts: 0, // TODO: Implement alert counting
    programs: 0, // TODO: Implement program counting
    uptime: '99.9%' // TODO: Calculate actual uptime
  };
</script>

<svelte:head>
  <title>Dashboard - HomeGrow v3</title>
</svelte:head>

<div class="dashboard max-w-7xl mx-auto">
  <PageHeader 
    title="Dashboard" 
    subtitle="Übersicht über alle hydroponischen Systeme"
  >
    <div slot="actions" class="flex items-center gap-4">
      <button 
        class="btn btn-primary"
        on:click={refreshDashboard}
        disabled={$deviceStore.loading}
      >
        {#if $deviceStore.loading}
          <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        {:else}
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        {/if}
        Aktualisieren
      </button>
      
      <span class="text-sm text-gray-500 dark:text-gray-400">
        Zuletzt: {lastRefresh.toLocaleTimeString()}
      </span>
    </div>
  </PageHeader>

  <!-- System Status Cards -->
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
    <StatusCard
      title="Geräte"
      value="{systemStatus.devices.online}/{systemStatus.devices.total}"
      subtitle="Online"
      type="devices"
      trend={systemStatus.devices.online > 0 ? 'up' : 'down'}
    />
    
    <StatusCard
      title="Aktive Alerts"
      value={systemStatus.alerts}
      subtitle="Benötigen Aufmerksamkeit"
      type="alerts"
      trend={systemStatus.alerts === 0 ? 'neutral' : 'down'}
    />
    
    <StatusCard
      title="Programme"
      value={systemStatus.programs}
      subtitle="Aktiv"
      type="programs"
      trend="neutral"
    />
    
    <StatusCard
      title="System Uptime"
      value={systemStatus.uptime}
      subtitle="Verfügbarkeit"
      type="uptime"
      trend="up"
    />
  </div>

  <!-- Main Content Grid -->
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
    <!-- Device Overview -->
    <div class="lg:col-span-2">
      <div class="card">
        <div class="card-header">
          <h2 class="text-lg font-semibold">Geräte-Übersicht</h2>
        </div>
        <div class="card-body">
          <DeviceGrid 
            devices={$deviceStore.devices}
            {sensorReadings}
          />
        </div>
      </div>
    </div>

    <!-- Sidebar -->
    <div class="space-y-6">
      <!-- Quick Actions -->
      <div class="card">
        <div class="card-header">
          <h2 class="text-lg font-semibold">Schnellaktionen</h2>
        </div>
        <div class="card-body">
          <QuickActions on:action={handleQuickAction} />
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="card">
        <div class="card-header">
          <h2 class="text-lg font-semibold">Letzte Aktivitäten</h2>
        </div>
        <div class="card-body">
          <RecentActivity />
        </div>
      </div>
    </div>
  </div>

  <!-- Error Display -->
  {#if $deviceStore.error}
    <div class="mt-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
      <div class="flex items-center gap-2">
        <svg class="w-5 h-5 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
        <h3 class="font-medium text-red-800 dark:text-red-200">Fehler beim Laden der Daten</h3>
      </div>
      <p class="mt-1 text-sm text-red-700 dark:text-red-300">{$deviceStore.error}</p>
      <button 
        class="mt-2 btn btn-sm btn-danger"
        on:click={() => deviceStore.clearError()}
      >
        Fehler schließen
      </button>
    </div>
  {/if}
</div> 