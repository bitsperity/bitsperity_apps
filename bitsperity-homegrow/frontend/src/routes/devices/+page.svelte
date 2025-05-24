<script>
	import { onMount } from 'svelte';
	import { devices, deviceCount, onlineDevices, deviceActions, pumpConfig, getPumpsByCategory } from '$lib/stores/device.js';
	import { uiActions } from '$lib/stores/ui.js';

	let selectedDevice = null;
	let showPumpControls = false;

	// Pumpe aktivieren
	async function activatePump(deviceId, pumpType, duration = null) {
		try {
			await deviceActions.activatePump(deviceId, pumpType, duration);
			uiActions.addNotification({
				type: 'success',
				title: 'Pumpe aktiviert',
				message: `${pumpConfig[pumpType].name} wurde aktiviert`,
				timeout: 3000
			});
		} catch (error) {
			uiActions.addNotification({
				type: 'error',
				title: 'Fehler',
				message: `Fehler beim Aktivieren der Pumpe: ${error.message}`,
				timeout: 5000
			});
		}
	}

	// Quick Actions
	async function quickPHAdjustment(deviceId, direction) {
		try {
			if (direction === 'up') {
				await deviceActions.quickPHUp(deviceId);
			} else {
				await deviceActions.quickPHDown(deviceId);
			}
			uiActions.addNotification({
				type: 'success',
				title: 'pH-Korrektur',
				message: `pH ${direction === 'up' ? 'erhöht' : 'gesenkt'}`,
				timeout: 3000
			});
		} catch (error) {
			uiActions.addNotification({
				type: 'error',
				title: 'Fehler',
				message: `Fehler bei pH-Korrektur: ${error.message}`,
				timeout: 5000
			});
		}
	}

	async function quickNutrientDose(deviceId) {
		try {
			await deviceActions.quickNutrients(deviceId);
			uiActions.addNotification({
				type: 'success',
				title: 'Nährstoffe',
				message: 'Nährstoff A & B dosiert',
				timeout: 3000
			});
		} catch (error) {
			uiActions.addNotification({
				type: 'error',
				title: 'Fehler',
				message: `Fehler bei Nährstoff-Dosierung: ${error.message}`,
				timeout: 5000
			});
		}
	}

	onMount(async () => {
		try {
			await deviceActions.loadDevices();
			uiActions.addNotification({
				type: 'success',
				title: 'Geräte',
				message: 'Geräte-Übersicht geladen',
				timeout: 2000
			});
		} catch (error) {
			uiActions.addNotification({
				type: 'error',
				title: 'Fehler',
				message: 'Fehler beim Laden der Geräte',
				timeout: 5000
			});
		}
	});

	// Echte Sensoren basierend auf ESP32-System
	function getDeviceSensors() {
		return ['pH', 'TDS']; // Nur diese 2!
	}

	// Pumpen-Kategorien für UI
	const circulationPumps = getPumpsByCategory('circulation');
	const phControlPumps = getPumpsByCategory('ph_control');
	const nutritionPumps = getPumpsByCategory('nutrition');
</script>

