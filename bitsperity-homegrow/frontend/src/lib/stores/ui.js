import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

// UI State
export const theme = writable('dark');
export const sidebarOpen = writable(false);
export const modalOpen = writable(null);
export const notifications = writable([]);
export const isOnline = writable(true);
export const loading = writable(false);

// Mobile/Touch Detection
export const isMobile = writable(false);
export const isTouch = writable(false);

// Screen Size
export const screenSize = writable({
	width: 0,
	height: 0,
	breakpoint: 'mobile'
});

// Derived Stores
export const isDarkMode = derived(theme, ($theme) => $theme === 'dark');
export const isLightMode = derived(theme, ($theme) => $theme === 'light');

export const breakpoint = derived(screenSize, ($screenSize) => $screenSize.breakpoint);

export const hasNotifications = derived(notifications, ($notifications) => 
	$notifications.length > 0
);

export const unreadNotifications = derived(notifications, ($notifications) => 
	$notifications.filter(n => !n.read).length
);

// UI Actions
export const uiActions = {
	// Theme Management
	setTheme(newTheme) {
		theme.set(newTheme);
		if (browser) {
			localStorage.setItem('homegrow-theme', newTheme);
			document.documentElement.setAttribute('data-theme', newTheme);
		}
	},

	toggleTheme() {
		theme.update(current => {
			const newTheme = current === 'dark' ? 'light' : 'dark';
			if (browser) {
				localStorage.setItem('homegrow-theme', newTheme);
				document.documentElement.setAttribute('data-theme', newTheme);
			}
			return newTheme;
		});
	},

	// Sidebar Management
	toggleSidebar() {
		sidebarOpen.update(current => !current);
	},

	closeSidebar() {
		sidebarOpen.set(false);
	},

	openSidebar() {
		sidebarOpen.set(true);
	},

	// Modal Management
	openModal(modalId) {
		modalOpen.set(modalId);
		if (browser) {
			document.body.style.overflow = 'hidden';
		}
	},

	closeModal() {
		modalOpen.set(null);
		if (browser) {
			document.body.style.overflow = '';
		}
	},

	// Notification Management
	addNotification(notification) {
		const id = Date.now().toString();
		const newNotification = {
			id,
			timestamp: new Date(),
			read: false,
			type: 'info',
			...notification
		};

		notifications.update(current => [newNotification, ...current]);

		// Auto-remove after timeout if specified
		if (notification.timeout) {
			setTimeout(() => {
				uiActions.removeNotification(id);
			}, notification.timeout);
		}

		return id;
	},

	removeNotification(id) {
		notifications.update(current => 
			current.filter(notification => notification.id !== id)
		);
	},

	markNotificationRead(id) {
		notifications.update(current => 
			current.map(notification => 
				notification.id === id 
					? { ...notification, read: true }
					: notification
			)
		);
	},

	clearAllNotifications() {
		notifications.set([]);
	},

	// Loading State
	setLoading(isLoading) {
		loading.set(isLoading);
	},

	// Online Status
	setOnlineStatus(online) {
		isOnline.set(online);
	},

	// Screen Size Detection
	updateScreenSize(width, height) {
		let breakpoint = 'mobile';
		if (width >= 1024) breakpoint = 'desktop';
		else if (width >= 768) breakpoint = 'tablet';

		screenSize.set({ width, height, breakpoint });
		isMobile.set(breakpoint === 'mobile');
	},

	// Touch Detection
	setTouchDevice(isTouchDevice) {
		try {
			if (isTouch && typeof isTouch.set === 'function') {
				isTouch.set(isTouchDevice);
			} else {
				console.warn('isTouch store not available for setTouchDevice');
			}
		} catch (error) {
			console.error('Error in setTouchDevice:', error);
		}
	},

	// Initialize UI
	init() {
		if (!browser) return;

		// Load theme from localStorage
		const savedTheme = localStorage.getItem('homegrow-theme') || 'dark';
		theme.set(savedTheme);
		document.documentElement.setAttribute('data-theme', savedTheme);

		// Detect screen size
		const updateSize = () => {
			uiActions.updateScreenSize(window.innerWidth, window.innerHeight);
		};
		updateSize();
		window.addEventListener('resize', updateSize);

		// Detect touch device
		const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
		uiActions.setTouchDevice(hasTouch);

		// Online/Offline detection
		const updateOnlineStatus = () => {
			uiActions.setOnlineStatus(navigator.onLine);
		};
		updateOnlineStatus();
		window.addEventListener('online', updateOnlineStatus);
		window.addEventListener('offline', updateOnlineStatus);

		// Cleanup function
		return () => {
			window.removeEventListener('resize', updateSize);
			window.removeEventListener('online', updateOnlineStatus);
			window.removeEventListener('offline', updateOnlineStatus);
		};
	}
}; 