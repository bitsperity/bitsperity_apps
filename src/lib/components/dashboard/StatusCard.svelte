<script>
  export let title;
  export let value;
  export let subtitle = '';
  export let type = 'default'; // 'devices', 'alerts', 'programs', 'uptime', 'default'
  export let trend = 'neutral'; // 'up', 'down', 'neutral'
  
  function getIcon(type) {
    const icons = {
      devices: 'M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z',
      alerts: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z',
      programs: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z',
      uptime: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
      default: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
    };
    return icons[type] || icons.default;
  }
  
  function getColors(type) {
    const colors = {
      devices: 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20',
      alerts: 'text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-900/20',
      programs: 'text-green-600 bg-green-50 dark:text-green-400 dark:bg-green-900/20',
      uptime: 'text-purple-600 bg-purple-50 dark:text-purple-400 dark:bg-purple-900/20',
      default: 'text-gray-600 bg-gray-50 dark:text-gray-400 dark:bg-gray-900/20'
    };
    return colors[type] || colors.default;
  }
  
  function getTrendIcon(trend) {
    const icons = {
      up: 'M7 14l3-3 3 3 5-5',
      down: 'M17 10l-3 3-3-3-5 5',
      neutral: 'M5 12h14'
    };
    return icons[trend] || icons.neutral;
  }
  
  function getTrendColor(trend) {
    const colors = {
      up: 'text-green-500',
      down: 'text-red-500',
      neutral: 'text-gray-400'
    };
    return colors[trend] || colors.neutral;
  }
</script>

<div class="card p-6">
  <div class="flex items-center justify-between">
    <div class="flex-1">
      <div class="flex items-center gap-3 mb-2">
        <div class="p-2 rounded-lg {getColors(type)}">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={getIcon(type)} />
          </svg>
        </div>
        <h3 class="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</h3>
      </div>
      
      <div class="mb-1">
        <span class="text-2xl font-bold text-gray-900 dark:text-white">{value}</span>
      </div>
      
      {#if subtitle}
        <p class="text-sm text-gray-500 dark:text-gray-400">{subtitle}</p>
      {/if}
    </div>
    
    <div class="flex-shrink-0 ml-4">
      <svg class="w-5 h-5 {getTrendColor(trend)}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={getTrendIcon(trend)} />
      </svg>
    </div>
  </div>
</div> 