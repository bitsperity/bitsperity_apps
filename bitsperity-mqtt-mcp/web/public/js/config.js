// MQTT MCP Frontend Configuration
window.CONFIG = {
    // API Endpoints
    API_BASE_URL: window.location.origin,
    WEBSOCKET_URL: null, // Disable WebSocket - use polling instead
    
    // Enable polling mode when WebSocket is disabled
    POLLING_MODE: true,
    POLLING_INTERVAL: 5000, // 5 seconds for polling updates
    
    // MongoDB Collections
    COLLECTIONS: {
        TOOL_CALLS: 'mcp_tool_calls',
        SYSTEM_LOGS: 'mcp_system_logs',
        PERFORMANCE_METRICS: 'mcp_performance_metrics'
    },
    
    // Data retention settings (for display purposes)
    RETENTION: {
        TOOL_CALLS: 24 * 60 * 60 * 1000, // 24 hours in milliseconds
        SYSTEM_LOGS: 7 * 24 * 60 * 60 * 1000, // 7 days
        PERFORMANCE_METRICS: 7 * 24 * 60 * 60 * 1000 // 7 days
    },
    
    // Live monitoring settings
    MONITOR: {
        MAX_TOOL_CALLS: 500, // Maximum tool calls in memory
        REFRESH_INTERVAL: 2000, // 2 seconds for live updates
        PERFORMANCE_UPDATE_INTERVAL: 10000, // 10 seconds for performance updates
        CHART_UPDATE_INTERVAL: 60000, // 1 minute for chart updates
    },
    
    // UI Settings
    UI: {
        TOAST_DURATION: 5000, // 5 seconds
        LOADING_DELAY: 300, // Delay before showing loading spinner
        DEBOUNCE_DELAY: 300, // Debounce delay for search/filter
        ANIMATION_DURATION: 300 // CSS transition duration
    },
    
    // System Logs settings (optional feature)
    LOGS: {
        DEFAULT_VISIBLE: false, // System logs are hidden by default
        MAX_LOG_ENTRIES: 200, // Maximum log entries to display
        AUTO_SCROLL: true, // Auto-scroll to newest logs
        LEVELS: ['DEBUG', 'INFO', 'WARN', 'ERROR'],
        COLORS: {
            DEBUG: '#6c757d',
            INFO: '#17a2b8', 
            WARN: '#ffc107',
            ERROR: '#dc3545'
        }
    },
    
    // Tool categories and their colors
    TOOL_CATEGORIES: {
        CONNECTION: {
            label: 'Connection',
            color: '#00d4aa',
            icon: '🔌'
        },
        DISCOVERY: {
            label: 'Discovery', 
            color: '#0088ff',
            icon: '🔍'
        },
        DATA: {
            label: 'Data',
            color: '#28a745',
            icon: '📊'
        },
        ANALYSIS: {
            label: 'Analysis',
            color: '#ffc107',
            icon: '🔬'
        },
        DEBUGGING: {
            label: 'Debugging',
            color: '#dc3545',
            icon: '🐛'
        },
        MONITORING: {
            label: 'Monitoring',
            color: '#6f42c1',
            icon: '📈'
        }
    },
    
    // Performance thresholds
    PERFORMANCE: {
        HEALTH_SCORE: {
            EXCELLENT: 90,
            GOOD: 75,
            WARNING: 60,
            CRITICAL: 0
        },
        RESPONSE_TIME: {
            FAST: 100, // < 100ms
            MEDIUM: 500, // < 500ms
            SLOW: 1000 // < 1s
        },
        ERROR_RATE: {
            LOW: 0.01, // < 1%
            MEDIUM: 0.05, // < 5%
            HIGH: 0.1 // < 10%
        }
    },
    
    // Chart.js default configuration
    CHART_DEFAULTS: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top',
                labels: {
                    color: '#b8bcc8',
                    font: {
                        size: 12
                    }
                }
            }
        },
        scales: {
            x: {
                ticks: {
                    color: '#8b949e',
                    font: {
                        size: 11
                    }
                },
                grid: {
                    color: '#3d444d'
                }
            },
            y: {
                ticks: {
                    color: '#8b949e',
                    font: {
                        size: 11
                    }
                },
                grid: {
                    color: '#3d444d'
                }
            }
        }
    },
    
    // Tutorial configuration
    TUTORIAL: {
        ENABLED: true,
        AUTO_START: false, // Don't auto-start tutorial (user can trigger manually)
        STEPS: [
            {
                title: 'Willkommen zum MQTT MCP Frontend',
                content: 'Dieses Frontend hilft dir dabei, die MQTT MCP Tools zu verstehen und live zu überwachen.',
                target: '.logo'
            },
            {
                title: 'MCP Tool Documentation',
                content: 'Hier findest du alle verfügbaren Tools mit Copy-Paste-Ready Beispielen.',
                target: '[data-tab="tools"]'
            },
            {
                title: 'Live Tool Call Monitoring',
                content: 'Überwache alle Tool Calls in Echtzeit und analysiere Performance.',
                target: '[data-tab="monitor"]'
            },
            {
                title: 'Session Management',
                content: 'Verwalte aktive MQTT Connections und Sessions.',
                target: '[data-tab="sessions"]'
            },
            {
                title: 'Health Dashboard',
                content: 'Überwache die Performance und Gesundheit des MCP Servers.',
                target: '[data-tab="health"]'
            },
            {
                title: 'Optional System Logs',
                content: 'System Logs sind standardmäßig ausgeblendet, können aber über diesen Toggle aktiviert werden.',
                target: '#toggleLogs'
            }
        ]
    },
    
    // Local storage keys
    STORAGE: {
        TUTORIAL_COMPLETED: 'mqtt-mcp-tutorial-completed',
        LOGS_ENABLED: 'mqtt-mcp-logs-enabled',
        ACTIVE_TAB: 'mqtt-mcp-active-tab',
        FILTER_PREFERENCES: 'mqtt-mcp-filter-preferences'
    },
    
    // Error messages
    ERRORS: {
        CONNECTION_FAILED: 'Verbindung zum Server fehlgeschlagen',
        API_ERROR: 'API-Fehler aufgetreten',
        WEBSOCKET_ERROR: 'WebSocket-Verbindung unterbrochen',
        MONGODB_ERROR: 'MongoDB-Verbindung nicht verfügbar',
        TOOL_LOAD_ERROR: 'Tools konnten nicht geladen werden',
        DATA_LOAD_ERROR: 'Daten konnten nicht geladen werden'
    },
    
    // Success messages
    SUCCESS: {
        CONNECTION_ESTABLISHED: 'Verbindung erfolgreich hergestellt',
        DATA_LOADED: 'Daten erfolgreich geladen',
        EXPORT_COMPLETED: 'Export erfolgreich abgeschlossen',
        COPIED_TO_CLIPBOARD: 'In Zwischenablage kopiert'
    },
    
    // Development mode (set to false in production)
    DEBUG: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',
    
    // Feature flags
    FEATURES: {
        EXPORT_FUNCTIONALITY: true,
        TUTORIAL_SYSTEM: true,
        SYSTEM_LOGS_TOGGLE: true,
        PERFORMANCE_CHARTS: true,
        REAL_TIME_UPDATES: true,
        COPY_CODE_SNIPPETS: true
    }
};

// Make configuration immutable in production
if (!CONFIG.DEBUG) {
    Object.freeze(CONFIG);
}

// Debug logging utility
window.DEBUG = CONFIG.DEBUG ? console.log.bind(console, '[MQTT-MCP]') : () => {};

// Global error handler for unhandled promises
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    
    // Show user-friendly error message
    if (window.UI && window.UI.showToast) {
        window.UI.showToast('Ein unerwarteter Fehler ist aufgetreten', 'error');
    }
});

// Global error handler for JavaScript errors
window.addEventListener('error', function(event) {
    console.error('JavaScript error:', event.error);
    
    // Show user-friendly error message
    if (window.UI && window.UI.showToast) {
        window.UI.showToast('Ein JavaScript-Fehler ist aufgetreten', 'error');
    }
});

DEBUG('Configuration loaded:', CONFIG); 