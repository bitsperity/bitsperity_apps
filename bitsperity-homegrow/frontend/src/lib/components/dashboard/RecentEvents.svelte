<script>
  export let events = [];
  
  const eventIcons = {
    'sensor_alert': '🚨',
    'device_offline': '📴',
    'device_online': '✅',
    'command_executed': '⚙️',
    'rule_triggered': '🔧',
    'system': 'ℹ️'
  };
  
  const eventColors = {
    'sensor_alert': 'text-red-400 border-red-500/20',
    'device_offline': 'text-orange-400 border-orange-500/20',
    'device_online': 'text-green-400 border-green-500/20',
    'command_executed': 'text-blue-400 border-blue-500/20',
    'rule_triggered': 'text-purple-400 border-purple-500/20',
    'system': 'text-gray-400 border-gray-500/20'
  };
  
  function formatTime(timestamp) {
    if (!timestamp) return '';
    const now = new Date();
    const time = new Date(timestamp);
    const diff = now - time;
    const minutes = Math.floor(diff / 60000);
    
    if (minutes < 1) return 'gerade eben';
    if (minutes < 60) return `vor ${minutes}min`;
    if (minutes < 1440) return `vor ${Math.floor(minutes / 60)}h`;
    return time.toLocaleDateString('de-DE');
  }
  
  // Mock events if none provided
  $: displayEvents = events.length > 0 ? events : [
    {
      id: 1,
      type: 'system',
      message: 'HomeGrow v3 Backend gestartet',
      timestamp: new Date(Date.now() - 5 * 60 * 1000),
      deviceName: 'System'
    },
    {
      id: 2,
      type: 'device_online',
      message: 'Test ESP32 verbunden',
      timestamp: new Date(Date.now() - 15 * 60 * 1000),
      deviceName: 'Test ESP32'
    }
  ];
</script>

<div class="space-y-4">
  <h3 class="text-lg font-semibold text-white mb-4">Letzte Ereignisse</h3>
  
  <div class="space-y-3 max-h-80 overflow-y-auto scrollbar-thin">
    {#each displayEvents.slice(0, 10) as event}
      <div class="glass-card p-3 rounded-lg border {eventColors[event.type] || eventColors.system}">
        <div class="flex items-start gap-3">
          <span class="text-lg mt-0.5">{eventIcons[event.type] || eventIcons.system}</span>
          <div class="flex-1 min-w-0">
            <p class="text-sm text-white leading-relaxed">{event.message}</p>
            <div class="flex items-center gap-2 mt-1">
              {#if event.deviceName}
                <span class="text-xs text-gray-400">{event.deviceName}</span>
                <span class="text-xs text-gray-600">•</span>
              {/if}
              <span class="text-xs text-gray-500">{formatTime(event.timestamp)}</span>
            </div>
          </div>
        </div>
      </div>
    {/each}
  </div>
  
  {#if displayEvents.length === 0}
    <div class="text-center py-8">
      <span class="text-4xl opacity-50">📝</span>
      <p class="text-sm text-gray-500 mt-2">Keine Ereignisse vorhanden</p>
    </div>
  {/if}
  
  {#if displayEvents.length > 10}
    <button class="w-full py-2 text-sm text-blue-400 hover:text-blue-300 transition-colors">
      Alle Ereignisse anzeigen →
    </button>
  {/if}
</div>

<style>
  .glass-card {
    background: rgba(30, 30, 30, 0.95);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
  }
  
  .scrollbar-thin::-webkit-scrollbar {
    width: 4px;
  }
  
  .scrollbar-thin::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
  }
  
  .scrollbar-thin::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.3);
    border-radius: 2px;
  }
  
  .scrollbar-thin::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.5);
  }
</style> 