// API Client for MQTT MCP Frontend
class APIClient {
    constructor() {
        this.baseURL = CONFIG.API_BASE_URL;
        this.timeout = 10000; // 10 seconds
        this.retryAttempts = 3;
        this.retryDelay = 1000; // 1 second
    }

    /**
     * Generic HTTP request with retry logic
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            timeout: this.timeout,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
            try {
                DEBUG(`API Request (attempt ${attempt}):`, { url, config });
                
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), this.timeout);
                
                const response = await fetch(url, {
                    ...config,
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                DEBUG(`API Response:`, data);
                return data;
                
            } catch (error) {
                DEBUG(`API Error (attempt ${attempt}):`, error);
                
                if (attempt === this.retryAttempts) {
                    throw new APIError(`Request failed after ${this.retryAttempts} attempts: ${error.message}`, endpoint, error);
                }
                
                // Wait before retry
                await this.delay(this.retryDelay * attempt);
            }
        }
    }

    /**
     * GET request
     */
    async get(endpoint, params = {}) {
        const searchParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                searchParams.append(key, value.toString());
            }
        });
        
        const queryString = searchParams.toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        
        return this.request(url, { method: 'GET' });
    }

    /**
     * POST request
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * Health check
     */
    async healthCheck() {
        try {
            const health = await this.get('/health');
            return {
                healthy: health.status === 'healthy',
                mongodb: health.mongodb,
                uptime: health.uptime,
                timestamp: health.timestamp
            };
        } catch (error) {
            return {
                healthy: false,
                error: error.message,
                timestamp: new Date()
            };
        }
    }

    /**
     * Get MCP Tools documentation
     */
    async getTools() {
        try {
            return await this.get('/api/tools');
        } catch (error) {
            throw new APIError('Failed to load MCP tools', '/api/tools', error);
        }
    }

    /**
     * Get recent tool calls with filtering
     */
    async getToolCalls(filters = {}) {
        try {
            const params = {
                limit: filters.limit || 50,
                ...(filters.tool && { tool: filters.tool }),
                ...(filters.status && { status: filters.status }),
                ...(filters.session_id && { session_id: filters.session_id })
            };
            
            return await this.get('/api/tool-calls', params);
        } catch (error) {
            throw new APIError('Failed to load tool calls', '/api/tool-calls', error);
        }
    }

    /**
     * Get system logs with filtering
     */
    async getSystemLogs(filters = {}) {
        try {
            const params = {
                limit: filters.limit || 100,
                ...(filters.level && { level: filters.level })
            };
            
            return await this.get('/api/system-logs', params);
        } catch (error) {
            throw new APIError('Failed to load system logs', '/api/system-logs', error);
        }
    }

    /**
     * Get performance metrics
     */
    async getPerformanceMetrics(hours = 24) {
        try {
            return await this.get('/api/performance-metrics', { hours });
        } catch (error) {
            throw new APIError('Failed to load performance metrics', '/api/performance-metrics', error);
        }
    }

    /**
     * Get active connections/sessions
     */
    async getConnections() {
        try {
            return await this.get('/api/connections');
        } catch (error) {
            throw new APIError('Failed to load connections', '/api/connections', error);
        }
    }

    /**
     * Export tool calls as JSON
     */
    async exportToolCalls(filters = {}, format = 'json') {
        try {
            const toolCalls = await this.getToolCalls({ 
                ...filters, 
                limit: 10000 // Get more data for export
            });
            
            if (format === 'json') {
                return this.downloadJSON(toolCalls, 'mqtt-mcp-tool-calls');
            } else if (format === 'csv') {
                return this.downloadCSV(toolCalls, 'mqtt-mcp-tool-calls');
            }
            
            throw new Error(`Unsupported export format: ${format}`);
        } catch (error) {
            throw new APIError('Failed to export tool calls', '/api/tool-calls', error);
        }
    }

    /**
     * Download data as JSON file
     */
    downloadJSON(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { 
            type: 'application/json' 
        });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `${filename}-${new Date().toISOString().slice(0, 19)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        URL.revokeObjectURL(url);
        return true;
    }

    /**
     * Download data as CSV file
     */
    downloadCSV(data, filename) {
        if (!Array.isArray(data) || data.length === 0) {
            throw new Error('No data to export');
        }
        
        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => 
                headers.map(header => {
                    const value = row[header];
                    if (typeof value === 'string' && value.includes(',')) {
                        return `"${value.replace(/"/g, '""')}"`;
                    }
                    return value;
                }).join(',')
            )
        ].join('\n');
        
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `${filename}-${new Date().toISOString().slice(0, 19)}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        URL.revokeObjectURL(url);
        return true;
    }

    /**
     * Utility: Delay function for retry logic
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

/**
 * Custom API Error class
 */
class APIError extends Error {
    constructor(message, endpoint, originalError) {
        super(message);
        this.name = 'APIError';
        this.endpoint = endpoint;
        this.originalError = originalError;
        this.timestamp = new Date();
    }
}

// Create global API client instance
window.API = new APIClient();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { APIClient, APIError };
}

DEBUG('API Client initialized'); 