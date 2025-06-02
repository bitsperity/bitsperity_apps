// Main Application Controller for MQTT MCP Frontend
class MQTTMCPApp {
    constructor() {
        this.initialized = false;
        this.currentTab = 'tools';
        this.tabs = new Map();
        this.updateIntervals = new Map();
        
        // Bind methods
        this.handleTabClick = this.handleTabClick.bind(this);
        this.handleLogsToggle = this.handleLogsToggle.bind(this);
        this.handleTutorialClick = this.handleTutorialClick.bind(this);
        this.handleVisibilityChange = this.handleVisibilityChange.bind(this);
    }

    /**
     * Initialize the application
     */
    async init() {
        try {
            DEBUG('Initializing MQTT MCP Frontend...');
            
            // Show loading
            UI.showLoading('Initializing application...');
            
            // Initialize core systems
            await this.initializeCore();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Initialize tab system
            this.initializeTabs();
            
            // Load initial data
            await this.loadInitialData();
            
            // Setup real-time updates
            this.setupRealTimeUpdates();
            
            // Restore user preferences
            this.restoreUserPreferences();
            
            // Hide loading
            UI.hideLoading();
            
            this.initialized = true;
            DEBUG('Application initialized successfully');
            
            // Show welcome message
            if (this.isFirstVisit()) {
                this.showWelcomeMessage();
            }
            
        } catch (error) {
            DEBUG('Application initialization failed:', error);
            UI.hideLoading();
            UI.showToast('Application initialization failed: ' + error.message, 'error');
        }
    }

    /**
     * Initialize core systems
     */
    async initializeCore() {
        // Check API connectivity
        const health = await API.healthCheck();
        if (!health.healthy) {
            throw new Error('Backend API is not available');
        }
        
        // Connect WebSocket
        WS.setupDataHandlers();
        WS.connect();
        
        // Initialize state management if needed
        if (window.StateManager) {
            window.StateManager.init();
        }
        
        DEBUG('Core systems initialized');
    }

