<script>
  // Mock data for now - will be replaced with real data from API
  const activities = [
    {
      id: 1,
      type: 'sensor_reading',
      device: 'ESP32-001',
      message: 'pH-Wert: 6.5 gemessen',
      timestamp: new Date(Date.now() - 2 * 60 * 1000),
      status: 'success'
    },
    {
      id: 2,
      type: 'command',
      device: 'ESP32-001',
      message: 'Wasserpumpe für 30s aktiviert',
      timestamp: new Date(Date.now() - 5 * 60 * 1000),
      status: 'success'
    },
    {
      id: 3,
      type: 'alert',
      device: 'ESP32-002',
      message: 'TDS-Wert zu hoch (850 ppm)',
      timestamp: new Date(Date.now() - 15 * 60 * 1000),
      status: 'warning'
    },
    {
      id: 4,
      type: 'device_status',
      device: 'ESP32-002',
      message: 'Gerät online',
      timestamp: new Date(Date.now() - 30 * 60 * 1000),
      status: 'success'
    },
    {
      id: 5,
      type: 'program',
      device: 'ESP32-001',
      message: 'Wachstumsprogramm gestartet',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
      status: 'info'
    }
  ];
  
  function getIcon(type) {
    const icons = {
      sensor_reading: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
      command: 'M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4',
      alert: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z',
      device_status: 'M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z',
      program: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z'
    };
    return icons[type] || icons.device_status;
  }
  
  function getStatusColor(status) {
    const colors = {
      success: 'text-green-600 bg-green-50 dark:text-green-400 dark:bg-green-900/20',
      warning: 'text-yellow-600 bg-yellow-50 dark:text-yellow-400 dark:bg-yellow-900/20',
      error: 'text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-900/20',
      info: 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20'
    };
    return colors[status] || colors.info;
  }
  
  function formatTime(timestamp) {
    const now = new Date();
    const diffMs = now - timestamp;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Gerade eben';
    if (diffMins < 60) return `vor ${diffMins} Min`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `vor ${diffHours} Std`;
    
    return timestamp.toLocaleDateString('de-DE', { 
      day: '2-digit', 
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
</script>

{#if activities.length === 0}
  <div class="text-center py-8">
    <svg class="w-8 h-8 mx-auto text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
    <p class="text-sm text-gray-500 dark:text-gray-400">Keine Aktivitäten</p>
  </div>
{:else}
  <div class="space-y-3 max-h-80 overflow-y-auto">
    {#each activities as activity (activity.id)}
      <div class="flex items-start gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50">
        <!-- Icon -->
        <div class="flex-shrink-0 p-1.5 rounded-lg {getStatusColor(activity.status)}">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={getIcon(activity.type)} />
          </svg>
        </div>
        
        <!-- Content -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between gap-2">
            <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
              {activity.device}
            </p>
            <span class="text-xs text-gray-500 dark:text-gray-400 flex-shrink-0">
              {formatTime(activity.timestamp)}
            </span>
          </div>
          <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
            {activity.message}
          </p>
        </div>
      </div>
    {/each}
  </div>
  
  <!-- View All Button -->
  <div class="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700">
    <button class="w-full text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium">
      Alle Aktivitäten anzeigen
    </button>
  </div>
{/if} 