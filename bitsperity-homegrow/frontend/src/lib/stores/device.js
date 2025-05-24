import { writable, derived } from 'svelte/store';

// Device Store basierend auf echtem ESP32-System
export const devices = writable([]);
export const selectedDevice = writable(null);
export const deviceStatus = writable('disconnected');

// ESP32 Hardware-Konfiguration (basierend auf pump_manager.cpp)
export const deviceCapabilities = {
	sensors: ['ph', 'tds'], // Nur diese 2 Sensoren!
	pumps: [
		'water_pump',      // Wasserpumpe
		'air_pump',        // Luftpumpe  
		'ph_up_pump',      // pH Up Pumpe
		'ph_down_pump',    // pH Down Pumpe
		'nutrient_pump_1', // Nährstoffpumpe 1
		'nutrient_pump_2', // Nährstoffpumpe 2  
		'nutrient_pump_3'  // Nährstoffpumpe 3
	]
};

// Pumpen-Konfiguration für UI
export const pumpConfig = {
	water_pump: {
		name: 'Wasserpumpe',
		icon: '💧',
		color: 'blue',
		description: 'Hauptwasserzirkulation',
		defaultDuration: 10000, // 10 Sekunden
		category: 'circulation'
	},
	air_pump: {
		name: 'Luftpumpe',
		icon: '🌬️',
		color: 'cyan',
		description: 'Belüftung der Nährlösung',
		defaultDuration: 30000, // 30 Sekunden
		category: 'circulation'
	},
	ph_up_pump: {
		name: 'pH Up Pumpe',
		icon: '⬆️',
		color: 'green',
		description: 'pH-Wert erhöhen',
		defaultDuration: 2000, // 2 Sekunden
		category: 'ph_control'
	},
	ph_down_pump: {
		name: 'pH Down Pumpe',
		icon: '⬇️',
		color: 'red',
		description: 'pH-Wert senken',
		defaultDuration: 2000, // 2 Sekunden
		category: 'ph_control'
	},
	nutrient_pump_1: {
		name: 'Nährstoff A',
		icon: '🌱',
		color: 'emerald',
		description: 'Basis-Nährlösung A',
		defaultDuration: 5000, // 5 Sekunden
		category: 'nutrition'
	},
	nutrient_pump_2: {
		name: 'Nährstoff B',
		icon: '🌿',
		color: 'lime',
		description: 'Basis-Nährlösung B',
		defaultDuration: 5000, // 5 Sekunden
		category: 'nutrition'
	},
	nutrient_pump_3: {
		name: 'Zusätze',
		icon: '⭐',
		color: 'yellow',
		description: 'Zusatznährstoffe',
		defaultDuration: 3000, // 3 Sekunden
		category: 'nutrition'
	}
};

// Derived Stores
export const deviceCount = derived(
	[devices],
	([$devices]) => ({
		total: $devices.length,
		online: $devices.filter(d => d.status === 'online').length,
		offline: $devices.filter(d => d.status === 'offline').length
	})
);

export const onlineDevices = derived(
	[devices],
	([$devices]) => $devices.filter(d => d.status === 'online')
);

export const devicesByType = derived(
	[devices],
	([$devices]) => {
		const byType = {};
		$devices.forEach(device => {
			const type = device.type || 'hydroponic';
			if (!byType[type]) byType[type] = [];
			byType[type].push(device);
		});
		return byType;
	}
);

