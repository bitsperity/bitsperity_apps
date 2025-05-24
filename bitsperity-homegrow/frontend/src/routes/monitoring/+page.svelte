<script>
	import { onMount } from 'svelte';
	import { latestSensorReadings, sensorHistory } from '$lib/stores/sensor.js';
	import { devices } from '$lib/stores/device.js';
	import { uiActions } from '$lib/stores/ui.js';

	// Mock Sensordaten für die Entwicklung
	const mockSensorData = {
		pH: { value: 6.2, unit: '', status: 'optimal', trend: 'stable' },
		tds: { value: 1200, unit: 'ppm', status: 'optimal', trend: 'rising' },
		temperature: { value: 22.5, unit: '°C', status: 'optimal', trend: 'stable' },
		humidity: { value: 65, unit: '%', status: 'optimal', trend: 'falling' }
	};

	// Sensor-Icons und Farben
	const sensorConfig = {
		pH: { icon: '🧪', color: 'from-blue-400 to-blue-600', bgColor: 'bg-blue-100 dark:bg-blue-900/50' },
		tds: { icon: '⚡', color: 'from-amber-400 to-amber-600', bgColor: 'bg-amber-100 dark:bg-amber-900/50' },
		temperature: { icon: '🌡️', color: 'from-red-400 to-red-600', bgColor: 'bg-red-100 dark:bg-red-900/50' },
		humidity: { icon: '💧', color: 'from-cyan-400 to-cyan-600', bgColor: 'bg-cyan-100 dark:bg-cyan-900/50' }
	};

	function getStatusColor(status) {
		switch (status) {
			case 'optimal': return 'text-green-600 dark:text-green-400';
			case 'warning': return 'text-yellow-600 dark:text-yellow-400';
			case 'critical': return 'text-red-600 dark:text-red-400';
			default: return 'text-gray-600 dark:text-gray-400';
		}
	}

	function getTrendIcon(trend) {
		switch (trend) {
			case 'rising': return '📈';
			case 'falling': return '📉';
			case 'stable': return '➡️';
			default: return '❓';
		}
	}

	onMount(() => {
		uiActions.addNotification({
			type: 'success',
			title: 'Monitoring',
			message: 'Sensor-Daten geladen',
			timeout: 2000
		});
	});

	$: displayData = Object.keys($latestSensorReadings).length > 0 ? $latestSensorReadings : mockSensorData;
</script>

