<script>
	import { onMount, onDestroy } from 'svelte';
	import { apiClient } from '$lib/api/client.js';

	// Real-time data state
	let devices = [];
	let sensorData = {};
	let loading = true;
	let error = null;
	let refreshInterval;

	// Real sensor configuration (only pH and TDS - no mock sensors!)
	const sensorConfig = {
		ph: { 
			icon: '🧪', 
			color: 'from-blue-400 to-blue-600', 
			bgColor: 'bg-blue-100 dark:bg-blue-900/50',
			name: 'pH-Wert',
			unit: '',
			optimal: { min: 5.5, max: 6.5 }
		},
		tds: { 
			icon: '⚡', 
			color: 'from-amber-400 to-amber-600', 
			bgColor: 'bg-amber-100 dark:bg-amber-900/50',
			name: 'Leitfähigkeit',
			unit: 'ppm',
			optimal: { min: 800, max: 1500 }
		}
	};

	// Load real data from API
	async function loadData() {
		try {
			loading = true;
			error = null;
			
			// Load devices and sensor data in parallel
			const [devicesResponse, sensorsResponse] = await Promise.all([
				apiClient.get('/devices'),
				apiClient.get('/sensors/latest')
			]);

			if (devicesResponse.success) {
				devices = devicesResponse.data.devices;
			}
			
			if (sensorsResponse.success) {
				sensorData = sensorsResponse.data;
			}

		} catch (err) {
			console.error('Fehler beim Laden der Daten:', err);
			error = err.message || 'Fehler beim Laden der Daten';
		} finally {
			loading = false;
		}
	}

	// Helper functions
	function getStatusColor(status) {
		switch (status) {
			case 'optimal': return 'text-green-600 dark:text-green-400';
			case 'warning': return 'text-yellow-600 dark:text-yellow-400';
			case 'critical': return 'text-red-600 dark:text-red-400';
			default: return 'text-gray-600 dark:text-gray-400';
		}
	}

	function getStatusIcon(status) {
		switch (status) {
			case 'optimal': return '✅';
			case 'warning': return '⚠️';
			case 'critical': return '🔴';
			default: return '⚪';
		}
	}

	function formatValue(value, precision = 2) {
		return typeof value === 'number' ? value.toFixed(precision) : value;
	}

	function getTimeSince(timestamp) {
		const now = new Date();
		const time = new Date(timestamp);
		const diffMs = now - time;
		const diffMins = Math.floor(diffMs / (1000 * 60));
		
		if (diffMins < 1) return 'Gerade eben';
		if (diffMins < 60) return `vor ${diffMins}min`;
		const diffHours = Math.floor(diffMins / 60);
		return `vor ${diffHours}h`;
	}

	// Computed values
	$: onlineDeviceCount = devices.filter(d => d.status === 'online').length;
	$: totalDeviceCount = devices.length;
	$: systemOnline = onlineDeviceCount > 0;
	$: totalSensorCount = Object.values(sensorData).reduce((total, deviceSensors) => {
		return total + Object.keys(deviceSensors).length;
	}, 0);

	// Calculate overall system health based on sensor statuses
	$: overallHealth = (() => {
		let optimal = 0, warning = 0, critical = 0, total = 0;
		
		Object.values(sensorData).forEach(deviceSensors => {
			Object.values(deviceSensors).forEach(sensor => {
				total++;
				switch (sensor.status) {
					case 'optimal': optimal++; break;
					case 'warning': warning++; break;
					case 'critical': critical++; break;
				}
			});
		});
		
		if (total === 0) return { score: 0, status: 'unknown' };
		
		const score = Math.round((optimal / total) * 100);
		let status = 'critical';
		if (score >= 80) status = 'excellent';
		else if (score >= 60) status = 'good';
		else if (score >= 40) status = 'warning';
		
		return { score, status };
	})();

	onMount(() => {
		loadData();
		// Auto-refresh every 30 seconds
		refreshInterval = setInterval(loadData, 30000);
	});

	onDestroy(() => {
		if (refreshInterval) {
			clearInterval(refreshInterval);
		}
	});
</script>

