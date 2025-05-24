<script>
	import '../app.css';
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { browser } from '$app/environment';
	import BottomNavigation from '$lib/components/layout/BottomNavigation.svelte';
	import StatusBar from '$lib/components/layout/StatusBar.svelte';
	import Toast from '$lib/components/ui/Toast.svelte';
	
	// Import all stores
	import { userActions, isAuthenticated as userAuthenticated, isLoading as userLoading } from '$lib/stores/user.js';
	import { deviceActions } from '$lib/stores/device.js';
	import { sensorActions } from '$lib/stores/sensor.js';
	import { rulesActions } from '$lib/stores/rules.js';
	import { uiActions, theme, isOnline } from '$lib/stores/ui.js';

	let cleanup;

	let hasInitialChecked = false;

	// Check authentication on mount
	onMount(async () => {
		if (browser) {
			// Initialize UI
			cleanup = uiActions.init();
			
			// Skip auth check for now
			// await userActions.checkAuth();
			hasInitialChecked = true;
		}
	});

	// Disable reactive data loading for now
	// $: if (browser && hasInitialChecked && $userAuthenticated) {
	// 	loadInitialData();
	// }

	async function loadInitialData() {
		try {
			await Promise.all([
				deviceActions.loadDevices(),
				sensorActions.loadSensorData(),
				rulesActions.loadRules()
			]);
		} catch (error) {
			console.error('Error loading initial data:', error);
			uiActions.addNotification({
				type: 'error',
				title: 'Fehler',
				message: 'Fehler beim Laden der Daten',
				timeout: 5000
			});
		}
	}

	onDestroy(() => {
		if (cleanup) cleanup();
	});

	// Check if current route requires authentication
	$: requiresAuth = false; // Temporarily disable auth for testing
	$: shouldRedirect = false; // Disable auto-redirect

	// Auto-redirect to login if not authenticated
	$: if (shouldRedirect) {
		window.location.href = '/auth/login';
	}
</script>

<svelte:head>
	<title>HomeGrow v3</title>
	<meta name="description" content="Professional hydroponic monitoring and automation system" />
</svelte:head>

{#if $userLoading}
	<div class="min-h-screen bg-homegrow-50 dark:bg-gray-900 flex items-center justify-center">
		<div class="text-center">
			<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-homegrow-600 mx-auto mb-4"></div>
			<p class="text-homegrow-700 dark:text-homegrow-300 font-medium">HomeGrow wird geladen...</p>
		</div>
	</div>
{:else}
	<!-- App Layout (temporary without auth) -->
	<div class="min-h-screen bg-gray-50 dark:bg-gray-900 pb-safe" data-theme={$theme}>
		<!-- Status Bar -->
		<StatusBar />
		
		<!-- Main Content -->
		<main class="pb-20 pt-safe">
			<slot />
		</main>
		
		<!-- Bottom Navigation -->
		<BottomNavigation />
		
		<!-- Offline Indicator -->
		{#if !$isOnline}
			<div class="fixed top-0 left-0 right-0 bg-red-500 text-white text-center py-2 text-sm z-50">
				Keine Internetverbindung
			</div>
		{/if}
	</div>
{/if}

<!-- Global Toast Notifications -->
<Toast />

<style>
	:global(html) {
		/* iOS safe area support */
		padding-top: env(safe-area-inset-top);
		padding-bottom: env(safe-area-inset-bottom);
	}
	
	.pt-safe {
		padding-top: max(1rem, env(safe-area-inset-top));
	}
	
	.pb-safe {
		padding-bottom: max(0, env(safe-area-inset-bottom));
	}
</style> 