<svelte:head>
	<title>Monitoring - HomeGrow v3</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-emerald-50 via-green-50 to-cyan-50 dark:from-gray-900 dark:to-emerald-900/20">
	<!-- Header -->
	<header class="bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg border-b border-emerald-200/30 dark:border-emerald-800/30 p-4 sticky top-0 z-10">
		<div class="flex items-center justify-between">
			<div>
				<h1 class="text-2xl font-bold text-emerald-800 dark:text-emerald-200 flex items-center gap-2">
					📊 System-Monitoring
				</h1>
				<p class="text-emerald-600 dark:text-emerald-400 text-sm">Live-Überwachung Ihrer Hydroponic-Systeme</p>
			</div>
			<div class="bg-emerald-100 dark:bg-emerald-900/50 px-3 py-2 rounded-full">
				<span class="text-emerald-700 dark:text-emerald-300 text-sm font-medium">
					🟢 Live
				</span>
			</div>
		</div>
	</header>

	<!-- Main Content -->
	<main class="p-4 space-y-6 max-w-6xl mx-auto">
		<!-- Sensor Cards Grid -->
		<section>
			<h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
				🌿 Aktuelle Messwerte
			</h2>
			<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
				{#each Object.entries(displayData) as [sensorType, data]}
					{@const config = sensorConfig[sensorType] || { icon: '📊', color: 'from-gray-400 to-gray-600', bgColor: 'bg-gray-100 dark:bg-gray-900/50' }}
					<div class="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl p-6 border border-emerald-200/50 dark:border-emerald-800/50 shadow-lg shadow-emerald-500/10">
						<!-- Sensor Header -->
						<div class="flex items-center justify-between mb-4">
							<div class="flex items-center gap-2">
								<div class="w-10 h-10 bg-gradient-to-br {config.color} rounded-full flex items-center justify-center text-white">
									{config.icon}
								</div>
								<div>
									<h3 class="font-medium text-gray-800 dark:text-gray-200 capitalize">{sensorType}</h3>
									<span class="text-xs {getStatusColor(data.status || 'optimal')} capitalize">
										{data.status || 'optimal'}
									</span>
								</div>
							</div>
							<div class="text-lg">
								{getTrendIcon(data.trend || 'stable')}
							</div>
						</div>

						<!-- Sensor Value -->
						<div class="text-center">
							<div class="text-3xl font-bold text-gray-800 dark:text-gray-200 mb-1">
								{typeof data === 'object' ? data.value : data}
								<span class="text-lg text-gray-600 dark:text-gray-400 ml-1">
									{data.unit || ''}
								</span>
							</div>
							
							<!-- Status Badge -->
							<div class="inline-flex items-center px-2 py-1 {config.bgColor} rounded-full mt-2">
								<span class="text-xs font-medium {getStatusColor(data.status || 'optimal')}">
									{data.status === 'optimal' ? 'Optimal' : 
									 data.status === 'warning' ? 'Warnung' : 
									 data.status === 'critical' ? 'Kritisch' : 'Normal'}
								</span>
							</div>
						</div>
					</div>
				{/each}
			</div>
		</section>

		<!-- Historical Charts Section -->
		<section>
			<h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
				📈 Verlaufsdaten
			</h2>
			<div class="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl p-6 border border-emerald-200/50 dark:border-emerald-800/50 shadow-lg shadow-emerald-500/10">
				<!-- Chart Placeholder -->
				<div class="h-64 bg-gradient-to-br from-emerald-100 to-green-100 dark:from-emerald-900/20 dark:to-green-900/20 rounded-xl flex items-center justify-center border-2 border-dashed border-emerald-300 dark:border-emerald-700">
					<div class="text-center">
						<div class="text-4xl mb-2">📊</div>
						<p class="text-emerald-700 dark:text-emerald-300 font-medium">Chart wird geladen...</p>
						<p class="text-emerald-600 dark:text-emerald-400 text-sm mt-1">Integration folgt in der nächsten Version</p>
					</div>
				</div>
			</div>
		</section>

		<!-- System Health -->
		<section>
			<h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
				💚 System-Gesundheit
			</h2>
			<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
				<!-- Water Quality -->
				<div class="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl p-4 border border-emerald-200/50 dark:border-emerald-800/50 shadow-lg shadow-emerald-500/10">
					<div class="flex items-center gap-3 mb-2">
						<div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
							💧
						</div>
						<h3 class="font-medium text-gray-800 dark:text-gray-200">Wasserqualität</h3>
					</div>
					<p class="text-2xl font-bold text-green-600 dark:text-green-400">Ausgezeichnet</p>
					<p class="text-sm text-gray-600 dark:text-gray-400">pH und TDS im optimalen Bereich</p>
				</div>

				<!-- Pump Status -->
				<div class="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl p-4 border border-emerald-200/50 dark:border-emerald-800/50 shadow-lg shadow-emerald-500/10">
					<div class="flex items-center gap-3 mb-2">
						<div class="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
							⚙️
						</div>
						<h3 class="font-medium text-gray-800 dark:text-gray-200">Pumpen</h3>
					</div>
					<p class="text-2xl font-bold text-green-600 dark:text-green-400">3/3 Aktiv</p>
					<p class="text-sm text-gray-600 dark:text-gray-400">Alle Systeme funktional</p>
				</div>

				<!-- Environment -->
				<div class="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl p-4 border border-emerald-200/50 dark:border-emerald-800/50 shadow-lg shadow-emerald-500/10">
					<div class="flex items-center gap-3 mb-2">
						<div class="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
							🌡️
						</div>
						<h3 class="font-medium text-gray-800 dark:text-gray-200">Umgebung</h3>
					</div>
					<p class="text-2xl font-bold text-green-600 dark:text-green-400">Ideal</p>
					<p class="text-sm text-gray-600 dark:text-gray-400">Temperatur und Luftfeuchtigkeit optimal</p>
				</div>
			</div>
		</section>

		<!-- Bottom Padding -->
		<div class="h-20"></div>
	</main>
</div> 