// Device Actions für API-Integration
export const deviceActions = {
	// Alle Geräte laden
	async loadDevices() {
		try {
			const response = await fetch('/api/devices');
			if (!response.ok) throw new Error('Fehler beim Laden der Geräte');
			
			const data = await response.json();
			if (data.success) {
				devices.set(data.data.devices || []);
				deviceStatus.set('connected');
				return data.data;
			}
		} catch (error) {
			console.error('Fehler beim Laden der Geräte:', error);
			deviceStatus.set('error');
			throw error;
		}
	},

	// Spezifisches Gerät laden
	async loadDevice(deviceId) {
		try {
			const response = await fetch(`/api/devices/${deviceId}`);
			if (!response.ok) throw new Error('Fehler beim Laden des Geräts');
			
			const data = await response.json();
			if (data.success) {
				selectedDevice.set(data.data);
				return data.data;
			}
		} catch (error) {
			console.error('Fehler beim Laden des Geräts:', error);
			throw error;
		}
	},

	// Pumpe aktivieren (Haupt-Feature!)
	async activatePump(deviceId, pumpType, duration = null) {
		try {
			// Verwende Standard-Duration falls nicht angegeben
			const pumpDuration = duration || pumpConfig[pumpType]?.defaultDuration || 5000;
			
			const response = await fetch(`/api/devices/${deviceId}/pumps/${pumpType}/activate`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					duration: pumpDuration
				})
			});
			
			if (!response.ok) throw new Error('Fehler beim Aktivieren der Pumpe');
			
			const data = await response.json();
			if (data.success) {
				// Update lokales Device mit neuer Pump-Info
				devices.update(deviceList => 
					deviceList.map(device => 
						device.deviceId === deviceId 
							? { 
								...device, 
								lastPumpActivation: {
									pumpType,
									duration: pumpDuration,
									timestamp: new Date()
								}
							}
							: device
					)
				);
				
				return data.data;
			}
		} catch (error) {
			console.error('Fehler beim Aktivieren der Pumpe:', error);
			throw error;
		}
	},

	// Command-Historie abrufen
	async getCommandHistory(deviceId, limit = 50) {
		try {
			const response = await fetch(`/api/devices/${deviceId}/commands/history?limit=${limit}`);
			if (!response.ok) throw new Error('Fehler beim Laden der Command-Historie');
			
			const data = await response.json();
			if (data.success) {
				return data.data.commands;
			}
		} catch (error) {
			console.error('Fehler beim Laden der Command-Historie:', error);
			throw error;
		}
	},

	// Quick Actions für häufige Pumpen-Aktivierungen
	async quickPHUp(deviceId, duration = 2000) {
		return this.activatePump(deviceId, 'ph_up_pump', duration);
	},

	async quickPHDown(deviceId, duration = 2000) {
		return this.activatePump(deviceId, 'ph_down_pump', duration);
	},

	async quickNutrients(deviceId, duration = 5000) {
		// Aktiviere Nährstoff A und B gleichzeitig
		const promises = [
			this.activatePump(deviceId, 'nutrient_pump_1', duration),
			this.activatePump(deviceId, 'nutrient_pump_2', duration)
		];
		return Promise.all(promises);
	},

	async quickWaterCirculation(deviceId, duration = 10000) {
		return this.activatePump(deviceId, 'water_pump', duration);
	},

	async quickAeration(deviceId, duration = 30000) {
		return this.activatePump(deviceId, 'air_pump', duration);
	},

	// Gerätestatus prüfen (basierend auf letzten Sensor-Daten)
	async checkDeviceStatus(deviceId) {
		try {
			const response = await fetch(`/api/devices/${deviceId}/sensors`);
			if (!response.ok) return 'offline';
			
			const data = await response.json();
			
			// Gerät ist online wenn es Sensordaten in den letzten 5 Minuten gab
			const hasRecentData = Object.values(data.data || {}).some(sensor => {
				const lastUpdate = new Date(sensor.timestamp);
				const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
				return lastUpdate > fiveMinutesAgo;
			});
			
			return hasRecentData ? 'online' : 'offline';
		} catch (error) {
			console.error('Fehler beim Prüfen des Gerätestatus:', error);
			return 'offline';
		}
	},

	// Bulk-Pumpen-Aktivierung für Wartung
	async maintenanceMode(deviceId, sequence = 'basic') {
		try {
			const sequences = {
				basic: [
					{ pump: 'water_pump', duration: 5000 },
					{ pump: 'air_pump', duration: 10000 }
				],
				full_cycle: [
					{ pump: 'water_pump', duration: 10000 },
					{ pump: 'nutrient_pump_1', duration: 3000 },
					{ pump: 'nutrient_pump_2', duration: 3000 },
					{ pump: 'air_pump', duration: 15000 }
				]
			};

			const steps = sequences[sequence] || sequences.basic;
			const results = [];

			for (const step of steps) {
				const result = await this.activatePump(deviceId, step.pump, step.duration);
				results.push(result);
				
				// Kurze Pause zwischen Pumpen
				await new Promise(resolve => setTimeout(resolve, 1000));
			}

			return results;
		} catch (error) {
			console.error('Fehler im Wartungsmodus:', error);
			throw error;
		}
	}
};

// Hilfsfunktionen
export function getPumpsByCategory(category) {
	return Object.entries(pumpConfig)
		.filter(([_, config]) => config.category === category)
		.map(([pumpType, config]) => ({ pumpType, ...config }));
}

export function formatPumpDuration(durationMs) {
	if (durationMs < 1000) return `${durationMs}ms`;
	if (durationMs < 60000) return `${Math.round(durationMs / 1000)}s`;
	return `${Math.round(durationMs / 60000)}min`;
} 