    /**
     * Setup global event listeners
     */
    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', this.handleTabClick);
        });
        
        // System logs toggle
        const logsToggle = document.getElementById('showLogsCheckbox');
        if (logsToggle) {
            logsToggle.addEventListener('change', this.handleLogsToggle);
        }
        
        // Tutorial button
        const tutorialBtn = document.getElementById('tutorialBtn');
        if (tutorialBtn) {
            tutorialBtn.addEventListener('click', this.handleTutorialClick);
        }
        
        // Page visibility change (pause updates when not visible)
        document.addEventListener('visibilitychange', this.handleVisibilityChange);
        
        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));
        
        // Window beforeunload (cleanup)
        window.addEventListener('beforeunload', this.cleanup.bind(this));
        
        DEBUG('Event listeners setup complete');
    }

    /**
     * Initialize tab system
     */
    initializeTabs() {
        // Simple tab system - no modules needed
        // All functionality is built into the main app
        
        // Show initial tab
        this.showTab(this.currentTab);
        
        DEBUG('Tab system initialized (simplified)');
    }

    /**
     * Load initial data for all components
     */
    async loadInitialData() {
        try {
            // Load tools documentation directly
            await this.loadTools();
            
            // Load initial monitoring data
            await this.loadToolCalls();
            
            // Load health data
            await this.loadHealthData();
            
            DEBUG('Initial data loaded');
        } catch (error) {
            DEBUG('Error loading initial data:', error);
            UI.showToast('Failed to load initial data: ' + error.message, 'error');
        }
    }

    /**
     * Load tools documentation
     */
    async loadTools() {
        try {
            DEBUG('Loading tools...');
            const tools = await API.getTools();
            
            this.renderTools(tools);
            this.setupToolSearch(tools);
            
            DEBUG(`Loaded ${tools.length} tools`);
        } catch (error) {
            DEBUG('Error loading tools:', error);
            UI.showToast('Failed to load tools: ' + error.message, 'error');
        }
    }

    /**
     * Render tools in the grid
     */
    renderTools(tools) {
        const toolsGrid = document.getElementById('toolsGrid');
        if (!toolsGrid) return;

        toolsGrid.innerHTML = tools.map(tool => `
            <div class="tool-card" data-category="${tool.category}">
                <div class="tool-header">
                    <h3>${tool.name}</h3>
                    <span class="category-badge">${tool.category}</span>
                </div>
                <div class="tool-description">
                    ${tool.description}
                </div>
                <div class="tool-parameters">
                    <h4>Parameters:</h4>
                    <ul>
                        ${Object.entries(tool.parameters || {}).map(([key, desc]) => 
                            `<li><code>${key}</code>: ${desc}</li>`
                        ).join('')}
                    </ul>
                </div>
                <div class="tool-example">
                    <h4>Example:</h4>
                    <code class="example-code">${tool.example}</code>
                    <button class="btn-copy" onclick="UI.copyToClipboard('${tool.example.replace(/'/g, "\\'")}')">📋 Copy</button>
                </div>
            </div>
        `).join('');
    }

    /**
     * Setup tool search functionality
     */
    setupToolSearch(tools) {
        const searchInput = document.getElementById('toolSearch');
        const categoryFilter = document.getElementById('categoryFilter');
        
        const filterTools = () => {
            const searchTerm = searchInput?.value.toLowerCase() || '';
            const selectedCategory = categoryFilter?.value || '';
            
            const toolCards = document.querySelectorAll('.tool-card');
            toolCards.forEach(card => {
                const toolName = card.querySelector('h3').textContent.toLowerCase();
                const toolDescription = card.querySelector('.tool-description').textContent.toLowerCase();
                const toolCategory = card.getAttribute('data-category');
                
                const matchesSearch = toolName.includes(searchTerm) || toolDescription.includes(searchTerm);
                const matchesCategory = !selectedCategory || toolCategory === selectedCategory;
                
                card.style.display = matchesSearch && matchesCategory ? 'block' : 'none';
            });
        };

        if (searchInput) {
            searchInput.addEventListener('input', UI.debounce(filterTools, 300));
        }
        
        if (categoryFilter) {
            categoryFilter.addEventListener('change', filterTools);
        }
    }

    /**
     * Load tool calls for monitoring
     */
    async loadToolCalls() {
        try {
            const response = await API.getToolCalls({ limit: 50 });
            this.renderToolCalls(response.tool_calls || []);
        } catch (error) {
            DEBUG('Error loading tool calls:', error);
        }
    }

    /**
     * Render tool calls in monitor tab
     */
    renderToolCalls(toolCalls) {
        const streamContainer = document.getElementById('toolCallsStream');
        if (!streamContainer) return;

        if (toolCalls.length === 0) {
            streamContainer.innerHTML = '<p class="no-data">No tool calls yet. Use the MQTT MCP tools to see monitoring data here.</p>';
            return;
        }

        streamContainer.innerHTML = toolCalls.map(call => `
            <div class="tool-call-item ${call.success ? 'success' : 'error'}">
                <div class="call-header">
                    <span class="tool-name">${call.tool_name}</span>
                    <span class="timestamp">${UI.formatTimestamp(call.timestamp)}</span>
                    <span class="status ${call.success ? 'success' : 'error'}">
                        ${call.success ? '✅' : '❌'}
                    </span>
                </div>
                <div class="call-details">
                    <div class="duration">Duration: ${UI.formatDuration(call.duration_ms)}</div>
                    <div class="result-size">Size: ${UI.formatFileSize(call.result_size_kb * 1024)}</div>
                    ${call.error ? `<div class="error-message">Error: ${call.error}</div>` : ''}
                </div>
                <div class="call-params">
                    <details>
                        <summary>Parameters</summary>
                        <pre>${JSON.stringify(call.params, null, 2)}</pre>
                    </details>
                </div>
            </div>
        `).join('');
    }

    /**
     * Load health data
     */
    async loadHealthData() {
        try {
            const health = await API.getHealth();
            this.renderHealthData(health);
        } catch (error) {
            DEBUG('Error loading health data:', error);
        }
    }

    /**
     * Render health data
     */
    renderHealthData(health) {
        const healthOverview = document.getElementById('healthOverview');
        if (!healthOverview) return;

        const dbConnected = health.database?.connected;
        const recentCalls = health.mcp_server?.recent_tool_calls || 0;
        const recentErrors = health.mcp_server?.recent_errors || 0;

        healthOverview.innerHTML = `
            <div class="health-cards">
                <div class="health-card ${dbConnected ? 'healthy' : 'unhealthy'}">
                    <h3>Database</h3>
                    <div class="health-value">${dbConnected ? 'Connected' : 'Disconnected'}</div>
                </div>
                <div class="health-card">
                    <h3>Recent Tool Calls</h3>
                    <div class="health-value">${recentCalls}</div>
                    <div class="health-subtitle">Last hour</div>
                </div>
                <div class="health-card ${recentErrors === 0 ? 'healthy' : 'warning'}">
                    <h3>Recent Errors</h3>
                    <div class="health-value">${recentErrors}</div>
                    <div class="health-subtitle">Last hour</div>
                </div>
            </div>
        `;
    }

    /**
     * Setup real-time updates
     */
    setupRealTimeUpdates() {
        // Performance updates every 30 seconds
        this.updateIntervals.set('health', setInterval(() => {
            if (!document.hidden) {
                this.loadHealthData();
            }
        }, 30000));
        
        // Tool calls updates every 10 seconds
        this.updateIntervals.set('toolcalls', setInterval(() => {
            if (!document.hidden && this.currentTab === 'monitor') {
                this.loadToolCalls();
            }
        }, 10000));
        
        DEBUG('Real-time updates setup complete');
    }

    /**
     * Handle tab navigation
     */
    handleTabClick(event) {
        event.preventDefault();
        const tabName = event.target.getAttribute('data-tab');
        
        if (tabName) {
            this.showTab(tabName);
        }
    }

    /**
     * Show specific tab
     */
    showTab(tabName) {
        DEBUG(`Switching to tab: ${tabName}`);
        
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('data-tab') === tabName) {
                item.classList.add('active');
            }
        });
        
        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        const targetContent = document.getElementById(tabName + 'Tab') || 
                              document.getElementById(tabName + 'TabContent');
        if (targetContent) {
            targetContent.classList.add('active');
        }
        
        // Load data when switching to specific tabs
        if (tabName === 'monitor') {
            this.loadToolCalls();
        } else if (tabName === 'health') {
            this.loadHealthData();
        }
        
        // Update current tab
        this.currentTab = tabName;
        this.saveUserPreference('activeTab', tabName);
    }

    /**
     * Handle system logs toggle
     */
    handleLogsToggle(event) {
        const enabled = event.target.checked;
        const logsTab = document.getElementById('logsTab');
        
        if (enabled) {
            logsTab.style.display = 'block';
            
            // Initialize system logs if needed
            if (window.SystemLogs && typeof window.SystemLogs.init === 'function') {
                window.SystemLogs.init();
            }
        } else {
            logsTab.style.display = 'none';
            
            // Switch away from logs tab if currently active
            if (this.currentTab === 'logs') {
                this.showTab('tools');
            }
        }
        
        this.saveUserPreference('logsEnabled', enabled);
        DEBUG(`System logs ${enabled ? 'enabled' : 'disabled'}`);
    }

    /**
     * Handle tutorial button click
     */
    handleTutorialClick(event) {
        event.preventDefault();
        
        if (window.Tutorial && typeof window.Tutorial.start === 'function') {
            window.Tutorial.start();
        } else {
            UI.showToast('Tutorial system not available', 'warning');
        }
    }

    /**
     * Handle page visibility change
     */
    handleVisibilityChange() {
        if (document.hidden) {
            DEBUG('Page hidden - pausing updates');
            this.pauseUpdates();
        } else {
            DEBUG('Page visible - resuming updates');
            this.resumeUpdates();
        }
    }

    /**
     * Handle keyboard shortcuts
     */
    handleKeyboardShortcuts(event) {
        // Ctrl/Cmd + K for search
        if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
            event.preventDefault();
            this.focusSearch();
        }
        
        // Escape to close modals/overlays
        if (event.key === 'Escape') {
            this.closeModals();
        }
        
        // Tab navigation with numbers (1-5)
        if (event.altKey && event.key >= '1' && event.key <= '5') {
            event.preventDefault();
            const tabNames = ['tools', 'monitor', 'sessions', 'health', 'logs'];
            const tabIndex = parseInt(event.key) - 1;
            if (tabNames[tabIndex]) {
                this.showTab(tabNames[tabIndex]);
            }
        }
    }

    /**
     * Focus search input in current tab
     */
    focusSearch() {
        const searchInputs = [
            '#toolSearch',
            '#logSearch'
        ];
        
        for (const selector of searchInputs) {
            const input = document.querySelector(selector);
            if (input && UI.isInViewport(input)) {
                input.focus();
                break;
            }
        }
    }

    /**
     * Close modals and overlays
     */
    closeModals() {
        // Close tutorial
        if (window.Tutorial && typeof window.Tutorial.close === 'function') {
            window.Tutorial.close();
        }
        
        // Close any other modals
        document.querySelectorAll('.modal, .overlay').forEach(modal => {
            if (modal.style.display !== 'none') {
                modal.style.display = 'none';
            }
        });
    }

    /**
     * Pause real-time updates
     */
    pauseUpdates() {
        // Keep critical updates but reduce frequency
        this.updateIntervals.forEach((interval, key) => {
            if (key !== 'critical') {
                clearInterval(interval);
                this.updateIntervals.delete(key);
            }
        });
    }

    /**
     * Resume real-time updates
     */
    resumeUpdates() {
        // Restart updates
        this.setupRealTimeUpdates();
        
        // Refresh current tab data
        const tabModule = this.tabs.get(this.currentTab);
        if (tabModule && typeof tabModule.refresh === 'function') {
            tabModule.refresh();
        }
    }

    /**
     * Save user preference to localStorage
     */
    saveUserPreference(key, value) {
        try {
            const storageKey = CONFIG.STORAGE[key.toUpperCase()] || `mqtt-mcp-${key}`;
            localStorage.setItem(storageKey, JSON.stringify(value));
        } catch (error) {
            DEBUG('Failed to save user preference:', error);
        }
    }

    /**
     * Get user preference from localStorage
     */
    getUserPreference(key, defaultValue = null) {
        try {
            const storageKey = CONFIG.STORAGE[key.toUpperCase()] || `mqtt-mcp-${key}`;
            const stored = localStorage.getItem(storageKey);
            return stored ? JSON.parse(stored) : defaultValue;
        } catch (error) {
            DEBUG('Failed to get user preference:', error);
            return defaultValue;
        }
    }

    /**
     * Restore user preferences
     */
    restoreUserPreferences() {
        // Restore active tab
        const savedTab = this.getUserPreference('activeTab', 'tools');
        if (savedTab !== 'tools') {
            this.showTab(savedTab);
        }
        
        // Restore logs enabled state
        const logsEnabled = this.getUserPreference('logsEnabled', false);
        const logsCheckbox = document.getElementById('showLogsCheckbox');
        if (logsCheckbox) {
            logsCheckbox.checked = logsEnabled;
            this.handleLogsToggle({ target: { checked: logsEnabled } });
        }
        
        DEBUG('User preferences restored');
    }

    /**
     * Check if this is first visit
     */
    isFirstVisit() {
        return !this.getUserPreference('visited', false);
    }

    /**
     * Show welcome message for first-time visitors
     */
    showWelcomeMessage() {
        UI.showToast('Willkommen zum MQTT MCP Frontend! Klicke auf "Tutorial" für eine Einführung.', 'info', 8000);
        this.saveUserPreference('visited', true);
    }

    /**
     * Cleanup on page unload
     */
    cleanup() {
        DEBUG('Cleaning up application...');
        
        // Clear intervals
        this.updateIntervals.forEach(interval => clearInterval(interval));
        this.updateIntervals.clear();
        
        // Disconnect WebSocket
        if (WS) {
            WS.disconnect();
        }
        
        // Cleanup modules
        this.tabs.forEach(tabModule => {
            if (tabModule && typeof tabModule.cleanup === 'function') {
                tabModule.cleanup();
            }
        });
    }

    /**
     * Get application status for debugging
     */
    getStatus() {
        return {
            initialized: this.initialized,
            currentTab: this.currentTab,
            activeIntervals: Array.from(this.updateIntervals.keys()),
            websocketStatus: WS ? WS.getStatus() : null,
            apiHealthy: API ? true : false
        };
    }
}

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    DEBUG('DOM loaded, initializing application...');
    
    // Create global app instance
    window.App = new MQTTMCPApp();
    
    // Initialize the application
    try {
        await window.App.init();
        DEBUG('Application startup complete');
    } catch (error) {
        console.error('Failed to start application:', error);
        
        // Show error to user
        if (window.UI) {
            UI.showToast('Failed to start application. Please refresh the page.', 'error', 10000);
        }
    }
});

// Export for debugging in console
if (CONFIG.DEBUG) {
    window.MQTTMCPApp = MQTTMCPApp;
}

DEBUG('App module loaded'); 