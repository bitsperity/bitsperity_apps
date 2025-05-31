<script lang="ts">
  import '../app.css';
  
  // Import stores and services
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  
  // Initialize the app when mounted
  onMount(() => {
    if (browser) {
      console.log('HomeGrow v3 - System starting...');
    }
  });
</script>

<main class="min-h-screen bg-gray-50">
  <slot />
</main>

<style>
  /* Additional global styles if needed */
</style> 