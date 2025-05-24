<script>
	import { userActions } from '$lib/stores/user.js';
	import { apiClient } from '$lib/api/client.js';
	import { goto } from '$app/navigation';

	let email = '';
	let password = '';
	let isLoading = false;
	let error = null;

	// Für Entwicklung: Auto-Login überspringen
	async function skipAuth() {
		try {
			// Setze einen dummy token über den API Client
			apiClient.setToken('dev-token-12345');
			
			// Rufe checkAuth auf um den dev-token zu erkennen und Stores zu aktualisieren
			const success = await userActions.checkAuth();
			
			if (success) {
				// Explizit zur Dashboard-Seite navigieren
				goto('/', { replaceState: true });
			} else {
				error = 'Auth-Bypass fehlgeschlagen';
			}
		} catch (err) {
			console.error('Skip Auth Fehler:', err);
			error = 'Auth-Bypass fehlgeschlagen';
		}
	}

	async function handleLogin() {
		if (!email || !password) {
			error = 'Bitte E-Mail und Passwort eingeben';
			return;
		}

		isLoading = true;
		error = null;

		try {
			await userActions.login({ email, password });
			goto('/');
		} catch (err) {
			error = err.message || 'Login fehlgeschlagen';
		} finally {
			isLoading = false;
		}
	}
</script>

<svelte:head>
	<title>Login - HomeGrow v3</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-homegrow-50 to-homegrow-100 dark:from-gray-900 dark:to-gray-800 p-4">
	<div class="max-w-md w-full space-y-8">
		<div class="text-center">
			<h1 class="text-3xl font-bold text-homegrow-600 dark:text-homegrow-400">HomeGrow v3</h1>
			<p class="mt-2 text-gray-600 dark:text-gray-400">Anmelden um fortzufahren</p>
		</div>

		<div class="bg-white dark:bg-gray-800 p-8 rounded-lg shadow-md border border-gray-200 dark:border-gray-700">
			{#if error}
				<div class="mb-4 p-3 bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-300 rounded">
					{error}
				</div>
			{/if}

			<form on:submit|preventDefault={handleLogin} class="space-y-6">
				<div>
					<label for="email" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
						E-Mail
					</label>
					<input
						id="email"
						type="email"
						bind:value={email}
						disabled={isLoading}
						class="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-homegrow-500 focus:border-homegrow-500 dark:bg-gray-700 dark:text-white"
						placeholder="ihre@email.de"
						required
					/>
				</div>

				<div>
					<label for="password" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
						Passwort
					</label>
					<input
						id="password"
						type="password"
						bind:value={password}
						disabled={isLoading}
						class="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-homegrow-500 focus:border-homegrow-500 dark:bg-gray-700 dark:text-white"
						placeholder="••••••••"
						required
					/>
				</div>

				<div class="space-y-3">
					<button
						type="submit"
						disabled={isLoading}
						class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-homegrow-600 hover:bg-homegrow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-homegrow-500 disabled:opacity-50 disabled:cursor-not-allowed"
					>
						{isLoading ? 'Anmelden...' : 'Anmelden'}
					</button>

					<!-- Entwicklungs-Bypass -->
					<button
						type="button"
						on:click={skipAuth}
						class="w-full flex justify-center py-2 px-4 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-homegrow-500"
					>
						🚀 Entwicklung: Auth überspringen
					</button>
				</div>
			</form>

			<div class="mt-6 text-center">
				<p class="text-sm text-gray-600 dark:text-gray-400">
					Für die Entwicklung können Sie die Authentifizierung überspringen.
				</p>
			</div>
		</div>
	</div>
</div> 