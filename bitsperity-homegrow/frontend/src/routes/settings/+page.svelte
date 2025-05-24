<script>
	import { onMount } from 'svelte';
	import { userActions, isAuthenticated, user } from '$lib/stores/user.js';
	import { uiActions, theme, notifications } from '$lib/stores/ui.js';
	import { goto } from '$app/navigation';

	let showUserModal = false;
	let showAboutModal = false;

	const settingsCategories = [
		{
			title: 'Benutzer & Account',
			icon: '👤',
			color: 'from-blue-400 to-blue-600',
			items: [
				{ id: 'profile', name: 'Profil bearbeiten', description: 'Name, E-Mail und Passwort ändern', icon: '✏️' },
				{ id: 'preferences', name: 'Einstellungen', description: 'Persönliche Präferenzen', icon: '⚙️' },
				{ id: 'logout', name: 'Abmelden', description: 'Sicher vom System abmelden', icon: '🚪' }
			]
		},
		{
			title: 'System & Design',
			icon: '🎨',
			color: 'from-green-400 to-green-600',
			items: [
				{ id: 'theme', name: 'Design-Modus', description: 'Hell/Dunkel Theme wechseln', icon: '🌗' },
				{ id: 'notifications', name: 'Benachrichtigungen', description: 'Notification-Einstellungen', icon: '🔔' },
				{ id: 'language', name: 'Sprache', description: 'Interface-Sprache ändern', icon: '🌍' }
			]
		},
		{
			title: 'Hydroponic System',
			icon: '🌱',
			color: 'from-emerald-400 to-emerald-600',
			items: [
				{ id: 'sensors', name: 'Sensor-Kalibrierung', description: 'pH, TDS und andere Sensoren kalibrieren', icon: '🧪' },
				{ id: 'pumps', name: 'Pumpen-Konfiguration', description: 'Pumpen und Aktoren einstellen', icon: '⚙️' },
				{ id: 'intervals', name: 'Mess-Intervalle', description: 'Sensor-Ableseintervalle konfigurieren', icon: '⏱️' }
			]
		},
		{
			title: 'Daten & Sicherheit',
			icon: '🔒',
			color: 'from-purple-400 to-purple-600',
			items: [
				{ id: 'backup', name: 'Datensicherung', description: 'System-Backup erstellen', icon: '💾' },
				{ id: 'export', name: 'Daten exportieren', description: 'Sensor-Daten als CSV exportieren', icon: '📊' },
				{ id: 'reset', name: 'System zurücksetzen', description: 'Werkseinstellungen wiederherstellen', icon: '🔄' }
			]
		}
	];

	function handleSettingClick(itemId) {
		switch (itemId) {
			case 'logout':
				handleLogout();
				break;
			case 'theme':
				toggleTheme();
				break;
			case 'profile':
				showUserModal = true;
				break;
			default:
				uiActions.addNotification({
					type: 'info',
					title: 'Einstellung',
					message: `${itemId} wird in einer zukünftigen Version implementiert`,
					timeout: 3000
				});
		}
	}

	function toggleTheme() {
		uiActions.toggleTheme();
		uiActions.addNotification({
			type: 'success',
			title: 'Design geändert',
			message: `Theme zu ${$theme === 'dark' ? 'Dunkel' : 'Hell'} gewechselt`,
			timeout: 2000
		});
	}

	async function handleLogout() {
		try {
			await userActions.logout();
			uiActions.addNotification({
				type: 'info',
				title: 'Abgemeldet',
				message: 'Sie wurden erfolgreich abgemeldet',
				timeout: 2000
			});
			goto('/auth/login');
		} catch (error) {
			uiActions.addNotification({
				type: 'error',
				title: 'Fehler',
				message: 'Fehler beim Abmelden',
				timeout: 3000
			});
		}
	}

	function showAbout() {
		showAboutModal = true;
	}

	onMount(() => {
		uiActions.addNotification({
			type: 'info',
			title: 'Einstellungen',
			message: 'Einstellungen geladen',
			timeout: 2000
		});
	});
</script>

