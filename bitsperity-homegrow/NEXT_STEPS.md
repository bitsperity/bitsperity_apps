# HomeGrow v3 - Nächste Entwicklungsschritte

## 🎯 Effizienter Implementierungsplan

Basierend auf der Analyse der Codebase und den Standards von homegrow_client3:

### ✅ Phase 1: WebSocket Service vervollständigen (FERTIG)
- [x] WebSocket Service Backend (`server/services/websocket.js`)
- [x] WebSocket Store Frontend (`src/lib/stores/websocketStore.js`)
- [x] Integration in server/index.js
- [x] Connection Status Indicator im UI

### 📋 Phase 2: PWA Features (2-3 Tage)

#### Service Worker Implementation
```javascript
// src/service-worker.js
import { build, files, version } from '$service-worker';

const CACHE = `cache-${version}`;
const ASSETS = [...build, ...files];

// Install service worker
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then((cache) => cache.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
});

// Activate and clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(async (keys) => {
      for (const key of keys) {
        if (key !== CACHE) await caches.delete(key);
      }
      self.clients.claim();
    })
  );
});

// Fetch with cache-first strategy
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request).then((cached) => {
      return cached || fetch(event.request).then((response) => {
        if (response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE).then((cache) => {
            cache.put(event.request, clone);
          });
        }
        return response;
      });
    })
  );
});
```

#### App Manifest
```json
// static/manifest.json
{
  "name": "HomeGrow v3",
  "short_name": "HomeGrow",
  "description": "Professional Hydroponic System Management",
  "theme_color": "#3b82f6",
  "background_color": "#ffffff",
  "display": "standalone",
  "orientation": "portrait",
  "scope": "/",
  "start_url": "/",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

### 📋 Phase 3: Program Editor UI (3-4 Tage)

#### Visual Program Editor Component
```svelte
<!-- src/lib/components/program/ProgramEditor.svelte -->
<script>
  import { programStore } from '$lib/stores/programStore.js';
  import ActionBlock from './ActionBlock.svelte';
  import ConditionBlock from './ConditionBlock.svelte';
  import { dndzone } from 'svelte-dnd-action';
  
  export let program = {
    name: '',
    description: '',
    schedule: { type: 'manual' },
    conditions: [],
    actions: []
  };
  
  let availableActions = [
    { type: 'activate_pump', label: 'Pumpe aktivieren' },
    { type: 'wait', label: 'Warten' },
    { type: 'notify', label: 'Benachrichtigung' }
  ];
  
  let availableConditions = [
    { type: 'sensor_value', label: 'Sensorwert' },
    { type: 'time_range', label: 'Zeitbereich' },
    { type: 'device_status', label: 'Gerätestatus' }
  ];
</script>

<div class="program-editor">
  <!-- Program basics -->
  <div class="editor-section">
    <h3>Programm-Grundlagen</h3>
    <input bind:value={program.name} placeholder="Programmname" />
    <textarea bind:value={program.description} placeholder="Beschreibung" />
  </div>
  
  <!-- Schedule -->
  <div class="editor-section">
    <h3>Zeitplan</h3>
    <select bind:value={program.schedule.type}>
      <option value="manual">Manuell</option>
      <option value="interval">Intervall</option>
      <option value="cron">Zeitplan</option>
      <option value="sensor_trigger">Sensor-Trigger</option>
    </select>
  </div>
  
  <!-- Conditions -->
  <div class="editor-section">
    <h3>Bedingungen</h3>
    <div class="drop-zone" use:dndzone={{ items: program.conditions }}>
      {#each program.conditions as condition}
        <ConditionBlock {condition} />
      {/each}
    </div>
  </div>
  
  <!-- Actions -->
  <div class="editor-section">
    <h3>Aktionen</h3>
    <div class="drop-zone" use:dndzone={{ items: program.actions }}>
      {#each program.actions as action}
        <ActionBlock {action} />
      {/each}
    </div>
  </div>
</div>
```

### 📋 Phase 4: Benutzer-Authentifizierung (3-4 Tage)

#### Auth Store
```javascript
// src/lib/stores/authStore.js
import { writable, derived } from 'svelte/store';
import { goto } from '$app/navigation';

function createAuthStore() {
  const { subscribe, set, update } = writable({
    user: null,
    token: null,
    loading: false,
    error: null
  });

  return {
    subscribe,
    
    async login(username, password) {
      update(state => ({ ...state, loading: true, error: null }));
      
      try {
        const response = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password })
        });
        
        if (!response.ok) {
          throw new Error('Login fehlgeschlagen');
        }
        
        const data = await response.json();
        
        // Store token in localStorage
        localStorage.setItem('auth_token', data.token);
        
        update(state => ({
          ...state,
          user: data.user,
          token: data.token,
          loading: false
        }));
        
        goto('/');
      } catch (error) {
        update(state => ({
          ...state,
          loading: false,
          error: error.message
        }));
      }
    },
    
    async logout() {
      localStorage.removeItem('auth_token');
      set({ user: null, token: null, loading: false, error: null });
      goto('/login');
    },
    
    async checkAuth() {
      const token = localStorage.getItem('auth_token');
      if (!token) return;
      
      try {
        const response = await fetch('/api/v1/auth/me', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
          const user = await response.json();
          update(state => ({ ...state, user, token }));
        } else {
          localStorage.removeItem('auth_token');
        }
      } catch (error) {
        console.error('Auth check failed:', error);
      }
    }
  };
}

export const authStore = createAuthStore();
export const isAuthenticated = derived(authStore, $auth => !!$auth.user);
```

## 🏗️ Architektur-Prinzipien (von homegrow_client3)

### 1. Modulare Struktur
- Klare Trennung von Concerns
- Interfaces für Erweiterbarkeit
- Factory-Pattern für Objekterstellung

### 2. State Machine Pattern
- Robuste Zustandsverwaltung
- Klare State-Übergänge
- Event-basierte Kommunikation

### 3. Event-Driven Architecture
- Lose Kopplung zwischen Komponenten
- WebSocket für Echtzeit-Updates
- MQTT für Geräte-Kommunikation

### 4. Safety First
- Umfassende Validierung
- Graceful Error Handling
- Notaus-Mechanismen

## 📈 Zeitschätzung

- **Phase 1**: ✅ Fertig
- **Phase 2**: 2-3 Tage (PWA)
- **Phase 3**: 3-4 Tage (Program Editor)
- **Phase 4**: 3-4 Tage (Auth)
- **Gesamt**: ~10 Tage bis zur 100% Fertigstellung

## 🚀 Quick Wins

1. **PWA Manifest** hinzufügen (30 Min)
2. **Service Worker** Basic Implementation (2 Stunden)
3. **Program Templates** erweitern (1 Stunde)
4. **WebSocket Reconnection** verbessern (1 Stunde)

## 🔍 Testing Prioritäten

1. **WebSocket Stabilität**: Connection/Reconnection Tests
2. **MQTT Bridge**: Message Handling Tests
3. **Program Engine**: Execution Logic Tests
4. **Frontend Stores**: State Management Tests

## 📝 Dokumentation TODO

1. **API Dokumentation** mit OpenAPI/Swagger
2. **Deployment Guide** für Umbrel
3. **ESP32 Client Setup** Guide
4. **User Manual** auf Deutsch 