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
  import ToastContainer from '$lib/components/ui/ToastContainer.svelte';

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

  function toggleNavigation() {
    navigationOpen = !navigationOpen;
  }

  function closeNavigation() {
    navigationOpen = false;
  }

  // Schließe Navigation bei Route-Wechsel auf Mobile
  $: if ($page.url.pathname) {
    navigationOpen = false;
  }
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
      <!-- Mobile Menu Button -->
      <button 
        class="mobile-menu-button md:hidden"
        on:click={toggleNavigation}
        aria-label="Navigation öffnen"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <!-- Navigation -->
      <Navigation 
        bind:open={navigationOpen} 
        currentPath={$page.url.pathname}
      />

      <!-- Main Content -->
      <main class="main-content" class:shifted={navigationOpen}>
        <slot />
      </main>

      <!-- Notification Toasts -->
      <NotificationToast />

      <!-- Toast Container -->
      <ToastContainer />
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
    min-height: 100vh;
    background: #f9fafb;
  }

  .mobile-menu-button {
    position: fixed;
    top: 1rem;
    left: 1rem;
    z-index: 60;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    padding: 0.5rem;
    color: #6b7280;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    transition: all 0.2s ease;
  }

  .mobile-menu-button:hover {
    background: #f9fafb;
    color: #374151;
  }

  .main-content {
    flex: 1;
    transition: margin-left 0.3s ease;
    min-width: 0; /* Prevent flex item from overflowing */
  }

  @media (min-width: 768px) {
    .main-content {
      margin-left: 16rem; /* Width of navigation */
    }
    
    .mobile-menu-button {
      display: none;
    }
  }

  @media (max-width: 767px) {
    .main-content.shifted {
      margin-left: 0;
    }
  }

  /* Dark mode support */
  :global(.dark) .app-layout {
    background: #111827;
  }

  :global(.dark) .mobile-menu-button {
    background: #1f2937;
    border-color: #374151;
    color: #9ca3af;
  }

  :global(.dark) .mobile-menu-button:hover {
    background: #374151;
    color: #d1d5db;
  }
</style> 