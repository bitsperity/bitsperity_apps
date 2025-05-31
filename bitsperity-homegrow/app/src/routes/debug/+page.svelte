<script lang="ts">
  import { onMount } from 'svelte';
  
  let devices: any[] = [];
  let loading = false;
  let error = '';
  let apiResponse = '';

  onMount(async () => {
    await loadDevices();
  });

  async function loadDevices() {
    loading = true;
    error = '';
    
    try {
      console.log('Fetching devices...');
      const response = await fetch('/api/v1/devices');
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('API Response:', data);
      
      apiResponse = JSON.stringify(data, null, 2);
      devices = data;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Unknown error';
      console.error('Error loading devices:', err);
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>Debug - API Test</title>
</svelte:head>

<div class="p-8">
  <h1 class="text-2xl font-bold mb-4">API Debug Page</h1>
  
  <button on:click={loadDevices} class="bg-blue-500 text-white px-4 py-2 rounded mb-4">
    Reload Devices
  </button>
  
  {#if loading}
    <p class="text-blue-600">Loading devices...</p>
  {/if}
  
  {#if error}
    <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
      <strong>Error:</strong> {error}
    </div>
  {/if}
  
  <div class="mb-4">
    <h2 class="text-lg font-semibold">Device Count: {devices.length}</h2>
  </div>
  
  <div class="mb-4">
    <h2 class="text-lg font-semibold">Raw API Response:</h2>
    <pre class="bg-gray-100 p-4 rounded overflow-auto text-sm">{apiResponse}</pre>
  </div>
  
  <div>
    <h2 class="text-lg font-semibold">Parsed Devices:</h2>
    {#each devices as device}
      <div class="border p-3 rounded mb-2">
        <p><strong>Name:</strong> {device.name}</p>
        <p><strong>ID:</strong> {device.device_id || device.deviceId || 'N/A'}</p>
        <p><strong>Status:</strong> {device.status}</p>
        <p><strong>Type:</strong> {device.type}</p>
      </div>
    {/each}
  </div>
</div> 