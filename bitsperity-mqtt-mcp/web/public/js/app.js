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
        // Register tab modules
        this.tabs.set('tools', window.ToolDashboard);
        this.tabs.set('monitor', window.LiveMonitor);
        this.tabs.set('sessions', window.SessionManager);
        this.tabs.set('health', window.HealthDashboard);
        this.tabs.set('logs', window.SystemLogs);
        
        // Show initial tab
        this.showTab(this.currentTab);
        
        DEBUG('Tab system initialized');
    }

    /**
     * Load initial data for all components
     */
    async loadInitialData() {
        const loadPromises = [];
        
        // Load tools documentation
        if (window.ToolDashboard) {
            loadPromises.push(window.ToolDashboard.loadTools());
        }
        
        // Load initial monitoring data
        if (window.LiveMonitor) {
            loadPromises.push(window.LiveMonitor.loadInitialData());
        }
        
        // Load sessions
        if (window.SessionManager) {
            loadPromises.push(window.SessionManager.loadSessions());
        }
        
        // Load health data
        if (window.HealthDashboard) {
            loadPromises.push(window.HealthDashboard.loadInitialData());
        }
        
        // Wait for all initial data to load
        await Promise.allSettled(loadPromises);
        
        DEBUG('Initial data loaded');
    }

    /**
     * Setup real-time updates
     */
    setupRealTimeUpdates() {
        // Performance updates every 10 seconds
        this.updateIntervals.set('performance', setInterval(() => {
            if (!document.hidden && window.HealthDashboard) {
                window.HealthDashboard.updatePerformanceMetrics();
            }
        }, CONFIG.MONITOR.PERFORMANCE_UPDATE_INTERVAL));
        
        // Sessions updates every 30 seconds
        this.updateIntervals.set('sessions', setInterval(() => {
            if (!document.hidden && window.SessionManager) {
                window.SessionManager.refreshSessions();
            }
        }, 30000));
        
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
        
        // Initialize tab if needed
        const tabModule = this.tabs.get(tabName);
        if (tabModule && typeof tabModule.onTabShow === 'function') {
            tabModule.onTabShow();
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