import { writable, derived } from 'svelte/store';
import { apiClient } from '$lib/api/client.js';

// User State
export const user = writable(null);
export const isAuthenticated = writable(false);
export const isLoading = writable(false);
export const error = writable(null);

// Derived Stores
export const userProfile = derived(user, ($user) => $user?.profile || null);
export const userPreferences = derived(user, ($user) => $user?.preferences || {});

// User Actions
export const userActions = {
	// Login
	async login(credentials) {
		isLoading.set(true);
		error.set(null);
		
		try {
			const response = await apiClient.post('/auth/login', credentials);
			const { user: userData, token } = response.data;
			
			// Store token
			apiClient.setToken(token);
			
			// Update stores
			user.set(userData);
			isAuthenticated.set(true);
			
			return userData;
		} catch (err) {
			console.error('Login Fehler:', err);
			error.set('Anmeldung fehlgeschlagen');
			throw err;
		} finally {
			isLoading.set(false);
		}
	},

	// Logout
	async logout() {
		try {
			await apiClient.post('/auth/logout');
		} catch (err) {
			console.error('Logout Fehler:', err);
		} finally {
			// Clear local state regardless of API response
			apiClient.clearToken();
			user.set(null);
			isAuthenticated.set(false);
		}
	},

	// Register
	async register(userData) {
		isLoading.set(true);
		error.set(null);
		
		try {
			const response = await apiClient.post('/auth/register', userData);
			return response.data;
		} catch (err) {
			console.error('Registrierung Fehler:', err);
			error.set('Registrierung fehlgeschlagen');
			throw err;
		} finally {
			isLoading.set(false);
		}
	},

	// Check authentication status
	async checkAuth() {
		if (!apiClient.hasToken()) {
			isAuthenticated.set(false);
			return false;
		}

		// Für Entwicklung: Wenn dev-token vorhanden, akzeptiere es
		if (apiClient.token === 'dev-token-12345') {
			user.set({
				id: 'dev-user',
				email: 'dev@homegrow.local',
				name: 'Entwickler',
				profile: { name: 'Entwickler' },
				preferences: {}
			});
			isAuthenticated.set(true);
			return true;
		}

		try {
			const response = await apiClient.get('/auth/me');
			user.set(response.data);
			isAuthenticated.set(true);
			return true;
		} catch (err) {
			console.error('Auth Check Fehler:', err);
			// Nur bei 401 oder echten Auth-Fehlern logout
			if (err.message.includes('401') || err.message.includes('Authentifizierung')) {
				apiClient.clearToken();
				user.set(null);
				isAuthenticated.set(false);
			}
			return false;
		}
	},

	// Update user profile
	async updateProfile(profileData) {
		isLoading.set(true);
		error.set(null);
		
		try {
			const response = await apiClient.put('/auth/profile', profileData);
			user.update(current => ({
				...current,
				profile: { ...current.profile, ...response.data }
			}));
			return response.data;
		} catch (err) {
			console.error('Profil Update Fehler:', err);
			error.set('Profil konnte nicht aktualisiert werden');
			throw err;
		} finally {
			isLoading.set(false);
		}
	},

	// Update user preferences
	async updatePreferences(preferences) {
		try {
			const response = await apiClient.put('/auth/preferences', preferences);
			user.update(current => ({
				...current,
				preferences: { ...current.preferences, ...response.data }
			}));
			return response.data;
		} catch (err) {
			console.error('Einstellungen Update Fehler:', err);
			error.set('Einstellungen konnten nicht gespeichert werden');
			throw err;
		}
	},

	// Clear error
	clearError() {
		error.set(null);
	}
}; 