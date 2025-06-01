// WebSocket Client for Real-time Updates
class WebSocketClient {
    constructor() {
        this.url = CONFIG.WEBSOCKET_URL;
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.maxReconnectDelay = 30000; // Max 30 seconds
        this.eventHandlers = new Map();
        this.isReconnecting = false;
        
        // Bind methods to preserve context
        this.handleOpen = this.handleOpen.bind(this);
        this.handleMessage = this.handleMessage.bind(this);
        this.handleClose = this.handleClose.bind(this);
        this.handleError = this.handleError.bind(this);
    }

    /**
     * Connect to WebSocket server
     */
    connect() {
        if (this.socket && (this.socket.readyState === WebSocket.CONNECTING || this.socket.readyState === WebSocket.OPEN)) {
            DEBUG('WebSocket already connecting or connected');
            return;
        }

        try {
            DEBUG('Connecting to WebSocket:', this.url);
            this.socket = new WebSocket(this.url);
            
            this.socket.addEventListener('open', this.handleOpen);
            this.socket.addEventListener('message', this.handleMessage);
            this.socket.addEventListener('close', this.handleClose);
            this.socket.addEventListener('error', this.handleError);
            
        } catch (error) {
            DEBUG('WebSocket connection error:', error);
            this.handleConnectionError(error);
        }
    }

    /**
     * Disconnect from WebSocket server
     */
    disconnect() {
        this.isReconnecting = false;
        
        if (this.socket) {
            this.socket.removeEventListener('open', this.handleOpen);
            this.socket.removeEventListener('message', this.handleMessage);
            this.socket.removeEventListener('close', this.handleClose);
            this.socket.removeEventListener('error', this.handleError);
            
            if (this.socket.readyState === WebSocket.OPEN) {
                this.socket.close();
            }
            
            this.socket = null;
        }
        
        this.isConnected = false;
        this.emit('disconnected');
    }

