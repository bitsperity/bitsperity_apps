import { browser } from '$app/environment';
import { goto } from '$app/navigation';

class ApiClient {
	constructor() {
		// SIMPLE: Browser ALWAYS uses localhost, Server uses Docker
		if (browser) {
			this.baseURL = 'http://localhost:4001';
			this.fallbackUrls = ['http://127.0.0.1:4001'];
		} else {
			this.baseURL = process.env.API_URL || 'http://host.docker.internal:4001';
		}
		
		this.token = null;
		
		if (browser) {
			this.token = localStorage.getItem('authToken');
		}
		
		console.log('🚀 ApiClient FIXED - baseURL:', this.baseURL);
		if (this.fallbackUrls) {
			console.log('🔄 Fallback URLs:', this.fallbackUrls);
		}
	}

	// Set authentication token
	setToken(token) {
		this.token = token;
		if (browser) {
			if (token) {
				localStorage.setItem('authToken', token);
			} else {
				localStorage.removeItem('authToken');
			}
		}
	}

	// Get authorization headers
	getHeaders() {
		const headers = {
			'Content-Type': 'application/json'
		};

		if (this.token) {
			headers.Authorization = `Bearer ${this.token}`;
		}

		return headers;
	}

	// Generic request method
	async request(endpoint, options = {}) {
		const urls = [this.baseURL];
		
		// Add fallback URLs if available (development mode)
		if (this.fallbackUrls) {
			urls.push(...this.fallbackUrls);
		}
		
		let lastError;
		
		// Try each URL until one works
		for (const baseUrl of urls) {
			const url = `${baseUrl}/api${endpoint}`;
			
			const config = {
				headers: this.getHeaders(),
				...options
			};

			try {
				const response = await fetch(url, config);
				
				// Handle authentication errors
				if (response.status === 401) {
					this.setToken(null);
					if (browser) {
						goto('/auth/login');
					}
					throw new Error('Authentifizierung erforderlich');
				}

				// Handle other errors
				if (!response.ok) {
					const errorData = await response.json().catch(() => ({}));
					throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
				}

				// Success! Update baseURL if we used a fallback
				if (baseUrl !== this.baseURL) {
					console.log(`ApiClient: Switched to working URL: ${baseUrl}`);
					this.baseURL = baseUrl;
				}

				// Handle empty responses
				const contentType = response.headers.get('content-type');
				if (contentType && contentType.includes('application/json')) {
					return await response.json();
				} else {
					return response;
				}
			} catch (error) {
				lastError = error;
				console.warn(`API request failed for ${url}:`, error.message);
				
				// If this is likely an ad-blocker error, try next URL
				if (error.message.includes('Failed to fetch') || 
					error.message.includes('Network request failed') ||
					error.message.includes('ERR_BLOCKED_BY_CLIENT')) {
					continue;
				}
				
				// For other errors, don't try fallbacks
				break;
			}
		}
		
		// All URLs failed
		console.error(`API Error (${endpoint}): All URLs failed. Last error:`, lastError);
		
		// Provide helpful error message for ad-blocker issues
		if (lastError && (lastError.message.includes('Failed to fetch') || 
			lastError.message.includes('ERR_BLOCKED_BY_CLIENT'))) {
			throw new Error('API nicht erreichbar. Möglicherweise wird die Verbindung von einem Ad-Blocker blockiert. Bitte deaktivieren Sie Ad-Blocker für localhost.');
		}
		
		throw lastError || new Error('API nicht erreichbar');
	}

	// HTTP Methods
	async get(endpoint, options = {}) {
		const { params, ...otherOptions } = options;
		
		let url = endpoint;
		if (params) {
			const searchParams = new URLSearchParams();
			Object.entries(params).forEach(([key, value]) => {
				if (value !== null && value !== undefined) {
					searchParams.append(key, value.toString());
				}
			});
			url += `?${searchParams.toString()}`;
		}

		return this.request(url, {
			method: 'GET',
			...otherOptions
		});
	}

	async post(endpoint, data, options = {}) {
		return this.request(endpoint, {
			method: 'POST',
			body: JSON.stringify(data),
			...options
		});
	}

	async put(endpoint, data, options = {}) {
		return this.request(endpoint, {
			method: 'PUT',
			body: JSON.stringify(data),
			...options
		});
	}

	async patch(endpoint, data, options = {}) {
		return this.request(endpoint, {
			method: 'PATCH',
			body: JSON.stringify(data),
			...options
		});
	}

	async delete(endpoint, options = {}) {
		return this.request(endpoint, {
			method: 'DELETE',
			...options
		});
	}

	// Authentication methods
	async login(credentials) {
		const response = await this.post('/auth/login', credentials);
		if (response.token) {
			this.setToken(response.token);
		}
		return response;
	}

	async logout() {
		try {
			await this.post('/auth/logout');
		} catch (error) {
			console.warn('Logout error:', error);
		} finally {
			this.setToken(null);
		}
	}

	async refreshToken() {
		try {
			const response = await this.post('/auth/refresh');
			if (response.token) {
				this.setToken(response.token);
			}
			return response;
		} catch (error) {
			this.setToken(null);
			throw error;
		}
	}

	// Check if user is authenticated
	isAuthenticated() {
		return !!this.token;
	}

	// Check if token exists
	hasToken() {
		return !!this.token;
	}

	// Clear token
	clearToken() {
		this.setToken(null);
	}
}

// Export singleton instance
export const apiClient = new ApiClient(); 