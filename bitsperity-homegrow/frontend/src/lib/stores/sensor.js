import { writable, derived } from 'svelte/store';
import { apiClient } from '$lib/api/client.js';

// Basis-Sensor Store basierend auf echtem ESP32-System
export const sensorData = writable({});
export const sensorHistory = writable({});
export const sensorStatus = writable('disconnected');

// ESP32 unterstützt nur diese Sensoren (keine Temperatur/Luftfeuchtigkeit!)
export const supportedSensors = ['ph', 'tds'];

// Sensor-Konfiguration für das echte System
export const sensorConfig = {
	ph: {
		name: 'pH-Wert',
		unit: '',
		icon: '🧪',
		color: 'blue',
		optimalRange: { min: 5.5, max: 6.5 },
		warningRange: { min: 5.0, max: 7.0 },
		description: 'Säuregrad der Nährlösung'
	},
	tds: {
		name: 'TDS-Wert',
		unit: 'ppm',
		icon: '⚡',
		color: 'amber',
		optimalRange: { min: 800, max: 1500 },
		warningRange: { min: 600, max: 2000 },
		description: 'Gelöste Feststoffe (Total Dissolved Solids)'
	}
};

// Aktuelle Sensor-Werte (nur pH und TDS)
export const latestSensorReadings = derived(
	[sensorData],
	([$sensorData]) => {
		const latest = {};
		
		supportedSensors.forEach(sensorType => {
			if ($sensorData[sensorType] && $sensorData[sensorType].length > 0) {
				// Neuester Wert
				const latestReading = $sensorData[sensorType][0];
				latest[sensorType] = {
					value: latestReading.value,
					rawValue: latestReading.rawValue || 0,
					timestamp: latestReading.timestamp,
					status: getSensorStatus(sensorType, latestReading.value),
					trend: calculateTrend($sensorData[sensorType])
				};
			}
		});
		
		return latest;
	}
);

// System-Gesundheit basierend auf Sensor-Werten
export const systemHealth = derived(
	[latestSensorReadings],
	([$latestSensorReadings]) => {
		const sensors = Object.values($latestSensorReadings);
		
		if (sensors.length === 0) {
			return {
				status: 'offline',
				score: 0,
				message: 'Keine Sensordaten verfügbar'
			};
		}
		
		const optimalCount = sensors.filter(s => s.status === 'optimal').length;
		const warningCount = sensors.filter(s => s.status === 'warning').length;
		const criticalCount = sensors.filter(s => s.status === 'critical').length;
		
		let score = 0;
		let status = 'critical';
		let message = '';
		
		if (criticalCount > 0) {
			score = 30;
			status = 'critical';
			message = `${criticalCount} kritische Werte`;
		} else if (warningCount > 0) {
			score = 60;
			status = 'warning';
			message = `${warningCount} Werte im Warnbereich`;
		} else if (optimalCount === sensors.length) {
			score = 95;
			status = 'optimal';
			message = 'Alle Werte optimal';
		}
		
		return { status, score, message };
	}
);

// Warnende Sensoren für StatusBar
export const alertingSensors = derived(
	[latestSensorReadings],
	([$latestSensorReadings]) => {
		return Object.entries($latestSensorReadings)
			.filter(([sensorType, reading]) => 
				reading.status === 'warning' || reading.status === 'critical'
			)
			.map(([sensorType, reading]) => ({
				sensorType,
				...reading
			}));
	}
);

// Sensor-Actions für API-Calls
export const sensorActions = {
	// Sensor-Daten laden
	async loadSensorData(deviceId, timeRange = '24h') {
		try {
			const response = await fetch(`/api/devices/${deviceId}/sensors`);
			if (!response.ok) throw new Error('Fehler beim Laden der Sensordaten');
			
			const data = await response.json();
			if (data.success) {
				// Update Store mit aktuellen Werten
				sensorData.update(store => ({
					...store,
					[deviceId]: data.data
				}));
				
				sensorStatus.set('connected');
				return data.data;
			}
		} catch (error) {
			console.error('Fehler beim Laden der Sensordaten:', error);
			sensorStatus.set('error');
			throw error;
		}
	},

	// Sensor-Historie laden
	async loadSensorHistory(deviceId, sensorType, hours = 24) {
		try {
			const response = await fetch(`/api/devices/${deviceId}/sensors/${sensorType}/history?hours=${hours}`);
			if (!response.ok) throw new Error('Fehler beim Laden der Sensor-Historie');
			
			const data = await response.json();
			if (data.success) {
				sensorHistory.update(store => ({
					...store,
					[`${deviceId}_${sensorType}`]: data.data.readings
				}));
				
				return data.data.readings;
			}
		} catch (error) {
			console.error('Fehler beim Laden der Sensor-Historie:', error);
			throw error;
		}
	},

	// Sensor kalibrieren
	async calibrateSensor(deviceId, sensorType, calibrationData) {
		try {
			const response = await fetch(`/api/devices/${deviceId}/calibrate`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					sensorType,
					calibrationData
				})
			});
			
			if (!response.ok) throw new Error('Fehler beim Kalibrieren');
			
			const data = await response.json();
			if (data.success) {
				return data.data;
			}
		} catch (error) {
			console.error('Fehler beim Kalibrieren:', error);
			throw error;
		}
	},

	// Echzeit-Updates simulieren (würde normalerweise über WebSocket kommen)
	startRealtimeUpdates(deviceId) {
		const interval = setInterval(async () => {
			try {
				await this.loadSensorData(deviceId);
			} catch (error) {
				console.error('Fehler bei Echtzeit-Updates:', error);
			}
		}, 5000); // Alle 5 Sekunden

		return () => clearInterval(interval);
	}
};

// Hilfsfunktionen
function getSensorStatus(sensorType, value) {
	const config = sensorConfig[sensorType];
	if (!config) return 'unknown';
	
	const { optimalRange, warningRange } = config;
	
	if (value >= optimalRange.min && value <= optimalRange.max) {
		return 'optimal';
	} else if (value >= warningRange.min && value <= warningRange.max) {
		return 'warning';
	} else {
		return 'critical';
	}
}

function calculateTrend(readings) {
	if (!readings || readings.length < 2) return 'stable';
	
	const recent = readings.slice(0, 5); // Letzten 5 Werte
	if (recent.length < 2) return 'stable';
	
	const latest = recent[0].value;
	const previous = recent[recent.length - 1].value;
	const change = latest - previous;
	
	if (Math.abs(change) < 0.1) return 'stable';
	return change > 0 ? 'rising' : 'falling';
} 