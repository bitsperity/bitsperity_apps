<script>
  export let devices = [];
  export let sensorReadings = new Map();
  
  function getStatusColor(status) {
    const colors = {
      online: 'bg-green-500',
      offline: 'bg-red-500',
      warning: 'bg-yellow-500',
      error: 'bg-red-600'
    };
    return colors[status] || colors.offline;
  }
  
  function getStatusText(status) {
    const texts = {
      online: 'Online',
      offline: 'Offline',
      warning: 'Warnung',
      error: 'Fehler'
    };
    return texts[status] || 'Unbekannt';
  }
  
  function formatLastSeen(lastSeen) {
    if (!lastSeen) return 'Nie';
    
    const date = new Date(lastSeen);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Gerade eben';
    if (diffMins < 60) return `vor ${diffMins} Min`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `vor ${diffHours} Std`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `vor ${diffDays} Tag${diffDays > 1 ? 'en' : ''}`;
  }
  
  function getSensorValue(deviceId, sensorType) {
    const key = `${deviceId}_${sensorType}`;
    const reading = sensorReadings.get(key);
    return reading?.values?.calibrated || null;
  }
</script>

{#if devices.length === 0}
  <div class="text-center py-12">
    <svg class="w-12 h-12 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
    </svg>
    <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">Keine Geräte gefunden</h3>
    <p class="text-gray-500 dark:text-gray-400 mb-4">Starten Sie die Geräteerkennung, um ESP32-Clients zu finden.</p>
    <button class="btn btn-primary">
      Geräte suchen
    </button>
  </div>
{:else}
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {#each devices as device (device.device_id)}
      <div class="device-card border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow">
        <!-- Device Header -->
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2">
            <div class="w-3 h-3 rounded-full {getStatusColor(device.status)}"></div>
            <h3 class="font-medium text-gray-900 dark:text-white truncate">
              {device.name || device.device_id}
            </h3>
          </div>
          <span class="text-xs px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
            {getStatusText(device.status)}
          </span>
        </div>
        
        <!-- Device Info -->
        <div class="space-y-2 mb-4">
          <div class="text-sm text-gray-600 dark:text-gray-400">
            <span class="font-medium">ID:</span> {device.device_id}
          </div>
          {#if device.location}
            <div class="text-sm text-gray-600 dark:text-gray-400">
              <span class="font-medium">Standort:</span> {device.location}
            </div>
          {/if}
          <div class="text-sm text-gray-600 dark:text-gray-400">
            <span class="font-medium">Zuletzt gesehen:</span> {formatLastSeen(device.last_seen)}
          </div>
        </div>
        
        <!-- Sensor Readings -->
        {#if device.status === 'online'}
          <div class="border-t border-gray-200 dark:border-gray-700 pt-3">
            <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Sensordaten</h4>
            <div class="grid grid-cols-2 gap-3">
              <!-- pH Value -->
              <div class="text-center">
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">pH-Wert</div>
                {#if getSensorValue(device.device_id, 'ph')}
                  <div class="text-lg font-semibold text-blue-600 dark:text-blue-400">
                    {getSensorValue(device.device_id, 'ph').toFixed(1)}
                  </div>
                {:else}
                  <div class="text-sm text-gray-400">--</div>
                {/if}
              </div>
              
              <!-- TDS Value -->
              <div class="text-center">
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">TDS (ppm)</div>
                {#if getSensorValue(device.device_id, 'tds')}
                  <div class="text-lg font-semibold text-green-600 dark:text-green-400">
                    {Math.round(getSensorValue(device.device_id, 'tds'))}
                  </div>
                {:else}
                  <div class="text-sm text-gray-400">--</div>
                {/if}
              </div>
            </div>
          </div>
        {/if}
        
        <!-- Actions -->
        <div class="border-t border-gray-200 dark:border-gray-700 pt-3 mt-3">
          <div class="flex gap-2">
            <button class="btn btn-sm btn-secondary flex-1">
              Details
            </button>
            {#if device.status === 'online'}
              <button class="btn btn-sm btn-primary flex-1">
                Steuern
              </button>
            {/if}
          </div>
        </div>
      </div>
    {/each}
  </div>
{/if} 