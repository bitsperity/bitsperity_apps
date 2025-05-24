<script>
	import { onMount } from 'svelte';
	import { rules, activeRules, inactiveRules } from '$lib/stores/rules.js';
	import { uiActions } from '$lib/stores/ui.js';

	let showCreateModal = false;

	// Mock-Regeln für die Entwicklung
	const mockRules = [
		{
			id: 'rule_ph_auto',
			name: 'pH Automatik',
			description: 'Automatische pH-Wert Regulierung',
			enabled: true,
			trigger: {
				type: 'sensor',
				sensor: 'pH',
				condition: 'outside_range',
				min: 5.5,
				max: 6.5
			},
			actions: [
				{
					type: 'pump',
					device: 'ph_up_pump',
					duration: 5,
					condition: 'pH < 5.5'
				},
				{
					type: 'pump',
					device: 'ph_down_pump',
					duration: 5,
					condition: 'pH > 6.5'
				}
			],
			lastTriggered: new Date(Date.now() - 3600000),
			category: 'water_management'
		},
		{
			id: 'rule_nutrient_auto',
			name: 'Nährstoff-Dosierung',
			description: 'Automatische Nährstoffzugabe bei niedrigem TDS',
			enabled: true,
			trigger: {
				type: 'sensor',
				sensor: 'TDS',
				condition: 'below',
				threshold: 800
			},
			actions: [
				{
					type: 'pump',
					device: 'nutrient_pump',
					duration: 10
				}
			],
			lastTriggered: null,
			category: 'nutrition'
		},
		{
			id: 'rule_temp_alert',
			name: 'Temperatur-Warnung',
			description: 'Benachrichtigung bei kritischer Temperatur',
			enabled: false,
			trigger: {
				type: 'sensor',
				sensor: 'temperature',
				condition: 'above',
				threshold: 30
			},
			actions: [
				{
					type: 'notification',
					message: 'Kritische Temperatur erreicht!'
				}
			],
			lastTriggered: null,
			category: 'safety'
		}
	];

	function toggleRule(ruleId) {
		console.log('Toggle rule:', ruleId);
		uiActions.addNotification({
			type: 'info',
			title: 'Regel',
			message: 'Regel-Status geändert',
			timeout: 2000
		});
	}

	function deleteRule(ruleId) {
		console.log('Delete rule:', ruleId);
		uiActions.addNotification({
			type: 'warning',
			title: 'Regel gelöscht',
			message: 'Die Regel wurde entfernt',
			timeout: 3000
		});
	}

	function createRule() {
		showCreateModal = true;
	}

	function getCategoryIcon(category) {
		switch (category) {
			case 'water_management': return '💧';
			case 'nutrition': return '🌱';
			case 'safety': return '⚠️';
			case 'environment': return '🌡️';
			default: return '⚙️';
		}
	}

	function getCategoryColor(category) {
		switch (category) {
			case 'water_management': return 'from-blue-400 to-blue-600';
			case 'nutrition': return 'from-green-400 to-green-600';
			case 'safety': return 'from-red-400 to-red-600';
			case 'environment': return 'from-amber-400 to-amber-600';
			default: return 'from-gray-400 to-gray-600';
		}
	}

	onMount(() => {
		uiActions.addNotification({
			type: 'info',
			title: 'Automation',
			message: 'Regel-Editor geladen',
			timeout: 2000
		});
	});

	$: displayRules = $rules.length > 0 ? $rules : mockRules;
	$: enabledRules = displayRules.filter(rule => rule.enabled);
	$: disabledRules = displayRules.filter(rule => !rule.enabled);
</script>

