<script>
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  
  // Import stores (placeholders for now)
  let deviceStore = { devices: [], loading: false };
  let sensorStore = { latestReadings: new Map() };
  
  // Import components (placeholders for now)
  import PageHeader from '$lib/components/ui/PageHeader.svelte';
  import StatusCard from '$lib/components/dashboard/StatusCard.svelte';
  import DeviceGrid from '$lib/components/dashboard/DeviceGrid.svelte';
  import QuickActions from '$lib/components/dashboard/QuickActions.svelte';
  import RecentActivity from '$lib/components/dashboard/RecentActivity.svelte';

  let refreshInterval;
  let lastRefresh = new Date();
  let systemStatus = {
    devices: { total: 0, online: 0, offline: 0 },
    alerts: 0,
    programs: 0,
    uptime: '99.9%'
  };

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
      // Fetch device data
      const response = await fetch('/api/v1/devices');
      if (response.ok) {
        const data = await response.json();
        deviceStore.devices = data.data || [];
        
        // Update system status
        systemStatus.devices = {
          total: deviceStore.devices.length,
          online: deviceStore.devices.filter(d => d.status === 'online').length,
          offline: deviceStore.devices.filter(d => d.status === 'offline').length
        };
      }
      
      lastRefresh = new Date();
    } catch (error) {
      console.error('Dashboard refresh failed:', error);
    }
  }

  function handleQuickAction(action) {
    switch (action.type) {
      case 'discover_devices':
        discoverDevices();
        break;
      case 'emergency_stop':
        emergencyStop();
        break;
      case 'refresh_data':
        refreshDashboard();
        break;
    }
  }

  async function discoverDevices() {
    try {
      const response = await fetch('/api/v1/devices/discover', { method: 'POST' });
      if (response.ok) {
        await refreshDashboard();
      }
    } catch (error) {
      console.error('Device discovery failed:', error);
    }
  }

  async function emergencyStop() {
    try {
      const response = await fetch('/api/v1/commands/emergency-stop', { method: 'POST' });
      if (response.ok) {
        console.log('Emergency stop activated');
      }
    } catch (error) {
      console.error('Emergency stop failed:', error);
    }
  }
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
        disabled={deviceStore.loading}
      >
        {#if deviceStore.loading}
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
            devices={deviceStore.devices}
            sensorReadings={sensorStore.latestReadings}
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
          <QuickActions on:action={e => handleQuickAction(e.detail)} />
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
</div>

<style>
  .dashboard {
    animation: fadeIn 0.5s ease-in-out;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
</style> 