<script>
  import { notificationStore } from '$lib/stores/notification.js';
  import { fly } from 'svelte/transition';
  
  function getIcon(type) {
    const icons = {
      success: 'M5 13l4 4L19 7',
      error: 'M6 18L18 6M6 6l12 12',
      warning: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z',
      info: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
    };
    return icons[type] || icons.info;
  }
  
  function getColors(type) {
    const colors = {
      success: 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900/20 dark:border-green-800 dark:text-green-200',
      error: 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900/20 dark:border-red-800 dark:text-red-200',
      warning: 'bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-900/20 dark:border-yellow-800 dark:text-yellow-200',
      info: 'bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900/20 dark:border-blue-800 dark:text-blue-200'
    };
    return colors[type] || colors.info;
  }
</script>

<div class="toast-container fixed top-4 right-4 z-50 space-y-2">
  {#each $notificationStore as notification (notification.id)}
    <div
      class="toast max-w-sm w-full border rounded-lg shadow-lg p-4 {getColors(notification.type)}"
      transition:fly={{ x: 300, duration: 300 }}
    >
      <div class="flex items-start gap-3">
        <!-- Icon -->
        <div class="flex-shrink-0 mt-0.5">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={getIcon(notification.type)} />
          </svg>
        </div>
        
        <!-- Content -->
        <div class="flex-1 min-w-0">
          {#if notification.title}
            <h4 class="font-medium text-sm mb-1">{notification.title}</h4>
          {/if}
          {#if notification.message}
            <p class="text-sm opacity-90">{notification.message}</p>
          {/if}
        </div>
        
        <!-- Dismiss Button -->
        {#if notification.dismissible}
          <button
            class="flex-shrink-0 ml-2 opacity-70 hover:opacity-100 transition-opacity"
            on:click={() => notificationStore.remove(notification.id)}
            aria-label="Dismiss notification"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        {/if}
      </div>
      
      <!-- Progress bar for auto-dismiss -->
      {#if notification.duration > 0}
        <div class="mt-3 h-1 bg-black bg-opacity-10 rounded-full overflow-hidden">
          <div 
            class="h-full bg-current opacity-50 rounded-full animate-progress"
            style="animation-duration: {notification.duration}ms"
          ></div>
        </div>
      {/if}
    </div>
  {/each}
</div>

<style>
  @keyframes progress {
    from { width: 100%; }
    to { width: 0%; }
  }
  
  .animate-progress {
    animation: progress linear forwards;
  }
  
  .toast-container {
    pointer-events: none;
  }
  
  .toast {
    pointer-events: auto;
  }
</style> 