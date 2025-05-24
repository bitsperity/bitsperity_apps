<script>
  export let title = '';
  export let value = '';
  export let unit = '';
  export let status = 'ok'; // ok, warning, alert
  export let icon = '';
  export let trend = 0; // positive, negative, neutral
  
  $: statusClass = {
    'ok': 'bg-green-500/10 border-green-500/20 text-green-400',
    'warning': 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400', 
    'alert': 'bg-red-500/10 border-red-500/20 text-red-400'
  }[status];
  
  $: trendIcon = trend > 0 ? '↗' : trend < 0 ? '↘' : '→';
  $: trendClass = trend > 0 ? 'text-green-400' : trend < 0 ? 'text-red-400' : 'text-gray-400';
</script>

<div class="glass-card p-4 rounded-xl border {statusClass} hover:scale-105 transition-transform duration-200">
  <div class="flex items-center justify-between mb-2">
    <h3 class="text-sm font-medium text-gray-300">{title}</h3>
    {#if icon}
      <span class="text-lg">{icon}</span>
    {/if}
  </div>
  
  <div class="flex items-end gap-2">
    <span class="text-2xl font-bold text-white">{value}</span>
    {#if unit}
      <span class="text-sm text-gray-400 mb-1">{unit}</span>
    {/if}
    {#if trend !== 0}
      <span class="text-xs {trendClass} mb-1">{trendIcon}</span>
    {/if}
  </div>
  
  <div class="mt-2 h-1 bg-gray-700 rounded-full overflow-hidden">
    <div class="h-full bg-gradient-to-r from-green-500 to-blue-500 rounded-full transition-all duration-500"
         style="width: {Math.min(Math.abs(value / 100) * 100, 100)}%"></div>
  </div>
</div>

<style>
  .glass-card {
    background: rgba(30, 30, 30, 0.95);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
  }
</style> 