// UI Components and Utilities for MQTT MCP Frontend
class UIComponents {
    constructor() {
        this.toastContainer = document.getElementById('toastContainer');
        this.loadingSpinner = document.getElementById('loadingSpinner');
        this.activeToasts = new Map();
        this.loadingTimeout = null;
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info', duration = CONFIG.UI.TOAST_DURATION) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const toastId = Date.now() + Math.random();
        toast.setAttribute('data-toast-id', toastId);
        
        // Create toast content
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-icon">${icons[type] || icons.info}</span>
                <span class="toast-message">${message}</span>
                <button class="toast-close" onclick="UI.dismissToast('${toastId}')">✕</button>
            </div>
        `;
        
        // Add to container
        this.toastContainer.appendChild(toast);
        this.activeToasts.set(toastId, toast);
        
        // Animate in
        setTimeout(() => toast.classList.add('toast-show'), 10);
        
        // Auto-dismiss after duration
        if (duration > 0) {
            setTimeout(() => {
                toast.classList.add('toast-hide');
                setTimeout(() => {
                    if (toast.parentElement) {
                        toast.parentElement.removeChild(toast);
                    }
                    this.activeToasts.delete(toastId);
                }, 300);
            }, duration);
        }
        
        DEBUG(`Toast shown: ${type} - ${message}`);
        return toastId;
    }

    /**
     * Dismiss toast notification
     */
    dismissToast(toastId) {
        const toast = this.activeToasts.get(toastId);
        if (toast) {
            toast.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
                this.activeToasts.delete(toastId);
            }, 300);
        }
    }

    /**
     * Get icon for toast type
     */
    getToastIcon(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type] || icons.info;
    }

    /**
     * Show loading spinner
     */
    showLoading(message = 'Loading...') {
        if (this.loadingTimeout) {
            clearTimeout(this.loadingTimeout);
        }
        
        // Delay showing spinner to avoid flicker for fast operations
        this.loadingTimeout = setTimeout(() => {
            const spinner = this.loadingSpinner;
            const messageElement = spinner.querySelector('p');
            
            if (messageElement) {
                messageElement.textContent = message;
            }
            
            spinner.style.display = 'flex';
            DEBUG(`Loading shown: ${message}`);
        }, CONFIG.UI.LOADING_DELAY);
    }

    /**
     * Hide loading spinner
     */
    hideLoading() {
        if (this.loadingTimeout) {
            clearTimeout(this.loadingTimeout);
            this.loadingTimeout = null;
        }
        
        this.loadingSpinner.style.display = 'none';
        DEBUG('Loading hidden');
    }

    /**
     * Create debounced function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Format timestamp for display
     */
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        // Less than 1 minute ago
        if (diff < 60000) {
            return 'Just now';
        }
        
        // Less than 1 hour ago
        if (diff < 3600000) {
            const minutes = Math.floor(diff / 60000);
            return `${minutes}m ago`;
        }
        
        // Less than 24 hours ago
        if (diff < 86400000) {
            const hours = Math.floor(diff / 3600000);
            return `${hours}h ago`;
        }
        
        // Format as date
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }

    /**
     * Format duration in milliseconds to human readable
     */
    formatDuration(ms) {
        if (ms < 1000) {
            return `${ms}ms`;
        }
        
        if (ms < 60000) {
            return `${(ms / 1000).toFixed(1)}s`;
        }
        
        if (ms < 3600000) {
            const minutes = Math.floor(ms / 60000);
            const seconds = Math.floor((ms % 60000) / 1000);
            return `${minutes}m ${seconds}s`;
        }
        
        const hours = Math.floor(ms / 3600000);
        const minutes = Math.floor((ms % 3600000) / 60000);
        return `${hours}h ${minutes}m`;
    }

    /**
     * Format file size in bytes to human readable
     */
    formatFileSize(bytes) {
        const sizes = ['B', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 B';
        
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        const size = (bytes / Math.pow(1024, i)).toFixed(1);
        
        return `${size} ${sizes[i]}`;
    }

    /**
     * Copy text to clipboard with enhanced feedback
     */
    async copyToClipboard(text, successMessage = 'Copied to clipboard!') {
        try {
            await navigator.clipboard.writeText(text);
            
            // Show success toast
            this.showToast(successMessage, 'success', 3000);
            
            DEBUG('Text copied to clipboard:', text.substring(0, 100) + '...');
            return true;
        } catch (error) {
            console.error('Failed to copy text:', error);
            
            // Fallback for older browsers
            try {
                const textArea = document.createElement('textarea');
                textArea.value = text;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                
                const success = document.execCommand('copy');
                document.body.removeChild(textArea);
                
                if (success) {
                    this.showToast(successMessage, 'success', 3000);
                    return true;
                } else {
                    throw new Error('Fallback copy failed');
                }
            } catch (fallbackError) {
                this.showToast('Failed to copy to clipboard', 'error');
                return false;
            }
        }
    }

    /**
     * Create HTML element with attributes and content
     */
    createElement(tag, attributes = {}, content = '') {
        const element = document.createElement(tag);
        
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'innerHTML') {
                element.innerHTML = value;
            } else if (key.startsWith('data-')) {
                element.setAttribute(key, value);
            } else {
                element[key] = value;
            }
        });
        
        if (content) {
            element.textContent = content;
        }
        
        return element;
    }

    /**
     * Animate element with CSS transitions
     */
    animate(element, fromClass, toClass, duration = CONFIG.UI.ANIMATION_DURATION) {
        return new Promise((resolve) => {
            element.classList.add(fromClass);
            
            requestAnimationFrame(() => {
                element.classList.remove(fromClass);
                element.classList.add(toClass);
                
                setTimeout(() => {
                    element.classList.remove(toClass);
                    resolve();
                }, duration);
            });
        });
    }

    /**
     * Smooth scroll to element
     */
    scrollToElement(element, behavior = 'smooth') {
        if (element) {
            element.scrollIntoView({ behavior, block: 'center' });
        }
    }

    /**
     * Check if element is in viewport
     */
    isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }

    /**
     * Throttle function execution
     */
    throttle(func, wait) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, wait);
            }
        };
    }

    /**
     * Generate unique ID
     */
    generateId(prefix = 'id') {
        return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Escape HTML entities
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Truncate text with ellipsis
     */
    truncateText(text, maxLength, suffix = '...') {
        if (text.length <= maxLength) {
            return text;
        }
        return text.substring(0, maxLength - suffix.length) + suffix;
    }

    /**
     * Convert object to query string
     */
    objectToQueryString(obj) {
        return Object.entries(obj)
            .filter(([_, value]) => value !== null && value !== undefined)
            .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
            .join('&');
    }

    /**
     * Deep clone object
     */
    deepClone(obj) {
        return JSON.parse(JSON.stringify(obj));
    }

    /**
     * Wait for element to exist in DOM
     */
    waitForElement(selector, timeout = 5000) {
        return new Promise((resolve, reject) => {
            const element = document.querySelector(selector);
            if (element) {
                resolve(element);
                return;
            }

            const observer = new MutationObserver((mutations, obs) => {
                const element = document.querySelector(selector);
                if (element) {
                    obs.disconnect();
                    resolve(element);
                }
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });

            setTimeout(() => {
                observer.disconnect();
                reject(new Error(`Element ${selector} not found within ${timeout}ms`));
            }, timeout);
        });
    }
}

// Global UI instance
window.UI = new UIComponents();

// Add CSS for toast animations if not already present
if (!document.querySelector('#toast-animations')) {
    const style = document.createElement('style');
    style.id = 'toast-animations';
    style.textContent = `
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

DEBUG('UI Components initialized'); 