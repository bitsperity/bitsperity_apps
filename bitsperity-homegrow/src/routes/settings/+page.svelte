<script>
  import { onMount } from 'svelte';
  import { theme } from '$lib/stores/theme.js';
  import { addNotification } from '$lib/stores/notification.js';
  import Card from '$lib/components/ui/Card.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';

  let loading = false;
  let systemInfo = null;
  let settings = {
    // Theme-Einstellungen
    theme: 'auto',
    
    // System-Einstellungen
    autoRefreshInterval: 5000,
    enableNotifications: true,
    enableSounds: false,
    
    // Monitoring-Einstellungen
    chartUpdateInterval: 2000,
    maxDataPoints: 100,
    enableRealTimeCharts: true,
    
    // Sicherheitseinstellungen
    confirmPumpActions: true,
    emergencyStopTimeout: 5000,
    maxPumpDuration: 60000,
    
    // Dateneinstellungen
    dataRetentionDays: 30,
    enableDataExport: true,
    exportFormat: 'csv',
    
    // Erweiterte Einstellungen
    debugMode: false,
    enableWebSocket: true,
    mqttQoS: 1
  };

  let originalSettings = {};

  onMount(async () => {
    await loadSystemInfo();
    await loadSettings();
  });

  async function loadSystemInfo() {
    try {
      const response = await fetch('/api/v1/system/status');
      const data = await response.json();
      
      if (data.success) {
        systemInfo = data.system;
      }
    } catch (error) {
      console.error('Fehler beim Laden der Systeminformationen:', error);
      addNotification('Fehler beim Laden der Systeminformationen', 'error');
    }
  }

  async function loadSettings() {
    try {
      // Lade Einstellungen aus localStorage
      const savedSettings = localStorage.getItem('homegrow-settings');
      if (savedSettings) {
        const parsed = JSON.parse(savedSettings);
        settings = { ...settings, ...parsed };
      }
      
      // Aktueller Theme-Status
      settings.theme = $theme;
      
      // Kopie für Änderungsvergleich
      originalSettings = { ...settings };
      
    } catch (error) {
      console.error('Fehler beim Laden der Einstellungen:', error);
      addNotification('Fehler beim Laden der Einstellungen', 'error');
    }
  }

  async function saveSettings() {
    loading = true;
    
    try {
      // Theme-Änderung anwenden
      if (settings.theme !== originalSettings.theme) {
        theme.set(settings.theme);
      }
      
      // Einstellungen in localStorage speichern
      localStorage.setItem('homegrow-settings', JSON.stringify(settings));
      
      // Kopie aktualisieren
      originalSettings = { ...settings };
      
      addNotification('Einstellungen erfolgreich gespeichert', 'success');
      
    } catch (error) {
      console.error('Fehler beim Speichern der Einstellungen:', error);
      addNotification('Fehler beim Speichern der Einstellungen', 'error');
    } finally {
      loading = false;
    }
  }

  function resetSettings() {
    if (confirm('Möchten Sie alle Einstellungen auf die Standardwerte zurücksetzen?')) {
      // Standardwerte wiederherstellen
      settings = {
        theme: 'auto',
        autoRefreshInterval: 5000,
        enableNotifications: true,
        enableSounds: false,
        chartUpdateInterval: 2000,
        maxDataPoints: 100,
        enableRealTimeCharts: true,
        confirmPumpActions: true,
        emergencyStopTimeout: 5000,
        maxPumpDuration: 60000,
        dataRetentionDays: 30,
        enableDataExport: true,
        exportFormat: 'csv',
        debugMode: false,
        enableWebSocket: true,
        mqttQoS: 1
      };
      
      addNotification('Einstellungen auf Standardwerte zurückgesetzt', 'info');
    }
  }

  function exportSettings() {
    try {
      const dataStr = JSON.stringify(settings, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      
      const link = document.createElement('a');
      link.href = URL.createObjectURL(dataBlob);
      link.download = `homegrow-settings-${new Date().toISOString().split('T')[0]}.json`;
      link.click();
      
      addNotification('Einstellungen exportiert', 'success');
    } catch (error) {
      console.error('Fehler beim Exportieren der Einstellungen:', error);
      addNotification('Fehler beim Exportieren der Einstellungen', 'error');
    }
  }

  function importSettings(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const importedSettings = JSON.parse(e.target.result);
        settings = { ...settings, ...importedSettings };
        addNotification('Einstellungen importiert', 'success');
      } catch (error) {
        console.error('Fehler beim Importieren der Einstellungen:', error);
        addNotification('Ungültige Einstellungsdatei', 'error');
      }
    };
    reader.readAsText(file);
  }

  function formatUptime(seconds) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) {
      return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  }

  function formatMemory(bytes) {
    const mb = bytes / 1024 / 1024;
    return `${mb.toFixed(1)} MB`;
  }

  $: hasChanges = JSON.stringify(settings) !== JSON.stringify(originalSettings);