<svelte:head>
	<title>Automation - HomeGrow v3</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 dark:from-gray-900 dark:to-teal-900/20">
	<!-- Header -->
	<header class="bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg border-b border-green-200/30 dark:border-green-800/30 p-4 sticky top-0 z-10">
		<div class="flex items-center justify-between">
			<div>
				<h1 class="text-2xl font-bold text-green-800 dark:text-green-200 flex items-center gap-2">
					🌿 Automation-Regeln
				</h1>
				<p class="text-green-600 dark:text-green-400 text-sm">Intelligente Steuerung Ihrer Hydroponic-Systeme</p>
			</div>
			<div class="bg-green-100 dark:bg-green-900/50 px-3 py-2 rounded-full">
				<span class="text-green-700 dark:text-green-300 text-sm font-medium">
					{enabledRules.length}/{displayRules.length} Aktiv
				</span>
			</div>
		</div>
	</header>

	<!-- Main Content -->
	<main class="p-4 space-y-6 max-w-6xl mx-auto">
		<!-- Quick Stats -->
		<section class="grid gap-4 sm:grid-cols-3">
			<div class="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl p-4 border border-green-200/50 dark:border-green-800/50 shadow-lg shadow-green-500/10">
				<div class="flex items-center gap-3">
					<div class="w-10 h-10 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center">
						✅
					</div>
					<div>
						<p class="text-2xl font-bold text-green-600 dark:text-green-400">{enabledRules.length}</p>
						<p class="text-sm text-gray-600 dark:text-gray-400">Aktive Regeln</p>
					</div>
				</div>
			</div>

			<div class="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl p-4 border border-green-200/50 dark:border-green-800/50 shadow-lg shadow-green-500/10">
				<div class="flex items-center gap-3">
					<div class="w-10 h-10 bg-gradient-to-br from-amber-400 to-amber-600 rounded-full flex items-center justify-center">
						⏸️
					</div>
					<div>
						<p class="text-2xl font-bold text-amber-600 dark:text-amber-400">{disabledRules.length}</p>
						<p class="text-sm text-gray-600 dark:text-gray-400">Deaktiviert</p>
					</div>
				</div>
			</div>

			<div class="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl p-4 border border-green-200/50 dark:border-green-800/50 shadow-lg shadow-green-500/10">
				<div class="flex items-center gap-3">
					<div class="w-10 h-10 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center">
						⚡
					</div>
					<div>
						<p class="text-2xl font-bold text-blue-600 dark:text-blue-400">24/7</p>
						<p class="text-sm text-gray-600 dark:text-gray-400">Überwachung</p>
					</div>
				</div>
			</div>
		</section>

		<!-- Create New Rule -->
		<section>
			<button 
				on:click={createRule}
				class="w-full bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white p-4 rounded-2xl font-medium transition-all transform hover:scale-105 shadow-lg shadow-green-500/25 flex items-center justify-center gap-2"
			>
				➕ Neue Automation-Regel erstellen
			</button>
		</section>

		<!-- Rules List -->
		<section>
			<h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
				📋 Alle Regeln
			</h2>
			<div class="space-y-4">
				{#each displayRules as rule}
					<div class="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl p-6 border border-green-200/50 dark:border-green-800/50 shadow-lg shadow-green-500/10">
						<!-- Rule Header -->
						<div class="flex items-start justify-between mb-4">
							<div class="flex items-center gap-3">
								<div class="w-12 h-12 bg-gradient-to-br {getCategoryColor(rule.category)} rounded-full flex items-center justify-center">
									<span class="text-white text-xl">{getCategoryIcon(rule.category)}</span>
								</div>
								<div>
									<h3 class="font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2">
										{rule.name}
										{#if rule.enabled}
											<span class="w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
										{:else}
											<span class="w-3 h-3 bg-gray-400 rounded-full"></span>
										{/if}
									</h3>
									<p class="text-sm text-gray-600 dark:text-gray-400">{rule.description}</p>
								</div>
							</div>
							<div class="flex items-center gap-2">
								<!-- Toggle Switch -->
								<button
									on:click={() => toggleRule(rule.id)}
									class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors {rule.enabled ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'}"
								>
									<span class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform {rule.enabled ? 'translate-x-6' : 'translate-x-1'}"></span>
								</button>
							</div>
						</div>

						<!-- Rule Details -->
						<div class="grid gap-4 sm:grid-cols-2">
							<!-- Trigger -->
							<div class="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
								<h4 class="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">🎯 Auslöser</h4>
								<p class="text-sm text-blue-700 dark:text-blue-300">
									{rule.trigger.sensor} {rule.trigger.condition} 
									{rule.trigger.threshold || `${rule.trigger.min}-${rule.trigger.max}`}
								</p>
							</div>

							<!-- Actions -->
							<div class="bg-green-50 dark:bg-green-900/20 p-3 rounded-lg">
								<h4 class="text-sm font-medium text-green-800 dark:text-green-200 mb-2">⚡ Aktionen</h4>
								<div class="space-y-1">
									{#each rule.actions as action}
										<p class="text-sm text-green-700 dark:text-green-300">
											{action.type === 'pump' ? `🔧 ${action.device} (${action.duration}s)` : 
											 action.type === 'notification' ? `📢 ${action.message}` : 
											 action.type}
										</p>
									{/each}
								</div>
							</div>
						</div>

						<!-- Last Triggered -->
						<div class="mt-4 pt-4 border-t border-green-200/50 dark:border-green-800/50 flex items-center justify-between">
							<span class="text-sm text-gray-600 dark:text-gray-400">
								Zuletzt ausgelöst: {rule.lastTriggered ? rule.lastTriggered.toLocaleString('de-DE') : 'Noch nie'}
							</span>
							<button
								on:click={() => deleteRule(rule.id)}
								class="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 text-sm"
							>
								🗑️ Löschen
							</button>
						</div>
					</div>
				{/each}
			</div>
		</section>

		<!-- Bottom Padding -->
		<div class="h-20"></div>
	</main>
</div>

<!-- Create Rule Modal (Placeholder) -->
{#if showCreateModal}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
		<div class="bg-white dark:bg-gray-800 rounded-2xl p-6 m-4 max-w-md w-full">
			<h3 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">Neue Regel erstellen</h3>
			<p class="text-gray-600 dark:text-gray-400 mb-4">
				Der visuelle Regel-Editor wird in der nächsten Version implementiert.
			</p>
			<button
				on:click={() => showCreateModal = false}
				class="w-full bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg transition-colors"
			>
				Verstanden
			</button>
		</div>
	</div>
{/if} 