<svelte:head>
	<title>Einstellungen - HomeGrow v3</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-slate-50 via-green-50 to-blue-50 dark:from-gray-900 dark:to-slate-900">
	<!-- Header -->
	<header class="bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg border-b border-slate-200/30 dark:border-slate-800/30 p-4 sticky top-0 z-10">
		<div class="flex items-center justify-between">
			<div>
				<h1 class="text-2xl font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
					⚙️ Einstellungen
				</h1>
				<p class="text-slate-600 dark:text-slate-400 text-sm">System-Konfiguration und Benutzer-Einstellungen</p>
			</div>
			<button
				on:click={showAbout}
				class="bg-slate-100 dark:bg-slate-800 px-3 py-2 rounded-full hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
			>
				<span class="text-slate-700 dark:text-slate-300 text-sm font-medium">
					ℹ️ Info
				</span>
			</button>
		</div>
	</header>

	<!-- Main Content -->
	<main class="p-4 space-y-8 max-w-4xl mx-auto">
		<!-- User Info Card -->
		{#if $isAuthenticated}
			<section class="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl p-6 border border-slate-200/50 dark:border-slate-800/50 shadow-lg shadow-slate-500/10">
				<div class="flex items-center gap-4">
					<div class="w-16 h-16 bg-gradient-to-br from-green-400 to-emerald-500 rounded-full flex items-center justify-center">
						<span class="text-white text-2xl">👤</span>
					</div>
					<div class="flex-1">
						<h2 class="text-xl font-semibold text-gray-800 dark:text-gray-200">
							{$user?.name || 'Entwicklungs-Benutzer'}
						</h2>
						<p class="text-gray-600 dark:text-gray-400">{$user?.email || 'dev@homegrow.local'}</p>
						<p class="text-sm text-green-600 dark:text-green-400 mt-1">
							✅ Angemeldet seit {new Date().toLocaleDateString('de-DE')}
						</p>
					</div>
					<button
						on:click={() => handleSettingClick('profile')}
						class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg transition-colors text-sm"
					>
						Bearbeiten
					</button>
				</div>
			</section>
		{/if}

		<!-- Settings Categories -->
		{#each settingsCategories as category}
			<section>
				<h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
					<span class="text-xl">{category.icon}</span>
					{category.title}
				</h2>
				<div class="space-y-3">
					{#each category.items as item}
						<button
							on:click={() => handleSettingClick(item.id)}
							class="w-full bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-xl p-4 border border-slate-200/50 dark:border-slate-800/50 shadow-lg shadow-slate-500/10 hover:shadow-slate-500/20 transition-all hover:scale-105 text-left group"
						>
							<div class="flex items-center gap-4">
								<div class="w-12 h-12 bg-gradient-to-br {category.color} rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
									<span class="text-white text-lg">{item.icon}</span>
								</div>
								<div class="flex-1">
									<h3 class="font-medium text-gray-800 dark:text-gray-200 group-hover:text-green-600 dark:group-hover:text-green-400 transition-colors">
										{item.name}
									</h3>
									<p class="text-sm text-gray-600 dark:text-gray-400">{item.description}</p>
								</div>
								<div class="text-gray-400 group-hover:text-green-500 transition-colors">
									→
								</div>
							</div>
						</button>
					{/each}
				</div>
			</section>
		{/each}

		<!-- Quick Actions -->
		<section>
			<h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
				⚡ Schnellaktionen
			</h2>
			<div class="grid gap-4 sm:grid-cols-2">
				<button
					on:click={toggleTheme}
					class="bg-gradient-to-r from-slate-500 to-slate-600 hover:from-slate-600 hover:to-slate-700 text-white p-4 rounded-xl font-medium transition-all transform hover:scale-105 shadow-lg shadow-slate-500/25 flex items-center justify-center gap-2"
				>
					🌗 Theme wechseln
				</button>
				<button
					on:click={handleLogout}
					class="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white p-4 rounded-xl font-medium transition-all transform hover:scale-105 shadow-lg shadow-red-500/25 flex items-center justify-center gap-2"
				>
					🚪 Abmelden
				</button>
			</div>
		</section>

		<!-- Bottom Padding -->
		<div class="h-20"></div>
	</main>
</div>

<!-- User Profile Modal -->
{#if showUserModal}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
		<div class="bg-white dark:bg-gray-800 rounded-2xl p-6 m-4 max-w-md w-full">
			<h3 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">Profil bearbeiten</h3>
			<div class="space-y-4">
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
					<input 
						type="text" 
						class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white"
						value={$user?.name || 'Entwicklungs-Benutzer'}
					/>
				</div>
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">E-Mail</label>
					<input 
						type="email" 
						class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white"
						value={$user?.email || 'dev@homegrow.local'}
					/>
				</div>
			</div>
			<div class="flex gap-3 mt-6">
				<button
					on:click={() => showUserModal = false}
					class="flex-1 bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
				>
					Abbrechen
				</button>
				<button
					on:click={() => {
						showUserModal = false;
						uiActions.addNotification({
							type: 'success',
							title: 'Profil',
							message: 'Änderungen gespeichert',
							timeout: 3000
						});
					}}
					class="flex-1 bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg transition-colors"
				>
					Speichern
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- About Modal -->
{#if showAboutModal}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
		<div class="bg-white dark:bg-gray-800 rounded-2xl p-6 m-4 max-w-md w-full">
			<h3 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
				🌱 HomeGrow v3
			</h3>
			<div class="space-y-3 text-sm text-gray-600 dark:text-gray-400">
				<p><strong>Version:</strong> 3.0.0-dev</p>
				<p><strong>Build:</strong> {new Date().toISOString().split('T')[0]}</p>
				<p><strong>Framework:</strong> SvelteKit 2.0</p>
				<p><strong>Design:</strong> Tailwind CSS 3.4</p>
				<p><strong>Backend:</strong> Node.js + Fastify</p>
				<div class="pt-2 border-t border-gray-200 dark:border-gray-700">
					<p class="font-medium text-green-600 dark:text-green-400">
						🌿 Professionelle Hydroponic-Automation
					</p>
					<p>Mit Liebe entwickelt für nachhaltigen Anbau</p>
				</div>
			</div>
			<button
				on:click={() => showAboutModal = false}
				class="w-full bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg transition-colors mt-4"
			>
				Verstanden
			</button>
		</div>
	</div>
{/if} 