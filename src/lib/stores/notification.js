import { writable } from 'svelte/store';

function createNotificationStore() {
  const { subscribe, update } = writable([]);

  return {
    subscribe,
    
    add(notification) {
      const id = Date.now() + Math.random();
      const newNotification = {
        id,
        type: notification.type || 'info', // 'success', 'warning', 'error', 'info'
        title: notification.title,
        message: notification.message,
        duration: notification.duration || 5000,
        dismissible: notification.dismissible !== false,
        timestamp: new Date()
      };
      
      update(notifications => [...notifications, newNotification]);
      
      // Auto-remove after duration
      if (newNotification.duration > 0) {
        setTimeout(() => {
          this.remove(id);
        }, newNotification.duration);
      }
      
      return id;
    },
    
    remove(id) {
      update(notifications => notifications.filter(n => n.id !== id));
    },
    
    clear() {
      update(() => []);
    },
    
    // Convenience methods
    success(title, message, options = {}) {
      return this.add({ type: 'success', title, message, ...options });
    },
    
    error(title, message, options = {}) {
      return this.add({ type: 'error', title, message, duration: 0, ...options });
    },
    
    warning(title, message, options = {}) {
      return this.add({ type: 'warning', title, message, ...options });
    },
    
    info(title, message, options = {}) {
      return this.add({ type: 'info', title, message, ...options });
    }
  };
}

export const notificationStore = createNotificationStore(); 