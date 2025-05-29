import { build, files, version } from '$service-worker';

// Cache names
const CACHE = `cache-${version}`;
const ASSETS = [...build, ...files];

// Install service worker
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Install event');
  
  async function addFilesToCache() {
    const cache = await caches.open(CACHE);
    await cache.addAll(ASSETS);
  }
  
  event.waitUntil(addFilesToCache());
  self.skipWaiting(); // Activate immediately
});

// Activate service worker and clean old caches
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activate event');
  
  async function deleteOldCaches() {
    const cacheNames = await caches.keys();
    for (const cacheName of cacheNames) {
      if (cacheName !== CACHE) {
        console.log('[Service Worker] Deleting old cache:', cacheName);
        await caches.delete(cacheName);
      }
    }
    self.clients.claim(); // Take control immediately
  }
  
  event.waitUntil(deleteOldCaches());
});

// Fetch event with cache-first strategy for assets, network-first for API
self.addEventListener('fetch', (event) => {
  // Only handle GET requests
  if (event.request.method !== 'GET') return;
  
  const url = new URL(event.request.url);
  
  // Handle different types of requests
  if (url.pathname.startsWith('/api/')) {
    // API requests: Network-first, cache as fallback
    event.respondWith(handleApiRequest(event.request));
  } else if (url.pathname.startsWith('/ws')) {
    // WebSocket requests: Don't cache
    return;
  } else {
    // Static assets: Cache-first
    event.respondWith(handleStaticRequest(event.request));
  }
});

// Handle API requests with network-first strategy
async function handleApiRequest(request) {
  try {
    // Try network first
    const response = await fetch(request);
    
    // Cache successful responses (except for health checks)
    if (response.ok && !request.url.includes('/health')) {
      const cache = await caches.open(CACHE);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    // Network failed, try cache
    console.log('[Service Worker] Network failed for API, trying cache:', request.url);
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline response for API calls
    return new Response(
      JSON.stringify({
        error: 'Offline',
        message: 'Netzwerk nicht verfügbar. Einige Funktionen sind möglicherweise eingeschränkt.'
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

// Handle static requests with cache-first strategy
async function handleStaticRequest(request) {
  const cached = await caches.match(request);
  
  if (cached) {
    return cached;
  }
  
  try {
    const response = await fetch(request);
    
    if (response.ok) {
      const cache = await caches.open(CACHE);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    console.log('[Service Worker] Fetch failed for:', request.url);
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      const offlineResponse = await caches.match('/offline.html');
      if (offlineResponse) {
        return offlineResponse;
      }
    }
    
    throw error;
  }
}

// Handle background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('[Service Worker] Background sync:', event.tag);
  
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

async function doBackgroundSync() {
  try {
    // Get stored offline actions
    const actions = await getStoredActions();
    
    for (const action of actions) {
      try {
        await fetch(action.url, action.options);
        await removeStoredAction(action.id);
        console.log('[Service Worker] Synced action:', action.id);
      } catch (error) {
        console.log('[Service Worker] Failed to sync action:', action.id, error);
      }
    }
  } catch (error) {
    console.error('[Service Worker] Background sync failed:', error);
  }
}

// Handle push notifications
self.addEventListener('push', (event) => {
  console.log('[Service Worker] Push received');
  
  const options = {
    body: event.data ? event.data.text() : 'HomeGrow Benachrichtigung',
    icon: '/icons/icon-192.png',
    badge: '/icons/badge.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Öffnen',
        icon: '/icons/checkmark.png'
      },
      {
        action: 'close',
        title: 'Schließen',
        icon: '/icons/xmark.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('HomeGrow v3', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('[Service Worker] Notification click received');
  
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Handle message from main thread
self.addEventListener('message', (event) => {
  console.log('[Service Worker] Message received:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Utility functions for offline storage
async function getStoredActions() {
  try {
    const cache = await caches.open('offline-actions');
    const keys = await cache.keys();
    const actions = [];
    
    for (const key of keys) {
      const response = await cache.match(key);
      const action = await response.json();
      actions.push(action);
    }
    
    return actions;
  } catch (error) {
    console.error('Failed to get stored actions:', error);
    return [];
  }
}

async function removeStoredAction(actionId) {
  try {
    const cache = await caches.open('offline-actions');
    await cache.delete(`/offline-action-${actionId}`);
  } catch (error) {
    console.error('Failed to remove stored action:', error);
  }
}

// Cache management
self.addEventListener('message', async (event) => {
  if (event.data && event.data.type === 'CACHE_STATS') {
    const cacheNames = await caches.keys();
    const stats = {};
    
    for (const cacheName of cacheNames) {
      const cache = await caches.open(cacheName);
      const keys = await cache.keys();
      stats[cacheName] = keys.length;
    }
    
    event.ports[0].postMessage(stats);
  }
});

console.log('[Service Worker] Loaded version:', version); 