<svelte:head>
	<title>Dashboard - HomeGrow v3</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-cyan-50 dark:from-gray-900 dark:to-green-900/20">
	<!-- Header -->
	<header class="bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg border-b border-green-200/30 dark:border-green-800/30 p-4 sticky top-0 z-10">
		<div class="flex items-center justify-between max-w-6xl mx-auto">
			<div>
				<h1 class="text-2xl font-bold text-green-800 dark:text-green-200 flex items-center gap-2">
					🌱 HomeGrow Dashboard
				</h1>
				<p class="text-green-600 dark:text-green-400 text-sm">
					{systemOnline ? `🟢 ${onlineDeviceCount} von ${totalDeviceCount} Geräten online` : '🔴 Alle Geräte offline'}
				</p>
			</div>
			<div class="flex items-center gap-4">
				<button 
					on:click={loadData} 
					class="bg-green-100 dark:bg-green-900/50 px-3 py-2 rounded-full hover:bg-green-200 dark:hover:bg-green-900/70 transition-colors"
					disabled={loading}
				>
					<span class="text-green-700 dark:text-green-300 text-sm font-medium">
						{loading ? '🔄' : '↻'} {loading ? 'Lädt...' : 'Aktualisieren'}
					</span>
				</button>
				<div class="bg-green-100 dark:bg-green-900/50 px-3 py-2 rounded-full">
					<span class="text-green-700 dark:text-green-300 text-sm font-medium">
						{new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}
					</span>
				</div>
			</div>
		</div>
	</header>

	<main class="p-4 space-y-6 max-w-6xl mx-auto">
		{#if loading && devices.length === 0}
			<!-- Loading State -->
			<div class="flex items-center justify-center py-12">
				<div class="text-center">
					<div class="animate-spin text-4xl mb-4">🔄</div>
					<p class="text-gray-600 dark:text-gray-400">Lade Dashboard-Daten...</p>
				</div>
			</div>
		{:else if error}
			<!-- Error State -->
			<div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl p-6">
				<div class="flex items-center gap-3">
					<div class="text-2xl">🚨</div>
					<div>
						<h3 class="font-semibold text-red-800 dark:text-red-200">Fehler beim Laden</h3>
						<p class="text-red-600 dark:text-red-400 text-sm">{error}</p>
					</div>
				</div>
			</div>
		{:else}
			<!-- System Overview -->
			<section class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
				<!-- System Health -->
				<div class="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl p-4 border border-green-200/50 dark:border-green-800/50 shadow-lg shadow-green-500/10">
					<div class="flex items-center gap-3">
						<div class="w-10 h-10 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center">
							{getStatusIcon(overallHealth.status)}
						</div>
						<div>
							<p class="text-2xl font-bold text-green-600 dark:text-green-400">{overallHealth.score}%</p>
							<p class="text-sm text-gray-600 dark:text-gray-400">System-Gesundheit</p>
						</div>
					</div>
				</div>

				<!-- Active Devices -->
				<div class="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl p-4 border border-green-200/50 dark:border-green-800/50 shadow-lg shadow-green-500/10">
					<div class="flex items-center gap-3">
						<div class="w-10 h-10 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center">
							🔧
						</div>
						<div>
							<p class="text-2xl font-bold text-blue-600 dark:text-blue-400">{onlineDeviceCount}/{totalDeviceCount}</p>
							<p class="text-sm text-gray-600 dark:text-gray-400">Geräte online</p>
						</div>
					</div>
				</div>

				<!-- Total Sensors -->
				<div class="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl p-4 border border-green-200/50 dark:border-green-800/50 shadow-lg shadow-green-500/10">
					<div class="flex items-center gap-3">
						<div class="w-10 h-10 bg-gradient-to-br from-purple-400 to-purple-600 rounded-full flex items-center justify-center">
							📊
						</div>
						<div>
							<p class="text-2xl font-bold text-purple-600 dark:text-purple-400">{totalSensorCount}</p>
							<p class="text-sm text-gray-600 dark:text-gray-400">Aktive Sensoren</p>
						</div>
					</div>
				</div>

				<!-- Data Freshness -->
				<div class="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl p-4 border border-green-200/50 dark:border-green-800/50 shadow-lg shadow-green-500/10">
					<div class="flex items-center gap-3">
						<div class="w-10 h-10 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-full flex items-center justify-center">
							⏱️
						</div>
						<div>
							<p class="text-2xl font-bold text-emerald-600 dark:text-emerald-400">LIVE</p>
							<p class="text-sm text-gray-600 dark:text-gray-400">Daten-Status</p>
						</div>
					</div>
				</div>
			</section>

			<!-- Devices and Sensors -->
			{#each devices as device}
				{@const deviceSensors = sensorData[device.deviceId] || {}}
				<section class="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl border border-green-200/50 dark:border-green-800/50 shadow-lg shadow-green-500/10">
					<!-- Device Header -->
					<div class="p-6 border-b border-green-200/30 dark:border-green-800/30">
						<div class="flex items-center justify-between">
							<div class="flex items-center gap-4">
								<div class="w-12 h-12 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center">
									{device.status === 'online' ? '🟢' : '🔴'}
								</div>
								<div>
									<h2 class="text-xl font-bold text-gray-800 dark:text-gray-200">{device.name}</h2>
									<div class="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
										<span class="flex items-center gap-1">
											📍 {device.location}
										</span>
										<span class="flex items-center gap-1">
											⏰ {device.lastSeen ? getTimeSince(device.lastSeen) : 'Nie'}
										</span>
									</div>
								</div>
							</div>
							<div class="text-right">
								<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium {device.status === 'online' ? 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-200' : 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-200'}">
									{device.status === 'online' ? 'Online' : 'Offline'}
								</span>
							</div>
						</div>
					</div>

					<!-- Device Sensors -->
					<div class="p-6">
						{#if Object.keys(deviceSensors).length > 0}
							<h3 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
								📊 Live-Sensordaten
								<span class="text-xs bg-green-500 text-white px-2 py-1 rounded-full animate-pulse">LIVE</span>
							</h3>
							<div class="grid gap-4 sm:grid-cols-2">
								{#each Object.entries(deviceSensors) as [sensorType, sensor]}
									{@const config = sensorConfig[sensorType]}
									{#if config}
										<div class="bg-gradient-to-br {config.bgColor} rounded-xl p-4 border border-green-200/30 dark:border-green-800/30">
											<div class="flex items-center justify-between mb-3">
												<div class="flex items-center gap-3">
													<div class="w-10 h-10 bg-gradient-to-br {config.color} rounded-full flex items-center justify-center text-white font-bold">
														{config.icon}
													</div>
													<div>
														<h4 class="font-medium text-gray-800 dark:text-gray-200">{config.name}</h4>
														<span class="text-xs {getStatusColor(sensor.status)} font-medium capitalize">
															{sensor.status}
														</span>
													</div>
												</div>
												<div class="text-right">
													<div class="text-2xl font-bold text-gray-800 dark:text-gray-200">
														{formatValue(sensor.value)}
													</div>
													{#if config.unit}
														<div class="text-xs text-gray-600 dark:text-gray-400">{config.unit}</div>
													{/if}
												</div>
											</div>
											<div class="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400">
												<span>Optimal: {config.optimal.min} - {config.optimal.max}</span>
												<span>{getTimeSince(sensor.receivedAt)}</span>
											</div>
										</div>
									{/if}
								{/each}
							</div>
						{:else}
							<div class="text-center py-8">
								<div class="text-4xl mb-2">📡</div>
								<p class="text-gray-600 dark:text-gray-400">Keine Sensordaten verfügbar</p>
								<p class="text-sm text-gray-500 dark:text-gray-500">Das Gerät sendet momentan keine Daten</p>
							</div>
						{/if}
					</div>
				</section>
			{/each}

			{#if devices.length === 0}
				<section class="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl border border-green-200/50 dark:border-green-800/50 shadow-lg shadow-green-500/10 p-8">
					<div class="text-center">
						<div class="text-6xl mb-4">🌱</div>
						<h2 class="text-2xl font-bold text-gray-800 dark:text-gray-200 mb-2">Keine Geräte gefunden</h2>
						<p class="text-gray-600 dark:text-gray-400 mb-4">Es sind noch keine ESP32-Geräte registriert.</p>
						<p class="text-sm text-gray-500 dark:text-gray-500">Geräte werden automatisch erkannt, sobald sie Daten senden.</p>
					</div>
				</section>
			{/if}
		{/if}
	</main>
</div> 