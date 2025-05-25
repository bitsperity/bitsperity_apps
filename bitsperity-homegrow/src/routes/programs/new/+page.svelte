<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { programStore, programTemplates, templatesLoading } from '$lib/stores/programStore.js';
  import { onlineDevices } from '$lib/stores/deviceStore.js';
  import { showSuccess, showError } from '$lib/stores/notification.js';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';

  let selectedDevice = '';
  let programName = '';
  let selectedTemplate = null;

  onMount(async () => {
    await programStore.loadTemplates();
  });

  async function handleCreateFromTemplate(template) {
    if (!selectedDevice) {
      showError('Bitte wählen Sie ein Gerät aus');
      return;
    }

    if (!programName.trim()) {
      showError('Bitte geben Sie einen Programmnamen ein');
      return;
    }

    try {
      const program = await programStore.createFromTemplate(
        template.id,
        selectedDevice,
        programName
      );
      
      showSuccess(`Programm "${programName}" erstellt`);
      goto(`/programs/${program._id}/edit`);
    } catch (error) {
      showError('Fehler beim Erstellen: ' + error.message);
    }
  }

  function handleManualCreate() {
    if (!selectedDevice) {
      showError('Bitte wählen Sie ein Gerät aus');
      return;
    }

    if (!programName.trim()) {
      showError('Bitte geben Sie einen Programmnamen ein');
      return;
    }

    // Weiterleitung zum Programm-Editor mit Parametern
    const params = new URLSearchParams({
      device_id: selectedDevice,
      name: programName
    });
    goto(`/programs/editor?${params.toString()}`);
  }
</script>

<svelte:head>
  <title>Neues Programm - HomeGrow v3</title>
</svelte:head>

