<script>
	import { onMount } from 'svelte';
	import { deviceCount } from '$lib/stores/device.js';
	import { alertingSensors } from '$lib/stores/sensor.js';
	import { Wifi, WifiOff, Bell, BellOff } from 'lucide-svelte';

	let currentTime = new Date();
	let isOnline = true;

	// Update time every minute
	onMount(() => {
		const interval = setInterval(() => {
			currentTime = new Date();
		}, 60000);

		// Check online status
		const handleOnline = () => isOnline = true;
		const handleOffline = () => isOnline = false;

		window.addEventListener('online', handleOnline);
		window.addEventListener('offline', handleOffline);

		return () => {
			clearInterval(interval);
			window.removeEventListener('online', handleOnline);
			window.removeEventListener('offline', handleOffline);
		};
	});

	$: formattedTime = currentTime.toLocaleTimeString('de-DE', {
		hour: '2-digit',
		minute: '2-digit'
	});

	$: hasAlerts = $alertingSensors.length > 0;
</script>

<header class="bg-white border-b border-gray-200 px-4 py-2">
	<div class="flex items-center justify-between">
		<!-- Left side: Time and connection status -->
		<div class="flex items-center space-x-2">
			<span class="text-sm font-medium text-gray-900">
				{formattedTime}
			</span>
			
			<div class="flex items-center space-x-1">
				{#if isOnline}
					<Wifi size={16} class="text-homegrow-600" />
				{:else}
					<WifiOff size={16} class="text-red-500" />
				{/if}
			</div>
		</div>

		<!-- Center: App title/logo -->
		<div class="flex items-center">
			<h1 class="text-lg font-bold text-homegrow-600">
				HomeGrow
			</h1>
		</div>

		<!-- Right side: Device count and alerts -->
		<div class="flex items-center space-x-3">
			<!-- Device status -->
			<div class="flex items-center space-x-1 text-xs">
				<div class="w-2 h-2 rounded-full bg-homegrow-500"></div>
				<span class="text-gray-600">
					{$deviceCount.online}/{$deviceCount.total}
				</span>
			</div>

			<!-- Alert indicator -->
			<div class="relative">
				{#if hasAlerts}
					<Bell size={16} class="text-red-500" />
					<div class="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full flex items-center justify-center">
						<span class="text-[8px] text-white font-bold">
							{Math.min($alertingSensors.length, 9)}
						</span>
					</div>
				{:else}
					<BellOff size={16} class="text-gray-400" />
				{/if}
			</div>
		</div>
	</div>
</header> 