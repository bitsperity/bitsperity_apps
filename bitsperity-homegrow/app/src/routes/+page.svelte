<script lang="ts">
  import { onMount } from 'svelte';
  import { devices, deviceStats, deviceActions } from '$lib/stores/devices.js';
  import { currentSensorData, sensorActions } from '$lib/stores/sensors.js';
  
  // Load data on mount
  onMount(async () => {
    await deviceActions.loadDevices();
    await sensorActions.loadCurrentSensorData();
  });
  
  // Reactive statements for computed values
  $: totalDevices = $deviceStats.total;
  $: onlineDevices = $deviceStats.online;
  $: offlineDevices = $deviceStats.offline;
  $: errorDevices = $deviceStats.error;
</script>

<svelte:head>
  <title>HomeGrow v3 - Dashboard</title>
</svelte:head>

<div class="min-h-screen bg-gray-50">
  <!-- Header -->
  <header class="bg-white shadow-sm border-b border-gray-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-16">
        <div class="flex items-center">
          <h1 class="text-2xl font-bold text-gray-900">HomeGrow v3</h1>
          <span class="ml-3 px-2 py-1 text-xs font-medium bg-primary-100 text-primary-800 rounded-full">
            Dashboard
          </span>
        </div>
        <div class="flex items-center space-x-4">
          <div class="text-sm text-gray-500">
            Last updated: {new Date().toLocaleTimeString()}
          </div>
          <div class="w-3 h-3 bg-success-500 rounded-full" title="System Online"></div>
        </div>
      </div>
    </div>
  </header>

  <!-- Main Content -->
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Stats Overview -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div class="card">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <div class="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"></path>
              </svg>
            </div>
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-500">Total Devices</p>
            <p class="text-2xl font-semibold text-gray-900">{totalDevices}</p>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <div class="w-8 h-8 bg-success-500 rounded-lg flex items-center justify-center">
              <div class="w-3 h-3 bg-white rounded-full"></div>
            </div>
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-500">Online</p>
            <p class="text-2xl font-semibold text-success-600">{onlineDevices}</p>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <div class="w-8 h-8 bg-gray-400 rounded-lg flex items-center justify-center">
              <div class="w-3 h-3 bg-white rounded-full"></div>
            </div>
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-500">Offline</p>
            <p class="text-2xl font-semibold text-gray-600">{offlineDevices}</p>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <div class="w-8 h-8 bg-error-500 rounded-lg flex items-center justify-center">
              <div class="w-3 h-3 bg-white rounded-full"></div>
            </div>
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-500">Errors</p>
            <p class="text-2xl font-semibold text-error-600">{errorDevices}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Devices Grid -->
    <div class="mb-8">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-lg font-medium text-gray-900">Devices</h2>
        <button class="btn-primary">
          Add Device
        </button>
      </div>

      {#if $devices.length === 0}
        <div class="card text-center py-12">
          <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"></path>
          </svg>
          <h3 class="mt-2 text-sm font-medium text-gray-900">No devices</h3>
          <p class="mt-1 text-sm text-gray-500">Get started by adding your first hydroponic device.</p>
          <div class="mt-6">
            <button class="btn-primary">
              Add your first device
            </button>
          </div>
        </div>
      {:else}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {#each $devices as device (device._id)}
            <div class="card hover:shadow-lg transition-shadow">
              <!-- Device Header -->
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold text-gray-900">{device.name}</h3>
                <div class="flex items-center space-x-2">
                  <div class="status-{device.status}"></div>
                  <span class="text-sm text-gray-500 capitalize">{device.status}</span>
                </div>
              </div>

              <!-- Device Info -->
              <div class="space-y-2 text-sm text-gray-600 mb-4">
                <div><strong>Type:</strong> {device.type}</div>
                <div><strong>ID:</strong> {device.device_id}</div>
                {#if device.location}
                  <div><strong>Location:</strong> {device.location}</div>
                {/if}
                <div><strong>Last Seen:</strong> 
                  {device.last_seen ? new Date(device.last_seen).toLocaleString() : 'Never'}
                </div>
              </div>

              <!-- Sensor Data -->
              {#if device.status === 'online'}
                {@const deviceSensors = $currentSensorData.find(d => d.device_id === device.device_id)}
                {#if deviceSensors}
                  <div class="border-t pt-4">
                    <h4 class="text-sm font-medium text-gray-900 mb-3">Current Readings</h4>
                    <div class="grid grid-cols-2 gap-3">
                      {#if deviceSensors.ph}
                        <div class="text-center">
                          <div class="text-lg font-semibold text-gray-900">{deviceSensors.ph.value.toFixed(1)}</div>
                          <div class="text-xs text-gray-500">pH</div>
                          <div class="w-2 h-2 bg-{deviceSensors.ph.quality === 'excellent' ? 'success' : deviceSensors.ph.quality === 'good' ? 'primary' : deviceSensors.ph.quality === 'fair' ? 'warning' : 'error'}-500 rounded-full mx-auto mt-1"></div>
                        </div>
                      {/if}
                      {#if deviceSensors.tds}
                        <div class="text-center">
                          <div class="text-lg font-semibold text-gray-900">{deviceSensors.tds.value.toFixed(0)}</div>
                          <div class="text-xs text-gray-500">TDS (ppm)</div>
                          <div class="w-2 h-2 bg-{deviceSensors.tds.quality === 'excellent' ? 'success' : deviceSensors.tds.quality === 'good' ? 'primary' : deviceSensors.tds.quality === 'fair' ? 'warning' : 'error'}-500 rounded-full mx-auto mt-1"></div>
                        </div>
                      {/if}
                      {#if deviceSensors.temperature}
                        <div class="text-center">
                          <div class="text-lg font-semibold text-gray-900">{deviceSensors.temperature.value.toFixed(1)}°C</div>
                          <div class="text-xs text-gray-500">Temperature</div>
                          <div class="w-2 h-2 bg-{deviceSensors.temperature.quality === 'excellent' ? 'success' : deviceSensors.temperature.quality === 'good' ? 'primary' : deviceSensors.temperature.quality === 'fair' ? 'warning' : 'error'}-500 rounded-full mx-auto mt-1"></div>
                        </div>
                      {/if}
                      {#if deviceSensors.water_level}
                        <div class="text-center">
                          <div class="text-lg font-semibold text-gray-900">{deviceSensors.water_level.value.toFixed(0)}%</div>
                          <div class="text-xs text-gray-500">Water Level</div>
                          <div class="w-2 h-2 bg-{deviceSensors.water_level.quality === 'excellent' ? 'success' : deviceSensors.water_level.quality === 'good' ? 'primary' : deviceSensors.water_level.quality === 'fair' ? 'warning' : 'error'}-500 rounded-full mx-auto mt-1"></div>
                        </div>
                      {/if}
                    </div>
                  </div>
                {/if}
              {/if}

              <!-- Actions -->
              <div class="mt-4 flex space-x-2">
                <button class="btn-primary flex-1">
                  Configure
                </button>
                <button class="btn-secondary flex-1">
                  View Details
                </button>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </main>
</div>
