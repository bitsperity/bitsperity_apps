class MongoMCPApp {
    constructor() {
        this.connections = new Map();
        this.recentQueries = [];
        this.ws = null;
        this.stats = {
            totalConnections: 0,
            totalQueries: 0,
            avgResponseTime: 0,
            uptime: 0
        };
        this.refreshInterval = 10000; // 10 seconds
        this.refreshTimer = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.connectWebSocket();
        this.startRefreshTimer();
        this.updateStatus('ready', 'Bereit für Verbindungen');
    }

    setupEventListeners() {
        // Mobile menu
        const menuToggle = document.getElementById('menuToggle');
        const closeMenu = document.getElementById('closeMenu');
        const menuOverlay = document.getElementById('menuOverlay');
        const mobileMenu = document.getElementById('mobileMenu');
        const menuPanel = document.getElementById('menuPanel');

        menuToggle?.addEventListener('click', () => this.openMobileMenu());
        closeMenu?.addEventListener('click', () => this.closeMobileMenu());
        menuOverlay?.addEventListener('click', () => this.closeMobileMenu());

        // Settings
        const refreshInterval = document.getElementById('refreshInterval');
        refreshInterval?.addEventListener('change', (e) => {
            this.refreshInterval = parseInt(e.target.value);
            this.restartRefreshTimer();
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeMobileMenu();
            }
        });
    }

    openMobileMenu() {
        const mobileMenu = document.getElementById('mobileMenu');
        const menuPanel = document.getElementById('menuPanel');
        
        mobileMenu.classList.remove('hidden');
        setTimeout(() => {
            menuPanel.classList.remove('translate-x-full');
        }, 10);
    }

    closeMobileMenu() {
        const mobileMenu = document.getElementById('mobileMenu');
        const menuPanel = document.getElementById('menuPanel');
        
        menuPanel.classList.add('translate-x-full');
        setTimeout(() => {
            mobileMenu.classList.add('hidden');
        }, 300);
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.updateStatus('connected', 'WebSocket verbunden');
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateStatus('disconnected', 'WebSocket getrennt');
                // Attempt to reconnect after 5 seconds
                setTimeout(() => this.connectWebSocket(), 5000);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateStatus('error', 'WebSocket Fehler');
            };
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.updateStatus('error', 'Verbindung fehlgeschlagen');
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'connection_update':
                this.updateConnection(data.connection);
                break;
            case 'connection_closed':
                this.removeConnection(data.session_id);
                break;
            case 'query_executed':
                this.addRecentQuery(data.query);
                break;
            case 'stats_update':
                this.updateStats(data.stats);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    async fetchData() {
        try {
            this.showLoading(true);
            
            // Fetch connections
            const connectionsResponse = await fetch('/api/connections');
            if (connectionsResponse.ok) {
                const connectionsData = await connectionsResponse.json();
                this.updateConnectionsDisplay(connectionsData.active_connections || []);
                this.updateStats(connectionsData.stats || {});
            }
            
            // Fetch recent queries
            const queriesResponse = await fetch('/api/recent-queries');
            if (queriesResponse.ok) {
                const queriesData = await queriesResponse.json();
                this.updateRecentQueries(queriesData.queries || []);
            }
            
        } catch (error) {
            console.error('Error fetching data:', error);
            this.showToast('Fehler beim Laden der Daten', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    updateConnectionsDisplay(connections) {
        const container = document.getElementById('connectionsContainer');
        const noConnections = document.getElementById('noConnections');
        
        if (connections.length === 0) {
            noConnections.classList.remove('hidden');
            // Remove all connection cards
            container.querySelectorAll('.connection-card').forEach(card => card.remove());
        } else {
            noConnections.classList.add('hidden');
            
            // Update existing connections and add new ones
            connections.forEach(conn => this.updateConnectionCard(conn));
            
            // Remove connections that are no longer active
            const activeSessionIds = new Set(connections.map(c => c.session_id));
            container.querySelectorAll('.connection-card').forEach(card => {
                const sessionId = card.dataset.sessionId;
                if (!activeSessionIds.has(sessionId)) {
                    card.remove();
                }
            });
        }
        
        // Update connection count
        document.getElementById('connectionCount').textContent = 
            `${connections.length} connection${connections.length !== 1 ? 's' : ''}`;
    }

    updateConnectionCard(connection) {
        const container = document.getElementById('connectionsContainer');
        let card = container.querySelector(`[data-session-id="${connection.session_id}"]`);
        
        if (!card) {
            card = this.createConnectionCard(connection);
            container.appendChild(card);
        } else {
            // Update existing card
            this.updateConnectionCardContent(card, connection);
        }
    }

    createConnectionCard(connection) {
        const card = document.createElement('div');
        card.className = 'connection-card bg-gray-800 rounded-lg p-4 border border-gray-700';
        card.dataset.sessionId = connection.session_id;
        
        this.updateConnectionCardContent(card, connection);
        return card;
    }

    updateConnectionCardContent(card, connection) {
        const lastUsed = this.formatTimeAgo(connection.last_used);
        const uptime = this.formatDuration(connection.age_seconds);
        const hostname = connection.parsed_info?.hostname || 'Unknown';
        
        card.innerHTML = `
            <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                    <div class="flex items-center space-x-2 mb-2">
                        <div class="w-3 h-3 bg-green-400 rounded-full"></div>
                        <h3 class="font-medium text-sm truncate">${hostname}</h3>
                    </div>
                    <p class="text-xs text-gray-400 truncate mb-1">
                        Session: ${connection.session_id}
                    </p>
                    <div class="flex items-center justify-between text-xs text-gray-500">
                        <span>Aktiv seit ${uptime}</span>
                        <span>Zuletzt: ${lastUsed}</span>
                    </div>
                </div>
                <button class="ml-3 p-1 text-gray-400 hover:text-red-400 transition-colors" 
                        onclick="app.closeConnection('${connection.session_id}')">
                    <i data-lucide="x" class="w-4 h-4"></i>
                </button>
            </div>
        `;
        
        // Re-initialize icons for the new content
        lucide.createIcons();
    }

    updateRecentQueries(queries) {
        const container = document.getElementById('recentQueries');
        const noQueries = document.getElementById('noQueries');
        
        if (queries.length === 0) {
            noQueries.classList.remove('hidden');
            container.querySelectorAll('.query-item').forEach(item => item.remove());
            return;
        }
        
        noQueries.classList.add('hidden');
        
        // Clear existing queries
        container.querySelectorAll('.query-item').forEach(item => item.remove());
        
        // Add recent queries (limit to 5)
        queries.slice(0, 5).forEach(query => {
            const queryItem = this.createQueryItem(query);
            container.appendChild(queryItem);
        });
    }

    createQueryItem(query) {
        const item = document.createElement('div');
        item.className = 'query-item bg-gray-800 rounded-lg p-3 border border-gray-700';
        
        const timeAgo = this.formatTimeAgo(query.timestamp);
        const operation = query.operation || 'Query';
        const database = query.database || 'Unknown';
        const collection = query.collection || '';
        
        item.innerHTML = `
            <div class="flex items-start space-x-3">
                <div class="w-8 h-8 bg-purple-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                    <i data-lucide="search" class="w-4 h-4 text-purple-400"></i>
                </div>
                <div class="flex-1 min-w-0">
                    <div class="flex items-center justify-between mb-1">
                        <h4 class="text-sm font-medium truncate">${operation}</h4>
                        <span class="text-xs text-gray-500">${timeAgo}</span>
                    </div>
                    <p class="text-xs text-gray-400 truncate">
                        ${database}${collection ? '.' + collection : ''}
                    </p>
                    ${query.duration ? `<p class="text-xs text-gray-500 mt-1">${query.duration}ms</p>` : ''}
                </div>
            </div>
        `;
        
        lucide.createIcons();
        return item;
    }

    updateStats(stats) {
        if (stats.total_connections !== undefined) {
            document.getElementById('totalConnections').textContent = stats.total_connections;
        }
        if (stats.total_queries !== undefined) {
            document.getElementById('totalQueries').textContent = stats.total_queries;
        }
        if (stats.avg_response_time !== undefined) {
            document.getElementById('avgResponseTime').textContent = 
                stats.avg_response_time ? `${Math.round(stats.avg_response_time)}` : '-';
        }
        if (stats.uptime !== undefined) {
            document.getElementById('uptime').textContent = 
                this.formatDuration(stats.uptime);
        }
    }

    updateStatus(status, message) {
        const indicator = document.getElementById('statusIndicator');
        const text = document.getElementById('statusText');
        
        if (indicator && text) {
            // Remove all status classes
            indicator.className = 'w-2 h-2 rounded-full';
            
            switch (status) {
                case 'connected':
                    indicator.classList.add('bg-green-400');
                    break;
                case 'ready':
                    indicator.classList.add('bg-blue-400');
                    break;
                case 'error':
                    indicator.classList.add('bg-red-400');
                    break;
                case 'disconnected':
                    indicator.classList.add('bg-yellow-400', 'animate-pulse');
                    break;
                default:
                    indicator.classList.add('bg-gray-400');
            }
            
            text.textContent = message;
        }
    }

    async closeConnection(sessionId) {
        try {
            const response = await fetch(`/api/connections/${sessionId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.showToast('Verbindung geschlossen', 'success');
                this.removeConnection(sessionId);
            } else {
                this.showToast('Fehler beim Schließen der Verbindung', 'error');
            }
        } catch (error) {
            console.error('Error closing connection:', error);
            this.showToast('Fehler beim Schließen der Verbindung', 'error');
        }
    }

    removeConnection(sessionId) {
        const card = document.querySelector(`[data-session-id="${sessionId}"]`);
        if (card) {
            card.remove();
        }
        
        // Update connection count
        const remainingConnections = document.querySelectorAll('.connection-card').length;
        document.getElementById('connectionCount').textContent = 
            `${remainingConnections} connection${remainingConnections !== 1 ? 's' : ''}`;
        
        // Show no connections message if none left
        if (remainingConnections === 0) {
            document.getElementById('noConnections').classList.remove('hidden');
        }
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast bg-surface border rounded-lg p-4 shadow-lg transition-all duration-300 transform translate-x-full`;
        
        let iconName = 'info';
        let colorClass = 'border-blue-500';
        
        switch (type) {
            case 'success':
                iconName = 'check-circle';
                colorClass = 'border-green-500';
                break;
            case 'error':
                iconName = 'alert-circle';
                colorClass = 'border-red-500';
                break;
            case 'warning':
                iconName = 'alert-triangle';
                colorClass = 'border-yellow-500';
                break;
        }
        
        toast.classList.add(colorClass);
        toast.innerHTML = `
            <div class="flex items-center space-x-3">
                <i data-lucide="${iconName}" class="w-5 h-5 flex-shrink-0"></i>
                <span class="text-sm">${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-auto">
                    <i data-lucide="x" class="w-4 h-4"></i>
                </button>
            </div>
        `;
        
        container.appendChild(toast);
        lucide.createIcons();
        
        // Animate in
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 10);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.classList.add('translate-x-full');
                setTimeout(() => toast.remove(), 300);
            }
        }, 5000);
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (show) {
            overlay.classList.remove('hidden');
        } else {
            overlay.classList.add('hidden');
        }
    }

    startRefreshTimer() {
        this.refreshTimer = setInterval(() => {
            this.fetchData();
        }, this.refreshInterval);
        
        // Initial fetch
        this.fetchData();
    }

    restartRefreshTimer() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
        this.startRefreshTimer();
    }

    formatTimeAgo(timestamp) {
        if (!timestamp) return 'Unbekannt';
        
        const now = Date.now() / 1000;
        const diff = now - timestamp;
        
        if (diff < 60) return 'Gerade eben';
        if (diff < 3600) return `${Math.floor(diff / 60)}m`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
        return `${Math.floor(diff / 86400)}d`;
    }

    formatDuration(seconds) {
        if (!seconds || seconds < 0) return '0s';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) return `${hours}h ${minutes}m`;
        if (minutes > 0) return `${minutes}m ${secs}s`;
        return `${secs}s`;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new MongoMCPApp();
});

// Handle mobile viewport height
function setViewportHeight() {
    const vh = window.innerHeight * 0.01;
    document.documentElement.style.setProperty('--vh', `${vh}px`);
}

window.addEventListener('resize', setViewportHeight);
setViewportHeight(); 