<script>
  import { deviceCount } from '$lib/stores/device.js';
  import { goto } from '$app/navigation';
  
  export let open = false;
  export let currentPath = '/';

  const navigationItems = [
    { 
      path: '/', 
      label: 'Dashboard', 
      icon: 'home',
      description: 'Übersicht & Status'
    },
    { 
      path: '/devices', 
      label: 'Geräte', 
      icon: 'device',
      description: 'Device Management'
    },
    { 
      path: '/monitoring', 
      label: 'Monitoring', 
      icon: 'chart',
      description: 'Live Sensordaten'
    },
    { 
      path: '/programs', 
      label: 'Programme', 
      icon: 'program',
      description: 'Wachstumsprogramme'
    },
    { 
      path: '/manual', 
      label: 'Manuell', 
      icon: 'manual',
      description: 'Manuelle Steuerung'
    },
    { 
      path: '/settings', 
      label: 'Einstellungen', 
      icon: 'settings',
      description: 'System-Konfiguration'
    }
  ];

  function handleNavigation(path) {
    goto(path);
    open = false; // Close mobile navigation
  }

  function getIcon(iconName) {
    const icons = {
      home: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
      device: 'M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z',
      chart: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
      program: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z',
      manual: 'M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4',
      settings: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z'
    };
    return icons[iconName] || icons.home;
  }

  $: onlineDevices = $deviceCount.online;
  $: totalDevices = $deviceCount.total;
</script>

<!-- Mobile Navigation Overlay -->
{#if open}
  <div 
    class="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
    on:click={() => open = false}
    on:keydown={(e) => e.key === 'Escape' && (open = false)}
  ></div>
{/if}

<!-- Navigation Sidebar -->
<nav class="navigation fixed top-0 left-0 h-full w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transform transition-transform duration-300 z-50 {open ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0">
  <!-- Logo & Title -->
  <div class="nav-header p-6 border-b border-gray-200 dark:border-gray-700">
    <div class="flex items-center gap-3">
      <svg class="w-8 h-8 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
      </svg>
      <div>
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white">HomeGrow</h2>
        <span class="text-xs text-gray-500 dark:text-gray-400">v3.0</span>
      </div>
    </div>
  </div>

  <!-- System Status -->
  <div class="p-4 border-b border-gray-200 dark:border-gray-700">
    <div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
      <div class="w-2 h-2 rounded-full {onlineDevices > 0 ? 'bg-green-500' : 'bg-red-500'}"></div>
      <span>{onlineDevices}/{totalDevices} Geräte online</span>
    </div>
  </div>

  <!-- Navigation Items -->
  <ul class="nav-items flex-1 py-4">
    {#each navigationItems as item}
      <li>
        <button
          class="nav-item w-full flex items-center gap-3 px-4 py-3 text-left text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors {currentPath === item.path ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400 border-r-2 border-primary-500' : ''}"
          on:click={() => handleNavigation(item.path)}
        >
          <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={getIcon(item.icon)} />
          </svg>
          <div class="flex-1">
            <div class="font-medium text-sm">{item.label}</div>
            <div class="text-xs opacity-70">{item.description}</div>
          </div>
        </button>
      </li>
    {/each}
  </ul>

  <!-- Footer -->
  <div class="p-4 border-t border-gray-200 dark:border-gray-700">
    <div class="text-xs text-gray-500 dark:text-gray-400 space-y-1">
      <div>HomeGrow v3.0.0</div>
      <div>© 2024 Bitsperity</div>
    </div>
  </div>
</nav>

<style>
  .navigation {
    overflow-y: auto;
  }
</style> 