<script>
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import { 
    programStore, 
    programs, 
    runningPrograms, 
    programStats, 
    engineStatus,
    loading 
  } from '$lib/stores/programStore.js';
  import { onlineDevices } from '$lib/stores/deviceStore.js';
  import { 
    showSuccess, 
    showError, 
    showProgramStarted, 
    showProgramStopped 
  } from '$lib/stores/notification.js';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';

  let searchTerm = '';
  let statusFilter = 'all'; // all, active, inactive, running
  let deviceFilter = 'all';
  let autoRefreshStop = null;

  onMount(async () => {
    await programStore.initialize();
    autoRefreshStop = programStore.startAutoRefresh();
  });

  onDestroy(() => {
    if (autoRefreshStop) {
      autoRefreshStop();
    }
  });

  async function handleRefresh() {
    try {
      await programStore.loadPrograms();
      await programStore.loadRunningPrograms();
      await programStore.loadEngineStatus();
      showSuccess('Programme aktualisiert');
    } catch (error) {
      showError('Fehler beim Aktualisieren: ' + error.message);
    }
  }

  async function handleToggleProgram(program) {
    try {
      await programStore.toggleProgram(program._id, !program.enabled);
      showSuccess(`Programm "${program.name}" ${!program.enabled ? 'aktiviert' : 'deaktiviert'}`);
    } catch (error) {
      showError('Fehler beim Umschalten: ' + error.message);
    }
  }

  async function handleRunProgram(program) {
    try {
      await programStore.runProgram(program._id);
      showProgramStarted(program.name);
    } catch (error) {
      showError('Fehler beim Starten: ' + error.message);
    }
  }

  async function handleStopProgram(programId) {
    try {
      const runningProgram = $runningPrograms.find(p => p.programId === programId);
      await programStore.stopProgram(programId);
      if (runningProgram) {
        showProgramStopped(runningProgram.programName);
      }
    } catch (error) {
      showError('Fehler beim Stoppen: ' + error.message);
    }
  }

  async function handleDeleteProgram(program) {
    if (!confirm(`Programm "${program.name}" wirklich löschen?`)) {
      return;
    }

    try {
      await programStore.deleteProgram(program._id);
      showSuccess(`Programm "${program.name}" gelöscht`);
    } catch (error) {
      showError('Fehler beim Löschen: ' + error.message);
    }
  }

  function isRunning(programId) {
    return $runningPrograms.some(p => p.programId === programId);
  }

  function getRunningInfo(programId) {
    return $runningPrograms.find(p => p.programId === programId);
  }

  function getDeviceName(deviceId) {
    const device = $onlineDevices.find(d => d.device_id === deviceId);
    return device ? device.name : deviceId;
  }

  function formatSchedule(schedule) {
    switch (schedule.type) {
      case 'manual':
        return 'Manuell';
      case 'interval':
        return `Alle ${schedule.interval_minutes} Min`;
      case 'cron':
        return `Zeitplan: ${schedule.cron_expression}`;
      case 'sensor_trigger':
        return 'Sensor-Trigger';
      default:
        return 'Unbekannt';
    }
  }

  function formatDuration(ms) {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  }

  function getStatusColor(program) {
    if (isRunning(program._id)) return 'text-blue-600';
    if (program.enabled) return 'text-green-600';
    return 'text-gray-600';
  }

  function getStatusText(program) {
    if (isRunning(program._id)) return 'Läuft';
    if (program.enabled) return 'Aktiv';
    return 'Inaktiv';
  }

  // Gefilterte Programme
  $: filteredPrograms = (() => {
    let filtered = $programs;

    // Status-Filter
    switch (statusFilter) {
      case 'active':
        filtered = filtered.filter(p => p.enabled);
        break;
      case 'inactive':
        filtered = filtered.filter(p => !p.enabled);
        break;
      case 'running':
        filtered = filtered.filter(p => isRunning(p._id));
        break;
    }

    // Geräte-Filter
    if (deviceFilter !== 'all') {
      filtered = filtered.filter(p => p.device_id === deviceFilter);
    }

    // Such-Filter
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(p => 
        p.name.toLowerCase().includes(term) ||
        p.description.toLowerCase().includes(term) ||
        getDeviceName(p.device_id).toLowerCase().includes(term)
      );
    }

    return filtered;
  })();
</script>

<svelte:head>
  <title>Programme - HomeGrow v3</title>
