<script>
  import { createEventDispatcher } from 'svelte';
  
  const dispatch = createEventDispatcher();
  
  const actions = [
    {
      id: 'discover_devices',
      title: 'Geräte suchen',
      description: 'ESP32-Clients automatisch erkennen',
      icon: 'search',
      color: 'blue'
    },
    {
      id: 'emergency_stop',
      title: 'Notfall-Stop',
      description: 'Alle Pumpen sofort stoppen',
      icon: 'stop',
      color: 'red'
    },
    {
      id: 'refresh_data',
      title: 'Daten aktualisieren',
      description: 'Sensordaten neu laden',
      icon: 'refresh',
      color: 'green'
    },
    {
      id: 'system_status',
      title: 'System-Status',
      description: 'Detaillierte Systeminfo',
      icon: 'info',
      color: 'gray'
    }
  ];
  
  function getIcon(iconName) {
    const icons = {
      search: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
      stop: 'M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z',
      refresh: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15',
      info: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
    };
    return icons[iconName] || icons.info;
  }
  
  function getColors(color) {
    const colors = {
      blue: 'text-blue-600 bg-blue-50 hover:bg-blue-100 dark:text-blue-400 dark:bg-blue-900/20 dark:hover:bg-blue-900/30',
      red: 'text-red-600 bg-red-50 hover:bg-red-100 dark:text-red-400 dark:bg-red-900/20 dark:hover:bg-red-900/30',
      green: 'text-green-600 bg-green-50 hover:bg-green-100 dark:text-green-400 dark:bg-green-900/20 dark:hover:bg-green-900/30',
      gray: 'text-gray-600 bg-gray-50 hover:bg-gray-100 dark:text-gray-400 dark:bg-gray-900/20 dark:hover:bg-gray-900/30'
    };
    return colors[color] || colors.gray;
  }
  
  function handleAction(action) {
    dispatch('action', action);
  }
</script>

<div class="space-y-3">
  {#each actions as action}
    <button
      class="w-full p-4 rounded-lg border border-gray-200 dark:border-gray-700 transition-all duration-200 {getColors(action.color)}"
      on:click={() => handleAction(action)}
    >
      <div class="flex items-center gap-3">
        <div class="flex-shrink-0">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={getIcon(action.icon)} />
          </svg>
        </div>
        <div class="flex-1 text-left">
          <h3 class="font-medium text-sm">{action.title}</h3>
          <p class="text-xs opacity-75 mt-1">{action.description}</p>
        </div>
        <div class="flex-shrink-0">
          <svg class="w-4 h-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </div>
    </button>
  {/each}
</div> 