import { writable, derived } from 'svelte/store';
import { apiClient } from '$lib/api/client.js';

// Rules State
export const rules = writable([]);
export const selectedRule = writable(null);
export const isLoading = writable(false);
export const error = writable(null);

// Derived Stores
export const activeRules = derived(rules, ($rules) => 
	$rules.filter(rule => rule.enabled)
);

export const inactiveRules = derived(rules, ($rules) => 
	$rules.filter(rule => !rule.enabled)
);

export const rulesByType = derived(rules, ($rules) => {
	const grouped = {};
	$rules.forEach(rule => {
		if (!grouped[rule.type]) {
			grouped[rule.type] = [];
		}
		grouped[rule.type].push(rule);
	});
	return grouped;
});

export const ruleStats = derived(rules, ($rules) => ({
	total: $rules.length,
	active: $rules.filter(r => r.enabled).length,
	inactive: $rules.filter(r => !r.enabled).length,
	triggered: $rules.filter(r => r.lastTriggered).length
}));

// Rules Actions
export const rulesActions = {
	// Lade alle Regeln
	async loadRules() {
		isLoading.set(true);
		error.set(null);
		
		try {
			const response = await apiClient.get('/rules');
			rules.set(response.data || []);
		} catch (err) {
			console.error('Fehler beim Laden der Regeln:', err);
			error.set('Fehler beim Laden der Regeln');
		} finally {
			isLoading.set(false);
		}
	},

	// Regel erstellen
	async createRule(ruleData) {
		try {
			const response = await apiClient.post('/rules', ruleData);
			rules.update(current => [...current, response.data]);
			return response.data;
		} catch (err) {
			console.error('Fehler beim Erstellen der Regel:', err);
			error.set('Fehler beim Erstellen der Regel');
			throw err;
		}
	},

	// Regel aktualisieren
	async updateRule(ruleId, updateData) {
		try {
			const response = await apiClient.put(`/rules/${ruleId}`, updateData);
			rules.update(current => 
				current.map(rule => 
					rule.id === ruleId ? { ...rule, ...response.data } : rule
				)
			);
			return response.data;
		} catch (err) {
			console.error('Fehler beim Aktualisieren der Regel:', err);
			error.set('Fehler beim Aktualisieren der Regel');
			throw err;
		}
	},

	// Regel löschen
	async deleteRule(ruleId) {
		try {
			await apiClient.delete(`/rules/${ruleId}`);
			rules.update(current => 
				current.filter(rule => rule.id !== ruleId)
			);
		} catch (err) {
			console.error('Fehler beim Löschen der Regel:', err);
			error.set('Fehler beim Löschen der Regel');
			throw err;
		}
	},

	// Regel aktivieren/deaktivieren
	async toggleRule(ruleId, enabled) {
		try {
			const response = await apiClient.patch(`/rules/${ruleId}`, { enabled });
			rules.update(current => 
				current.map(rule => 
					rule.id === ruleId ? { ...rule, enabled } : rule
				)
			);
			return response.data;
		} catch (err) {
			console.error('Fehler beim Umschalten der Regel:', err);
			error.set('Fehler beim Umschalten der Regel');
			throw err;
		}
	},

	// Regel manuell ausführen
	async executeRule(ruleId) {
		try {
			const response = await apiClient.post(`/rules/${ruleId}/execute`);
			return response.data;
		} catch (err) {
			console.error('Fehler beim Ausführen der Regel:', err);
			error.set('Fehler beim Ausführen der Regel');
			throw err;
		}
	},

	// Regel-Historie laden
	async loadRuleHistory(ruleId, limit = 50) {
		try {
			const response = await apiClient.get(`/rules/${ruleId}/history?limit=${limit}`);
			return response.data;
		} catch (err) {
			console.error('Fehler beim Laden der Regel-Historie:', err);
			error.set('Fehler beim Laden der Regel-Historie');
			throw err;
		}
	},

	// Regel auswählen
	selectRule(rule) {
		selectedRule.set(rule);
	},

	// Fehler zurücksetzen
	clearError() {
		error.set(null);
	}
}; 