<svelte:head>
	<title>Geräte - HomeGrow v3</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-green-50 to-emerald-50 dark:from-gray-900 dark:to-green-900/20">
	<!-- Header mit natürlichem Design -->
	<header class="bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg border-b border-green-200/30 dark:border-green-800/30 p-4 sticky top-0 z-10">
		<div class="flex items-center justify-between">
			<div>
				<h1 class="text-2xl font-bold text-green-800 dark:text-green-200 flex items-center gap-2">
					🔧 Geräte-Verwaltung
				</h1>
				<p class="text-green-600 dark:text-green-400 text-sm">Verwalten Sie Ihre Hydroponic-Systeme</p>
			</div>
			<div class="bg-green-100 dark:bg-green-900/50 px-3 py-2 rounded-full">
				<span class="text-green-700 dark:text-green-300 text-sm font-medium">
					{$deviceCount.online}/{$deviceCount.total} Online
				</span>
			</div>
		</div>
	</header>

	<!-- Main Content -->
	<main class="p-4 space-y-6 max-w-4xl mx-auto">
		<!-- Geräte-Grid -->
		<section>
			<div class="grid gap-4 md:grid-cols-2">
				{#each $devices as device}
					<div class="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl p-6 border border-green-200/50 dark:border-green-800/50 shadow-lg shadow-green-500/10">
						<!-- Device Header -->
						<div class="flex items-start justify-between mb-4">
							<div class="flex items-center gap-3">
								<div class="w-12 h-12 bg-gradient-to-br from-green-400 to-emerald-500 rounded-full flex items-center justify-center">
									<span class="text-white text-xl">🌱</span>
								</div>
								<div>
									<h3 class="font-semibold text-gray-800 dark:text-gray-200">{device.name || device.deviceId}</h3>
									<p class="text-sm text-gray-600 dark:text-gray-400">{device.location || 'ESP32 Hydroponic System'}</p>
								</div>
							</div>
							<div class="flex items-center gap-2">
								<div class="w-3 h-3 rounded-full {device.status === 'online' ? 'bg-green-500 animate-pulse' : 'bg-red-500'}"></div>
								<span class="text-sm text-gray-600 dark:text-gray-400 capitalize">{device.status}</span>
							</div>
						</div>

						<!-- Sensoren (nur pH und TDS!) -->
						<div class="mb-4">
							<h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Sensoren</h4>
							<div class="flex flex-wrap gap-2">
								{#each getDeviceSensors() as sensor}
									<span class="px-2 py-1 bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 text-xs rounded-full">
										🧪 {sensor}
									</span>
								{/each}
							</div>
						</div>

						<!-- Pumpen (7 Stück!) -->
						<div class="mb-4">
							<h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Pumpen (7 verfügbar)</h4>
							<div class="grid grid-cols-2 gap-2 text-xs">
								<span class="px-2 py-1 bg-cyan-100 dark:bg-cyan-900/50 text-cyan-700 dark:text-cyan-300 rounded-full">
									💧 Wasser
								</span>
								<span class="px-2 py-1 bg-cyan-100 dark:bg-cyan-900/50 text-cyan-700 dark:text-cyan-300 rounded-full">
									🌬️ Luft
								</span>
								<span class="px-2 py-1 bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300 rounded-full">
									⬆️ pH Up
								</span>
								<span class="px-2 py-1 bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-300 rounded-full">
									⬇️ pH Down
								</span>
								<span class="px-2 py-1 bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300 rounded-full">
									🌱 Nährstoff A
								</span>
								<span class="px-2 py-1 bg-lime-100 dark:bg-lime-900/50 text-lime-700 dark:text-lime-300 rounded-full">
									🌿 Nährstoff B
								</span>
								<span class="px-2 py-1 bg-yellow-100 dark:bg-yellow-900/50 text-yellow-700 dark:text-yellow-300 rounded-full">
									⭐ Zusätze
								</span>
							</div>
						</div>

						<!-- Quick Actions -->
						<div class="space-y-2 pt-4 border-t border-green-200/50 dark:border-green-800/50">
							<!-- pH Kontrolle -->
							<div class="flex gap-2">
								<button 
									on:click={() => quickPHAdjustment(device.deviceId, 'up')}
									class="flex-1 bg-green-500 hover:bg-green-600 text-white px-3 py-2 rounded-lg text-sm font-medium transition-colors"
								>
									⬆️ pH Up
								</button>
								<button 
									on:click={() => quickPHAdjustment(device.deviceId, 'down')}
									class="flex-1 bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded-lg text-sm font-medium transition-colors"
								>
									⬇️ pH Down
								</button>
							</div>
							
							<!-- Nährstoff & Wasser -->
							<div class="flex gap-2">
								<button 
									on:click={() => quickNutrientDose(device.deviceId)}
									class="flex-1 bg-emerald-500 hover:bg-emerald-600 text-white px-3 py-2 rounded-lg text-sm font-medium transition-colors"
								>
									🌱 Nährstoffe
								</button>
								<button 
									on:click={() => activatePump(device.deviceId, 'water_pump')}
									class="flex-1 bg-blue-500 hover:bg-blue-600 text-white px-3 py-2 rounded-lg text-sm font-medium transition-colors"
								>
									💧 Wasser
								</button>
							</div>

							<!-- Erweiterte Steuerung -->
							<button 
								on:click={() => {selectedDevice = device; showPumpControls = true;}}
								class="w-full bg-gray-500 hover:bg-gray-600 text-white px-3 py-2 rounded-lg text-sm font-medium transition-colors"
							>
								⚙️ Erweiterte Steuerung
							</button>
						</div>
					</div>
				{/each}
			</div>
		</section>

		<!-- Verbindungsinfo -->
		<section class="bg-blue-50 dark:bg-blue-900/20 rounded-2xl p-4 border border-blue-200/50 dark:border-blue-800/50">
			<div class="flex items-center gap-3">
				<div class="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
					📡
				</div>
				<div>
					<h3 class="font-semibold text-blue-800 dark:text-blue-200">ESP32 Auto-Discovery</h3>
					<p class="text-sm text-blue-600 dark:text-blue-300">
						Geräte werden automatisch erkannt wenn sie sich mit dem MQTT-Broker verbinden
					</p>
				</div>
			</div>
		</section>

		<!-- Bottom Padding -->
		<div class="h-20"></div>
	</main>
</div>

<!-- Erweiterte Pumpen-Kontrolle Modal -->
{#if showPumpControls && selectedDevice}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
		<div class="bg-white dark:bg-gray-800 rounded-2xl p-6 m-4 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
			<div class="flex items-center justify-between mb-6">
				<h3 class="text-xl font-semibold text-gray-800 dark:text-gray-200">
					🔧 Pumpen-Steuerung - {selectedDevice.name || selectedDevice.deviceId}
				</h3>
				<button
					on:click={() => showPumpControls = false}
					class="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
				>
					✕
				</button>
			</div>

			<!-- Zirkulation -->
			<div class="mb-6">
				<h4 class="text-lg font-medium text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
					🌊 Zirkulation
				</h4>
				<div class="grid grid-cols-2 gap-3">
					{#each circulationPumps as pump}
						<button
							on:click={() => activatePump(selectedDevice.deviceId, pump.pumpType)}
							class="bg-gradient-to-r from-{pump.color}-400 to-{pump.color}-500 hover:from-{pump.color}-500 hover:to-{pump.color}-600 text-white p-4 rounded-xl font-medium transition-all transform hover:scale-105"
						>
							<div class="text-2xl mb-1">{pump.icon}</div>
							<div class="text-sm">{pump.name}</div>
							<div class="text-xs opacity-75">{pump.description}</div>
						</button>
					{/each}
				</div>
			</div>

			<!-- pH-Kontrolle -->
			<div class="mb-6">
				<h4 class="text-lg font-medium text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
					🧪 pH-Kontrolle
				</h4>
				<div class="grid grid-cols-2 gap-3">
					{#each phControlPumps as pump}
						<button
							on:click={() => activatePump(selectedDevice.deviceId, pump.pumpType)}
							class="bg-gradient-to-r from-{pump.color}-400 to-{pump.color}-500 hover:from-{pump.color}-500 hover:to-{pump.color}-600 text-white p-4 rounded-xl font-medium transition-all transform hover:scale-105"
						>
							<div class="text-2xl mb-1">{pump.icon}</div>
							<div class="text-sm">{pump.name}</div>
							<div class="text-xs opacity-75">{pump.description}</div>
						</button>
					{/each}
				</div>
			</div>

			<!-- Nährstoffe -->
			<div class="mb-6">
				<h4 class="text-lg font-medium text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
					🌱 Nährstoff-System
				</h4>
				<div class="grid grid-cols-3 gap-3">
					{#each nutritionPumps as pump}
						<button
							on:click={() => activatePump(selectedDevice.deviceId, pump.pumpType)}
							class="bg-gradient-to-r from-{pump.color}-400 to-{pump.color}-500 hover:from-{pump.color}-500 hover:to-{pump.color}-600 text-white p-4 rounded-xl font-medium transition-all transform hover:scale-105"
						>
							<div class="text-2xl mb-1">{pump.icon}</div>
							<div class="text-sm">{pump.name}</div>
							<div class="text-xs opacity-75">{pump.description}</div>
						</button>
					{/each}
				</div>
			</div>

			<!-- Wartungssequenzen -->
			<div class="mb-6">
				<h4 class="text-lg font-medium text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
					🔧 Wartungssequenzen
				</h4>
				<div class="grid grid-cols-2 gap-3">
					<button
						on:click={() => deviceActions.maintenanceMode(selectedDevice.deviceId, 'basic')}
						class="bg-gradient-to-r from-gray-400 to-gray-500 hover:from-gray-500 hover:to-gray-600 text-white p-4 rounded-xl font-medium transition-all"
					>
						<div class="text-xl mb-1">🔄</div>
						<div class="text-sm">Basis-Wartung</div>
						<div class="text-xs opacity-75">Wasser + Luft</div>
					</button>
					<button
						on:click={() => deviceActions.maintenanceMode(selectedDevice.deviceId, 'full_cycle')}
						class="bg-gradient-to-r from-purple-400 to-purple-500 hover:from-purple-500 hover:to-purple-600 text-white p-4 rounded-xl font-medium transition-all"
					>
						<div class="text-xl mb-1">🔄</div>
						<div class="text-sm">Vollzyklus</div>
						<div class="text-xs opacity-75">Alles testen</div>
					</button>
				</div>
			</div>

			<!-- Schließen -->
			<div class="flex justify-end">
				<button
					on:click={() => showPumpControls = false}
					class="bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded-lg transition-colors"
				>
					Schließen
				</button>
			</div>
		</div>
	</div>
{/if} 