<script>
  export let sensorType = '';
  export let value = 0;
  export let unit = '';
  export let status = 'ok';
  export let timestamp = '';
  export let deviceName = '';
  export let trend = [];
  
  const sensorNames = {
    'ph': 'pH-Wert',
    'temperature': 'Temperatur', 
    'humidity': 'Luftfeuchtigkeit',
    'ec': 'Leitfähigkeit',
    'water_level': 'Wasserstand',
    'light_intensity': 'Lichtintensität'
  };
  
  const sensorIcons = {
    'ph': '🧪',
    'temperature': '🌡️',
    'humidity': '💧',
    'ec': '⚡',
    'water_level': '🌊',
    'light_intensity': '💡'
  };
  
  $: displayName = sensorNames[sensorType] || sensorType;
  $: icon = sensorIcons[sensorType] || '📊';
  
  $: statusColor = {
    'ok': 'border-green-500/30 bg-green-500/5',
    'warning': 'border-yellow-500/30 bg-yellow-500/5',
    'alert': 'border-red-500/30 bg-red-500/5'
  }[status];
  
  $: valueColor = {
    'ok': 'text-green-400',
    'warning': 'text-yellow-400', 
    'alert': 'text-red-400'
  }[status];
  
  function formatTimestamp(timestamp) {
    if (!timestamp) return '';
    return new Date(timestamp).toLocaleTimeString('de-DE', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  }
</script>

<div class="glass-card border rounded-xl p-4 {statusColor} hover:scale-105 transition-all duration-200">
  <div class="flex items-center justify-between mb-3">
    <div class="flex items-center gap-2">
      <span class="text-xl">{icon}</span>
      <div>
        <h3 class="text-sm font-medium text-white">{displayName}</h3>
        {#if deviceName}
          <p class="text-xs text-gray-400">{deviceName}</p>
        {/if}
      </div>
    </div>
    {#if timestamp}
      <span class="text-xs text-gray-500">{formatTimestamp(timestamp)}</span>
    {/if}
  </div>
  
  <div class="flex items-end gap-1 mb-2">
    <span class="text-2xl font-bold {valueColor}">{value}</span>
    {#if unit}
      <span class="text-sm text-gray-400 mb-1">{unit}</span>
    {/if}
  </div>
  
  {#if trend && trend.length > 0}
    <div class="flex items-center gap-1 h-8">
      {#each trend.slice(-10) as point, i}
        <div 
          class="flex-1 bg-gray-600 rounded-sm opacity-70 transition-all duration-300"
          style="height: {Math.max(2, (point / Math.max(...trend)) * 24)}px"
        ></div>
      {/each}
    </div>
  {/if}
  
  <div class="flex items-center justify-between mt-2 pt-2 border-t border-gray-700/50">
    <span class="text-xs text-gray-500 capitalize">{status}</span>
    <button class="text-xs text-blue-400 hover:text-blue-300 transition-colors">
      Details →
    </button>
  </div>
</div>

<style>
  .glass-card {
    background: rgba(30, 30, 30, 0.95);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
  }
</style> 