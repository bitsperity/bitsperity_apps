<script>
  export let devices = [];
  
  const quickCommands = [
    { id: 'water_pump', name: 'Wasserpumpe', icon: '💧', color: 'blue' },
    { id: 'led_strip', name: 'Beleuchtung', icon: '💡', color: 'yellow' },
    { id: 'fan', name: 'Lüfter', icon: '🌀', color: 'green' },
    { id: 'air_pump', name: 'Luftpumpe', icon: '🫧', color: 'purple' }
  ];
  
  function executeCommand(command) {
    console.log('Executing command:', command);
    // TODO: Implement command execution
  }
</script>

<div class="space-y-4">
  <h3 class="text-lg font-semibold text-white mb-4">Schnellaktionen</h3>
  
  <div class="grid grid-cols-2 gap-3">
    {#each quickCommands as command}
      <button 
        class="glass-card p-4 rounded-xl border border-{command.color}-500/20 bg-{command.color}-500/5 
               hover:bg-{command.color}-500/10 transition-all duration-200 
               active:scale-95 touch-manipulation"
        on:click={() => executeCommand(command)}
      >
        <div class="flex flex-col items-center gap-2">
          <span class="text-2xl">{command.icon}</span>
          <span class="text-sm font-medium text-white">{command.name}</span>
        </div>
      </button>
    {/each}
  </div>
  
  <div class="mt-6">
    <h4 class="text-sm font-medium text-gray-300 mb-2">Geräte-Status</h4>
    <div class="space-y-2">
      {#if devices.length === 0}
        <p class="text-sm text-gray-500">Keine Geräte verbunden</p>
      {:else}
        {#each devices as device}
          <div class="flex items-center justify-between p-3 glass-card rounded-lg border border-gray-700/30">
            <div class="flex items-center gap-3">
              <div class="w-2 h-2 rounded-full {device.status === 'online' ? 'bg-green-500' : 'bg-red-500'}"></div>
              <span class="text-sm text-white">{device.name}</span>
            </div>
            <span class="text-xs text-gray-400 capitalize">{device.status}</span>
          </div>
        {/each}
      {/if}
    </div>
  </div>
</div>

<style>
  .glass-card {
    background: rgba(30, 30, 30, 0.95);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
  }
</style> 