<div class="new-program-page">
  <!-- Header -->
  <div class="page-header">
    <div class="header-content">
      <h1 class="page-title">Neues Programm erstellen</h1>
      <p class="page-subtitle">Wählen Sie eine Vorlage oder erstellen Sie ein eigenes Programm</p>
    </div>
    
    <div class="header-actions">
      <Button variant="secondary" href="/programs">
        Zurück
      </Button>
    </div>
  </div>

  <!-- Configuration -->
  <Card title="Grundkonfiguration" padding="md">
    <div class="config-form">
      <div class="form-group">
        <label for="device-select">Gerät auswählen:</label>
        <select 
          id="device-select"
          bind:value={selectedDevice}
          class="form-select"
          required
        >
          <option value="">-- Gerät auswählen --</option>
          {#each $onlineDevices as device}
            <option value={device.device_id}>{device.name}</option>
          {/each}
        </select>
      </div>
      
      <div class="form-group">
        <label for="program-name">Programmname:</label>
        <input 
          id="program-name"
          type="text" 
          bind:value={programName}
          placeholder="z.B. Tägliche Bewässerung"
          class="form-input"
          required
        />
      </div>
    </div>
  </Card>

  <!-- Templates -->
  <Card title="Vorlagen" padding="md">
    {#if $templatesLoading}
      <LoadingSpinner size="md" text="Lade Vorlagen..." centered />
    {:else if $programTemplates.length === 0}
      <div class="no-templates">
        <p>Keine Vorlagen verfügbar</p>
      </div>
    {:else}
      <div class="templates-grid">
        {#each $programTemplates as template}
          <div class="template-card">
            <div class="template-header">
              <h3 class="template-name">{template.name}</h3>
            </div>
            
            <div class="template-content">
              <p class="template-description">{template.description}</p>
              
              <div class="template-details">
                <div class="detail-item">
                  <span class="detail-label">Zeitplan:</span>
                  <span class="detail-value">
                    {#if template.schedule.type === 'cron'}
                      Zeitplan ({template.schedule.cron_expression})
                    {:else if template.schedule.type === 'interval'}
                      Alle {template.schedule.interval_minutes} Min
                    {:else if template.schedule.type === 'sensor_trigger'}
                      Sensor-Trigger
                    {:else}
                      Manuell
                    {/if}
                  </span>
                </div>
                
                <div class="detail-item">
                  <span class="detail-label">Aktionen:</span>
                  <span class="detail-value">{template.actions.length}</span>
                </div>
                
                {#if template.conditions.length > 0}
                  <div class="detail-item">
                    <span class="detail-label">Bedingungen:</span>
                    <span class="detail-value">{template.conditions.length}</span>
                  </div>
                {/if}
              </div>
            </div>
            
            <div class="template-actions">
              <Button 
                variant="primary" 
                size="sm" 
                fullWidth
                disabled={!selectedDevice || !programName.trim()}
                on:click={() => handleCreateFromTemplate(template)}
              >
                Aus Vorlage erstellen
              </Button>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </Card>

  <!-- Manual Creation -->
  <Card title="Manuell erstellen" padding="md">
    <div class="manual-creation">
      <div class="manual-info">
        <h3>Eigenes Programm erstellen</h3>
        <p>Erstellen Sie ein komplett neues Programm mit dem visuellen Editor.</p>
        
        <ul class="feature-list">
          <li>✅ Drag & Drop Aktionen</li>
          <li>✅ Flexible Bedingungen</li>
          <li>✅ Verschiedene Zeitpläne</li>
          <li>✅ Sensor-basierte Trigger</li>
        </ul>
      </div>
      
      <div class="manual-actions">
        <Button 
          variant="secondary" 
          size="lg"
          disabled={!selectedDevice || !programName.trim()}
          on:click={handleManualCreate}
        >
          Programm-Editor öffnen
        </Button>
      </div>
    </div>
  </Card>
</div>

<style>
  .new-program-page {
    max-width: 1200px;
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
  }

  .config-form {
    display: grid;
    gap: 1.5rem;
    max-width: 500px;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .form-group label {
    font-size: 0.875rem;
    font-weight: 500;
    color: #374151;
  }

  .form-select,
  .form-input {
    padding: 0.75rem;
    border: 1px solid #d1d5db;
    border-radius: 0.375rem;
    background: white;
    font-size: 0.875rem;
    color: #1f2937;
  }

  .form-select:focus,
  .form-input:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 1px #3b82f6;
  }

  .templates-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
  }

  .template-card {
    border: 1px solid #e5e7eb;
    border-radius: 0.75rem;
    padding: 1.5rem;
    background: white;
    transition: all 0.2s ease;
  }

  .template-card:hover {
    border-color: #3b82f6;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  }

  .template-header {
    margin-bottom: 1rem;
  }

  .template-name {
    font-size: 1.125rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0;
  }

  .template-content {
    margin-bottom: 1.5rem;
  }

  .template-description {
    color: #6b7280;
    font-size: 0.875rem;
    line-height: 1.4;
    margin: 0 0 1rem 0;
  }

  .template-details {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .detail-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.875rem;
  }

  .detail-label {
    color: #6b7280;
  }

  .detail-value {
    color: #374151;
    font-weight: 500;
  }

  .template-actions {
    border-top: 1px solid #f3f4f6;
    padding-top: 1rem;
  }

  .manual-creation {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 2rem;
    align-items: center;
  }

  .manual-info h3 {
    font-size: 1.125rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0 0 0.5rem 0;
  }

  .manual-info p {
    color: #6b7280;
    margin: 0 0 1rem 0;
    line-height: 1.4;
  }

  .feature-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .feature-list li {
    font-size: 0.875rem;
    color: #374151;
  }

  .no-templates {
    text-align: center;
    padding: 2rem;
    color: #9ca3af;
  }

  @media (max-width: 768px) {
    .new-program-page {
      padding: 0.5rem;
    }

    .page-header {
      flex-direction: column;
      align-items: stretch;
    }

    .templates-grid {
      grid-template-columns: 1fr;
    }

    .manual-creation {
      grid-template-columns: 1fr;
      text-align: center;
    }
  }
</style> 