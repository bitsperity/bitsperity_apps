<script>
  import '../app.css';
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { browser } from '$app/environment';
  
  // Import stores (will be created)
  import { themeStore } from '$lib/stores/theme.js';
  import { deviceStore } from '$lib/stores/device.js';
  import { notificationStore } from '$lib/stores/notification.js';
  
  // Import components (will be created)
  import Navigation from '$lib/components/Navigation.svelte';
  import NotificationToast from '$lib/components/ui/NotificationToast.svelte';
  import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';

  let isLoading = true;
  let navigationOpen = false;

  onMount(async () => {
    if (browser) {
      // Initialize theme
      themeStore.initialize();
      
      // Initialize device store
      await deviceStore.initialize();
      
      // Register service worker for PWA
      if ('serviceWorker' in navigator) {
        try {
          await navigator.serviceWorker.register('/service-worker.js');
          console.log('Service Worker registered');
        } catch (error) {
          console.error('Service Worker registration failed:', error);
        }
      }

      isLoading = false;
    }
  });

  $: currentPath = $page.url.pathname;
  $: isDark = $themeStore?.isDark || false;
</script>

<svelte:head>
  <title>HomeGrow v3 - Hydroponic Management</title>
  <meta name="description" content="Professional hydroponic system management with real-time monitoring and automation" />
</svelte:head>

<div class="app" class:dark={isDark}>
  {#if isLoading}
    <div class="loading-screen">
      <LoadingSpinner size="large" />
      <p class="mt-4 text-gray-600 dark:text-gray-400">HomeGrow wird geladen...</p>
    </div>
  {:else}
    <div class="app-layout">
      <!-- Mobile Header -->
      <header class="mobile-header md:hidden bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <button 
          class="menu-button p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
          on:click={() => navigationOpen = !navigationOpen}
          aria-label="Navigation öffnen"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        
        <h1 class="app-title text-xl font-semibold text-gray-900 dark:text-white">HomeGrow v3</h1>
        
        <button 
          class="theme-toggle p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
          on:click={themeStore.toggle}
          aria-label="Theme wechseln"
        >
          {#if isDark}
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          {:else}
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          {/if}
        </button>
      </header>

      <!-- Navigation -->
      <Navigation bind:open={navigationOpen} {currentPath} />

      <!-- Main Content -->
      <main class="main-content flex-1 p-4 md:p-6 md:ml-64">
        <slot />
      </main>

      <!-- Notification Toasts -->
      <NotificationToast />
    </div>
  {/if}
</div>

<style>
  .app {
    min-height: 100vh;
    background: var(--bg-primary);
    color: var(--text-primary);
    transition: background-color 0.2s ease;
  }

  .loading-screen {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
  }

  .app-layout {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }

  .mobile-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem;
    position: sticky;
    top: 0;
    z-index: 40;
  }

  .main-content {
    max-width: 100%;
    overflow-x: hidden;
  }

  @media (min-width: 768px) {
    .app-layout {
      flex-direction: row;
    }
  }
</style> 