</script>

<svelte:head>
  <title>Einstellungen - HomeGrow v3</title>
</svelte:head>

<div class="container mx-auto px-4 py-6 max-w-6xl">
  <div class="mb-6">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
      Einstellungen
    </h1>
    <p class="text-gray-600 dark:text-gray-400">
      System-Konfiguration und Benutzereinstellungen verwalten
    </p>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <!-- Systeminformationen -->
    <div class="lg:col-span-1">
      <Card>
        <div class="p-6">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Systeminformationen
          </h2>
          
          {#if systemInfo}
            <div class="space-y-3">
              <div class="flex justify-between">
                <span class="text-gray-600 dark:text-gray-400">Version:</span>
                <span class="font-medium text-gray-900 dark:text-white">
                  {systemInfo.version}
                </span>
              </div>
              
              <div class="flex justify-between">
                <span class="text-gray-600 dark:text-gray-400">Laufzeit:</span>
                <span class="font-medium text-gray-900 dark:text-white">
                  {formatUptime(systemInfo.uptime)}
                </span>
              </div>
              
              <div class="flex justify-between">
                <span class="text-gray-600 dark:text-gray-400">Speicher:</span>
                <span class="font-medium text-gray-900 dark:text-white">
                  {formatMemory(systemInfo.memory_usage.heapUsed)} / 
                  {formatMemory(systemInfo.memory_usage.heapTotal)}
                </span>
              </div>
              
              <div class="flex justify-between">
                <span class="text-gray-600 dark:text-gray-400">Geräte:</span>
                <span class="font-medium text-gray-900 dark:text-white">
                  {systemInfo.devices.online} / {systemInfo.devices.total} online
                </span>
              </div>
              
              <div class="border-t border-gray-200 dark:border-gray-700 pt-3 mt-4">
                <h3 class="text-sm font-medium text-gray-900 dark:text-white mb-2">
                  Services
                </h3>
                <div class="space-y-2">
                  <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-600 dark:text-gray-400">Datenbank:</span>
                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                      {systemInfo.services.database}
                    </span>
                  </div>
                  <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-600 dark:text-gray-400">MQTT:</span>
                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                      {systemInfo.services.mqtt.connected ? 'verbunden' : 'getrennt'}
                    </span>
                  </div>
                  <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-600 dark:text-gray-400">Beacon:</span>
                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                      {systemInfo.services.beacon.status}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          {:else}
            <div class="flex justify-center py-4">
              <LoadingSpinner size="sm" />
            </div>
          {/if}
        </div>
      </Card>
    </div>

    <!-- Einstellungen -->
    <div class="lg:col-span-2">
      <div class="space-y-6">
        <!-- Theme-Einstellungen -->
        <Card>
          <div class="p-6">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Darstellung
            </h2>
            
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Theme
                </label>
                <select 
                  bind:value={settings.theme}
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="light">Hell</option>
                  <option value="dark">Dunkel</option>
                  <option value="auto">Automatisch</option>
                </select>
              </div>
              
              <div class="flex items-center">
                <input 
                  type="checkbox" 
                  id="enableNotifications"
                  bind:checked={settings.enableNotifications}
                  class="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                />
                <label for="enableNotifications" class="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                  Benachrichtigungen aktivieren
                </label>
              </div>
              
              <div class="flex items-center">
                <input 
                  type="checkbox" 
                  id="enableSounds"
                  bind:checked={settings.enableSounds}
                  class="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                />
                <label for="enableSounds" class="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                  Töne aktivieren
                </label>
              </div>
            </div>
          </div>
        </Card>

        <!-- Monitoring-Einstellungen -->
        <Card>
          <div class="p-6">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Monitoring
            </h2>
            
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Auto-Refresh Intervall (ms)
                </label>
                <input 
                  type="number" 
                  bind:value={settings.autoRefreshInterval}
                  min="1000"
                  max="60000"
                  step="1000"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Chart Update Intervall (ms)
                </label>
                <input 
                  type="number" 
                  bind:value={settings.chartUpdateInterval}
                  min="500"
                  max="10000"
                  step="500"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Maximale Datenpunkte in Charts
                </label>
                <input 
                  type="number" 
                  bind:value={settings.maxDataPoints}
                  min="50"
                  max="500"
                  step="10"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              
              <div class="flex items-center">
                <input 
                  type="checkbox" 
                  id="enableRealTimeCharts"
                  bind:checked={settings.enableRealTimeCharts}
                  class="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                />
                <label for="enableRealTimeCharts" class="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                  Echtzeit-Charts aktivieren
                </label>
              </div>
            </div>
          </div>
        </Card>

        <!-- Sicherheitseinstellungen -->
        <Card>
          <div class="p-6">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Sicherheit
            </h2>
            
            <div class="space-y-4">
              <div class="flex items-center">
                <input 
                  type="checkbox" 
                  id="confirmPumpActions"
                  bind:checked={settings.confirmPumpActions}
                  class="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                />
                <label for="confirmPumpActions" class="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                  Pumpen-Aktionen bestätigen
                </label>
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Notaus-Timeout (ms)
                </label>
                <input 
                  type="number" 
                  bind:value={settings.emergencyStopTimeout}
                  min="1000"
                  max="30000"
                  step="1000"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Maximale Pumpen-Laufzeit (ms)
                </label>
                <input 
                  type="number" 
                  bind:value={settings.maxPumpDuration}
                  min="1000"
                  max="300000"
                  step="1000"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
            </div>
          </div>
        </Card>

        <!-- Dateneinstellungen -->
        <Card>
          <div class="p-6">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Daten
            </h2>
            
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Datenaufbewahrung (Tage)
                </label>
                <input 
                  type="number" 
                  bind:value={settings.dataRetentionDays}
                  min="1"
                  max="365"
                  step="1"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              
              <div class="flex items-center">
                <input 
                  type="checkbox" 
                  id="enableDataExport"
                  bind:checked={settings.enableDataExport}
                  class="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                />
                <label for="enableDataExport" class="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                  Datenexport aktivieren
                </label>
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Export-Format
                </label>
                <select 
                  bind:value={settings.exportFormat}
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="csv">CSV</option>
                  <option value="json">JSON</option>
                  <option value="xlsx">Excel</option>
                </select>
              </div>
            </div>
          </div>
        </Card>

        <!-- Erweiterte Einstellungen -->
        <Card>
          <div class="p-6">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Erweitert
            </h2>
            
            <div class="space-y-4">
              <div class="flex items-center">
                <input 
                  type="checkbox" 
                  id="debugMode"
                  bind:checked={settings.debugMode}
                  class="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                />
                <label for="debugMode" class="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                  Debug-Modus aktivieren
                </label>
              </div>
              
              <div class="flex items-center">
                <input 
                  type="checkbox" 
                  id="enableWebSocket"
                  bind:checked={settings.enableWebSocket}
                  class="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                />
                <label for="enableWebSocket" class="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                  WebSocket-Verbindung aktivieren
                </label>
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  MQTT QoS Level
                </label>
                <select 
                  bind:value={settings.mqttQoS}
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value={0}>0 - At most once</option>
                  <option value={1}>1 - At least once</option>
                  <option value={2}>2 - Exactly once</option>
                </select>
              </div>
            </div>
          </div>
        </Card>

        <!-- Aktionen -->
        <Card>
          <div class="p-6">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Aktionen
            </h2>
            
            <div class="flex flex-wrap gap-3">
              <Button 
                variant="primary" 
                on:click={saveSettings}
                disabled={loading || !hasChanges}
              >
                {#if loading}
                  <LoadingSpinner size="sm" />
                  Speichern...
                {:else}
                  Einstellungen speichern
                {/if}
              </Button>
              
              <Button variant="secondary" on:click={resetSettings}>
                Zurücksetzen
              </Button>
              
              <Button variant="outline" on:click={exportSettings}>
                Exportieren
              </Button>
              
              <div class="relative">
                <input 
                  type="file" 
                  accept=".json"
                  on:change={importSettings}
                  class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <Button variant="outline">
                  Importieren
                </Button>
              </div>
            </div>
            
            {#if hasChanges}
              <div class="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md">
                <p class="text-sm text-yellow-800 dark:text-yellow-200">
                  Sie haben ungespeicherte Änderungen.
                </p>
              </div>
            {/if}
          </div>
        </Card>
      </div>
    </div>
  </div>
</div> 