    /**
     * Handle WebSocket open event
     */
    handleOpen(event) {
        DEBUG('WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000; // Reset delay
        this.isReconnecting = false;
        
        this.emit('connected', {
            timestamp: new Date(),
            reconnected: this.reconnectAttempts > 0
        });
        
        // Update UI connection status
        this.updateConnectionStatus('connected');
    }

    /**
     * Handle WebSocket message event
     */
    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            DEBUG('WebSocket message received:', data);
            
            // Emit specific event based on message type
            if (data.type) {
                this.emit(data.type, data.payload || data);
            }
            
            // Also emit generic message event
            this.emit('message', data);
            
        } catch (error) {
            DEBUG('Error parsing WebSocket message:', error, event.data);
        }
    }

    /**
     * Handle WebSocket close event
     */
    handleClose(event) {
        DEBUG('WebSocket disconnected:', { code: event.code, reason: event.reason });
        this.isConnected = false;
        
        this.emit('disconnected', {
            code: event.code,
            reason: event.reason,
            timestamp: new Date()
        });
        
        // Update UI connection status
        this.updateConnectionStatus('disconnected');
        
        // Attempt reconnection if not intentionally closed
        if (event.code !== 1000 && !this.isReconnecting) { // 1000 = normal closure
            this.attemptReconnect();
        }
    }

    /**
     * Handle WebSocket error event
     */
    handleError(event) {
        DEBUG('WebSocket error:', event);
        
        this.emit('error', {
            error: event,
            timestamp: new Date()
        });
        
        this.updateConnectionStatus('error');
        this.handleConnectionError(event);
    }

    /**
     * Handle connection errors and failures
     */
    handleConnectionError(error) {
        if (!this.isReconnecting) {
            this.attemptReconnect();
        }
    }

    /**
     * Attempt to reconnect with exponential backoff
     */
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            DEBUG('Max reconnection attempts reached');
            this.updateConnectionStatus('failed');
            this.emit('reconnect_failed');
            return;
        }

        this.isReconnecting = true;
        this.reconnectAttempts++;
        
        DEBUG(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${this.reconnectDelay}ms`);
        
        this.updateConnectionStatus('reconnecting');
        
        this.emit('reconnecting', {
            attempt: this.reconnectAttempts,
            maxAttempts: this.maxReconnectAttempts,
            delay: this.reconnectDelay
        });

        setTimeout(() => {
            if (this.isReconnecting) {
                this.connect();
                
                // Exponential backoff with jitter
                this.reconnectDelay = Math.min(
                    this.reconnectDelay * 2 + Math.random() * 1000,
                    this.maxReconnectDelay
                );
            }
        }, this.reconnectDelay);
    }

    /**
     * Send message to server
     */
    send(data) {
        if (!this.isConnected || !this.socket) {
            DEBUG('Cannot send message: WebSocket not connected');
            return false;
        }

        try {
            const message = typeof data === 'string' ? data : JSON.stringify(data);
            this.socket.send(message);
            DEBUG('WebSocket message sent:', data);
            return true;
        } catch (error) {
            DEBUG('Error sending WebSocket message:', error);
            return false;
        }
    }

    /**
     * Add event listener
     */
    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }

    /**
     * Remove event listener
     */
    off(event, handler) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    /**
     * Emit event to all listeners
     */
    emit(event, data) {
        if (this.eventHandlers.has(event)) {
            this.eventHandlers.get(event).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    DEBUG('Error in event handler:', error);
                }
            });
        }
    }

    /**
     * Update connection status in UI
     */
    updateConnectionStatus(status) {
        const statusIndicator = document.getElementById('statusIndicator');
        const statusText = document.getElementById('statusText');
        
        if (!statusIndicator || !statusText) return;
        
        // Remove all status classes
        statusIndicator.className = 'status-indicator';
        
        switch (status) {
            case 'connected':
                statusIndicator.classList.add('connected');
                statusText.textContent = 'Connected';
                break;
                
            case 'disconnected':
                statusText.textContent = 'Disconnected';
                break;
                
            case 'reconnecting':
                statusText.textContent = 'Reconnecting...';
                break;
                
            case 'error':
                statusIndicator.classList.add('error');
                statusText.textContent = 'Connection Error';
                break;
                
            case 'failed':
                statusIndicator.classList.add('error');
                statusText.textContent = 'Connection Failed';
                break;
                
            default:
                statusText.textContent = 'Connecting...';
        }
    }

    /**
     * Get connection status
     */
    getStatus() {
        return {
            connected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            reconnecting: this.isReconnecting,
            readyState: this.socket ? this.socket.readyState : WebSocket.CLOSED
        };
    }

    /**
     * Setup real-time data handlers for the application
     */
    setupDataHandlers() {
        // Handle tool call updates
        this.on('tool_call_update', (data) => {
            DEBUG('Tool call update received:', data);
            if (window.LiveMonitor) {
                window.LiveMonitor.handleToolCallUpdate(data);
            }
        });

        // Handle system log updates
        this.on('system_log_update', (data) => {
            DEBUG('System log update received:', data);
            if (window.SystemLogs && window.SystemLogs.isVisible()) {
                window.SystemLogs.handleLogUpdate(data);
            }
        });

        // Handle performance updates
        this.on('performance_update', (data) => {
            DEBUG('Performance update received:', data);
            if (window.HealthDashboard) {
                window.HealthDashboard.handlePerformanceUpdate(data);
            }
        });

        // Handle connection updates
        this.on('connected', () => {
            if (window.UI) {
                window.UI.showToast(CONFIG.SUCCESS.CONNECTION_ESTABLISHED, 'success');
            }
        });

        // Handle disconnection
        this.on('disconnected', () => {
            if (window.UI) {
                window.UI.showToast(CONFIG.ERRORS.WEBSOCKET_ERROR, 'warning');
            }
        });

        // Handle reconnection failures
        this.on('reconnect_failed', () => {
            if (window.UI) {
                window.UI.showToast('WebSocket Reconnection failed - some features may not work', 'error');
            }
        });
    }
}

// Create global WebSocket client instance
window.WS = new WebSocketClient();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketClient;
}

DEBUG('WebSocket Client initialized'); 