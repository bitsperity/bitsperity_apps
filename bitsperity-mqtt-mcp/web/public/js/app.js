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
            
            // Note: System logs only loaded when explicitly enabled
            // Note: Sessions and Health tabs removed - not critical for MCP tool usage
            
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

        // Save current state of opened details before re-render
        const openedDetails = new Set();
        streamContainer.querySelectorAll('details[open]').forEach(detail => {
            // Debug: Log each open detail we find
            if (typeof DEBUG === 'function') {
                const summary = detail.querySelector('summary')?.textContent || 'no summary';
                DEBUG(`Found open detail: "${summary.substring(0, 50)}..."`);
            }
            
            // Create unique identifier for each detail section
            const toolCallItem = detail.closest('.tool-call-item');
            if (toolCallItem) {
                const toolName = toolCallItem.querySelector('.tool-name')?.textContent;
                const timestamp = toolCallItem.querySelector('.timestamp')?.textContent;
                const detailType = detail.closest('.call-params') ? 'params' : 
                                 detail.closest('.call-result') ? 'result' : 'metadata';
                const identifier = `${toolName}-${timestamp}-${detailType}`;
                openedDetails.add(identifier);
                if (typeof DEBUG === 'function') {
                    DEBUG(`Added tool call detail: ${identifier}`);
                }
            } else {
                // Handle messages container details
                const messagesContainer = detail.closest('.messages-container');
                if (messagesContainer) {
                    openedDetails.add('messages-container');
                    if (typeof DEBUG === 'function') {
                        DEBUG(`Added messages-container to openedDetails`);
                    }
                }
                
                // Handle result metadata details
                const isMetadata = detail.querySelector('summary')?.textContent?.includes('Raw Result Metadata');
                if (isMetadata) {
                    // Find parent tool call for unique identifier
                    const parentToolCall = detail.closest('.tool-call-item');
                    if (parentToolCall) {
                        const toolName = parentToolCall.querySelector('.tool-name')?.textContent;
                        const timestamp = parentToolCall.querySelector('.timestamp')?.textContent;
                        openedDetails.add(`${toolName}-${timestamp}-metadata`);
                        if (typeof DEBUG === 'function') {
                            DEBUG(`Added metadata detail: ${toolName}-${timestamp}-metadata`);
                        }
                    }
                }
            }
        });

        if (typeof DEBUG === 'function') {
            DEBUG(`Total openedDetails collected: ${openedDetails.size}, details: [${Array.from(openedDetails).join(', ')}]`);
        }

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
                ${call.result ? `
                    <div class="call-result">
                        <details>
                            <summary><strong>🎯 Tool Response (${call.result_summary || 'result'})</strong></summary>
                            ${this.formatToolResult(call.result, call.tool_name, call.timestamp, openedDetails)}
                            <div class="result-actions">
                                <button class="btn-copy" onclick="UI.copyToClipboard('${JSON.stringify(call.result).replace(/'/g, "\\'")}')">📋 Copy Result</button>
                            </div>
                        </details>
                    </div>
                ` : ''}
            </div>
        `).join('');

        // Restore opened details state after re-render
        streamContainer.querySelectorAll('.tool-call-item').forEach(toolCallItem => {
            const toolName = toolCallItem.querySelector('.tool-name')?.textContent;
            const timestamp = toolCallItem.querySelector('.timestamp')?.textContent;
            
            // Check and restore params details
            const paramsDetail = toolCallItem.querySelector('.call-params details');
            if (paramsDetail && openedDetails.has(`${toolName}-${timestamp}-params`)) {
                paramsDetail.open = true;
            }
            
            // Check and restore result details
            const resultDetail = toolCallItem.querySelector('.call-result details');
            if (resultDetail && openedDetails.has(`${toolName}-${timestamp}-result`)) {
                resultDetail.open = true;
            }
        });

        // Restore messages container state
        streamContainer.querySelectorAll('.messages-container details').forEach(detail => {
            if (openedDetails.has('messages-container')) {
                detail.open = true;
                if (typeof DEBUG === 'function') {
                    DEBUG(`Restored messages-container to OPEN state`);
                }
            } else {
                // Explicitly force close if not in openedDetails
                detail.open = false;
                if (typeof DEBUG === 'function') {
                    DEBUG(`Set messages-container to CLOSED state (not in openedDetails)`);
                }
            }
        });

        // Restore metadata details state
        streamContainer.querySelectorAll('.tool-call-item').forEach(toolCallItem => {
            const toolName = toolCallItem.querySelector('.tool-name')?.textContent;
            const timestamp = toolCallItem.querySelector('.timestamp')?.textContent;
            
            // Find metadata details more reliably
            const allDetails = toolCallItem.querySelectorAll('details');
            allDetails.forEach(detail => {
                const summary = detail.querySelector('summary');
                if (summary && summary.textContent.includes('Raw Result Metadata')) {
                    if (openedDetails.has(`${toolName}-${timestamp}-metadata`)) {
                        detail.open = true;
                    }
                }
            });
        });
    }

    /**
     * Format tool result for better display, especially for MQTT messages with JSON payloads
     */
    formatToolResult(result, toolName, timestamp, openedDetails) {
        // Check if this is a result from subscribe_and_collect tool with messages
        if (result.messages && Array.isArray(result.messages)) {
            return this.formatMessagesResult(result, openedDetails);
        }
        
        // Default formatting for other tool results
        return `<pre class="result-content">${JSON.stringify(result, null, 2)}</pre>`;
    }

    /**
     * Format MQTT messages with enhanced JSON payload display
     */
    formatMessagesResult(result, openedDetails) {
        const messages = result.messages || [];
        
        if (messages.length === 0) {
            return `
                <div class="messages-result">
                    <div class="result-summary">
                        <p>No messages collected during the specified duration.</p>
                        <pre class="result-metadata">${JSON.stringify(result, null, 2)}</pre>
                    </div>
                </div>
            `;
        }

        // Create enhanced message display
        const messagesHtml = messages.map((msg, index) => {
            const payloadDisplay = this.formatMessagePayload(msg);
            const topicClass = this.getTopicClass(msg.topic);
            
            return `
                <div class="message-item ${topicClass}">
                    <div class="message-header">
                        <span class="message-topic">${msg.topic}</span>
                        <span class="message-timestamp">${UI.formatTimestamp(msg.timestamp)}</span>
                        <span class="message-qos">QoS: ${msg.qos}</span>
                        ${msg.retain ? '<span class="message-retain">📌 Retained</span>' : ''}
                        ${msg.payload_type ? `<span class="payload-type-badge ${msg.payload_type}">${msg.payload_type.toUpperCase()}</span>` : ''}
                    </div>
                    <div class="message-payload">
                        ${payloadDisplay}
                    </div>
                </div>
            `;
        }).join('');

        // Create result summary
        const summary = `
            <div class="result-summary">
                <div class="summary-stats">
                    <span class="stat-item">📊 ${messages.length} messages</span>
                    <span class="stat-item">⏱️ ${result.collection_duration_seconds}s duration</span>
                    ${result.pruning_applied ? `<span class="stat-item">✂️ Pruned from ${result.original_message_count}</span>` : ''}
                </div>
                <div class="topic-pattern">Pattern: <code>${result.topic_pattern}</code></div>
            </div>
        `;

        // Check if messages container should be opened (default: closed)
        const messagesContainerOpen = openedDetails && openedDetails.has('messages-container');

        // Debug output
        if (typeof DEBUG === 'function') {
            DEBUG(`Messages container state - openedDetails size: ${openedDetails ? openedDetails.size : 'null'}, has 'messages-container': ${openedDetails ? openedDetails.has('messages-container') : 'N/A'}, will open: ${messagesContainerOpen}`);
        }

        return `
            <div class="messages-result">
                ${summary}
                <div class="messages-container">
                    <details${messagesContainerOpen ? ' open' : ''}>
                        <summary><strong>📨 Collected Messages (${messages.length})</strong></summary>
                        <div class="messages-list">
                            ${messagesHtml}
                        </div>
                    </details>
                </div>
                <details>
                    <summary>🔧 Raw Result Metadata</summary>
                    <pre class="result-metadata">${JSON.stringify(result, null, 2)}</pre>
                </details>
            </div>
        `;
    }

    /**
     * Format message payload based on type
     */
    formatMessagePayload(message) {
        const payload = message.payload;
        const payloadType = message.payload_type || 'text';
        const rawPayload = message.payload_raw || payload;

        switch (payloadType) {
            case 'json':
                // Beautiful JSON formatting
                return `
                    <div class="payload-json">
                        <div class="payload-actions">
                            <button class="btn-copy-small" onclick="UI.copyToClipboard('${JSON.stringify(payload).replace(/'/g, "\\'")}')">📋 Copy JSON</button>
                            <button class="btn-copy-small" onclick="UI.copyToClipboard('${rawPayload.replace(/'/g, "\\'")}')">📋 Copy Raw</button>
                        </div>
                        <pre class="json-payload">${JSON.stringify(payload, null, 2)}</pre>
                    </div>
                `;
                
            case 'number':
                return `
                    <div class="payload-number">
                        <span class="number-value">${payload}</span>
                        <button class="btn-copy-small" onclick="UI.copyToClipboard('${payload}')">📋</button>
                    </div>
                `;
                
            case 'text':
            default:
                // Regular text with option to show raw
                const isLongText = rawPayload.length > 100;
                const displayText = isLongText ? rawPayload.substring(0, 100) + '...' : rawPayload;
                
                return `
                    <div class="payload-text">
                        <div class="payload-actions">
                            <button class="btn-copy-small" onclick="UI.copyToClipboard('${rawPayload.replace(/'/g, "\\'")}')">📋 Copy</button>
                        </div>
                        <div class="text-payload">
                            <span class="text-content">${this.escapeHtml(displayText)}</span>
                            ${isLongText ? `
                                <details class="text-expand">
                                    <summary>Show full text (${rawPayload.length} chars)</summary>
                                    <pre class="full-text">${this.escapeHtml(rawPayload)}</pre>
                                </details>
                            ` : ''}
                        </div>
                    </div>
                `;
        }
    }

    /**
     * Get CSS class for topic styling
     */
    getTopicClass(topic) {
        const topicLower = topic.toLowerCase();
        
        if (topicLower.includes('error') || topicLower.includes('alarm') || topicLower.includes('warning')) {
            return 'topic-error';
        }
        if (topicLower.includes('sensor') || topicLower.includes('data')) {
            return 'topic-sensor';
        }
        if (topicLower.includes('command') || topicLower.includes('control')) {
            return 'topic-command';
        }
        if (topicLower.includes('status') || topicLower.includes('heartbeat')) {
            return 'topic-status';
        }
        
        return 'topic-default';
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Load system logs
     */
    async loadSystemLogs() {
        try {
            const response = await API.getSystemLogs({ limit: 100 });
            this.renderSystemLogs(response.logs || []);
        } catch (error) {
            DEBUG('Error loading system logs:', error);
        }
    }

    /**
     * Render system logs
     */
    renderSystemLogs(logs) {
        const logsContainer = document.getElementById('logsContainer');
        if (!logsContainer) return;

        if (logs.length === 0) {
            logsContainer.innerHTML = '<p class="no-data">No system logs available.</p>';
            return;
        }

        logsContainer.innerHTML = logs.map(log => `
            <div class="log-entry ${log.level.toLowerCase()}">
                <div class="log-header">
                    <span class="log-level ${log.level.toLowerCase()}">${log.level}</span>
                    <span class="log-event">${log.event_type}</span>
                    <span class="log-timestamp">${UI.formatTimestamp(log.timestamp)}</span>
                </div>
                <div class="log-message">${log.message}</div>
                ${log.metadata && Object.keys(log.metadata).length > 0 ? `
                    <div class="log-metadata">
                        <details>
                            <summary>Metadata</summary>
                            <pre>${JSON.stringify(log.metadata, null, 2)}</pre>
                        </details>
                    </div>
                ` : ''}
            </div>
        `).join('');
    }

    /**
     * Setup real-time updates
     */
    setupRealTimeUpdates() {
        // Tool calls updates every 30 seconds (increased from 10s to give users time to read)
        this.updateIntervals.set('toolcalls', setInterval(() => {
            if (!document.hidden && this.currentTab === 'monitor') {
                this.loadToolCalls();
            }
        }, 30000));
        
        // System logs updates every 60 seconds (increased from 20s)
        this.updateIntervals.set('systemlogs', setInterval(() => {
            if (!document.hidden && this.currentTab === 'logs') {
                this.loadSystemLogs();
            }
        }, 60000));
        
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
        
        // Handle special case for logs tab
        let targetContent;
        if (tabName === 'logs') {
            targetContent = document.getElementById('logsTabContent');
        } else {
            targetContent = document.getElementById(tabName + 'Tab') || 
                          document.getElementById(tabName + 'TabContent');
        }
        
        if (targetContent) {
            targetContent.classList.add('active');
        }
        
        // Load data when switching to specific tabs
        if (tabName === 'monitor') {
            this.loadToolCalls();
        } else if (tabName === 'logs') {
            this.loadSystemLogs();
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
            
            // Load system logs when enabled
            this.loadSystemLogs();
            
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