</svelte:head>

<div class="programs-page">
  <!-- Header -->
  <div class="page-header">
    <div class="header-content">
      <h1 class="page-title">Programme</h1>
      <p class="page-subtitle">Automatisierung und Programmverwaltung</p>
    </div>
    
    <div class="header-actions">
      <Button 
        variant="secondary" 
        size="sm" 
        on:click={handleRefresh}
        loading={$loading}
      >
        Aktualisieren
      </Button>
      
      <Button 
        variant="primary" 
        size="sm" 
        href="/programs/new"
      >
        Neues Programm
      </Button>
    </div>
  </div>

  <!-- Stats Cards -->
  <div class="stats-grid">
    <Card padding="md">
      <div class="stat-card">
        <div class="stat-icon total">⚙️</div>
        <div class="stat-content">
          <div class="stat-value">{$programStats.total}</div>
          <div class="stat-label">Programme gesamt</div>
        </div>
      </div>
    </Card>
    
    <Card padding="md">
      <div class="stat-card">
        <div class="stat-icon active">✅</div>
        <div class="stat-content">
          <div class="stat-value">{$programStats.active}</div>
          <div class="stat-label">Aktiv</div>
        </div>
      </div>
    </Card>
    
    <Card padding="md">
      <div class="stat-card">
        <div class="stat-icon running">🔄</div>
        <div class="stat-content">
          <div class="stat-value">{$engineStatus.totalRunningPrograms}</div>
          <div class="stat-label">Laufend</div>
        </div>
      </div>
    </Card>
    
    <Card padding="md">
      <div class="stat-card">
        <div class="stat-icon runs">📊</div>
        <div class="stat-content">
          <div class="stat-value">{$programStats.totalRuns}</div>
          <div class="stat-label">Ausführungen</div>
        </div>
      </div>
    </Card>
  </div>

  <!-- Engine Status -->
  <Card title="Programm-Engine Status" padding="md">
    <div class="engine-status">
      <div class="status-indicator">
        <div class="status-dot {$engineStatus.isRunning ? 'running' : 'stopped'}"></div>
        <span class="status-text">
          {$engineStatus.isRunning ? 'Engine läuft' : 'Engine gestoppt'}
        </span>
      </div>
      
      {#if $runningPrograms.length > 0}
        <div class="running-programs">
          <h4>Laufende Programme:</h4>
          <div class="running-list">
            {#each $runningPrograms as running}
              <div class="running-item">
                <span class="program-name">{running.programName}</span>
                <span class="program-device">{getDeviceName(running.deviceId)}</span>
                <span class="program-duration">{formatDuration(running.duration)}</span>
                <span class="program-progress">
                  {running.currentActionIndex + 1}/{running.totalActions}
                </span>
                <Button 
                  variant="danger" 
                  size="xs" 
                  on:click={() => handleStopProgram(running.programId)}
                >
                  Stoppen
                </Button>
              </div>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  </Card>

  <!-- Filters -->
  <Card title="Filter & Suche" padding="md">
    <div class="filters-container">
      <div class="search-group">
        <label for="search">Suche:</label>
        <input 
          id="search"
          type="text" 
          placeholder="Programmname oder Beschreibung..."
          bind:value={searchTerm}
          class="search-input"
        />
      </div>
      
      <div class="filter-group">
        <label for="status-filter">Status:</label>
        <select 
          id="status-filter"
          bind:value={statusFilter}
          class="filter-select"
        >
          <option value="all">Alle</option>
          <option value="active">Aktiv ({$programStats.active})</option>
          <option value="inactive">Inaktiv ({$programStats.inactive})</option>
          <option value="running">Laufend ({$engineStatus.totalRunningPrograms})</option>
        </select>
      </div>
      
      <div class="filter-group">
        <label for="device-filter">Gerät:</label>
        <select 
          id="device-filter"
          bind:value={deviceFilter}
          class="filter-select"
        >
          <option value="all">Alle Geräte</option>
          {#each $onlineDevices as device}
            <option value={device.device_id}>{device.name}</option>
          {/each}
        </select>
      </div>
    </div>
  </Card>

  <!-- Program List -->
  <div class="programs-section">
    {#if $loading}
      <Card padding="lg">
        <LoadingSpinner size="lg" text="Lade Programme..." centered />
      </Card>
    {:else if filteredPrograms.length === 0}
      <Card padding="lg">
        <div class="no-programs">
          {#if $programStats.total === 0}
            <div class="no-programs-icon">⚙️</div>
            <h3>Keine Programme vorhanden</h3>
            <p>Erstellen Sie Ihr erstes Automatisierungs-Programm.</p>
            <Button variant="primary" href="/programs/new">
              Erstes Programm erstellen
            </Button>
          {:else}
            <div class="no-programs-icon">🔍</div>
            <h3>Keine Programme gefunden</h3>
            <p>Keine Programme entsprechen den aktuellen Filterkriterien.</p>
            <Button variant="secondary" on:click={() => { searchTerm = ''; statusFilter = 'all'; deviceFilter = 'all'; }}>
              Filter zurücksetzen
            </Button>
          {/if}
        </div>
      </Card>
    {:else}
      <div class="programs-grid">
        {#each filteredPrograms as program (program._id)}
          <Card padding="md">
            <div class="program-card">
              <div class="program-header">
                <div class="program-title">
                  <h3>{program.name}</h3>
                  <span class="program-status {getStatusColor(program)}">
                    <div class="status-dot {program.enabled ? 'active' : 'inactive'}"></div>
                    {getStatusText(program)}
                  </span>
                </div>
                
                {#if isRunning(program._id)}
                  <div class="running-indicator">
                    <div class="spinner"></div>
                    <span>Läuft...</span>
                  </div>
                {/if}
              </div>
              
              <div class="program-info">
                <p class="program-description">{program.description}</p>
                
                <div class="program-meta">
                  <div class="meta-item">
                    <span class="meta-label">Gerät:</span>
                    <span class="meta-value">{getDeviceName(program.device_id)}</span>
                  </div>
                  <div class="meta-item">
                    <span class="meta-label">Zeitplan:</span>
                    <span class="meta-value">{formatSchedule(program.schedule)}</span>
                  </div>
                  <div class="meta-item">
                    <span class="meta-label">Aktionen:</span>
                    <span class="meta-value">{program.actions.length}</span>
                  </div>
                </div>
                
                {#if program.stats}
                  <div class="program-stats">
                    <div class="stat-item">
                      <span class="stat-value">{program.stats.total_runs}</span>
                      <span class="stat-label">Ausführungen</span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-value">{program.stats.successful_runs}</span>
                      <span class="stat-label">Erfolgreich</span>
                    </div>
                    {#if program.stats.last_run}
                      <div class="stat-item">
                        <span class="stat-value">
                          {new Date(program.stats.last_run).toLocaleDateString()}
                        </span>
                        <span class="stat-label">Letzte Ausführung</span>
                      </div>
                    {/if}
                  </div>
                {/if}
              </div>
              
              <div class="program-actions">
                {#if isRunning(program._id)}
                  <Button 
                    variant="danger" 
                    size="sm" 
                    on:click={() => handleStopProgram(program._id)}
                  >
                    Stoppen
                  </Button>
                {:else}
                  <Button 
                    variant="primary" 
                    size="sm" 
                    disabled={!program.enabled}
                    on:click={() => handleRunProgram(program)}
                  >
                    Ausführen
                  </Button>
                {/if}
                
                <Button 
                  variant="secondary" 
                  size="sm" 
                  on:click={() => handleToggleProgram(program)}
                >
                  {program.enabled ? 'Deaktivieren' : 'Aktivieren'}
                </Button>
                
                <Button 
                  variant="secondary" 
                  size="sm" 
                  href="/programs/{program._id}/edit"
                >
                  Bearbeiten
                </Button>
                
                <Button 
                  variant="danger" 
                  size="sm" 
                  on:click={() => handleDeleteProgram(program)}
                >
                  Löschen
                </Button>
              </div>
            </div>
          </Card>
        {/each}
      </div>
    {/if}
  </div>
</div>

<style>
  .programs-page {
    max-width: 1400px;
    margin: 0 auto;
    padding: 1rem;
    display: grid;
    gap: 1.5rem;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
  }

  .header-content {
    flex: 1;
  }

  .page-title {
    font-size: 2rem;
    font-weight: 700;
    color: #1f2937;
    margin: 0 0 0.5rem 0;
  }

  .page-subtitle {
    color: #6b7280;
    margin: 0;
  }

  .header-actions {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }

  .stat-card {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .stat-icon {
    font-size: 2rem;
    width: 3rem;
    height: 3rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 0.75rem;
  }

  .stat-icon.total { background: #dbeafe; }
  .stat-icon.active { background: #d1fae5; }
  .stat-icon.running { background: #fef3c7; }
  .stat-icon.runs { background: #e0e7ff; }

  .stat-content {
    flex: 1;
  }

  .stat-value {
    font-size: 1.875rem;
    font-weight: 700;
    color: #1f2937;
    line-height: 1;
  }

  .stat-label {
    font-size: 0.875rem;
    color: #6b7280;
    margin-top: 0.25rem;
  }

  .engine-status {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .status-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .status-dot {
    width: 0.75rem;
    height: 0.75rem;
    border-radius: 50%;
  }

  .status-dot.running { background: #10b981; }
  .status-dot.stopped { background: #ef4444; }
  .status-dot.active { background: #10b981; }
  .status-dot.inactive { background: #6b7280; }

  .status-text {
    font-weight: 500;
    color: #374151;
  }

  .running-programs h4 {
    font-size: 1rem;
    font-weight: 600;
    color: #374151;
    margin: 0 0 0.5rem 0;
  }

  .running-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .running-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.5rem;
    background: #f9fafb;
    border-radius: 0.375rem;
    font-size: 0.875rem;
  }

  .program-name {
    font-weight: 500;
    color: #374151;
    min-width: 120px;
  }

  .program-device {
    color: #6b7280;
    min-width: 100px;
  }

  .program-duration {
    color: #6b7280;
    min-width: 60px;
  }

  .program-progress {
    color: #6b7280;
    min-width: 40px;
  }

  .filters-container {
    display: flex;
    gap: 2rem;
    flex-wrap: wrap;
    align-items: end;
  }

  .search-group,
  .filter-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    min-width: 200px;
  }

  .search-group label,
  .filter-group label {
    font-size: 0.875rem;
    font-weight: 500;
    color: #374151;
  }

  .search-input,
  .filter-select {
    padding: 0.5rem;
    border: 1px solid #d1d5db;
    border-radius: 0.375rem;
    background: white;
    font-size: 0.875rem;
    color: #1f2937;
  }

  .search-input:focus,
  .filter-select:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 1px #3b82f6;
  }

  .programs-section {
    min-height: 400px;
  }

  .programs-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
    gap: 1.5rem;
  }

  .program-card {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .program-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }

  .program-title {
    flex: 1;
  }

  .program-title h3 {
    font-size: 1.125rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0 0 0.25rem 0;
  }

  .program-status {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    font-size: 0.875rem;
    font-weight: 500;
  }

  .running-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #3b82f6;
    font-size: 0.875rem;
  }

  .spinner {
    width: 1rem;
    height: 1rem;
    border: 2px solid #e5e7eb;
    border-top: 2px solid #3b82f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .program-description {
    color: #6b7280;
    font-size: 0.875rem;
    margin: 0 0 1rem 0;
    line-height: 1.4;
  }

  .program-meta {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  .meta-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.875rem;
  }

  .meta-label {
    color: #6b7280;
  }

  .meta-value {
    color: #374151;
    font-weight: 500;
  }

  .program-stats {
    display: flex;
    gap: 1rem;
    padding: 0.75rem;
    background: #f9fafb;
    border-radius: 0.375rem;
    margin-bottom: 1rem;
  }

  .stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .stat-item .stat-value {
    font-size: 1rem;
    font-weight: 600;
    color: #374151;
    line-height: 1;
  }

  .stat-item .stat-label {
    font-size: 0.75rem;
    color: #6b7280;
    margin-top: 0.25rem;
  }

  .program-actions {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .no-programs {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 3rem 1rem;
  }

  .no-programs-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
    opacity: 0.5;
  }

  .no-programs h3 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0 0 0.5rem 0;
  }

  .no-programs p {
    color: #6b7280;
    margin: 0 0 1.5rem 0;
    max-width: 400px;
  }

  @media (max-width: 768px) {
    .programs-page {
      padding: 0.5rem;
    }

    .page-header {
      flex-direction: column;
      align-items: stretch;
    }

    .header-actions {
      justify-content: space-between;
    }

    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .filters-container {
      flex-direction: column;
      gap: 1rem;
    }

    .search-group,
    .filter-group {
      min-width: auto;
    }

    .programs-grid {
      grid-template-columns: 1fr;
    }

    .running-item {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.5rem;
    }

    .program-actions {
      flex-direction: column;
    }
  }
</style> 